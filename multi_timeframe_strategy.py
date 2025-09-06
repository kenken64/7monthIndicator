#!/usr/bin/env python3
"""
Multi-Timeframe Confluence Trading Strategy
Combines signals across multiple timeframes for higher probability trades
"""

import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from trading_bot import TechnicalIndicators, BinanceFuturesBot
from config import TRADING_CONFIG, INDICATOR_CONFIG

logger = logging.getLogger(__name__)

class MultiTimeframeStrategy(BinanceFuturesBot):
    """
    Enhanced trading bot with multi-timeframe confluence analysis
    Trades only when multiple timeframes align for higher success rate
    """
    
    def __init__(self, symbol: str = 'SUIUSDC', leverage: int = 50, risk_percentage: float = 1.0):
        super().__init__(symbol, leverage, risk_percentage)
        
        # Timeframe configuration
        self.timeframes = {
            'fast': '5m',      # Quick signals and entries
            'medium': '15m',   # Trend confirmation
            'slow': '1h'       # Market direction filter
        }
        
        # Confluence requirements
        self.min_timeframes_aligned = 2  # Minimum timeframes that must agree
        self.confluence_weights = {
            'fast': 1.0,
            'medium': 1.5,     # Medium-term carries more weight
            'slow': 2.0        # Long-term direction is most important
        }
        
        logger.info(f"🔄 Multi-Timeframe Strategy initialized for {symbol}")
        logger.info(f"📊 Timeframes: {self.timeframes}")
        logger.info(f"⚖️ Min alignment required: {self.min_timeframes_aligned}")
    
    def get_multi_timeframe_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch data for all timeframes"""
        multi_data = {}
        
        for name, timeframe in self.timeframes.items():
            try:
                klines = self.client.futures_historical_klines(
                    self.symbol,
                    timeframe,
                    limit=INDICATOR_CONFIG['klines_limit']
                )
                
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convert to numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                multi_data[name] = df
                
                logger.debug(f"✅ {name} ({timeframe}): {len(df)} candles fetched")
                
            except BinanceAPIException as e:
                logger.error(f"❌ Error fetching {timeframe} data: {e}")
                return None
        
        return multi_data
    
    def calculate_timeframe_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate indicators for a single timeframe"""
        try:
            indicators = {}
            
            # EMAs
            indicators['ema_9'] = TechnicalIndicators.ema(df['close'], INDICATOR_CONFIG['ema_fast'])
            indicators['ema_21'] = TechnicalIndicators.ema(df['close'], INDICATOR_CONFIG['ema_medium'])
            indicators['ema_50'] = TechnicalIndicators.ema(df['close'], INDICATOR_CONFIG['ema_slow'])
            indicators['ema_200'] = TechnicalIndicators.ema(df['close'], INDICATOR_CONFIG['ema_trend'])
            
            # MACD
            macd_data = TechnicalIndicators.macd(df['close'])
            indicators.update(macd_data)
            
            # RSI
            indicators['rsi'] = TechnicalIndicators.rsi(df['close'])
            
            # VWAP
            indicators['vwap'] = TechnicalIndicators.vwap(df['high'], df['low'], df['close'], df['volume'])
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators: {e}")
            return {}
    
    def generate_timeframe_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Generate signal for a single timeframe"""
        if not indicators or len(df) < 2:
            return {'signal': 0, 'strength': 0, 'reasons': []}
        
        current_price = df['close'].iloc[-1]
        signals = []
        reasons = []
        
        # Simplified signal logic for timeframe analysis
        try:
            # EMA trend analysis
            ema_9 = indicators['ema_9'].iloc[-1]
            ema_21 = indicators['ema_21'].iloc[-1]
            ema_50 = indicators['ema_50'].iloc[-1]
            
            # Price vs EMAs
            if current_price > ema_9 > ema_21 > ema_50:
                signals.append(2)
                reasons.append("Strong bullish EMA alignment")
            elif current_price > ema_9 > ema_21:
                signals.append(1)
                reasons.append("Bullish short-term trend")
            elif current_price < ema_9 < ema_21 < ema_50:
                signals.append(-2)
                reasons.append("Strong bearish EMA alignment")
            elif current_price < ema_9 < ema_21:
                signals.append(-1)
                reasons.append("Bearish short-term trend")
            
            # MACD confirmation
            macd_current = indicators['macd'].iloc[-1]
            signal_current = indicators['signal'].iloc[-1]
            histogram = indicators['histogram'].iloc[-1]
            
            if macd_current > signal_current and histogram > 0:
                signals.append(1)
                reasons.append("MACD bullish momentum")
            elif macd_current < signal_current and histogram < 0:
                signals.append(-1)
                reasons.append("MACD bearish momentum")
            
            # RSI filter
            rsi = indicators['rsi'].iloc[-1]
            if rsi < 30:
                signals.append(1)
                reasons.append("RSI oversold")
            elif rsi > 70:
                signals.append(-1)
                reasons.append("RSI overbought")
            
            # Calculate final signal
            total_signal = sum(signals)
            strength = abs(total_signal)
            direction = 1 if total_signal > 0 else -1 if total_signal < 0 else 0
            
            return {
                'signal': direction,
                'strength': min(strength, 5),  # Cap at 5
                'reasons': reasons,
                'raw_signals': signals
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating timeframe signal: {e}")
            return {'signal': 0, 'strength': 0, 'reasons': []}
    
    def analyze_confluence(self, timeframe_signals: Dict) -> Dict:
        """
        Analyze confluence across timeframes
        Returns: Enhanced signal with confluence weighting
        """
        try:
            aligned_signals = []
            total_weight = 0
            confluence_reasons = []
            timeframe_summary = {}
            
            # Analyze each timeframe
            for tf_name, signal_data in timeframe_signals.items():
                if signal_data['signal'] != 0:
                    weight = self.confluence_weights[tf_name]
                    weighted_signal = signal_data['signal'] * signal_data['strength'] * weight
                    aligned_signals.append(weighted_signal)
                    total_weight += weight
                    
                    timeframe_summary[tf_name] = {
                        'signal': signal_data['signal'],
                        'strength': signal_data['strength'],
                        'weight': weight,
                        'reasons': signal_data['reasons'][:2]  # Top 2 reasons
                    }
                    
                    confluence_reasons.append(f"{tf_name.upper()}: {signal_data['signal']} (strength: {signal_data['strength']})")
            
            # Check confluence requirements
            bullish_timeframes = sum(1 for sig in aligned_signals if sig > 0)
            bearish_timeframes = sum(1 for sig in aligned_signals if sig < 0)
            
            # Confluence logic
            if bullish_timeframes >= self.min_timeframes_aligned and bearish_timeframes == 0:
                # All aligned bullish
                final_signal = 1
                confluence_strength = min(bullish_timeframes * 2, 6)
                confluence_reasons.insert(0, f"✅ {bullish_timeframes} timeframes aligned BULLISH")
                
            elif bearish_timeframes >= self.min_timeframes_aligned and bullish_timeframes == 0:
                # All aligned bearish
                final_signal = -1
                confluence_strength = min(bearish_timeframes * 2, 6)
                confluence_reasons.insert(0, f"✅ {bearish_timeframes} timeframes aligned BEARISH")
                
            elif total_weight > 0:
                # Weighted average with conflict penalty
                avg_signal = sum(aligned_signals) / total_weight
                conflict_penalty = min(bullish_timeframes, bearish_timeframes) * 0.5
                
                if abs(avg_signal) > 1.5:  # Strong weighted signal
                    final_signal = 1 if avg_signal > 0 else -1
                    confluence_strength = max(1, int(abs(avg_signal) - conflict_penalty))
                    confluence_reasons.insert(0, f"⚖️ Weighted confluence: {avg_signal:.1f}")
                else:
                    final_signal = 0
                    confluence_strength = 0
                    confluence_reasons.insert(0, "⚠️ Mixed signals - no clear confluence")
            else:
                # No signals
                final_signal = 0
                confluence_strength = 0
                confluence_reasons = ["📊 No significant signals across timeframes"]
            
            return {
                'signal': final_signal,
                'strength': confluence_strength,
                'reasons': confluence_reasons,
                'timeframe_analysis': timeframe_summary,
                'confluence_score': len(aligned_signals),
                'bullish_count': bullish_timeframes,
                'bearish_count': bearish_timeframes
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing confluence: {e}")
            return {'signal': 0, 'strength': 0, 'reasons': ["Error in confluence analysis"]}
    
    def generate_enhanced_signals(self) -> Dict:
        """
        Main method: Generate signals using multi-timeframe confluence
        """
        logger.info("🔍 Starting multi-timeframe analysis...")
        
        # Get data for all timeframes
        multi_data = self.get_multi_timeframe_data()
        if not multi_data:
            logger.error("❌ Failed to fetch multi-timeframe data")
            return {'signal': 0, 'strength': 0, 'reasons': ["Data fetch error"]}
        
        # Analyze each timeframe
        timeframe_signals = {}
        
        for tf_name, df in multi_data.items():
            logger.info(f"📊 Analyzing {tf_name} timeframe ({self.timeframes[tf_name]})...")
            
            # Calculate indicators
            indicators = self.calculate_timeframe_indicators(df)
            if not indicators:
                continue
            
            # Generate signal for this timeframe
            signal_data = self.generate_timeframe_signal(df, indicators)
            timeframe_signals[tf_name] = signal_data
            
            logger.info(f"  {tf_name}: Signal={signal_data['signal']}, Strength={signal_data['strength']}")
        
        # Analyze confluence
        confluence_result = self.analyze_confluence(timeframe_signals)
        
        # Log results
        logger.info("🎯 Multi-Timeframe Confluence Results:")
        logger.info(f"  Final Signal: {confluence_result['signal']}")
        logger.info(f"  Confluence Strength: {confluence_result['strength']}")
        logger.info(f"  Bullish TFs: {confluence_result['bullish_count']}")
        logger.info(f"  Bearish TFs: {confluence_result['bearish_count']}")
        
        for reason in confluence_result['reasons'][:3]:
            logger.info(f"  📝 {reason}")
        
        return confluence_result
    
    def should_trade(self, signal_data: Dict) -> bool:
        """
        Enhanced trade decision logic
        """
        if signal_data['signal'] == 0:
            return False
        
        # Require minimum confluence strength
        if signal_data['strength'] < 2:
            logger.info("⚠️ Signal too weak for multi-timeframe strategy")
            return False
        
        # Require minimum timeframe agreement
        if signal_data['confluence_score'] < self.min_timeframes_aligned:
            logger.info(f"⚠️ Only {signal_data['confluence_score']} timeframes aligned, need {self.min_timeframes_aligned}")
            return False
        
        logger.info("✅ Multi-timeframe confluence criteria met - TRADE APPROVED")
        return True

# Test function
def test_multi_timeframe_strategy():
    """Test the multi-timeframe strategy"""
    logger.info("🧪 Testing Multi-Timeframe Strategy...")
    
    try:
        # Initialize strategy
        strategy = MultiTimeframeStrategy('SUIUSDC', leverage=20, risk_percentage=1.0)
        
        # Generate signals
        signal_result = strategy.generate_enhanced_signals()
        
        # Display results
        print("\n" + "="*50)
        print("MULTI-TIMEFRAME CONFLUENCE RESULTS")
        print("="*50)
        print(f"Signal: {signal_result['signal']} ({'BUY' if signal_result['signal'] == 1 else 'SELL' if signal_result['signal'] == -1 else 'HOLD'})")
        print(f"Strength: {signal_result['strength']}/6")
        print(f"Confluence Score: {signal_result['confluence_score']}")
        print(f"Bullish TFs: {signal_result['bullish_count']}")
        print(f"Bearish TFs: {signal_result['bearish_count']}")
        
        print("\nREASONS:")
        for i, reason in enumerate(signal_result['reasons'][:5], 1):
            print(f"{i}. {reason}")
        
        # Trade decision
        should_trade = strategy.should_trade(signal_result)
        print(f"\nTRADE DECISION: {'✅ EXECUTE' if should_trade else '❌ SKIP'}")
        
        if 'timeframe_analysis' in signal_result:
            print("\nTIMEFRAME BREAKDOWN:")
            for tf, data in signal_result['timeframe_analysis'].items():
                print(f"{tf.upper()}: {data['signal']} (strength: {data['strength']}, weight: {data['weight']})")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multi_timeframe_strategy()