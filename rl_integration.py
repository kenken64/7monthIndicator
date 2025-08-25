#!/usr/bin/env python3
"""
RL Integration Module
Integrates the lightweight RL agent with the existing trading bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lightweight_rl import LightweightRLSystem
from database import get_database
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RLTradingDecision:
    """
    Enhanced trading decision system using RL + traditional signals
    """
    
    def __init__(self):
        self.rl_system = LightweightRLSystem()
        self.rl_system.agent.load_model()  # Load trained model
        self.db = get_database()
        
    def make_enhanced_decision(self, indicators: dict, traditional_signal: dict) -> dict:
        """
        Combine RL recommendation with traditional signals
        
        Args:
            indicators: Technical indicators dict
            traditional_signal: Original bot signal result
            
        Returns:
            Enhanced decision with RL input
        """
        
        # Get RL recommendation
        rl_recommendation = self.rl_system.get_trading_recommendation(indicators)
        
        # Original signal info
        original_signal = traditional_signal.get('signal', 0)
        original_strength = traditional_signal.get('strength', 0)
        original_reasons = traditional_signal.get('reasons', [])
        
        # RL recommendation
        rl_action = rl_recommendation['action']
        rl_confidence = rl_recommendation['confidence']
        rl_state = rl_recommendation['state']
        
        # Decision logic: Combine both systems
        final_decision = self._combine_decisions(
            original_signal, original_strength,
            rl_action, rl_confidence
        )
        
        # Enhanced decision
        enhanced_decision = {
            'signal': final_decision['signal'],
            'strength': final_decision['strength'],
            'reasons': final_decision['reasons'],
            'rl_action': rl_action,
            'rl_confidence': rl_confidence,
            'rl_state': rl_state,
            'traditional_signal': original_signal,
            'traditional_strength': original_strength,
            'decision_source': final_decision['source'],
            'risk_level': final_decision['risk_level']
        }
        
        return enhanced_decision
    
    def _combine_decisions(self, traditional_signal: int, traditional_strength: int,
                          rl_action: str, rl_confidence: float) -> dict:
        """
        Intelligent combination of traditional and RL signals
        """
        
        # Convert RL action to signal format
        rl_signal_map = {
            'BUY': 1,
            'SELL': -1,
            'HOLD': 0,
            'CLOSE': 0
        }
        rl_signal = rl_signal_map.get(rl_action, 0)
        
        # Risk assessment based on historical performance
        # Since traditional signals had 7% win rate, be very cautious
        
        if rl_action == 'HOLD' and rl_confidence > 0.7:
            # RL strongly suggests holding - override traditional signal
            return {
                'signal': 0,
                'strength': 0,
                'reasons': [f"RL recommends HOLD with {rl_confidence:.1%} confidence"],
                'source': 'RL_OVERRIDE',
                'risk_level': 'LOW'
            }
        
        elif rl_action in ['BUY', 'SELL'] and rl_confidence > 0.8:
            # RL has high confidence in trading action
            if traditional_signal == rl_signal:
                # Both agree - increase strength but cap at reasonable level
                combined_strength = min(3, traditional_strength + 1)
                return {
                    'signal': rl_signal,
                    'strength': combined_strength,
                    'reasons': [
                        f"RL and traditional signals agree on {rl_action}",
                        f"RL confidence: {rl_confidence:.1%}",
                        f"Traditional strength: {traditional_strength}"
                    ],
                    'source': 'COMBINED_AGREEMENT',
                    'risk_level': 'MEDIUM'
                }
            else:
                # Signals disagree - be conservative
                return {
                    'signal': 0,
                    'strength': 0,
                    'reasons': [
                        f"Signal conflict: Traditional={traditional_signal}, RL={rl_signal}",
                        f"Defaulting to HOLD for safety"
                    ],
                    'source': 'CONFLICT_RESOLUTION',
                    'risk_level': 'LOW'
                }
        
        elif traditional_strength >= 4:
            # Strong traditional signal but RL disagrees - be very cautious
            # Historical data shows even strength 4-5 signals failed
            return {
                'signal': 0,
                'strength': 0,
                'reasons': [
                    f"Traditional signal strength {traditional_strength} historically unreliable",
                    f"RL suggests {rl_action} - staying safe with HOLD"
                ],
                'source': 'RISK_MANAGEMENT',
                'risk_level': 'LOW'
            }
        
        else:
            # Default to conservative approach
            return {
                'signal': 0,
                'strength': 0,
                'reasons': [
                    f"Conservative approach: Traditional strength {traditional_strength}",
                    f"RL suggests {rl_action} with {rl_confidence:.1%} confidence",
                    f"Insufficient confidence for trading action"
                ],
                'source': 'CONSERVATIVE_DEFAULT',
                'risk_level': 'LOW'
            }
    
    def should_close_position(self, current_position: dict, indicators: dict) -> dict:
        """
        Determine if current position should be closed
        """
        
        if not current_position or current_position.get('size', 0) == 0:
            return {'should_close': False, 'reason': 'No position to close'}
        
        # Get RL recommendation
        rl_recommendation = self.rl_system.get_trading_recommendation(indicators)
        
        # Calculate unrealized P&L
        current_price = indicators.get('price', 0)
        entry_price = current_position.get('entry_price', current_price)
        position_side = current_position.get('side', 'LONG')
        
        if position_side == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Risk management rules
        should_close = False
        reason = ""
        
        if pnl_pct < -0.02:  # 2% loss
            should_close = True
            reason = f"Stop loss triggered: {pnl_pct:.1%} loss"
            
        elif pnl_pct > 0.01:  # 1% profit
            should_close = True
            reason = f"Take profit triggered: {pnl_pct:.1%} gain"
            
        elif rl_recommendation['action'] == 'CLOSE' and rl_recommendation['confidence'] > 0.6:
            should_close = True
            reason = f"RL recommends closing with {rl_recommendation['confidence']:.1%} confidence"
        
        return {
            'should_close': should_close,
            'reason': reason,
            'current_pnl_pct': pnl_pct,
            'rl_action': rl_recommendation['action'],
            'rl_confidence': rl_recommendation['confidence']
        }
    
    def get_position_size_recommendation(self, signal_strength: int, rl_confidence: float) -> float:
        """
        Recommend position size based on signal quality and RL confidence
        """
        
        # Base position size (much smaller than original 51%)
        base_size = 0.02  # 2% of balance
        
        # Adjust based on combined confidence
        combined_confidence = (signal_strength / 10) * 0.3 + rl_confidence * 0.7
        
        # Conservative sizing
        if combined_confidence > 0.8:
            position_size = base_size * 1.5  # 3% max
        elif combined_confidence > 0.6:
            position_size = base_size * 1.0  # 2%
        else:
            position_size = base_size * 0.5  # 1% min
        
        return min(position_size, 0.03)  # Never exceed 3%

def create_rl_enhanced_signal_function():
    """
    Create enhanced signal generation function for integration with existing bot
    """
    
    rl_decision = RLTradingDecision()
    
    def enhanced_generate_signals(df, indicators):
        """
        Enhanced signal generation with RL integration
        This replaces the original generate_signals method
        """
        
        # Get traditional signal (simplified version of original logic)
        current_price = df['close'].iloc[-1]
        rsi = indicators.get('rsi', pd.Series([50])).iloc[-1]
        macd = indicators.get('macd', pd.Series([0])).iloc[-1]
        macd_signal = indicators.get('macd_signal', pd.Series([0])).iloc[-1]
        macd_histogram = indicators.get('macd_histogram', pd.Series([0])).iloc[-1]
        vwap = indicators.get('vwap', pd.Series([current_price])).iloc[-1]
        
        # Traditional signal logic (simplified)
        traditional_signal = 0
        traditional_strength = 0
        reasons = []
        
        # RSI conditions
        if rsi < 30:
            traditional_signal += 1
            traditional_strength += 1
            reasons.append("RSI oversold")
        elif rsi > 70:
            traditional_signal -= 1
            traditional_strength += 1
            reasons.append("RSI overbought")
        
        # MACD conditions
        if macd > macd_signal:
            traditional_signal += 1
            traditional_strength += 1
            reasons.append("MACD bullish")
        else:
            traditional_signal -= 1
            traditional_strength += 1
            reasons.append("MACD bearish")
        
        # Price vs VWAP
        if current_price > vwap:
            traditional_signal += 1
            reasons.append("Price above VWAP")
        else:
            traditional_signal -= 1
            reasons.append("Price below VWAP")
        
        # Normalize signal
        traditional_signal = max(-1, min(1, traditional_signal))
        
        # Prepare indicators for RL
        indicator_dict = {
            'price': current_price,
            'rsi': rsi,
            'macd': macd,
            'macd_histogram': macd_histogram,
            'vwap': vwap,
            'ema_9': indicators.get('ema_9', pd.Series([current_price])).iloc[-1],
            'ema_21': indicators.get('ema_21', pd.Series([current_price])).iloc[-1]
        }
        
        # Get enhanced decision
        enhanced_decision = rl_decision.make_enhanced_decision(
            indicator_dict,
            {
                'signal': traditional_signal,
                'strength': traditional_strength,
                'reasons': reasons
            }
        )
        
        return enhanced_decision
    
    return enhanced_generate_signals, rl_decision

# Integration test
def test_rl_integration():
    """Test the RL integration"""
    
    logger.info("🧪 Testing RL Integration...")
    
    enhanced_signals, rl_decision = create_rl_enhanced_signal_function()
    
    # Mock data for testing
    import pandas as pd
    
    test_df = pd.DataFrame({
        'close': [3.68, 3.69, 3.67, 3.68]
    })
    
    test_indicators = {
        'rsi': pd.Series([45, 46, 44, 45]),
        'macd': pd.Series([-0.01, -0.008, -0.012, -0.01]),
        'macd_signal': pd.Series([-0.015, -0.013, -0.017, -0.015]),
        'macd_histogram': pd.Series([0.005, 0.005, 0.005, 0.005]),
        'vwap': pd.Series([3.70, 3.70, 3.69, 3.70]),
        'ema_9': pd.Series([3.65, 3.66, 3.64, 3.65]),
        'ema_21': pd.Series([3.67, 3.67, 3.66, 3.67])
    }
    
    # Test enhanced signal generation
    result = enhanced_signals(test_df, test_indicators)
    
    logger.info("🎯 Test Results:")
    logger.info(f"Final Signal: {result['signal']}")
    logger.info(f"Signal Strength: {result['strength']}")
    logger.info(f"Decision Source: {result['decision_source']}")
    logger.info(f"Risk Level: {result['risk_level']}")
    logger.info(f"RL Action: {result['rl_action']}")
    logger.info(f"RL Confidence: {result['rl_confidence']:.1%}")
    logger.info("Reasons:")
    for reason in result['reasons']:
        logger.info(f"  • {reason}")
    
    return result

if __name__ == "__main__":
    test_rl_integration()