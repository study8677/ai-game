#!/bin/bash

# AI Game Generator 停止开发服务脚本

echo "🛑 停止 AI Game Generator 开发服务..."

# 加载环境变量
if [ -f "config.env" ]; then
    export $(cat config.env | grep -v '^#' | xargs)
    echo "✅ 已加载环境变量"
fi

# 停止后端服务
echo "📚 停止后端服务 (端口 $BACKEND_PORT)..."
BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT)
if [ ! -z "$BACKEND_PIDS" ]; then
    kill $BACKEND_PIDS
    echo "✅ 后端服务已停止"
else
    echo "ℹ️  未发现运行中的后端服务"
fi

# 停止前端服务
echo "🎨 停止前端服务 (端口 $FRONTEND_PORT)..."
FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT)
if [ ! -z "$FRONTEND_PIDS" ]; then
    kill $FRONTEND_PIDS
    echo "✅ 前端服务已停止"
else
    echo "ℹ️  未发现运行中的前端服务"
fi

# 额外清理：停止所有相关的 node 和 python 进程
echo "🧹 清理相关进程..."
pkill -f "uvicorn.*app:app" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

echo "🎉 所有服务已停止！" 