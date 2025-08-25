#!/usr/bin/env python3
"""
RL-Enhanced Trading Bot
Enhanced version of the original trading bot with RL integration
"""

# Import the enhanced decision system
from rl_patch import create_rl_enhanced_bot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_rl_enhanced_trading_bot_class():
    """
    Create RL-enhanced version of the existing TradingBot class
    This can replace the original TradingBot
    """
    
    # Import original trading bot
    import sys
    sys.path.append('/root/7monthIndicator')
    
    try:
        from trading_bot import TradingBot as OriginalTradingBot
        
        class RLEnhancedTradingBot(OriginalTradingBot):
            """
            Enhanced trading bot with RL capabilities
            """
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                # Initialize RL enhancement
                self.rl_generator, self.rl_enhancer = create_rl_enhanced_bot()
                
                # Override position percentage to be much smaller
                self.position_percentage = 2.0  # 2% instead of 51%
                
                logger.info("🤖 RL-Enhanced Trading Bot Initialized")
                logger.info(f"⚠️  Position size reduced from 51% to {self.position_percentage}%")
                logger.info("🛡️  Enhanced risk management active")
            
            def generate_signals(self, df, indicators):
                """
                Enhanced signal generation with RL integration
                """
                
                # Get original signal using parent method logic
                original_signal_data = self._get_original_signal(df, indicators)
                
                # Enhance with RL
                enhanced_decision = self.rl_generator(original_signal_data, indicators)
                
                # Return in format expected by trading bot
                return {
                    'signal': enhanced_decision['signal'],
                    'strength': enhanced_decision['strength'],
                    'reasons': [enhanced_decision['reason']],
                    'indicators': self._extract_indicator_values(indicators),
                    'rl_enhanced': True,
                    'risk_level': enhanced_decision['risk_level']
                }
            
            def _get_original_signal(self, df, indicators):
                """Get original signal using traditional logic"""
                
                signal = 0
                strength = 0
                reasons = []
                
                if len(df) < 50:
                    return {'signal': 0, 'strength': 0, 'reasons': ['Insufficient data']}
                
                current_price = df['close'].iloc[-1]
                
                # RSI analysis
                rsi = indicators['rsi'].iloc[-1]
                if rsi < 30:
                    signal += 1
                    strength += 2
                    reasons.append(f"RSI oversold ({rsi:.1f})")
                elif rsi > 70:
                    signal -= 1
                    strength += 2
                    reasons.append(f"RSI overbought ({rsi:.1f})")
                
                # MACD analysis
                macd = indicators['macd'].iloc[-1]
                macd_signal = indicators['macd_signal'].iloc[-1]
                macd_histogram = indicators['macd_histogram'].iloc[-1]
                
                if macd > macd_signal:
                    signal += 1
                    strength += 1
                    reasons.append("MACD bullish crossover")
                else:
                    signal -= 1
                    strength += 1
                    reasons.append("MACD bearish")
                
                # VWAP analysis
                vwap = indicators['vwap'].iloc[-1]
                if current_price > vwap:
                    signal += 1
                    reasons.append(f"Price above VWAP (${vwap:.4f})")
                else:
                    signal -= 1
                    reasons.append(f"Price below VWAP (${vwap:.4f})")
                
                # Normalize signal
                signal = max(-1, min(1, signal))
                
                return {
                    'signal': signal,
                    'strength': min(strength, 5),
                    'reasons': reasons
                }
            
            def _extract_indicator_values(self, indicators):
                """Extract indicator values for storage"""
                current_values = {}
                for key, series in indicators.items():
                    if hasattr(series, 'iloc'):
                        current_values[key] = series.iloc[-1]
                    else:
                        current_values[key] = series
                return current_values
            
            def execute_trade(self, signal_data, current_price):
                """
                Enhanced trade execution with better risk management
                """
                
                signal = signal_data['signal']
                strength = signal_data['strength']
                risk_level = signal_data.get('risk_level', 'LOW')
                
                if signal == 0:
                    logger.info("🛑 No trade signal - holding position")
                    return False
                
                # Dynamic position sizing based on risk level
                position_sizes = {
                    'MINIMAL': 0.5,  # 0.5%
                    'LOW': 1.0,      # 1.0%
                    'MEDIUM': 1.5,   # 1.5%
                    'HIGH': 2.0      # 2.0% max
                }
                
                adjusted_position_percentage = position_sizes.get(risk_level, 1.0)
                
                logger.info(f"🎯 RL-Enhanced Trade Execution:")
                logger.info(f"   Signal: {signal}, Strength: {strength}")
                logger.info(f"   Risk Level: {risk_level}")
                logger.info(f"   Position Size: {adjusted_position_percentage}% (vs original 51%)")
                
                # Temporarily override position percentage
                original_position_percentage = self.position_percentage
                self.position_percentage = adjusted_position_percentage
                
                try:
                    # Execute trade using parent method
                    result = super().execute_trade(signal_data, current_price)
                    
                    if result:
                        logger.info(f"✅ RL-Enhanced trade executed successfully")
                    
                    return result
                    
                finally:
                    # Restore original position percentage
                    self.position_percentage = original_position_percentage
            
            def should_close_position(self, current_price):
                """
                Enhanced position closing logic
                """
                
                # Get position info
                position_info = self.get_position_info()
                
                if not position_info['side'] or position_info['size'] == 0:
                    return False
                
                # Use RL enhancer for exit decision
                position_data = {
                    'entry_price': getattr(self, 'entry_price', current_price),
                    'side': 'LONG' if position_info['side'] == 'LONG' else 'SELL'
                }
                
                exit_decision = self.rl_enhancer.check_exit_conditions(position_data, current_price)
                
                if exit_decision['should_exit']:
                    logger.info(f"🚪 RL Exit Signal: {exit_decision['reason']}")
                    return True
                
                return False
            
            def run(self, interval: int = 300):
                """
                Enhanced main bot loop with RL integration
                """
                
                logger.info(f"🤖 Starting RL-Enhanced Trading Bot for {self.symbol}")
                logger.info(f"🛡️  Enhanced Risk Management: Max 2% position size")
                logger.info(f"🧠 RL Integration: Active with trained model")
                logger.info(f"📊 Historical Performance Fix: Addressing 7% win rate")
                
                # Run the original bot loop but with enhanced methods
                super().run(interval)
        
        return RLEnhancedTradingBot
        
    except ImportError as e:
        logger.error(f"❌ Could not import original trading bot: {e}")
        return None

# Usage example and testing
def main():
    """Test the RL-enhanced trading bot"""
    
    logger.info("🚀 Creating RL-Enhanced Trading Bot...")
    
    # Create enhanced bot class
    EnhancedBotClass = create_rl_enhanced_trading_bot_class()
    
    if EnhancedBotClass:
        logger.info("✅ RL-Enhanced Trading Bot class created successfully!")
        logger.info("🔧 To use: Replace 'TradingBot' with 'RLEnhancedTradingBot' in your code")
        logger.info("📈 Key improvements:")
        logger.info("   • RL-guided signal filtering")
        logger.info("   • Reduced position sizes (0.5%-2% vs 51%)")  
        logger.info("   • Enhanced risk management")
        logger.info("   • Improved exit strategies")
        logger.info("   • Historical failure pattern avoidance")
    else:
        logger.error("❌ Failed to create enhanced bot")

if __name__ == "__main__":
    main()