# CryptoCurrency AI Trading Bot Dashboard (Experimental) 🤖

## Advanced AI-Powered Trading System with Cross-Asset Correlation Analysis

## It's Like a Point-Scoring Game! 🎯

Imagine you're trying to decide whether to buy or sell something (like trading cards), but you don't want to make a bad choice. So you have a special rule: you need to collect at least 3 points before you can make a trade.

### How You Get Points:

**MACD Signals (±1 point each) 📈**
- Think of this like watching how fast a race car is speeding up or slowing down
- If the car is speeding up = +1 point (good to buy)
- If it's slowing down = -1 point (maybe sell)

**VWAP Signal (±1 point) ⚖️**
- This is like seeing who's winning in a tug-of-war between buyers and sellers
- If buyers are stronger = +1 point
- If sellers are stronger = -1 point

**EMA Signals (Different point values) 📊**
- These are like looking at different time periods to see which way things are moving:
  - Short-term trend (9 days): ±1 point
  - Medium-term crossover (9 vs 21 days): ±2 points
  - Longer trends (50 and 200 days): ±1 point each
  - Big trend change: ±3 points (this is like a really important signal!)

**RSI Signal (±1 point) 🌡️**
- This is like a thermometer that tells you if something is "too hot" (expensive) or "too cold" (cheap)
- If it's too expensive = -1 point
- If it's too cheap = +1 point

### The Rule:
You can only make a trade when you collect at least 3 points in the same direction. It's like needing enough friends to agree with you before making a big decision!

This way, you don't make trades based on just one signal - you wait until multiple "friends" (indicators) agree with you first! 🤝

---

A sophisticated trading bot that uses multi-indicator strategy (MACD, VWAP, EMAs, RSI) enhanced with Reinforcement Learning (RL) to generate intelligent trading signals for Binance Futures markets with advanced position management and PnL-based decision making.

## 🚨 IMPORTANT SAFETY WARNINGS

- **Start with Testnet**: Always test thoroughly on testnet first
- **Use Small Risk %**: Start with 1-2% risk per trade maximum  
- **Monitor Closely**: Never leave the bot completely unattended
- **Set Stop Losses**: Consider manual stop losses for major positions
- **Check Market Hours**: Crypto markets are 24/7, plan accordingly

## Features

### 🚀 Core Trading Features
- **Multi-Indicator Strategy**: MACD + VWAP + EMAs (9,21,50,200) + RSI
- **Advanced Position Management**: Cross margin with position percentage slider  
- **Weighted Signal System**: Minimum signal strength of 3 required for execution
- **Real-time Monitoring**: Live PnL, liquidation prices, and position tracking
- **Enhanced Logging**: Emoji-rich console output with detailed market analysis

### 🧠 Advanced AI Enhancement Features
- **Cross-Asset Correlation Analysis**: Enhanced market awareness using BTC/ETH trends and market context
- **Reinforcement Learning Integration**: Q-Learning agent with enhanced state representation
- **Market Context Intelligence**: 
  - BTC dominance analysis and correlation patterns
  - Fear & Greed Index integration for market sentiment
  - Volatility regime detection (high/medium/low)
  - Market trend classification (bullish/bearish/neutral)
- **Smart Position Management**: PnL-based decision making with cross-asset confirmation
- **Enhanced Risk Management**: 
  - Only closes positions on HOLD signals if PnL is negative (keeps profitable positions)
  - Cross-asset momentum confirmation before position changes
  - Market regime-based risk adjustment
  - BTC correlation-based position sizing
- **Database-Driven Learning**: SQLite database with market context storage and correlation analysis
- **Cost-Optimized AI**: Local sentiment analysis alternative to reduce OpenAI costs by 95%

### 📊 Chart Analysis Bot (NEW!)
- **AI-Powered Chart Analysis**: OpenAI GPT-4o analyzes professional candlestick charts
- **Real-time SUI/USDC Analysis**: 15-minute interval data with 24-hour history
- **Automated Analysis Cycle**: Runs every 15 minutes for continuous market insights
- **Technical Indicators**: EMA 9/21, SMA 50, RSI, MACD, Bollinger Bands, Volume analysis
- **Professional Charts**: High-quality mplfinance candlestick charts with technical overlays
- **Trading Recommendations**: BUY/SELL/HOLD signals with confidence levels and reasoning
- **Risk Assessment**: Key observations and risk factors for informed decision-making

### 🌐 Enhanced Web Dashboard
- **Real-time Dashboard**: "CryptoCurrency AI Trading Bot Dashboard (Experimental)" at http://your-ip:5000
- **🌍 Market Context Section**: NEW! Real-time cross-asset correlation display
  - Live BTC/ETH prices with 24h changes and color-coded indicators
  - BTC Dominance percentage tracking
  - Fear & Greed Index with color-coded sentiment levels
  - Market trend indicators (Bullish/Bearish/Neutral)
  - Cross-asset signal states (BTC Trend, Market Regime, Breadth)
- **Chart Visualization**: Live SUI/USDC chart display with analysis results
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **Live Analysis Display**: OpenAI recommendations, confidence levels, and market insights
- **Performance Metrics**: PnL tracking, win rates, trade history, and system statistics
- **Bot Control**: PIN-protected pause/resume functionality for secure remote control
- **Live Log Streaming**: Real-time logs from all bots (RL, Trading, Chart Analysis)
- **Multi-Bot Monitoring**: Unified view of all system components and their status
- **📰 Smart Market News**: Enhanced cryptocurrency news with cost-optimized AI sentiment analysis
  - Paginated news display (10 articles per page)
  - Dual-mode sentiment analysis: OpenAI GPT-4o-mini OR local keyword-based (FREE)
  - Aggressive caching system (1h-24h) to reduce API costs by 90%
  - Real-time market sentiment indicators with confidence levels
  - Bearish/Bullish sentiment badges in news header

### 📊 Enhanced Database & Analytics
- **SQLite Database**: Stores signals, trades, market data, performance metrics, and cross-asset correlation data
- **Market Context Storage**: NEW! Dedicated table for BTC/ETH data, Fear & Greed Index, market trends
- **Cross-Asset Correlation Analysis**: Historical correlation patterns and regime detection
- **Performance Tracking**: Win rate, PnL analysis, trade history with market context correlation
- **Data-Driven Decisions**: Enhanced RL model learns from actual trading outcomes plus market context
- **Chart Analysis Storage**: AI recommendations and market analysis history
- **Cost Optimization Analytics**: Track API usage and cost savings from local vs OpenAI sentiment analysis

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

2. **Add your API credentials to .env:**
   ```
   BINANCE_API_KEY=your_binance_api_key_here
   BINANCE_SECRET_KEY=your_binance_secret_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   BOT_CONTROL_PIN=your_6_digit_pin_here
   NEWS_API_KEY=your_newsapi_key_here
   USE_LOCAL_SENTIMENT=true  # Enable cost-saving mode (optional)
   ```

3. **Get Required API Keys:**

   **Binance API Keys:**
   - Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
   - Create a new API key
   - Enable "Enable Futures" permission
   - Restrict API access to your IP address (recommended)
   - **Never share your secret key!**

   **OpenAI API Key:**
   - Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new API key for GPT-4 access
   - Required for chart analysis and market sentiment analysis
   - **Keep your API key secure!**

   **NewsAPI Key:**
   - Go to [NewsAPI](https://newsapi.org/)
   - Sign up for a free account to get your API key
   - Required for cryptocurrency market news and sentiment analysis
   - Free tier includes 1000 requests per day

## 💰 Cost Optimization Features

### **AI Sentiment Analysis Cost Reduction**
The system now includes advanced cost optimization to reduce OpenAI API expenses by up to **95%**:

#### **Dual-Mode Sentiment Analysis**
- **Premium Mode**: OpenAI GPT-4o-mini (60x cheaper than GPT-4)
- **Cost-Saving Mode**: Local keyword-based analysis (100% FREE)

#### **Smart Caching System**
- **1-hour caching**: Premium mode with minimal API calls
- **24-hour caching**: Cost-saving mode for maximum savings
- **File-based caching**: Persistent across restarts

#### **Cost Configuration**
```bash
# Switch to cost-saving mode (FREE sentiment analysis)
python3 configure_costs.py cost-saving

# Switch to premium mode (GPT-4o-mini sentiment analysis)
python3 configure_costs.py premium

# Check current cost settings
python3 configure_costs.py status
```

#### **Monthly Cost Comparison**
| Mode | Sentiment Analysis | Monthly Cost | Features |
|------|-------------------|--------------|----------|
| **Old GPT-4** | GPT-4 | $15-30/month | High-quality sentiment |
| **Premium** | GPT-4o-mini | $1-3/month | Good sentiment, 60x cheaper |
| **Cost-Saving** | Local keywords | $0/month | Basic sentiment, FREE |

### **Additional Cost Optimizations**
- **CoinGecko API**: FREE (rate limited)
- **Fear & Greed Index**: FREE
- **NewsAPI**: FREE tier available
- **Cross-asset data**: FREE from public APIs

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

### Standard Bot
1. **Start the bot:**
   ```bash
   python trading_bot.py
   ```

### RL-Enhanced Bot with Full System (Recommended)
1. **Start all bots (RL, Web Dashboard, Chart Analysis):**
   ```bash
   ./restart_both.sh
   ```

### 🔄 Multi-Claude Code Development Setup
For parallel development on different services using multiple Claude Code instances:

1. **Setup modular services (one-time setup):**
   ```bash
   ./scripts/setup_worktrees.sh   # Initialize git worktrees
   ./scripts/restart_all.sh       # Start all 4 services
   ```

2. **Launch 4 Claude Code instances:**
   ```bash
   # Terminal 1: claude code /root/7monthIndicator/services/trading
   # Terminal 2: claude code /root/7monthIndicator/services/web-dashboard  
   # Terminal 3: claude code /root/7monthIndicator/services/chart-analysis
   # Terminal 4: claude code /root/7monthIndicator/services/mcp-server
   ```

3. **Service assignments:**
   - **Instance 1** (Trading): RL algorithms, trading logic, position management
   - **Instance 2** (Web Dashboard): UI/UX, Flask routes, mobile responsiveness
   - **Instance 3** (Chart Analysis): AI analysis, chart generation, visualization
   - **Instance 4** (MCP Server): Database APIs, query optimization, data management

2. **Individual bot commands:**
   ```bash
   # RL Bot
   ./start_rl_bot.sh start     # Start RL trading bot
   ./start_rl_bot.sh status    # Check bot status and positions
   ./start_rl_bot.sh logs      # View live logs  
   ./start_rl_bot.sh stop      # Stop the bot
   ./start_rl_bot.sh restart   # Restart the bot

   # Chart Analysis Bot  
   ./start_chart_bot.sh start    # Start chart analysis bot
   ./start_chart_bot.sh status   # Check chart bot status
   ./start_chart_bot.sh stop     # Stop chart bot
   ./start_chart_bot.sh restart  # Restart chart bot

   # Web Dashboard
   ./start_web_dashboard.sh start    # Start web dashboard
   ./start_web_dashboard.sh stop     # Stop web dashboard
   ./start_web_dashboard.sh restart  # Restart web dashboard
   ```

3. **Access Web Dashboard:**
   - **Local**: http://localhost:5000
   - **Remote**: http://your-server-ip:5000
   - Features live charts, AI analysis, bot control, and monitoring

4. **Monitor logs:**
   - Console output shows real-time analysis with RL decisions
   - `logs/rl_bot_main.log` - RL bot history
   - `trading_bot.log` - Standard bot history  
   - `chart_analysis_bot.log` - Chart analysis and OpenAI results
   - `web_dashboard.log` - Web server logs
   - **Web Interface**: Access logs via dashboard at /logs

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

## 🤖 RL Model Retraining

The bot includes an advanced RL model retraining system that learns from your actual trading data to improve decision-making over time.

### 🔧 How It Works

1. **Data Collection**: The bot continuously stores signals, trades, and outcomes in a SQLite database
2. **Outcome Analysis**: Real trade results are categorized (good_profit, small_profit, small_loss, bad_loss)
3. **Enhanced Reward System**: The RL agent learns with rewards/penalties based on actual P&L
4. **Continuous Learning**: Model improves its decision-making based on historical patterns

### 📊 Retraining Process

#### Automatic Backup
Before retraining, your current model is automatically backed up:
```bash
# Backup is created with timestamp
rl_trading_model_backup_YYYYMMDD_HHMMSS.pkl
```

#### Manual Retraining
To retrain your RL model with fresh data:

```bash
# Activate virtual environment
source venv/bin/activate

# Run retraining (requires sufficient data)
python3 retrain_rl_model.py
```

#### What Happens During Retraining:
1. **Data Preparation**: Loads signals and trade outcomes from database (last 30 days)
2. **Enhanced Learning**: Uses improved reward system:
   - **Big rewards** for profitable trades (>2% profit)
   - **Heavy penalties** for large losses (>2% loss)
   - **Streak bonuses/penalties** for consecutive wins/losses
   - **Smart HOLD rewards** for avoiding bad trades
3. **Training Episodes**: Runs 150 training episodes with real market scenarios
4. **Model Updates**: Saves improved model with enhanced decision-making
5. **Backup Creation**: Creates episodic backups every 50 episodes

### 📈 Retraining Requirements

- **Minimum Data**: 50+ signals with indicators (usually 1-2 hours of bot runtime)
- **Optimal Data**: 2000+ signals with trade outcomes (24-48 hours of runtime)
- **Best Results**: 30+ days of trading data with varied market conditions

### 🎯 Enhanced Logic After Retraining

The retrained model implements intelligent position management:

#### HOLD Signal Logic
```
Current Position: LONG +$50 PnL → HOLD Signal
Result: ✅ Position kept open (positive PnL)
Log: "HOLD signal detected - keeping LONG position open (positive PnL: $50.00)"

Current Position: LONG -$30 PnL → HOLD Signal  
Result: ❌ Position closed (negative PnL)
Log: "HOLD signal detected - closing LONG position (negative PnL: $-30.00)"
```

#### Signal Flip Logic
```
Current Position: LONG +$50 PnL → SELL Signal
Result: ✅ Keep LONG position (profitable)
Log: "SELL signal detected with open LONG position - keeping position open (positive PnL: $50.00)"

Current Position: LONG -$30 PnL → SELL Signal
Result: ❌ Close LONG, Open SHORT (cutting losses)
Log: "SELL signal detected with open LONG position - closing due to negative PnL: $-30.00"
Log: "📈 Executing new trade after closing opposite position based on SELL signal..."
```

### 📋 Retraining Results Analysis

After retraining, the system provides detailed analysis:

```
🎉 Retraining complete! Best performance: 0.2%
📊 Recent Performance (last 50 episodes):
   Average win rate: 49.1%
   Average return: -0.0%
   Average trades per episode: 34.4
   Total states learned: 13
   Total episodes: 155
📈 Learning Progress:
   Early episodes avg return: 0.0%
   Recent episodes avg return: -0.0%
   Improvement: -0.0%
```

### 🔄 When to Retrain

- **After significant market changes** (new volatility patterns)
- **Weekly/bi-weekly** for optimal performance
- **After 100+ closed trades** for maximum learning benefit
- **When win rate drops** below acceptable levels

### 💾 Model Files

- `rl_trading_model.pkl` - Current active model
- `rl_trading_model_backup_*.pkl` - Timestamped backups
- `rl_trading_model_episode_*.pkl` - Training checkpoint backups

### 🧪 Testing Retrained Models

After retraining, test the model's recommendations:
```bash
python3 -c "
from lightweight_rl import LightweightRLSystem
rl = LightweightRLSystem()
recommendation = rl.get_trading_recommendation({
    'rsi': 45, 'macd': -0.01, 'price': 3.68,
    'vwap': 3.70, 'ema_9': 3.65, 'ema_21': 3.67
})
print(f'Action: {recommendation[\"action\"]}, Confidence: {recommendation[\"confidence\"]:.1%}')
"
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

#### Trading Bot Issues
- **API Permission Error**: Enable Futures trading in API settings
- **Insufficient Balance**: Ensure adequate USDC balance for SUIUSDC trading
- **Symbol Not Found**: Check symbol formatting (e.g., 'SUIUSDC')
- **Margin Type Error**: May be already set to CROSS (this is normal)
- **Rate Limiting**: Reduce check frequency if needed
- **Position Size Error**: Check symbol precision and minimum order size

#### RL Model Issues
- **"No module named 'numpy'"**: Activate virtual environment: `source venv/bin/activate`
- **"Insufficient data for training"**: Let bot run for at least 2-3 hours before retraining
- **"Model file not found"**: First time setup - model will be created automatically
- **Poor RL performance**: Need more diverse trading data; run bot through different market conditions
- **Retraining takes too long**: Reduce episodes in `retrain_rl_model.py` (default: 150)

#### Chart Analysis Bot Issues
- **"Missing OpenAI API key"**: Add `OPENAI_API_KEY` to your `.env` file
- **"Model not found" errors**: OpenAI deprecated older models, bot uses `gpt-4o`
- **"Chart generation failed"**: Check if `mplfinance` is installed: `pip install mplfinance`
- **"No chart analysis data"**: Bot runs every 15 minutes, wait for first cycle
- **Chart not displaying**: Check web dashboard at `/api/chart-image` endpoint

#### Web Dashboard Issues  
- **Dashboard not accessible**: Check if port 5000 is open and not blocked by firewall
- **Chart image not loading**: Verify chart analysis bot is running: `./start_chart_bot.sh status`
- **PIN protection not working**: Ensure `BOT_CONTROL_PIN` is set in `.env` file
- **Mobile display issues**: Dashboard is responsive, try refreshing or clearing cache
- **Market news not showing**: Verify `NEWS_API_KEY` is set in `.env` file
- **Sentiment analysis not working**: Check OpenAI API key and ensure sufficient credits
- **News pagination errors**: Restart web dashboard: `./start_web_dashboard.sh restart`

#### Database Issues  
- **"Database locked"**: Stop bot before running retraining: `./start_rl_bot.sh stop`
- **"No signals in database"**: Let bot run and collect data first
- **Database corruption**: Backup and delete `trading_bot.db`, bot will recreate it

### Error Logs:
- **Standard Bot**: Check `trading_bot.log` 
- **RL Bot**: Check `logs/rl_bot_main.log` and `logs/rl_bot_error.log`
- **Chart Analysis Bot**: Check `chart_analysis_bot.log`
- **Web Dashboard**: Check `web_dashboard.log`
- **Retraining**: Check `rl_retraining.log`
- **Web Interface**: Access all logs via dashboard at `/logs`

### Debugging Tips:
- Start with testnet mode first
- Use smaller position percentages initially (2% instead of 51%)
- Monitor liquidation prices closely
- Check Binance API status if experiencing connection issues
- For RL issues, check if database contains enough data: `ls -la *.db`
- Monitor all bot statuses: 
  - `./start_rl_bot.sh status`
  - `./start_chart_bot.sh status`  
  - `./start_web_dashboard.sh status`
- Access web dashboard for real-time monitoring and chart analysis

### RL Model Recovery:
If RL model becomes corrupted:
```bash
# Restore from backup
cp rl_trading_model_backup_YYYYMMDD_HHMMSS.pkl rl_trading_model.pkl

# Or start fresh (will retrain automatically)
rm rl_trading_model.pkl
./start_rl_bot.sh restart
```

## 🚀 Complete System Overview

This trading bot system now includes three integrated components:

### **1. RL-Enhanced Trading Bot**
- Multi-indicator strategy with reinforcement learning
- Smart position management and PnL-based decisions  
- Continuous learning from trading outcomes
- Automated trading with risk management

### **2. Chart Analysis Bot** 
- AI-powered chart analysis using OpenAI GPT-4o
- Professional candlestick charts with technical indicators
- Automated analysis every 15 minutes
- Trading recommendations with detailed reasoning

### **3. Web Dashboard**
- Real-time monitoring and control interface
- Live chart display with AI analysis results
- Performance metrics and bot status monitoring
- PIN-protected remote control capabilities

### **Quick Start Commands**
```bash
# Start everything at once
./restart_both.sh

# Individual control
./start_rl_bot.sh start           # Start RL trading bot
./start_chart_bot.sh start        # Start chart analysis bot  
./start_web_dashboard.sh start    # Start web dashboard

# Access dashboard
# Local: http://localhost:5000
# Remote: http://your-ip:5000
```

### **System Features**
- **📊 Live Charts**: Real-time SUI/USDC charts with AI analysis
- **🤖 Multi-Bot Management**: Unified control of all components
- **📱 Mobile Responsive**: Works on all devices  
- **🔒 Secure Access**: PIN-protected controls
- **📝 Live Logging**: Real-time log streaming from all bots
- **⏰ Automated Analysis**: Chart analysis every 15 minutes
- **🧠 AI Integration**: OpenAI GPT-4o powered recommendations
- **📰 Smart News**: Paginated cryptocurrency news with AI sentiment analysis
- **📈 Market Sentiment**: Real-time bullish/bearish indicators with confidence ratings

## 🚀 **Quick Reference: Multi-Claude Code Launch**

Ready to develop with multiple Claude Code instances? Here's your quick launch guide:

```bash
# Launch 4 Claude Code instances for parallel development:
# Terminal 1: claude code /root/7monthIndicator/services/trading
# Terminal 2: claude code /root/7monthIndicator/services/web-dashboard  
# Terminal 3: claude code /root/7monthIndicator/services/chart-analysis
# Terminal 4: claude code /root/7monthIndicator/services/mcp-server

# Master control:
./scripts/restart_all.sh                 # Control all services
./scripts/setup_worktrees.sh             # Initialize git worktrees (one-time)
./scripts/validate_migration.sh          # Validate system integrity

# Access points:
# Web Dashboard: http://localhost:5000
# MCP Server API: http://localhost:3000
```

**Each Claude Code instance works on its own service branch with isolated development, independent testing, and seamless integration capabilities!** 🎯

## Disclaimer

This trading bot is for educational purposes only. Trading cryptocurrencies involves substantial risk and may not be suitable for all investors. Past performance is not indicative of future results. Always do your own research and consider your financial situation before trading.

**Use at your own risk. The authors are not responsible for any financial losses.**