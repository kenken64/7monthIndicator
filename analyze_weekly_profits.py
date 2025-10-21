#!/usr/bin/env python3
"""
Analyze Binance position history to find largest profits for the week
"""
from binance.client import Client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from collections import defaultdict

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')

client = Client(api_key, secret_key, testnet=False)

# Get trades from the past week
week_ago = datetime.now() - timedelta(days=7)
start_time = int(week_ago.timestamp() * 1000)

print("=" * 100)
print("📊 BINANCE POSITION HISTORY - PAST 7 DAYS")
print("=" * 100)

# Get all trades from the past week
trades = client.futures_account_trades(
    symbol='SUIUSDC',
    startTime=start_time,
    limit=1000
)

print(f"\n📋 Total trades this week: {len(trades)}")

# Analyze trades by realized PnL
profitable_trades = []
losing_trades = []
total_realized_pnl = 0

for trade in trades:
    realized_pnl = float(trade['realizedPnl'])

    if realized_pnl > 0:
        profitable_trades.append({
            'timestamp': datetime.fromtimestamp(trade['time'] / 1000),
            'side': trade['side'],
            'qty': float(trade['qty']),
            'price': float(trade['price']),
            'pnl': realized_pnl,
            'commission': float(trade['commission'])
        })
    elif realized_pnl < 0:
        losing_trades.append({
            'timestamp': datetime.fromtimestamp(trade['time'] / 1000),
            'side': trade['side'],
            'qty': float(trade['qty']),
            'price': float(trade['price']),
            'pnl': realized_pnl,
            'commission': float(trade['commission'])
        })

    total_realized_pnl += realized_pnl

# Sort by PnL
profitable_trades.sort(key=lambda x: x['pnl'], reverse=True)
losing_trades.sort(key=lambda x: x['pnl'])

print(f"\n💰 Total Realized PnL This Week: ${total_realized_pnl:.2f}")
print(f"✅ Profitable trades: {len(profitable_trades)}")
print(f"❌ Losing trades: {len(losing_trades)}")

if profitable_trades:
    print("\n" + "=" * 100)
    print("🏆 TOP 10 MOST PROFITABLE TRADES THIS WEEK")
    print("=" * 100)
    print(f"{'Rank':<6} {'Date/Time':<20} {'Side':<6} {'Quantity':<10} {'Price':<10} {'PnL':<12} {'Note'}")
    print("=" * 100)

    for i, trade in enumerate(profitable_trades[:10], 1):
        note = ""
        if i == 1:
            note = "🥇 BEST"
        elif i == 2:
            note = "🥈"
        elif i == 3:
            note = "🥉"

        print(f"{i:<6} {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S'):<20} "
              f"{trade['side']:<6} {trade['qty']:<10.1f} ${trade['price']:<9.4f} "
              f"${trade['pnl']:<11.2f} {note}")

    # Analyze the best trade
    best_trade = profitable_trades[0]
    print("\n" + "=" * 100)
    print("🔍 DETAILED ANALYSIS OF BEST TRADE")
    print("=" * 100)
    print(f"📅 Date/Time:     {best_trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💹 Side:          {best_trade['side']}")
    print(f"📊 Quantity:      {best_trade['qty']:.1f} SUI")
    print(f"💵 Price:         ${best_trade['price']:.4f}")
    print(f"💰 Realized PnL:  ${best_trade['pnl']:.2f}")
    print(f"💸 Commission:    ${best_trade['commission']:.4f}")
    print(f"📈 Position Value: ${best_trade['qty'] * best_trade['price']:.2f}")

    # Calculate ROI
    position_value = best_trade['qty'] * best_trade['price']
    roi = (best_trade['pnl'] / position_value) * 100 if position_value > 0 else 0
    print(f"📊 ROI:           {roi:.2f}%")

    # Check if bot detected this opportunity
    print("\n🤖 Bot Analysis:")
    print(f"   Time of best trade: {best_trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Bot runs every 25 seconds, so it should have seen this price level.")
    print(f"   Check database signals around this time to see if bot generated a signal.")

if losing_trades:
    print("\n" + "=" * 100)
    print("❌ TOP 5 WORST TRADES THIS WEEK")
    print("=" * 100)
    print(f"{'Rank':<6} {'Date/Time':<20} {'Side':<6} {'Quantity':<10} {'Price':<10} {'Loss'}")
    print("=" * 100)

    for i, trade in enumerate(losing_trades[:5], 1):
        print(f"{i:<6} {best_trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S'):<20} "
              f"{trade['side']:<6} {trade['qty']:<10.1f} ${trade['price']:<9.4f} "
              f"${trade['pnl']:.2f}")

# Daily breakdown
print("\n" + "=" * 100)
print("📅 DAILY PnL BREAKDOWN")
print("=" * 100)

daily_pnl = defaultdict(float)
daily_trades = defaultdict(int)

for trade in trades:
    date = datetime.fromtimestamp(trade['time'] / 1000).date()
    pnl = float(trade['realizedPnl'])
    daily_pnl[date] += pnl
    if pnl != 0:  # Only count trades with realized PnL
        daily_trades[date] += 1

for date in sorted(daily_pnl.keys()):
    pnl = daily_pnl[date]
    count = daily_trades[date]
    emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⚪"
    print(f"{emoji} {date.strftime('%Y-%m-%d')} | Trades: {count:3d} | PnL: ${pnl:8.2f}")

print("\n" + "=" * 100)
