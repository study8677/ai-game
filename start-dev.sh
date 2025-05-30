#!/bin/bash

# AI Game Generator 开发环境启动脚本

echo "🚀 启动 AI Game Generator 开发环境..."

# 检查Python虚拟环境
if [ ! -d "python3.10-env" ]; then
    echo "❌ Python虚拟环境不存在，请先运行安装脚本"
    exit 1
fi

# 加载环境变量
if [ -f "config.env" ]; then
    export $(cat config.env | grep -v '^#' | xargs)
    echo "✅ 已加载环境变量"
fi

# 创建日志目录
mkdir -p logs

# 函数：启动后端
start_backend() {
    echo "📚 启动后端服务 (端口 $BACKEND_PORT)..."
    cd /root/workspace
    source python3.10-env/bin/activate
    export PYTHONPATH=/root/workspace:$PYTHONPATH
    cd backend
    nohup python -m uvicorn app:app --host 0.0.0.0 --port $BACKEND_PORT --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
    echo "📄 后端日志: logs/backend.log"
    cd ..
}

# 函数：启动前端
start_frontend() {
    echo "🎨 启动前端服务 (端口 $FRONTEND_PORT)..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "📦 安装前端依赖..."
        npm install
    fi
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
    echo "📄 前端日志: logs/frontend.log"
    cd ..
}

# 函数：健康检查
health_check() {
    echo "🔍 等待服务启动..."
    sleep 5
    
    # 检查后端
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
        echo "✅ 后端服务健康检查通过"
    else
        echo "❌ 后端服务健康检查失败"
    fi
    
    # 检查前端
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
        echo "✅ 前端服务健康检查通过"
    else
        echo "❌ 前端服务健康检查失败"
    fi
}

# 清理函数
cleanup() {
    echo "🛑 正在停止服务..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo "✅ 服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 启动服务
start_backend
start_frontend

# 健康检查
health_check

echo ""
echo "🎉 AI Game Generator 开发环境已启动！"
echo ""
echo "📍 服务地址："
echo "   🔗 前端: http://localhost:$FRONTEND_PORT"
echo "   🔗 后端: http://localhost:$BACKEND_PORT"
echo "   📊 后端健康检查: http://localhost:$BACKEND_PORT/health"
echo ""
echo "💡 使用说明："
echo "   - 在前端界面输入游戏描述"
echo "   - 点击'生成游戏'按钮"
echo "   - 等待AI生成可玩的HTML5游戏"
echo ""
echo "⚠️  按 Ctrl+C 停止服务"
echo ""

# 保持脚本运行
wait 