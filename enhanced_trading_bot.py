#!/usr/bin/env python3
"""
Enhanced Trading Bot with Multiple Strategy Integration
Combines original signals with multi-timeframe confluence and adaptive position sizing
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

from trading_bot import BinanceFuturesBot, TechnicalIndicators
from multi_timeframe_strategy import MultiTimeframeStrategy
from config import TRADING_CONFIG, INDICATOR_CONFIG, RISK_CONFIG
from database import get_database

logger = logging.getLogger(__name__)

class EnhancedTradingBot(BinanceFuturesBot):
    """
    Enhanced trading bot that combines multiple strategies:
    1. Original technical analysis
    2. Multi-timeframe confluence  
    3. Adaptive position sizing
    4. Enhanced risk management
    """
    
    def __init__(self, symbol: str = 'SUIUSDC', leverage: int = 50, risk_percentage: float = 1.0):
        super().__init__(symbol, leverage, risk_percentage)
        
        # Initialize multi-timeframe strategy
        self.mtf_strategy = MultiTimeframeStrategy(symbol, leverage, risk_percentage)
        
        # Strategy weights
        self.strategy_weights = {
            'original': 0.4,        # Original technical analysis
            'confluence': 0.6       # Multi-timeframe confluence
        }
        
        # Enhanced settings
        self.min_combined_strength = 3
        self.confluence_required = True
        self.adaptive_sizing = True
        
        logger.info(f"🚀 Enhanced Trading Bot initialized for {symbol}")
        logger.info(f"⚖️ Strategy weights: Original={self.strategy_weights['original']}, Confluence={self.strategy_weights['confluence']}")
    
    def calculate_adaptive_position_size(self, signal_strength: int, confluence_data: Dict) -> float:
        """
        Calculate adaptive position size based on signal quality and market conditions
        """
        base_position = self.position_percentage / 100  # Convert from percentage
        
        # Signal strength multiplier (1-6 scale)
        strength_multiplier = min(signal_strength / 6.0, 1.0)
        
        # Confluence multiplier
        confluence_score = confluence_data.get('confluence_score', 0)
        max_confluence = 3  # Max timeframes
        confluence_multiplier = min(confluence_score / max_confluence, 1.0)
        
        # Risk adjustment based on recent performance
        try:
            db = get_database()
            recent_trades = db.get_recent_trades(self.symbol, limit=10)
            
            if recent_trades:
                recent_pnl = [trade.get('pnl', 0) for trade in recent_trades[-5:]]
                avg_recent_pnl = sum(recent_pnl) / len(recent_pnl)
                
                # Reduce size after losses, increase after wins
                performance_multiplier = max(0.5, min(1.5, 1.0 + (avg_recent_pnl / 100)))
            else:
                performance_multiplier = 1.0
                
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch recent performance: {e}")
            performance_multiplier = 1.0
        
        # Calculate final position size
        adaptive_size = base_position * strength_multiplier * confluence_multiplier * performance_multiplier
        
        # Apply limits
        min_size = 0.1  # Minimum 10% of base
        max_size = 0.8  # Maximum 80% of balance
        final_size = max(min_size, min(max_size, adaptive_size))
        
        logger.info(f"📊 Adaptive Position Sizing:")
        logger.info(f"  Base: {base_position:.1%}")
        logger.info(f"  Strength Mult: {strength_multiplier:.2f}")
        logger.info(f"  Confluence Mult: {confluence_multiplier:.2f}")
        logger.info(f"  Performance Mult: {performance_multiplier:.2f}")
        logger.info(f"  Final Size: {final_size:.1%}")
        
        return final_size
    
    def generate_enhanced_signals(self) -> Dict:
        """
        Generate enhanced signals combining original and multi-timeframe analysis
        """
        logger.info("🧠 Generating enhanced signals...")
        
        try:
            # Get original signals
            df = self.get_market_data()
            if df is None or len(df) < 50:
                return {'signal': 0, 'strength': 0, 'reasons': ["Insufficient market data"]}
            
            indicators = self.calculate_indicators(df)
            original_signals = self.generate_signals(df, indicators)
            
            logger.info(f"📈 Original Signal: {original_signals['signal']} (strength: {original_signals.get('strength', 0)})")
            
            # Get multi-timeframe confluence
            confluence_result = self.mtf_strategy.generate_enhanced_signals()
            
            logger.info(f"🔄 Confluence Signal: {confluence_result['signal']} (strength: {confluence_result['strength']})")
            
            # Combine signals
            combined_result = self.combine_signals(original_signals, confluence_result)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced signals: {e}")
            return {'signal': 0, 'strength': 0, 'reasons': [f"Signal generation error: {str(e)}"]}
    
    def combine_signals(self, original: Dict, confluence: Dict) -> Dict:
        """
        Combine original and confluence signals with weighting
        """
        try:
            # Extract signal components
            orig_signal = original.get('signal', 0)
            orig_strength = original.get('strength', 0)
            
            conf_signal = confluence.get('signal', 0)
            conf_strength = confluence.get('strength', 0)
            
            # Weighted combination
            orig_weight = self.strategy_weights['original']
            conf_weight = self.strategy_weights['confluence']
            
            # Calculate weighted signal strength
            orig_weighted = orig_signal * orig_strength * orig_weight
            conf_weighted = conf_signal * conf_strength * conf_weight
            
            total_weighted = orig_weighted + conf_weighted
            total_possible = (orig_strength * orig_weight) + (conf_strength * conf_weight)
            
            # Determine final signal
            if abs(total_weighted) < 1.0:
                final_signal = 0
                final_strength = 0
                signal_decision = "Weak combined signal"
            else:
                final_signal = 1 if total_weighted > 0 else -1
                final_strength = min(6, int(abs(total_weighted)))
                signal_decision = f"{'Bullish' if final_signal == 1 else 'Bearish'} consensus"
            
            # Check confluence requirement
            if self.confluence_required and conf_signal == 0:
                final_signal = 0
                final_strength = 0
                signal_decision = "No multi-timeframe confluence - trade skipped"
            
            # Agreement bonus
            if orig_signal == conf_signal and orig_signal != 0:
                final_strength = min(6, final_strength + 1)
                signal_decision += " + Strategy Agreement Bonus"
            
            # Compile reasons
            combined_reasons = [signal_decision]
            
            # Add original reasons
            if 'reasons' in original and original['reasons']:
                combined_reasons.append(f"Original: {original['reasons'][0]}")
            
            # Add confluence reasons
            if 'reasons' in confluence and confluence['reasons']:
                combined_reasons.extend([f"MTF: {reason}" for reason in confluence['reasons'][:2]])
            
            result = {
                'signal': final_signal,
                'strength': final_strength,
                'reasons': combined_reasons,
                'original_data': original,
                'confluence_data': confluence,
                'weighted_score': total_weighted,
                'strategy_agreement': orig_signal == conf_signal
            }
            
            logger.info(f"🎯 Combined Signal Result:")
            logger.info(f"  Final Signal: {final_signal} ({'BUY' if final_signal == 1 else 'SELL' if final_signal == -1 else 'HOLD'})")
            logger.info(f"  Combined Strength: {final_strength}/6")
            logger.info(f"  Strategy Agreement: {'✅' if result['strategy_agreement'] else '❌'}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error combining signals: {e}")
            return {'signal': 0, 'strength': 0, 'reasons': ["Signal combination error"]}
    
    def should_execute_trade(self, signal_data: Dict) -> Tuple[bool, str]:
        """
        Enhanced trade execution decision with stricter criteria
        """
        if signal_data['signal'] == 0:
            return False, "No trading signal"
        
        # Minimum strength requirement
        if signal_data['strength'] < self.min_combined_strength:
            return False, f"Signal strength {signal_data['strength']} below minimum {self.min_combined_strength}"
        
        # Confluence requirement check
        if self.confluence_required:
            confluence_data = signal_data.get('confluence_data', {})
            if confluence_data.get('signal', 0) == 0:
                return False, "Multi-timeframe confluence required but not present"
        
        # Strategy agreement check (optional but preferred)
        if not signal_data.get('strategy_agreement', False):
            logger.warning("⚠️ Strategies disagree - proceeding with caution")
        
        # Risk management checks
        try:
            current_balance = float(self.client.futures_account_balance()[0]['balance'])
            if current_balance < 100:  # Minimum balance check
                return False, f"Balance too low: ${current_balance:.2f}"
        except Exception as e:
            logger.warning(f"⚠️ Could not check balance: {e}")
        
        return True, "All criteria met - trade approved"
    
    def execute_enhanced_trade(self, signal_data: Dict) -> Dict:
        """
        Execute trade with enhanced position sizing and risk management
        """
        should_trade, reason = self.should_execute_trade(signal_data)
        
        if not should_trade:
            logger.info(f"❌ Trade execution declined: {reason}")
            return {'success': False, 'reason': reason}
        
        try:
            # Calculate adaptive position size
            if self.adaptive_sizing:
                confluence_data = signal_data.get('confluence_data', {})
                position_size = self.calculate_adaptive_position_size(
                    signal_data['strength'], 
                    confluence_data
                )
                # Update position percentage for this trade
                original_position_pct = self.position_percentage
                self.position_percentage = position_size * 100
            
            # Execute the trade using parent method
            result = self.execute_trade(signal_data['signal'], signal_data['strength'])
            
            # Store enhanced signal data
            if result.get('success'):
                try:
                    db = get_database()
                    db.store_enhanced_signal(
                        symbol=self.symbol,
                        signal=signal_data['signal'],
                        strength=signal_data['strength'],
                        original_signal=signal_data.get('original_data', {}),
                        confluence_data=signal_data.get('confluence_data', {}),
                        position_size=position_size if self.adaptive_sizing else None
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Could not store enhanced signal: {e}")
            
            # Restore original position percentage
            if self.adaptive_sizing:
                self.position_percentage = original_position_pct
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error executing enhanced trade: {e}")
            return {'success': False, 'reason': f"Execution error: {str(e)}"}
    
    def run_enhanced_strategy(self):
        """
        Main loop for enhanced trading strategy
        """
        logger.info("🚀 Starting Enhanced Trading Strategy...")
        
        while True:
            try:
                # Generate enhanced signals
                signal_data = self.generate_enhanced_signals()
                
                if signal_data['signal'] != 0:
                    logger.info("📊 Signal Generated - Evaluating trade...")
                    
                    # Execute trade if criteria met
                    trade_result = self.execute_enhanced_trade(signal_data)
                    
                    if trade_result.get('success'):
                        logger.info("✅ Enhanced trade executed successfully")
                    else:
                        logger.info(f"⏸️ Trade skipped: {trade_result.get('reason', 'Unknown')}")
                else:
                    logger.info("📊 No trading signals - monitoring...")
                
                # Wait for next check
                time.sleep(TRADING_CONFIG['check_interval'])
                
            except KeyboardInterrupt:
                logger.info("👋 Enhanced strategy stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Enhanced strategy error: {e}")
                time.sleep(30)  # Wait before retry

# Test function
def test_enhanced_strategy():
    """Test the enhanced trading strategy"""
    logger.info("🧪 Testing Enhanced Trading Strategy...")
    
    try:
        bot = EnhancedTradingBot('SUIUSDC', leverage=20, risk_percentage=1.0)
        
        # Generate signals
        signal_data = bot.generate_enhanced_signals()
        
        print("\n" + "="*60)
        print("ENHANCED TRADING STRATEGY RESULTS")
        print("="*60)
        print(f"Final Signal: {signal_data['signal']} ({'BUY' if signal_data['signal'] == 1 else 'SELL' if signal_data['signal'] == -1 else 'HOLD'})")
        print(f"Combined Strength: {signal_data['strength']}/6")
        print(f"Strategy Agreement: {'✅ YES' if signal_data.get('strategy_agreement', False) else '❌ NO'}")
        
        print("\nREASONS:")
        for i, reason in enumerate(signal_data['reasons'][:5], 1):
            print(f"{i}. {reason}")
        
        # Trade decision
        should_trade, reason = bot.should_execute_trade(signal_data)
        print(f"\nTRADE DECISION: {'✅ EXECUTE' if should_trade else '❌ SKIP'}")
        print(f"Reason: {reason}")
        
        # Show individual strategy results
        if 'original_data' in signal_data:
            orig = signal_data['original_data']
            print(f"\nOriginal Strategy: {orig.get('signal', 0)} (strength: {orig.get('strength', 0)})")
        
        if 'confluence_data' in signal_data:
            conf = signal_data['confluence_data']
            print(f"Confluence Strategy: {conf.get('signal', 0)} (strength: {conf.get('strength', 0)})")
            print(f"Timeframes Aligned: {conf.get('confluence_score', 0)}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Enhanced strategy test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_strategy()