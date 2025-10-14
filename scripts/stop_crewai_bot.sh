#!/bin/bash
###############################################################################
# Stop CrewAI-Enhanced Trading Bot
# Gracefully stops the running bot
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/crewai_bot.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping CrewAI Trading Bot${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
    echo "Bot may not be running or was not started with start script"
    exit 1
fi

# Read PID
BOT_PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$BOT_PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Bot process (PID: $BOT_PID) is not running${NC}"
    echo "Removing stale PID file..."
    rm -f "$PID_FILE"
    exit 0
fi

# Stop the bot
echo -e "${YELLOW}🛑 Stopping bot (PID: $BOT_PID)...${NC}"
kill "$BOT_PID"

# Wait for graceful shutdown
echo -n "Waiting for bot to stop"
for i in {1..10}; do
    if ! ps -p "$BOT_PID" > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Bot stopped successfully${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo -n "."
    sleep 1
done

# Force kill if still running
echo ""
echo -e "${YELLOW}⚠️  Bot did not stop gracefully, forcing shutdown...${NC}"
kill -9 "$BOT_PID" 2>/dev/null

sleep 2

if ! ps -p "$BOT_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bot forcefully stopped${NC}"
    rm -f "$PID_FILE"
else
    echo -e "${RED}❌ Failed to stop bot${NC}"
    exit 1
fi
