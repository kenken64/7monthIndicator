#!/bin/bash
###############################################################################
# Start CrewAI-Enhanced Trading Bot
# Launches the RL + CrewAI integrated trading bot with all protections active
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BOT_SCRIPT="$PROJECT_DIR/rl_bot_with_crewai.py"
PID_FILE="$PROJECT_DIR/crewai_bot.pid"
LOG_FILE="$PROJECT_DIR/logs/crewai_bot.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CrewAI-Enhanced Trading Bot Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if bot is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Bot is already running (PID: $OLD_PID)${NC}"
        echo ""
        echo "Options:"
        echo "  1. Stop current bot: ./scripts/stop_crewai_bot.sh"
        echo "  2. View status: ./scripts/status_crewai_bot.sh"
        echo "  3. View logs: tail -f $LOG_FILE"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Stale PID file found, removing...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Check if bot script exists
if [ ! -f "$BOT_SCRIPT" ]; then
    echo -e "${RED}❌ Error: Bot script not found at $BOT_SCRIPT${NC}"
    exit 1
fi

# Check if Python virtual environment exists
if [ -d "$PROJECT_DIR/venv" ]; then
    echo -e "${GREEN}✅ Activating virtual environment${NC}"
    source "$PROJECT_DIR/venv/bin/activate"
elif [ -d "$PROJECT_DIR/.venv" ]; then
    echo -e "${GREEN}✅ Activating virtual environment${NC}"
    source "$PROJECT_DIR/.venv/bin/activate"
else
    echo -e "${YELLOW}⚠️  No virtual environment found${NC}"
fi

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Check for required environment variables
echo -e "${BLUE}🔍 Checking configuration...${NC}"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env file with:"
    echo "  - BINANCE_API_KEY"
    echo "  - BINANCE_SECRET_KEY"
    echo "  - OPENAI_API_KEY"
    echo "  - TELEGRAM_BOT_TOKEN (optional)"
    exit 1
fi

# Check for OpenAI API key (required for CrewAI)
if ! grep -q "OPENAI_API_KEY" "$PROJECT_DIR/.env"; then
    echo -e "${RED}❌ Error: OPENAI_API_KEY not found in .env file${NC}"
    echo "CrewAI requires OpenAI API key for AI agents"
    exit 1
fi

echo -e "${GREEN}✅ Configuration valid${NC}"
echo ""

# Display feature status
echo -e "${BLUE}🚀 Starting bot with features:${NC}"
echo "  ✅ RL-Enhanced Signals"
echo "  ✅ Circuit Breaker Protection"
echo "  ✅ Market Spike Detection"
echo "  ✅ AI Agent Analysis"
echo "  ✅ Telegram Notifications"
echo ""
echo -e "${BLUE}📊 Trading Settings:${NC}"
echo "  • Symbol: SUIUSDC"
echo "  • Position Size: 2% of account"
echo "  • Leverage: 50x"
echo "  • Take Profit: 15%"
echo "  • Stop Loss: 5%"
echo ""

# Start the bot in background
echo -e "${GREEN}🏁 Launching bot...${NC}"

cd "$PROJECT_DIR" || exit 1

# Start bot and capture PID
nohup python3 "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
BOT_PID=$!

# Save PID
echo "$BOT_PID" > "$PID_FILE"

# Wait a moment to see if it starts successfully
sleep 3

if ps -p "$BOT_PID" > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}✅ Bot started successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Bot Information:${NC}"
    echo "  • PID: $BOT_PID"
    echo "  • Log: $LOG_FILE"
    echo "  • PID File: $PID_FILE"
    echo ""
    echo -e "${BLUE}🛠️  Management Commands:${NC}"
    echo "  • View status: ./scripts/status_crewai_bot.sh"
    echo "  • Stop bot: ./scripts/stop_crewai_bot.sh"
    echo "  • View logs: tail -f $LOG_FILE"
    echo "  • Pause trading: touch bot_pause.flag"
    echo "  • Resume trading: rm bot_pause.flag"
    echo ""
    echo -e "${BLUE}🔍 Initial log output:${NC}"
    tail -20 "$LOG_FILE"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Bot is now running in background${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo ""
    echo -e "${RED}❌ Bot failed to start${NC}"
    echo ""
    echo "Check logs for errors:"
    echo "  tail -50 $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
