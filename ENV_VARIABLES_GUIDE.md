# Environment Variables Guide

## Overview
This guide covers all environment variables used in the 7-Month Indicator Trading Bot system. The bot uses environment variables for configuration to keep sensitive information secure and allow easy deployment across different environments.

## Quick Setup

### 1. **Using the Setup Script (Recommended)**
```bash
python3 setup_env.py                    # Full interactive setup
python3 setup_env.py validate          # Validate current setup
python3 setup_env.py interactive       # Interactive setup only
python3 setup_env.py template          # Create from template
```

### 2. **Manual Setup**
```bash
cp .env.comprehensive .env
# Edit .env with your actual values
```

## Critical Environment Variables

These **MUST** be configured for the bot to work:

### **Binance API** 
```bash
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
```
- Get from: https://www.binance.com/en/my/settings/api-management
- Required permissions: Spot & Margin Trading, Futures Trading

### **Telegram Notifications**
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
BOT_CONTROL_PIN=123456
```
- Create bot: https://t.me/BotFather
- Get chat ID by messaging your bot first

### **OpenAI API (for Chart Analysis)**
```bash
OPENAI_API_KEY=your_openai_api_key_here
```
- Get from: https://platform.openai.com/api-keys

## Trading Configuration

### **Basic Trading Settings**
```bash
SYMBOL=SUIUSDC                    # Trading pair
LEVERAGE=50                       # Futures leverage (1-125)
POSITION_PERCENT=51.0            # % of balance per trade
RISK_PERCENT=2.0                 # Risk per trade
TRADING_INTERVAL=300             # Seconds between signal checks
MIN_SIGNAL_STRENGTH=3            # Minimum signal strength (1-5)
```

### **Enhanced RL Settings**
```bash
RL_ENHANCED_MODE=true            # Enable RL enhancement
USE_ENHANCED_REWARDS=true        # Use advanced reward system
RL_CONFIDENCE_THRESHOLD=0.6      # Minimum RL confidence
```

### **Risk Management**
```bash
STOP_LOSS_PERCENT=5.0           # Stop loss %
TAKE_PROFIT_PERCENT=10.0        # Take profit %
MAX_DAILY_TRADES=20             # Max trades per day
DRAWDOWN_LIMIT=15.0             # Max portfolio drawdown %
MAX_CONSECUTIVE_LOSSES=3         # Emergency stop after losses
```

## Service-Specific Configuration

### **Web Dashboard**
```bash
FLASK_HOST=0.0.0.0              # Bind to all interfaces
FLASK_PORT=5000                 # Web dashboard port
FLASK_ENV=production            # Flask environment
DASHBOARD_UPDATE_INTERVAL=30     # Dashboard refresh seconds
MAX_CHART_HISTORY_DAYS=90       # Chart history retention
```

### **Chart Analysis Bot**
```bash
CHART_ANALYSIS_INTERVAL=900     # Analysis interval (seconds)
CHART_TIMEFRAME=15m             # Chart timeframe
CHART_HISTORY_HOURS=24          # Hours of data to analyze
AI_MODEL=gpt-4o                 # OpenAI model to use
MAX_ANALYSIS_RETRIES=3          # Retry failed analysis
```

### **Database Configuration**
```bash
DATABASE_PATH=data/trading_bot.db    # SQLite database path
DATABASE_BACKUP_ENABLED=true        # Enable auto backups
KEEP_SIGNALS_DAYS=90                # Signal retention
KEEP_TRADES_DAYS=365                # Trade history retention
```

## Security Settings

### **Authentication & Access**
```bash
FLASK_SECRET_KEY=your_flask_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
ENABLE_IP_WHITELIST=false
ALLOWED_IPS=127.0.0.1,localhost
```

### **TLS/SSL (Production)**
```bash
TLS_ENABLED=false
TLS_CERT_PATH=/path/to/cert.pem
TLS_KEY_PATH=/path/to/key.pem
```

## Development & Testing

### **Development Mode**
```bash
DEVELOPMENT_MODE=false          # Enable dev features
DEBUG_TRADING=false            # Debug trading decisions
PAPER_TRADING=false            # Simulate trading
TEST_MODE=false                # Use test database
USE_TESTNET=false              # Use Binance testnet
```

### **Testing Configuration**
```bash
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret
TEST_DATABASE_PATH=test_trading_bot.db
TEST_BALANCE=10000
```

## Optional Integrations

### **Additional Notifications**
```bash
# Discord
DISCORD_WEBHOOK_URL=your_discord_webhook_url
DISCORD_NOTIFICATIONS_ENABLED=false

# Slack  
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_NOTIFICATIONS_ENABLED=false

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_NOTIFICATIONS_ENABLED=false
```

### **News & Market Data**
```bash
NEWS_API_KEY=your_news_api_key
NEWS_SOURCES=coindesk,cointelegraph
NEWS_REFRESH_INTERVAL=1800
MARKET_DATA_PROVIDER=binance
```

## Environment File Locations

The system uses multiple `.env` files:

```
├── .env                           # Main configuration
├── .env.comprehensive             # Complete template
├── .env.example                   # Basic template
└── services/
    ├── trading/.env              # Trading service config
    ├── web-dashboard/.env        # Dashboard config
    ├── chart-analysis/.env       # Chart analysis config
    └── mcp-server/.env          # MCP server config
```

## Validation & Troubleshooting

### **Validate Configuration**
```bash
python3 setup_env.py validate
```

### **Common Issues**

1. **"Missing critical variables"**
   - Run `python3 setup_env.py interactive`
   - Ensure all required API keys are set

2. **"Service environment missing"**
   - Service `.env` files are auto-generated
   - Run setup script to recreate them

3. **"Invalid API credentials"**
   - Check Binance API key permissions
   - Ensure IP restrictions allow your server

4. **"Bot not receiving messages"**
   - Verify Telegram bot token
   - Send a message to your bot first to get chat ID

### **Security Best Practices**

1. **Never commit .env files to git**
   - Add `.env*` to `.gitignore`
   - Use `.env.example` for templates

2. **Rotate API keys regularly**
   - Binance: Monthly rotation recommended
   - OpenAI: Monitor usage and rotate quarterly

3. **Use strong secrets**
   - Generate random Flask/JWT secrets
   - Use 6+ digit control PINs

4. **Limit API permissions**
   - Binance: Only enable required permissions
   - Use IP restrictions when possible

## Environment Inheritance

Services inherit variables in this order:
1. Service-specific `.env` file
2. Main `.env` file  
3. System environment variables
4. Default values in code

## Advanced Configuration

### **Performance Tuning**
```bash
MAX_CPU_USAGE=80
MAX_MEMORY_USAGE=2048
WORKER_PROCESSES=auto
HEALTH_CHECK_INTERVAL=60
```

### **Clustering (Multi-Instance)**
```bash
LOAD_BALANCER_ENABLED=false
INSTANCE_ID=primary
CLUSTER_MODE=false
```

### **ML Model Configuration**
```bash
ML_MODEL_RETRAINING_INTERVAL=86400
AUTO_MODEL_BACKUP=true
MODEL_PERFORMANCE_THRESHOLD=0.6
```

## Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BINANCE_API_KEY` | ✅ | - | Binance API key |
| `BINANCE_SECRET_KEY` | ✅ | - | Binance secret key |
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Telegram bot token |
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key |
| `SYMBOL` | ❌ | `SUIUSDC` | Trading pair |
| `LEVERAGE` | ❌ | `50` | Futures leverage |
| `FLASK_PORT` | ❌ | `5000` | Dashboard port |
| `USE_ENHANCED_REWARDS` | ❌ | `true` | Enhanced RL rewards |

## Getting Help

If you need help with environment configuration:

1. **Run the validator**: `python3 setup_env.py validate`
2. **Check service logs**: `tail -f logs/systemd.log`  
3. **Test individual components**: Use test scripts in the repository
4. **Review documentation**: Check `README.md` for service-specific guides

The setup script provides interactive guidance for all critical configurations.