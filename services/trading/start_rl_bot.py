#!/usr/bin/env python3
"""
Start RL-Enhanced Trading Bot
"""

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    try:
        from trading_bot_integrated import BinanceFuturesBot
        
        print("🚀 Starting RL-Enhanced Trading Bot...")
        print("🛡️ Enhanced with:")
        print("   • Reinforcement Learning signal filtering")
        print("   • Reduced position sizes (2% max vs 51%)")
        print("   • Better risk management")
        print("   • Position reconciliation")
        print()
        
        # Create and run the bot
        bot = BinanceFuturesBot(
            symbol='SUIUSDC',
            position_percentage=2.0,  # Much safer than 51%
            leverage=50
        )
        
        bot.run(interval=300)  # 5 minutes
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
