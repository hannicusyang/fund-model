#!/bin/bash
# 一键停止脚本 - 停止前后端所有服务

# 用法: ./stop-all.sh [development|test|production]
# 默认: development

ENV=${1:-development}

SCRIPT_DIR="$(dirname "$0")"
BACKEND_DIR="$SCRIPT_DIR/Fund_backend"
FRONT_DIR="$SCRIPT_DIR/Fund_front"

echo "=========================================="
echo "  基金管理系统 - 一键停止"
echo "=========================================="

# 停止前端
echo "[1/2] 停止前端服务..."
cd "$FRONT_DIR"
./stop.sh dev

# 停止后端
echo ""
echo "[2/2] 停止后端服务..."
cd "$BACKEND_DIR"
./stop.sh $ENV

echo ""
echo "=========================================="
echo "  所有服务已停止"
echo "=========================================="
