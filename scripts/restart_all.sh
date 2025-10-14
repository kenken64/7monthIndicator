#!/bin/bash
# Master restart script for modular services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_header() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}🔄 Modular Trading Bot System Restart${NC}"
    echo -e "${PURPLE}   (4 Independent Services)${NC}"
    echo -e "${PURPLE}================================================${NC}"
    echo ""
}

# Log rotation function
rotate_logs() {
    print_info "🔄 Rotating logs before restart..."
    
    # Define log directories and files to rotate
    local log_paths=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT"
        "$PROJECT_ROOT/services/trading"
        "$PROJECT_ROOT/services/chart-analysis"
        "$PROJECT_ROOT/services/mcp-server"
    )
    
    # Create rotated logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs/rotated"
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local rotated_count=0
    
    # Find and rotate log files larger than 1MB
    for log_dir in "${log_paths[@]}"; do
        if [ -d "$log_dir" ]; then
            # Find .log files larger than 1MB (1048576 bytes)
            find "$log_dir" -maxdepth 1 -name "*.log" -size +1M -type f | while read -r logfile; do
                if [ -f "$logfile" ]; then
                    local filename=$(basename "$logfile")
                    local dirname=$(dirname "$logfile")
                    local rotated_name="${filename%.log}_${timestamp}.log"
                    
                    # Move the log file to rotated directory
                    mv "$logfile" "$PROJECT_ROOT/logs/rotated/$rotated_name"
                    
                    # Create a new empty log file with same permissions
                    touch "$logfile"
                    chmod 644 "$logfile"
                    
                    print_status "📦 Rotated: $filename → rotated/$rotated_name"
                    rotated_count=$((rotated_count + 1))
                fi
            done
        fi
    done
    
    # Clean up old rotated logs (keep only last 10 rotations per log type)
    find "$PROJECT_ROOT/logs/rotated" -name "*.log" -type f -mtime +7 -delete 2>/dev/null
    
    if [ $rotated_count -eq 0 ]; then
        print_info "📝 No logs required rotation (all < 1MB)"
    else
        print_status "✅ Rotated $rotated_count log files"
    fi
}

print_header

# Set global environment
export PROJECT_ROOT="$PROJECT_ROOT"

# Rotate logs before stopping services
rotate_logs

# Service definitions: name:description
services=(
    "trading:🤖 RL Trading Bot"
    "chart-analysis:📊 Chart Analysis Bot"  
    "web-dashboard:🌐 Web Dashboard"
    "mcp-server:🔗 MCP Server"
)

# Stop all services
print_info "🛑 Stopping all modular services..."
for service_info in "${services[@]}"; do
    service=$(echo $service_info | cut -d: -f1)
    name=$(echo $service_info | cut -d: -f2)
    service_path="$PROJECT_ROOT/services/$service"
    
    print_info "Stopping $name..."
    if [ -d "$service_path" ]; then
        cd "$service_path"
        if [ -f "start_service.sh" ]; then
            ./start_service.sh stop
        fi
        cd "$PROJECT_ROOT"  # Return to project root
    fi
done

sleep 3

# Start all services  
print_info "⚡ Starting all modular services..."
for service_info in "${services[@]}"; do
    service=$(echo $service_info | cut -d: -f1)
    name=$(echo $service_info | cut -d: -f2)
    service_path="$PROJECT_ROOT/services/$service"
    
    print_info "Starting $name..."
    
    if [ -d "$service_path" ]; then
        cd "$service_path"
        if [ -f "start_service.sh" ]; then
            ./start_service.sh start
            if [ $? -eq 0 ]; then
                print_status "✅ $name started successfully"
            else
                print_error "❌ $name failed to start"
            fi
        else
            print_error "Missing start_service.sh for $service"
        fi
        cd "$PROJECT_ROOT"  # Return to project root
    else
        print_error "Service directory not found: $service_path"
    fi
    
    sleep 2
done

echo ""
print_status "🚀 Modular system restart complete!"
echo ""

# Show service status
print_info "📊 Service Status Summary:"
for service_info in "${services[@]}"; do
    service=$(echo $service_info | cut -d: -f1)
    name=$(echo $service_info | cut -d: -f2)
    service_path="$PROJECT_ROOT/services/$service"
    
    echo -e "${BLUE}$name:${NC}"
    if [ -d "$service_path" ]; then
        cd "$service_path"
        if [ -f "start_service.sh" ]; then
            ./start_service.sh status | sed 's/^/  /'
        fi
        cd "$PROJECT_ROOT"  # Return to project root
    fi
done

echo ""
print_info "📝 Monitor logs:"
echo -e "${BLUE}   Trading:     tail -f $PROJECT_ROOT/logs/trading_service.log${NC}"
echo -e "${BLUE}   Dashboard:   tail -f $PROJECT_ROOT/logs/web_dashboard_service.log${NC}"
echo -e "${BLUE}   Chart Bot:   tail -f $PROJECT_ROOT/logs/chart_analysis_service.log${NC}"
echo -e "${BLUE}   MCP Server:  tail -f $PROJECT_ROOT/logs/mcp_server_service.log${NC}"

echo ""
print_info "🔧 Individual service control:"
echo -e "${BLUE}   cd services/trading && ./start_service.sh {start|stop|status|logs}${NC}"
echo -e "${BLUE}   cd services/web-dashboard && ./start_service.sh {start|stop|status|logs}${NC}"
echo -e "${BLUE}   cd services/chart-analysis && ./start_service.sh {start|stop|status|logs}${NC}"
echo -e "${BLUE}   cd services/mcp-server && ./start_service.sh {start|stop|status|logs}${NC}"