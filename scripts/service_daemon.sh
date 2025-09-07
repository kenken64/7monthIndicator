#!/bin/bash
# Service daemon script for systemd - starts all services using existing scripts
# This runs in foreground mode suitable for systemd Type=simple

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

log_info "🚀 Starting Trading Bot System Daemon..."

# Set global environment
export PROJECT_ROOT="$PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Service definitions: script_name:description
services=(
    "start_rl_bot.sh:🤖 RL Trading Bot"
    "start_chart_bot.sh:📊 Chart Analysis Bot"
    "start_web_dashboard.sh:🌐 Web Dashboard"
)

# Function to stop all services on exit
cleanup() {
    log_info "🛑 Stopping all services..."
    
    # Stop services using the same scripts but with stop command
    if [ -f "start_web_dashboard.sh" ]; then
        log_info "Stopping Web Dashboard..."
        ./start_web_dashboard.sh stop
    fi
    
    if [ -f "start_rl_bot.sh" ]; then
        log_info "Stopping RL Bot..."
        ./start_rl_bot.sh stop
    fi
    
    if [ -f "start_chart_bot.sh" ]; then
        log_info "Stopping Chart Bot..."
        ./start_chart_bot.sh stop
    fi
    
    log_info "👋 Service daemon shutting down"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start all services
log_info "⚡ Starting all services using existing scripts..."
for service_info in "${services[@]}"; do
    script=$(echo $service_info | cut -d: -f1)
    name=$(echo $service_info | cut -d: -f2)
    
    log_info "Starting $name..."
    
    if [ -f "$script" ]; then
        ./$script start
        if [ $? -eq 0 ]; then
            log_success "✅ $name started successfully"
        else
            log_error "❌ $name failed to start"
        fi
    else
        log_error "Script not found: $script"
    fi
    
    sleep 3
done

log_success "🚀 All services started - daemon running"

# Keep daemon running and monitor services
while true; do
    sleep 60
    
    # Basic health check - just verify we're still running
    log_info "📊 Daemon heartbeat - services monitoring..."
    
    # Check if any critical processes died and exit if so
    # This will trigger systemd to restart the entire service
    failed_services=0
    for service_info in "${services[@]}"; do
        service=$(echo $service_info | cut -d: -f1)
        service_path="$PROJECT_ROOT/services/$service"
        
        if [ -d "$service_path" ]; then
            cd "$service_path"
            if [ -f "start_service.sh" ]; then
                # Check service status
                ./start_service.sh status >/dev/null 2>&1
                if [ $? -ne 0 ]; then
                    failed_services=$((failed_services + 1))
                fi
            fi
            cd "$PROJECT_ROOT"
        fi
    done
    
    if [ $failed_services -gt 2 ]; then
        log_error "Too many services failed ($failed_services) - triggering restart"
        cleanup
        exit 1
    fi
done