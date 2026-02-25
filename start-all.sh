#!/bin/bash
# 一键启动脚本 - 启动前后端所有服务

# 用法: ./start-all.sh [development|test|production]
# 默认: development

ENV=${1:-development}

SCRIPT_DIR="$(dirname "$0")"
BACKEND_DIR="$SCRIPT_DIR/Fund_backend"
FRONT_DIR="$SCRIPT_DIR/Fund_front"

echo "=========================================="
echo "  基金管理系统 - 一键启动"
echo "=========================================="
echo "后端环境: $ENV"
echo "前端模式: dev (开发)"
echo "=========================================="
echo ""

# 启动后端
echo "[1/2] 启动后端服务..."
cd "$BACKEND_DIR"
./start.sh $ENV

# 启动前端
echo ""
echo "[2/2] 启动前端服务..."
cd "$FRONT_DIR"
./start.sh dev

echo ""
echo "=========================================="
echo "  启动完成!"
echo "=========================================="
echo "前端访问: http://localhost:5173 (开发)"
echo "后端API: http://localhost:5000"
echo ""
echo "如需停止服务，请运行:"
echo "  ./stop-all.sh $ENV"
