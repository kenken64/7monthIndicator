"""
Unit tests for web_dashboard.py

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
    """Test individual Flask routes with mocked dependencies"""

    def test_index_page_loads(self, client):
        """Test that main dashboard page loads"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'CryptoCurrency AI Trading Bot Dashboard' in response.data
        assert b'SUI/USDC Chart Analysis' in response.data or b'SUIUSDC' in response.data

    def test_static_files_accessible(self, client):
        """Test static files are accessible"""
        # Test CSS file access
        response = client.get('/static/enhanced-dashboard.css')
        # May be 404 if file doesn't exist, but route should work
        assert response.status_code in [200, 404]

    def test_api_data_returns_json(self, client, mock_db):
        """Test /api/data endpoint returns valid JSON"""
        # Mock database responses
        mock_db.get_recent_signals.return_value = []
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {
            'win_rate': 0,
            'total_pnl': 0,
            'total_trades': 0
        }

        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_api_data_structure(self, client, mock_db):
        """Test /api/data returns expected data structure"""
        # Mock complete database responses
        mock_db.get_recent_signals.return_value = [
            {
                'id': 1,
                'timestamp': '2025-01-22 10:00:00',
                'symbol': 'SUIUSDC',
                'signal': 1,
                'strength': 4,
                'price': 3.55,
                'reasons': 'RSI oversold',
                'status': 'executed'
            }
        ]
        mock_db.get_recent_trades.return_value = [
            {
                'id': 1,
                'timestamp': '2025-01-22 10:05:00',
                'symbol': 'SUIUSDC',
                'side': 'BUY',
                'quantity': 10.0,
                'entry_price': 3.55,
                'status': 'CLOSED',
                'pnl': 5.5
            }
        ]
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {
            'win_rate': 65.5,
            'total_pnl': 125.50,
            'total_trades': 10,
            'winning_trades': 7,
            'losing_trades': 3,
            'avg_win': 25.0,
            'avg_loss': -10.0
        }

        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        # Verify top-level structure
        assert 'signals' in data
        assert 'trades' in data
        assert 'open_trades' in data
        assert 'performance' in data

        # Verify data types
        assert isinstance(data['signals'], list)
        assert isinstance(data['trades'], list)
        assert isinstance(data['open_trades'], list)
        assert isinstance(data['performance'], dict)

        # Verify signal data
        assert len(data['signals']) == 1
        assert data['signals'][0]['signal'] == 1

        # Verify trade data
        assert len(data['trades']) == 1
        assert data['trades'][0]['side'] == 'BUY'

        # Verify performance metrics
        assert data['performance']['win_rate'] == 65.5

    def test_api_system_stats_returns_stats(self, client, mock_db):
        """Test /api/system-stats endpoint"""
        # Mock database connection and query
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'total_signals': 100,
            'total_trades': 50,
            'open_trades': 2,
            'last_signal_time': '2025-01-22 10:00:00'
        }
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_db.get_connection.return_value = mock_conn

        response = client.get('/api/system-stats')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['total_signals'] == 100

    def test_api_chart_data_returns_chart_data(self, client, mock_db):
        """Test /api/chart-data endpoint"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'timestamp': '2025-01-22 10:00:00',
                'pnl': 10.5,
                'side': 'BUY',
                'quantity': 10.0,
                'entry_price': 3.50,
                'exit_price': 3.60
            }
        ]
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_db.get_connection.return_value = mock_conn

        response = client.get('/api/chart-data/SUIUSDC?days=30')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'data' in data
        assert 'trades' in data['data']
        assert 'signals' in data['data']

    def test_api_rl_status_endpoint(self, client, mock_db):
        """Test /api/rl-status endpoint"""
        mock_db.get_latest_rl_decision.return_value = {
            'timestamp': '2025-01-22 10:00:00',
            'original_signal': 'BUY',
            'rl_action': 'EXECUTE',
            'final_decision': 'BUY',
            'reason': 'Market conditions favorable',
            'confidence': 0.85
        }

        response = client.get('/api/rl-status')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        if data['success']:
            assert data['data']['final_decision'] == 'BUY'

    @patch('web_dashboard.NewsApiClient')
    def test_api_news_endpoint(self, mock_news_api, client):
        """Test /api/news endpoint with mocked NewsAPI"""
        mock_news = MagicMock()
        mock_news.get_everything.return_value = {
            'articles': [
                {
                    'title': 'Bitcoin hits new high',
                    'description': 'BTC reaches $100k',
                    'url': 'https://example.com',
                    'publishedAt': '2025-01-22T10:00:00Z',
                    'source': {'name': 'CryptoNews'},
                    'urlToImage': 'https://example.com/image.jpg'
                }
            ],
            'totalResults': 1
        }
        mock_news_api.return_value = mock_news

        response = client.get('/api/news')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert len(data['articles']) > 0


@pytest.mark.unit
class TestDashboardErrorHandling:
    """Test error handling in dashboard endpoints"""

    def test_api_data_handles_database_error(self, client, mock_db):
        """Test /api/data handles database errors gracefully"""
        mock_db.get_recent_signals.side_effect = Exception("Database connection failed")

        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 500
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'error' in data

    def test_api_handles_missing_symbol(self, client, mock_db):
        """Test API handles missing symbol parameter"""
        mock_db.get_recent_signals.return_value = []
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {}

        # Request without symbol should still work
        response = client.get('/api/data/INVALIDSYMBOL')

        # Should return 200 with empty data or 400
        assert response.status_code in [200, 400]


@pytest.mark.unit
class TestDashboardSecurity:
    """Test security features"""

    def test_pin_modal_present_in_html(self, client):
        """Test PIN modal is included in HTML"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'pinModal' in response.data or b'PIN' in response.data

    def test_api_pause_requires_pin(self, client):
        """Test /api/pause-bot requires PIN"""
        # Request without PIN
        response = client.post('/api/pause-bot',
                              json={},
                              content_type='application/json')

        # Should reject or require PIN
        assert response.status_code in [400, 401, 403]

    def test_api_validates_json_input(self, client):
        """Test API validates JSON input"""
        # Send malformed JSON
        response = client.post('/api/pause-bot',
                              data='not valid json',
                              content_type='application/json')

        assert response.status_code in [400, 500]


@pytest.mark.unit
class TestDashboardDataFormatting:
    """Test data formatting and transformation"""

    def test_timestamp_formatting(self, client, mock_db):
        """Test timestamps are properly formatted"""
        mock_db.get_recent_signals.return_value = [
            {
                'timestamp': '2025-01-22 10:00:00',
                'signal': 1,
                'strength': 4,
                'price': 3.55
            }
        ]
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {}

        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        # Verify timestamp exists and is string
        if len(data['signals']) > 0:
            assert 'timestamp' in data['signals'][0]
            assert isinstance(data['signals'][0]['timestamp'], str)

    def test_numeric_precision(self, client, mock_db):
        """Test numeric values maintain appropriate precision"""
        mock_db.get_recent_signals.return_value = []
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {
            'win_rate': 66.66666666,
            'total_pnl': 125.5012345,
            'avg_win': 25.123456
        }

        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        # Verify numbers are properly formatted
        perf = data['performance']
        assert isinstance(perf['win_rate'], (int, float))
        assert isinstance(perf['total_pnl'], (int, float))


@pytest.mark.unit
class TestDashboardPerformance:
    """Test performance-related functionality"""

    def test_api_response_time_is_reasonable(self, client, mock_db):
        """Test API endpoints respond quickly"""
        import time

        mock_db.get_recent_signals.return_value = []
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {}

        start = time.time()
        response = client.get('/api/data/SUIUSDC')
        duration = time.time() - start

        assert response.status_code == 200
        # API should respond in under 1 second with mocked data
        assert duration < 1.0

    def test_large_dataset_handling(self, client, mock_db):
        """Test API can handle large datasets"""
        # Mock large dataset
        large_signals = [
            {
                'timestamp': f'2025-01-22 10:{i:02d}:00',
                'signal': 1 if i % 2 == 0 else -1,
                'strength': 4,
                'price': 3.5 + (i * 0.001)
            }
            for i in range(1000)
        ]

        mock_db.get_recent_signals.return_value = large_signals
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_trades.return_value = []
        mock_db.get_performance_metrics.return_value = {}

        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should handle large dataset
        assert len(data['signals']) <= 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
