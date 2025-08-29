#!/bin/bash
# Restart Web Dashboard, RL Bot, and Chart Analysis Bot
# Usage: ./restart_both.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_header() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}🔄 Trading Bot System Restart Script${NC}"
    echo -e "${PURPLE}   (Web Dashboard + RL Bot + Chart Bot)${NC}"
    echo -e "${PURPLE}================================================${NC}"
    echo ""
}

print_header

# Check if scripts exist
if [ ! -f "start_web_dashboard.sh" ]; then
    print_error "start_web_dashboard.sh not found!"
    exit 1
fi

if [ ! -f "start_rl_bot.sh" ]; then
    print_error "start_rl_bot.sh not found!"
    exit 1
fi

if [ ! -f "start_chart_bot.sh" ]; then
    print_error "start_chart_bot.sh not found!"
    exit 1
fi

# Make sure scripts are executable
chmod +x start_web_dashboard.sh start_rl_bot.sh start_chart_bot.sh

print_info "🛑 Stopping Web Dashboard..."
./start_web_dashboard.sh stop
sleep 2

print_info "🛑 Stopping RL Bot..."
./start_rl_bot.sh stop
sleep 2

print_info "🛑 Stopping Chart Analysis Bot..."
./start_chart_bot.sh stop
sleep 2

print_info "⚡ Starting RL Bot..."
./start_rl_bot.sh start

if [ $? -eq 0 ]; then
    print_status "✅ RL Bot started successfully"
    sleep 3
    
    print_info "🤖 Starting Chart Analysis Bot..."
    ./start_chart_bot.sh start
    
    if [ $? -eq 0 ]; then
        print_status "✅ Chart Analysis Bot started successfully"
        sleep 2
        
        print_info "🌐 Starting Web Dashboard..."
        ./start_web_dashboard.sh start
        
        if [ $? -eq 0 ]; then
            print_status "✅ Web Dashboard started successfully"
            echo ""
            print_status "🎉 All services restarted successfully!"
            echo ""
            print_info "📊 Web Dashboard URLs:"
            PUBLIC_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
            echo -e "${BLUE}   Public: http://$PUBLIC_IP:5000${NC}"
            echo -e "${BLUE}   Local:  http://localhost:5000${NC}"
            echo ""
            print_info "🤖 Service Status:"
            ./start_rl_bot.sh status
            ./start_chart_bot.sh status
            echo ""
            print_info "📝 Monitor logs:"
            echo -e "${BLUE}   RL Bot:     tail -f logs/rl_bot_main.log${NC}"
            echo -e "${BLUE}   Dashboard:  tail -f web_dashboard.log${NC}"
            echo -e "${BLUE}   Chart Bot:  tail -f chart_analysis_bot.log${NC}"
        else
            print_error "Failed to start Web Dashboard"
            exit 1
        fi
    else
        print_error "Failed to start Chart Analysis Bot"
        exit 1
    fi
else
    print_error "Failed to start RL Bot"
    exit 1
fi

print_status "🚀 System restart complete!"