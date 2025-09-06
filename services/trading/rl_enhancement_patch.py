
# RL Enhancement Patch - Add this to your existing trading_bot.py

from rl_patch import create_rl_enhanced_bot

class RLEnhancedBinanceFuturesBot(BinanceFuturesBot):
    """RL-Enhanced version of BinanceFuturesBot"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize RL enhancement
        self.rl_generator, self.rl_enhancer = create_rl_enhanced_bot()
        
        # Override risky settings
        self.position_percentage = 2.0  # 2% instead of 51%
        self.take_profit_percent = 1.0  # 1% instead of 2%
        self.stop_loss_percent = 1.5    # 1.5% instead of 3%
        
        logger.info("🤖 RL Enhancement: Activated")
        logger.info(f"📉 Position size: {self.position_percentage}% (was 51%)")
    
    def generate_signals(self, df, indicators):
        """Enhanced signal generation"""
        
        # Get original signal
        original_signal = super().generate_signals(df, indicators)
        
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
        
        # Enhance with RL
        enhanced = self.rl_generator(original_signal, indicator_dict)
        
        # Return enhanced signal
        return {
            'signal': enhanced['signal'],
            'strength': enhanced['strength'],
            'reasons': [enhanced['reason']],
            'indicators': original_signal['indicators'],
            'rl_enhanced': True
        }
