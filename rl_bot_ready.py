#!/usr/bin/env python3
"""
RL-Enhanced Trading Bot - Ready to Run
Direct copy of original bot with RL integration
"""

import os
import time
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
import argparse
import sys
import requests
import json
warnings.filterwarnings('ignore')

# Import RL enhancement
try:
    from rl_patch import create_rl_enhanced_bot
    RL_ENHANCEMENT_ENABLED = True
    rl_generator, rl_enhancer = create_rl_enhanced_bot()
    print("🤖 RL Enhancement: ACTIVATED")
except ImportError as e:
    RL_ENHANCEMENT_ENABLED = False
    print(f"⚠️ RL Enhancement: NOT AVAILABLE - {e}")

# Import unified signal aggregator
try:
    from unified_signal_aggregator import create_aggregator
    from signal_data_collector import SignalDataCollector
    UNIFIED_SIGNALS_ENABLED = True
    print("📊 Unified Signal Aggregator: ACTIVATED")
except ImportError as e:
    UNIFIED_SIGNALS_ENABLED = False
    print(f"⚠️ Unified Signal Aggregator: NOT AVAILABLE - {e}")

# Import database module
from database import get_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Handle Telegram notifications for trading signals
    
    This class manages sending trading notifications to Telegram channels/chats.
    It handles authentication, message formatting, and error handling for
    communication with the Telegram Bot API.
    """
    
    def __init__(self):
        """Initialize Telegram notifier with credentials from environment variables"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '@bnbfutura_bot')
        self.enabled = bool(self.bot_token and self.bot_token.strip())
        
        if self.enabled:
            logger.info(f"📱 Telegram notifications enabled for {self.chat_id}")
        else:
            logger.warning("📱 Telegram notifications disabled - no bot token provided")
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send message to Telegram bot
        
        Args:
            message: The message text to send
            parse_mode: Message formatting mode ('HTML' or 'Markdown')
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📱 Telegram message sent successfully to {self.chat_id}")
                return True
            else:
                error_msg = response.text
                if "chat not found" in error_msg:
                    logger.error(f"📱 Telegram Error: Chat '{self.chat_id}' not found")
                    logger.error("💡 Please check: 1) Bot is added to the channel/group, 2) Chat ID is correct, 3) Bot has permission to send messages")
                else:
                    logger.error(f"📱 Telegram API error: {response.status_code} - {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"📱 Failed to send Telegram message: {e}")
            return False
    
    def send_signal_notification(self, signal_data: Dict, current_price: float, position_info: Dict = None) -> bool:
        """Send RL signal notification to Telegram
        
        Creates a formatted trading signal message with current market data,
        RL enhancement status, position information, and analysis reasons.
        
        Args:
            signal_data: Dictionary containing signal strength, direction, and analysis
            current_price: Current market price of the trading pair
            position_info: Optional current position details for context
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Signal emoji and name
            signal = signal_data.get('signal', 0)
            signal_emoji = "🟢" if signal > 0 else "🔴" if signal < 0 else "⚪"
            signal_name = "BUY" if signal > 0 else "SELL" if signal < 0 else "HOLD"
            
            # RL enhancement status
            rl_status = "🤖 RL Enhanced" if signal_data.get('rl_enhanced') else "📊 Traditional"
            
            # Position status
            pos_status = ""
            if position_info and position_info.get('side'):
                pnl_emoji = "🟢" if position_info.get('unrealized_pnl', 0) > 0 else "🔴"
                pos_status = f"\n📍 Current Position: {position_info['side']} {position_info.get('size', 0):.1f}"
                pos_status += f"\n💰 PnL: {pnl_emoji} ${position_info.get('unrealized_pnl', 0):.2f}"

            # Determine strength display based on unified signal availability
            if signal_data.get('unified_details'):
                # Use unified 0-10 scale
                strength_display = f"{signal_data['unified_details']['strength']:.1f}/10"
            else:
                # Use legacy 0-5 scale
                strength_display = f"{signal_data.get('strength', 0)}/5"

            # Create message
            message = f"""<b>🚀 SUI/USDC RL Trading Signal</b>

{signal_emoji} <b>Signal: {signal_name}</b>
💪 Strength: {strength_display}
💹 Price: ${current_price:.4f}
{rl_status}
{pos_status}

📊 Analysis:"""
            
            # Add top reasons
            reasons = signal_data.get('reasons', [])[:3]  # Top 3 reasons
            for reason in reasons:
                message += f"\n• {reason}"
            
            message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"📱 Error creating signal notification: {e}")
            return False

class TechnicalIndicators:
    """Calculate technical indicators for trading signals
    
    This class provides static methods for calculating common technical analysis
    indicators including EMA, RSI, MACD, and VWAP. All methods are stateless
    and work with pandas Series data structures.
    """
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average
        
        EMA gives more weight to recent prices, making it more responsive
        to price changes than simple moving average.
        
        Args:
            data: Time series data (usually closing prices)
            period: Number of periods for the EMA calculation
            
        Returns:
            pd.Series: EMA values for each data point
        """
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index
        
        RSI oscillates between 0 and 100. Values above 70 indicate overbought
        conditions, while values below 30 indicate oversold conditions.
        
        Args:
            data: Time series data (usually closing prices)
            period: Number of periods for RSI calculation (default: 14)
            
        Returns:
            pd.Series: RSI values for each data point
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)
        
        MACD consists of the MACD line (fast EMA - slow EMA), signal line
        (EMA of MACD line), and histogram (MACD line - signal line).
        
        Args:
            data: Time series data (usually closing prices)
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
            
        Returns:
            Dict containing 'macd', 'macd_signal', and 'macd_histogram' Series
        """
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price
        
        VWAP represents the average price weighted by volume. It's used to
        determine if current price is above or below the average trading price.
        
        Args:
            high: High prices for each period
            low: Low prices for each period  
            close: Closing prices for each period
            volume: Volume for each period
            
        Returns:
            pd.Series: VWAP values for each period
        """
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()

class RLEnhancedBinanceFuturesBot:
    """RL-Enhanced Binance Futures Trading Bot
    
    A comprehensive trading bot that integrates Reinforcement Learning enhancements
    with traditional technical analysis. Features include:
    - RL-enhanced signal generation and position sizing
    - Risk management with take profit and stop loss
    - Position tracking and reconciliation with Binance
    - Telegram notifications
    - Database integration for trade and signal storage
    - Pause/resume functionality for manual control
    """
    
    def __init__(self, symbol: str = 'SUIUSDC', leverage: int = 50, position_percentage: float = 2.0):
        """Initialize the RL-Enhanced Trading Bot
        
        Sets up API connections, trading parameters, database connections,
        and performs initial position reconciliation.
        
        Args:
            symbol: Trading pair symbol (e.g., 'SUIUSDC')
            leverage: Futures leverage multiplier (default: 50x)
            position_percentage: Percentage of account balance to use per trade (default: 2%)
        """
        # API Setup - Initialize Binance futures client with credentials
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Binance API credentials not found in environment variables")
        
        self.client = Client(self.api_key, self.secret_key, testnet=False)
        
        # Trading Parameters - Conservative defaults for safety
        # Position size reduced from original 51% to 2% for risk management
        self.symbol = symbol
        self.leverage = leverage
        self.position_percentage = position_percentage  # 2% instead of 51%!
        self.take_profit_percent = 8.0  # 8% profit target
        self.stop_loss_percent = 3.5    # 3.5% loss limit
        
        # State tracking - Monitor current positions and entry points
        self.position_side = None  # LONG, SHORT, or None
        self.position_size = 0
        self.entry_price = 0
        
        # Order ID tracking - Ensures bot only manages positions it created
        # This prevents interference with manual trades or other trading systems
        self.bot_order_ids = set()  # Track order IDs created by this bot
        self.position_order_id = None  # The order ID that created current position
        
        # Pause/Resume functionality - Allows temporary suspension of trading
        self.paused = False
        self.pause_file = 'bot_pause.flag'
        
        # Database - SQLite connection for storing trades and signals
        self.db = get_database()
        
        # Telegram notifications - Real-time alerts for trading activity
        self.telegram = TelegramNotifier()

        # Unified Signal Aggregator - Combines all signal sources
        self.unified_aggregator = None
        self.signal_collector = None
        self.unified_signals_enabled = UNIFIED_SIGNALS_ENABLED
        if self.unified_signals_enabled:
            try:
                self.unified_aggregator = create_aggregator()
                self.signal_collector = SignalDataCollector()
                self.signal_collector.start_collection()
                logger.info("📊 Unified Signal Aggregator initialized and data collection started")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Unified Signal Aggregator: {e}")
                self.unified_signals_enabled = False

        logger.info(f"🤖 RL-Enhanced Bot initialized for {symbol}")
        logger.info(f"🛡️ SAFETY SETTINGS: {position_percentage}% position size (vs 51% original)")
        logger.info(f"🎯 Risk Management: {self.take_profit_percent}% TP, {self.stop_loss_percent}% SL")
        
        # Check for existing positions on startup
        self.check_existing_positions_on_startup()
        
        # Run enhanced reconciliation on startup
        logger.info("🔄 Running enhanced reconciliation on startup...")
        try:
            self.enhanced_reconcile_with_display()
        except Exception as e:
            logger.error(f"⚠️ Startup reconciliation failed: {e}")
        
        # Send startup notification to Telegram
        unified_status = "ACTIVE" if (self.unified_signals_enabled and self.unified_aggregator) else "DISABLED"
        startup_message = f"""<b>🤖 RL Trading Bot Started</b>

📊 Symbol: {symbol}
🛡️ Position Size: {position_percentage}%
⚡ Leverage: {leverage}x
🎯 TP: {self.take_profit_percent}% | SL: {self.stop_loss_percent}%
🤖 RL Enhancement: {'ACTIVE' if RL_ENHANCEMENT_ENABLED else 'DISABLED'}
📊 Unified Signals: {unified_status}

Signal Sources:
  • Layer 1: Technical Indicators (RSI, MACD, VWAP, EMA)
  • Layer 2: RL Enhancement
  • Chart Analysis (GPT-4 Vision)
  • CrewAI Multi-Agent
  • Market Context & Cross-Asset
  • News Sentiment

✅ Bot is now monitoring signals...
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
        
        try:
            self.telegram.send_message(startup_message)
        except Exception as e:
            logger.error(f"📱 Startup notification error: {e}")
    
    def get_klines(self, interval: str = '5m', limit: int = 200) -> pd.DataFrame:
        """Fetch kline (candlestick) data from Binance
        
        Retrieves OHLCV data for the specified symbol and converts it to
        a pandas DataFrame with proper data types and timestamp formatting.
        
        Args:
            interval: Kline interval (e.g., '1m', '5m', '1h', '1d')
            limit: Number of klines to retrieve (max 1000)
            
        Returns:
            pd.DataFrame: OHLCV data with timestamp, open, high, low, close, volume
        """
        try:
            klines = self.client.futures_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to proper types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching kline data: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators for the trading strategy
        
        Computes EMAs (9, 21, 50, 200), RSI, MACD, and VWAP indicators
        used for signal generation and market analysis.
        
        Args:
            df: DataFrame containing OHLCV data
            
        Returns:
            Dict: Dictionary containing all calculated indicators as pandas Series
        """
        if df.empty or len(df) < 50:
            return {}
        
        indicators = {}
        
        # EMAs
        indicators['ema_9'] = TechnicalIndicators.ema(df['close'], 9)
        indicators['ema_21'] = TechnicalIndicators.ema(df['close'], 21)
        indicators['ema_50'] = TechnicalIndicators.ema(df['close'], 50)
        indicators['ema_200'] = TechnicalIndicators.ema(df['close'], 200)
        
        # RSI
        indicators['rsi'] = TechnicalIndicators.rsi(df['close'])
        
        # MACD
        macd_data = TechnicalIndicators.macd(df['close'])
        indicators.update(macd_data)
        
        # VWAP
        indicators['vwap'] = TechnicalIndicators.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        return indicators
    
    def generate_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """RL-Enhanced signal generation with Unified Signal Aggregation

        Combines multiple signal sources:
        1. Traditional technical analysis (Layer 1)
        2. RL enhancement (Layer 2)
        3. Chart analysis (OpenAI GPT-4 Vision)
        4. CrewAI multi-agent system
        5. Market context & cross-asset analysis
        6. News sentiment analysis

        Args:
            df: DataFrame containing OHLCV market data
            indicators: Dictionary of calculated technical indicators

        Returns:
            Dict: Complete signal data including direction, strength, reasons, and enhancement status
        """

        # Get original signal using traditional logic (Layer 1)
        original_signal_data = self._generate_original_signals(df, indicators)

        # Apply RL enhancement if available (Layer 2)
        rl_signal_data = {'action': 'HOLD', 'confidence': 0.0}
        if RL_ENHANCEMENT_ENABLED:
            try:
                # Prepare indicators for RL
                indicator_dict = {
                    'price': df['close'].iloc[-1],
                    'rsi': indicators['rsi'].iloc[-1],
                    'macd': indicators['macd'].iloc[-1],
                    'macd_histogram': indicators['macd_histogram'].iloc[-1],
                    'vwap': indicators['vwap'].iloc[-1],
                    'ema_9': indicators['ema_9'].iloc[-1],
                    'ema_21': indicators['ema_21'].iloc[-1]
                }

                # Get RL enhancement
                enhanced = rl_generator(original_signal_data, indicator_dict)

                # Store risk level for position sizing
                self._current_risk_level = enhanced.get('risk_level', 'LOW')

                # Convert to format for unified aggregator
                rl_signal_data = {
                    'action': 'BUY' if enhanced['signal'] > 0 else 'SELL' if enhanced['signal'] < 0 else 'HOLD',
                    'confidence': enhanced.get('strength', 0) * 20.0,  # Convert 0-5 to 0-100
                    'reason': enhanced.get('reason', '')
                }

                logger.info(f"💹 Current SUIUSDC Price: ${df['close'].iloc[-1]:.4f}")
                logger.info(f"🤖 RL Enhancement: {rl_signal_data['action']} (confidence: {rl_signal_data['confidence']:.1f}%)")

            except Exception as e:
                logger.error(f"❌ RL Enhancement failed: {e}")

        # Use Unified Signal Aggregator if available
        if self.unified_signals_enabled and self.unified_aggregator:
            try:
                # Convert traditional signal to format for aggregator
                tech_action = 'BUY' if original_signal_data['signal'] > 0 else 'SELL' if original_signal_data['signal'] < 0 else 'HOLD'
                tech_signal = {
                    'action': tech_action,
                    'strength': original_signal_data['strength'],
                    'confidence': min(original_signal_data['strength'] * 20.0, 100.0),
                    'indicators': original_signal_data.get('indicators', {})
                }

                # Get unified signal from aggregator
                current_price = df['close'].iloc[-1]
                unified_result = self.unified_aggregator.aggregate_signals(
                    technical_signal=tech_signal,
                    rl_signal=rl_signal_data,
                    current_price=current_price,
                    symbol=self.symbol
                )

                # Log unified signal summary
                logger.info(self.unified_aggregator.get_signal_summary(unified_result))

                # Convert unified signal back to bot's format
                unified_action = unified_result['signal']
                signal_value = 1 if unified_action == 'BUY' else -1 if unified_action == 'SELL' else 0
                strength_value = int(unified_result['strength'] / 2)  # Convert 0-10 to 0-5

                signal_data = {
                    'signal': signal_value,
                    'strength': strength_value,
                    'reasons': [
                        f"Unified Signal: {unified_action} (strength: {unified_result['strength']:.1f}/10, confidence: {unified_result['confidence']:.1f}%)"
                    ] + original_signal_data.get('reasons', []),
                    'indicators': self._extract_current_indicators(indicators),
                    'rl_enhanced': RL_ENHANCEMENT_ENABLED,
                    'unified_signal': True,
                    'unified_details': unified_result
                }

            except Exception as e:
                logger.error(f"❌ Unified Signal Aggregation failed: {e}")
                # Fallback to RL or traditional signal
                if RL_ENHANCEMENT_ENABLED and rl_signal_data['confidence'] > 0:
                    signal_data = {
                        'signal': enhanced['signal'],
                        'strength': enhanced['strength'],
                        'reasons': [enhanced['reason']] + original_signal_data.get('reasons', []),
                        'indicators': self._extract_current_indicators(indicators),
                        'rl_enhanced': True
                    }
                else:
                    signal_data = original_signal_data

        # Fallback to RL or traditional if unified not available
        elif RL_ENHANCEMENT_ENABLED and rl_signal_data['confidence'] > 0:
            try:
                enhanced = rl_generator(original_signal_data, indicator_dict)
                logger.info(f"   Original: Signal={original_signal_data['signal']}, Strength={original_signal_data['strength']}")
                logger.info(f"   Enhanced: Signal={enhanced['signal']}, Strength={enhanced['strength']}")
                logger.info(f"   Reason: {enhanced['reason']}")

                self._current_risk_level = enhanced.get('risk_level', 'LOW')

                signal_data = {
                    'signal': enhanced['signal'],
                    'strength': enhanced['strength'],
                    'reasons': [enhanced['reason']] + original_signal_data.get('reasons', []),
                    'indicators': self._extract_current_indicators(indicators),
                    'rl_enhanced': True
                }
            except Exception as e:
                logger.error(f"❌ RL Enhancement failed: {e}")
                signal_data = original_signal_data
        else:
            logger.warning("⚠️ Running with traditional signals only")
            signal_data = original_signal_data

        # Store the signal in the database
        signal_id = self.db.store_signal(
            self.symbol,
            df['close'].iloc[-1],
            signal_data
        )
        signal_data['signal_id'] = signal_id

        return signal_data
    
    def _generate_original_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Original signal generation logic using traditional technical analysis
        
        Analyzes multiple technical indicators to generate buy/sell signals:
        - RSI: Overbought (>70) and oversold (<30) conditions
        - MACD: Bullish/bearish crossovers and histogram analysis
        - VWAP: Price position relative to volume-weighted average
        - EMA: Trend analysis using multiple EMA alignments
        
        Args:
            df: DataFrame containing OHLCV market data
            indicators: Dictionary of calculated technical indicators
            
        Returns:
            Dict: Signal data with direction (-1 to 1), strength (0-5), and reasoning
        """
        
        signal = 0
        strength = 0
        reasons = []
        
        if len(df) < 50:
            return {
                'signal': 0,
                'strength': 0,
                'reasons': ['Insufficient data for analysis'],
                'indicators': {}
            }
        
        current_price = df['close'].iloc[-1]
        
        try:
            # RSI Analysis - Relative Strength Index for overbought/oversold conditions
            rsi = indicators['rsi'].iloc[-1]
            if rsi < 30:
                signal += 1
                strength += 2
                reasons.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:
                signal -= 1
                strength += 2
                reasons.append(f"RSI overbought ({rsi:.1f})")
            else:
                reasons.append(f"RSI neutral ({rsi:.1f})")
            
            # MACD Analysis - Moving Average Convergence Divergence for trend momentum
            macd = indicators['macd'].iloc[-1]
            macd_signal = indicators['macd_signal'].iloc[-1]
            macd_histogram = indicators['macd_histogram'].iloc[-1]
            
            if macd > macd_signal and macd_histogram > 0:
                signal += 1
                strength += 1
                reasons.append("MACD bullish crossover")
            elif macd < macd_signal and macd_histogram < 0:
                signal -= 1
                strength += 1
                reasons.append("MACD bearish crossover")
            
            # VWAP Analysis - Volume Weighted Average Price for institutional levels
            vwap = indicators['vwap'].iloc[-1]
            if current_price > vwap * 1.001:  # 0.1% above VWAP
                signal += 1
                reasons.append(f"Price above VWAP (+{((current_price/vwap-1)*100):.2f}%)")
            elif current_price < vwap * 0.999:  # 0.1% below VWAP
                signal -= 1
                reasons.append(f"Price below VWAP ({((current_price/vwap-1)*100):.2f}%)")
            
            # EMA Trend Analysis - Exponential Moving Average alignment for trend direction
            ema_9 = indicators['ema_9'].iloc[-1]
            ema_21 = indicators['ema_21'].iloc[-1]
            ema_50 = indicators['ema_50'].iloc[-1]
            
            if ema_9 > ema_21 > ema_50:
                signal += 1
                strength += 1
                reasons.append("EMA bullish alignment (9>21>50)")
            elif ema_9 < ema_21 < ema_50:
                signal -= 1
                strength += 1
                reasons.append("EMA bearish alignment (9<21<50)")
            
        except Exception as e:
            logger.error(f"Error in signal calculation: {e}")
            return {
                'signal': 0,
                'strength': 0,
                'reasons': ['Error in signal calculation'],
                'indicators': {}
            }
        
        # Normalize signal to ensure it's within valid range (-1 to 1)
        signal = max(-1, min(1, signal))
        
        return {
            'signal': signal,
            'strength': min(strength, 5),
            'reasons': reasons,
            'indicators': self._extract_current_indicators(indicators)
        }
    
    def _extract_current_indicators(self, indicators: Dict) -> Dict:
        """Extract current indicator values for database storage"""
        current_indicators = {}
        for key, series in indicators.items():
            if hasattr(series, 'iloc') and len(series) > 0:
                current_indicators[key] = float(series.iloc[-1])
        return current_indicators
    
    def check_pause_status(self) -> bool:
        """Check if bot is paused by looking for pause flag file
        
        Allows external control of bot trading activity without stopping
        the entire process. When paused, signals are still generated but
        no actual trades are executed.
        
        Returns:
            bool: True if bot is paused, False if active
        """
        if os.path.exists(self.pause_file):
            if not self.paused:
                self.paused = True
                logger.info("⏸️ Bot paused - signals will continue but no trades will be executed")
            return True
        else:
            if self.paused:
                self.paused = False
                logger.info("▶️ Bot resumed - trade execution enabled")
            return False
    
    def execute_trade(self, signal_data: Dict, current_price: float) -> bool:
        """Execute trade with RL-enhanced position sizing
        
        Places market orders based on signal direction with dynamic position sizing.
        Features:
        - RL-based position size adjustment based on risk assessment
        - Account balance verification and position size calculation
        - Order tracking for bot-created positions
        - Database storage of trade details
        - Automatic take profit and stop loss placement
        
        Args:
            signal_data: Dictionary containing signal information and strength
            current_price: Current market price for order execution
            
        Returns:
            bool: True if trade executed successfully, False otherwise
        """
        
        # Check if bot is paused - Respect pause flag for manual control
        if self.check_pause_status():
            logger.info("⏸️ Bot is paused - skipping trade execution (signal still recorded)")
            return False
        
        signal = signal_data['signal']
        
        if signal == 0:
            logger.info("🛑 No trade signal - maintaining current position")
            return False
        
        # RL Risk Management Override - Adjust position size based on RL risk assessment
        if RL_ENHANCEMENT_ENABLED:
            # Much smaller position sizes based on RL recommendations
            original_percentage = self.position_percentage
            if hasattr(self, '_current_risk_level'):
                self.position_percentage = rl_enhancer.should_use_smaller_position({'risk_level': self._current_risk_level})
                logger.info(f"🛡️ RL Position Size: {self.position_percentage * 100}% (risk: {self._current_risk_level})")
        
        try:
            # Get account info - Fetch current balance for position size calculation
            account_info = self.client.futures_account()
            available_balance = 0.0
            for asset in account_info['assets']:
                if asset['asset'] == self.symbol.replace('SUI', ''):
                    available_balance = float(asset['walletBalance'])
                    break
            
            # Calculate position size - Conservative sizing for risk management
            position_value = available_balance * self.position_percentage
            position_size = (position_value * self.leverage) / current_price
            
            # Round to appropriate decimal places
            position_size = round(position_size, 1)
            
            if position_size < 0.1:  # Minimum position size
                logger.warning(f"⚠️ Position size too small: {position_size}")
                return False
            
            # Determine trade direction
            side = 'BUY' if signal > 0 else 'SELL'
            
            logger.info(f"🎯 RL-Enhanced Trade Execution:")
            logger.info(f"   Direction: {side}")
            logger.info(f"   Size: {position_size} {self.symbol.replace('USDC', '')}")
            logger.info(f"   Value: ${position_value:.2f} ({self.position_percentage}% of ${available_balance:.2f})")
            logger.info(f"   Leverage: {self.leverage}x")
            
            # Place order - Execute market order on Binance
            order = self.client.futures_create_order(
                symbol=self.symbol,
                side=side,
                type='MARKET',
                quantity=position_size
            )
            
            # Track the order ID for this bot - Ensure we only manage our own positions
            order_id = order.get('orderId')
            if order_id:
                self.bot_order_ids.add(order_id)
                self.position_order_id = order_id
                logger.info(f"🔢 Tracking order ID: {order_id}")
            
            # Store in database - Record trade details for tracking
            trade_id = self.db.store_trade(
                signal_id=signal_data['signal_id'],
                symbol=self.symbol,
                side=side,
                quantity=position_size,
                entry_price=current_price,
                leverage=self.leverage,
                position_percentage=self.position_percentage,
                order_id=order_id
            )
            
            logger.info(f"✅ RL-Enhanced trade executed: Order ID {order_id}, DB Trade ID {trade_id}")
            
            # Update internal state - Keep bot's position tracking current
            self.position_side = 'LONG' if side == 'BUY' else 'SHORT'
            self.position_size = position_size
            self.entry_price = current_price

            # Set TP/SL - Automatically place risk management orders
            self.set_tp_sl(side, current_price, position_size)
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"❌ Trade execution failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in trade execution: {e}")
            return False

    def get_tp_sl_prices(self):
        """Get current Take Profit and Stop Loss prices from open orders"""
        try:
            open_orders = self.client.futures_get_open_orders(symbol=self.symbol)
            tp_price = None
            sl_price = None
            
            for order in open_orders:
                if order['type'] == 'TAKE_PROFIT_MARKET':
                    tp_price = float(order['stopPrice'])
                elif order['type'] == 'STOP_MARKET':
                    sl_price = float(order['stopPrice'])
            
            return tp_price, sl_price
            
        except BinanceAPIException as e:
            logger.error(f"Error getting TP/SL prices: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error getting TP/SL prices: {e}")
            return None, None

    def set_tp_sl(self, side: str, entry_price: float, quantity: float):
        """Set Take Profit and Stop Loss orders
        
        Creates conditional orders to automatically close positions:
        - Take Profit: 15% profit target
        - Stop Loss: 5% maximum loss limit
        
        Args:
            side: Original trade direction ('BUY' or 'SELL')
            entry_price: Price at which position was entered
            quantity: Position size for the orders
        """
        try:
            if side == 'BUY':
                tp_price = round(entry_price * 1.15, 4)  # 15% profit (85% -> 115%)
                sl_price = round(entry_price * 0.95, 4)  # 5% loss (95%)
                tp_side = 'SELL'
                sl_side = 'SELL'
            else: # SELL
                tp_price = round(entry_price * 0.85, 4)  # 15% profit (85%)
                sl_price = round(entry_price * 1.05, 4)  # 5% loss (105%)
                tp_side = 'BUY'
                sl_side = 'BUY'

            # Take Profit Order
            self.client.futures_create_order(
                symbol=self.symbol,
                side=tp_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp_price,
                closePosition=True
            )
            logger.info(f"🟢 Take Profit set at ${tp_price:.4f}")

            # Stop Loss Order
            self.client.futures_create_order(
                symbol=self.symbol,
                side=sl_side,
                type='STOP_MARKET',
                stopPrice=sl_price,
                closePosition=True
            )
            logger.info(f"🔴 Stop Loss set at ${sl_price:.4f}")

        except BinanceAPIException as e:
            logger.error(f"❌ Error setting TP/SL: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error setting TP/SL: {e}")
    
    def can_close_position(self) -> bool:
        """Check if the bot can close the current position (only if it was opened by this bot)"""
        if not self.position_order_id:
            logger.info("🚫 No position order ID tracked - assuming position not opened by bot")
            return False
        
        if self.position_order_id not in self.bot_order_ids:
            logger.info(f"🚫 Position order ID {self.position_order_id} not in bot's tracked orders")
            return False
        
        return True
    
    def clear_position_tracking(self):
        """Clear position tracking when position is closed"""
        if self.position_order_id:
            logger.info(f"🗑️ Clearing tracking for order ID: {self.position_order_id}")
            self.position_order_id = None
        
        # Reset internal state
        self.position_side = None
        self.position_size = 0
        self.entry_price = 0
    
    def check_existing_positions_on_startup(self):
        """Check for existing positions on startup and warn if they exist"""
        try:
            positions = self.client.futures_position_information(symbol=self.symbol)
            
            for position in positions:
                if position['symbol'] == self.symbol:
                    position_amt = float(position['positionAmt'])
                    
                    if abs(position_amt) > 0.001:  # Has existing position
                        entry_price = float(position['entryPrice'])
                        mark_price = float(position['markPrice'])
                        unrealized_pnl = float(position['unRealizedProfit'])
                        side = 'LONG' if position_amt > 0 else 'SHORT'
                        
                        logger.warning(f"⚠️ EXISTING POSITION DETECTED ON STARTUP:")
                        logger.warning(f"   {side} {abs(position_amt)} @ ${entry_price:.4f}")
                        logger.warning(f"   Current: ${mark_price:.4f} | PnL: ${unrealized_pnl:.2f}")
                        logger.warning(f"   🚫 Bot will NOT close this position - it was not opened by this bot")
                        logger.warning(f"   💡 If you want the bot to manage this position, please close it manually first")
                        break
                        
        except Exception as e:
            logger.error(f"❌ Error checking existing positions on startup: {e}")
    
    def get_position_info(self):
        """Get current position information with TP/SL prices"""
        try:
            positions = self.client.futures_position_information(symbol=self.symbol)
            
            for position in positions:
                if position['symbol'] == self.symbol:
                    position_amt = float(position['positionAmt'])
                    
                    if abs(position_amt) > 0.001:  # Has position
                        entry_price = float(position['entryPrice'])
                        mark_price = float(position['markPrice'])
                        unrealized_pnl = float(position['unRealizedProfit'])
                        
                        # Calculate percentage
                        if entry_price > 0:
                            percentage = ((mark_price - entry_price) / entry_price) * 100 * self.leverage
                            if position_amt < 0:  # Short position
                                percentage = -percentage
                        else:
                            percentage = 0
                        
                        # Get TP/SL prices from open orders
                        tp_price, sl_price = self.get_tp_sl_prices()
                        
                        return {
                            'symbol': self.symbol,
                            'side': 'LONG' if position_amt > 0 else 'SHORT',
                            'size': abs(position_amt),
                            'entry_price': entry_price,
                            'mark_price': mark_price,
                            'unrealized_pnl': unrealized_pnl,
                            'percentage': percentage,
                            'liquidation_price': float(position.get('liquidationPrice', 0)),
                            'take_profit_price': tp_price,
                            'stop_loss_price': sl_price
                        }
            
            return {'symbol': self.symbol, 'side': None, 'size': 0}
            
        except BinanceAPIException as e:
            logger.error(f"Error getting position info: {e}")
            return {'symbol': self.symbol, 'side': None, 'size': 0}
    
    def reconcile_positions(self):
        """Reconcile database positions with actual Binance positions
        
        Ensures database records match actual exchange positions by:
        - Comparing live Binance positions with database open trades
        - Detecting externally closed positions
        - Updating database records to reflect actual state
        - Clearing position tracking for externally managed trades
        
        This prevents discrepancies between bot's internal state and reality.
        """
        try:
            # Get live positions from Binance
            positions = self.client.futures_position_information(symbol=self.symbol)
            live_position_amt = 0
            
            for pos in positions:
                if pos['symbol'] == self.symbol:
                    live_position_amt = float(pos['positionAmt'])
                    break
            
            # Get open trades from database
            open_trades = self.db.get_open_trades(self.symbol)
            db_position_amt = 0
            
            for trade in open_trades:
                if trade['side'] == 'BUY':
                    db_position_amt += trade['quantity']
                else:  # SELL
                    db_position_amt -= trade['quantity']
            
            # Check if positions match
            if abs(live_position_amt) < 0.001 and len(open_trades) > 0:
                # Position closed on Binance but still open in database
                logger.info(f"🔄 Reconciling: Position closed on Binance but {len(open_trades)} open trades in database")
                
                # Get current price
                ticker = self.client.get_symbol_ticker(symbol=self.symbol)
                current_price = float(ticker['price'])
                
                # Close all open trades in database
                self.update_open_trades_on_close(current_price)
                
                # Clear position tracking since position was closed externally
                self.clear_position_tracking()
                
                logger.info(f"✅ Reconciled {len(open_trades)} trades - marked as closed with current price ${current_price:.4f}")
                
            elif abs(abs(live_position_amt) - abs(db_position_amt)) > 0.001:
                logger.warning(f"⚠️ Position mismatch: Binance={live_position_amt}, Database={db_position_amt}")
                
        except Exception as e:
            logger.error(f"❌ Error reconciling positions: {e}")
    
    def update_open_trades_on_close(self, current_price):
        """Update all open trades when position is closed externally"""
        try:
            open_trades = self.db.get_open_trades(self.symbol)
            
            for trade in open_trades:
                # Calculate PnL
                if trade['side'] == 'BUY':
                    pnl = (current_price - trade['entry_price']) * trade['quantity']
                else:  # SELL
                    pnl = (trade['entry_price'] - current_price) * trade['quantity']
                
                # Calculate PnL percentage
                pnl_percentage = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
                
                # Update trade to closed
                self.db.update_trade_exit(
                    trade_id=trade['id'],
                    exit_price=current_price,
                    pnl=pnl,
                    pnl_percentage=pnl_percentage,
                    status='CLOSED'
                )
                
                logger.info(f"📝 Trade {trade['id']}: {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.4f} → ${current_price:.4f}, PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
                
        except Exception as e:
            logger.error(f"❌ Error updating open trades on close: {e}")
    
    def close_position_on_hold_signal(self, position_info: Dict, current_price: float):
        """Close current position when HOLD signal is detected - only close if PnL is negative and bot opened the position"""
        try:
            if not position_info['side']:
                return  # No position to close
            
            # Check if bot can close this position (only if it was opened by bot)
            if not self.can_close_position():
                logger.info(f"🚫 HOLD signal detected but cannot close {position_info['side']} position - not opened by this bot")
                return False
            
            # Check PnL
            unrealized_pnl = position_info.get('unrealized_pnl', 0)
            
            if unrealized_pnl > 0:
                logger.info(f"🛑 HOLD signal detected - keeping {position_info['side']} position open (positive PnL: ${unrealized_pnl:.2f})")
                return False
            
            logger.info(f"🛑 HOLD signal detected - closing {position_info['side']} position (negative PnL: ${unrealized_pnl:.2f})")
            
            # Cancel all existing orders (TP/SL)
            try:
                self.client.futures_cancel_all_open_orders(symbol=self.symbol)
                logger.info("❌ Cancelled all existing orders (TP/SL)")
            except BinanceAPIException as e:
                logger.warning(f"⚠️ Could not cancel orders: {e}")
            
            # Determine the closing side (opposite of current position)
            close_side = 'SELL' if position_info['side'] == 'LONG' else 'BUY'
            
            # Execute market order to close position
            close_order = self.client.futures_create_order(
                symbol=self.symbol,
                side=close_side,
                type='MARKET',
                quantity=position_info['size']
            )
            
            # Update database trades
            self.update_open_trades_on_close(current_price)
            
            logger.info(f"✅ Position closed due to HOLD signal with negative PnL: Order ID {close_order.get('orderId')}")
            logger.info(f"💰 Final PnL: ${unrealized_pnl:.2f} ({position_info.get('percentage', 0):.2f}%)")
            
            # Clear position tracking
            self.clear_position_tracking()
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"❌ Failed to close position on HOLD signal: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error closing position on HOLD: {e}")
            return False
    
    def close_position_on_opposite_signal(self, position_info: Dict, signal: int, current_price: float):
        """Close position when signal flips to opposite direction - only close if PnL is negative and bot opened the position"""
        try:
            if not position_info['side']:
                return False  # No position to close
            
            # Determine if signal is opposite to current position
            is_opposite_signal = False
            if position_info['side'] == 'LONG' and signal < 0:  # LONG position with SELL signal
                is_opposite_signal = True
            elif position_info['side'] == 'SHORT' and signal > 0:  # SHORT position with BUY signal
                is_opposite_signal = True
            
            if not is_opposite_signal:
                return False  # Signal is not opposite
            
            # Check if bot can close this position (only if it was opened by bot)
            if not self.can_close_position():
                signal_name = "SELL" if signal < 0 else "BUY"
                logger.info(f"🚫 {signal_name} signal detected but cannot close {position_info['side']} position - not opened by this bot")
                return False
            
            # Check PnL
            unrealized_pnl = position_info.get('unrealized_pnl', 0)
            signal_name = "SELL" if signal < 0 else "BUY"
            
            if unrealized_pnl > 0:
                logger.info(f"🔄 {signal_name} signal detected with open {position_info['side']} position - keeping position open (positive PnL: ${unrealized_pnl:.2f})")
                return False
            
            logger.info(f"🔄 {signal_name} signal detected with open {position_info['side']} position - closing due to negative PnL: ${unrealized_pnl:.2f}")
            
            # Cancel all existing orders (TP/SL)
            try:
                self.client.futures_cancel_all_open_orders(symbol=self.symbol)
                logger.info("❌ Cancelled all existing orders (TP/SL)")
            except BinanceAPIException as e:
                logger.warning(f"⚠️ Could not cancel orders: {e}")
            
            # Determine the closing side (opposite of current position)
            close_side = 'SELL' if position_info['side'] == 'LONG' else 'BUY'
            
            # Execute market order to close position
            close_order = self.client.futures_create_order(
                symbol=self.symbol,
                side=close_side,
                type='MARKET',
                quantity=position_info['size']
            )
            
            # Update database trades
            self.update_open_trades_on_close(current_price)
            
            logger.info(f"✅ Position closed due to opposite {signal_name} signal with negative PnL: Order ID {close_order.get('orderId')}")
            logger.info(f"💰 Final PnL: ${unrealized_pnl:.2f} ({position_info.get('percentage', 0):.2f}%)")
            
            # Clear position tracking
            self.clear_position_tracking()
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"❌ Failed to close position on opposite signal: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error closing position on opposite signal: {e}")
            return False
    
    def run(self, interval: int = 300):
        """Main bot loop with RL enhancement
        
        Core trading loop that:
        1. Fetches market data and calculates indicators
        2. Generates RL-enhanced trading signals
        3. Manages existing positions and risk
        4. Executes new trades based on signals
        5. Sends Telegram notifications
        6. Handles pause/resume functionality
        
        The loop runs continuously with configurable intervals.
        
        Args:
            interval: Time between iterations in seconds (default: 300 = 5 minutes)
        """
        logger.info(f"🚀 Starting RL-Enhanced Binance Futures Bot for {self.symbol}")
        logger.info(f"🛡️ SAFETY MODE: {self.position_percentage}% max position (vs 51% original)")
        logger.info(f"🤖 RL Enhancement: {'ACTIVE' if RL_ENHANCEMENT_ENABLED else 'DISABLED'}")
        logger.info(f"🎯 Risk Management: TP {self.take_profit_percent}% | SL {self.stop_loss_percent}%")
        logger.info(f"⏸️ Pause Control: Create '{self.pause_file}' file to pause trade execution")
        
        while True:
            try:
                # Check pause status
                paused = self.check_pause_status()
                if paused:
                    logger.info("⏸️ Bot paused - generating signals only, no trade execution")
                
                # Reconcile positions with Binance (if available)
                if hasattr(self, 'reconcile_positions'):
                    self.reconcile_positions()
                
                # Get position info
                position_info = self.get_position_info()
                
                # Fetch market data
                df = self.get_klines()
                if df.empty:
                    logger.error("❌ No market data received")
                    time.sleep(interval)
                    continue
                
                # Calculate indicators
                indicators = self.calculate_indicators(df)
                if not indicators:
                    logger.warning("⚠️ Could not calculate indicators")
                    time.sleep(interval)
                    continue
                
                # Generate RL-enhanced signals
                signal_data = self.generate_signals(df, indicators)
                
                # Current market info
                current_price = df['close'].iloc[-1]
                rsi = indicators['rsi'].iloc[-1] if 'rsi' in indicators else 0
                vwap = indicators['vwap'].iloc[-1] if 'vwap' in indicators else current_price
                
                # Send Telegram notification for significant signals
                if signal_data.get('signal', 0) != 0 and signal_data.get('strength', 0) > 0:
                    try:
                        self.telegram.send_signal_notification(signal_data, current_price, position_info)
                    except Exception as e:
                        logger.error(f"📱 Telegram notification error: {e}")
                
                # Position display
                if position_info['side']:
                    pnl_emoji = "🟢" if position_info['unrealized_pnl'] > 0 else "🔴"
                    can_close_emoji = "✅" if self.can_close_position() else "🚫"
                    logger.info(f"📍 Position: {position_info['side']} {position_info['size']:.1f} {can_close_emoji}")
                    logger.info(f"💰 PnL: {pnl_emoji} ${position_info['unrealized_pnl']:.2f} ({position_info['percentage']:.2f}%)")
                    
                    # Show order tracking status
                    if self.position_order_id:
                        logger.info(f"🔢 Bot Order ID: {self.position_order_id} (Bot can manage this position)")
                    else:
                        logger.info(f"🚫 No bot order ID tracked (Bot will NOT close this position)")
                    
                    # Display TP/SL prices if available
                    if position_info.get('take_profit_price') or position_info.get('stop_loss_price'):
                        tp_text = f"${position_info['take_profit_price']:.4f}" if position_info.get('take_profit_price') else "Not set"
                        sl_text = f"${position_info['stop_loss_price']:.4f}" if position_info.get('stop_loss_price') else "Not set"
                        logger.info(f"🎯 TP: {tp_text} | SL: {sl_text}")
                else:
                    logger.info("📍 Position: No open position")
                
                # Market status
                logger.info(f"💹 {self.symbol}: ${current_price:.4f} | RSI: {rsi:.1f} | VWAP: ${vwap:.4f}")
                
                # Signal info
                signal_emoji = "🟢" if signal_data['signal'] > 0 else "🔴" if signal_data['signal'] < 0 else "⚪"
                signal_name = "BUY" if signal_data['signal'] > 0 else "SELL" if signal_data['signal'] < 0 else "HOLD"
                pause_status = " (PAUSED)" if paused else ""
                logger.info(f"🎯 Signal: {signal_emoji} {signal_name} (Strength: {signal_data['strength']}){pause_status}")
                
                if signal_data.get('rl_enhanced'):
                    logger.info("🤖 RL Enhancement: ACTIVE")
                
                # Check for RL-enhanced exit conditions
                if RL_ENHANCEMENT_ENABLED and position_info['side']:
                    # Check if bot can close this position (only if it was opened by bot)
                    if self.can_close_position():
                        position_data = {
                            'entry_price': position_info['entry_price'],
                            'side': position_info['side']
                        }
                        exit_decision = rl_enhancer.check_exit_conditions(position_data, current_price)
                        
                        if exit_decision['should_exit']:
                            logger.info(f"🚪 RL Exit Signal: {exit_decision['reason']}")
                            self.client.futures_cancel_all_open_orders(symbol=self.symbol)
                            close_order = self.client.futures_create_order(
                                symbol=self.symbol,
                                side='BUY' if position_info['side'] == 'SHORT' else 'SELL',
                                type='MARKET',
                                quantity=position_info['size']
                            )
                            # Update database trades
                            self.update_open_trades_on_close(current_price)
                            # Clear position tracking
                            self.clear_position_tracking()
                            logger.info(f"✅ Position closed based on RL exit signal: Order ID {close_order.get('orderId')}")
                    else:
                        logger.info("🚫 RL exit signal detected but cannot close position - not opened by this bot")
                
                # DISABLED: Signal-based position closures
                # These functions were bypassing TP/SL risk management by closing positions
                # prematurely when signals changed. Positions should ONLY be closed by:
                # 1. Take Profit orders reaching 15% target
                # 2. Stop Loss orders hitting 5% limit
                # 3. Manual intervention
                # 4. RL-based exit signals (which use more sophisticated criteria)

                # Signal changes are informational only - they do NOT justify closing positions
                # that have properly set TP/SL orders. Premature signal-based closures lead to:
                # - Missing profit targets
                # - Taking losses before SL is hit
                # - Excessive trading frequency
                # - Reduced overall profitability

                # COMMENTED OUT: Check for HOLD signal to close existing positions
                # if signal_data['signal'] == 0 and position_info['side']:
                #     logger.info(f"🛑 HOLD signal detected with open {position_info['side']} position")
                #     self.close_position_on_hold_signal(position_info, current_price)

                # COMMENTED OUT: Check for opposite signal to close existing positions with negative PnL
                # elif signal_data['signal'] != 0 and position_info['side']:
                #     position_closed = self.close_position_on_opposite_signal(position_info, signal_data['signal'], current_price)
                #
                #     # If position was closed, we can now execute a new trade
                #     if position_closed and signal_data['strength'] > 0:
                #         logger.info(f"📈 Executing new trade after closing opposite position based on {signal_name} signal...")
                #         self.execute_trade(signal_data, current_price)
                #     elif not position_closed:
                #         logger.info(f"✅ {signal_name} signal detected but keeping {position_info['side']} position (positive PnL). No new trade will be executed.")

                # Log signal changes for informational purposes without closing positions
                if signal_data['signal'] == 0 and position_info['side']:
                    logger.info(f"ℹ️ HOLD signal detected with open {position_info['side']} position - keeping position open, respecting TP/SL orders")
                elif signal_data['signal'] != 0 and position_info['side']:
                    signal_name = "BUY" if signal_data['signal'] > 0 else "SELL"
                    if (position_info['side'] == 'LONG' and signal_data['signal'] < 0) or \
                       (position_info['side'] == 'SHORT' and signal_data['signal'] > 0):
                        logger.info(f"ℹ️ Opposite {signal_name} signal detected with open {position_info['side']} position - keeping position open, respecting TP/SL orders")
                
                # Execute trades based on signals (no current position)
                elif signal_data['signal'] != 0 and signal_data['strength'] > 0:
                    if not position_info['side']:  # No current position
                        logger.info(f"📈 Executing trade based on {signal_name} signal...")
                        self.execute_trade(signal_data, current_price)
                
                # Log reasons
                for reason in signal_data.get('reasons', []):
                    logger.info(f"   • {reason}")
                
                logger.info(f"⏰ Next update in {interval//60} minutes...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("👋 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def detect_individual_manual_closures(self):
        """Detect and record individual manual position closures"""
        try:
            logger.info("🔍 Analyzing individual manual position closures...")
            
            # Get all trades excluding previous manual closures
            all_trades = self.db.get_all_trades(self.symbol, exclude_manual=True)
            
            if not all_trades:
                logger.info("📊 No trades found for analysis")
                return []
            
            # Track position and detect manual closures
            position = 0
            manual_closures = []
            large_position_start = None
            
            for trade in all_trades:
                old_position = position
                
                if trade['side'] == 'BUY':
                    position += trade['quantity']
                    # Track when we first go positive (indicating start of large untracked position)
                    if old_position <= 0 and position > 0:
                        large_position_start = {
                            'timestamp': trade['timestamp'],
                            'entry_price': trade['entry_price']
                        }
                        logger.info(f"📈 Large position start detected: {position:.1f} at {trade['timestamp']}")
                else:  # SELL
                    position -= trade['quantity']
                    
                    # Detect manual closure events
                    if old_position > 0 and position <= 0:
                        # Full closure detected
                        closure_amount = old_position
                        exit_price = trade.get('exit_price', trade['entry_price'])
                        entry_price = large_position_start['entry_price'] if large_position_start else trade['entry_price']
                        
                        manual_closures.append({
                            'timestamp': trade['timestamp'],
                            'type': 'FULL_CLOSE',
                            'amount': closure_amount,
                            'exit_price': exit_price,
                            'entry_price': entry_price
                        })
                        logger.info(f"🔴 FULL closure detected: {closure_amount:.1f} at {trade['timestamp']}")
                        
                    elif old_position > 0 and position < old_position:
                        # Partial closure
                        closure_amount = old_position - position
                        if closure_amount > 100:  # Only record significant partial closures
                            exit_price = trade.get('exit_price', trade['entry_price'])
                            entry_price = large_position_start['entry_price'] if large_position_start else trade['entry_price']
                            
                            manual_closures.append({
                                'timestamp': trade['timestamp'],
                                'type': 'PARTIAL_CLOSE',
                                'amount': closure_amount,
                                'exit_price': exit_price,
                                'entry_price': entry_price
                            })
                            logger.info(f"🟡 PARTIAL closure detected: {closure_amount:.1f} at {trade['timestamp']}")
            
            # Handle final untracked position if exists
            try:
                current_position = self.get_position_info()
                current_size = current_position.get('size', 0) if current_position.get('side') else 0
            except:
                current_size = 0
            
            if position < 0 and current_size == 0:
                # There's still an untracked closure
                final_closure_amount = abs(position)
                
                # Get current market price
                try:
                    ticker = self.client.get_symbol_ticker(symbol=self.symbol)
                    current_price = float(ticker['price'])
                except:
                    current_price = 3.42  # Fallback
                
                entry_price = large_position_start['entry_price'] if large_position_start else current_price
                
                manual_closures.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'FINAL_MANUAL_CLOSE',
                    'amount': final_closure_amount,
                    'exit_price': current_price,
                    'entry_price': entry_price
                })
                logger.info(f"🔴 FINAL manual closure detected: {final_closure_amount:.1f}")
            
            # Record closures in database
            recorded_count = 0
            for closure in manual_closures:
                if self.db.record_manual_closure(closure, self.symbol):
                    recorded_count += 1
            
            logger.info(f"🎯 Recorded {recorded_count} individual manual closures")
            return manual_closures
            
        except Exception as e:
            logger.error(f"❌ Error detecting individual closures: {e}")
            return []

    def show_recent_trades(self, limit=10):
        """Display recent trades with proper price formatting"""
        try:
            logger.info(f"📊 Displaying last {limit} trades:")
            
            # Get recent trades from database
            recent_trades = self.db.get_recent_trades(self.symbol, limit)
            
            if not recent_trades:
                logger.info("📭 No recent trades found")
                return
            
            logger.info(f"📋 Recent {len(recent_trades)} trades:")
            for trade in recent_trades:
                # Show exit_price for SELL trades, entry_price for BUY trades
                if trade['side'] == 'SELL' and trade.get('exit_price'):
                    price = trade['exit_price']
                else:
                    price = trade['entry_price']
                
                pnl_str = f"PnL: ${trade['pnl']:.2f}" if trade.get('pnl') else "PnL: N/A"
                logger.info(f"  {trade['timestamp']} | {trade['side']} {trade['quantity']:.1f} @ ${price:.4f} | {pnl_str}")
            
            # Show total trades count
            total_count = self.db.get_total_trades_count(self.symbol)
            logger.info(f"📊 Total trades in database: {total_count}")
            
        except Exception as e:
            logger.error(f"❌ Error showing recent trades: {e}")

    def enhanced_reconcile_with_display(self):
        """Enhanced reconciliation with manual closure detection and trade display"""
        try:
            logger.info("🔄 Starting enhanced position reconciliation...")
            
            # First detect and record individual manual closures
            manual_closures = self.detect_individual_manual_closures()
            
            # Run standard position reconciliation
            self.reconcile_positions()
            
            # Display recent trades
            self.show_recent_trades(limit=15)
            
            # Send summary notification if Telegram is available
            if hasattr(self, 'send_telegram_message') and manual_closures:
                message = f"🔄 Reconciliation Complete\n"
                message += f"Manual closures detected: {len(manual_closures)}\n"
                if manual_closures:
                    total_amount = sum(c['amount'] for c in manual_closures)
                    message += f"Total amount: {total_amount:.1f} {self.symbol}\n"
                self.send_telegram_message(message)
            
            logger.info("✅ Enhanced reconciliation completed!")
            
        except Exception as e:
            logger.error(f"❌ Enhanced reconciliation failed: {e}")

def main():
    """Start the RL-Enhanced Trading Bot
    
    Entry point for running the bot with default parameters.
    Creates bot instance with conservative settings and starts the main loop.
    """
    try:
        logger.info("🤖 Initializing RL-Enhanced Trading Bot...")
        
        # Create bot with much safer defaults
        bot = RLEnhancedBinanceFuturesBot(
            symbol='SUIUSDC',
            leverage=50,
            position_percentage=2.0  # 2% instead of 51%!
        )
        
        # Run the bot
        bot.run(interval=25)  # 25 seconds
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

def show_status():
    """Show current bot status and position info"""
    try:
        # Check if bot is running
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        is_running = 'rl_bot_ready.py' in result.stdout
        
        print("🤖 RL-Enhanced Trading Bot Status")
        print("=" * 40)
        print(f"Status: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}")
        
        if is_running:
            # Get process info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'rl_bot_ready.py' in line and 'grep' not in line:
                    parts = line.split()
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    print(f"PID: {pid} | CPU: {cpu}% | Memory: {mem}%")
                    break
        
        # Check database connection
        try:
            from database import get_database
            db = get_database()
            print(f"Database: 🟢 CONNECTED")
            
            # Get position info
            open_trades = db.get_open_trades('SUIUSDC')
            print(f"Open Positions: {len(open_trades)}")
            
            for trade in open_trades:
                # Get current price for PnL calculation
                load_dotenv()
                client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'))
                ticker = client.get_symbol_ticker(symbol='SUIUSDC')
                current_price = float(ticker['price'])
                
                if trade['side'] == 'SELL':
                    pnl = (trade['entry_price'] - current_price) * trade['quantity']
                    pnl_pct = ((trade['entry_price'] - current_price) / trade['entry_price']) * 100
                else:
                    pnl = (current_price - trade['entry_price']) * trade['quantity']
                    pnl_pct = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
                
                # Get TP/SL prices from open orders
                try:
                    open_orders = client.futures_get_open_orders(symbol='SUIUSDC')
                    tp_price = None
                    sl_price = None
                    
                    for order in open_orders:
                        if order['type'] == 'TAKE_PROFIT_MARKET':
                            tp_price = float(order['stopPrice'])
                        elif order['type'] == 'STOP_MARKET':
                            sl_price = float(order['stopPrice'])
                except:
                    tp_price = None
                    sl_price = None
                
                color = "🟢" if pnl > 0 else "🔴"
                print(f"  {color} {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.4f}")
                print(f"    Current: ${current_price:.4f} | PnL: ${pnl:.2f} ({pnl_pct:.2f}%)")
                
                if tp_price or sl_price:
                    tp_text = f"${tp_price:.4f}" if tp_price else "Not set"
                    sl_text = f"${sl_price:.4f}" if sl_price else "Not set"
                    print(f"    🎯 TP: {tp_text} | SL: {sl_text}")
                
        except Exception as e:
            print(f"Database: 🔴 ERROR - {e}")
        
        # Check RL system
        try:
            if RL_ENHANCEMENT_ENABLED:
                print(f"RL System: 🟢 ACTIVE")
                if os.path.exists('rl_trading_model.pkl'):
                    print(f"RL Model: 🟢 LOADED")
                else:
                    print(f"RL Model: 🔴 MISSING")
            else:
                print(f"RL System: 🔴 DISABLED")
        except:
            print(f"RL System: 🔴 ERROR")
        
        # Log file info
        if os.path.exists('trading_bot.log'):
            size = os.path.getsize('trading_bot.log')
            print(f"Log File: 🟢 {size} bytes")
        else:
            print(f"Log File: 🔴 NOT FOUND")
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")

def show_logs(lines=20, follow=False):
    """Show recent log entries"""
    try:
        if not os.path.exists('trading_bot.log'):
            print("❌ Log file not found")
            return
            
        if follow:
            print("📜 Following logs (Ctrl+C to stop)...")
            import subprocess
            subprocess.run(['tail', '-f', 'trading_bot.log'])
        else:
            print(f"📜 Last {lines} log entries:")
            print("=" * 50)
            import subprocess
            result = subprocess.run(['tail', f'-{lines}', 'trading_bot.log'], 
                                  capture_output=True, text=True)
            print(result.stdout)
            
    except KeyboardInterrupt:
        print("\n👋 Log following stopped")
    except Exception as e:
        print(f"❌ Log display failed: {e}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='RL-Enhanced Trading Bot')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command (default)
    run_parser = subparsers.add_parser('run', help='Start the trading bot')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show bot status')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show log entries')
    logs_parser.add_argument('-n', '--lines', type=int, default=20, 
                           help='Number of log lines to show (default: 20)')
    logs_parser.add_argument('-f', '--follow', action='store_true', 
                           help='Follow log output in real-time')
    
    # Reconcile command
    reconcile_parser = subparsers.add_parser('reconcile', help='Run enhanced reconciliation with recent trades display')
    
    return parser.parse_args()

def run_reconcile():
    """Run enhanced reconciliation standalone"""
    try:
        logger.info("🔄 Starting standalone enhanced reconciliation...")
        
        # Initialize bot for reconciliation only
        bot = RLEnhancedBinanceFuturesBot(
            symbol='SUIUSDC',
            leverage=50,
            position_percentage=2.0
        )
        
        # Run enhanced reconciliation
        bot.enhanced_reconcile_with_display()
        
        logger.info("✅ Standalone reconciliation completed!")
        
    except Exception as e:
        logger.error(f"❌ Standalone reconciliation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.command == 'status':
        show_status()
    elif args.command == 'logs':
        show_logs(args.lines, args.follow)
    elif args.command == 'reconcile':
        run_reconcile()
    else:
        # Default to running the bot
        main()