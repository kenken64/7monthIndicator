#!/bin/bash
###############################################################################
# Check Status of CrewAI-Enhanced Trading Bot
# Shows detailed status including circuit breaker state
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/crewai_bot.pid"
LOG_FILE="$PROJECT_DIR/logs/crewai_bot.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CrewAI Trading Bot Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if bot is running
if [ -f "$PID_FILE" ]; then
    BOT_PID=$(cat "$PID_FILE")

    if ps -p "$BOT_PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Status: RUNNING${NC}"
        echo -e "${CYAN}📋 Process Information:${NC}"
        echo "   PID: $BOT_PID"

        # Get CPU and memory usage
        CPU=$(ps -p "$BOT_PID" -o %cpu= | xargs)
        MEM=$(ps -p "$BOT_PID" -o %mem= | xargs)
        ELAPSED=$(ps -p "$BOT_PID" -o etime= | xargs)

        echo "   CPU: ${CPU}%"
        echo "   Memory: ${MEM}%"
        echo "   Uptime: $ELAPSED"
    else
        echo -e "${RED}❌ Status: STOPPED${NC}"
        echo "   Stale PID file found (process not running)"
    fi
else
    echo -e "${RED}❌ Status: STOPPED${NC}"
    echo "   No PID file found"
fi

echo ""

# Check if pause flag exists
if [ -f "$PROJECT_DIR/bot_pause.flag" ]; then
    echo -e "${YELLOW}⏸️  Trading: PAUSED${NC}"
    echo "   Bot is generating signals but not executing trades"
    echo "   Remove pause: rm bot_pause.flag"
else
    echo -e "${GREEN}▶️  Trading: ACTIVE${NC}"
    echo "   Bot is executing trades based on signals"
fi

echo ""

# Check log file
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
    LOG_LINES=$(wc -l < "$LOG_FILE")
    echo -e "${CYAN}📄 Log File:${NC}"
    echo "   Path: $LOG_FILE"
    echo "   Size: $LOG_SIZE"
    echo "   Lines: $LOG_LINES"
    echo ""

    # Show last few log entries
    echo -e "${CYAN}📜 Recent Log Entries (last 10 lines):${NC}"
    echo "----------------------------------------"
    tail -10 "$LOG_FILE" | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  No log file found${NC}"
fi

echo ""

# Check configuration
echo -e "${CYAN}⚙️  Configuration:${NC}"
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "   .env file: ✅ Found"

    # Check for required keys (without displaying them)
    if grep -q "BINANCE_API_KEY" "$PROJECT_DIR/.env"; then
        echo "   Binance API: ✅ Configured"
    else
        echo "   Binance API: ❌ Missing"
    fi

    if grep -q "OPENAI_API_KEY" "$PROJECT_DIR/.env"; then
        echo "   OpenAI API: ✅ Configured"
    else
        echo "   OpenAI API: ❌ Missing"
    fi

    if grep -q "TELEGRAM_BOT_TOKEN" "$PROJECT_DIR/.env"; then
        echo "   Telegram: ✅ Configured"
    else
        echo "   Telegram: ⚠️  Not configured"
    fi
else
    echo "   .env file: ❌ Not found"
fi

echo ""

# Check CrewAI configuration
if [ -f "$PROJECT_DIR/config/crewai_spike_agent.yaml" ]; then
    echo -e "${CYAN}🤖 CrewAI Configuration:${NC}"
    echo "   Config file: ✅ Found"

    # Extract key settings
    if grep -q "enabled: true" "$PROJECT_DIR/config/crewai_spike_agent.yaml"; then
        echo "   Circuit Breaker: ✅ Enabled"
    else
        echo "   Circuit Breaker: ❌ Disabled"
    fi

    # Get BTC threshold
    BTC_THRESHOLD=$(grep "dump_1h_percent:" "$PROJECT_DIR/config/crewai_spike_agent.yaml" | head -1 | awk '{print $2}')
    if [ -n "$BTC_THRESHOLD" ]; then
        echo "   BTC Crash Threshold: ${BTC_THRESHOLD}%"
    fi
else
    echo -e "${YELLOW}⚠️  CrewAI config not found${NC}"
fi

echo ""

# Check database
if [ -f "$PROJECT_DIR/data/trading_bot.db" ]; then
    echo -e "${CYAN}💾 Database:${NC}"
    DB_SIZE=$(du -h "$PROJECT_DIR/data/trading_bot.db" | cut -f1)
    echo "   Database: ✅ Found"
    echo "   Size: $DB_SIZE"

    # Count recent spike detections if sqlite3 is available
    if command -v sqlite3 &> /dev/null; then
        SPIKE_COUNT=$(sqlite3 "$PROJECT_DIR/data/trading_bot.db" "SELECT COUNT(*) FROM spike_detections WHERE timestamp > datetime('now', '-24 hours');" 2>/dev/null || echo "N/A")
        echo "   Spikes (24h): $SPIKE_COUNT"
    fi
else
    echo -e "${YELLOW}⚠️  Database not found${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

# Show quick commands
echo ""
echo -e "${CYAN}🛠️  Quick Commands:${NC}"
echo "   Start bot: ./scripts/start_crewai_bot.sh"
echo "   Stop bot: ./scripts/stop_crewai_bot.sh"
echo "   View logs: tail -f $LOG_FILE"
echo "   Pause trading: touch bot_pause.flag"
echo "   Resume trading: rm bot_pause.flag"
