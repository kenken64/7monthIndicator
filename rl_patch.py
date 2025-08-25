#!/usr/bin/env python3
"""
RL Trading Bot Patch
Simple patch to enhance existing trading bot with RL capabilities
"""

import os
import sys
import logging
from lightweight_rl import LightweightRLSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RLEnhancedDecision:
    """
    Simple RL enhancement that can be dropped into existing trading bot
    """
    
    def __init__(self):
        self.rl_system = LightweightRLSystem()
        self.rl_system.agent.load_model()
        logger.info("🤖 RL Enhancement System Initialized")
    
    def enhance_signal_decision(self, original_signal_data, indicators_dict):
        """
        Enhance original signal decision with RL input
        
        Args:
            original_signal_data: Original signal result from trading bot
            indicators_dict: Technical indicators dictionary
            
        Returns:
            Enhanced decision with risk management
        """
        
        # Get RL recommendation
        rl_rec = self.rl_system.get_trading_recommendation(indicators_dict)
        
        # Original signal
        original_signal = original_signal_data.get('signal', 0)
        original_strength = original_signal_data.get('strength', 0)
        
        # Enhanced decision logic
        enhanced_decision = self._make_enhanced_decision(
            original_signal, original_strength, rl_rec
        )
        
        # Log the decision process
        logger.info(f"📊 ENHANCED DECISION:")
        logger.info(f"   Original: Signal={original_signal}, Strength={original_strength}")
        logger.info(f"   RL: Action={rl_rec['action']}, Confidence={rl_rec['confidence']:.1%}")
        logger.info(f"   Final: Signal={enhanced_decision['signal']}, Strength={enhanced_decision['strength']}")
        logger.info(f"   Reason: {enhanced_decision['reason']}")
        
        return enhanced_decision
    
    def _make_enhanced_decision(self, original_signal, original_strength, rl_rec):
        """Make enhanced trading decision"""
        
        # Given the 7% win rate, be EXTREMELY conservative
        
        # If RL strongly suggests HOLD, override everything
        if rl_rec['action'] == 'HOLD' and rl_rec['confidence'] > 0.7:
            return {
                'signal': 0,
                'strength': 0,
                'reason': f"RL override: HOLD with {rl_rec['confidence']:.1%} confidence",
                'risk_level': 'MINIMAL'
            }
        
        # If both systems agree and confidence is high
        rl_signal_map = {'BUY': 1, 'SELL': -1, 'HOLD': 0, 'CLOSE': 0}
        rl_signal = rl_signal_map.get(rl_rec['action'], 0)
        
        if (original_signal == rl_signal and 
            original_signal != 0 and 
            rl_rec['confidence'] > 0.5 and 
            original_strength >= 1):
            
            # Both agree with high confidence - but still be cautious
            return {
                'signal': original_signal,
                'strength': min(2, original_strength - 1),  # Reduce strength
                'reason': f"Agreement: Both suggest {rl_rec['action']} (reduced risk)",
                'risk_level': 'LOW'
            }
        
        # Default to HOLD for safety
        return {
            'signal': 0,
            'strength': 0,
            'reason': f"Safety first: Original={original_signal}, RL={rl_rec['action']}, insufficient confidence",
            'risk_level': 'MINIMAL'
        }
    
    def should_use_smaller_position(self, enhanced_decision):
        """Recommend much smaller position sizes"""
        
        return 0.25 # 25%
    
    def check_exit_conditions(self, current_position_info, current_price):
        """Enhanced exit condition checking"""
        
        if not current_position_info:
            return {'should_exit': False, 'reason': 'No position'}
        
        entry_price = current_position_info.get('entry_price', current_price)
        side = current_position_info.get('side', 'LONG')
        
        # Calculate P&L
        if side == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Strict risk management (much tighter than original)
        if pnl_pct < -0.04:  # 4% loss
            return {
                'should_exit': True,
                'reason': f'Stop loss: {pnl_pct:.1%} loss exceeds 4% limit'
            }
        
        if pnl_pct > 0.08:  # 8% profit
            return {
                'should_exit': True,
                'reason': f'Take profit: {pnl_pct:.1%} gain exceeds 8% limit'
            }
        
        return {'should_exit': False, 'reason': f'Position OK: {pnl_pct:.1%} P&L'}

# Simple integration function that can be imported
def create_rl_enhanced_bot():
    """
    Create RL enhanced version of trading bot
    This can be imported and used to replace signal generation
    """
    
    rl_enhancer = RLEnhancedDecision()
    
    def enhanced_signal_generator(original_signal_data, indicators):
        """
        Drop-in replacement for signal generation
        """
        
        # Convert indicators to simple dict
        indicator_dict = {}
        current_price = indicators.get('close', 3.7)
        
        if hasattr(current_price, 'iloc'):
            current_price = current_price.iloc[-1]
        
        indicator_dict['price'] = current_price
        
        # Extract other indicators safely
        for key in ['rsi', 'macd', 'macd_histogram', 'vwap', 'ema_9', 'ema_21']:
            if key in indicators:
                val = indicators[key]
                if hasattr(val, 'iloc'):
                    val = val.iloc[-1]
                indicator_dict[key] = val
            else:
                indicator_dict[key] = current_price if 'ema' in key or key == 'vwap' else 50 if key == 'rsi' else 0
        
        # Get enhanced decision
        enhanced = rl_enhancer.enhance_signal_decision(original_signal_data, indicator_dict)
        
        return enhanced
    
    return enhanced_signal_generator, rl_enhancer

# Test the system
def test_rl_enhancement():
    """Test RL enhancement system"""
    
    logger.info("🧪 Testing RL Enhancement System...")
    
    enhanced_generator, rl_enhancer = create_rl_enhanced_bot()
    
    # Test data
    original_signal = {
        'signal': -1,
        'strength': 4,
        'reasons': ['MACD bearish', 'Price below VWAP']
    }
    
    test_indicators = {
        'price': 3.68,
        'rsi': 45,
        'macd': -0.01,
        'macd_histogram': 0.005,
        'vwap': 3.70,
        'ema_9': 3.65,
        'ema_21': 3.67
    }
    
    # Test enhancement
    result = enhanced_generator(original_signal, test_indicators)
    
    # Test position sizing
    recommended_size = rl_enhancer.should_use_smaller_position(result)
    
    logger.info(f"💡 ENHANCEMENT RESULTS:")
    logger.info(f"   Recommended Position Size: {recommended_size:.1%}")
    logger.info(f"   vs Original 51% (0.51) - {(51/100) / recommended_size:.0f}x smaller!")
    
    # Test exit conditions
    test_position = {
        'entry_price': 3.70,
        'side': 'SELL'
    }
    
    exit_check = rl_enhancer.check_exit_conditions(test_position, 3.68)
    logger.info(f"   Exit Recommendation: {exit_check}")
    
    return result

if __name__ == "__main__":
    test_rl_enhancement()