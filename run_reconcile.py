#!/usr/bin/env python3
"""
Manual Position Reconciliation Tool
Reconciles database positions with actual Binance positions
"""

import sys
import os
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, '/root/7monthIndicator')

# Load environment variables
load_dotenv()

def run_reconcile():
    """Run position reconciliation manually"""
    try:
        print("🔄 Starting manual position reconciliation...")
        
        # Import the RL bot class
        from rl_bot_ready import RLEnhancedBinanceFuturesBot
        
        # Initialize bot (this won't start the trading loop)
        print("🤖 Initializing bot for reconciliation...")
        bot = RLEnhancedBinanceFuturesBot(
            symbol='SUIUSDC',
            leverage=50,
            position_percentage=2.0
        )
        
        print("🔍 Checking current positions...")
        
        # Get position info first
        position_info = bot.get_position_info()
        print(f"📊 Current Position: {position_info}")
        
        # Run reconciliation
        print("⚙️ Running reconciliation process...")
        bot.reconcile_positions()
        
        print("✅ Reconciliation completed!")
        
        # Show updated position info
        updated_position = bot.get_position_info()
        print(f"📊 Updated Position: {updated_position}")
        
    except Exception as e:
        print(f"❌ Reconciliation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_reconcile()
    sys.exit(0 if success else 1)