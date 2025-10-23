#!/bin/bash
###############################################################################
# Docker Prerequisites Check Script
# Verifies system has required tools before running Docker deployment
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Docker Prerequisites Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ERRORS=0

# Check Docker
echo -n "Checking Docker installation... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✅ Found (version $DOCKER_VERSION)${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}Install Docker: https://docs.docker.com/get-docker/${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker Compose
echo -n "Checking Docker Compose... "
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✅ Found (version $COMPOSE_VERSION)${NC}"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short)
    echo -e "${GREEN}✅ Found (version $COMPOSE_VERSION - plugin)${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}Install Docker Compose: https://docs.docker.com/compose/install/${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check if Docker daemon is running
echo -n "Checking Docker daemon... "
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
    echo -e "${YELLOW}Start Docker daemon: sudo systemctl start docker${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check .env file
echo -n "Checking .env file... "
if [ -f .env ]; then
    echo -e "${GREEN}✅ Found${NC}"

    # Check for required variables
    echo "Checking required environment variables..."
    REQUIRED_VARS=("BINANCE_API_KEY" "BINANCE_SECRET_KEY" "OPENAI_API_KEY" "BOT_CONTROL_PIN")

    for VAR in "${REQUIRED_VARS[@]}"; do
        echo -n "  - $VAR... "
        if grep -q "^${VAR}=" .env && ! grep -q "^${VAR}=.*_here" .env; then
            echo -e "${GREEN}✅${NC}"
        else
            echo -e "${RED}❌ Not configured${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}Create .env file: cp .env.example .env${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check disk space
echo -n "Checking disk space... "
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -gt 5 ]; then
    echo -e "${GREEN}✅ ${AVAILABLE_SPACE}GB available${NC}"
else
    echo -e "${YELLOW}⚠️  Only ${AVAILABLE_SPACE}GB available (5GB+ recommended)${NC}"
fi

# Check memory
echo -n "Checking available memory... "
if command -v free &> /dev/null; then
    AVAILABLE_MEM=$(free -g | grep Mem | awk '{print $7}')
    if [ "$AVAILABLE_MEM" -gt 2 ]; then
        echo -e "${GREEN}✅ ${AVAILABLE_MEM}GB available${NC}"
    else
        echo -e "${YELLOW}⚠️  Only ${AVAILABLE_MEM}GB available (2GB+ recommended)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot determine (free command not found)${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Review your .env configuration"
    echo "  2. Run: ./docker-restart.sh"
    echo "  3. Access dashboard at: http://localhost:5000"
else
    echo -e "${RED}❌ $ERRORS issue(s) found. Please fix before deploying.${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""
