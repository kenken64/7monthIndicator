#!/bin/bash
###############################################################################
# Docker Restart Script for Trading Bot System
# Stops and restarts all Docker containers following restart_both.sh logic
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Restarting Trading System (Docker)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$SCRIPT_DIR" || exit 1

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Please create a .env file from .env.example${NC}"
    echo -e "${YELLOW}cp .env.example .env${NC}"
    exit 1
fi

# Stop all running containers
echo -e "${YELLOW}🛑 Stopping all Docker containers...${NC}"
docker compose down

sleep 2

echo -e "${GREEN}✅ All containers stopped${NC}"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs
mkdir -p data

# Build and start services
echo -e "${GREEN}🚀 Building and starting Docker containers...${NC}"
echo ""

docker compose up -d --build

sleep 5

# Check container status
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Container Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check each service
RL_STATUS=$(docker compose ps rl-bot | grep "Up" || echo "")
CHART_STATUS=$(docker compose ps chart-bot | grep "Up" || echo "")
DASH_STATUS=$(docker compose ps web-dashboard | grep "Up" || echo "")

if [ -n "$RL_STATUS" ]; then
    echo -e "${GREEN}✅ RL Trading Bot is running${NC}"
else
    echo -e "${RED}❌ RL Trading Bot failed to start${NC}"
    echo -e "${YELLOW}Check logs: docker compose logs rl-bot${NC}"
fi

if [ -n "$CHART_STATUS" ]; then
    echo -e "${GREEN}✅ Chart Analysis Bot is running${NC}"
else
    echo -e "${RED}❌ Chart Analysis Bot failed to start${NC}"
    echo -e "${YELLOW}Check logs: docker compose logs chart-bot${NC}"
fi

if [ -n "$DASH_STATUS" ]; then
    echo -e "${GREEN}✅ Web Dashboard is running${NC}"
else
    echo -e "${RED}❌ Web Dashboard failed to start${NC}"
    echo -e "${YELLOW}Check logs: docker compose logs web-dashboard${NC}"
fi

echo ""
echo -e "${BLUE}📝 Monitor logs:${NC}"
echo "   All services:    docker compose logs -f"
echo "   RL Bot:          docker compose logs -f rl-bot"
echo "   Chart Bot:       docker compose logs -f chart-bot"
echo "   Dashboard:       docker compose logs -f web-dashboard"
echo ""
echo -e "${BLUE}🌐 Web Dashboard: http://localhost:5000${NC}"
echo ""
echo -e "${BLUE}📊 Container stats:${NC}"
echo "   docker compose ps"
echo "   docker stats"
echo ""
