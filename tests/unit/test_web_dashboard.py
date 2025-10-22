"""
Unit tests for web_dashboard.py - Updated for actual API routes

Fast, isolated tests with all dependencies mocked.
No database or external API calls.

Run with: pytest tests/unit/test_web_dashboard.py -v
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def app():
    """Flask app in testing mode"""
    import web_dashboard
    web_dashboard.app.config['TESTING'] = True
    return web_dashboard.app


@pytest.fixture
def client(app):
    """Flask test client"""
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    """Mock database for unit tests"""
    with patch('web_dashboard.get_database') as mock:
        db_mock = MagicMock()
        mock.return_value = db_mock
        yield db_mock


@pytest.mark.unit
class TestDashboardRoutes:
    """Test actual web dashboard routes"""

    def test_index_page_loads(self, client):
        """Test that main dashboard page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'CryptoCurrency AI Trading Bot Dashboard' in response.data or b'SUIUSDC' in response.data

    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200

    def test_api_signals_endpoint(self, client, mock_db):
        """Test /api/signals/<symbol> endpoint"""
        mock_db.get_recent_signals.return_value = []

        response = client.get('/api/signals/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'signals' in data or 'success' in data

    def test_api_trades_endpoint(self, client, mock_db):
        """Test /api/trades/<symbol> endpoint"""
        mock_db.get_recent_trades.return_value = []

        response = client.get('/api/trades/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'trades' in data or 'success' in data

    def test_api_performance_endpoint(self, client, mock_db):
        """Test /api/performance/<symbol> endpoint"""
        mock_db.get_performance_metrics.return_value = {
            'win_rate': 0,
            'total_pnl': 0,
            'total_trades': 0
        }

        response = client.get('/api/performance/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data or 'performance' in data

    def test_api_chart_data_endpoint(self, client, mock_db):
        """Test /api/chart-data/<symbol> endpoint"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_db.get_connection.return_value = mock_conn

        response = client.get('/api/chart-data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_api_system_stats_endpoint(self, client, mock_db):
        """Test /api/system-stats endpoint"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'total_signals': 0,
            'total_trades': 0
        }
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_db.get_connection.return_value = mock_conn

        response = client.get('/api/system-stats')

        assert response.status_code == 200

    def test_api_open_positions_endpoint(self, client, mock_db):
        """Test /api/open-positions/<symbol> endpoint"""
        mock_db.get_open_trades.return_value = []

        response = client.get('/api/open-positions/SUIUSDC')

        assert response.status_code == 200

    def test_api_unified_signals_endpoint(self, client, mock_db):
        """Test /api/unified-signals/<symbol> endpoint"""
        mock_db.get_latest_unified_signal.return_value = None

        response = client.get('/api/unified-signals/SUIUSDC')

        assert response.status_code == 200

    def test_api_rl_decisions_endpoint(self, client, mock_db):
        """Test /api/rl-decisions/<symbol> endpoint"""
        mock_db.get_recent_rl_decisions.return_value = []

        response = client.get('/api/rl-decisions/SUIUSDC')

        assert response.status_code == 200


@pytest.mark.unit
class TestDashboardSecurity:
    """Test security features"""

    def test_pin_modal_present_in_html(self, client):
        """Test PIN modal is included in HTML"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'pinModal' in response.data or b'PIN' in response.data

    def test_api_bot_pause_endpoint_exists(self, client):
        """Test /api/bot-pause endpoint exists"""
        response = client.post('/api/bot-pause',
                              json={'pin': '000000'},
                              content_type='application/json')

        # Should respond (not 404), even if PIN is wrong
        assert response.status_code != 404


@pytest.mark.unit
class TestDashboardPerformance:
    """Test performance-related functionality"""

    def test_api_response_time_is_reasonable(self, client, mock_db):
        """Test API endpoints respond quickly"""
        import time

        mock_db.get_recent_signals.return_value = []

        start = time.time()
        response = client.get('/api/signals/SUIUSDC')
        duration = time.time() - start

        assert response.status_code == 200
        # API should respond in under 1 second with mocked data
        assert duration < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
