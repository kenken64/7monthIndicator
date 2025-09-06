#!/bin/bash
# Ubuntu startup script for RL-Enhanced Binance Futures Trading Bot
# Starts the RL bot in background with logging and monitoring

# Script configuration
SCRIPT_NAME="rl-enhanced-trading-bot"
BOT_SCRIPT="rl_bot_ready.py"
LOG_DIR="logs"
PID_FILE="$LOG_DIR/rl_bot.pid"
MAIN_LOG="$LOG_DIR/rl_bot_main.log"
ERROR_LOG="$LOG_DIR/rl_bot_error.log"
VENV_PATH="venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_rl() {
    echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] RL: $1${NC}"
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
            
            print_info "RL Bot log files initialized:"
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
            print_info "Created RL bot main log file: $MAIN_LOG"
        fi
        
        if [ ! -f "$ERROR_LOG" ]; then
            touch "$ERROR_LOG"
            chmod 644 "$ERROR_LOG"
            print_info "Created RL bot error log file: $ERROR_LOG"
        fi
    fi
    
    # Verify directory is writable
    if [ ! -w "$LOG_DIR" ]; then
        print_error "Log directory is not writable: $LOG_DIR"
        print_error "Fix permissions: sudo chmod 755 $LOG_DIR"
        exit 1
    fi
}

# Check if RL bot is already running
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

# Check system requirements specific to RL bot
check_requirements() {
    print_info "Checking RL bot requirements..."
    
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
    
    # Check if RL bot script exists
    if [ ! -f "$BOT_SCRIPT" ]; then
        print_error "RL bot script $BOT_SCRIPT not found"
        print_info "Make sure rl_bot_ready.py exists in the current directory"
        exit 1
    fi
    
    # Check RL dependencies
    check_rl_dependencies
    
    # Check .env file
    check_env_file
    
    print_status "RL bot requirements check passed"
}

# Check RL-specific dependencies
check_rl_dependencies() {
    print_rl "Checking RL system dependencies..."
    
    # Check if RL patch file exists
    if [ ! -f "rl_patch.py" ]; then
        print_error "RL patch file (rl_patch.py) not found"
        print_info "This file is required for RL enhancement"
        exit 1
    fi
    
    # Check if RL model exists
    if [ ! -f "rl_trading_model.pkl" ]; then
        print_warning "RL model file (rl_trading_model.pkl) not found"
        print_info "RL bot will work but without trained model benefits"
    else
        print_status "RL model file found"
    fi
    
    # Check if lightweight RL exists
    if [ ! -f "lightweight_rl.py" ]; then
        print_error "Lightweight RL file (lightweight_rl.py) not found"
        exit 1
    fi
    
    print_rl "RL dependencies check passed"
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

# RL Bot Configuration (Safer defaults)
SYMBOL=SUIUSDC
LEVERAGE=50
POSITION_PERCENTAGE=2.0  # Much safer than 51%
RISK_PERCENTAGE=1.5
USE_TESTNET=false
EOF
    print_status "Basic .env template created with RL-safe defaults"
}

# Validate Binance API keys for RL bot
validate_api_keys() {
    print_info "Validating Binance API configuration for RL bot..."
    
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

# Test Binance API connection for RL bot
test_api_connection() {
    print_info "Testing Binance API connection for RL bot..."
    
    # Activate virtual environment for API test
    source "$VENV_PATH/bin/activate" 2>/dev/null || {
        print_warning "Cannot activate virtual environment for API test"
        return 0
    }
    
    # Create a simple Python script to test RL bot API connection
    cat > test_rl_api.py << 'EOF'
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
    print(f"SUCCESS: Connected to Binance {'Testnet' if testnet else 'Live'} for RL bot")
    print(f"Account Status: {account['accountType']}")
    
    # Test futures account specifically for RL bot
    if not testnet:
        try:
            futures_account = client.futures_account()
            balance = float(futures_account['availableBalance'])
            print(f"Futures Account: Available Balance = {balance:.2f} USDT")
            
            # Check if balance is sufficient for RL bot (much lower requirements)
            if balance < 10:
                print("WARNING: Low balance - RL bot needs at least $10 USDT for safe operation")
            else:
                print(f"✅ Balance sufficient for RL bot (2% position sizing)")
            
            # Check SUIUSDC position
            positions = client.futures_position_information(symbol='SUIUSDC')
            for pos in positions:
                if pos['symbol'] == 'SUIUSDC':
                    amt = float(pos['positionAmt'])
                    if abs(amt) > 0:
                        print(f"Current SUIUSDC position: {amt}")
                    break
            
        except Exception as e:
            print(f"WARNING: Futures access issue: {str(e)}")
            print("Make sure 'Enable Futures' is enabled in your API key settings")
    
    # Test RL components
    try:
        from rl_patch import create_rl_enhanced_bot
        print("✅ RL enhancement system available")
    except ImportError as e:
        print(f"WARNING: RL system not available: {e}")
    
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
    if python test_rl_api.py 2>/dev/null; then
        print_status "✅ Binance API connection test passed for RL bot"
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
    rm -f test_rl_api.py
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
            
            print_status "Virtual environment ready for RL bot"
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

# Install dependencies for RL bot
install_dependencies() {
    print_info "Installing/updating RL bot dependencies..."
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    if [ -f "requirements.txt" ]; then
        print_info "Installing packages from requirements.txt..."
        
        # Install requirements with progress
        if pip install -r requirements.txt; then
            print_status "All RL bot dependencies installed successfully"
            
            # Show installed packages relevant to RL bot
            print_info "Installed packages for RL bot:"
            pip list | grep -E "(binance|pandas|numpy|scikit|python-dotenv)" || true
        else
            print_error "Failed to install some dependencies"
            print_warning "RL bot may not function properly"
            exit 1
        fi
    else
        print_warning "requirements.txt not found"
        print_info "Creating basic requirements.txt file for RL bot..."
        cat > requirements.txt << EOF
python-binance==1.0.19
pandas==2.1.4
numpy==1.24.3
python-dotenv==1.0.0
scikit-learn==1.3.0
matplotlib==3.8.2
seaborn==0.13.0
EOF
        print_status "Basic RL bot requirements.txt created"
        install_dependencies  # Retry installation
    fi
}

# Start the RL trading bot
start_bot() {
    print_rl "Starting $SCRIPT_NAME..."
    
    if is_bot_running; then
        print_warning "RL bot is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    # Kill any other trading bots first
    print_info "Checking for conflicting trading bot processes..."
    if pgrep -f "trading_bot.py" > /dev/null; then
        print_warning "Found running trading_bot.py - stopping it first"
        pkill -f "trading_bot.py"
        sleep 2
    fi
    
    # Activate virtual environment and start RL bot
    source "$VENV_PATH/bin/activate"
    
    print_rl "🚀 Launching RL-Enhanced Trading Bot..."
    print_rl "🛡️ Safety Features: 2% position size, RL signal filtering, enhanced risk management"
    
    # Start RL bot in background with nohup
    nohup python3 "$BOT_SCRIPT" > "$MAIN_LOG" 2> "$ERROR_LOG" &
    BOT_PID=$!
    
    # Save PID to file
    echo $BOT_PID > "$PID_FILE"
    
    # Wait a moment to check if RL bot started successfully
    sleep 5
    
    if ps -p $BOT_PID > /dev/null 2>&1; then
        print_status "🎉 RL bot started successfully (PID: $BOT_PID)"
        print_rl "🤖 RL Enhancement: ACTIVE"
        print_rl "🛡️ Position Size: 2.0% (vs 51% original)"
        print_rl "📊 Risk Management: Enhanced with ML pattern recognition"
        print_info "Main log: $MAIN_LOG"
        print_info "Error log: $ERROR_LOG"
        print_info "Use './start_rl_bot.sh status' to check RL bot status"
        print_info "Use './start_rl_bot.sh stop' to stop the RL bot"
        print_info "Use './start_rl_bot.sh logs' to view live logs"
        
        # Show initial status
        sleep 2
        print_info "Initial RL bot status check..."
        tail -n 5 "$MAIN_LOG" 2>/dev/null || echo "Waiting for log output..."
        
        return 0
    else
        print_error "RL bot failed to start. Check error log: $ERROR_LOG"
        if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
            print_error "Recent errors:"
            tail -n 10 "$ERROR_LOG"
        fi
        rm -f "$PID_FILE"
        return 1
    fi
}

# Stop the RL trading bot
stop_bot() {
    print_rl "Stopping $SCRIPT_NAME..."
    
    if ! is_bot_running; then
        print_warning "RL bot is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    kill $PID
    
    # Wait for process to terminate
    sleep 5
    
    if ps -p $PID > /dev/null 2>&1; then
        print_warning "RL bot didn't stop gracefully, force killing..."
        kill -9 $PID
    fi
    
    rm -f "$PID_FILE"
    print_status "🛑 RL bot stopped successfully"
}

# Show RL bot status with enhanced information
show_status() {
    print_rl "Checking $SCRIPT_NAME status..."
    
    if is_bot_running; then
        PID=$(cat "$PID_FILE")
        UPTIME=$(ps -o etime= -p $PID | tr -d ' ')
        MEMORY=$(ps -o rss= -p $PID | tr -d ' ')
        CPU=$(ps -o %cpu= -p $PID | tr -d ' ')
        print_status "🟢 RL bot is running (PID: $PID)"
        print_info "⏱️  Uptime: $UPTIME"
        print_info "💾 Memory: ${MEMORY}KB"
        print_info "🏃 CPU: ${CPU}%"
        
        # Use built-in status command if available
        print_rl "Getting RL bot internal status..."
        source "$VENV_PATH/bin/activate" 2>/dev/null
        python3 "$BOT_SCRIPT" status 2>/dev/null || {
            print_warning "RL bot status command not available, showing logs instead"
            
            # Show recent log entries
            if [ -f "$MAIN_LOG" ]; then
                print_info "Recent RL bot log entries:"
                tail -n 10 "$MAIN_LOG"
            fi
        }
    else
        print_warning "🔴 RL bot is not running"
        
        # Show recent error log if exists
        if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
            print_error "Recent RL bot errors:"
            tail -n 5 "$ERROR_LOG"
        fi
        
        print_info "To start RL bot: ./start_rl_bot.sh start"
    fi
}

# View live RL bot logs
view_logs() {
    if [ -f "$MAIN_LOG" ]; then
        print_rl "Showing live RL bot logs (Ctrl+C to exit):"
        echo -e "${PURPLE}===============================================${NC}"
        tail -f "$MAIN_LOG"
    else
        print_error "RL bot log file not found: $MAIN_LOG"
        print_info "Start the RL bot first: ./start_rl_bot.sh start"
    fi
}

# Restart the RL bot
restart_bot() {
    print_rl "Restarting $SCRIPT_NAME..."
    stop_bot
    sleep 3
    start_bot
}

# Show RL bot help
show_help() {
    echo -e "${PURPLE}🤖 RL-Enhanced Trading Bot Management Script${NC}"
    echo ""
    echo -e "${GREEN}🚀 Key Features:${NC}"
    echo -e "${PURPLE}  • Reinforcement Learning signal filtering${NC}"
    echo -e "${PURPLE}  • 2% position size (vs 51% original)${NC}"
    echo -e "${PURPLE}  • Enhanced risk management${NC}"
    echo -e "${PURPLE}  • Automatic position reconciliation${NC}"
    echo -e "${PURPLE}  • ML pattern recognition${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./start_rl_bot.sh [command]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  start     - Start the RL bot in background (safer 2% positions)"
    echo "  stop      - Stop the RL bot"
    echo "  restart   - Restart the RL bot"
    echo "  status    - Show RL bot status and live positions"
    echo "  logs      - View live RL bot logs (Ctrl+C to exit)"
    echo "  setup     - Initial setup: create venv and install RL dependencies"
    echo "  test-api  - Test Binance API connection for RL bot"
    echo "  install   - Install/update RL bot dependencies only"
    echo "  help      - Show this help message"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./start_rl_bot.sh setup     # First-time RL bot setup"
    echo "  ./start_rl_bot.sh test-api  # Test your API keys with RL bot"
    echo "  ./start_rl_bot.sh start     # Start RL bot (much safer than original)"
    echo "  ./start_rl_bot.sh status    # Check RL bot status and positions"
    echo "  ./start_rl_bot.sh logs      # View live RL bot activity"
    echo ""
    echo -e "${GREEN}First Time Setup:${NC}"
    echo "  1. ./start_rl_bot.sh setup"
    echo "  2. Edit .env with your Binance API keys (safer defaults included)"
    echo "  3. ./start_rl_bot.sh test-api (verify RL bot configuration)"
    echo "  4. ./start_rl_bot.sh start"
    echo ""
    echo -e "${PURPLE}🛡️ RL Bot Safety Features:${NC}"
    echo -e "${PURPLE}  • 25x smaller position sizes (2% vs 51%)${NC}"
    echo -e "${PURPLE}  • ML-based signal filtering${NC}"
    echo -e "${PURPLE}  • Automatic risk management${NC}"
    echo -e "${PURPLE}  • Position reconciliation with Binance${NC}"
    echo -e "${PURPLE}  • Historical failure pattern avoidance${NC}"
}

# Main script logic
main() {
    create_log_directory
    
    case "${1:-start}" in
        "start")
            check_requirements
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
            install_dependencies
            print_status "🎉 RL bot setup complete! You can now:"
            print_info "1. Edit .env with your Binance API keys (safer 2% defaults included)"
            print_info "2. Run './start_rl_bot.sh test-api' to verify your RL bot setup"
            print_info "3. Run './start_rl_bot.sh start' to begin safer RL-enhanced trading"
            ;;
        "test-api"|"test")
            check_requirements
            check_env_file
            print_status "🎉 RL bot API key validation complete!"
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