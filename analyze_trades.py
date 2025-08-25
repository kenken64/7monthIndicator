#!/usr/bin/env python3
"""
Trading Analysis Script
Analyze stored signals and trades from SQLite database
"""

import argparse
import pandas as pd
from datetime import datetime, timedelta
from database import get_database
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    parser = argparse.ArgumentParser(description='Analyze trading bot performance')
    parser.add_argument('--symbol', default='SUIUSDC', help='Trading symbol to analyze')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--export', action='store_true', help='Export data to CSV')
    parser.add_argument('--plot', action='store_true', help='Generate performance plots')
    
    args = parser.parse_args()
    
    # Initialize database
    db = get_database()
    
    print(f"📊 Analyzing {args.symbol} performance for last {args.days} days")
    print("=" * 60)
    
    # Performance metrics
    performance = db.calculate_performance_metrics(args.symbol, args.days)
    
    if performance.get('total_trades', 0) > 0:
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Winning Trades: {performance['winning_trades']}")
        print(f"Losing Trades: {performance['losing_trades']}")
        print(f"Win Rate: {performance['win_rate']:.2f}%")
        print(f"Total PnL: ${performance['total_pnl']:.2f}")
        print(f"Average Win: ${performance['avg_win']:.2f}")
        print(f"Average Loss: ${performance['avg_loss']:.2f}")
        print(f"Max Loss: ${performance['max_loss']:.2f}")
        
        # Risk-Reward Ratio
        if performance['avg_loss'] != 0:
            rr_ratio = abs(performance['avg_win'] / performance['avg_loss'])
            print(f"Risk-Reward Ratio: 1:{rr_ratio:.2f}")
    else:
        print("No completed trades found for the specified period.")
    
    print()
    
    # Recent signals
    print("🎯 Recent Signals:")
    signals = db.get_recent_signals(args.symbol, 10)
    if signals:
        for signal in signals[:5]:  # Show last 5
            executed = "✅" if signal['executed'] else "⏳"
            print(f"{executed} {signal['timestamp']}: Signal {signal['signal']} "
                 f"(Strength: {signal['strength']}) @ ${signal['price']:.4f}")
    else:
        print("No recent signals found.")
    
    print()
    
    # Recent trades
    print("💰 Recent Trades:")
    trades = db.get_recent_trades(args.symbol, 10)
    if trades:
        for trade in trades[:5]:  # Show last 5
            status_emoji = "🟢" if trade['status'] == 'CLOSED' else "🔵"
            pnl_str = f"${trade['pnl']:.2f}" if trade['pnl'] else "Open"
            print(f"{status_emoji} {trade['timestamp']}: {trade['side']} "
                 f"{trade['quantity']:.4f} @ ${trade['entry_price']:.4f} "
                 f"(PnL: {pnl_str})")
    else:
        print("No recent trades found.")
    
    print()
    
    # Open positions
    open_trades = db.get_open_trades(args.symbol)
    if open_trades:
        print("🔵 Open Positions:")
        for trade in open_trades:
            print(f"   {trade['side']} {trade['quantity']:.4f} @ ${trade['entry_price']:.4f}")
    else:
        print("🔴 No open positions")
    
    # Export data if requested
    if args.export:
        print("\n📁 Exporting data to CSV files...")
        signals_file = db.export_data('signals', f'{args.symbol}_signals.csv')
        trades_file = db.export_data('trades', f'{args.symbol}_trades.csv')
        if signals_file and trades_file:
            print(f"   Signals exported to: {signals_file}")
            print(f"   Trades exported to: {trades_file}")
    
    # Generate plots if requested
    if args.plot and performance.get('total_trades', 0) > 0:
        print("\n📈 Generating performance plots...")
        generate_plots(db, args.symbol, args.days)

def generate_plots(db, symbol, days):
    """Generate performance visualization plots"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Get trade data
        with db.get_connection() as conn:
            trades_df = pd.read_sql_query('''
                SELECT * FROM trades 
                WHERE symbol = ? AND status = 'CLOSED' 
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp
            '''.format(days), conn, params=(symbol,))
        
        if trades_df.empty:
            print("No closed trades to plot")
            return
        
        # Convert timestamp to datetime
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{symbol} Trading Performance - Last {days} Days', fontsize=16)
        
        # 1. Cumulative PnL
        ax1.plot(trades_df['timestamp'], trades_df['cumulative_pnl'])
        ax1.set_title('Cumulative PnL')
        ax1.set_ylabel('PnL ($)')
        ax1.grid(True)
        
        # 2. PnL Distribution
        ax2.hist(trades_df['pnl'], bins=20, alpha=0.7, edgecolor='black')
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        ax2.set_title('PnL Distribution')
        ax2.set_xlabel('PnL ($)')
        ax2.set_ylabel('Frequency')
        
        # 3. Win/Loss by Side
        win_loss = trades_df.groupby(['side', trades_df['pnl'] > 0]).size().unstack(fill_value=0)
        win_loss.plot(kind='bar', ax=ax3, stacked=True)
        ax3.set_title('Win/Loss by Trade Side')
        ax3.set_ylabel('Number of Trades')
        ax3.legend(['Loss', 'Win'])
        
        # 4. Trade Size Distribution
        ax4.hist(trades_df['quantity'], bins=15, alpha=0.7, edgecolor='black')
        ax4.set_title('Trade Size Distribution')
        ax4.set_xlabel('Quantity')
        ax4.set_ylabel('Frequency')
        
        plt.tight_layout()
        
        # Save plot
        filename = f'{symbol}_performance_{datetime.now().strftime("%Y%m%d")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   Plot saved to: {filename}")
        
        # Show plot if in interactive environment
        try:
            plt.show()
        except:
            pass  # Non-interactive environment
            
    except ImportError:
        print("matplotlib and seaborn required for plotting. Install with:")
        print("pip install matplotlib seaborn")
    except Exception as e:
        print(f"Error generating plots: {e}")

if __name__ == "__main__":
    main()