#!/bin/bash
# Trading Service Startup Script

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_FILE="$SERVICE_DIR/trading_service.pid"
LOG_FILE="$PROJECT_ROOT/logs/trading_service.log"
PYTHON_SCRIPT="$SERVICE_DIR/rl_bot_ready.py"

start_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${BLUE}Trading service is already running (PID: $(cat "$PID_FILE"))${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Starting Trading Service...${NC}"
    
    # Set environment
    export PROJECT_ROOT="$PROJECT_ROOT"
    
    # Start service in background
    cd "$SERVICE_DIR"
    nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Trading service started successfully (PID: $(cat "$PID_FILE"))${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start trading service${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${BLUE}Stopping trading service (PID: $PID)...${NC}"
        
        if kill -TERM "$PID" 2>/dev/null; then
            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                kill -KILL "$PID" 2>/dev/null
            fi
        fi
        
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ Trading service stopped${NC}"
    else
        echo -e "${BLUE}Trading service is not running${NC}"
    fi
}

status_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}🟢 Trading service is running (PID: $PID)${NC}"
        
        # Show resource usage
        if command -v ps >/dev/null; then
            ps -p "$PID" -o pid,ppid,cpu,pmem,time,comm --no-headers
        fi
    else
        echo -e "${RED}🔴 Trading service is not running${NC}"
        rm -f "$PID_FILE"
    fi
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 2
        start_service
        ;;
    status)
        status_service
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac