#!/bin/bash
###############################################################################
# Simple Restart Script for Trading Bot and Web Dashboard
# Stops and restarts both RL bot and web dashboard
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Restarting Trading System${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$PROJECT_DIR" || exit 1

# Stop all running processes
echo -e "${YELLOW}🛑 Stopping all services...${NC}"

# Kill by process name
pkill -f "rl_bot_ready.py"
pkill -f "chart_analysis_bot.py"
pkill -f "web_dashboard.py"

sleep 2

# Verify stopped
if pgrep -f "rl_bot_ready.py\|chart_analysis_bot.py\|web_dashboard.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Force killing remaining processes...${NC}"
    pkill -9 -f "rl_bot_ready.py"
    pkill -9 -f "chart_analysis_bot.py"
    pkill -9 -f "web_dashboard.py"
    sleep 1
fi

echo -e "${GREEN}✅ All services stopped${NC}"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Start services
echo -e "${GREEN}🚀 Starting services...${NC}"
echo ""

# Start RL Trading Bot
echo -e "${BLUE}Starting RL Trading Bot...${NC}"
nohup python3 rl_bot_ready.py > logs/trading_bot.log 2>&1 &
RL_BOT_PID=$!
echo $RL_BOT_PID > rl_bot.pid
sleep 2

if ps -p $RL_BOT_PID > /dev/null; then
    echo -e "${GREEN}✅ RL Bot started (PID: $RL_BOT_PID)${NC}"
else
    echo -e "${RED}❌ RL Bot failed to start${NC}"
    echo -e "${YELLOW}Check logs: tail -f logs/trading_bot.log${NC}"
fi

# Start Chart Analysis Bot
echo -e "${BLUE}Starting Chart Analysis Bot...${NC}"
nohup python3 chart_analysis_bot.py > logs/chart_analysis.log 2>&1 &
CHART_PID=$!
echo $CHART_PID > chart_analysis_bot.pid
sleep 2

if ps -p $CHART_PID > /dev/null; then
    echo -e "${GREEN}✅ Chart Bot started (PID: $CHART_PID)${NC}"
else
    echo -e "${RED}❌ Chart Bot failed to start${NC}"
    echo -e "${YELLOW}Check logs: tail -f logs/chart_analysis.log${NC}"
fi

# Start Web Dashboard
echo -e "${BLUE}Starting Web Dashboard...${NC}"
nohup python3 web_dashboard.py > logs/web_dashboard.log 2>&1 &
DASH_PID=$!
echo $DASH_PID > web_dashboard.pid
sleep 2

if ps -p $DASH_PID > /dev/null; then
    echo -e "${GREEN}✅ Web Dashboard started (PID: $DASH_PID)${NC}"
else
    echo -e "${RED}❌ Web Dashboard failed to start${NC}"
    echo -e "${YELLOW}Check logs: tail -f logs/web_dashboard.log${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Service Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Show running processes
ps aux | grep -E "rl_bot_ready|chart_analysis_bot|web_dashboard" | grep python | grep -v grep | awk '{printf "✅ %s (PID: %s, CPU: %s%%, Mem: %s%%)\n", $11, $2, $3, $4}'

echo ""
echo -e "${BLUE}📝 Monitor logs:${NC}"
echo "   RL Bot:      tail -f logs/trading_bot.log"
echo "   Chart Bot:   tail -f logs/chart_analysis.log"
echo "   Dashboard:   tail -f logs/web_dashboard.log"
echo ""
echo -e "${BLUE}🌐 Web Dashboard: http://localhost:5000${NC}"
echo ""
