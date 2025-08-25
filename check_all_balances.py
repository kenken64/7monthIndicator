#!/usr/bin/env python3
"""
Check all account balances to debug why USDC is not showing
"""
import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

try:
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    client = Client(api_key, secret_key, testnet=False)
    
    print("🔍 CHECKING ALL ACCOUNT BALANCES...")
    print("=" * 50)
    
    # Check Spot account
    print("\n💰 SPOT ACCOUNT BALANCES:")
    try:
        account = client.get_account()
        non_zero_balances = []
        
        for asset in account['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            total = free + locked
            
            if total > 0.00001:  # Show balances > 0.00001
                non_zero_balances.append({
                    'asset': asset['asset'],
                    'free': free,
                    'locked': locked,
                    'total': total
                })
        
        if non_zero_balances:
            for balance in sorted(non_zero_balances, key=lambda x: x['total'], reverse=True):
                print(f"  {balance['asset']}: Total={balance['total']:.8f} (Free={balance['free']:.8f}, Locked={balance['locked']:.8f})")
        else:
            print("  No non-zero spot balances found")
            
    except Exception as e:
        print(f"  ❌ Error getting spot balances: {e}")
    
    # Check Futures account
    print("\n🚀 FUTURES ACCOUNT BALANCES:")
    try:
        futures_account = client.futures_account()
        total_balance = float(futures_account['totalWalletBalance'])
        available_balance = float(futures_account['availableBalance'])
        unrealized_pnl = float(futures_account['totalUnrealizedProfit'])
        
        print(f"  Total Wallet Balance: ${total_balance:.8f}")
        print(f"  Available Balance: ${available_balance:.8f}")  
        print(f"  Unrealized PnL: ${unrealized_pnl:.8f}")
        
        # Show individual asset balances
        for asset in futures_account['assets']:
            balance = float(asset['walletBalance'])
            if balance > 0.00001:
                print(f"  {asset['asset']}: ${balance:.8f}")
                
    except Exception as e:
        print(f"  ❌ Error getting futures balances: {e}")
    
    # Check if account has any positions
    print("\n📊 CURRENT POSITIONS:")
    try:
        positions = client.futures_position_information()
        active_positions = []
        
        for pos in positions:
            amt = float(pos['positionAmt'])
            if abs(amt) > 0.00001:
                active_positions.append(pos)
        
        if active_positions:
            for pos in active_positions:
                print(f"  {pos['symbol']}: {pos['positionAmt']} @ ${pos['entryPrice']} (PnL: ${pos['unRealizedProfit']})")
        else:
            print("  No active positions")
            
    except Exception as e:
        print(f"  ❌ Error getting positions: {e}")
    
    print("\n" + "=" * 50)
    print("💡 SUMMARY:")
    print("If you see 4 USDC in the Binance app but not here,")
    print("it might be in:")
    print("- Savings/Earn products")
    print("- Cross/Isolated margin")
    print("- Funding wallet")
    print("- Different API key permissions")
    
except Exception as e:
    print(f"❌ Connection error: {e}")