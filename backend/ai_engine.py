import os
import json
import base64
import re
import asyncio
from typing import Dict, AsyncGenerator, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class DeepSeekEngine:
    """DeepSeek API 引擎，负责生成游戏代码"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
        
        # 配置DeepSeek客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model_name = "deepseek-chat"
        
    def create_game_prompt(self, user_input: str) -> str:
        """构建游戏生成的提示词"""
        return f"""请根据用户需求生成一个完整的HTML5游戏。用户需求：{user_input}

要求：
1. 生成一个完整可玩的HTML5游戏，包含所有必要的HTML、CSS和JavaScript代码
2. 游戏必须是自包含的，不依赖外部资源
3. 代码要简洁高效，适合在现代浏览器中运行
4. 游戏应该有基本的交互性和可玩性
5. 请确保代码安全，不包含任何恶意内容

**重要的中文显示要求：**
6. **HTML必须包含UTF-8编码声明：<meta charset="UTF-8">**
7. **HTML的lang属性必须设置为zh-CN：<html lang="zh-CN">**
8. **所有游戏界面文字、提示信息、按钮文字、说明文字必须使用中文**
9. **所有JavaScript中的alert、confirm、prompt等提示文字必须是中文**
10. **游戏标题必须是中文，不要使用英文**
11. **CSS中如需要设置字体，请包含中文字体：font-family: 'Microsoft YaHei', '微软雅黑', SimHei, '黑体', Arial, sans-serif**

输出格式：
请将生成的代码按以下格式输出，每个文件用特定标记包围：

<FILE:index.html>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>游戏标题</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', '微软雅黑', SimHei, '黑体', Arial, sans-serif;
            /* 其他样式 */
        }}
    </style>
</head>
<body>
    <!-- 游戏内容，所有文字必须是中文 -->
    <script>
        // JavaScript代码，所有提示文字必须是中文
        // 例如：alert('游戏开始！'); 而不是 alert('Game Start!');
    </script>
</body>
</html>
</FILE:index.html>

<FILE:style.css>
/* CSS代码内容，如果有的话 */
</FILE:style.css>

<FILE:script.js>
/* JavaScript代码内容，如果有的话 */
/* 所有游戏提示文字、按钮文字必须是中文 */
</FILE:script.js>

注意：
- 如果所有代码都在HTML文件中，只需要输出index.html文件
- 确保游戏完整可玩，界面美观
- 不要包含任何外部链接或依赖
- 代码要清晰注释，便于理解
- **特别重要：确保HTML包含正确的UTF-8编码和中文语言声明**
- **所有用户看到的文字都必须是中文，包括游戏说明、按钮、提示等**

现在请生成游戏："""

    async def generate_game_stream(self, user_input: str) -> AsyncGenerator[Dict, None]:
        """流式生成游戏代码"""
        try:
            # 发送进度更新
            yield {
                "type": "progress",
                "text": "正在连接DeepSeek AI...",
                "accumulated": 0
            }
            
            messages = [
                {"role": "system", "content": "你是一个专业的游戏开发助手，擅长创建HTML5游戏。"},
                {"role": "user", "content": self.create_game_prompt(user_input)}
            ]
            
            # 使用DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=4000
            )
            
            if response and response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                
                # 发送进度更新
                yield {
                    "type": "progress", 
                    "text": "正在解析响应...",
                    "accumulated": len(content) // 2
                }
                
                # 解析文件
                files = self.extract_files_from_text(content)
                
                if not files:
                    # 如果没有找到文件标记，直接将内容作为HTML
                    files = {"index.html": content}
                
                # 发送每个文件
                for filename, file_content in files.items():
                    yield {
                        "type": "file",
                        "name": filename,
                        "content": base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
                    }
                
                # 发送完成信号
                yield {
                    "type": "complete",
                    "files": {
                        name: base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
                        for name, file_content in files.items()
                    },
                    "message": "游戏生成完成"
                }
            else:
                yield {
                    "type": "error",
                    "message": "AI 没有返回有效内容"
                }
                
        except Exception as e:
            yield {
                "type": "error",
                "message": f"生成失败: {str(e)}"
            }
    
    def extract_files_from_text(self, text: str) -> Dict[str, str]:
        """从生成的文本中提取文件内容"""
        files = {}
        
        # 匹配文件标记格式
        file_pattern = r'<FILE:([^>]+)>\s*(.*?)\s*</FILE:[^>]+>'
        matches = re.findall(file_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for filename, content in matches:
            # 清理文件名
            filename = filename.strip()
            # 清理内容（移除多余的空白）
            content = content.strip()
            files[filename] = content
        
        # 如果没有找到文件标记，但内容看起来像HTML，则作为index.html
        if not files and ('<html' in text.lower() or '<!doctype' in text.lower() or '<div' in text.lower()):
            files['index.html'] = text.strip()
        
        return files
    
    async def generate_game_sync(self, user_input: str) -> Dict[str, str]:
        """同步生成游戏（用于非流式场景）"""
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的游戏开发助手，擅长创建HTML5游戏。"},
                {"role": "user", "content": self.create_game_prompt(user_input)}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=4000
            )
            
            if response and response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                files = self.extract_files_from_text(content)
                
                if not files:
                    files = {"index.html": content}
                    
                return files
            else:
                raise Exception("AI 没有返回有效内容")
                
        except Exception as e:
            raise Exception(f"同步生成失败: {str(e)}")

# 全局实例
deepseek_engine = DeepSeekEngine() 