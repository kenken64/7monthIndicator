#!/bin/bash
# Start MCP SQLite Server for Trading Bot Databases
# Usage: ./start_mcp_server.sh [start|stop|restart|status]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="mcp_server.pid"
LOG_FILE="mcp_server.log"

start_mcp_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "⚠️  MCP server is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    echo "🚀 Starting MCP SQLite server in background..."
    echo "📊 Databases: trading_bot.db, trading_data.db"

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "⚠️  Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install/update dependencies
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1

    # Check if databases exist
    if [ ! -f "trading_bot.db" ]; then
        echo "⚠️  trading_bot.db not found. Please run the trading bot first to create the database."
    fi
    
    if [ ! -f "trading_data.db" ]; then
        echo "ℹ️  trading_data.db not found. Will be created if needed."
    fi

    echo "🔗 Starting MCP SQLite server..."
    echo "📝 Logs will be written to: $LOG_FILE"

    # Start MCP server in background
    nohup python3 mcp_sqlite_server.py trading_bot.db trading_data.db > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ MCP server started successfully (PID: $(cat $PID_FILE))"
        echo "🔍 Monitor logs with: tail -f $LOG_FILE"
    else
        echo "❌ Failed to start MCP server"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_mcp_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  MCP server is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "🛑 Stopping MCP server (PID: $PID)..."
        kill "$PID"
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "⚡ Force stopping MCP server..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ MCP server stopped"
    else
        echo "⚠️  Process not found, cleaning up PID file"
        rm -f "$PID_FILE"
    fi
}

status_mcp_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ MCP server is running (PID: $(cat $PID_FILE))"
        echo "📊 Databases: trading_bot.db, trading_data.db" 
        echo "📝 Log file: $LOG_FILE"
        return 0
    else
        echo "❌ MCP server is not running"
        return 1
    fi
}

case "${1:-start}" in
    start)
        start_mcp_server
        ;;
    stop)
        stop_mcp_server
        ;;
    restart)
        stop_mcp_server
        sleep 2
        start_mcp_server
        ;;
    status)
        status_mcp_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo "  start   - Start the MCP server in background (default)"
        echo "  stop    - Stop the MCP server"
        echo "  restart - Restart the MCP server"
        echo "  status  - Check MCP server status"
        exit 1
        ;;
esac