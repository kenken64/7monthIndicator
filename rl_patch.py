#!/usr/bin/env python3
"""
RL Trading Bot Patch

A drop-in enhancement module that integrates Reinforcement Learning capabilities
into existing trading bots. This patch provides:

- RL-enhanced signal decision making
- Conservative risk management with smaller position sizes
- Advanced exit condition monitoring
- Safety-first approach given historical performance data

The module can be imported and used to replace traditional signal generation
without major code restructuring.
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
    
    This class provides intelligent signal enhancement using a trained RL model.
    It combines traditional technical analysis signals with learned patterns
    to make more informed trading decisions while prioritizing capital preservation.
    
    Features:
    - Signal strength adjustment based on RL confidence
    - Conservative position sizing recommendations
    - Enhanced exit condition monitoring
    - Risk level assessment and management
    """
    
    def __init__(self):
        """Initialize RL enhancement system
        
        Loads the trained RL model and sets up the enhancement system
        with conservative default parameters.
        """
        self.rl_system = LightweightRLSystem()
        self.rl_system.agent.load_model()
        logger.info("🤖 RL Enhancement System Initialized")
    
    def enhance_signal_decision(self, original_signal_data, indicators_dict):
        """
        Enhance original signal decision with RL input
        
        Combines traditional technical analysis signals with RL recommendations
        to produce enhanced trading decisions. Emphasizes safety and capital
        preservation over aggressive trading.
        
        Args:
            original_signal_data: Original signal result from trading bot containing
                                signal direction, strength, and reasoning
            indicators_dict: Technical indicators dictionary with current market data
            
        Returns:
            Dict: Enhanced decision with:
                - signal: Direction (-1, 0, 1 for sell, hold, buy)
                - strength: Signal strength (0-5)
                - reason: Explanation of the decision
                - risk_level: Risk assessment (MINIMAL, LOW, MEDIUM, HIGH)
        """
        
        # Get RL recommendation from trained model
        rl_rec = self.rl_system.get_trading_recommendation(indicators_dict)
        
        # Extract original signal parameters
        original_signal = original_signal_data.get('signal', 0)
        original_strength = original_signal_data.get('strength', 0)
        
        # Apply RL enhancement logic with safety prioritization
        enhanced_decision = self._make_enhanced_decision(
            original_signal, original_strength, rl_rec
        )
        
        # Log the complete decision process for transparency and debugging
        logger.info(f"📊 ENHANCED DECISION:")
        logger.info(f"   Original: Signal={original_signal}, Strength={original_strength}")
        logger.info(f"   RL: Action={rl_rec['action']}, Confidence={rl_rec['confidence']:.1%}")
        logger.info(f"   Final: Signal={enhanced_decision['signal']}, Strength={enhanced_decision['strength']}")
        logger.info(f"   Reason: {enhanced_decision['reason']}")
        
        return enhanced_decision
    
    def _make_enhanced_decision(self, original_signal, original_strength, rl_rec):
        """Make enhanced trading decision using RL and traditional analysis
        
        Implements conservative decision logic that prioritizes capital preservation
        over aggressive trading, especially given historical low win rates.
        
        Args:
            original_signal: Traditional signal direction (-1, 0, 1)
            original_strength: Traditional signal strength (0-5)
            rl_rec: RL recommendation dictionary with action and confidence
            
        Returns:
            Dict: Enhanced decision with safety-first approach
        """
        
        # Given historical low win rate, prioritize extreme conservation
        
        # RL HOLD override - respect strong RL recommendation to avoid trades
        if rl_rec['action'] == 'HOLD' and rl_rec['confidence'] > 0.7:
            return {
                'signal': 0,
                'strength': 0,
                'reason': f"RL override: HOLD with {rl_rec['confidence']:.1%} confidence",
                'risk_level': 'MINIMAL'
            }
        
        # Agreement check - only trade when both traditional and RL systems align
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
        
        # Default to HOLD - safety-first approach when uncertain
        return {
            'signal': 0,
            'strength': 0,
            'reason': f"Safety first: Original={original_signal}, RL={rl_rec['action']}, insufficient confidence",
            'risk_level': 'MINIMAL'
        }
    
    def should_use_smaller_position(self, enhanced_decision):
        """Recommend much smaller position sizes for risk management
        
        Returns significantly reduced position sizes compared to traditional
        trading to minimize potential losses and preserve capital.
        
        Args:
            enhanced_decision: Enhanced decision dictionary (currently unused)
            
        Returns:
            float: Position size as percentage (0.25 = 25%)
        """
        
        # Return 0.25% (25% of original 1%) for extremely conservative sizing
        return 0.25
    
    def check_exit_conditions(self, current_position_info, current_price):
        """Enhanced exit condition checking with tight risk controls
        
        Monitors open positions and recommends exits based on strict risk
        management rules to prevent large losses.
        
        Args:
            current_position_info: Dictionary with position details (entry_price, side)
            current_price: Current market price
            
        Returns:
            Dict: Exit recommendation with 'should_exit' boolean and 'reason' string
        """
        
        if not current_position_info:
            return {'should_exit': False, 'reason': 'No position'}
        
        entry_price = current_position_info.get('entry_price', current_price)
        side = current_position_info.get('side', 'LONG')
        
        # Calculate current position P&L percentage
        if side == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Apply strict risk management with tight stop losses and profit targets
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
    
    Factory function that creates and returns the RL enhancement components.
    This provides a simple integration point for existing trading bots.
    
    Returns:
        Tuple: (enhanced_signal_generator_function, rl_enhancer_instance)
            - enhanced_signal_generator: Drop-in replacement for signal generation
            - rl_enhancer: RLEnhancedDecision instance for additional functionality
    """
    
    rl_enhancer = RLEnhancedDecision()
    
    def enhanced_signal_generator(original_signal_data, indicators):
        """
        Drop-in replacement for signal generation with RL enhancement
        
        This function can directly replace traditional signal generation
        in existing trading bots without requiring code restructuring.
        
        Args:
            original_signal_data: Traditional signal analysis results
            indicators: Dictionary or pandas Series of technical indicators
            
        Returns:
            Dict: Enhanced signal decision with RL improvements
        """
        
        # Convert pandas Series indicators to simple dictionary format
        indicator_dict = {}
        current_price = indicators.get('close', 3.7)
        
        if hasattr(current_price, 'iloc'):
            current_price = current_price.iloc[-1]
        
        indicator_dict['price'] = current_price
        
        # Safely extract technical indicators with fallback values
        for key in ['rsi', 'macd', 'macd_histogram', 'vwap', 'ema_9', 'ema_21']:
            if key in indicators:
                val = indicators[key]
                if hasattr(val, 'iloc'):
                    val = val.iloc[-1]
                indicator_dict[key] = val
            else:
                indicator_dict[key] = current_price if 'ema' in key or key == 'vwap' else 50 if key == 'rsi' else 0
        
        # Generate RL-enhanced trading decision
        enhanced = rl_enhancer.enhance_signal_decision(original_signal_data, indicator_dict)
        
        return enhanced
    
    return enhanced_signal_generator, rl_enhancer

# Test the system
def test_rl_enhancement():
    """Test RL enhancement system with sample data
    
    Validates the RL enhancement functionality using test market data
    and demonstrates the decision-making process.
    
    Returns:
        Dict: Test results showing enhanced decision output
    """
    
    logger.info("🧪 Testing RL Enhancement System...")
    
    enhanced_generator, rl_enhancer = create_rl_enhanced_bot()
    
    # Create sample test data for validation
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
    
    # Run enhancement test with sample data
    result = enhanced_generator(original_signal, test_indicators)
    
    # Test conservative position sizing recommendation
    recommended_size = rl_enhancer.should_use_smaller_position(result)
    
    logger.info(f"💡 ENHANCEMENT RESULTS:")
    logger.info(f"   Recommended Position Size: {recommended_size:.1%}")
    logger.info(f"   vs Original 51% (0.51) - {(51/100) / recommended_size:.0f}x smaller!")
    
    # Test exit condition monitoring with sample position
    test_position = {
        'entry_price': 3.70,
        'side': 'SELL'
    }
    
    exit_check = rl_enhancer.check_exit_conditions(test_position, 3.68)
    logger.info(f"   Exit Recommendation: {exit_check}")
    
    return result

if __name__ == "__main__":
    test_rl_enhancement()