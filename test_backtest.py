#!/usr/bin/env python3
"""Test backtest to debug why no trades are being generated"""

from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig
from datetime import datetime, timedelta
import sqlite3

# Check which database has data
print("Checking databases...")

# Check local database
try:
    conn = sqlite3.connect('data/trading_bot.db')
    cursor = conn.execute('SELECT COUNT(*) as count FROM signals WHERE symbol = "SUIUSDC"')
    local_count = cursor.fetchone()[0]
    print(f"Local database (data/trading_bot.db): {local_count} signals")
    conn.close()
except Exception as e:
    print(f"Local database error: {e}")
    local_count = 0

# Check shared database
try:
    conn = sqlite3.connect('shared/databases/trading_bot.db')
    cursor = conn.execute('SELECT COUNT(*) as count FROM signals WHERE symbol = "SUIUSDC"')
    shared_count = cursor.fetchone()[0]
    print(f"Shared database (shared/databases/trading_bot.db): {shared_count} signals")

    # Check date range
    cursor = conn.execute('SELECT MIN(timestamp), MAX(timestamp) FROM signals WHERE symbol = "SUIUSDC"')
    result = cursor.fetchone()
    print(f"Date range: {result[0]} to {result[1]}")

    # Check signal distribution
    cursor = conn.execute('SELECT signal, COUNT(*) FROM signals WHERE symbol = "SUIUSDC" GROUP BY signal')
    for row in cursor.fetchall():
        signal_type = 'BUY' if row[0] > 0 else 'SELL' if row[0] < 0 else 'HOLD'
        print(f"  {signal_type}: {row[1]}")

    conn.close()
except Exception as e:
    print(f"Shared database error: {e}")
    shared_count = 0

# Use the database with more data
db_path = 'shared/databases/trading_bot.db' if shared_count > local_count else 'data/trading_bot.db'
print(f"\nUsing database: {db_path}")

# Create config
config = BacktestConfig(
    symbol='SUIUSDC',
    start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
    end_date=datetime.now().strftime('%Y-%m-%d'),
    initial_balance=10000.0,
    buy_threshold=5.5,
    sell_threshold=4.5,
    min_confidence=0.0
)

print(f"\nRunning backtest...")
print(f"Config: {config}")

# Run backtest
backtester = UnifiedSignalBacktester(db_path=db_path)
result = backtester.run_backtest(config)

print("\n" + "="*80)
print("RESULTS:")
print("="*80)
print(f"Total Trades: {result.total_trades}")
print(f"Win Rate: {result.win_rate:.1f}%")
print(f"ROI: {result.roi:.2f}%")
print(f"Total PnL: ${result.total_pnl:.2f}")
print(f"Final Balance: ${result.final_balance:.2f}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown_pct:.1f}%")

if result.total_trades > 0:
    print(f"\nFirst 5 trades:")
    for i, trade in enumerate(result.trades[:5], 1):
        print(f"{i}. {trade['entry_time']} -> {trade['exit_time']} | {trade['side']} | PnL: ${trade['pnl']:.2f}")
else:
    print("\nNo trades executed. This is the problem!")
