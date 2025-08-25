#!/usr/bin/env python3
"""
Quick RL Position Analysis
"""
import sys
sys.path.append('/root/7monthIndicator')

from rl_patch import create_rl_enhanced_bot
from binance.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

# Get current price
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'), testnet=False)
ticker = client.get_symbol_ticker(symbol='SUIUSDC')
current_price = float(ticker['price'])

# Current position
entry_price = 3.6359
position_size = 73.8
side = 'SELL'  # SHORT

# Calculate current PnL
if side == 'SELL':
    pnl = (entry_price - current_price) * position_size
    pnl_percentage = ((entry_price - current_price) / entry_price) * 100
else:
    pnl = (current_price - entry_price) * position_size  
    pnl_percentage = ((current_price - entry_price) / entry_price) * 100

print(f"🎯 CURRENT POSITION ANALYSIS")
print(f"📍 Position: {side} {position_size} SUIUSDC")
print(f"💰 Entry: ${entry_price:.4f} | Current: ${current_price:.4f}")
print(f"📊 PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
print()

# Get RL recommendation
try:
    _, rl_enhancer = create_rl_enhanced_bot()
    
    position_data = {
        'entry_price': entry_price,
        'side': 'SELL' if side == 'SELL' else 'BUY',
        'size': position_size
    }
    
    exit_decision = rl_enhancer.check_exit_conditions(position_data, current_price)
    
    print(f"🤖 RL RECOMMENDATION:")
    print(f"Should Exit: {'✅ YES' if exit_decision['should_exit'] else '❌ NO'}")
    print(f"Reason: {exit_decision['reason']}")
    print(f"Confidence: {exit_decision['confidence']:.1f}%")
    
    if exit_decision['should_exit']:
        print(f"\n🚨 ACTION REQUIRED: Close position immediately")
        print(f"Expected outcome: Limit losses at {pnl_percentage:.2f}%")
    else:
        print(f"\n⏳ HOLD: RL suggests keeping position open")
        
except Exception as e:
    print(f"❌ RL analysis failed: {e}")