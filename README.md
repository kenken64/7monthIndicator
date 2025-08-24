# Binance Futures Trading Bot

A sophisticated trading bot that uses multi-indicator strategy (MACD, VWAP, EMAs, RSI) to generate trading signals for Binance Futures markets with advanced position management.

## 🚨 IMPORTANT SAFETY WARNINGS

- **Start with Testnet**: Always test thoroughly on testnet first
- **Use Small Risk %**: Start with 1-2% risk per trade maximum  
- **Monitor Closely**: Never leave the bot completely unattended
- **Set Stop Losses**: Consider manual stop losses for major positions
- **Check Market Hours**: Crypto markets are 24/7, plan accordingly

## Features

- **Multi-Indicator Strategy**: MACD + VWAP + EMAs (9,21,50,200) + RSI
- **Advanced Position Management**: Cross margin with position percentage slider
- **Weighted Signal System**: Minimum signal strength of 3 required for execution
- **Real-time Monitoring**: Live PnL, liquidation prices, and position tracking
- **Enhanced Logging**: Emoji-rich console output with detailed market analysis
- **Risk Management**: Automatic position sizing and opposite position closing

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install TA-Lib (if needed - bot now uses pandas-based indicators):**

   **Windows:**
   ```bash
   # Download TA-Lib wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   pip install TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl
   ```

   **macOS:**
   ```bash
   brew install ta-lib
   pip install ta-lib
   ```

   **Linux:**
   ```bash
   sudo apt-get install build-essential
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install
   pip install ta-lib
   ```

## Configuration

1. **Create your .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your Binance API credentials to .env:**
   ```
   BINANCE_API_KEY=your_binance_api_key_here
   BINANCE_SECRET_KEY=your_binance_secret_key_here
   ```

3. **Get Binance API Keys:**
   - Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
   - Create a new API key
   - Enable "Enable Futures" permission
   - Restrict API access to your IP address (recommended)
   - **Never share your secret key!**

## Bot Configuration

Key settings in `main()` function:

```python
SYMBOL = 'SUIUSDC'         # Trading pair (as shown in screenshot)
LEVERAGE = 50              # Cross 50x leverage (as shown in screenshot)  
POSITION_PERCENT = 51.0    # Percentage of balance to use per trade (like screenshot slider)
RISK_PERCENT = 2.0         # Risk management percentage for stop loss
INTERVAL = 300             # Check interval in seconds (5 minutes)
```

### Testnet Mode

For testing, change this line in `__init__`:
```python
self.client = Client(api_key, secret_key, testnet=True)  # Enable testnet
```

### Position Management
- **Cross Margin**: Uses CROSS margin type with configurable leverage
- **Position Slider**: Mimics the percentage slider (51% of available balance)
- **Auto Position Sizing**: Calculates position size based on balance and leverage

## Signal Strength System

The bot uses an advanced weighted scoring system:

- **Minimum Signal Strength**: 3 (required to execute trades)
- **Signal Weights**:
  - **MACD Signals**: ±1 point each
    - MACD line crossovers (bullish/bearish)
    - Histogram momentum expansion
  - **VWAP Signals**: ±1 point (bulls vs bears control)
  - **EMA Signals**: Multiple weightings
    - Price vs 9 EMA: ±1 point (short-term trend)
    - 9/21 EMA crossover: ±2 points (momentum shift)
    - Price vs 50 EMA: ±1 point (trend confirmation) 
    - Price vs 200 EMA: ±1 point (market direction)
    - Golden/Death Cross: ±3 points (major trend change)
  - **RSI Signals**: ±1 point (overbought/oversold conditions)

## Running the Bot

1. **Start the bot:**
   ```bash
   python trading_bot.py
   ```

2. **Monitor logs:**
   - Console output shows real-time analysis
   - `trading_bot.log` file contains detailed history
   - Press Ctrl+C to stop gracefully

## Sample Output

```
2024-01-15 10:30:15 - INFO - 🚀 Starting Binance Futures Bot for SUIUSDC
2024-01-15 10:30:15 - INFO - ⚡ Mode: CROSS 50x | Position Size: 51%
2024-01-15 10:30:15 - INFO - 🎯 Risk Management: 2% | Strategy: MACD + VWAP + EMAs + RSI
2024-01-15 10:30:20 - INFO - 💲 SUIUSDC: $4.2150 | RSI: 65.2 (⚖️ Neutral)
2024-01-15 10:30:20 - INFO - 📈 VWAP: $4.1980 (🔵 Bulls) | Signal: 1 | Strength: 4
2024-01-15 10:30:20 - INFO - 🔍 Analysis: MACD bullish crossover, Price above VWAP, 9 EMA crossed above 21 EMA
2024-01-15 10:30:25 - INFO - 🚀 Strong signal detected! Executing trade...
2024-01-15 10:30:25 - INFO - ✅ BUY Order Executed: 2400.5 SUIUSDC
2024-01-15 10:30:25 - INFO - 📊 Entry Price: $4.2150
2024-01-15 10:30:25 - INFO - ⚠️ Liquidation Price: $4.1200
```

## Customization Options

### Indicator Parameters
Modify in `TechnicalIndicators` class:
- EMA periods (default: 9, 21, 50, 200)
- MACD settings (default: 12, 26, 9) 
- RSI period (default: 14)
- VWAP calculation methods

### Signal Logic
Modify in `generate_signals()`:
- Signal strengths and weights
- Add additional indicators as needed
- Adjust minimum signal threshold (default: 3)

### Trading Intervals
Supported intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d

### Position Management
- **Position Percentage**: Adjust the slider percentage (default: 51%)
- **Leverage**: Modify leverage multiplier (1-125x)
- **Risk Percentage**: Change risk management percentage

## Risk Management Features

- **Position Sizing**: Based on position percentage slider and available balance
- **Cross Margin**: Uses CROSS margin type with automatic leverage setting
- **Opposite Position Closing**: Automatically closes conflicting positions
- **Signal Filtering**: Only executes on strong, confirmed signals (strength ≥ 3)
- **Real-time Monitoring**: Live PnL tracking and liquidation price alerts
- **Safe Shutdown**: Closes all positions when bot is stopped

## Troubleshooting

### Common Issues:

- **API Permission Error**: Enable Futures trading in API settings
- **Insufficient Balance**: Ensure adequate USDC balance for SUIUSDC trading
- **Symbol Not Found**: Check symbol formatting (e.g., 'SUIUSDC')
- **Margin Type Error**: May be already set to CROSS (this is normal)
- **Rate Limiting**: Reduce check frequency if needed
- **Position Size Error**: Check symbol precision and minimum order size

### Error Logs:
Check `trading_bot.log` for detailed error information and debugging.

### Debugging Tips:
- Start with testnet mode first
- Use smaller position percentages initially
- Monitor liquidation prices closely
- Check Binance API status if experiencing connection issues

## Disclaimer

This trading bot is for educational purposes only. Trading cryptocurrencies involves substantial risk and may not be suitable for all investors. Past performance is not indicative of future results. Always do your own research and consider your financial situation before trading.

**Use at your own risk. The authors are not responsible for any financial losses.**