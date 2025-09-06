#!/bin/bash
# Run trading analysis with virtual environment

set -e  # Exit on any error

# Setup virtual environment if it doesn't exist
if [ ! -d "analyze_venv" ]; then
    echo "🔧 Setting up virtual environment for trading analysis..."
    echo "Creating virtual environment..."
    python3 -m venv analyze_venv
    
    # Activate and setup
    source analyze_venv/bin/activate
    echo "Upgrading pip..."
    pip install --upgrade pip
    echo "Installing required packages..."
    pip install -r requirements.txt
    echo "✅ Virtual environment setup complete!"
else
    echo "🔧 Activating virtual environment..."
    source analyze_venv/bin/activate
fi

# Check if database exists
if [ ! -f "trading_bot.db" ]; then
    echo "❌ No trading database found (trading_bot.db)"
    echo "Make sure the trading bot has been running to collect data."
    exit 1
fi

# Default parameters
SYMBOL="SUIUSDC"
DAYS=7
EXPORT=""
PLOT=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --export)
            EXPORT="--export"
            shift
            ;;
        --plot)
            PLOT="--plot"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --symbol SYMBOL    Trading symbol to analyze (default: SUIUSDC)"
            echo "  --days DAYS        Number of days to analyze (default: 7)"
            echo "  --export          Export data to CSV files"
            echo "  --plot            Generate performance plots"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --symbol BTCUSDC --days 30"
            echo "  $0 --export --plot"
            echo "  $0 --symbol ETHUSDC --days 14 --export --plot"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run analysis
echo "📊 Running trading analysis..."
echo "Symbol: $SYMBOL | Days: $DAYS | Export: $([ -n "$EXPORT" ] && echo "Yes" || echo "No") | Plot: $([ -n "$PLOT" ] && echo "Yes" || echo "No")"
echo ""

python analyze_trades.py --symbol "$SYMBOL" --days "$DAYS" $EXPORT $PLOT

echo ""
echo "✅ Analysis complete!"

# Deactivate virtual environment
deactivate