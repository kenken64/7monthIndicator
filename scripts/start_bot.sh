#!/bin/bash
# Ubuntu startup script for Binance Futures Trading Bot
# Starts the bot in background with logging and monitoring

# Script configuration
SCRIPT_NAME="7indicator-trading-bot"
BOT_SCRIPT="trading_bot.py"
LOG_DIR="logs"
PID_FILE="$LOG_DIR/bot.pid"
MAIN_LOG="$LOG_DIR/bot_main.log"
ERROR_LOG="$LOG_DIR/bot_error.log"
VENV_PATH="venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Create logs directory if it doesn't exist
create_log_directory() {
    if [ ! -d "$LOG_DIR" ]; then
        print_info "Logs directory not found. Creating: $LOG_DIR"
        if mkdir -p "$LOG_DIR"; then
            print_status "Successfully created log directory: $LOG_DIR"
            
            # Set proper permissions
            chmod 755 "$LOG_DIR"
            
            # Create initial log files if they don't exist
            touch "$MAIN_LOG" "$ERROR_LOG"
            chmod 644 "$MAIN_LOG" "$ERROR_LOG"
            
            print_info "Log files initialized:"
            print_info "  Main log: $MAIN_LOG"
            print_info "  Error log: $ERROR_LOG"
        else
            print_error "Failed to create log directory: $LOG_DIR"
            print_error "Check permissions or create it manually: sudo mkdir -p $LOG_DIR"
            exit 1
        fi
    else
        print_info "Log directory exists: $LOG_DIR"
        
        # Ensure log files exist
        if [ ! -f "$MAIN_LOG" ]; then
            touch "$MAIN_LOG"
            chmod 644 "$MAIN_LOG"
            print_info "Created main log file: $MAIN_LOG"
        fi
        
        if [ ! -f "$ERROR_LOG" ]; then
            touch "$ERROR_LOG"
            chmod 644 "$ERROR_LOG"
            print_info "Created error log file: $ERROR_LOG"
        fi
    fi
    
    # Verify directory is writable
    if [ ! -w "$LOG_DIR" ]; then
        print_error "Log directory is not writable: $LOG_DIR"
        print_error "Fix permissions: sudo chmod 755 $LOG_DIR"
        exit 1
    fi
}

# Check if bot is already running
is_bot_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0  # Bot is running
        else
            rm -f "$PID_FILE"  # Remove stale PID file
            return 1  # Bot is not running
        fi
    else
        return 1  # Bot is not running
    fi
}

# Check system requirements
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        print_info "Install Python3 with: sudo apt update && sudo apt install python3 python3-pip python3-venv"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        print_error "pip3 is not available"
        print_info "Install pip with: sudo apt install python3-pip"
        exit 1
    fi
    
    print_status "Python3 and pip are available"
    
    # Check virtual environment
    create_virtual_environment
    
    # Check if bot script exists
    if [ ! -f "$BOT_SCRIPT" ]; then
        print_error "Bot script $BOT_SCRIPT not found"
        exit 1
    fi
    
    # Check .env file
    check_env_file
    
    print_status "System requirements check passed"
}

# Check and validate .env file and API keys
check_env_file() {
    print_info "Checking environment configuration..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        
        # Check if .env.example exists
        if [ -f ".env.example" ]; then
            print_info "Found .env.example file"
            read -p "$(echo -e "${YELLOW}Would you like to copy .env.example to .env now? (y/n): ${NC}")" -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp .env.example .env
                print_status ".env file created from template"
                print_warning "IMPORTANT: You must now edit .env with your Binance API keys"
                print_info "Edit command: nano .env"
                print_info "Add your actual API keys and save the file"
                exit 1
            else
                print_error "Cannot proceed without .env file"
                print_info "Create it manually: cp .env.example .env"
                exit 1
            fi
        else
            print_error "Neither .env nor .env.example found"
            print_info "Creating basic .env template..."
            create_env_template
            print_warning "Please edit .env with your Binance API keys"
            exit 1
        fi
    fi
    
    # Load and validate environment variables
    source .env
    
    print_status ".env file found"
    
    # Check for API keys
    validate_api_keys
}

# Create basic .env template
create_env_template() {
    cat > .env << EOF
# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Trading Configuration (Optional - uses config.py defaults if not set)
# SYMBOL=SUIUSDC
# LEVERAGE=50
# POSITION_PERCENTAGE=51.0
# RISK_PERCENTAGE=2.0
# USE_TESTNET=true
EOF
    print_status "Basic .env template created"
}

# Validate Binance API keys
validate_api_keys() {
    print_info "Validating Binance API configuration..."
    
    # Check if API keys are set and not default values
    if [ -z "$BINANCE_API_KEY" ] || [ "$BINANCE_API_KEY" = "your_binance_api_key_here" ]; then
        print_error "BINANCE_API_KEY is not configured"
        print_info "Please edit .env file and set your actual Binance API key"
        print_info "Edit with: nano .env"
        exit 1
    fi
    
    if [ -z "$BINANCE_SECRET_KEY" ] || [ "$BINANCE_SECRET_KEY" = "your_binance_secret_key_here" ]; then
        print_error "BINANCE_SECRET_KEY is not configured"
        print_info "Please edit .env file and set your actual Binance secret key"
        print_info "Edit with: nano .env"
        exit 1
    fi
    
    # Basic format validation
    if [ ${#BINANCE_API_KEY} -lt 20 ]; then
        print_error "BINANCE_API_KEY appears too short (should be ~64 characters)"
        print_warning "Please verify your API key is correct"
        exit 1
    fi
    
    if [ ${#BINANCE_SECRET_KEY} -lt 20 ]; then
        print_error "BINANCE_SECRET_KEY appears too short (should be ~64 characters)"
        print_warning "Please verify your secret key is correct"
        exit 1
    fi
    
    print_status "API keys appear to be configured correctly"
    
    # Test API connection if possible
    test_api_connection
}

# Test Binance API connection
test_api_connection() {
    print_info "Testing Binance API connection..."
    
    # Activate virtual environment for API test
    source "$VENV_PATH/bin/activate" 2>/dev/null || {
        print_warning "Cannot activate virtual environment for API test"
        return 0
    }
    
    # Create a simple Python script to test API connection
    cat > test_api.py << 'EOF'
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from binance.client import Client
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    # Use testnet if specified
    testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
    
    client = Client(api_key, secret_key, testnet=testnet)
    
    # Test connection with account info
    account = client.get_account()
    print(f"SUCCESS: Connected to Binance {'Testnet' if testnet else 'Live'}")
    print(f"Account Status: {account['accountType']}")
    
    # Test futures account if not testnet
    if not testnet:
        try:
            futures_account = client.futures_account()
            print(f"Futures Account: Available Balance = {futures_account['availableBalance']} USDT")
        except Exception as e:
            print(f"WARNING: Futures access issue: {str(e)}")
            print("Make sure 'Enable Futures' is enabled in your API key settings")
    
except ImportError:
    print("ERROR: python-binance not installed")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {str(e)}")
    if "Invalid API-key" in str(e):
        print("Your API key appears to be invalid")
    elif "Signature" in str(e):
        print("Your secret key appears to be invalid")
    elif "IP" in str(e):
        print("Your IP address may not be whitelisted")
    sys.exit(1)
EOF
    
    # Run the test
    if python test_api.py 2>/dev/null; then
        print_status "✅ Binance API connection test passed"
    else
        print_error "❌ Binance API connection test failed"
        print_warning "Your API keys may be incorrect or have insufficient permissions"
        print_info "Please verify:"
        print_info "  1. API keys are correct in .env file"
        print_info "  2. 'Enable Futures' is checked in Binance API settings"
        print_info "  3. Your IP address is whitelisted (if IP restrictions are enabled)"
        
        read -p "$(echo -e "${YELLOW}Continue anyway? (y/n): ${NC}")" -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Clean up test file
    rm -f test_api.py
}

# Create virtual environment if needed
create_virtual_environment() {
    if [ ! -d "$VENV_PATH" ]; then
        print_info "Virtual environment not found. Creating new one..."
        
        if python3 -m venv "$VENV_PATH"; then
            print_status "Virtual environment created successfully: $VENV_PATH"
            
            # Activate and upgrade pip
            source "$VENV_PATH/bin/activate"
            print_info "Upgrading pip in virtual environment..."
            python -m pip install --upgrade pip
            
            print_status "Virtual environment ready"
        else
            print_error "Failed to create virtual environment"
            print_info "Make sure python3-venv is installed: sudo apt install python3-venv"
            exit 1
        fi
    else
        print_info "Virtual environment exists: $VENV_PATH"
        
        # Verify virtual environment is working
        if [ ! -f "$VENV_PATH/bin/activate" ]; then
            print_error "Virtual environment appears corrupted"
            print_warning "Removing corrupted venv and creating new one..."
            rm -rf "$VENV_PATH"
            create_virtual_environment
            return
        fi
        
        # Test activation
        if source "$VENV_PATH/bin/activate" 2>/dev/null; then
            print_status "Virtual environment is working correctly"
        else
            print_error "Cannot activate virtual environment"
            print_warning "Recreating virtual environment..."
            rm -rf "$VENV_PATH"
            create_virtual_environment
            return
        fi
    fi
}

# Install dependencies
install_dependencies() {
    print_info "Installing/updating dependencies..."
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    if [ -f "requirements.txt" ]; then
        print_info "Installing packages from requirements.txt..."
        
        # Install requirements with progress
        if pip install -r requirements.txt; then
            print_status "All dependencies installed successfully"
            
            # Show installed packages
            print_info "Installed packages:"
            pip list | grep -E "(binance|pandas|numpy|ta-lib|python-dotenv|matplotlib|seaborn)" || true
        else
            print_error "Failed to install some dependencies"
            print_warning "You may need to install TA-Lib system dependencies first:"
            print_info "  Ubuntu/Debian: sudo apt-get install build-essential"
            print_info "  Then install TA-Lib manually if needed"
            exit 1
        fi
    else
        print_warning "requirements.txt not found"
        print_info "Creating basic requirements.txt file..."
        cat > requirements.txt << EOF
python-binance==1.0.19
pandas==2.1.4
numpy==1.24.3
ta-lib==0.4.28
python-dotenv==1.0.0
matplotlib==3.8.2
seaborn==0.13.0
EOF
        print_status "Basic requirements.txt created"
        install_dependencies  # Retry installation
    fi
}

# Install TA-Lib system dependencies if needed
install_talib_dependencies() {
    print_info "Checking TA-Lib system dependencies..."
    
    # Check if we're on Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        print_info "Detected apt package manager (Ubuntu/Debian)"
        
        # Check if build-essential is installed
        if ! dpkg -l | grep -q build-essential; then
            print_warning "build-essential not found, attempting to install..."
            if sudo apt-get update && sudo apt-get install -y build-essential; then
                print_status "build-essential installed successfully"
            else
                print_error "Failed to install build-essential"
                print_info "Please run manually: sudo apt-get install build-essential"
                return 1
            fi
        else
            print_status "build-essential is already installed"
        fi
        
        # Install other dependencies for TA-Lib
        print_info "Installing additional dependencies for TA-Lib..."
        sudo apt-get install -y wget curl
        
    # Check if we're on CentOS/RHEL/Fedora
    elif command -v yum &> /dev/null || command -v dnf &> /dev/null; then
        print_info "Detected Red Hat based system"
        if command -v dnf &> /dev/null; then
            sudo dnf groupinstall -y "Development Tools"
            sudo dnf install -y wget curl
        else
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y wget curl
        fi
    else
        print_warning "Unknown package manager, please install build tools manually"
    fi
}

# Start the trading bot
start_bot() {
    print_info "Starting $SCRIPT_NAME..."
    
    if is_bot_running; then
        print_warning "Bot is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    # Activate virtual environment and start bot
    source "$VENV_PATH/bin/activate"
    
    # Start bot in background with nohup
    nohup python3 "$BOT_SCRIPT" > "$MAIN_LOG" 2> "$ERROR_LOG" &
    BOT_PID=$!
    
    # Save PID to file
    echo $BOT_PID > "$PID_FILE"
    
    # Wait a moment to check if bot started successfully
    sleep 3
    
    if ps -p $BOT_PID > /dev/null 2>&1; then
        print_status "Bot started successfully (PID: $BOT_PID)"
        print_info "Main log: $MAIN_LOG"
        print_info "Error log: $ERROR_LOG"
        print_info "Use './start_bot.sh status' to check status"
        print_info "Use './start_bot.sh stop' to stop the bot"
        return 0
    else
        print_error "Bot failed to start. Check error log: $ERROR_LOG"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Stop the trading bot
stop_bot() {
    print_info "Stopping $SCRIPT_NAME..."
    
    if ! is_bot_running; then
        print_warning "Bot is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    kill $PID
    
    # Wait for process to terminate
    sleep 5
    
    if ps -p $PID > /dev/null 2>&1; then
        print_warning "Bot didn't stop gracefully, force killing..."
        kill -9 $PID
    fi
    
    rm -f "$PID_FILE"
    print_status "Bot stopped successfully"
}

# Show bot status
show_status() {
    print_info "Checking $SCRIPT_NAME status..."
    
    if is_bot_running; then
        PID=$(cat "$PID_FILE")
        UPTIME=$(ps -o etime= -p $PID | tr -d ' ')
        MEMORY=$(ps -o rss= -p $PID | tr -d ' ')
        print_status "Bot is running (PID: $PID, Uptime: $UPTIME, Memory: ${MEMORY}KB)"
        
        # Show recent log entries
        if [ -f "$MAIN_LOG" ]; then
            print_info "Recent log entries:"
            tail -n 10 "$MAIN_LOG"
        fi
    else
        print_warning "Bot is not running"
        
        # Show recent error log if exists
        if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
            print_error "Recent errors:"
            tail -n 5 "$ERROR_LOG"
        fi
    fi
}

# View live logs
view_logs() {
    if [ -f "$MAIN_LOG" ]; then
        print_info "Showing live logs (Ctrl+C to exit):"
        tail -f "$MAIN_LOG"
    else
        print_error "Log file not found: $MAIN_LOG"
    fi
}

# Restart the bot
restart_bot() {
    print_info "Restarting $SCRIPT_NAME..."
    stop_bot
    sleep 2
    start_bot
}

# Show help
show_help() {
    echo -e "${BLUE}$SCRIPT_NAME Management Script${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./start_bot.sh [command]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  start     - Start the trading bot in background (auto-creates venv)"
    echo "  stop      - Stop the trading bot"
    echo "  restart   - Restart the trading bot"
    echo "  status    - Show bot status and recent logs"
    echo "  logs      - View live logs (Ctrl+C to exit)"
    echo "  setup     - Initial setup: create venv and install dependencies"
    echo "  test-api  - Test Binance API connection and validate keys"
    echo "  install   - Install/update dependencies only"
    echo "  help      - Show this help message"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./start_bot.sh setup     # First-time setup"
    echo "  ./start_bot.sh test-api  # Test your API keys"
    echo "  ./start_bot.sh start     # Start the bot (creates venv if needed)"
    echo "  ./start_bot.sh status    # Check if bot is running"
    echo "  ./start_bot.sh logs      # View live logs"
    echo ""
    echo -e "${GREEN}First Time Setup:${NC}"
    echo "  1. ./start_bot.sh setup"
    echo "  2. cp .env.example .env (or script will prompt you)"
    echo "  3. Edit .env with your Binance API keys"
    echo "  4. ./start_bot.sh test-api (verify configuration)"
    echo "  5. ./start_bot.sh start"
}

# Main script logic
main() {
    create_log_directory
    
    case "${1:-start}" in
        "start")
            check_requirements
            install_talib_dependencies
            install_dependencies
            start_bot
            ;;
        "stop")
            stop_bot
            ;;
        "restart")
            restart_bot
            ;;
        "status")
            show_status
            ;;
        "logs")
            view_logs
            ;;
        "install"|"setup")
            check_requirements
            install_talib_dependencies
            install_dependencies
            print_status "Setup complete! You can now:"
            print_info "1. Copy .env.example to .env and add your API keys"
            print_info "2. Run './start_bot.sh test-api' to verify your API keys"
            print_info "3. Run './start_bot.sh start' to begin trading"
            ;;
        "test-api"|"test")
            check_requirements
            check_env_file
            print_status "API key validation complete!"
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

# Run main function with all arguments
main "$@"