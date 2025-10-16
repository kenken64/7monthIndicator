"""
Backtesting Framework for Unified Signal Aggregator
Replay historical signals through database and calculate what-if performance with different weights
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest run"""
    symbol: str = "SUIUSDC"
    start_date: str = None  # YYYY-MM-DD format
    end_date: str = None    # YYYY-MM-DD format
    initial_balance: float = 10000.0
    position_size_pct: float = 0.10  # 10% of balance per trade
    leverage: int = 1
    maker_fee: float = 0.001  # 0.1%
    taker_fee: float = 0.001  # 0.1%
    stop_loss_pct: float = 0.03  # 3%
    take_profit_pct: float = 0.06  # 6%

    # Signal weights to test
    weights: Dict[str, float] = None

    # Thresholds
    buy_threshold: float = 6.5  # Unified score >= 6.5 triggers BUY
    sell_threshold: float = 3.5  # Unified score <= 3.5 triggers SELL
    min_confidence: float = 55.0  # Minimum confidence for trade


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    config: BacktestConfig

    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0

    # Final state
    final_balance: float = 0.0
    roi: float = 0.0

    # Trade history
    trades: List[Dict] = None
    equity_curve: List[Dict] = None

    # Signal breakdown
    signal_contributions: Dict[str, float] = None

    def __post_init__(self):
        if self.trades is None:
            self.trades = []
        if self.equity_curve is None:
            self.equity_curve = []
        if self.signal_contributions is None:
            self.signal_contributions = {}


class UnifiedSignalBacktester:
    """Backtest engine for unified signal aggregator"""

    # Default weights from unified_signal_aggregator.py
    DEFAULT_WEIGHTS = {
        'technical': 0.25,
        'rl': 0.15,
        'chart_analysis': 0.30,
        'crewai': 0.15,
        'market_context': 0.10,
        'news_sentiment': 0.05
    }

    def __init__(self, db_path: str = 'trading_bot.db'):
        """Initialize backtester with database connection"""
        self.db_path = db_path
        self.conn = None

    def _connect_db(self):
        """Connect to database"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

    def _close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """
        Run backtest with given configuration

        Args:
            config: BacktestConfig with test parameters

        Returns:
            BacktestResult with performance metrics
        """
        logger.info("=" * 80)
        logger.info("STARTING BACKTEST")
        logger.info("=" * 80)
        logger.info(f"Symbol: {config.symbol}")
        logger.info(f"Period: {config.start_date} to {config.end_date}")
        logger.info(f"Initial Balance: ${config.initial_balance:,.2f}")
        logger.info(f"Weights: {config.weights}")
        logger.info("=" * 80)

        self._connect_db()

        try:
            # Load historical signals and market data
            signals_df = self._load_signals(config)

            if signals_df.empty:
                logger.warning("No signals found in database for the specified period")
                return BacktestResult(config=config, final_balance=config.initial_balance)

            logger.info(f"Loaded {len(signals_df)} historical signals")

            # Initialize backtest state
            result = BacktestResult(config=config)
            balance = config.initial_balance
            position = None  # Current position: None, or {'side': 'BUY/SELL', 'entry_price': float, 'quantity': float, 'entry_time': datetime}
            peak_balance = balance

            # Simulate trading through historical signals
            for idx, row in signals_df.iterrows():
                signal_data = self._parse_signal_row(row)

                # Calculate unified score with custom weights
                unified_score = self._calculate_unified_score(signal_data, config.weights or self.DEFAULT_WEIGHTS)

                # Determine action based on unified score
                action = self._determine_action(unified_score, config, signal_data)

                # Track equity
                current_equity = balance
                if position:
                    # Mark-to-market current position
                    current_price = signal_data['price']
                    if position['side'] == 'BUY':
                        unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
                    else:  # SELL/SHORT
                        unrealized_pnl = (position['entry_price'] - current_price) * position['quantity']
                    current_equity = balance + unrealized_pnl

                # Record equity curve
                result.equity_curve.append({
                    'timestamp': signal_data['timestamp'],
                    'balance': balance,
                    'equity': current_equity,
                    'position': 'OPEN' if position else 'FLAT'
                })

                # Execute trades
                if action == 'BUY' and position is None:
                    # Open long position
                    position = self._open_position(
                        side='BUY',
                        price=signal_data['price'],
                        balance=balance,
                        config=config,
                        timestamp=signal_data['timestamp'],
                        signal_data=signal_data
                    )
                    logger.info(f"[{signal_data['timestamp']}] OPEN LONG @ ${signal_data['price']:.4f} | Score: {unified_score:.2f}")

                elif action == 'SELL' and position and position['side'] == 'BUY':
                    # Close long position
                    trade_result = self._close_position(
                        position=position,
                        exit_price=signal_data['price'],
                        exit_time=signal_data['timestamp'],
                        config=config,
                        reason='Signal'
                    )

                    balance += trade_result['pnl']
                    result.trades.append(trade_result)
                    result.total_trades += 1

                    if trade_result['pnl'] > 0:
                        result.winning_trades += 1
                    else:
                        result.losing_trades += 1

                    logger.info(f"[{signal_data['timestamp']}] CLOSE LONG @ ${signal_data['price']:.4f} | PnL: ${trade_result['pnl']:.2f} ({trade_result['pnl_pct']:.2f}%)")

                    position = None

                # Check stop loss / take profit
                if position:
                    position, trade_result = self._check_exit_conditions(
                        position=position,
                        current_price=signal_data['price'],
                        current_time=signal_data['timestamp'],
                        config=config
                    )

                    if trade_result:  # Position was closed
                        balance += trade_result['pnl']
                        result.trades.append(trade_result)
                        result.total_trades += 1

                        if trade_result['pnl'] > 0:
                            result.winning_trades += 1
                        else:
                            result.losing_trades += 1

                        logger.info(f"[{signal_data['timestamp']}] {trade_result['exit_reason']} @ ${signal_data['price']:.4f} | PnL: ${trade_result['pnl']:.2f}")

                # Track max drawdown
                if current_equity > peak_balance:
                    peak_balance = current_equity
                drawdown = peak_balance - current_equity
                if drawdown > result.max_drawdown:
                    result.max_drawdown = drawdown
                    result.max_drawdown_pct = (drawdown / peak_balance) * 100 if peak_balance > 0 else 0

            # Close any remaining open position at end of backtest
            if position:
                last_price = signals_df.iloc[-1]['price']
                last_time = signals_df.iloc[-1]['timestamp']
                trade_result = self._close_position(
                    position=position,
                    exit_price=last_price,
                    exit_time=last_time,
                    config=config,
                    reason='End of backtest'
                )
                balance += trade_result['pnl']
                result.trades.append(trade_result)
                result.total_trades += 1
                if trade_result['pnl'] > 0:
                    result.winning_trades += 1
                else:
                    result.losing_trades += 1

            # Calculate final metrics
            result.final_balance = balance
            result.total_pnl = balance - config.initial_balance
            result.total_pnl_pct = (result.total_pnl / config.initial_balance) * 100
            result.roi = result.total_pnl_pct

            if result.total_trades > 0:
                result.win_rate = (result.winning_trades / result.total_trades) * 100

                winning_pnls = [t['pnl'] for t in result.trades if t['pnl'] > 0]
                losing_pnls = [t['pnl'] for t in result.trades if t['pnl'] < 0]

                result.avg_win = np.mean(winning_pnls) if winning_pnls else 0
                result.avg_loss = np.mean(losing_pnls) if losing_pnls else 0
                result.max_win = max(winning_pnls) if winning_pnls else 0
                result.max_loss = min(losing_pnls) if losing_pnls else 0

                # Profit factor
                gross_profit = sum(winning_pnls) if winning_pnls else 0
                gross_loss = abs(sum(losing_pnls)) if losing_pnls else 0
                result.profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

                # Sharpe ratio (simplified)
                returns = [t['pnl_pct'] for t in result.trades]
                if len(returns) > 1:
                    result.sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0

            # Analyze signal contributions
            result.signal_contributions = self._analyze_signal_contributions(result.trades, config.weights or self.DEFAULT_WEIGHTS)

            self._print_results(result)

            return result

        finally:
            self._close_db()

    def _load_signals(self, config: BacktestConfig) -> pd.DataFrame:
        """Load historical signals from database"""
        query = """
            SELECT
                timestamp,
                symbol,
                price,
                signal,
                strength,
                reasons,
                indicators,
                rl_enhanced
            FROM signals
            WHERE symbol = ?
        """

        params = [config.symbol]

        if config.start_date:
            query += " AND date(timestamp) >= ?"
            params.append(config.start_date)

        if config.end_date:
            query += " AND date(timestamp) <= ?"
            params.append(config.end_date)

        query += " ORDER BY timestamp ASC"

        df = pd.read_sql_query(query, self.conn, params=params)

        return df

    def _parse_signal_row(self, row) -> Dict:
        """Parse database row into signal data"""
        indicators = json.loads(row['indicators']) if row['indicators'] else {}
        reasons = json.loads(row['reasons']) if row['reasons'] else []

        return {
            'timestamp': row['timestamp'],
            'symbol': row['symbol'],
            'price': row['price'],
            'signal': row['signal'],
            'strength': row['strength'],
            'reasons': reasons,
            'indicators': indicators,
            'rl_enhanced': row['rl_enhanced']
        }

    def _calculate_unified_score(self, signal_data: Dict, weights: Dict[str, float]) -> float:
        """
        Calculate unified score from signal data using custom weights
        This simulates the unified_signal_aggregator.py logic
        """
        scores = {}

        # Technical indicators score (from database signal)
        signal_val = signal_data['signal']  # -1, 0, 1
        if signal_val == 1:  # BUY
            scores['technical'] = 7.0
        elif signal_val == -1:  # SELL
            scores['technical'] = 3.0
        else:  # HOLD
            scores['technical'] = 5.0

        # Adjust for RSI
        rsi = signal_data['indicators'].get('rsi', 50)
        if rsi < 30:
            scores['technical'] += 1.0
        elif rsi > 70:
            scores['technical'] -= 1.0

        scores['technical'] = max(0.0, min(10.0, scores['technical']))

        # RL enhancement (if available)
        if signal_data['rl_enhanced']:
            if signal_val == 1:
                scores['rl'] = 8.0
            elif signal_val == -1:
                scores['rl'] = 2.0
            else:
                scores['rl'] = 5.0
        else:
            scores['rl'] = 5.0  # Neutral if not available

        # Other signals (use neutral default for historical data)
        # In a real backtest with complete data, these would be loaded from respective sources
        scores['chart_analysis'] = 5.0
        scores['crewai'] = 5.0
        scores['market_context'] = 5.0
        scores['news_sentiment'] = 5.0

        # Calculate weighted score
        unified_score = sum(scores[key] * weights[key] for key in weights.keys())

        return unified_score

    def _determine_action(self, unified_score: float, config: BacktestConfig, signal_data: Dict) -> str:
        """Determine trading action based on unified score"""
        # Require minimum confidence (use strength as proxy)
        confidence = signal_data['strength'] * 10  # Convert 0-10 to 0-100

        if confidence < config.min_confidence:
            return 'HOLD'

        if unified_score >= config.buy_threshold:
            return 'BUY'
        elif unified_score <= config.sell_threshold:
            return 'SELL'
        else:
            return 'HOLD'

    def _open_position(self, side: str, price: float, balance: float, config: BacktestConfig,
                      timestamp: str, signal_data: Dict) -> Dict:
        """Open a new position"""
        position_value = balance * config.position_size_pct
        quantity = (position_value / price) * config.leverage
        fees = position_value * config.taker_fee

        return {
            'side': side,
            'entry_price': price,
            'quantity': quantity,
            'entry_time': timestamp,
            'fees_paid': fees,
            'signal_data': signal_data
        }

    def _close_position(self, position: Dict, exit_price: float, exit_time: str,
                       config: BacktestConfig, reason: str) -> Dict:
        """Close position and calculate PnL"""
        if position['side'] == 'BUY':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:  # SELL/SHORT
            pnl = (position['entry_price'] - exit_price) * position['quantity']

        # Subtract fees
        position_value = position['entry_price'] * position['quantity']
        exit_fees = (exit_price * position['quantity']) * config.taker_fee
        pnl -= (position['fees_paid'] + exit_fees)

        pnl_pct = (pnl / position_value) * 100

        return {
            'entry_time': position['entry_time'],
            'exit_time': exit_time,
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': reason,
            'duration': None  # Could calculate duration here
        }

    def _check_exit_conditions(self, position: Dict, current_price: float, current_time: str,
                               config: BacktestConfig) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Check if stop loss or take profit is hit"""
        if position['side'] == 'BUY':
            pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100

            if pnl_pct <= -config.stop_loss_pct * 100:
                trade_result = self._close_position(position, current_price, current_time, config, 'Stop Loss')
                return None, trade_result

            if pnl_pct >= config.take_profit_pct * 100:
                trade_result = self._close_position(position, current_price, current_time, config, 'Take Profit')
                return None, trade_result

        return position, None

    def _analyze_signal_contributions(self, trades: List[Dict], weights: Dict[str, float]) -> Dict[str, float]:
        """Analyze which signals contributed most to performance"""
        contributions = {key: 0.0 for key in weights.keys()}

        # This is a simplified analysis - in reality, would need to track each signal's contribution per trade
        for key in weights.keys():
            contributions[key] = weights[key]  # Placeholder

        return contributions

    def _print_results(self, result: BacktestResult):
        """Print backtest results"""
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Initial Balance: ${result.config.initial_balance:,.2f}")
        logger.info(f"Final Balance:   ${result.final_balance:,.2f}")
        logger.info(f"Total PnL:       ${result.total_pnl:,.2f} ({result.total_pnl_pct:.2f}%)")
        logger.info(f"ROI:             {result.roi:.2f}%")
        logger.info("-" * 80)
        logger.info(f"Total Trades:    {result.total_trades}")
        logger.info(f"Winning Trades:  {result.winning_trades}")
        logger.info(f"Losing Trades:   {result.losing_trades}")
        logger.info(f"Win Rate:        {result.win_rate:.2f}%")
        logger.info("-" * 80)
        logger.info(f"Average Win:     ${result.avg_win:.2f}")
        logger.info(f"Average Loss:    ${result.avg_loss:.2f}")
        logger.info(f"Max Win:         ${result.max_win:.2f}")
        logger.info(f"Max Loss:        ${result.max_loss:.2f}")
        logger.info(f"Profit Factor:   {result.profit_factor:.2f}")
        logger.info("-" * 80)
        logger.info(f"Max Drawdown:    ${result.max_drawdown:.2f} ({result.max_drawdown_pct:.2f}%)")
        logger.info(f"Sharpe Ratio:    {result.sharpe_ratio:.2f}")
        logger.info("=" * 80 + "\n")


def run_weight_optimization(
    symbol: str = "SUIUSDC",
    start_date: str = None,
    end_date: str = None,
    initial_balance: float = 10000.0,
    db_path: str = 'trading_bot.db'
) -> pd.DataFrame:
    """
    Run backtests with different weight combinations to find optimal settings

    Args:
        symbol: Trading pair symbol
        start_date: Start date for backtest
        end_date: End date for backtest
        initial_balance: Starting capital
        db_path: Path to database file

    Returns:
        DataFrame with results for each weight combination
    """
    backtester = UnifiedSignalBacktester(db_path=db_path)

    # Define weight combinations to test
    weight_combinations = [
        # Baseline
        {'technical': 0.25, 'rl': 0.15, 'chart_analysis': 0.30, 'crewai': 0.15, 'market_context': 0.10, 'news_sentiment': 0.05},

        # Technical-heavy
        {'technical': 0.40, 'rl': 0.20, 'chart_analysis': 0.20, 'crewai': 0.10, 'market_context': 0.05, 'news_sentiment': 0.05},

        # Chart-heavy
        {'technical': 0.20, 'rl': 0.10, 'chart_analysis': 0.45, 'crewai': 0.15, 'market_context': 0.05, 'news_sentiment': 0.05},

        # RL-focused
        {'technical': 0.20, 'rl': 0.35, 'chart_analysis': 0.25, 'crewai': 0.10, 'market_context': 0.05, 'news_sentiment': 0.05},

        # AI-heavy (Chart + CrewAI)
        {'technical': 0.15, 'rl': 0.10, 'chart_analysis': 0.35, 'crewai': 0.30, 'market_context': 0.05, 'news_sentiment': 0.05},

        # Balanced
        {'technical': 0.30, 'rl': 0.20, 'chart_analysis': 0.25, 'crewai': 0.15, 'market_context': 0.05, 'news_sentiment': 0.05},
    ]

    results = []

    for idx, weights in enumerate(weight_combinations, 1):
        logger.info(f"\n{'#' * 80}")
        logger.info(f"TESTING WEIGHT COMBINATION {idx}/{len(weight_combinations)}")
        logger.info(f"{'#' * 80}\n")

        config = BacktestConfig(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            weights=weights
        )

        result = backtester.run_backtest(config)

        results.append({
            'weights': weights,
            'roi': result.roi,
            'total_pnl': result.total_pnl,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'profit_factor': result.profit_factor,
            'max_drawdown_pct': result.max_drawdown_pct,
            'sharpe_ratio': result.sharpe_ratio
        })

    # Create DataFrame
    results_df = pd.DataFrame(results)

    # Print comparison
    logger.info("\n" + "=" * 120)
    logger.info("WEIGHT OPTIMIZATION RESULTS")
    logger.info("=" * 120)
    logger.info(results_df.to_string(index=False))
    logger.info("=" * 120 + "\n")

    # Find best configuration
    best_idx = results_df['roi'].idxmax()
    best_result = results_df.iloc[best_idx]

    logger.info(f"\nBEST CONFIGURATION (by ROI):")
    logger.info(f"Weights: {best_result['weights']}")
    logger.info(f"ROI: {best_result['roi']:.2f}%")
    logger.info(f"Win Rate: {best_result['win_rate']:.2f}%")
    logger.info(f"Profit Factor: {best_result['profit_factor']:.2f}")

    return results_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Backtest Unified Signal Aggregator')
    parser.add_argument('--symbol', default='SUIUSDC', help='Trading symbol')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--balance', type=float, default=10000.0, help='Initial balance')
    parser.add_argument('--optimize', action='store_true', help='Run weight optimization')

    args = parser.parse_args()

    if args.optimize:
        # Run weight optimization
        run_weight_optimization(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_balance=args.balance
        )
    else:
        # Run single backtest with default weights
        backtester = UnifiedSignalBacktester()
        config = BacktestConfig(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_balance=args.balance
        )
        result = backtester.run_backtest(config)
