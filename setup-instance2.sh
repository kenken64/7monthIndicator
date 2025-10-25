#!/bin/bash
###############################################################################
# Setup Script for Instance 2
# Creates necessary directories and files for the second instance
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setting Up Instance 2${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$SCRIPT_DIR" || exit 1

# Create directories
echo -e "${BLUE}📁 Creating directories for Instance 2...${NC}"
mkdir -p data2
mkdir -p shared2
mkdir -p logs

echo -e "${GREEN}✅ Directories created:${NC}"
echo "   - data2/     (Instance 2 data directory)"
echo "   - shared2/   (Instance 2 shared files)"
echo "   - logs/      (Shared logs directory)"
echo ""

# Create empty database files (will be populated by bot)
echo -e "${BLUE}📄 Creating empty database files...${NC}"
touch trading_bot_2.db
touch trading_data_2.db
touch trading_bot_2.log
touch chart_analysis_2.log
touch news_sentiment_2.json

echo -e "${GREEN}✅ Files created:${NC}"
echo "   - trading_bot_2.db"
echo "   - trading_data_2.db"
echo "   - trading_bot_2.log"
echo "   - chart_analysis_2.log"
echo "   - news_sentiment_2.json"
echo ""

# Set permissions
echo -e "${BLUE}🔒 Setting permissions...${NC}"
chmod 755 data2
chmod 755 shared2
chmod 644 trading_bot_2.db trading_data_2.db
chmod 644 trading_bot_2.log chart_analysis_2.log
chmod 644 news_sentiment_2.json

echo -e "${GREEN}✅ Permissions set${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Instance 2 is ready to start!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start instance 2: ${YELLOW}./docker-multi-instance.sh start-2${NC}"
echo "  2. Check status:     ${YELLOW}./docker-multi-instance.sh status${NC}"
echo "  3. View logs:        ${YELLOW}./docker-multi-instance.sh logs-2${NC}"
echo "  4. Access dashboard: ${YELLOW}http://localhost:5001${NC}"
echo ""
echo "Or start both instances:"
echo "  ${YELLOW}./docker-multi-instance.sh start${NC}"
echo ""
