#!/bin/bash
# Start Web Dashboard for Trading Bot in Background
# Usage: ./start_web_dashboard.sh [start|stop|restart|status]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="web_dashboard.pid"
LOG_FILE="web_dashboard.log"

start_dashboard() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "⚠️  Web dashboard is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    echo "🚀 Starting Trading Bot Web Dashboard in background..."

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

    # Set environment variables for Flask
    export FLASK_APP=web_dashboard.py
    export FLASK_ENV=production

    # Check if database exists
    if [ ! -f "trading_bot.db" ]; then
        echo "⚠️  Database not found. Please run the trading bot first to create the database."
        echo "   Or create sample data with: python3 -c \"from database import get_database; get_database()\""
    fi

    PUBLIC_IP=$(hostname -I | awk '{print $1}')
    echo "🌐 Starting web dashboard on public IP: http://$PUBLIC_IP:5000"
    echo "📊 Access your trading analytics at: http://$PUBLIC_IP:5000"
    echo "🏠 Local access: http://localhost:5000"
    echo "📝 Logs will be written to: $LOG_FILE"

    # Start Flask server in background
    nohup python3 web_dashboard.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ Web dashboard started successfully (PID: $(cat $PID_FILE))"
        echo "🔍 Monitor logs with: tail -f $LOG_FILE"
    else
        echo "❌ Failed to start web dashboard"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_dashboard() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  Web dashboard is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "🛑 Stopping web dashboard (PID: $PID)..."
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
            echo "⚡ Force stopping web dashboard..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Web dashboard stopped"
    else
        echo "⚠️  Process not found, cleaning up PID file"
        rm -f "$PID_FILE"
    fi
}

status_dashboard() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ Web dashboard is running (PID: $(cat $PID_FILE))"
        PUBLIC_IP=$(hostname -I | awk '{print $1}')
        echo "🌐 Public URL: http://$PUBLIC_IP:5000"
        echo "🏠 Local URL: http://localhost:5000"
        echo "📝 Log file: $LOG_FILE"
        return 0
    else
        echo "❌ Web dashboard is not running"
        return 1
    fi
}

case "${1:-start}" in
    start)
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    restart)
        stop_dashboard
        sleep 2
        start_dashboard
        ;;
    status)
        status_dashboard
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo "  start   - Start the web dashboard in background (default)"
        echo "  stop    - Stop the web dashboard"
        echo "  restart - Restart the web dashboard"
        echo "  status  - Check dashboard status"
        exit 1
        ;;
esac