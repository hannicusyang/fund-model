#!/bin/bash

BACKEND_DIR="/home/clawdbot/.openclaw/workspace/Fund_backend"
FRONT_DIR="/home/clawdbot/.openclaw/workspace/Fund_front"
LOG_DIR="/home/clawdbot/.openclaw/workspace/logs"

mkdir -p "$LOG_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

check_process() {
    pgrep -f "$1" > /dev/null 2>&1
}

start_backend() {
    if check_process "python.*app.py"; then
        echo -e "${YELLOW}后端已在运行${NC}"
        return
    fi
    echo -e "${GREEN}启动后端...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup python app.py > "$LOG_DIR/backend.log" 2>&1 &
    echo -e "${GREEN}后端已启动${NC}"
}

stop_backend() {
    pkill -f "python.*app.py"
    echo -e "${GREEN}后端已停止${NC}"
}

start_frontend() {
    if check_process "vite"; then
        echo -e "${YELLOW}前端已在运行${NC}"
        return
    fi
    echo -e "${GREEN}启动前端...${NC}"
    cd "$FRONT_DIR"
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo -e "${GREEN}前端已启动${NC}"
}

stop_frontend() {
    pkill -f "vite"
    echo -e "${GREEN}前端已停止${NC}"
}

show_logs() {
    echo -e "${GREEN}=== 后端日志 ===${NC}"
    tail -30 "$LOG_DIR/backend.log" 2>/dev/null
    echo ""
    echo -e "${GREEN}=== 前端日志 ===${NC}"
    tail -30 "$LOG_DIR/frontend.log" 2>/dev/null
}

start_all() {
    start_backend
    sleep 2
    start_frontend
    echo ""
    echo "========================================"
    echo "  基金管理系统已全部启动"
    echo "  后端: http://localhost:5000"
    echo "  前端: http://localhost:5173"
    echo "========================================"
}

stop_all() {
    stop_frontend
    stop_backend
    echo -e "${GREEN}所有服务已停止${NC}"
}

restart_all() {
    stop_all
    sleep 2
    start_all
}

status() {
    echo "========================================"
    echo "  基金管理系统状态"
    echo "========================================"
    if check_process "python.*app.py"; then
        echo -e "${GREEN}● 后端 - 运行中${NC}"
    else
        echo -e "${RED}● 后端 - 已停止${NC}"
    fi
    if check_process "vite"; then
        echo -e "${GREEN}● 前端 - 运行中${NC}"
    else
        echo -e "${RED}● 前端 - 已停止${NC}"
    fi
    echo "========================================"
}

case "$1" in
    start) start_all ;;
    stop) stop_all ;;
    restart) restart_all ;;
    status) status ;;
    logs) show_logs ;;
    backend)
        case "$2" in
            start) start_backend ;;
            stop) stop_backend ;;
            *) echo "用法: $0 backend {start|stop}" ;;
        esac
        ;;
    frontend)
        case "$2" in
            start) start_frontend ;;
            stop) stop_frontend ;;
            *) echo "用法: $0 frontend {start|stop}" ;;
        esac
        ;;
    *) echo "用法: $0 {start|stop|restart|status|logs}" ;;
esac
