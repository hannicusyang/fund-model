#!/bin/bash
# 基金系统监控脚本

LOG_FILE="/home/clawdbot/.openclaw/workspace/logs/monitor.log"
FRONT_PORT=5173
BACK_PORT=5000

check_service() {
    local name=$1
    local port=$2
    
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $name 运行正常" >> $LOG_FILE
        return 0
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $name 未运行，正在启动..." >> $LOG_FILE
        return 1
    fi
}

# 检查前端
if ! check_service "前端" $FRONT_PORT; then
    cd /home/clawdbot/.openclaw/workspace/Fund_front
    nohup npm run dev > /home/clawdbot/.openclaw/workspace/logs/frontend.log 2>&1 &
fi

# 检查后端
if ! check_service "后端" $BACK_PORT; then
    cd /home/clawdbot/.openclaw/workspace/Fund_backend
    source venv/bin/activate
    nohup python app.py > /home/clawdbot/.openclaw/workspace/logs/backend.log 2>&1 &
fi
