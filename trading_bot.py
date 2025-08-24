#!/usr/bin/env python3
"""
Binance Futures Trading Bot
Multi-Indicator Strategy: MACD, VWAP, EMAs (9,21,50,200), RSI

Requirements:
pip install python-binance pandas numpy ta-lib python-dotenv

Create a .env file with:
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
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
warnings.filterwarnings('ignore')

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

class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        cumulative_volume = volume.cumsum()
        cumulative_pv = (typical_price * volume).cumsum()
        return cumulative_pv / cumulative_volume

class BinanceFuturesBot:
    """Binance Futures Trading Bot with Multi-Indicator Strategy"""
    
    def __init__(self, symbol: str = 'SUIUSDC', leverage: int = 50, risk_percentage: float = 1.0, position_percentage: float = 51.0):
        """
        Initialize the trading bot
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage multiplier  
            risk_percentage: Risk percentage for stop loss calculation
            position_percentage: Percentage of available balance to use per trade (like screenshot slider)
        """
        self.symbol = symbol
        self.leverage = leverage
        self.risk_percentage = risk_percentage  # For risk management
        self.position_percentage = position_percentage  # For position sizing (like screenshot slider)
        
        # Initialize Binance client
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            raise ValueError("Please set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env file")
        
        self.client = Client(api_key, secret_key, testnet=False)  # Set testnet=True for testing
        
        # Initialize variables
        self.position_size = 0
        self.position_side = None
        self.indicators = TechnicalIndicators()
        
        # Initialize database
        self.db = get_database()
        logger.info("Database initialized for signal and trade tracking")
        
        # Set margin type to CROSS and leverage
        try:
            # Set margin type to CROSS (like in screenshot)
            self.client.futures_change_margin_type(symbol=symbol, marginType='CROSSED')
            logger.info(f"Set margin type to CROSS for {symbol}")
            
            # Set leverage
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info(f"Set leverage to {leverage}x CROSS for {symbol}")
        except BinanceAPIException as e:
            # Margin type might already be set, continue with leverage
            try:
                self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
                logger.info(f"Set leverage to {leverage}x for {symbol}")
            except BinanceAPIException as e2:
                logger.error(f"Error setting leverage: {e2}")
        
    def get_klines(self, interval: str = '5m', limit: int = 500) -> pd.DataFrame:
        """Fetch klines data from Binance"""
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
            
            # Convert to numeric and datetime
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df[numeric_columns]
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching klines: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators"""
        if len(df) < 200:
            logger.warning("Not enough data to calculate indicators")
            return {}
        
        indicators = {}
        
        # EMAs
        indicators['ema_9'] = self.indicators.ema(df['close'], 9)
        indicators['ema_21'] = self.indicators.ema(df['close'], 21)
        indicators['ema_50'] = self.indicators.ema(df['close'], 50)
        indicators['ema_200'] = self.indicators.ema(df['close'], 200)
        
        # MACD
        macd_data = self.indicators.macd(df['close'])
        indicators.update(macd_data)
        
        # RSI
        indicators['rsi'] = self.indicators.rsi(df['close'])
        
        # VWAP
        indicators['vwap'] = self.indicators.vwap(
            df['high'], df['low'], df['close'], df['volume']
        )
        
        return indicators
    
    def generate_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, int]:
        """
        Generate trading signals based on all indicators
        Returns: Dict with 'signal' (-1 for sell, 0 for hold, 1 for buy) and 'strength'
        """
        if not indicators:
            return {'signal': 0, 'strength': 0}
        
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        
        signals = []
        reasons = []
        
        # 1. MACD Signals
        macd_current = indicators['macd'].iloc[-1]
        macd_prev = indicators['macd'].iloc[-2]
        signal_current = indicators['signal'].iloc[-1]
        signal_prev = indicators['signal'].iloc[-2]
        histogram_current = indicators['histogram'].iloc[-1]
        histogram_prev = indicators['histogram'].iloc[-2]
        
        # MACD crossover signals
        if macd_prev <= signal_prev and macd_current > signal_current:
            signals.append(1)
            reasons.append("MACD bullish crossover")
        elif macd_prev >= signal_prev and macd_current < signal_current:
            signals.append(-1)
            reasons.append("MACD bearish crossover")
        
        # MACD histogram momentum
        if histogram_current > histogram_prev and histogram_current > 0:
            signals.append(1)
            reasons.append("MACD histogram expanding bullish")
        elif histogram_current < histogram_prev and histogram_current < 0:
            signals.append(-1)
            reasons.append("MACD histogram expanding bearish")
        
        # 2. VWAP Signals
        vwap_current = indicators['vwap'].iloc[-1]
        if current_price > vwap_current:
            signals.append(1)
            reasons.append("Price above VWAP (bulls in control)")
        elif current_price < vwap_current:
            signals.append(-1)
            reasons.append("Price below VWAP (bears dominating)")
        
        # 3. EMA Signals
        ema_9_current = indicators['ema_9'].iloc[-1]
        ema_21_current = indicators['ema_21'].iloc[-1]
        ema_50_current = indicators['ema_50'].iloc[-1]
        ema_200_current = indicators['ema_200'].iloc[-1]
        
        ema_9_prev = indicators['ema_9'].iloc[-2]
        ema_21_prev = indicators['ema_21'].iloc[-2]
        
        # Quick trend (9 EMA)
        if current_price > ema_9_current:
            signals.append(1)
            reasons.append("Price above 9 EMA (short-term bullish)")
        elif current_price < ema_9_current:
            signals.append(-1)
            reasons.append("Price below 9 EMA (short-term bearish)")
        
        # EMA crossovers (9 vs 21)
        if ema_9_prev <= ema_21_prev and ema_9_current > ema_21_current:
            signals.append(2)  # Stronger signal
            reasons.append("9 EMA crossed above 21 EMA (bullish momentum)")
        elif ema_9_prev >= ema_21_prev and ema_9_current < ema_21_current:
            signals.append(-2)  # Stronger signal
            reasons.append("9 EMA crossed below 21 EMA (bearish momentum)")
        
        # Trend confirmation (50 EMA)
        if current_price > ema_50_current:
            signals.append(1)
            reasons.append("Price above 50 EMA (healthy uptrend)")
        elif current_price < ema_50_current:
            signals.append(-1)
            reasons.append("Price below 50 EMA (weak/reversing trend)")
        
        # Long-term direction (200 EMA)
        if current_price > ema_200_current:
            signals.append(1)
            reasons.append("Price above 200 EMA (bull market)")
        elif current_price < ema_200_current:
            signals.append(-1)
            reasons.append("Price below 200 EMA (bear market)")
        
        # Golden Cross / Death Cross
        if ema_50_current > ema_200_current and indicators['ema_50'].iloc[-2] <= indicators['ema_200'].iloc[-2]:
            signals.append(3)  # Very strong signal
            reasons.append("Golden Cross (50 EMA above 200 EMA)")
        elif ema_50_current < ema_200_current and indicators['ema_50'].iloc[-2] >= indicators['ema_200'].iloc[-2]:
            signals.append(-3)  # Very strong signal
            reasons.append("Death Cross (50 EMA below 200 EMA)")
        
        # 4. RSI Signals
        rsi_current = indicators['rsi'].iloc[-1]
        if rsi_current < 30:
            signals.append(1)
            reasons.append(f"RSI oversold ({rsi_current:.1f})")
        elif rsi_current > 70:
            signals.append(-1)
            reasons.append(f"RSI overbought ({rsi_current:.1f})")
        
        # Calculate overall signal
        if not signals:
            return {'signal': 0, 'strength': 0, 'reasons': []}
        
        signal_sum = sum(signals)
        signal_strength = abs(signal_sum)
        
        if signal_sum > 0:
            final_signal = 1  # Buy
        elif signal_sum < 0:
            final_signal = -1  # Sell
        else:
            final_signal = 0  # Hold
        
        signal_data = {
            'signal': final_signal,
            'strength': signal_strength,
            'reasons': reasons,
            'raw_signals': signals
        }
        
        # Store signal in database with current price and indicators
        current_price = df['close'].iloc[-1]
        indicator_values = {
            'rsi': indicators['rsi'].iloc[-1] if 'rsi' in indicators else 0,
            'vwap': indicators['vwap'].iloc[-1] if 'vwap' in indicators else current_price,
            'ema_9': indicators['ema_9'].iloc[-1] if 'ema_9' in indicators else current_price,
            'ema_21': indicators['ema_21'].iloc[-1] if 'ema_21' in indicators else current_price,
            'ema_50': indicators['ema_50'].iloc[-1] if 'ema_50' in indicators else current_price,
            'ema_200': indicators['ema_200'].iloc[-1] if 'ema_200' in indicators else current_price,
            'macd': indicators['macd'].iloc[-1] if 'macd' in indicators else 0,
            'macd_signal': indicators['signal'].iloc[-1] if 'signal' in indicators else 0,
            'macd_histogram': indicators['histogram'].iloc[-1] if 'histogram' in indicators else 0
        }
        
        signal_data['indicators'] = indicator_values
        signal_id = self.db.store_signal(self.symbol, current_price, signal_data)
        signal_data['signal_id'] = signal_id
        
        return signal_data
    
    def calculate_position_size(self) -> float:
        """Calculate position size based on position percentage (like screenshot slider)"""
        try:
            account_info = self.client.futures_account()
            available_balance = float(account_info['availableBalance'])
            
            # Get current price
            ticker = self.client.futures_symbol_ticker(symbol=self.symbol)
            current_price = float(ticker['price'])
            
            # Calculate position size based on position percentage (like screenshot)
            # This mimics the percentage slider shown in the screenshot (51%)
            position_value_usdc = available_balance * (self.position_percentage / 100)
            
            # Apply leverage to get the actual position value
            leveraged_position_value = position_value_usdc * self.leverage
            
            # Calculate quantity in base asset (SUI)
            position_size = leveraged_position_value / current_price
            
            # Get symbol info for proper rounding
            symbol_info = self.client.futures_exchange_info()
            for s in symbol_info['symbols']:
                if s['symbol'] == self.symbol:
                    step_size = float(s['filters'][1]['stepSize'])
                    precision = len(str(step_size).rstrip('0').split('.')[-1])
                    position_size = round(position_size, precision)
                    break
            
            logger.info(f"💰 Position Calc: {self.position_percentage}% of ${available_balance:.2f} = ${position_value_usdc:.2f}")
            logger.info(f"⚡ With {self.leverage}x leverage: ${leveraged_position_value:.2f} → {position_size:.4f} SUI")
            
            return position_size
            
        except BinanceAPIException as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def execute_trade(self, signal_data: Dict) -> bool:
        """Execute trade based on signal"""
        if signal_data['strength'] < 3:  # Minimum signal strength threshold
            logger.info(f"Signal strength {signal_data['strength']} below threshold")
            return False
        
        try:
            # Calculate position size
            position_size = self.calculate_position_size()
            if position_size == 0:
                logger.error("Invalid position size")
                return False
            
            # Determine order side
            if signal_data['signal'] == 1:
                side = 'BUY'
                new_position = 'LONG'
            elif signal_data['signal'] == -1:
                side = 'SELL'
                new_position = 'SHORT'
            else:
                return False
            
            # Close existing position if opposite direction
            if self.position_side and self.position_side != new_position:
                self.close_position()
            
            # Skip if already in same position
            if self.position_side == new_position:
                logger.info(f"Already in {new_position} position")
                return False
            
            # Place market order (like screenshot shows Market order type)
            order = self.client.futures_create_order(
                symbol=self.symbol,
                side=side,
                type='MARKET',
                quantity=position_size
            )
            
            # Update position tracking
            self.position_size = position_size
            self.position_side = new_position
            
            # Get updated position info for logging
            updated_position = self.get_position_info()
            entry_price = updated_position.get('entry_price', 0)
            liquidation_price = updated_position.get('liquidation_price', 0)
            
            # Store trade in database
            trade_id = self.db.store_trade(
                signal_id=signal_data.get('signal_id', 0),
                symbol=self.symbol,
                side=side,
                quantity=position_size,
                entry_price=entry_price,
                leverage=self.leverage,
                position_percentage=self.position_percentage,
                order_id=order.get('orderId') if order else None,
                liquidation_price=liquidation_price
            )
            
            logger.info(f"✅ {side} Order Executed: {position_size} {self.symbol}")
            logger.info(f"📊 Entry Price: ${entry_price:.4f}")
            logger.info(f"🎯 Signal Reasons: {', '.join(signal_data['reasons'])}")
            logger.info(f"💾 Trade stored in database (ID: {trade_id})")
            
            if liquidation_price > 0:
                logger.info(f"⚠️ Liquidation Price: ${liquidation_price:.4f}")
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Error executing trade: {e}")
            return False
    
    def get_position_info(self) -> Dict:
        """Get current position information (like screenshot display)"""
        try:
            positions = self.client.futures_position_information(symbol=self.symbol)
            
            for pos in positions:
                if pos['symbol'] == self.symbol:
                    position_amt = float(pos['positionAmt'])
                    if position_amt != 0:
                        return {
                            'symbol': pos['symbol'],
                            'side': 'LONG' if position_amt > 0 else 'SHORT',
                            'size': abs(position_amt),
                            'entry_price': float(pos['entryPrice']),
                            'mark_price': float(pos['markPrice']),
                            'unrealized_pnl': float(pos['unRealizedProfit']),
                            'liquidation_price': float(pos['liquidationPrice']) if pos['liquidationPrice'] != '0' else 0,
                            'margin_type': pos['marginType'],
                            'isolated_wallet': float(pos['isolatedWallet']) if pos['isolatedWallet'] else 0,
                            'percentage': float(pos['percentage'])
                        }
            
            return {'symbol': self.symbol, 'side': None, 'size': 0}
            
        except BinanceAPIException as e:
            logger.error(f"Error getting position info: {e}")
            return {'symbol': self.symbol, 'side': None, 'size': 0}
    
    def close_position(self):
        """Close current position"""
        if not self.position_side or self.position_size == 0:
            return True
        
        try:
            side = 'SELL' if self.position_side == 'LONG' else 'BUY'
            
            order = self.client.futures_create_order(
                symbol=self.symbol,
                side=side,
                type='MARKET',
                quantity=self.position_size
            )
            
            logger.info(f"Position closed: {self.position_side} {self.position_size} {self.symbol}")
            
            self.position_size = 0
            self.position_side = None
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def run(self, interval: int = 300):  # 5 minutes
        """Main bot loop"""
        logger.info(f"🚀 Starting Binance Futures Bot for {self.symbol}")
        logger.info(f"⚡ Mode: CROSS {self.leverage}x | Position Size: {self.position_percentage}%")
        logger.info(f"🎯 Risk Management: {self.risk_percentage}% | Strategy: MACD + VWAP + EMAs + RSI")
        logger.info(f"💾 Database: SQLite database tracking signals and trades")
        
        # Show recent performance on startup
        performance = self.db.calculate_performance_metrics(self.symbol, 30)
        if performance.get('total_trades', 0) > 0:
            logger.info(f"📈 Last 30 days: {performance['total_trades']} trades, "
                       f"{performance['win_rate']:.1f}% win rate, "
                       f"${performance['total_pnl']:.2f} total PnL")
        
        while True:
            try:
                # Get current position info (like screenshot)
                position_info = self.get_position_info()
                
                # Fetch data
                df = self.get_klines()
                if df.empty:
                    logger.error("❌ No data received")
                    time.sleep(interval)
                    continue
                
                # Calculate indicators
                indicators = self.calculate_indicators(df)
                if not indicators:
                    logger.warning("⚠️ Could not calculate indicators")
                    time.sleep(interval)
                    continue
                
                # Generate signals
                signal_data = self.generate_signals(df, indicators)
                
                # Log current status (screenshot style)
                current_price = df['close'].iloc[-1]
                rsi = indicators['rsi'].iloc[-1] if 'rsi' in indicators else 0
                vwap = indicators['vwap'].iloc[-1] if 'vwap' in indicators else current_price
                
                # Position display (like screenshot)
                if position_info['side']:
                    pnl_emoji = "🟢" if position_info['unrealized_pnl'] > 0 else "🔴"
                    logger.info(f"📍 Position: {position_info['side']} {position_info['size']:.4f} SUI")
                    logger.info(f"💰 PnL: {pnl_emoji} {position_info['unrealized_pnl']:.4f} USDC ({position_info['percentage']:.2f}%)")
                    if position_info['liquidation_price'] > 0:
                        logger.info(f"⚠️ Liquidation: ${position_info['liquidation_price']:.4f}")
                
                # Market analysis display
                vwap_status = "🔵 Bulls" if current_price > vwap else "🔴 Bears"
                rsi_status = "🔥 Overbought" if rsi > 70 else "❄️ Oversold" if rsi < 30 else "⚖️ Neutral"
                
                logger.info(f"💲 {self.symbol}: ${current_price:.4f} | RSI: {rsi:.1f} ({rsi_status})")
                logger.info(f"📈 VWAP: ${vwap:.4f} ({vwap_status}) | Signal: {signal_data['signal']} | Strength: {signal_data['strength']}")
                
                if signal_data['reasons']:
                    logger.info(f"🔍 Analysis: {', '.join(signal_data['reasons'][:3])}")
                
                # Execute trade if strong signal
                if abs(signal_data['signal']) > 0 and signal_data['strength'] >= 3:
                    signal_emoji = "🚀" if signal_data['signal'] > 0 else "📉"
                    logger.info(f"{signal_emoji} Strong signal detected! Executing trade...")
                    self.execute_trade(signal_data)
                
                # Wait for next iteration
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                # Close any open positions before stopping
                position = self.get_position_info()
                if position['side']:
                    logger.info("🔒 Closing positions before shutdown...")
                    self.close_position()
                break
            except Exception as e:
                logger.error(f"💥 Unexpected error: {e}")
                time.sleep(interval)

def main():
    """Main function to run the bot"""
    # Configuration matching screenshot
    SYMBOL = 'SUIUSDC'         # Trading pair (as shown in screenshot)
    LEVERAGE = 50              # Cross 50x leverage (as shown in screenshot)
    POSITION_PERCENT = 51.0    # Percentage of balance to use per trade (like screenshot slider)
    RISK_PERCENT = 2.0         # Risk management percentage for stop loss
    INTERVAL = 300             # Check interval in seconds (5 minutes)
    
    try:
        # Initialize and run bot
        bot = BinanceFuturesBot(
            symbol=SYMBOL,
            leverage=LEVERAGE,
            risk_percentage=RISK_PERCENT,
            position_percentage=POSITION_PERCENT
        )
        
        bot.run(interval=INTERVAL)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()