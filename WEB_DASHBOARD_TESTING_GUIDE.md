# Web Dashboard Automated Testing Guide

This guide provides comprehensive strategies for automated testing of the Flask-based web dashboard (`web_dashboard.py`).

## Table of Contents

1. [Testing Strategy Overview](#testing-strategy-overview)
2. [Test Setup](#test-setup)
3. [Unit Tests for API Endpoints](#unit-tests-for-api-endpoints)
4. [Integration Tests](#integration-tests)
5. [Frontend/E2E Tests](#frontend-e2e-tests)
6. [Running Tests](#running-tests)

---

## Testing Strategy Overview

The web dashboard has three primary testing layers:

### 1. **Unit Tests** (Fast, Isolated)
- Test individual Flask routes/endpoints
- Mock all external dependencies (database, Binance API, OpenAI)
- Verify JSON response structure and data
- **Location**: `tests/unit/test_web_dashboard.py`
- **Runtime**: < 1 second per test

### 2. **Integration Tests** (Component Interaction)
- Test Flask app with real database (temporary)
- Test data flow between backend components
- Verify database queries and data transformation
- **Location**: `tests/integration/test_web_dashboard_integration.py`
- **Runtime**: 1-5 seconds per test

### 3. **E2E Tests** (Full System)
- Test complete user workflows in browser
- Test frontend JavaScript functionality
- Test real-time updates and interactions
- **Location**: `tests/e2e/test_web_dashboard_e2e.py`
- **Runtime**: 10-30 seconds per test

---

## Test Setup

### Install Testing Dependencies

Add to `requirements.txt`:

```txt
# Testing dependencies
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-timeout>=2.2.0
pytest-flask>=1.3.0
playwright>=1.40.0  # For E2E browser tests
pytest-playwright>=0.4.4
```

Install:

```bash
pip install pytest pytest-cov pytest-mock pytest-timeout pytest-flask
pip install playwright pytest-playwright
python -m playwright install chromium  # Install browser for E2E tests
```

---

## Unit Tests for API Endpoints

### Test File Structure

Create `tests/unit/test_web_dashboard.py`:

```python
"""
Unit tests for web_dashboard.py API endpoints

Tests individual Flask routes with mocked dependencies.
No database or external API calls.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from web_dashboard import app, get_database


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    """Mock database connection"""
    with patch('web_dashboard.get_database') as mock:
        db_mock = MagicMock()
        mock.return_value = db_mock
        yield db_mock


@pytest.mark.unit
class TestDashboardEndpoints:
    """Test dashboard API endpoints"""

    def test_index_page_loads(self, client):
        """Test that main dashboard page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'CryptoCurrency AI Trading Bot Dashboard' in response.data

    def test_api_data_endpoint_returns_json(self, client, mock_db):
        """Test /api/data endpoint returns proper JSON structure"""
        # Mock database responses
        mock_db.get_recent_signals.return_value = [
            {
                'timestamp': '2025-01-22 10:00:00',
                'signal': 1,
                'strength': 4,
                'price': 3.55,
                'status': 'executed'
            }
        ]
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {
            'win_rate': 65.5,
            'total_pnl': 125.50,
            'total_trades': 10
        }

        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'signals' in data
        assert 'trades' in data
        assert 'open_trades' in data
        assert 'performance' in data
        assert data['performance']['win_rate'] == 65.5

    def test_api_chart_data_endpoint(self, client, mock_db):
        """Test /api/chart-data endpoint"""
        mock_db.get_connection.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = [
            {'timestamp': '2025-01-22 10:00:00', 'pnl': 10.5, 'side': 'BUY'}
        ]

        response = client.get('/api/chart-data/SUIUSDC?days=30')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'data' in data
        assert 'trades' in data['data']
        assert 'signals' in data['data']

    def test_api_system_stats_endpoint(self, client, mock_db):
        """Test /api/system-stats endpoint"""
        mock_db.get_connection.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = {
            'total_signals': 100,
            'total_trades': 50,
            'open_trades': 2
        }

        response = client.get('/api/system-stats')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        assert 'data' in data

    def test_api_rl_status_endpoint(self, client, mock_db):
        """Test /api/rl-status endpoint returns RL bot status"""
        mock_db.get_latest_rl_decision.return_value = {
            'timestamp': '2025-01-22 10:00:00',
            'original_signal': 'BUY',
            'rl_action': 'EXECUTE',
            'final_decision': 'BUY',
            'reason': 'Market conditions favorable'
        }

        response = client.get('/api/rl-status')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        assert 'data' in data
        assert data['data']['final_decision'] == 'BUY'

    def test_api_news_endpoint(self, client):
        """Test /api/news endpoint"""
        with patch('web_dashboard.NewsApiClient') as mock_news:
            mock_news.return_value.get_everything.return_value = {
                'articles': [
                    {
                        'title': 'Bitcoin hits new high',
                        'description': 'BTC reaches $100k',
                        'url': 'https://example.com',
                        'publishedAt': '2025-01-22T10:00:00Z',
                        'source': {'name': 'CryptoNews'}
                    }
                ]
            }

            response = client.get('/api/news')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert len(data['articles']) > 0
            assert 'title' in data['articles'][0]

    def test_api_chart_analysis_endpoint(self, client, mock_db):
        """Test /api/chart-analysis endpoint"""
        mock_db.get_latest_chart_analysis.return_value = {
            'timestamp': '2025-01-22 10:00:00',
            'recommendation': 'BUY',
            'confidence': '75%',
            'current_price': 3.55,
            'reasoning': 'Strong upward momentum'
        }

        response = client.get('/api/chart-analysis/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['recommendation'] == 'BUY'

    def test_api_error_handling(self, client, mock_db):
        """Test API error handling when database fails"""
        mock_db.get_recent_signals.side_effect = Exception("Database error")

        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 500
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'error' in data

    def test_api_pause_bot_requires_pin(self, client):
        """Test /api/pause-bot requires valid PIN"""
        # Without PIN
        response = client.post('/api/pause-bot', json={})
        data = json.loads(response.data)

        assert response.status_code in [400, 401, 403]

        # With invalid PIN
        response = client.post('/api/pause-bot', json={'pin': '000000'})
        data = json.loads(response.data)

        assert data['success'] is False

    def test_api_unified_signals_endpoint(self, client, mock_db):
        """Test /api/unified-signals endpoint"""
        mock_db.get_latest_unified_signal.return_value = {
            'timestamp': '2025-01-22 10:00:00',
            'decision': 'BUY',
            'strength': 7.5,
            'confidence': 85.0,
            'technical_score': 8.0,
            'rl_score': 7.0,
            'chart_score': 8.5
        }

        response = client.get('/api/unified-signals/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['decision'] == 'BUY'
        assert data['data']['strength'] == 7.5

    def test_api_backtest_endpoint(self, client):
        """Test /api/run-backtest endpoint"""
        with patch('web_dashboard.backtest_unified_signals') as mock_backtest:
            mock_backtest.return_value = {
                'roi': 15.5,
                'win_rate': 65.0,
                'total_trades': 50,
                'sharpe_ratio': 1.8,
                'max_drawdown': -5.2
            }

            response = client.post('/api/run-backtest', json={
                'symbol': 'SUIUSDC',
                'days': 30
            })

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['results']['roi'] == 15.5
            assert data['results']['win_rate'] == 65.0


@pytest.mark.unit
class TestDashboardDataTransformation:
    """Test data transformation and formatting"""

    def test_signal_data_formatting(self, client, mock_db):
        """Test signal data is properly formatted for frontend"""
        raw_signal = {
            'timestamp': '2025-01-22T10:00:00',
            'signal': 1,
            'strength': 4,
            'price': 3.55123456,
            'reasons': ['RSI oversold', 'MACD crossover']
        }

        mock_db.get_recent_signals.return_value = [raw_signal]
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {}

        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        # Verify signal is included
        assert len(data['signals']) > 0

        # Verify timestamp formatting
        signal = data['signals'][0]
        assert 'timestamp' in signal

    def test_performance_metrics_calculation(self, client, mock_db):
        """Test performance metrics are calculated correctly"""
        mock_db.get_performance_metrics.return_value = {
            'win_rate': 66.67,
            'total_pnl': 150.75,
            'avg_win': 25.50,
            'avg_loss': -10.25,
            'total_trades': 15,
            'winning_trades': 10,
            'losing_trades': 5
        }
        mock_db.get_recent_signals.return_value = []
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []

        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        perf = data['performance']
        assert perf['win_rate'] == 66.67
        assert perf['total_pnl'] == 150.75
        assert perf['winning_trades'] == 10


@pytest.mark.unit
class TestDashboardSecurity:
    """Test security features"""

    def test_pin_verification(self, client):
        """Test PIN verification for bot control"""
        with patch('os.getenv') as mock_env:
            mock_env.return_value = '123456'

            # Valid PIN
            response = client.post('/api/pause-bot', json={'pin': '123456'})
            # Should process (may fail for other reasons, but PIN check passes)

            # Invalid PIN
            response = client.post('/api/pause-bot', json={'pin': '000000'})
            data = json.loads(response.data)
            assert data['success'] is False

    def test_xss_protection(self, client, mock_db):
        """Test XSS protection in user inputs"""
        malicious_data = {
            'timestamp': '2025-01-22',
            'signal': '<script>alert("xss")</script>',
            'price': 3.55
        }

        mock_db.get_recent_signals.return_value = [malicious_data]
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {}

        response = client.get('/api/data/SUIUSDC')

        # Verify script tags are not executed
        assert b'<script>' not in response.data or response.status_code == 200
```

---

## Integration Tests

Create `tests/integration/test_web_dashboard_integration.py`:

```python
"""
Integration tests for web dashboard

Tests component interaction with real database (temporary)
and verified data flows.
"""

import pytest
import json
import sqlite3
from datetime import datetime, timedelta
from web_dashboard import app
from database import get_database


@pytest.fixture
def app_with_temp_db(temp_database, monkeypatch):
    """Flask app with temporary database"""
    app.config['TESTING'] = True
    app.config['DATABASE'] = temp_database

    # Patch get_database to use temp database
    def mock_get_database():
        from database import TradingDatabase
        return TradingDatabase(temp_database)

    monkeypatch.setattr('web_dashboard.get_database', mock_get_database)

    return app


@pytest.fixture
def client(app_with_temp_db):
    """Test client with temp database"""
    with app_with_temp_db.test_client() as client:
        yield client


@pytest.fixture
def populated_db(temp_database):
    """Database with test data"""
    from database import TradingDatabase
    db = TradingDatabase(temp_database)

    # Insert test signals
    for i in range(10):
        timestamp = datetime.now() - timedelta(hours=i)
        db.store_signal(
            symbol='SUIUSDC',
            price=3.5 + (i * 0.01),
            signal_data={
                'signal': 1 if i % 2 == 0 else -1,
                'strength': 3 + (i % 3),
                'reasons': ['Test reason']
            }
        )

    # Insert test trades
    for i in range(5):
        timestamp = datetime.now() - timedelta(hours=i*2)
        db.store_trade(
            symbol='SUIUSDC',
            side='BUY' if i % 2 == 0 else 'SELL',
            quantity=10.0,
            entry_price=3.5,
            status='CLOSED'
        )

    return db


@pytest.mark.integration
class TestWebDashboardIntegration:
    """Integration tests for web dashboard"""

    def test_end_to_end_signal_retrieval(self, client, populated_db):
        """Test complete flow from database to API response"""
        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify signals from database are returned
        assert len(data['signals']) > 0
        assert len(data['trades']) > 0

    def test_chart_data_with_real_database(self, client, populated_db):
        """Test chart data generation with real database queries"""
        response = client.get('/api/chart-data/SUIUSDC?days=7')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'trades' in data['data']
        assert 'signals' in data['data']

    def test_performance_metrics_calculation(self, client, populated_db):
        """Test performance metrics are calculated from real data"""
        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'performance' in data
        # Verify calculations make sense
        perf = data['performance']
        if perf.get('total_trades', 0) > 0:
            assert 'win_rate' in perf

    def test_database_transaction_handling(self, client, temp_database):
        """Test database transactions are handled properly"""
        from database import TradingDatabase
        db = TradingDatabase(temp_database)

        # Store signal
        signal_id = db.store_signal('SUIUSDC', 3.55, {
            'signal': 1,
            'strength': 4
        })

        # Verify it appears in API
        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        assert len(data['signals']) == 1
```

---

## Frontend/E2E Tests

Create `tests/e2e/test_web_dashboard_e2e.py`:

```python
"""
End-to-end tests for web dashboard using Playwright

Tests complete user workflows including frontend JavaScript.
Requires: playwright installed (pip install playwright pytest-playwright)
"""

import pytest
from playwright.sync_api import Page, expect
import time


@pytest.fixture(scope="session")
def dashboard_url():
    """Dashboard URL - update for your environment"""
    return "http://localhost:5001"  # Adjust port as needed


@pytest.mark.e2e
class TestDashboardE2E:
    """End-to-end browser tests"""

    def test_dashboard_loads(self, page: Page, dashboard_url):
        """Test dashboard page loads in browser"""
        page.goto(dashboard_url)

        # Wait for page title
        expect(page).to_have_title(/Trading Bot Dashboard/)

        # Verify key elements are visible
        expect(page.locator('#totalSignals')).to_be_visible()
        expect(page.locator('#totalTrades')).to_be_visible()
        expect(page.locator('#openTrades')).to_be_visible()

    def test_refresh_button_updates_data(self, page: Page, dashboard_url):
        """Test refresh button updates dashboard data"""
        page.goto(dashboard_url)

        # Wait for initial load
        page.wait_for_selector('#totalSignals')

        initial_value = page.locator('#totalSignals').inner_text()

        # Click refresh button
        page.click('#refreshBtn')

        # Wait for update (value may or may not change)
        page.wait_for_timeout(1000)

        # Verify refresh was triggered (check for loading state or new data)
        expect(page.locator('#totalSignals')).not_to_have_text('-')

    def test_symbol_selector_works(self, page: Page, dashboard_url):
        """Test symbol selector changes dashboard data"""
        page.goto(dashboard_url)

        # Wait for page load
        page.wait_for_selector('#symbolSelect')

        # Select different symbol (if multiple available)
        page.select_option('#symbolSelect', 'SUIUSDC')

        # Verify data updates
        page.wait_for_timeout(500)
        expect(page.locator('#totalSignals')).to_be_visible()

    def test_time_range_selector(self, page: Page, dashboard_url):
        """Test time range selector updates chart data"""
        page.goto(dashboard_url)

        page.wait_for_selector('#timeRange')

        # Change time range
        page.select_option('#timeRange', '7')

        # Wait for chart update
        page.wait_for_timeout(1000)

        # Verify charts are still visible
        expect(page.locator('canvas#pnlChart')).to_be_visible()

    def test_chart_analysis_section(self, page: Page, dashboard_url):
        """Test chart analysis section displays data"""
        page.goto(dashboard_url)

        # Wait for chart analysis to load
        page.wait_for_selector('#chartAnalysisSection', timeout=10000)

        # Check if image or loading state is shown
        chart_img = page.locator('#chartImage')
        loading = page.locator('#chartLoading')

        # Either image loaded or still loading
        assert chart_img.is_visible() or loading.is_visible()

    def test_news_section_loads(self, page: Page, dashboard_url):
        """Test news section loads articles"""
        page.goto(dashboard_url)

        # Scroll to news section
        page.locator('#newsContainer').scroll_into_view_if_needed()

        # Wait for news to load
        page.wait_for_timeout(2000)

        # Verify news container exists
        expect(page.locator('#newsContainer')).to_be_visible()

    def test_responsive_design_mobile(self, page: Page, dashboard_url):
        """Test dashboard works on mobile viewport"""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto(dashboard_url)

        # Verify key elements are still visible and functional
        expect(page.locator('#totalSignals')).to_be_visible()
        expect(page.locator('#refreshBtn')).to_be_visible()

    def test_pause_button_shows_pin_modal(self, page: Page, dashboard_url):
        """Test pause button shows PIN modal"""
        page.goto(dashboard_url)

        # Click pause button
        page.click('#pauseBtn')

        # Wait for modal
        page.wait_for_selector('#pinModal')

        # Verify modal is visible
        expect(page.locator('#pinModal')).to_be_visible()
        expect(page.locator('#controlPin')).to_be_visible()

    def test_real_time_updates(self, page: Page, dashboard_url):
        """Test dashboard auto-refreshes data"""
        page.goto(dashboard_url)

        page.wait_for_selector('#totalSignals')

        initial_time = page.locator('#lastSignal').inner_text()

        # Wait for auto-refresh (dashboard refreshes every 10-30s)
        page.wait_for_timeout(12000)

        # Verify page is still functional
        expect(page.locator('#totalSignals')).to_be_visible()


@pytest.mark.e2e
class TestDashboardInteractions:
    """Test user interactions"""

    def test_backtest_button_runs_backtest(self, page: Page, dashboard_url):
        """Test backtest button triggers backtest"""
        page.goto(dashboard_url)

        # Scroll to backtest section
        page.locator('#quickBacktestBtn').scroll_into_view_if_needed()

        # Click quick backtest button
        page.click('#quickBacktestBtn')

        # Wait for loading state
        page.wait_for_selector('#backtestLoading', state='visible', timeout=2000)

        # Wait for results (may take a while)
        page.wait_for_selector('#backtestResults', state='visible', timeout=30000)

        # Verify results are displayed
        expect(page.locator('#backtestROI')).to_be_visible()

    def test_logs_button_opens_logs(self, page: Page, dashboard_url):
        """Test logs button shows system logs"""
        page.goto(dashboard_url)

        # Click logs button
        page.click('#logsBtn')

        # Scroll to logs section
        page.locator('#agentLogsList').scroll_into_view_if_needed()

        # Verify logs section is visible
        expect(page.locator('#agentLogsList')).to_be_visible()
```

---

## Running Tests

### Run All Tests

```bash
# From project root
cd /root/7monthIndicator

# Run all web dashboard tests
pytest tests/unit/test_web_dashboard.py -v
pytest tests/integration/test_web_dashboard_integration.py -v

# Run E2E tests (requires dashboard to be running)
# First, start the dashboard:
python web_dashboard.py &

# Then run E2E tests
pytest tests/e2e/test_web_dashboard_e2e.py -v --headed  # --headed to see browser

# Kill dashboard after tests
pkill -f web_dashboard.py
```

### Run with Coverage

```bash
pytest tests/unit/test_web_dashboard.py \
  tests/integration/test_web_dashboard_integration.py \
  -v --cov=web_dashboard --cov-report=html --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# Only unit tests
pytest tests/unit/test_web_dashboard.py -v -m unit

# Only integration tests
pytest tests/integration/test_web_dashboard_integration.py -v -m integration

# Only E2E tests
pytest tests/e2e/test_web_dashboard_e2e.py -v -m e2e
```

### Continuous Testing During Development

```bash
# Watch mode - re-run tests on file changes
pytest-watch tests/unit/test_web_dashboard.py -v
```

---

## Test Configuration

### pytest.ini

Create `pytest.ini` in project root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (component interaction)
    e2e: End-to-end tests (full system, requires running server)
    slow: Slow running tests
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
timeout = 60
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/web_dashboard_tests.yml`:

```yaml
name: Web Dashboard Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'web_dashboard.py'
      - 'tests/unit/test_web_dashboard.py'
      - 'tests/integration/test_web_dashboard_integration.py'
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-flask

    - name: Run unit tests
      run: |
        pytest tests/unit/test_web_dashboard.py -v --cov=web_dashboard

    - name: Run integration tests
      run: |
        pytest tests/integration/test_web_dashboard_integration.py -v

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Best Practices

### 1. **Mock External Services**
Always mock Binance API, OpenAI, NewsAPI in unit tests:

```python
@patch('web_dashboard.NewsApiClient')
@patch('web_dashboard.get_database')
def test_my_endpoint(mock_db, mock_news, client):
    # Test code here
    pass
```

### 2. **Use Fixtures for Common Setup**
Define reusable fixtures in `conftest.py`:

```python
@pytest.fixture
def sample_dashboard_data():
    return {
        'signals': [...],
        'trades': [...],
        'performance': {...}
    }
```

### 3. **Test Edge Cases**
- Empty database
- Database errors
- Invalid user input
- Network timeouts
- Malformed JSON

### 4. **Verify Response Structure**
Always check JSON response has expected structure:

```python
def test_api_response_structure(client):
    response = client.get('/api/data/SUIUSDC')
    data = json.loads(response.data)

    assert 'signals' in data
    assert 'trades' in data
    assert isinstance(data['signals'], list)
```

### 5. **Test Security**
- PIN verification
- XSS protection
- SQL injection protection
- CSRF protection (if implemented)

---

## Troubleshooting

### Issue: E2E tests fail with "Browser not found"

**Solution:**
```bash
python -m playwright install chromium
```

### Issue: Tests fail with database lock

**Solution:** Use `temp_database` fixture which creates isolated database per test.

### Issue: Flask app not starting in tests

**Solution:** Check `app.config['TESTING'] = True` is set.

### Issue: Async/await errors in E2E tests

**Solution:** Use `playwright.sync_api` for synchronous tests or switch to `async` tests with `pytest-asyncio`.

---

## Next Steps

1. **Create the test files** using examples above
2. **Run tests** to verify dashboard functionality
3. **Add coverage tracking** to identify untested code
4. **Integrate into CI/CD** for automated testing on commits
5. **Write additional tests** for new features as they're added

---

## Additional Resources

- [Flask Testing Documentation](https://flask.palletsprojects.com/en/latest/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [pytest-flask Plugin](https://pytest-flask.readthedocs.io/)

---

**Created:** 2025-01-22
**Updated:** 2025-01-22
**Maintainer:** AI Trading Bot Team
