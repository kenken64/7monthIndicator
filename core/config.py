#!/usr/bin/env python3
"""
Configuration file for Binance Futures Trading Bot
Modify these settings to customize your trading strategy
"""
import os

# Trading Configuration
TRADING_CONFIG = {
    # Basic Settings
    'symbol': 'BTCUSDT',           # Trading pair
    'leverage': 10,                # Leverage multiplier (1-125)
    'risk_percentage': 2.0,        # Risk per trade as % of balance (1-5% recommended)
    'check_interval': 300,         # Check interval in seconds (300 = 5 minutes)
    'use_testnet': True,           # Set to False for live trading
    
    # Signal Strength Thresholds
    'min_signal_strength': 3,      # Minimum signal strength to execute trade
    'strong_signal_threshold': 5,  # Threshold for strong signals
    
    # Position Management
    'max_positions': 1,            # Maximum concurrent positions
    'allow_position_flip': True,   # Allow flipping from long to short
}

# Technical Indicator Settings
INDICATOR_CONFIG = {
    # EMA Settings
    'ema_fast': 9,                 # Fast EMA period
    'ema_medium': 21,              # Medium EMA period  
    'ema_slow': 50,                # Slow EMA period
    'ema_trend': 200,              # Long-term trend EMA
    
    # MACD Settings
    'macd_fast': 12,               # MACD fast EMA
    'macd_slow': 26,               # MACD slow EMA
    'macd_signal': 9,              # MACD signal line EMA
    
    # RSI Settings
    'rsi_period': 14,              # RSI calculation period
    'rsi_overbought': 70,          # RSI overbought threshold
    'rsi_oversold': 30,            # RSI oversold threshold
    
    # Data Settings
    'klines_limit': 500,           # Number of historical candles to fetch
    'timeframe': '5m',             # Timeframe for analysis (1m, 3m, 5m, 15m, 30m, 1h, etc.)
}

# Signal Weight Configuration
SIGNAL_WEIGHTS = {
    # MACD Signals
    'macd_crossover': 1,           # MACD line crossing signal line
    'macd_histogram_momentum': 1,   # MACD histogram expansion
    
    # VWAP Signals  
    'vwap_position': 1,            # Price position relative to VWAP
    
    # EMA Signals
    'price_vs_ema': 1,             # Price relative to individual EMAs
    'ema_crossover_fast_medium': 2, # 9 EMA vs 21 EMA crossover
    'golden_death_cross': 3,       # 50 EMA vs 200 EMA crossover
    
    # RSI Signals
    'rsi_extremes': 1,             # RSI overbought/oversold
    'rsi_divergence': 2,           # RSI divergence (if implemented)
}

# Risk Management Settings
RISK_CONFIG = {
    'max_drawdown': 10.0,          # Max portfolio drawdown % before stopping
    'daily_loss_limit': 5.0,       # Daily loss limit as % of balance
    'max_trades_per_day': 20,      # Maximum trades per day
    
    # Stop Loss Settings (recommended for risk management)
    'use_stop_loss': True,         # Enable stop loss orders (RECOMMENDED)
    'stop_loss_percentage': 10.0,  # Stop loss % from entry price (10% for balanced risk)
    'use_take_profit': True,       # Enable take profit orders
    'take_profit_percentage': 10.0, # Take profit % from entry price (1:1 risk/reward)
    
    # Advanced Stop Loss Settings
    'trailing_stop_loss': False,   # Enable trailing stop loss
    'trailing_stop_percentage': 5.0, # Trailing stop activation distance
    'breakeven_threshold': 5.0,    # Move stop to breakeven after X% profit
}

# Logging and Monitoring
LOGGING_CONFIG = {
    'log_level': 'INFO',           # DEBUG, INFO, WARNING, ERROR
    'log_to_file': True,           # Save logs to file
    'log_filename': 'trading_bot.log',
    'log_trades': True,            # Log all trade executions
    'save_data': False,            # Save market data for analysis
}

# Notification Settings (future feature)
NOTIFICATION_CONFIG = {
    'enable_notifications': False,  # Enable trade notifications
    'discord_webhook': None,       # Discord webhook URL
    'telegram_bot_token': None,    # Telegram bot token  
    'telegram_chat_id': None,      # Telegram chat ID
}

# NewsAPI Configuration
# Load environment variables first
from dotenv import load_dotenv
load_dotenv('.env')

NEWS_CONFIG = {
    'api_key': os.getenv('NEWS_API_KEY') or 'ecc8081a11e24c1490722c9da1564fe5',
}


# Advanced Settings
ADVANCED_CONFIG = {
    'use_market_orders': True,     # Use market orders (vs limit orders)
    'slippage_tolerance': 0.1,     # Max slippage % for limit orders
    'order_timeout': 60,           # Order timeout in seconds
    'reconnect_attempts': 3,       # API reconnection attempts
    'rate_limit_buffer': 0.1,      # Buffer for API rate limiting
}

# Backtesting Configuration  
BACKTEST_CONFIG = {
    'start_date': '2024-01-01',    # Backtest start date
    'end_date': '2024-12-31',      # Backtest end date
    'initial_balance': 10000,      # Starting balance for backtest
    'commission': 0.0004,          # Trading commission (0.04% for Binance Futures)
}

# Strategy Validation Rules
VALIDATION_RULES = {
    'min_candles_for_signal': 200, # Minimum candles needed for valid signals
    'require_volume_confirmation': True, # Require volume confirmation
    'filter_weekend_trading': False, # Skip weekend trading (crypto trades 24/7)
    'avoid_news_times': False,     # Avoid trading during major news (needs implementation)
}

def get_trading_symbols():
    """Return list of symbols to trade (for multi-symbol bots)"""
    return [
        'BTCUSDT',
        'ETHUSDT', 
        'BNBUSDT',
        # Add more symbols as needed
    ]

def get_timeframes():
    """Return list of timeframes for multi-timeframe analysis"""
    return ['5m', '15m', '1h']  # Primary, secondary, trend timeframes

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    if TRADING_CONFIG['risk_percentage'] > 5:
        errors.append("Risk percentage > 5% not recommended")
    
    if TRADING_CONFIG['leverage'] > 50:
        errors.append("High leverage (>50x) is very risky")
        
    if INDICATOR_CONFIG['rsi_overbought'] <= INDICATOR_CONFIG['rsi_oversold']:
        errors.append("RSI overbought must be > RSI oversold")
        
    return errors

# Export main config for easy import
CONFIG = {
    'trading': TRADING_CONFIG,
    'indicators': INDICATOR_CONFIG,
    'signals': SIGNAL_WEIGHTS,
    'risk': RISK_CONFIG,
    'logging': LOGGING_CONFIG,
    'notifications': NOTIFICATION_CONFIG,
    'advanced': ADVANCED_CONFIG,
    'backtest': BACKTEST_CONFIG,
    'validation': VALIDATION_RULES,
}

if __name__ == "__main__":
    # Validate configuration when run directly
    errors = validate_config()
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
        
    # Display key settings
    print(f"\nKey Settings:")
    print(f"  Symbol: {TRADING_CONFIG['symbol']}")
    print(f"  Leverage: {TRADING_CONFIG['leverage']}x")
    print(f"  Risk: {TRADING_CONFIG['risk_percentage']}%")
    print(f"  Timeframe: {INDICATOR_CONFIG['timeframe']}")
    print(f"  Min Signal: {TRADING_CONFIG['min_signal_strength']}")