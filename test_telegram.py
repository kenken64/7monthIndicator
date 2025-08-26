#!/usr/bin/env python3
"""
Test Telegram Integration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, '/root/7monthIndicator')

# Import the TelegramNotifier from our bot
from rl_bot_ready import TelegramNotifier

def test_telegram():
    """Test Telegram bot integration"""
    print("🧪 Testing Telegram Integration...")
    
    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '@bnbfutura_bot')
    
    print(f"📱 Bot Token: {'✅ Set' if bot_token else '❌ Missing'}")
    print(f"📱 Chat ID: {chat_id}")
    
    if not bot_token:
        print("❌ Please set TELEGRAM_BOT_TOKEN in .env file")
        print("💡 Get your bot token from @BotFather on Telegram")
        return False
    
    # Initialize notifier
    telegram = TelegramNotifier()
    
    # Test basic message
    test_message = """<b>🧪 Telegram Integration Test</b>

This is a test message from the RL Trading Bot.

✅ If you see this message, the integration is working!
⏰ Test completed successfully."""
    
    print("📤 Sending test message...")
    success = telegram.send_message(test_message)
    
    if success:
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send test message")
        print("💡 Check your bot token and chat ID")
    
    # Test signal notification format
    print("📤 Testing signal notification format...")
    test_signal_data = {
        'signal': 1,
        'strength': 3,
        'rl_enhanced': True,
        'reasons': [
            'RSI oversold (28.5)',
            'MACD bullish crossover',
            'Price above VWAP (+1.2%)'
        ]
    }
    
    test_position_info = {
        'side': 'LONG',
        'size': 150.3,
        'unrealized_pnl': 2.45
    }
    
    success2 = telegram.send_signal_notification(test_signal_data, 3.4567, test_position_info)
    
    if success2:
        print("✅ Signal notification sent successfully!")
    else:
        print("❌ Failed to send signal notification")
    
    return success and success2

if __name__ == "__main__":
    test_telegram()