#!/usr/bin/env python3
from binance.client import Client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')

client = Client(api_key, secret_key, testnet=False)

# Get recent trades
trades = client.futures_account_trades(symbol='SUIUSDC', limit=30)

print("Recent Binance Trades (Last 15):")
print("=" * 90)

for trade in reversed(trades[-15:]):
    timestamp = datetime.fromtimestamp(trade['time'] / 1000)
    side = trade['side']
    qty = float(trade['qty'])
    price = float(trade['price'])
    value = qty * price
    realized_pnl = float(trade['realizedPnl'])

    print(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {side:4s} | {qty:8.1f} @ ${price:.4f} | Val: ${value:7.2f} | PnL: ${realized_pnl:7.2f}")

print("\n" + "=" * 90)

# Find trades around $145.52 value
print("\nTrades with value between $140-$151:")
count = 0
for trade in trades:
    qty = float(trade['qty'])
    price = float(trade['price'])
    value = qty * price
    if 140 <= value <= 151:
        timestamp = datetime.fromtimestamp(trade['time'] / 1000)
        side = trade['side']
        realized_pnl = float(trade['realizedPnl'])
        print(f">>> {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {side} | {qty:.1f} @ ${price:.4f} | Value: ${value:.2f} | PnL: ${realized_pnl:.2f}")
        count += 1

if count == 0:
    print("No trades found in this value range")
