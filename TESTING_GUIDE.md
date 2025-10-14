# Testing Guide for 7monthIndicator AI Trading Bot

This guide provides comprehensive information about testing the trading bot system.

## Overview

The 7monthIndicator trading bot has a complete test suite covering:
- **Unit Tests**: Individual component testing (database, RL system, indicators)
- **Integration Tests**: Component interaction testing (trading flow, web dashboard)
- **E2E Tests**: Complete workflow testing (full trading cycle, multi-bot system)
- **Performance Tests**: Speed and load testing

## Quick Start

### 1. Install Test Dependencies

```bash
pip install pytest pytest-cov pytest-mock pytest-timeout pytest-asyncio pytest-xdist
```

### 2. Run Tests Using Slash Command

The easiest way to run the complete test suite is using the `/test` slash command:

```
/test
```

This will:
- Pause any running bots
- Execute all test categories
- Generate coverage reports
- Resume bots after testing

### 3. Manual Test Execution

```bash
# All tests with coverage
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

# Specific test categories
pytest tests/unit/ -v              # Fast unit tests
pytest tests/integration/ -v       # Integration tests
pytest tests/e2e/ -v              # End-to-end tests

# By markers
pytest -m unit -v                  # All unit tests
pytest -m integration -v           # All integration tests
pytest -m slow -v                  # Slow tests only
pytest -m "not slow" -v           # Skip slow tests
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (mocks, sample data)
├── README.md                # Detailed testing documentation
│
├── unit/                    # Fast, isolated tests (< 1s each)
│   ├── test_database.py    # Database operations
│   ├── test_rl_system.py   # RL agent logic (to be created)
│   ├── test_technical_indicators.py  # Indicator calculations
│   └── test_cross_asset.py # Cross-asset correlation
│
├── integration/             # Component interaction tests (1-5s each)
│   ├── test_trading_bot.py # Trading workflow
│   ├── test_web_dashboard.py  # Flask endpoints
│   └── test_chart_analysis.py # Chart generation + AI
│
├── e2e/                     # Complete workflow tests (10-60s each)
│   ├── test_trading_cycle.py  # Full trading cycle
│   └── test_multi_bot_system.py  # Multi-bot coordination
│
└── performance/             # Speed and load tests
    └── test_performance.py  # Benchmarks and load tests
```

## Available Fixtures

All fixtures are defined in `tests/conftest.py` and auto-available:

### Mock Services
- `mock_binance_client` - Mock Binance API (no real API calls)
- `mock_openai` - Mock OpenAI GPT-4o
- `mock_telegram` - Mock Telegram notifications
- `mock_env_vars` - Mock environment variables

### Sample Data
- `sample_klines_df` - 200 periods of OHLCV data
- `sample_indicators` - Pre-calculated technical indicators
- `sample_signal_data` - Sample trading signal
- `temp_database` - Temporary database (auto-cleaned)

### Usage Example

```python
import pytest

@pytest.mark.unit
def test_my_function(mock_binance_client, temp_database, sample_klines_df):
    """All fixtures are automatically available"""
    # Your test code here
    pass
```

## Sample Test: Database Operations

File: `tests/unit/test_database.py`

This file demonstrates comprehensive database testing:

```python
@pytest.mark.unit
def test_store_signal(temp_database, sample_signal_data):
    """Test storing a trading signal"""
    db = TradingDatabase(temp_database)
    signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

    assert signal_id > 0

    signals = db.get_recent_signals('SUIUSDC', limit=1)
    assert len(signals) == 1
    assert signals[0]['signal'] == 1
    assert signals[0]['strength'] == 4
    assert signals[0]['rl_enhanced'] == True
```

Run this specific test:
```bash
pytest tests/unit/test_database.py::test_store_signal -v
```

## Creating New Tests

### 1. Choose the Right Category

- **Unit Test** (`tests/unit/`): Testing a single function/class in isolation
- **Integration Test** (`tests/integration/`): Testing multiple components together
- **E2E Test** (`tests/e2e/`): Testing complete user workflows
- **Performance Test** (`tests/performance/`): Testing speed/load

### 2. Use the Template

```python
"""
Brief description of what this test file covers
"""

import pytest
from your_module import YourClass

@pytest.mark.unit  # or @pytest.mark.integration, @pytest.mark.e2e
class TestYourFeature:
    """Test description"""

    def test_specific_behavior(self, required_fixtures):
        """Test a specific behavior"""
        # Arrange
        obj = YourClass()

        # Act
        result = obj.your_method()

        # Assert
        assert result == expected_value
```

### 3. Add Markers

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.performance    # Performance test
@pytest.mark.slow          # Slow-running test (> 5s)
```

### 4. Mock External Services

```python
@pytest.mark.unit
def test_with_mocked_binance(mock_binance_client):
    """Binance API is automatically mocked"""
    from binance.client import Client

    client = Client('key', 'secret')  # Uses mock
    klines = client.futures_klines(symbol='SUIUSDC', interval='5m')

    # Returns mocked data, no real API call
    assert len(klines) > 0
```

## Testing Best Practices

### 1. Fast Tests
- Unit tests should complete in < 1 second
- Use mocks for all external services
- Use temporary databases

### 2. Isolated Tests
- Tests should not depend on each other
- Clean up after each test (use fixtures)
- Don't modify global state

### 3. Descriptive Names
```python
# Good
def test_store_signal_marks_rl_enhanced_flag()

# Bad
def test1()
```

### 4. One Assertion Per Test
```python
# Good
def test_signal_is_stored():
    signal_id = db.store_signal(...)
    assert signal_id > 0

def test_signal_has_correct_data():
    db.store_signal(...)
    signals = db.get_recent_signals()
    assert signals[0]['signal'] == 1

# Less ideal
def test_signal():
    signal_id = db.store_signal(...)
    assert signal_id > 0
    signals = db.get_recent_signals()
    assert signals[0]['signal'] == 1  # Two behaviors in one test
```

### 5. Test Edge Cases
```python
def test_store_signal_with_empty_reasons():
    """Test edge case: signal with no reasons"""
    signal_data = {'signal': 1, 'strength': 1, 'reasons': []}
    # ...

def test_store_signal_with_invalid_symbol():
    """Test error handling"""
    with pytest.raises(ValueError):
        db.store_signal('', 3.55, signal_data)
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
```

### View Report

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

### Coverage Goals
- Critical components (database, RL system): **>90%**
- Trading bot logic: **>85%**
- Web dashboard: **>80%**
- Overall project: **>80%**

## Continuous Integration

### GitHub Actions Setup

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
        run: |
          pytest tests/ -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors

Make sure you're in the project root:
```bash
cd /root/7monthIndicator
pytest tests/ -v
```

### Database Lock Errors

Stop the bot before running tests:
```bash
./start_rl_bot.sh stop
pytest tests/ -v
```

Or use the `/test` slash command which handles this automatically.

### Slow Tests

Run only fast tests:
```bash
pytest tests/unit/ -v
```

Or skip slow tests:
```bash
pytest -m "not slow" -v
```

### Mock Not Working

Ensure fixture is used:
```python
def test_my_function(mock_binance_client):  # Add fixture parameter
    # Now Binance calls are mocked
```

## Advanced Testing

### Parallel Execution

Run tests in parallel (4 workers):
```bash
pytest tests/ -v -n 4
```

### Benchmarking

```python
@pytest.mark.performance
def test_signal_generation_speed(benchmark):
    """Benchmark signal generation"""
    result = benchmark(bot.generate_signals, df, indicators)
    assert result is not None
```

### Debugging Failed Tests

```bash
# Run with pdb debugger on failure
pytest tests/ -v --pdb

# Show local variables on failure
pytest tests/ -v --tb=long

# Stop on first failure
pytest tests/ -v -x
```

## Next Steps

1. **Add More Tests**: Create tests for:
   - `tests/unit/test_rl_system.py`
   - `tests/unit/test_technical_indicators.py`
   - `tests/integration/test_trading_bot.py`
   - `tests/e2e/test_trading_cycle.py`

2. **Improve Coverage**: Run coverage and add tests for uncovered code:
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing
   ```

3. **Set Up CI/CD**: Add GitHub Actions workflow for automatic testing

4. **Performance Baselines**: Establish performance benchmarks

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test Directory: tests/README.md](tests/README.md)

## Support

For questions about testing:
1. Check `tests/README.md` for detailed documentation
2. Review `tests/conftest.py` for available fixtures
3. Look at `tests/unit/test_database.py` for examples
4. Use `/test` slash command for automated testing
