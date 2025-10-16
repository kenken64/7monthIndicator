# Run Comprehensive Test Suite

Run the complete test suite for the 7monthIndicator AI Trading Bot system. This command executes all tests for the multi-component trading system including the RL-enhanced trading bot, web dashboard, chart analysis bot, and database components.

## Test Execution Strategy

### 1. Pre-Test System Check
```bash
# Check if bots are running
ps aux | grep -E '(rl_bot_ready|web_dashboard|chart_analysis_bot)' | grep -v grep

# Pause any running bots to prevent interference
if [ -f bot_pause.flag ]; then
    echo "Bot already paused"
else
    touch bot_pause.flag
    echo "Bot paused for testing"
fi
```

### 2. Unit Tests - Core Components

#### Database Tests (database.py)
Test database operations including:
- Signal storage and retrieval
- Trade tracking with PnL calculations
- Market context storage (cross-asset correlation)
- Performance metrics calculations
- Manual closure detection
- Database migrations

```python
# Test file: tests/test_database.py
pytest tests/test_database.py -v --cov=database --cov-report=term-missing

# Key test cases:
# - test_store_signal()
# - test_store_trade()
# - test_update_trade_exit()
# - test_get_open_trades()
# - test_calculate_performance_metrics()
# - test_market_context_storage()
# - test_manual_closure_recording()
```

#### RL System Tests (lightweight_rl.py)
Test reinforcement learning components:
- Q-learning agent behavior
- State representation and encoding
- Action selection (BUY/SELL/HOLD)
- Reward calculation with enhanced system
- Risk level assessment
- Position sizing recommendations
- Exit condition logic

```python
# Test file: tests/test_rl_system.py
pytest tests/test_rl_system.py -v --cov=lightweight_rl

# Key test cases:
# - test_rl_agent_initialization()
# - test_get_trading_recommendation()
# - test_reward_calculation()
# - test_risk_level_assessment()
# - test_exit_conditions()
# - test_position_sizing()
```

#### Technical Indicators Tests (rl_bot_ready.py:TechnicalIndicators)
Test indicator calculations:
- EMA (9, 21, 50, 200)
- RSI calculation accuracy
- MACD and signal line
- VWAP calculations

```python
# Test file: tests/test_technical_indicators.py
pytest tests/test_technical_indicators.py -v

# Key test cases:
# - test_ema_calculation()
# - test_rsi_overbought_oversold()
# - test_macd_crossover()
# - test_vwap_accuracy()
```

#### Cross-Asset Correlation Tests (cross_asset_correlation.py)
Test market context analysis:
- BTC/ETH price fetching
- Fear & Greed Index integration
- Correlation signal generation
- Volatility regime detection
- Market trend analysis

```python
# Test file: tests/test_cross_asset.py
pytest tests/test_cross_asset.py -v --cov=cross_asset_correlation

# Key test cases:
# - test_fetch_btc_eth_data()
# - test_fear_greed_index()
# - test_correlation_signals()
# - test_volatility_regime()
# - test_market_breadth()
```

### 3. Integration Tests - Bot Components

#### Trading Bot Integration
Test the complete RL-enhanced trading flow:
- Signal generation (traditional + RL enhancement)
- Position management (entry/exit)
- TP/SL order placement
- PnL tracking
- Telegram notifications
- Pause/resume functionality
- Position reconciliation

```python
# Test file: tests/test_trading_bot.py
pytest tests/test_trading_bot.py -v --timeout=60

# Key test cases:
# - test_bot_initialization()
# - test_signal_generation_flow()
# - test_rl_enhancement_integration()
# - test_trade_execution_with_mocked_api()
# - test_position_tracking()
# - test_tp_sl_calculation()
# - test_opposite_signal_handling()
# - test_hold_signal_with_negative_pnl()
# - test_pause_resume_functionality()
# - test_position_reconciliation()
```

#### Web Dashboard Tests (web_dashboard.py)
Test Flask endpoints and functionality:
- Dashboard rendering
- Real-time data endpoints
- Bot control (pause/resume with PIN)
- Chart image serving
- Market news fetching
- Sentiment analysis (local vs OpenAI)
- Log streaming

```python
# Test file: tests/test_web_dashboard.py
pytest tests/test_web_dashboard.py -v

# Key test cases:
# - test_dashboard_loads()
# - test_api_bot_status()
# - test_api_positions()
# - test_api_recent_trades()
# - test_api_performance_metrics()
# - test_bot_control_with_pin()
# - test_chart_image_endpoint()
# - test_market_news_api()
# - test_sentiment_analysis_modes()
```

#### Chart Analysis Bot Tests (chart_analysis_bot.py)
Test chart generation and AI analysis:
- Chart generation with mplfinance
- OpenAI GPT-4o integration
- Technical indicator overlays
- Analysis result storage
- 15-minute cycle timing

```python
# Test file: tests/test_chart_analysis.py
pytest tests/test_chart_analysis.py -v

# Key test cases:
# - test_chart_generation()
# - test_indicator_overlays()
# - test_openai_analysis_integration()
# - test_recommendation_parsing()
# - test_chart_storage()
```

### 4. End-to-End Tests

#### Complete Trading Cycle Test
Simulate a complete trading cycle:
1. Market data fetch
2. Indicator calculation
3. Signal generation (with RL)
4. Trade execution
5. Position monitoring
6. TP/SL management
7. Position closure
8. Database recording

```python
# Test file: tests/test_e2e_trading_cycle.py
pytest tests/test_e2e_trading_cycle.py -v --timeout=120

# Use mocked Binance API to simulate real trading
```

#### Multi-Bot Coordination Test
Test system-wide coordination:
- All bots running simultaneously
- Database access coordination
- Web dashboard reflecting live data
- Chart analysis integration

```python
# Test file: tests/test_multi_bot_system.py
pytest tests/test_multi_bot_system.py -v --timeout=180
```

### 5. Performance & Load Tests

```python
# Test file: tests/test_performance.py
pytest tests/test_performance.py -v

# Key test cases:
# - test_signal_generation_speed()  # Should complete in <1s
# - test_database_query_performance()  # Should handle 1000+ queries
# - test_concurrent_access()  # Multiple threads
# - test_memory_usage()  # Monitor for leaks
```

### 6. API Mocking for External Services

Mock external API calls to ensure tests are:
- Fast (no network delays)
- Reliable (no rate limits)
- Deterministic (consistent results)

```python
# tests/conftest.py - Shared fixtures
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_binance_client():
    """Mock Binance API client"""
    with patch('binance.client.Client') as mock:
        # Configure mock responses
        mock.return_value.futures_klines.return_value = [...]
        mock.return_value.futures_position_information.return_value = [...]
        yield mock

@pytest.fixture
def mock_openai():
    """Mock OpenAI API"""
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value = {"choices": [{"message": {"content": "BUY"}}]}
        yield mock

@pytest.fixture
def mock_telegram():
    """Mock Telegram notifications"""
    with patch('requests.post') as mock:
        mock.return_value.status_code = 200
        yield mock
```

### 7. Test Data Fixtures

```python
# tests/fixtures/market_data.py
def get_sample_klines():
    """Sample OHLCV data for testing"""
    return [
        {'timestamp': '2025-01-01', 'open': 3.5, 'high': 3.6,
         'low': 3.4, 'close': 3.55, 'volume': 1000000},
        # ... more data
    ]

def get_sample_indicators():
    """Sample technical indicators"""
    return {
        'ema_9': 3.5, 'ema_21': 3.48, 'ema_50': 3.45,
        'rsi': 65.2, 'macd': 0.01, 'vwap': 3.52
    }
```

### 8. Test Execution Commands

```bash
# Run all tests with coverage
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/test_database.py -v  # Database tests only
pytest tests/test_rl_system.py -v  # RL system tests only
pytest tests/test_trading_bot.py -v  # Trading bot tests only

# Run with specific markers
pytest -m "unit" -v  # Unit tests only
pytest -m "integration" -v  # Integration tests only
pytest -m "e2e" -v  # End-to-end tests only

# Run failed tests only
pytest --lf -v

# Run with detailed output
pytest -vv --tb=short

# Run with pdb on failure
pytest --pdb -v
```

## Test Structure

Create the following directory structure:

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── fixtures/
│   ├── __init__.py
│   ├── market_data.py             # Sample market data
│   └── database_fixtures.py       # Database test data
├── unit/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_rl_system.py
│   ├── test_technical_indicators.py
│   ├── test_cross_asset.py
│   ├── test_local_sentiment.py
│   └── test_enhanced_rewards.py
├── integration/
│   ├── __init__.py
│   ├── test_trading_bot.py
│   ├── test_web_dashboard.py
│   ├── test_chart_analysis.py
│   └── test_database_integration.py
├── e2e/
│   ├── __init__.py
│   ├── test_trading_cycle.py
│   └── test_multi_bot_system.py
└── performance/
    ├── __init__.py
    └── test_performance.py
```

## Required Test Dependencies

Add to requirements.txt:
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-timeout>=2.1.0
pytest-mock>=3.11.0
pytest-xdist>=3.3.1  # For parallel test execution
pytest-benchmark>=4.0.0  # For performance testing
responses>=0.23.0  # For mocking HTTP requests
freezegun>=1.2.2  # For time-based testing
faker>=19.0.0  # For generating test data
```

## Post-Test Actions

```bash
# Resume bot if it was paused
rm -f bot_pause.flag
echo "Bot resumed after testing"

# Generate coverage report
coverage html
echo "Coverage report: htmlcov/index.html"

# Optional: Upload coverage to codecov
# codecov -t $CODECOV_TOKEN
```

## Continuous Integration Setup

Create `.github/workflows/tests.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        env:
          BINANCE_API_KEY: ${{ secrets.TEST_BINANCE_API_KEY }}
          BINANCE_SECRET_KEY: ${{ secrets.TEST_BINANCE_SECRET_KEY }}
        run: |
          pytest tests/ -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Success Criteria

Tests pass when:
- All unit tests pass (100% of critical paths)
- All integration tests pass
- Code coverage > 80%
- No critical security vulnerabilities
- All external API calls properly mocked
- Performance benchmarks met:
  - Signal generation < 1s
  - Database queries < 100ms
  - Web dashboard response < 500ms

## Test Execution

After creating the test files, run:
```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
```

View the HTML coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```
