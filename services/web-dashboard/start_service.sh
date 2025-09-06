#!/bin/bash
# Web Dashboard Service Startup Script

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_FILE="$SERVICE_DIR/web_dashboard_service.pid"
LOG_FILE="$PROJECT_ROOT/logs/web_dashboard_service.log"
PYTHON_SCRIPT="$SERVICE_DIR/web_dashboard.py"

start_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${BLUE}Web Dashboard service is already running (PID: $(cat "$PID_FILE"))${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Starting Web Dashboard Service...${NC}"
    
    # Set environment
    export PROJECT_ROOT="$PROJECT_ROOT"
    export FLASK_PORT="${FLASK_PORT:-5000}"
    export FLASK_HOST="${FLASK_HOST:-0.0.0.0}"
    
    # Start service in background
    cd "$SERVICE_DIR"
    nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 3
    
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Web Dashboard service started successfully (PID: $(cat "$PID_FILE"))${NC}"
        echo -e "${BLUE}🌐 Access at: http://localhost:${FLASK_PORT:-5000}${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start Web Dashboard service${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${BLUE}Stopping Web Dashboard service (PID: $PID)...${NC}"
        
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
        echo -e "${GREEN}✅ Web Dashboard service stopped${NC}"
    else
        echo -e "${BLUE}Web Dashboard service is not running${NC}"
    fi
}

status_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}🟢 Web Dashboard service is running (PID: $PID)${NC}"
        echo -e "${BLUE}🌐 Access at: http://localhost:${FLASK_PORT:-5000}${NC}"
        
        # Show resource usage
        if command -v ps >/dev/null; then
            ps -p "$PID" -o pid,ppid,cpu,pmem,time,comm --no-headers
        fi
    else
        echo -e "${RED}🔴 Web Dashboard service is not running${NC}"
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