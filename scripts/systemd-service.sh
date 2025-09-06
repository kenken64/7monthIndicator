#!/bin/bash
"""
Install trading bot as a systemd service for automatic startup
Run this script to create and install the systemd service
"""

SERVICE_NAME="trading-bot"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
CURRENT_DIR=$(pwd)
USER=$(whoami)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Create systemd service file
create_service() {
    print_status "Creating systemd service file..."
    
    cat > $SERVICE_FILE << EOF
[Unit]
Description=7-Indicator Binance Futures Trading Bot
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/trading_bot.py
ExecReload=/bin/kill -HUP \$MAINPID
StandardOutput=append:$CURRENT_DIR/logs/systemd.log
StandardError=append:$CURRENT_DIR/logs/systemd-error.log

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$CURRENT_DIR

[Install]
WantedBy=multi-user.target
EOF

    print_status "Service file created: $SERVICE_FILE"
}

# Install and enable service
install_service() {
    print_status "Installing systemd service..."
    
    # Create logs directory with proper permissions
    if [ ! -d "$CURRENT_DIR/logs" ]; then
        print_status "Creating logs directory: $CURRENT_DIR/logs"
        mkdir -p "$CURRENT_DIR/logs"
        if [ $? -eq 0 ]; then
            print_status "Logs directory created successfully"
        else
            print_error "Failed to create logs directory"
            exit 1
        fi
    fi
    
    # Set proper ownership and permissions
    chown -R $USER:$USER "$CURRENT_DIR/logs"
    chmod 755 "$CURRENT_DIR/logs"
    
    # Create initial log files
    touch "$CURRENT_DIR/logs/systemd.log" "$CURRENT_DIR/logs/systemd-error.log"
    chown $USER:$USER "$CURRENT_DIR/logs/systemd.log" "$CURRENT_DIR/logs/systemd-error.log"
    chmod 644 "$CURRENT_DIR/logs/systemd.log" "$CURRENT_DIR/logs/systemd-error.log"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable $SERVICE_NAME
    
    print_status "Service installed and enabled"
    print_status "Service will start automatically on boot"
}

# Show service management commands
show_commands() {
    echo ""
    print_status "Service Management Commands:"
    echo "  sudo systemctl start $SERVICE_NAME     - Start the service"
    echo "  sudo systemctl stop $SERVICE_NAME      - Stop the service"  
    echo "  sudo systemctl restart $SERVICE_NAME   - Restart the service"
    echo "  sudo systemctl status $SERVICE_NAME    - Check service status"
    echo "  sudo systemctl enable $SERVICE_NAME    - Enable auto-start on boot"
    echo "  sudo systemctl disable $SERVICE_NAME   - Disable auto-start"
    echo "  sudo journalctl -u $SERVICE_NAME -f    - View live service logs"
    echo ""
    print_status "Log Files:"
    echo "  $CURRENT_DIR/logs/systemd.log         - Service output"
    echo "  $CURRENT_DIR/logs/systemd-error.log   - Service errors"
    echo "  $CURRENT_DIR/trading_bot.log          - Bot application logs"
}

# Main installation
main() {
    check_root
    
    print_status "Installing $SERVICE_NAME systemd service..."
    print_status "Bot directory: $CURRENT_DIR"
    print_status "Running as user: $USER"
    
    # Check if virtual environment exists
    if [ ! -d "$CURRENT_DIR/venv" ]; then
        print_error "Virtual environment not found. Please run:"
        print_error "  python3 -m venv venv"
        print_error "  source venv/bin/activate"
        print_error "  pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if .env exists
    if [ ! -f "$CURRENT_DIR/.env" ]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    create_service
    install_service
    show_commands
    
    print_status "Installation complete!"
    print_warning "To start the service now, run: sudo systemctl start $SERVICE_NAME"
}

# Run with command line argument support
case "${1:-install}" in
    "install")
        main
        ;;
    "uninstall")
        check_root
        print_status "Uninstalling service..."
        systemctl stop $SERVICE_NAME 2>/dev/null
        systemctl disable $SERVICE_NAME 2>/dev/null
        rm -f $SERVICE_FILE
        systemctl daemon-reload
        print_status "Service uninstalled"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: sudo ./systemd-service.sh [install|uninstall|help]"
        echo ""
        echo "Commands:"
        echo "  install   - Install the trading bot as a systemd service"
        echo "  uninstall - Remove the systemd service"
        echo "  help      - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run './systemd-service.sh help' for usage"
        exit 1
        ;;
esac