#!/bin/bash
# Chart Analysis Bot Control Script
# Usage: ./start_chart_bot.sh {start|stop|restart|status}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PYTHON_SCRIPT="chart_analysis_bot.py"
PID_FILE="chart_analysis_bot.pid"
LOG_FILE="chart_analysis_bot.log"
VENV_PATH="venv/bin/activate"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

start_chart_bot() {
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            print_warning "Chart Analysis Bot is already running (PID: $PID)"
            return 1
        else
            print_info "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        print_error "Python script '$PYTHON_SCRIPT' not found!"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ ! -f "$VENV_PATH" ]; then
        print_error "Virtual environment not found at '$VENV_PATH'!"
        return 1
    fi
    
    print_info "🤖 Starting Chart Analysis Bot..."
    
    # Start the bot in background with virtual environment
    nohup bash -c "source $VENV_PATH && python $PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if ps -p $! > /dev/null 2>&1; then
        print_status "✅ Chart Analysis Bot started successfully (PID: $!)"
        print_info "📝 Log file: $LOG_FILE"
        return 0
    else
        print_error "Failed to start Chart Analysis Bot"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_chart_bot() {
    if [ ! -f "$PID_FILE" ]; then
        print_warning "Chart Analysis Bot is not running (no PID file found)"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p $PID > /dev/null 2>&1; then
        print_warning "Chart Analysis Bot is not running (process not found)"
        rm -f "$PID_FILE"
        return 0
    fi
    
    print_info "🛑 Stopping Chart Analysis Bot (PID: $PID)..."
    
    # Try graceful shutdown first
    kill $PID
    
    # Wait for process to terminate
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p $PID > /dev/null 2>&1; then
        print_warning "Force killing Chart Analysis Bot..."
        kill -9 $PID
        sleep 1
    fi
    
    # Check if stopped
    if ! ps -p $PID > /dev/null 2>&1; then
        print_status "✅ Chart Analysis Bot stopped successfully"
        rm -f "$PID_FILE"
        return 0
    else
        print_error "Failed to stop Chart Analysis Bot"
        return 1
    fi
}

status_chart_bot() {
    if [ ! -f "$PID_FILE" ]; then
        print_info "Chart Analysis Bot is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p $PID > /dev/null 2>&1; then
        print_status "Chart Analysis Bot is running (PID: $PID)"
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            print_info "Recent log entries:"
            tail -n 5 "$LOG_FILE"
        fi
        return 0
    else
        print_info "Chart Analysis Bot is not running (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

restart_chart_bot() {
    print_info "🔄 Restarting Chart Analysis Bot..."
    stop_chart_bot
    sleep 2
    start_chart_bot
}

# Main script logic
case "$1" in
    start)
        start_chart_bot
        ;;
    stop)
        stop_chart_bot
        ;;
    restart)
        restart_chart_bot
        ;;
    status)
        status_chart_bot
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Chart Analysis Bot"
        echo "  stop    - Stop the Chart Analysis Bot"
        echo "  restart - Restart the Chart Analysis Bot"
        echo "  status  - Show Chart Analysis Bot status"
        exit 1
        ;;
esac

exit $?