#!/bin/bash
###############################################################################
# Advanced Multi-Instance Docker Management Script
# Supports individual service control per instance
# Instance 1: OpenAI provider (all services)
# Instance 2: DeepSeek provider (rl-bot, chart-bot, dashboard only)
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
INSTANCE_1_PORT=5000
INSTANCE_2_PORT=5001

show_help() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Advanced Multi-Instance Manager${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${CYAN}Instance 1 (OpenAI - Port 5000):${NC}"
    echo "  Services: RL Bot, Chart Bot, CrewAI Bot, Dashboard"
    echo ""
    echo -e "${CYAN}Instance 2 (DeepSeek - Port 5001):${NC}"
    echo "  Services: RL Bot, Chart Bot, CrewAI Bot, Dashboard"
    echo ""
    echo -e "${YELLOW}Usage: $0 [COMMAND] [OPTIONS]${NC}"
    echo ""
    echo -e "${GREEN}Instance Control:${NC}"
    echo "  start-1              Start all Instance 1 services (OpenAI)"
    echo "  start-2              Start all Instance 2 services (DeepSeek)"
    echo "  stop-1               Stop all Instance 1 services"
    echo "  stop-2               Stop all Instance 2 services"
    echo "  restart-1            Restart Instance 1"
    echo "  restart-2            Restart Instance 2"
    echo ""
    echo -e "${GREEN}Individual Service Control - Instance 1:${NC}"
    echo "  start-1-rl           Start RL Bot (instance 1)"
    echo "  start-1-chart        Start Chart Bot (instance 1)"
    echo "  start-1-crewai       Start CrewAI Bot (instance 1)"
    echo "  start-1-dash         Start Dashboard (instance 1)"
    echo "  stop-1-rl            Stop RL Bot (instance 1)"
    echo "  stop-1-chart         Stop Chart Bot (instance 1)"
    echo "  stop-1-crewai        Stop CrewAI Bot (instance 1)"
    echo "  stop-1-dash          Stop Dashboard (instance 1)"
    echo ""
    echo -e "${GREEN}Individual Service Control - Instance 2:${NC}"
    echo "  start-2-rl           Start RL Bot (instance 2)"
    echo "  start-2-chart        Start Chart Bot (instance 2)"
    echo "  start-2-crewai       Start CrewAI Bot (instance 2)"
    echo "  start-2-dash         Start Dashboard (instance 2)"
    echo "  stop-2-rl            Stop RL Bot (instance 2)"
    echo "  stop-2-chart         Stop Chart Bot (instance 2)"
    echo "  stop-2-crewai        Stop CrewAI Bot (instance 2)"
    echo "  stop-2-dash          Stop Dashboard (instance 2)"
    echo ""
    echo -e "${GREEN}Combined Control:${NC}"
    echo "  start-all            Start both instances (all services)"
    echo "  stop-all             Stop both instances"
    echo "  restart-all          Restart both instances"
    echo "  status               Show status of all instances"
    echo "  logs-1 [service]     Show logs (service: rl/chart/crewai/dash)"
    echo "  logs-2 [service]     Show logs (service: rl/chart/crewai/dash)"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 start-2                # Start instance 2 (all services)"
    echo "  $0 start-2-rl             # Start only RL bot on instance 2"
    echo "  $0 start-2-dash           # Start only dashboard on instance 2"
    echo "  $0 status                 # Check status"
    echo "  $0 logs-2 rl              # View RL bot logs for instance 2"
    echo ""
}

check_env() {
    if [ ! -f .env.instance1 ] || [ ! -f .env.instance2 ]; then
        echo -e "${RED}❌ Environment files not found!${NC}"
        echo -e "${YELLOW}Required files: .env.instance1, .env.instance2${NC}"
        exit 1
    fi
}

create_directories() {
    echo -e "${CYAN}📁 Creating necessary directories...${NC}"
    mkdir -p logs data data2 shared shared2
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Instance 1 Commands (OpenAI)
start_instance_1() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Starting Instance 1 (OpenAI)${NC}"
    echo -e "${BLUE}  Port: $INSTANCE_1_PORT${NC}"
    echo -e "${BLUE}========================================${NC}"
    docker compose up -d --build
    sleep 3
    echo -e "${GREEN}✅ Instance 1 started${NC}"
}

stop_instance_1() {
    echo -e "${YELLOW}🛑 Stopping Instance 1...${NC}"
    docker compose down
    echo -e "${GREEN}✅ Instance 1 stopped${NC}"
}

restart_instance_1() {
    stop_instance_1
    sleep 2
    start_instance_1
}

# Instance 1 Individual Services
start_instance_1_service() {
    local service=$1
    echo -e "${CYAN}Starting Instance 1 - $service${NC}"
    docker compose up -d $service
}

stop_instance_1_service() {
    local service=$1
    echo -e "${YELLOW}Stopping Instance 1 - $service${NC}"
    docker compose stop $service
}

# Instance 2 Commands (DeepSeek)
start_instance_2() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Starting Instance 2 (DeepSeek)${NC}"
    echo -e "${BLUE}  Port: $INSTANCE_2_PORT${NC}"
    echo -e "${BLUE}========================================${NC}"
    docker compose -f docker-compose.instance2.yml up -d --build
    sleep 3
    echo -e "${GREEN}✅ Instance 2 started${NC}"
}

stop_instance_2() {
    echo -e "${YELLOW}🛑 Stopping Instance 2...${NC}"
    docker compose -f docker-compose.instance2.yml down
    echo -e "${GREEN}✅ Instance 2 stopped${NC}"
}

restart_instance_2() {
    stop_instance_2
    sleep 2
    start_instance_2
}

# Instance 2 Individual Services
start_instance_2_service() {
    local service=$1
    echo -e "${CYAN}Starting Instance 2 - $service${NC}"
    docker compose -f docker-compose.instance2.yml up -d $service
}

stop_instance_2_service() {
    local service=$1
    echo -e "${YELLOW}Stopping Instance 2 - $service${NC}"
    docker compose -f docker-compose.instance2.yml stop $service
}

# Combined Commands
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

restart_all() {
    stop_all
    sleep 2
    start_all
}

# Status Display
show_status() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Multi-Instance Status${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "${CYAN}Instance 1 - OpenAI (Port $INSTANCE_1_PORT):${NC}"
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
    echo -e "${CYAN}Instance 2 - DeepSeek (Port $INSTANCE_2_PORT):${NC}"
    echo "-----------------------------------"

    # Check instance 2 services
    RL_2=$(docker compose -f docker-compose.instance2.yml ps rl-bot-2 2>/dev/null | grep "Up" || echo "")
    CHART_2=$(docker compose -f docker-compose.instance2.yml ps chart-bot-2 2>/dev/null | grep "Up" || echo "")
    CREW_2=$(docker compose -f docker-compose.instance2.yml ps crewai-bot-2 2>/dev/null | grep "Up" || echo "")
    DASH_2=$(docker compose -f docker-compose.instance2.yml ps web-dashboard-2 2>/dev/null | grep "Up" || echo "")

    [ -n "$RL_2" ] && echo -e "  ${GREEN}✅ RL Bot${NC}" || echo -e "  ${RED}❌ RL Bot${NC}"
    [ -n "$CHART_2" ] && echo -e "  ${GREEN}✅ Chart Bot${NC}" || echo -e "  ${RED}❌ Chart Bot${NC}"
    [ -n "$CREW_2" ] && echo -e "  ${GREEN}✅ CrewAI Bot${NC}" || echo -e "  ${RED}❌ CrewAI Bot${NC}"
    [ -n "$DASH_2" ] && echo -e "  ${GREEN}✅ Dashboard${NC}" || echo -e "  ${RED}❌ Dashboard${NC}"

    echo ""
    echo -e "${MAGENTA}🌐 Web Dashboards:${NC}"
    echo "  Instance 1 (OpenAI):  http://localhost:$INSTANCE_1_PORT"
    echo "  Instance 2 (DeepSeek): http://localhost:$INSTANCE_2_PORT"
    echo ""
}

# Logs Display
show_logs_1() {
    local service=${1:-""}

    case $service in
        rl)
            echo -e "${CYAN}📝 Instance 1 - RL Bot Logs${NC}"
            docker compose logs -f rl-bot
            ;;
        chart)
            echo -e "${CYAN}📝 Instance 1 - Chart Bot Logs${NC}"
            docker compose logs -f chart-bot
            ;;
        crewai)
            echo -e "${CYAN}📝 Instance 1 - CrewAI Bot Logs${NC}"
            docker compose logs -f crewai-bot
            ;;
        dash)
            echo -e "${CYAN}📝 Instance 1 - Dashboard Logs${NC}"
            docker compose logs -f web-dashboard
            ;;
        *)
            echo -e "${CYAN}📝 Instance 1 - All Logs${NC}"
            docker compose logs -f
            ;;
    esac
}

show_logs_2() {
    local service=${1:-""}

    case $service in
        rl)
            echo -e "${CYAN}📝 Instance 2 - RL Bot Logs${NC}"
            docker compose -f docker-compose.instance2.yml logs -f rl-bot-2
            ;;
        chart)
            echo -e "${CYAN}📝 Instance 2 - Chart Bot Logs${NC}"
            docker compose -f docker-compose.instance2.yml logs -f chart-bot-2
            ;;
        crewai)
            echo -e "${CYAN}📝 Instance 2 - CrewAI Bot Logs${NC}"
            docker compose -f docker-compose.instance2.yml logs -f crewai-bot-2
            ;;
        dash)
            echo -e "${CYAN}📝 Instance 2 - Dashboard Logs${NC}"
            docker compose -f docker-compose.instance2.yml logs -f web-dashboard-2
            ;;
        *)
            echo -e "${CYAN}📝 Instance 2 - All Logs${NC}"
            docker compose -f docker-compose.instance2.yml logs -f
            ;;
    esac
}

# Main script logic
cd "$SCRIPT_DIR" || exit 1

case "$1" in
    # Instance 1 Controls
    start-1) check_env; create_directories; start_instance_1 ;;
    stop-1) stop_instance_1 ;;
    restart-1) restart_instance_1 ;;

    # Instance 1 Individual Services
    start-1-rl) start_instance_1_service "rl-bot" ;;
    start-1-chart) start_instance_1_service "chart-bot" ;;
    start-1-crewai) start_instance_1_service "crewai-bot" ;;
    start-1-dash) start_instance_1_service "web-dashboard" ;;
    stop-1-rl) stop_instance_1_service "rl-bot" ;;
    stop-1-chart) stop_instance_1_service "chart-bot" ;;
    stop-1-crewai) stop_instance_1_service "crewai-bot" ;;
    stop-1-dash) stop_instance_1_service "web-dashboard" ;;

    # Instance 2 Controls
    start-2) check_env; create_directories; start_instance_2 ;;
    stop-2) stop_instance_2 ;;
    restart-2) restart_instance_2 ;;

    # Instance 2 Individual Services
    start-2-rl) start_instance_2_service "rl-bot-2" ;;
    start-2-chart) start_instance_2_service "chart-bot-2" ;;
    start-2-crewai) start_instance_2_service "crewai-bot-2" ;;
    start-2-dash) start_instance_2_service "web-dashboard-2" ;;
    stop-2-rl) stop_instance_2_service "rl-bot-2" ;;
    stop-2-chart) stop_instance_2_service "chart-bot-2" ;;
    stop-2-crewai) stop_instance_2_service "crewai-bot-2" ;;
    stop-2-dash) stop_instance_2_service "web-dashboard-2" ;;

    # Combined Controls
    start-all) start_all ;;
    stop-all) stop_all ;;
    restart-all) restart_all ;;
    status) show_status ;;

    # Logs
    logs-1) show_logs_1 "$2" ;;
    logs-2) show_logs_2 "$2" ;;

    # Help
    help|--help|-h|*) show_help ;;
esac

echo ""
