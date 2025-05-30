import json
import base64
import asyncio
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import logging

from ai_engine import deepseek_engine
from guard import code_guard

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Game Generator", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameRequest(BaseModel):
    prompt: str
    stream: bool = True

class GameResponse(BaseModel):
    files: Dict[str, str]
    message: str

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "AI Game Generator is running"}

@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "AI Game Generator API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_game": "/generateGame (POST)",
        }
    }

@app.post("/generateGame")
async def generate_game(request: GameRequest):
    """生成游戏的主接口，支持流式和非流式响应"""
    
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="游戏描述不能为空")
    
    # 检查请求长度
    if len(request.prompt) > 1000:
        raise HTTPException(status_code=400, detail="游戏描述过长，请控制在1000字符以内")
    
    logger.info(f"接收到游戏生成请求: {request.prompt}")
    
    if request.stream:
        # 流式响应
        return StreamingResponse(
            stream_game_generation(request.prompt),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    else:
        # 非流式响应
        try:
            files = await deepseek_engine.generate_game_sync(request.prompt)
            
            if not files:
                raise HTTPException(status_code=500, detail="AI 未能生成有效的游戏代码")
            
            # 安全检查
            decoded_files = {}
            for filename, content in files.items():
                decoded_files[filename] = content
            
            is_safe, safety_message = code_guard.check_game_files(decoded_files)
            if not is_safe:
                logger.warning(f"安全检查失败: {safety_message}")
                raise HTTPException(status_code=400, detail=f"生成的代码存在安全风险: {safety_message}")
            
            # 转换为 base64
            base64_files = {}
            for filename, content in decoded_files.items():
                base64_files[filename] = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            return GameResponse(
                files=base64_files,
                message="游戏生成完成"
            )
            
        except Exception as e:
            logger.error(f"非流式生成失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"游戏生成失败: {str(e)}")

@app.get("/generateGame")
async def generate_game_stream_get(prompt: str, stream: str = "true"):
    """流式生成游戏的GET接口，支持EventSource"""
    
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="游戏描述不能为空")
    
    # 检查请求长度
    if len(prompt) > 1000:
        raise HTTPException(status_code=400, detail="游戏描述过长，请控制在1000字符以内")
    
    logger.info(f"接收到流式游戏生成请求: {prompt}")
    
    # 流式响应
    return StreamingResponse(
        stream_game_generation(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

async def stream_game_generation(prompt: str):
    """流式生成游戏的生成器函数"""
    try:
        # 发送开始事件
        start_data = json.dumps({'type': 'start', 'message': '开始生成游戏...'})
        yield f"data: {start_data}\n\n"
        
        sent_files = set()  # 跟踪已发送的文件，避免重复
        
        async for chunk in deepseek_engine.generate_game_stream(prompt):
            chunk_type = chunk.get("type")
            
            if chunk_type == "progress":
                # 发送进度更新
                progress_data = json.dumps({
                    'type': 'progress',
                    'message': chunk.get('text', '正在生成...'),
                    'length': chunk.get('accumulated', 0)
                })
                yield f"data: {progress_data}\n\n"
                
            elif chunk_type == "file":
                # 处理文件数据
                filename = chunk.get("name")
                content_b64 = chunk.get("content")
                
                if filename and content_b64 and filename not in sent_files:
                    try:
                        # 解码内容进行安全检查
                        content = base64.b64decode(content_b64).decode('utf-8')
                        
                        # 单文件安全检查
                        if filename.endswith(('.html', '.htm')):
                            is_safe, message = code_guard.check_html_code(content)
                        elif filename.endswith('.js'):
                            is_safe, message = code_guard.check_javascript_code(content)
                        else:
                            is_safe, message = True, "文件类型安全"
                        
                        if is_safe:
                            file_data = json.dumps({
                                'type': 'file',
                                'name': filename,
                                'content': content_b64
                            })
                            yield f"data: {file_data}\n\n"
                            sent_files.add(filename)
                        else:
                            logger.warning(f"文件 {filename} 安全检查失败: {message}")
                            warning_data = json.dumps({
                                'type': 'warning',
                                'message': f'文件 {filename} 存在安全风险，已跳过'
                            })
                            yield f"data: {warning_data}\n\n"
                            
                    except Exception as e:
                        logger.error(f"处理文件 {filename} 时出错: {str(e)}")
                        error_data = json.dumps({
                            'type': 'warning',
                            'message': f'处理文件 {filename} 时出错'
                        })
                        yield f"data: {error_data}\n\n"
                        
            elif chunk_type == "complete":
                # 最终完成检查
                files = chunk.get("files", {})
                if files:
                    # 解码所有文件进行最终安全检查
                    decoded_files = {}
                    for filename, content_b64 in files.items():
                        try:
                            content = base64.b64decode(content_b64).decode('utf-8')
                            decoded_files[filename] = content
                        except Exception as e:
                            logger.error(f"解码文件 {filename} 失败: {str(e)}")
                            continue
                    
                    if decoded_files:
                        is_safe, safety_message = code_guard.check_game_files(decoded_files)
                        if is_safe:
                            # 发送未发送的文件
                            for filename, content_b64 in files.items():
                                if filename not in sent_files:
                                    file_data = json.dumps({
                                        'type': 'file',
                                        'name': filename,
                                        'content': content_b64
                                    })
                                    yield f"data: {file_data}\n\n"
                            
                            complete_data = json.dumps({
                                'type': 'complete',
                                'message': chunk.get('message', '游戏生成完成'),
                                'fileCount': len(files)
                            })
                            yield f"data: {complete_data}\n\n"
                        else:
                            error_data = json.dumps({
                                'type': 'error',
                                'message': f'生成的代码存在安全风险: {safety_message}'
                            })
                            yield f"data: {error_data}\n\n"
                    else:
                        error_data = json.dumps({
                            'type': 'error',
                            'message': '未能生成有效的游戏文件'
                        })
                        yield f"data: {error_data}\n\n"
                else:
                    error_data = json.dumps({
                        'type': 'error',
                        'message': '生成过程中未收到文件内容'
                    })
                    yield f"data: {error_data}\n\n"
                break
                
            elif chunk_type == "error":
                error_data = json.dumps({
                    'type': 'error',
                    'message': chunk.get('message', '生成过程中发生错误')
                })
                yield f"data: {error_data}\n\n"
                break
                
        # 发送结束事件
        end_data = json.dumps({'type': 'end'})
        yield f"data: {end_data}\n\n"
        
    except Exception as e:
        logger.error(f"流式生成过程中发生错误: {str(e)}")
        error_data = json.dumps({
            'type': 'error',
            'message': f'生成过程中发生错误: {str(e)}'
        })
        yield f"data: {error_data}\n\n"
        end_data = json.dumps({'type': 'end'})
        yield f"data: {end_data}\n\n"

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("AI Game Generator 正在启动...")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("AI Game Generator 正在关闭...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 