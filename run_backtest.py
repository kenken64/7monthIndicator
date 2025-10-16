"""
Quick runner script for backtesting
Checks available data and runs backtest
"""

import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig, run_weight_optimization

def check_available_data(db_path='trading_bot.db'):
    """Check what data is available in the database"""
    conn = sqlite3.connect(db_path)

    print("\n" + "="*80)
    print("DATABASE ANALYSIS")
    print("="*80)

    # Check signals table
    query = """
        SELECT
            symbol,
            COUNT(*) as signal_count,
            MIN(timestamp) as first_signal,
            MAX(timestamp) as last_signal,
            AVG(CASE WHEN signal = 1 THEN 1 ELSE 0 END) * 100 as buy_pct,
            AVG(CASE WHEN signal = -1 THEN 1 ELSE 0 END) * 100 as sell_pct,
            AVG(CASE WHEN signal = 0 THEN 1 ELSE 0 END) * 100 as hold_pct,
            AVG(CASE WHEN rl_enhanced = 1 THEN 1 ELSE 0 END) * 100 as rl_enhanced_pct
        FROM signals
        GROUP BY symbol
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("\n❌ No signals found in database!")
        print("The backtest requires historical signal data.")
        print("\nPlease run the trading bot for a period to collect signals, or import historical data.")
        conn.close()
        return False

    print("\nSIGNALS DATA:")
    print(df.to_string(index=False))

    # Check trades table
    query = """
        SELECT
            symbol,
            COUNT(*) as trade_count,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
            SUM(pnl) as total_pnl
        FROM trades
        WHERE pnl IS NOT NULL
        GROUP BY symbol
    """

    df_trades = pd.read_sql_query(query, conn)

    if not df_trades.empty:
        print("\nTRADES DATA:")
        print(df_trades.to_string(index=False))
    else:
        print("\n⚠️  No completed trades found in database (only signals available)")

    # Get date range for most recent data
    query = "SELECT symbol, MIN(timestamp) as start, MAX(timestamp) as end FROM signals GROUP BY symbol"
    df_range = pd.read_sql_query(query, conn)

    print("\n" + "="*80)
    print("AVAILABLE DATE RANGES:")
    print("="*80)
    for _, row in df_range.iterrows():
        print(f"\n{row['symbol']}:")
        print(f"  Start: {row['start']}")
        print(f"  End:   {row['end']}")

        # Calculate data duration
        try:
            start = datetime.fromisoformat(row['start'].replace('Z', ''))
            end = datetime.fromisoformat(row['end'].replace('Z', ''))
            duration = end - start
            print(f"  Duration: {duration.days} days, {duration.seconds // 3600} hours")
        except:
            print(f"  Duration: Unable to calculate")

    conn.close()
    print("\n" + "="*80)

    return True


def run_quick_backtest(symbol='SUIUSDC', days_back=30):
    """Run a quick backtest on recent data"""

    # Check data availability first
    if not check_available_data():
        return

    # Try to get actual date range from database
    conn = sqlite3.connect('trading_bot.db')
    try:
        query = "SELECT MIN(timestamp) as start, MAX(timestamp) as end FROM signals WHERE symbol = ?"
        df = pd.read_sql_query(query, conn, params=[symbol])
        if not df.empty and df.iloc[0]['start']:
            start_date = df.iloc[0]['start'].split(' ')[0]
            end_date = df.iloc[0]['end'].split(' ')[0]
        else:
            # Fallback to date range
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    finally:
        conn.close()

    # Use fallback if still no dates
    if not start_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    print("\n" + "="*80)
    print(f"RUNNING QUICK BACKTEST: {symbol}")
    print(f"Period: {start_date} to {end_date} ({days_back} days)")
    print("="*80 + "\n")

    # Run backtest with default weights
    backtester = UnifiedSignalBacktester()
    config = BacktestConfig(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000.0,
        position_size_pct=0.10,
        stop_loss_pct=0.03,
        take_profit_pct=0.06
    )

    result = backtester.run_backtest(config)

    return result


def run_full_optimization(symbol='SUIUSDC', days_back=30):
    """Run full weight optimization"""

    # Check data availability first
    if not check_available_data():
        return

    # Calculate date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    print("\n" + "="*80)
    print(f"RUNNING WEIGHT OPTIMIZATION: {symbol}")
    print(f"Period: {start_date} to {end_date} ({days_back} days)")
    print("="*80 + "\n")

    results_df = run_weight_optimization(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000.0
    )

    # Save results to CSV
    output_file = f"backtest_results_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to: {output_file}")

    return results_df


if __name__ == "__main__":
    import sys

    print("\n" + "="*80)
    print("UNIFIED SIGNAL AGGREGATOR BACKTESTING")
    print("="*80)

    if len(sys.argv) > 1 and sys.argv[1] == 'optimize':
        # Run optimization
        run_full_optimization(symbol='SUIUSDC', days_back=30)
    elif len(sys.argv) > 1 and sys.argv[1] == 'check':
        # Just check data
        check_available_data()
    else:
        # Run quick backtest
        run_quick_backtest(symbol='SUIUSDC', days_back=30)

    print("\n" + "="*80)
    print("USAGE:")
    print("  python run_backtest.py           # Run quick backtest")
    print("  python run_backtest.py check     # Check available data")
    print("  python run_backtest.py optimize  # Run weight optimization")
    print("="*80 + "\n")
