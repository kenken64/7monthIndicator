# Testing Quick Reference

## Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_database.py -v

# Run specific test
pytest tests/unit/test_database.py::TestSignalStorage::test_store_signal -v

# Run by category
pytest tests/unit/ -v              # Unit tests
pytest tests/integration/ -v       # Integration tests
pytest tests/e2e/ -v              # E2E tests

# Run by marker
pytest -m unit -v                  # All unit tests
pytest -m integration -v           # All integration tests
pytest -m "not slow" -v           # Skip slow tests

# Stop on first failure
pytest tests/ -v -x

# Run with debugger
pytest tests/ -v --pdb

# Parallel execution (4 workers)
pytest tests/ -v -n 4
```

## Slash Command

```
/test
```

Automatically:
- Pauses running bots
- Runs complete test suite
- Generates coverage reports
- Resumes bots

## Available Fixtures

From `conftest.py`:

### Mocks
- `mock_binance_client` - Binance API
- `mock_openai` - OpenAI GPT-4o
- `mock_telegram` - Telegram notifications
- `mock_env_vars` - Environment variables

### Data
- `sample_klines_df` - OHLCV DataFrame
- `sample_indicators` - Technical indicators
- `sample_signal_data` - Trading signal
- `temp_database` - Temporary DB

## Writing a Test

```python
import pytest

@pytest.mark.unit
def test_my_feature(mock_binance_client, temp_database):
    """Test description"""
    # Arrange
    setup_data = ...

    # Act
    result = function_to_test()

    # Assert
    assert result == expected
```

## Test Markers

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.e2e           # E2E test
@pytest.mark.performance    # Performance test
@pytest.mark.slow          # Slow test (>5s)
```

## Coverage

```bash
# Generate HTML report
pytest tests/ --cov=. --cov-report=html

# View report
open htmlcov/index.html      # macOS
xdg-open htmlcov/index.html  # Linux

# Show missing lines
pytest tests/ --cov=. --cov-report=term-missing
```

## Debugging

```bash
# Show print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ -v --tb=long

# Drop into debugger on failure
pytest tests/ -v --pdb

# Run last failed tests
pytest --lf -v
```

## Common Issues

### Import Error
```bash
# Run from project root
cd /root/7monthIndicator
pytest tests/ -v
```

### Database Locked
```bash
# Stop bot first
./start_rl_bot.sh stop
pytest tests/ -v

# Or use /test command (auto-pauses)
```

### Mock Not Working
```python
# Add fixture parameter
def test_function(mock_binance_client):
    # Now mocked
```

## File Locations

- **Tests**: `tests/`
- **Fixtures**: `tests/conftest.py`
- **Documentation**: `tests/README.md`
- **Guide**: `TESTING_GUIDE.md`
- **Slash Command**: `.claude/commands/test.md`

## Test Structure

```
tests/
├── unit/           # Fast (<1s), isolated
├── integration/    # Medium (1-5s), component interaction
├── e2e/           # Slow (10-60s), complete workflows
└── performance/    # Variable, benchmarks
```

## Example: Database Test

```python
@pytest.mark.unit
def test_store_signal(temp_database, sample_signal_data):
    db = TradingDatabase(temp_database)
    signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

    assert signal_id > 0
```

## CI/CD

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
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ -v --cov=.
```

## Resources

- Full docs: `tests/README.md`
- Testing guide: `TESTING_GUIDE.md`
- pytest docs: https://docs.pytest.org/
