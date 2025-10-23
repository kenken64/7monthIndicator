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

    @patch('binance.client.Client')
    def test_api_trades_endpoint(self, mock_client_class, client, mock_db):
        """Test /api/trades/<symbol> endpoint"""
        mock_db.get_recent_trades.return_value = []

        # Mock Binance Client
        mock_client = MagicMock()
        mock_client.get_symbol_ticker.return_value = {'price': '3.5'}
        mock_client_class.return_value = mock_client

        response = client.get('/api/trades/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data or 'success' in data

    def test_api_performance_endpoint(self, client, mock_db):
        """Test /api/performance/<symbol> endpoint"""
        mock_db.calculate_performance_metrics.return_value = {
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_loss': 0.0,
            'days': 30
        }

        response = client.get('/api/performance/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data and data['success'] is True

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

    @patch('binance.client.Client')
    def test_api_system_stats_endpoint(self, mock_client_class, client, mock_db):
        """Test /api/system-stats endpoint"""
        # Mock Binance Client
        mock_client = MagicMock()
        mock_client.futures_position_information.return_value = []
        mock_client_class.return_value = mock_client

        mock_conn = MagicMock()

        # Create a mock row class that supports dict access
        class MockRow:
            def __init__(self, data):
                self.data = data

            def __getitem__(self, key):
                return self.data.get(key, 0)

        # Mock cursor that returns dict-accessible rows
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = MockRow({'count': 0})
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_db.get_connection.return_value = mock_conn

        response = client.get('/api/system-stats')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data

    def test_api_open_positions_endpoint(self, client, mock_db):
        """Test /api/open-positions/<symbol> endpoint"""
        mock_db.get_open_trades.return_value = []

        response = client.get('/api/open-positions/SUIUSDC')

        assert response.status_code == 200

    @patch('os.path.exists')
    def test_api_unified_signals_endpoint(self, mock_exists, client, mock_db):
        """Test /api/unified-signals/<symbol> endpoint"""
        # Mock that files don't exist to avoid file I/O
        mock_exists.return_value = False

        # Return a proper signal with all required fields
        mock_signal = {
            'timestamp': '2025-01-22 10:00:00',
            'signal': 1,  # Buy signal
            'strength': 4,  # Strength 1-5
            'unified_details': None
        }
        mock_db.get_recent_signals.return_value = [mock_signal]

        response = client.get('/api/unified-signals/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data and data['success'] is True

    def test_api_rl_decisions_endpoint(self, client, mock_db):
        """Test /api/rl-decisions/<symbol> endpoint"""
        # Return list of decision dicts instead of MagicMock
        mock_decisions = [
            {
                'timestamp': '2025-01-22 10:00:00',
                'original_signal': 1,
                'rl_action': 1,
                'final_decision': 1,
                'confidence': 0.8,
                'reasoning': 'Test decision'
            }
        ]
        mock_db.get_recent_rl_signals.return_value = mock_decisions

        response = client.get('/api/rl-decisions/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data and data['success'] is True


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
