#!/bin/bash
"""
Docker startup script for Binance Futures Trading Bot
Builds and runs the bot in a Docker container
"""

CONTAINER_NAME="trading-bot"
IMAGE_NAME="7indicator-trading-bot"
NETWORK_NAME="trading-network"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    print_status "Docker check passed"
}

# Create Dockerfile if it doesn't exist
create_dockerfile() {
    if [ ! -f "Dockerfile" ]; then
        print_info "Creating Dockerfile..."
        
        cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib
WORKDIR /tmp
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/ta-lib*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY trading_bot.py .
COPY config.py .
COPY .env* ./

# Create logs directory
RUN mkdir -p logs

# Create non-root user for security
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /app
USER trader

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f "python.*trading_bot.py" || exit 1

# Run the bot
CMD ["python", "trading_bot.py"]
EOF
        print_status "Dockerfile created"
    fi
}

# Build Docker image
build_image() {
    print_info "Building Docker image: $IMAGE_NAME"
    
    if docker build -t $IMAGE_NAME . ; then
        print_status "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Create Docker network if it doesn't exist
create_network() {
    if ! docker network ls | grep -q $NETWORK_NAME; then
        print_info "Creating Docker network: $NETWORK_NAME"
        docker network create $NETWORK_NAME
        print_status "Docker network created"
    fi
}

# Stop and remove existing container
cleanup_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_info "Stopping and removing existing container..."
        docker stop $CONTAINER_NAME 2>/dev/null
        docker rm $CONTAINER_NAME 2>/dev/null
        print_status "Container cleanup completed"
    fi
}

# Start the trading bot container
start_container() {
    print_info "Starting trading bot container..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Run container with unlimited resources
    docker run -d \
        --name $CONTAINER_NAME \
        --network $NETWORK_NAME \
        --env-file .env \
        --restart unless-stopped \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/.env:/app/.env:ro" \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        print_status "Container started successfully"
        print_info "Container name: $CONTAINER_NAME"
        print_info "Logs directory: $(pwd)/logs"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Show container status
show_status() {
    print_info "Container status:"
    docker ps -a --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.RunningFor}}"
    
    print_info "Resource usage:"
    docker stats $CONTAINER_NAME --no-stream 2>/dev/null || print_warning "Container not running"
    
    print_info "Recent logs:"
    docker logs --tail 20 $CONTAINER_NAME 2>/dev/null || print_warning "No logs available"
}

# View live logs
view_logs() {
    print_info "Showing live container logs (Ctrl+C to exit):"
    docker logs -f $CONTAINER_NAME
}

# Stop container
stop_container() {
    print_info "Stopping trading bot container..."
    docker stop $CONTAINER_NAME
    print_status "Container stopped"
}

# Show help
show_help() {
    echo -e "${BLUE}Docker Trading Bot Management${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./docker-start.sh [command]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  build     - Build Docker image"
    echo "  start     - Start trading bot container"
    echo "  stop      - Stop trading bot container"  
    echo "  restart   - Restart trading bot container"
    echo "  status    - Show container status and logs"
    echo "  logs      - View live container logs"
    echo "  shell     - Open shell in container"
    echo "  cleanup   - Remove container and image"
    echo "  help      - Show this help"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./docker-start.sh build     # Build the image"
    echo "  ./docker-start.sh start     # Start the bot"
    echo "  ./docker-start.sh logs      # View live logs"
}

# Open shell in container
open_shell() {
    if docker ps --filter name=$CONTAINER_NAME --format '{{.Names}}' | grep -q $CONTAINER_NAME; then
        print_info "Opening shell in container..."
        docker exec -it $CONTAINER_NAME /bin/bash
    else
        print_error "Container is not running"
        exit 1
    fi
}

# Cleanup Docker resources
cleanup() {
    print_info "Cleaning up Docker resources..."
    docker stop $CONTAINER_NAME 2>/dev/null
    docker rm $CONTAINER_NAME 2>/dev/null
    docker rmi $IMAGE_NAME 2>/dev/null
    docker network rm $NETWORK_NAME 2>/dev/null
    print_status "Cleanup completed"
}

# Main script logic
main() {
    case "${1:-start}" in
        "build")
            check_docker
            create_dockerfile
            build_image
            ;;
        "start")
            check_docker
            create_dockerfile
            build_image
            create_network
            cleanup_container
            start_container
            show_status
            ;;
        "stop")
            stop_container
            ;;
        "restart")
            stop_container
            sleep 2
            start_container
            ;;
        "status")
            show_status
            ;;
        "logs")
            view_logs
            ;;
        "shell")
            open_shell
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with arguments
main "$@"