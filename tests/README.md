# 7monthIndicator Trading Bot Test Suite

Comprehensive test suite for the AI-powered cryptocurrency trading bot system.

## Quick Start

### Installation

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-timeout pytest-asyncio

# Or use the provided requirements.txt
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
pytest tests/e2e/ -v              # End-to-end tests only

# Run tests by marker
pytest -m "unit" -v               # All unit tests
pytest -m "integration" -v        # All integration tests
pytest -m "slow" -v               # All slow-running tests

# Run specific test file
pytest tests/unit/test_database.py -v

# Run specific test class
pytest tests/unit/test_database.py::TestSignalStorage -v

# Run specific test
pytest tests/unit/test_database.py::TestSignalStorage::test_store_signal -v
```

### Using the Slash Command

From within Claude Code:

```
/test
```

This will execute the comprehensive test suite as defined in `.claude/commands/test.md`.

## Test Structure

```
tests/
├── __init__.py                    # Package initialization
├── conftest.py                    # Shared fixtures and configuration
├── README.md                      # This file
├── fixtures/                      # Test data fixtures
│   ├── __init__.py
│   ├── market_data.py            # Sample market data
│   └── database_fixtures.py      # Database test data
├── unit/                          # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_database.py          # Database operations
│   ├── test_rl_system.py         # RL agent logic
│   ├── test_technical_indicators.py
│   ├── test_cross_asset.py       # Cross-asset correlation
│   └── test_local_sentiment.py   # Sentiment analysis
├── integration/                   # Integration tests (component interaction)
│   ├── __init__.py
│   ├── test_trading_bot.py       # Trading bot workflow
│   ├── test_web_dashboard.py     # Flask endpoints
│   ├── test_chart_analysis.py    # Chart generation and AI analysis
│   └── test_database_integration.py
├── e2e/                          # End-to-end tests (complete workflows)
│   ├── __init__.py
│   ├── test_trading_cycle.py    # Complete trading cycle
│   └── test_multi_bot_system.py # Multi-bot coordination
└── performance/                   # Performance and load tests
    ├── __init__.py
    └── test_performance.py       # Speed and load benchmarks
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests that verify individual components work correctly:

- **Database Tests**: Signal storage, trade tracking, performance metrics
- **RL System Tests**: Q-learning agent, reward calculation, exit conditions
- **Technical Indicators**: EMA, RSI, MACD, VWAP calculations
- **Cross-Asset Correlation**: BTC/ETH data, Fear & Greed Index
- **Sentiment Analysis**: Local keyword-based sentiment

**Characteristics:**
- Run in < 1 second each
- No external API calls (everything mocked)
- No database dependencies (use temp database)
- No network I/O

### Integration Tests (`tests/integration/`)

Tests that verify components work together correctly:

- **Trading Bot Integration**: Signal generation → Trade execution → Position management
- **Web Dashboard**: Flask routes, API endpoints, data flow
- **Chart Analysis**: Chart generation → OpenAI analysis → Result storage
- **Database Integration**: Multi-table operations, transactions

**Characteristics:**
- Run in 1-5 seconds each
- May use temporary database
- Mock external APIs (Binance, OpenAI, Telegram)
- Test component interactions

### E2E Tests (`tests/e2e/`)

Complete system workflow tests:

- **Trading Cycle**: Full cycle from data fetch to position closure
- **Multi-Bot System**: All bots running and coordinating

**Characteristics:**
- Run in 10-60 seconds each
- Test complete user scenarios
- May require system setup/teardown
- Most realistic testing

### Performance Tests (`tests/performance/`)

Speed and load testing:

- Signal generation performance (< 1s target)
- Database query performance (< 100ms target)
- Concurrent access handling
- Memory leak detection

**Characteristics:**
- May run for minutes
- Use benchmarking tools
- Measure time and resources
- Establish performance baselines

## Writing Tests

### Example Unit Test

```python
import pytest
from database import TradingDatabase

@pytest.mark.unit
def test_store_signal(temp_database, sample_signal_data):
    """Test storing a trading signal"""
    db = TradingDatabase(temp_database)
    signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

    assert signal_id > 0

    signals = db.get_recent_signals('SUIUSDC', limit=1)
    assert len(signals) == 1
    assert signals[0]['signal'] == 1
```

### Example Integration Test

```python
import pytest
from rl_bot_ready import RLEnhancedBinanceFuturesBot

@pytest.mark.integration
def test_signal_to_trade_flow(mock_binance_client, temp_database, mock_env_vars):
    """Test complete signal generation and trade execution"""
    bot = RLEnhancedBinanceFuturesBot('SUIUSDC', 50, 2.0)

    # Fetch data and generate signal
    df = bot.get_klines()
    indicators = bot.calculate_indicators(df)
    signal_data = bot.generate_signals(df, indicators)

    # Execute trade
    success = bot.execute_trade(signal_data, 3.55)

    assert success == True
```

### Using Fixtures

Fixtures are defined in `conftest.py` and automatically available:

```python
def test_with_mocked_binance(mock_binance_client):
    """Binance client is automatically mocked"""
    # Your test code here
    pass

def test_with_temp_db(temp_database):
    """Uses temporary database that's auto-cleaned"""
    db = TradingDatabase(temp_database)
    # Your test code here
    pass

def test_with_sample_data(sample_klines_df, sample_indicators):
    """Use pre-made test data"""
    # Your test code here
    pass
```

## Mocking External Services

### Binance API

```python
def test_with_binance_mock(mock_binance_client):
    # All Binance calls are mocked automatically
    client = Client('key', 'secret')
    # Returns mocked data
    klines = client.futures_klines(symbol='SUIUSDC', interval='5m')
```

### OpenAI API

```python
def test_with_openai_mock(mock_openai):
    # OpenAI calls return mocked responses
    response = openai.ChatCompletion.create(...)
    # Returns mocked analysis
```

### Telegram API

```python
def test_with_telegram_mock(mock_telegram):
    # Telegram notifications are mocked
    # Returns success without sending actual messages
```

## Coverage Reports

After running tests with coverage:

```bash
pytest tests/ -v --cov=. --cov-report=html
```

Open the HTML report:

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Or manually navigate to: htmlcov/index.html
```

## Best Practices

1. **Use descriptive test names**: `test_store_signal_with_rl_enhancement()` not `test1()`
2. **One assertion per test**: Focus each test on a single behavior
3. **Use fixtures**: Don't repeat setup code
4. **Mock external services**: Keep tests fast and deterministic
5. **Test edge cases**: Not just the happy path
6. **Clean up**: Tests should not affect each other
7. **Document**: Add docstrings explaining what's being tested

## Troubleshooting

### Tests fail with "Connection refused"

Make sure all external services are mocked:
```python
def test_my_function(mock_binance_client, mock_openai, mock_telegram):
    # Now external calls are mocked
```

### Database errors

Use the `temp_database` fixture:
```python
def test_my_db_function(temp_database):
    db = TradingDatabase(temp_database)
    # Uses temporary database
```

### Import errors

Make sure you're running tests from the project root:
```bash
cd /root/7monthIndicator
pytest tests/ -v
```

### Slow tests

Run only fast unit tests:
```bash
pytest tests/unit/ -v
```

Or skip slow tests:
```bash
pytest -m "not slow" -v
```

## CI/CD Integration

Tests can be run automatically on every commit using GitHub Actions. See `.github/workflows/tests.yml` for configuration.

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest tests/ -v`
3. Check coverage: `pytest tests/ --cov=.`
4. Aim for >80% coverage on new code
5. Add integration tests for new components
6. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
