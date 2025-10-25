#!/bin/bash
###############################################################################
# Multi-Instance Docker Management Script
# Manages multiple trading bot instances on different ports
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
INSTANCE_1_PORT=5000
INSTANCE_2_PORT=5001

show_help() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Multi-Instance Trading Bot Manager${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start          Start all instances (both port 5000 and 5001)"
    echo "  stop           Stop all instances"
    echo "  restart        Restart all instances"
    echo "  status         Show status of all instances"
    echo "  logs           Show logs from all instances"
    echo ""
    echo "  start-1        Start instance 1 only (port 5000)"
    echo "  start-2        Start instance 2 only (port 5001)"
    echo "  stop-1         Stop instance 1 only"
    echo "  stop-2         Stop instance 2 only"
    echo "  logs-1         Show logs from instance 1"
    echo "  logs-2         Show logs from instance 2"
    echo ""
    echo "Examples:"
    echo "  $0 start       # Start both instances"
    echo "  $0 status      # Check status of all instances"
    echo "  $0 logs-1      # View logs for instance 1"
    echo ""
}

check_env() {
    if [ ! -f .env ]; then
        echo -e "${RED}❌ .env file not found!${NC}"
        echo -e "${YELLOW}Please create a .env file from .env.example${NC}"
        exit 1
    fi
}

create_directories() {
    echo -e "${CYAN}📁 Creating necessary directories...${NC}"
    mkdir -p logs data data2 shared shared2
    echo -e "${GREEN}✅ Directories created${NC}"
}

start_instance_1() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Starting Instance 1 (Port $INSTANCE_1_PORT)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    docker compose up -d --build

    sleep 3
    echo -e "${GREEN}✅ Instance 1 started on port $INSTANCE_1_PORT${NC}"
}

start_instance_2() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Starting Instance 2 (Port $INSTANCE_2_PORT)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    docker compose -f docker-compose.multi-instance.yml up -d --build

    sleep 3
    echo -e "${GREEN}✅ Instance 2 started on port $INSTANCE_2_PORT${NC}"
}

start_all() {
    cd "$SCRIPT_DIR" || exit 1
    check_env
    create_directories

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Starting All Instances${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    start_instance_1
    echo ""
    start_instance_2
    echo ""

    show_status
}

stop_instance_1() {
    echo -e "${YELLOW}🛑 Stopping Instance 1...${NC}"
    docker compose down
    echo -e "${GREEN}✅ Instance 1 stopped${NC}"
}

stop_instance_2() {
    echo -e "${YELLOW}🛑 Stopping Instance 2...${NC}"
    docker compose -f docker-compose.multi-instance.yml down
    echo -e "${GREEN}✅ Instance 2 stopped${NC}"
}

stop_all() {
    cd "$SCRIPT_DIR" || exit 1

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Stopping All Instances${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    stop_instance_1
    echo ""
    stop_instance_2
    echo ""
}

show_status() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Multi-Instance Status${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "${CYAN}Instance 1 (Port $INSTANCE_1_PORT):${NC}"
    echo "-----------------------------------"

    # Check instance 1 services
    RL_1=$(docker compose ps rl-bot 2>/dev/null | grep "Up" || echo "")
    CHART_1=$(docker compose ps chart-bot 2>/dev/null | grep "Up" || echo "")
    CREW_1=$(docker compose ps crewai-bot 2>/dev/null | grep "Up" || echo "")
    DASH_1=$(docker compose ps web-dashboard 2>/dev/null | grep "Up" || echo "")

    [ -n "$RL_1" ] && echo -e "  ${GREEN}✅ RL Bot${NC}" || echo -e "  ${RED}❌ RL Bot${NC}"
    [ -n "$CHART_1" ] && echo -e "  ${GREEN}✅ Chart Bot${NC}" || echo -e "  ${RED}❌ Chart Bot${NC}"
    [ -n "$CREW_1" ] && echo -e "  ${GREEN}✅ CrewAI Bot${NC}" || echo -e "  ${RED}❌ CrewAI Bot${NC}"
    [ -n "$DASH_1" ] && echo -e "  ${GREEN}✅ Dashboard${NC}" || echo -e "  ${RED}❌ Dashboard${NC}"

    echo ""
    echo -e "${CYAN}Instance 2 (Port $INSTANCE_2_PORT):${NC}"
    echo "-----------------------------------"

    # Check instance 2 services
    RL_2=$(docker compose -f docker-compose.multi-instance.yml ps rl-bot-2 2>/dev/null | grep "Up" || echo "")
    CHART_2=$(docker compose -f docker-compose.multi-instance.yml ps chart-bot-2 2>/dev/null | grep "Up" || echo "")
    CREW_2=$(docker compose -f docker-compose.multi-instance.yml ps crewai-bot-2 2>/dev/null | grep "Up" || echo "")
    DASH_2=$(docker compose -f docker-compose.multi-instance.yml ps web-dashboard-2 2>/dev/null | grep "Up" || echo "")

    [ -n "$RL_2" ] && echo -e "  ${GREEN}✅ RL Bot${NC}" || echo -e "  ${RED}❌ RL Bot${NC}"
    [ -n "$CHART_2" ] && echo -e "  ${GREEN}✅ Chart Bot${NC}" || echo -e "  ${RED}❌ Chart Bot${NC}"
    [ -n "$CREW_2" ] && echo -e "  ${GREEN}✅ CrewAI Bot${NC}" || echo -e "  ${RED}❌ CrewAI Bot${NC}"
    [ -n "$DASH_2" ] && echo -e "  ${GREEN}✅ Dashboard${NC}" || echo -e "  ${RED}❌ Dashboard${NC}"

    echo ""
    echo -e "${BLUE}🌐 Web Dashboards:${NC}"
    echo "  Instance 1: http://localhost:$INSTANCE_1_PORT"
    echo "  Instance 2: http://localhost:$INSTANCE_2_PORT"
    echo ""
}

show_logs_1() {
    echo -e "${CYAN}📝 Instance 1 Logs (Press Ctrl+C to exit)${NC}"
    echo ""
    docker compose logs -f
}

show_logs_2() {
    echo -e "${CYAN}📝 Instance 2 Logs (Press Ctrl+C to exit)${NC}"
    echo ""
    docker compose -f docker-compose.multi-instance.yml logs -f
}

show_logs_all() {
    echo -e "${CYAN}📝 All Instances Logs${NC}"
    echo "Choose which logs to view:"
    echo "  1) Instance 1 only"
    echo "  2) Instance 2 only"
    echo "  3) Both (split terminal recommended)"
    echo ""
    read -p "Selection [1-3]: " choice

    case $choice in
        1) show_logs_1 ;;
        2) show_logs_2 ;;
        3)
            echo -e "${YELLOW}Opening logs in separate windows...${NC}"
            echo "Run these in separate terminals:"
            echo "  Terminal 1: docker compose logs -f"
            echo "  Terminal 2: docker compose -f docker-compose.multi-instance.yml logs -f"
            ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
}

restart_all() {
    stop_all
    sleep 2
    start_all
}

# Main script logic
cd "$SCRIPT_DIR" || exit 1

case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs_all
        ;;
    start-1)
        check_env
        create_directories
        start_instance_1
        ;;
    start-2)
        check_env
        create_directories
        start_instance_2
        ;;
    stop-1)
        stop_instance_1
        ;;
    stop-2)
        stop_instance_2
        ;;
    logs-1)
        show_logs_1
        ;;
    logs-2)
        show_logs_2
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac

echo ""
