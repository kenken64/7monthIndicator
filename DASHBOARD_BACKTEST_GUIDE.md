# Dashboard Backtesting Guide

## Overview

The web dashboard now includes a comprehensive backtesting and strategy analysis section that allows you to:

1. **Test Historical Performance** - See how your current strategy would have performed on historical data
2. **Optimize Signal Weights** - Find the best combination of signal source weights
3. **Get Actionable Insights** - Receive specific recommendations for your current trading decisions

## Accessing the Backtest Section

1. Open the web dashboard: `http://your-server:5000`
2. Scroll down to the **"Strategy Backtesting & Insights"** section (located after the Unified Signal Aggregation section)

## Features

### 1. Data Availability Display

The top section shows:
- **Total Signals**: Number of historical signals in your database
- **BUY Signals**: Count of actionable buy signals
- **SELL Signals**: Count of actionable sell signals
- **Data Status**: Whether you have enough data to run meaningful backtests

**Note**: You need at least some BUY or SELL signals (not just HOLD) for meaningful backtesting results.

### 2. Quick Backtest

**Purpose**: Test your current weight configuration on historical data

**How to Use**:
1. Click the **"⚡ Quick Backtest"** button
2. Wait 5-10 seconds for the backtest to complete
3. View results showing:
   - **ROI**: Return on Investment percentage
   - **Win Rate**: Percentage of profitable trades
   - **Total Trades**: Number of trades executed in the simulation
   - **Total PnL**: Total profit/loss in dollars
   - **Sharpe Ratio**: Risk-adjusted return metric (>1.0 is good, >2.0 is excellent)
   - **Max Drawdown**: Largest peak-to-trough decline

**Current Weights Being Tested**:
- Technical Indicators: 25%
- RL Enhancement: 15%
- Chart Analysis: 30%
- CrewAI Multi-Agent: 15%
- Market Context: 10%
- News Sentiment: 5%

### 3. Optimize Weights

**Purpose**: Find the optimal signal source weight combination

**How to Use**:
1. Click the **"🎯 Optimize Weights"** button
2. Wait 30-60 seconds as the system tests 6 different weight configurations
3. The best performing configuration will be displayed
4. Full results are logged to the browser console

**What It Tests**:
- **Balanced**: Current default weights
- **Technical-Heavy**: 40/20/20/10/5/5
- **Chart-Heavy**: 20/10/45/15/5/5
- **RL-Focused**: 20/35/25/10/5/5
- **AI-Heavy**: 15/10/35/30/5/5
- **Conservative**: 30/15/25/15/10/5

### 4. Actionable Insights

**Purpose**: Get specific recommendations for your current trading decisions

**What You'll See**:

Insights are automatically generated and categorized by type:

#### 🚨 Danger (Red)
Critical issues requiring immediate action:
- Negative returns
- High drawdown risk
- System failures

#### ⚠️ Warning (Yellow)
Important concerns to address:
- Low win rate
- Poor risk-adjusted returns
- Suboptimal configuration

#### ✅ Positive (Green)
Good performance indicators:
- Strong win rate
- Profitable strategy
- Good risk management

#### ℹ️ Info (Blue)
General information and current signals:
- Low trading activity
- Current signal recommendations
- Data collection suggestions

**Example Insights**:

```
🚨 Negative Returns
Strategy lost 8.2% over backtest period. Immediate review recommended.
Action: Pause trading and run optimization
Confidence: HIGH
```

```
✅ Strong Win Rate
Your strategy has a 65.3% win rate over the last 30 days. Current weights are performing well.
Action: Continue with current weight configuration
Confidence: HIGH
```

```
ℹ️ Current Signal: BUY
Based on 58.5% historical win rate, current BUY signal has moderate confidence.
Action: Execute BUY if signal strength is above 55%
Confidence: MEDIUM
```

## How to Use Backtest Results for Trading Decisions

### Step-by-Step Decision Framework

1. **Run Quick Backtest** (Daily or after significant market changes)
   - Check ROI and Win Rate
   - Verify risk metrics (Sharpe, Drawdown)

2. **Review Insights** (Before each trade)
   - Look for 🚨 Danger alerts → PAUSE trading
   - Check ⚠️ Warnings → Review configuration
   - Confirm ℹ️ Current Signal insights → Execute with confidence

3. **Optimize Periodically** (Weekly or monthly)
   - Run weight optimization
   - If best ROI > current ROI by 5%+ → Consider updating weights
   - Test new configuration for 1-2 days before full deployment

### Example Decision Scenarios

**Scenario 1: Strong Performance**
```
Backtest Results: ROI: +22%, Win Rate: 68%, Sharpe: 1.8
Current Signal: BUY
Insight: "Strong win rate, continue with current configuration"
Decision: ✅ Execute BUY trade with full position size
```

**Scenario 2: Poor Performance**
```
Backtest Results: ROI: -12%, Win Rate: 42%, Sharpe: 0.3
Current Signal: BUY
Insight: "Negative returns, pause trading and run optimization"
Decision: ⏸️ PAUSE trading, run optimization, review weights
```

**Scenario 3: Mixed Signals**
```
Backtest Results: ROI: +8%, Win Rate: 52%, Sharpe: 0.9
Current Signal: BUY
Insight: "Modest performance, consider lowering position size"
Decision: ⚠️ Execute BUY with 50% position size
```

## Understanding the Metrics

### ROI (Return on Investment)
- **Good**: > 15% per month
- **Average**: 5-15% per month
- **Poor**: < 5% or negative

### Win Rate
- **Excellent**: > 60%
- **Good**: 50-60%
- **Poor**: < 50%

### Sharpe Ratio
- **Excellent**: > 2.0
- **Good**: 1.0-2.0
- **Average**: 0.5-1.0
- **Poor**: < 0.5

### Max Drawdown
- **Excellent**: < 10%
- **Good**: 10-20%
- **Concerning**: > 20%

### Profit Factor
- **Excellent**: > 2.0
- **Good**: 1.5-2.0
- **Breakeven**: 1.0
- **Poor**: < 1.0

## API Endpoints (For Advanced Users)

### Check Data Availability
```bash
curl http://localhost:5000/api/backtest/available-data
```

### Run Quick Backtest
```bash
curl -X POST http://localhost:5000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SUIUSDC", "days_back": 30}'
```

### Run Weight Optimization
```bash
curl -X POST http://localhost:5000/api/backtest/optimize \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SUIUSDC", "days_back": 30}'
```

### Get Actionable Insights
```bash
curl http://localhost:5000/api/backtest/insights
```

## Troubleshooting

### "No Data" or "Limited Data" Status

**Problem**: Not enough historical signals in the database

**Solutions**:
1. Let the trading bot run for at least 7-14 days
2. Check if the bot is actually generating signals:
   ```bash
   sqlite3 trading_bot.db "SELECT COUNT(*), signal FROM signals GROUP BY signal"
   ```
3. Ensure the bot is not paused

### Backtest Fails with Error

**Problem**: Backtest encounters an error

**Solutions**:
1. Check the browser console for detailed error messages
2. Verify database integrity:
   ```bash
   python3 run_backtest.py check
   ```
3. Restart the web dashboard:
   ```bash
   pkill -f web_dashboard.py
   python3 web_dashboard.py &
   ```

### All Results Show 0 Trades

**Problem**: Backtest runs but no trades are simulated

**Causes**:
- Only HOLD signals in database (no BUY/SELL signals)
- Thresholds too strict (buy_threshold too high, sell_threshold too low)
- Confidence requirements not met

**Solutions**:
1. Wait for more diverse signal data
2. Lower thresholds temporarily to test:
   ```python
   # In API call
   {"buy_threshold": 5.5, "sell_threshold": 4.5}
   ```

### Insights Don't Update

**Problem**: Insights section shows old data

**Solutions**:
1. Click "Quick Backtest" button to refresh
2. Hard refresh the page (Ctrl+Shift+R)
3. Check browser console for JavaScript errors

## Best Practices

### Data Collection
- ✅ Run bot continuously for at least 30 days before heavy reliance on backtests
- ✅ Collect data across different market conditions (bull, bear, sideways)
- ✅ Ensure all 6 signal sources are active and generating signals

### Backtest Frequency
- **Daily**: Quick backtest to check current performance
- **Weekly**: Full weight optimization
- **After major events**: Run backtest after significant market crashes or rallies
- **Before big trades**: Always check insights before executing large positions

### Interpretation
- ❌ Don't overfit: Don't change weights daily based on 1-day backtests
- ❌ Don't ignore risk: High ROI with high drawdown is dangerous
- ✅ Focus on consistency: Prefer stable 10% monthly ROI over volatile 30% ROI
- ✅ Use multiple metrics: Don't decide based on ROI alone

### Weight Updates
- Test new weights for 2-3 days in paper trading before live deployment
- Document why you changed weights and when
- Roll back if performance degrades after weight changes

## Integration with Current Trading

The backtest system is designed to work alongside your current trading workflow:

1. **Morning Routine**:
   - Check overnight signals
   - Run quick backtest
   - Review insights
   - Make trading decisions

2. **Before Each Trade**:
   - Check current signal insight
   - Verify confidence level
   - Adjust position size based on backtest performance

3. **Weekly Review**:
   - Run weight optimization
   - Compare to previous week
   - Identify trends and patterns
   - Adjust strategy if needed

## Advanced: Custom Backtests

For advanced users who want more control, you can run custom backtests programmatically:

```python
from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig

# Custom configuration
config = BacktestConfig(
    symbol='SUIUSDC',
    start_date='2025-09-01',
    end_date='2025-10-15',
    initial_balance=10000.0,
    weights={
        'technical': 0.30,
        'rl': 0.20,
        'chart_analysis': 0.25,
        'crewai': 0.15,
        'market_context': 0.05,
        'news_sentiment': 0.05
    },
    buy_threshold=6.0,      # More aggressive
    sell_threshold=4.0,
    position_size_pct=0.15, # Larger positions
    stop_loss_pct=0.02,     # Tighter stop loss
    take_profit_pct=0.08    # Higher take profit
)

# Run backtest
backtester = UnifiedSignalBacktester()
result = backtester.run_backtest(config)

# Print results
print(f"ROI: {result.roi:.2f}%")
print(f"Win Rate: {result.win_rate:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

## Support

For issues or questions:
1. Check the console for detailed error messages
2. Review `BACKTEST_README.md` for detailed technical documentation
3. Check `BACKTEST_IMPLEMENTATION_SUMMARY.md` for implementation details

---

**Last Updated**: October 15, 2025
**Version**: 1.0.0
**Dashboard Integration**: Complete
