#!/bin/bash

# AI Game Generator 服务状态检查脚本

echo "🔍 检查 AI Game Generator 开发服务状态..."

# 加载环境变量
if [ -f "config.env" ]; then
    export $(cat config.env | grep -v '^#' | xargs)
    echo "✅ 已加载环境变量"
fi

echo ""
echo "📊 服务状态："

# 检查后端服务
echo "📚 后端服务 (端口 $BACKEND_PORT):"
BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo "   ✅ 运行中 (PID: $BACKEND_PIDS)"
    echo "   🔗 地址: http://localhost:$BACKEND_PORT"
    echo "   📄 日志: logs/backend.log"
else
    echo "   ❌ 未运行"
fi

echo ""

# 检查前端服务
echo "🎨 前端服务 (端口 $FRONTEND_PORT):"
FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "   ✅ 运行中 (PID: $FRONTEND_PIDS)"
    echo "   🔗 地址: http://localhost:$FRONTEND_PORT"
    echo "   📄 日志: logs/frontend.log"
else
    echo "   ❌ 未运行"
fi

echo ""
echo "📋 相关命令："
echo "   启动服务: ./start-dev.sh"
echo "   停止服务: ./stop-dev.sh"
echo "   查看后端日志: tail -f logs/backend.log"
echo "   查看前端日志: tail -f logs/frontend.log" 