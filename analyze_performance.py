#!/usr/bin/env python3
"""
Performance Analysis Tool
Analyze trading bot performance and identify patterns for RL improvement
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from database import get_database
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self):
        self.db = get_database()
        self.trades_df = None
        self.signals_df = None
    
    def load_data(self):
        """Load trading data from database"""
        logger.info("📊 Loading trading data from database...")
        
        with self.db.get_connection() as conn:
            # Load trades
            trades_query = """
                SELECT t.*, s.signal, s.strength, s.reasons, s.indicators
                FROM trades t
                LEFT JOIN signals s ON t.signal_id = s.id
                ORDER BY t.timestamp
            """
            self.trades_df = pd.read_sql_query(trades_query, conn)
            
            # Load signals
            signals_query = """
                SELECT * FROM signals
                ORDER BY timestamp
            """
            self.signals_df = pd.read_sql_query(signals_query, conn)
        
        logger.info(f"✅ Loaded {len(self.trades_df)} trades and {len(self.signals_df)} signals")
        
        # Process data
        self.trades_df['timestamp'] = pd.to_datetime(self.trades_df['timestamp'])
        self.signals_df['timestamp'] = pd.to_datetime(self.signals_df['timestamp'])
        
        # Parse JSON fields
        if 'reasons' in self.signals_df.columns:
            self.signals_df['reasons'] = self.signals_df['reasons'].apply(
                lambda x: json.loads(x) if x else []
            )
        if 'indicators' in self.signals_df.columns:
            self.signals_df['indicators'] = self.signals_df['indicators'].apply(
                lambda x: json.loads(x) if x else {}
            )
    
    def analyze_trade_performance(self):
        """Analyze trade performance metrics"""
        logger.info("📈 Analyzing trade performance...")
        
        closed_trades = self.trades_df[self.trades_df['status'] == 'CLOSED'].copy()
        
        if len(closed_trades) == 0:
            logger.warning("⚠️ No closed trades to analyze")
            return
        
        # Basic performance metrics
        total_trades = len(closed_trades)
        winning_trades = len(closed_trades[closed_trades['pnl'] > 0])
        losing_trades = len(closed_trades[closed_trades['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100
        
        total_pnl = closed_trades['pnl'].sum()
        avg_win = closed_trades[closed_trades['pnl'] > 0]['pnl'].mean()
        avg_loss = closed_trades[closed_trades['pnl'] < 0]['pnl'].mean()
        
        max_win = closed_trades['pnl'].max()
        max_loss = closed_trades['pnl'].min()
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 else float('inf')
        
        logger.info("="*60)
        logger.info("📊 TRADING PERFORMANCE ANALYSIS")
        logger.info("="*60)
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Winning Trades: {winning_trades} ({win_rate:.1f}%)")
        logger.info(f"Losing Trades: {losing_trades} ({100-win_rate:.1f}%)")
        logger.info(f"Total PnL: ${total_pnl:.2f}")
        logger.info(f"Average Win: ${avg_win:.2f}")
        logger.info(f"Average Loss: ${avg_loss:.2f}")
        logger.info(f"Max Win: ${max_win:.2f}")
        logger.info(f"Max Loss: ${max_loss:.2f}")
        logger.info(f"Profit Factor: {profit_factor:.2f}")
        logger.info("="*60)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    def analyze_signal_patterns(self):
        """Analyze signal effectiveness"""
        logger.info("🎯 Analyzing signal patterns...")
        
        # Merge trades with signals to analyze effectiveness
        merged_df = self.trades_df.merge(
            self.signals_df, 
            left_on='signal_id', 
            right_on='id', 
            suffixes=('_trade', '_signal'),
            how='left'
        )
        
        closed_merged = merged_df[merged_df['status'] == 'CLOSED'].copy()
        
        if len(closed_merged) == 0:
            logger.warning("⚠️ No closed trades with signals to analyze")
            return
        
        # Analyze by signal strength
        logger.info("\n📊 Performance by Signal Strength:")
        strength_analysis = closed_merged.groupby('strength').agg({
            'pnl': ['count', 'mean', 'sum'],
            'pnl_percentage': 'mean'
        }).round(2)
        
        for strength in strength_analysis.index:
            count = strength_analysis.loc[strength, ('pnl', 'count')]
            avg_pnl = strength_analysis.loc[strength, ('pnl', 'mean')]
            total_pnl = strength_analysis.loc[strength, ('pnl', 'sum')]
            avg_pct = strength_analysis.loc[strength, ('pnl_percentage', 'mean')]
            logger.info(f"  Strength {strength}: {count} trades, Avg PnL: ${avg_pnl:.2f}, Total: ${total_pnl:.2f}, Avg %: {avg_pct:.2f}%")
        
        # Analyze by signal type
        logger.info("\n📊 Performance by Signal Type:")
        signal_analysis = closed_merged.groupby('signal').agg({
            'pnl': ['count', 'mean', 'sum'],
            'pnl_percentage': 'mean'
        }).round(2)
        
        signal_names = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
        for signal in signal_analysis.index:
            if pd.notna(signal):
                count = signal_analysis.loc[signal, ('pnl', 'count')]
                avg_pnl = signal_analysis.loc[signal, ('pnl', 'mean')]
                total_pnl = signal_analysis.loc[signal, ('pnl', 'sum')]
                avg_pct = signal_analysis.loc[signal, ('pnl_percentage', 'mean')]
                signal_name = signal_names.get(int(signal), f'Signal_{signal}')
                logger.info(f"  {signal_name}: {count} trades, Avg PnL: ${avg_pnl:.2f}, Total: ${total_pnl:.2f}, Avg %: {avg_pct:.2f}%")
    
    def analyze_indicator_effectiveness(self):
        """Analyze which indicators lead to better trades"""
        logger.info("🔍 Analyzing indicator effectiveness...")
        
        merged_df = self.trades_df.merge(
            self.signals_df, 
            left_on='signal_id', 
            right_on='id', 
            suffixes=('_trade', '_signal'),
            how='left'
        )
        
        closed_merged = merged_df[merged_df['status'] == 'CLOSED'].copy()
        
        if len(closed_merged) == 0:
            return
        
        # Extract indicator values for winning vs losing trades
        winning_trades = closed_merged[closed_merged['pnl'] > 0]
        losing_trades = closed_merged[closed_merged['pnl'] < 0]
        
        if len(winning_trades) > 0 and len(losing_trades) > 0:
            logger.info("\n📊 Indicator Analysis (Winning vs Losing Trades):")
            
            # Get indicator data
            winning_indicators = []
            losing_indicators = []
            
            for _, trade in winning_trades.iterrows():
                if trade['indicators'] and isinstance(trade['indicators'], dict):
                    winning_indicators.append(trade['indicators'])
            
            for _, trade in losing_trades.iterrows():
                if trade['indicators'] and isinstance(trade['indicators'], dict):
                    losing_indicators.append(trade['indicators'])
            
            if winning_indicators and losing_indicators:
                # Convert to DataFrames
                winning_ind_df = pd.DataFrame(winning_indicators)
                losing_ind_df = pd.DataFrame(losing_indicators)
                
                # Compare averages
                for col in winning_ind_df.columns:
                    if col in losing_ind_df.columns:
                        win_avg = winning_ind_df[col].mean()
                        lose_avg = losing_ind_df[col].mean()
                        difference = win_avg - lose_avg
                        logger.info(f"  {col}: Win={win_avg:.4f}, Lose={lose_avg:.4f}, Diff={difference:.4f}")
    
    def identify_failure_patterns(self):
        """Identify common patterns in losing trades"""
        logger.info("🔍 Identifying failure patterns...")
        
        merged_df = self.trades_df.merge(
            self.signals_df, 
            left_on='signal_id', 
            right_on='id', 
            suffixes=('_trade', '_signal'),
            how='left'
        )
        
        losing_trades = merged_df[(merged_df['status'] == 'CLOSED') & (merged_df['pnl'] < 0)]
        
        if len(losing_trades) == 0:
            logger.warning("⚠️ No losing trades to analyze")
            return
        
        logger.info(f"\n❌ Analyzing {len(losing_trades)} losing trades:")
        
        # Most common losing patterns
        logger.info("\n🔍 Most Common Losing Signal Reasons:")
        all_reasons = []
        for _, trade in losing_trades.iterrows():
            if trade['reasons'] and isinstance(trade['reasons'], list):
                all_reasons.extend(trade['reasons'])
        
        if all_reasons:
            reason_counts = pd.Series(all_reasons).value_counts()
            for reason, count in reason_counts.head(10).items():
                percentage = (count / len(losing_trades)) * 100
                logger.info(f"  {reason}: {count} times ({percentage:.1f}% of losing trades)")
        
        # Time-based patterns
        losing_trades['hour'] = pd.to_datetime(losing_trades['timestamp_trade']).dt.hour
        hour_losses = losing_trades.groupby('hour')['pnl'].agg(['count', 'sum', 'mean'])
        worst_hours = hour_losses.sort_values('mean').head(5)
        
        logger.info("\n🕐 Worst Trading Hours (by average loss):")
        for hour in worst_hours.index:
            count = worst_hours.loc[hour, 'count']
            avg_loss = worst_hours.loc[hour, 'mean']
            total_loss = worst_hours.loc[hour, 'sum']
            logger.info(f"  {hour:02d}:00: {count} trades, Avg: ${avg_loss:.2f}, Total: ${total_loss:.2f}")
    
    def generate_rl_insights(self):
        """Generate insights for RL implementation"""
        logger.info("\n🤖 Generating Reinforcement Learning Insights...")
        
        insights = {
            'problems_identified': [],
            'rl_features': [],
            'reward_structure': {},
            'action_space': []
        }
        
        # Identify key problems
        performance = self.analyze_trade_performance()
        if performance and performance['win_rate'] < 50:
            insights['problems_identified'].append(f"Low win rate: {performance['win_rate']:.1f}%")
        
        if performance and performance['profit_factor'] < 1.0:
            insights['problems_identified'].append(f"Poor profit factor: {performance['profit_factor']:.2f}")
        
        # Suggest RL features
        insights['rl_features'] = [
            'rsi', 'macd', 'macd_signal', 'macd_histogram',
            'ema_9', 'ema_21', 'ema_50', 'ema_200', 'vwap',
            'price_vs_vwap_ratio', 'signal_strength', 'volatility',
            'time_of_day', 'position_duration', 'unrealized_pnl'
        ]
        
        # Suggest reward structure
        insights['reward_structure'] = {
            'profit_reward': 'pnl / entry_price',  # Normalized profit
            'loss_penalty': 'pnl / entry_price * 2',  # Double penalty for losses
            'hold_cost': '-0.001',  # Small cost for holding positions
            'transaction_cost': '-0.002'  # Cost per trade
        }
        
        # Suggest action space
        insights['action_space'] = [
            'HOLD',      # 0: Do nothing
            'BUY_LOW',   # 1: Buy with low confidence (smaller position)
            'BUY_HIGH',  # 2: Buy with high confidence (larger position)
            'SELL_LOW',  # 3: Sell with low confidence
            'SELL_HIGH', # 4: Sell with high confidence
            'CLOSE'      # 5: Close current position
        ]
        
        logger.info("\n🎯 Key Problems Identified:")
        for problem in insights['problems_identified']:
            logger.info(f"  • {problem}")
        
        logger.info("\n🤖 Recommended RL Features:")
        for feature in insights['rl_features'][:10]:  # Show first 10
            logger.info(f"  • {feature}")
        
        logger.info("\n💰 Suggested Reward Structure:")
        for reward_type, formula in insights['reward_structure'].items():
            logger.info(f"  • {reward_type}: {formula}")
        
        logger.info("\n🎮 Suggested Action Space:")
        for i, action in enumerate(insights['action_space']):
            logger.info(f"  • {i}: {action}")
        
        return insights
    
    def run_full_analysis(self):
        """Run complete performance analysis"""
        logger.info("🚀 Starting comprehensive performance analysis...")
        
        self.load_data()
        performance = self.analyze_trade_performance()
        self.analyze_signal_patterns()
        self.analyze_indicator_effectiveness()
        self.identify_failure_patterns()
        insights = self.generate_rl_insights()
        
        return {
            'performance': performance,
            'rl_insights': insights
        }

def main():
    analyzer = PerformanceAnalyzer()
    results = analyzer.run_full_analysis()
    
    logger.info("\n🎉 Analysis complete! Ready for RL implementation.")

if __name__ == "__main__":
    main()