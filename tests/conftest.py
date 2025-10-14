"""
Shared pytest fixtures and configuration for all tests

This module provides reusable fixtures for mocking external services
and setting up test environments.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_binance_client():
    """Mock Binance API client for testing without real API calls"""
    with patch('binance.client.Client') as mock_client:
        # Configure mock client
        client_instance = Mock()

        # Mock futures_klines
        client_instance.futures_klines.return_value = [
            [1609459200000, '3.5000', '3.6000', '3.4000', '3.5500', '1000000.0',
             1609459260000, '3550000.0', 1000, '500000.0', '1775000.0', '0']
        ] * 200

        # Mock futures_position_information
        client_instance.futures_position_information.return_value = [
            {
                'symbol': 'SUIUSDC',
                'positionAmt': '0',
                'entryPrice': '0',
                'markPrice': '3.5500',
                'unRealizedProfit': '0',
                'liquidationPrice': '0'
            }
        ]

        # Mock futures_account
        client_instance.futures_account.return_value = {
            'assets': [
                {'asset': 'USDC', 'walletBalance': '1000.0', 'availableBalance': '1000.0'}
            ]
        }

        # Mock order creation
        client_instance.futures_create_order.return_value = {
            'orderId': 12345,
            'symbol': 'SUIUSDC',
            'status': 'FILLED'
        }

        # Mock ticker
        client_instance.get_symbol_ticker.return_value = {
            'symbol': 'SUIUSDC',
            'price': '3.5500'
        }

        # Mock open orders
        client_instance.futures_get_open_orders.return_value = []

        # Mock cancel orders
        client_instance.futures_cancel_all_open_orders.return_value = []

        mock_client.return_value = client_instance
        yield mock_client


@pytest.fixture
def mock_openai():
    """Mock OpenAI API for chart analysis testing"""
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="""
                        **Recommendation**: BUY
                        **Confidence**: 75%
                        **Key Observations**:
                        - Strong upward momentum
                        - RSI in healthy range
                        - MACD bullish crossover
                        **Risk Factors**:
                        - Market volatility
                        """
                    )
                )
            ]
        )
        yield mock


@pytest.fixture
def mock_telegram():
    """Mock Telegram API for notification testing"""
    with patch('requests.post') as mock:
        mock.return_value = MagicMock(
            status_code=200,
            text='{"ok":true}'
        )
        yield mock


@pytest.fixture
def sample_klines_df():
    """Sample DataFrame with OHLCV data for testing"""
    dates = pd.date_range(start='2025-01-01', periods=200, freq='5min')
    return pd.DataFrame({
        'timestamp': dates,
        'open': [3.5 + (i * 0.01) for i in range(200)],
        'high': [3.6 + (i * 0.01) for i in range(200)],
        'low': [3.4 + (i * 0.01) for i in range(200)],
        'close': [3.55 + (i * 0.01) for i in range(200)],
        'volume': [1000000.0] * 200
    })


@pytest.fixture
def sample_indicators():
    """Sample technical indicators for testing"""
    return {
        'ema_9': 3.55,
        'ema_21': 3.50,
        'ema_50': 3.45,
        'ema_200': 3.40,
        'rsi': 65.2,
        'macd': 0.01,
        'macd_signal': 0.005,
        'macd_histogram': 0.005,
        'vwap': 3.52
    }


@pytest.fixture
def sample_signal_data():
    """Sample signal data for testing"""
    return {
        'signal': 1,  # BUY
        'strength': 4,
        'reasons': [
            'RSI neutral (65.2)',
            'MACD bullish crossover',
            'Price above VWAP (+0.85%)',
            'EMA bullish alignment (9>21>50)'
        ],
        'indicators': {
            'rsi': 65.2,
            'macd': 0.01,
            'vwap': 3.52,
            'ema_9': 3.55,
            'ema_21': 3.50
        },
        'rl_enhanced': True
    }


@pytest.fixture
def temp_database(tmp_path):
    """Temporary database for testing"""
    db_path = tmp_path / "test_trading_bot.db"
    return str(db_path)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv('BINANCE_API_KEY', 'test_api_key')
    monkeypatch.setenv('BINANCE_SECRET_KEY', 'test_secret_key')
    monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test_telegram_token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '@test_chat')
    monkeypatch.setenv('BOT_CONTROL_PIN', '123456')
    monkeypatch.setenv('NEWS_API_KEY', 'test_news_key')
    monkeypatch.setenv('USE_LOCAL_SENTIMENT', 'true')


@pytest.fixture(autouse=True)
def cleanup_pause_flag():
    """Automatically cleanup pause flag after each test"""
    yield
    if os.path.exists('bot_pause.flag'):
        os.remove('bot_pause.flag')


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
