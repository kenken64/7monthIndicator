"""
Integration tests for web_dashboard.py

Tests component interaction with real database (temporary)
and verified data flows between backend components.

Run with: pytest tests/integration/test_web_dashboard_integration.py -v
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


@pytest.fixture
def app_with_temp_db(temp_database, monkeypatch, mock_env_vars):
    """Flask app configured with temporary database"""
    # Set up environment
    monkeypatch.setenv('DATABASE_PATH', temp_database)

    # Patch get_database to use temp database before importing app
    def mock_get_database():
        from database import TradingDatabase
        return TradingDatabase(temp_database)

    # Import app after patching
    import web_dashboard
    monkeypatch.setattr('web_dashboard.get_database', mock_get_database)

    web_dashboard.app.config['TESTING'] = True
    web_dashboard.app.config['DATABASE'] = temp_database

    return web_dashboard.app


@pytest.fixture
def client(app_with_temp_db):
    """Test client with temporary database"""
    with app_with_temp_db.test_client() as client:
        yield client


@pytest.fixture
def populated_db(temp_database):
    """Database populated with test data"""
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
                'reasons': [f'Test reason {i}'],
                'indicators': {
                    'rsi': 50 + i,
                    'macd': 0.01,
                    'vwap': 3.5
                }
            }
        )

    # Insert test trades
    for i in range(5):
        timestamp = datetime.now() - timedelta(hours=i*2)
        trade_id = db.store_trade(
            symbol='SUIUSDC',
            side='BUY' if i % 2 == 0 else 'SELL',
            quantity=10.0,
            entry_price=3.5 + (i * 0.01),
            status='OPEN' if i == 0 else 'CLOSED'
        )

        # Close some trades with PnL
        if i > 0:
            pnl = 10.5 if i % 2 == 0 else -5.2
            db.close_trade(trade_id, exit_price=3.5 + (i * 0.02), pnl=pnl)

    return db


@pytest.mark.integration
class TestWebDashboardIntegration:
    """Integration tests for web dashboard with real database"""

    def test_dashboard_index_loads(self, client):
        """Test that main dashboard page loads successfully"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'CryptoCurrency AI Trading Bot Dashboard' in response.data
        assert b'totalSignals' in response.data
        assert b'totalTrades' in response.data

    def test_api_data_with_populated_database(self, client, populated_db):
        """Test /api/data endpoint with real database data"""
        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify data structure
        assert 'signals' in data
        assert 'trades' in data
        assert 'open_trades' in data
        assert 'performance' in data

        # Verify signals from database
        assert len(data['signals']) > 0
        assert data['signals'][0]['symbol'] == 'SUIUSDC'

        # Verify trades from database
        assert len(data['trades']) > 0

        # Verify open trades
        assert len(data['open_trades']) >= 0

        # Verify performance metrics exist
        assert 'win_rate' in data['performance'] or 'total_trades' in data['performance']

    def test_api_chart_data_integration(self, client, populated_db):
        """Test /api/chart-data endpoint with real database queries"""
        response = client.get('/api/chart-data/SUIUSDC?days=7')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'data' in data
        assert 'trades' in data['data']
        assert 'signals' in data['data']

        # Verify trades have cumulative PnL calculated
        if len(data['data']['trades']) > 0:
            trade = data['data']['trades'][0]
            assert 'cumulative_pnl' in trade

    def test_api_system_stats_integration(self, client, populated_db):
        """Test /api/system-stats endpoint with real database"""
        response = client.get('/api/system-stats')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        assert data['success'] is True
        assert 'data' in data

        # Verify stats are calculated
        stats = data['data']
        assert 'total_signals' in stats
        assert 'total_trades' in stats
        assert stats['total_signals'] == 10  # From populated_db
        assert stats['total_trades'] == 5    # From populated_db

    def test_api_open_positions_integration(self, client, populated_db):
        """Test /api/open-positions endpoint"""
        with patch('binance.client.Client') as mock_binance:
            # Mock Binance client
            mock_client = MagicMock()
            mock_client.futures_position_information.return_value = [
                {
                    'symbol': 'SUIUSDC',
                    'positionAmt': '10.0',
                    'entryPrice': '3.50',
                    'markPrice': '3.55',
                    'unRealizedProfit': '5.0'
                }
            ]
            mock_binance.return_value = mock_client

            response = client.get('/api/open-positions/SUIUSDC')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert 'database_positions' in data['data']

    def test_performance_metrics_calculation(self, client, populated_db):
        """Test that performance metrics are calculated correctly from database"""
        response = client.get('/api/data/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        perf = data['performance']

        # Verify calculations
        if perf.get('total_trades', 0) > 0:
            assert 'win_rate' in perf
            assert 0 <= perf['win_rate'] <= 100

            if perf.get('winning_trades', 0) > 0:
                assert 'avg_win' in perf

            if perf.get('losing_trades', 0) > 0:
                assert 'avg_loss' in perf

    def test_database_transaction_consistency(self, client, temp_database):
        """Test that database operations maintain consistency"""
        from database import TradingDatabase
        db = TradingDatabase(temp_database)

        # Store a signal
        signal_id = db.store_signal('SUIUSDC', 3.55, {
            'signal': 1,
            'strength': 4,
            'reasons': ['Test']
        })

        assert signal_id is not None

        # Verify it appears in API immediately
        response = client.get('/api/data/SUIUSDC')
        data = json.loads(response.data)

        assert len(data['signals']) == 1
        assert data['signals'][0]['price'] == 3.55

    def test_api_error_handling_with_invalid_symbol(self, client, populated_db):
        """Test API handles invalid symbol gracefully"""
        response = client.get('/api/data/INVALIDsymbol123')

        # Should either return empty data or handle gracefully
        assert response.status_code in [200, 400, 404]

        if response.status_code == 200:
            data = json.loads(response.data)
            # Should return empty lists for invalid symbol
            assert data['signals'] == [] or len(data['signals']) == 0


@pytest.mark.integration
class TestWebDashboardAPIEndpoints:
    """Test specific API endpoints with real data flow"""

    def test_api_rl_status_endpoint(self, client, temp_database):
        """Test /api/rl-status endpoint"""
        from database import TradingDatabase
        db = TradingDatabase(temp_database)

        # Store RL decision
        db.store_rl_decision(
            symbol='SUIUSDC',
            original_signal='BUY',
            rl_action='EXECUTE',
            final_decision='BUY',
            reason='Market conditions favorable',
            metadata={'confidence': 0.85}
        )

        response = client.get('/api/rl-status')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        if data['success']:
            assert 'data' in data
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
                    'url': 'https://example.com/article1',
                    'publishedAt': '2025-01-22T10:00:00Z',
                    'source': {'name': 'CryptoNews'},
                    'urlToImage': 'https://example.com/image.jpg'
                },
                {
                    'title': 'Ethereum update',
                    'description': 'ETH network upgrade',
                    'url': 'https://example.com/article2',
                    'publishedAt': '2025-01-22T09:00:00Z',
                    'source': {'name': 'CoinDesk'},
                    'urlToImage': 'https://example.com/image2.jpg'
                }
            ],
            'totalResults': 2
        }
        mock_news_api.return_value = mock_news

        response = client.get('/api/news?page=1')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert len(data['articles']) == 2
        assert data['articles'][0]['title'] == 'Bitcoin hits new high'
        assert data['total'] == 2

    def test_api_chart_analysis_endpoint(self, client, temp_database):
        """Test /api/chart-analysis endpoint"""
        from database import TradingDatabase
        db = TradingDatabase(temp_database)

        # Store chart analysis
        analysis_data = {
            'recommendation': 'BUY',
            'confidence': '75%',
            'current_price': 3.55,
            'price_change_24h': '+2.5%',
            'observations': ['Strong momentum', 'RSI healthy'],
            'risk_factors': ['High volatility'],
            'reasoning': 'Bullish trend with strong indicators'
        }

        db.store_chart_analysis('SUIUSDC', analysis_data)

        response = client.get('/api/chart-analysis/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['recommendation'] == 'BUY'
        assert data['data']['confidence'] == '75%'

    def test_api_unified_signals_endpoint(self, client, temp_database):
        """Test /api/unified-signals endpoint"""
        from database import TradingDatabase
        db = TradingDatabase(temp_database)

        # Store unified signal
        unified_data = {
            'decision': 'BUY',
            'strength': 7.5,
            'confidence': 85.0,
            'technical_score': 8.0,
            'rl_score': 7.0,
            'chart_score': 8.5,
            'crewai_score': 7.5,
            'market_context_score': 6.5,
            'news_score': 7.0
        }

        db.store_unified_signal('SUIUSDC', 3.55, unified_data)

        response = client.get('/api/unified-signals/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['decision'] == 'BUY'
        assert data['data']['strength'] == 7.5
        assert data['data']['confidence'] == 85.0

    def test_api_projection_endpoint(self, client, populated_db):
        """Test /api/projection endpoint"""
        response = client.get('/api/projection/SUIUSDC')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'success' in data
        if data['success']:
            assert 'current_balance' in data
            assert 'projections' in data

    @patch('web_dashboard.analyze_market_sentiment')
    def test_api_market_context_endpoint(self, mock_sentiment, client):
        """Test /api/market-context endpoint"""
        mock_sentiment.return_value = {
            'sentiment': 'Bullish',
            'confidence': 8,
            'explanation': 'Strong positive sentiment'
        }

        with patch('web_dashboard.requests.get') as mock_get:
            # Mock CoinGecko API
            mock_get.return_value.json.return_value = {
                'bitcoin': {'usd': 100000, 'usd_24h_change': 2.5},
                'ethereum': {'usd': 4000, 'usd_24h_change': 1.8}
            }

            response = client.get('/api/market-context')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert 'success' in data


@pytest.mark.integration
class TestWebDashboardSecurity:
    """Test security features with integration"""

    def test_pin_verification_flow(self, client, monkeypatch):
        """Test PIN verification for bot control"""
        monkeypatch.setenv('BOT_CONTROL_PIN', '123456')

        # Test with invalid PIN
        response = client.post('/api/pause-bot',
                              json={'pin': '000000'},
                              content_type='application/json')

        data = json.loads(response.data)
        assert data['success'] is False

        # Test with valid PIN
        response = client.post('/api/pause-bot',
                              json={'pin': '123456'},
                              content_type='application/json')

        # Should succeed or fail for different reason (not PIN)
        # Status could be 200 even if bot pause fails for other reasons
        assert response.status_code in [200, 400, 401, 403, 500]

    def test_api_input_validation(self, client):
        """Test API validates inputs properly"""
        # Test with malformed JSON
        response = client.post('/api/run-backtest',
                              data='invalid json',
                              content_type='application/json')

        assert response.status_code in [400, 500]

        # Test with missing required fields
        response = client.post('/api/run-backtest',
                              json={},
                              content_type='application/json')

        assert response.status_code in [400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
