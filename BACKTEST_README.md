# Unified Signal Aggregator Backtesting Framework

## Overview

This backtesting framework allows you to **replay historical signals** through the database and calculate **what-if performance** with different weight configurations for the Unified Signal Aggregator.

### Key Features

✅ **Historical Signal Replay** - Uses actual signals from your trading bot database
✅ **Weight Optimization** - Test different weight combinations to find optimal settings
✅ **Comprehensive Metrics** - Win rate, PnL, Sharpe ratio, drawdown, profit factor
✅ **Low Effort, High Insight** - Leverages existing data without additional setup

---

## Quick Start

### 1. Check Available Data

First, check what historical data you have:

```bash
python3 run_backtest.py check
```

This will show:
- Number of signals available
- Date range of historical data
- Signal distribution (BUY/SELL/HOLD percentages)
- Completed trades (if any)

### 2. Run Quick Backtest

Run a backtest with default weights:

```bash
python3 run_backtest.py
```

This tests the **current default weights** from `unified_signal_aggregator.py`:
- Technical: 25%
- RL: 15%
- Chart Analysis: 30%
- CrewAI: 15%
- Market Context: 10%
- News Sentiment: 5%

### 3. Run Weight Optimization

Test multiple weight combinations to find the optimal configuration:

```bash
python3 run_backtest.py optimize
```

This will test 6 different weight combinations and output:
- Performance comparison table
- Best configuration by ROI
- Detailed results saved to CSV file

---

## Components

### 1. `backtest_unified_signals.py`

Main backtesting engine with:

**Classes:**
- `BacktestConfig` - Configuration dataclass for backtest parameters
- `BacktestResult` - Results dataclass with all performance metrics
- `UnifiedSignalBacktester` - Core backtesting engine

**Key Methods:**
- `run_backtest(config)` - Execute a single backtest run
- `run_weight_optimization()` - Test multiple weight combinations

**Features:**
- Position management with stop loss and take profit
- Realistic fee modeling (maker/taker fees)
- Mark-to-market equity tracking
- Comprehensive performance metrics

### 2. `run_backtest.py`

Helper script with convenience functions:

**Functions:**
- `check_available_data()` - Analyze database contents
- `run_quick_backtest()` - Quick backtest with default settings
- `run_full_optimization()` - Full weight optimization suite

---

## Configuration Options

### BacktestConfig Parameters

```python
BacktestConfig(
    symbol='SUIUSDC',           # Trading pair
    start_date='2025-01-01',    # Start date (YYYY-MM-DD)
    end_date='2025-12-31',      # End date (YYYY-MM-DD)
    initial_balance=10000.0,    # Starting capital
    position_size_pct=0.10,     # 10% of balance per trade
    leverage=1,                 # No leverage by default
    maker_fee=0.001,            # 0.1% maker fee
    taker_fee=0.001,            # 0.1% taker fee
    stop_loss_pct=0.03,         # 3% stop loss
    take_profit_pct=0.06,       # 6% take profit
    weights={...},              # Custom signal weights
    buy_threshold=6.5,          # Score >= 6.5 triggers BUY
    sell_threshold=3.5,         # Score <= 3.5 triggers SELL
    min_confidence=55.0         # Minimum confidence for trades
)
```

---

## Understanding the Results

### Performance Metrics

```
BACKTEST RESULTS
================================================================================
Initial Balance: $10,000.00
Final Balance:   $12,500.00
Total PnL:       $2,500.00 (25.00%)
ROI:             25.00%
--------------------------------------------------------------------------------
Total Trades:    45
Winning Trades:  28
Losing Trades:   17
Win Rate:        62.22%
--------------------------------------------------------------------------------
Average Win:     $150.50
Average Loss:    $-82.35
Max Win:         $420.00
Max Loss:        $-180.00
Profit Factor:   2.15
--------------------------------------------------------------------------------
Max Drawdown:    $350.00 (3.50%)
Sharpe Ratio:    1.85
================================================================================
```

**Key Metrics Explained:**

- **ROI (Return on Investment)**: Percentage gain/loss from initial balance
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss (>1.0 is profitable)
- **Sharpe Ratio**: Risk-adjusted return (>1.0 is good, >2.0 is excellent)
- **Max Drawdown**: Largest peak-to-trough decline

### Weight Optimization Output

```
WEIGHT OPTIMIZATION RESULTS
================================================================================
                                  weights    roi  total_pnl  win_rate  ...
Technical-heavy (40/20/20/10/5/5)          28.5%  $2,850.00     65.5%  ...
Chart-heavy (20/10/45/15/5/5)              32.1%  $3,210.00     68.2%  ...
RL-focused (20/35/25/10/5/5)               25.3%  $2,530.00     61.8%  ...
...
================================================================================

BEST CONFIGURATION (by ROI):
Weights: {'technical': 0.20, 'rl': 0.10, 'chart_analysis': 0.45, ...}
ROI: 32.1%
Win Rate: 68.2%
Profit Factor: 2.45
```

---

## Advanced Usage

### Custom Backtest with Specific Weights

```python
from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig

# Define custom weights
custom_weights = {
    'technical': 0.30,
    'rl': 0.20,
    'chart_analysis': 0.25,
    'crewai': 0.15,
    'market_context': 0.05,
    'news_sentiment': 0.05
}

# Create config
config = BacktestConfig(
    symbol='SUIUSDC',
    start_date='2025-09-01',
    end_date='2025-09-30',
    initial_balance=10000.0,
    weights=custom_weights,
    buy_threshold=6.0,  # More aggressive
    sell_threshold=4.0
)

# Run backtest
backtester = UnifiedSignalBacktester()
result = backtester.run_backtest(config)

# Access results
print(f"Final PnL: ${result.total_pnl:.2f}")
print(f"Win Rate: {result.win_rate:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### Programmatic Weight Grid Search

```python
import itertools
from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig

backtester = UnifiedSignalBacktester()

# Define ranges for key weights
tech_weights = [0.20, 0.25, 0.30]
rl_weights = [0.10, 0.15, 0.20]
chart_weights = [0.25, 0.30, 0.35]

results = []

for tech, rl, chart in itertools.product(tech_weights, rl_weights, chart_weights):
    # Ensure weights sum to 1.0
    remaining = 1.0 - (tech + rl + chart)
    crewai = remaining * 0.5
    market = remaining * 0.3
    news = remaining * 0.2

    weights = {
        'technical': tech,
        'rl': rl,
        'chart_analysis': chart,
        'crewai': crewai,
        'market_context': market,
        'news_sentiment': news
    }

    config = BacktestConfig(
        symbol='SUIUSDC',
        weights=weights,
        initial_balance=10000.0
    )

    result = backtester.run_backtest(config)
    results.append({
        'weights': weights,
        'roi': result.roi,
        'sharpe': result.sharpe_ratio,
        'win_rate': result.win_rate
    })

# Find best result
best = max(results, key=lambda x: x['sharpe'])
print(f"Best Sharpe Ratio: {best['sharpe']:.2f}")
print(f"Optimal Weights: {best['weights']}")
```

---

## Data Requirements

The backtesting system requires historical **signal data** stored in the `trading_bot.db` database.

### Signals Table Schema

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    price REAL,
    signal INTEGER,      -- -1 (SELL), 0 (HOLD), 1 (BUY)
    strength INTEGER,    -- 0-10
    reasons TEXT,        -- JSON array
    indicators TEXT,     -- JSON object (RSI, MACD, etc.)
    rl_enhanced BOOLEAN,
    executed BOOLEAN
)
```

### Collecting Historical Data

**Option 1: Run the Bot**
- Let your trading bot run for several days/weeks
- Signals are automatically logged to the database
- More data = more reliable backtest results

**Option 2: Import Historical Data**
- Create a script to generate signals from historical price data
- Use your existing signal generation logic
- Bulk insert into the database

**Recommended Timeline:**
- **Minimum**: 7 days of data (limited insights)
- **Good**: 30 days of data (reasonable testing)
- **Ideal**: 90+ days of data (statistical significance)

---

## Interpreting Results

### What Makes a Good Backtest?

✅ **Win Rate > 50%** - More wins than losses
✅ **Profit Factor > 1.5** - Wins significantly outweigh losses
✅ **Sharpe Ratio > 1.0** - Good risk-adjusted returns
✅ **Max Drawdown < 20%** - Acceptable risk exposure
✅ **ROI > Buy & Hold** - Strategy outperforms passive holding

### Common Pitfalls

❌ **Overfitting** - Optimizing too many parameters on limited data
❌ **Look-Ahead Bias** - Using future information in past decisions
❌ **Insufficient Data** - Making conclusions from too few trades
❌ **Ignoring Fees** - Not accounting for transaction costs
❌ **Unrealistic Assumptions** - Not modeling slippage/latency

---

## Roadmap & Future Enhancements

### Phase 2: Advanced Features
- [ ] Walk-forward analysis (rolling window optimization)
- [ ] Monte Carlo simulation (random trade shuffling)
- [ ] Parameter sensitivity heat maps
- [ ] Multi-symbol concurrent backtesting

### Phase 3: Risk Management
- [ ] Position sizing optimization (Kelly Criterion)
- [ ] Dynamic stop loss/take profit
- [ ] Maximum concurrent positions limit
- [ ] Risk-adjusted position scaling

### Phase 4: Reporting
- [ ] HTML report generation with charts
- [ ] Equity curve visualization
- [ ] Trade distribution analysis
- [ ] Correlation analysis with market conditions

### Phase 5: Live Validation
- [ ] Paper trading mode integration
- [ ] Real-time performance tracking
- [ ] Backtest vs live performance comparison
- [ ] Automated weight adjustment

---

## Troubleshooting

### "No signals found in database"

**Solution:** Run your trading bot to collect signals, or import historical data.

### "Database locked"

**Solution:** Close any other processes accessing `trading_bot.db`.

### "Not enough data for meaningful backtest"

**Solution:** Collect at least 7 days of signal data before backtesting.

### Slow performance with large datasets

**Solution:** Add date filters or reduce the backtest period.

---

## Examples

### Example 1: Testing Chart-Heavy Strategy

```bash
python3 -c "
from backtest_unified_signals import *

config = BacktestConfig(
    symbol='SUIUSDC',
    weights={
        'technical': 0.15,
        'rl': 0.10,
        'chart_analysis': 0.50,  # Heavy chart weight
        'crewai': 0.15,
        'market_context': 0.05,
        'news_sentiment': 0.05
    }
)

backtester = UnifiedSignalBacktester()
result = backtester.run_backtest(config)
"
```

### Example 2: Conservative Trading

```bash
python3 -c "
from backtest_unified_signals import *

config = BacktestConfig(
    symbol='SUIUSDC',
    buy_threshold=7.0,      # Higher threshold = fewer trades
    sell_threshold=3.0,
    min_confidence=70.0,    # Higher confidence required
    position_size_pct=0.05  # Smaller positions
)

backtester = UnifiedSignalBacktester()
result = backtester.run_backtest(config)
"
```

---

## Contributing

Found a bug or have a feature request? Please open an issue or submit a pull request.

**Areas for contribution:**
- Additional performance metrics
- Visualization tools
- Data import scripts
- Documentation improvements

---

## License

Part of the 7monthIndicator cryptocurrency trading bot project.

---

## Changelog

### v1.0.0 (Current)
- Initial release
- Basic backtest engine
- Weight optimization
- Comprehensive metrics
- Database integration

---

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review example usage
3. Examine backtest logs for detailed information
4. Open an issue with reproducible steps

---

**Last Updated:** October 2025
**Status:** Production Ready
**Python Version:** 3.8+
**Dependencies:** pandas, numpy, sqlite3
