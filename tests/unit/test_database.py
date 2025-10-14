"""
Unit tests for database.py - TradingDatabase class

Tests all database operations including signal storage, trade tracking,
performance metrics, and market context management.
"""

import pytest
import json
from datetime import datetime
from database import TradingDatabase, get_database


@pytest.mark.unit
class TestDatabaseInitialization:
    """Test database initialization and table creation"""

    def test_database_creation(self, temp_database):
        """Test database file is created"""
        db = TradingDatabase(temp_database)
        assert db.db_path == temp_database

    def test_tables_exist(self, temp_database):
        """Test all required tables are created"""
        db = TradingDatabase(temp_database)
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row['name'] for row in cursor.fetchall()]

            assert 'signals' in tables
            assert 'trades' in tables
            assert 'market_data' in tables
            assert 'performance' in tables
            assert 'market_context' in tables

    def test_indexes_created(self, temp_database):
        """Test indexes are created for performance"""
        db = TradingDatabase(temp_database)
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row['name'] for row in cursor.fetchall()]

            assert 'idx_signals_timestamp' in indexes
            assert 'idx_signals_symbol' in indexes
            assert 'idx_trades_timestamp' in indexes
            assert 'idx_trades_symbol' in indexes
            assert 'idx_trades_status' in indexes


@pytest.mark.unit
class TestSignalStorage:
    """Test signal storage and retrieval"""

    def test_store_signal(self, temp_database, sample_signal_data):
        """Test storing a signal in the database"""
        db = TradingDatabase(temp_database)
        signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

        assert signal_id > 0

        # Verify signal was stored
        signals = db.get_recent_signals('SUIUSDC', limit=1)
        assert len(signals) == 1
        assert signals[0]['signal'] == 1
        assert signals[0]['strength'] == 4
        assert signals[0]['rl_enhanced'] == True

    def test_store_signal_with_reasons(self, temp_database):
        """Test signal storage includes reasons"""
        db = TradingDatabase(temp_database)
        signal_data = {
            'signal': 1,
            'strength': 3,
            'reasons': ['MACD bullish', 'RSI oversold'],
            'indicators': {'rsi': 28.5, 'macd': 0.02},
            'rl_enhanced': False
        }

        signal_id = db.store_signal('SUIUSDC', 3.50, signal_data)
        signals = db.get_recent_signals('SUIUSDC', limit=1)

        assert len(signals[0]['reasons']) == 2
        assert 'MACD bullish' in signals[0]['reasons']

    def test_get_recent_rl_signals(self, temp_database, sample_signal_data):
        """Test filtering for RL-enhanced signals"""
        db = TradingDatabase(temp_database)

        # Store one RL signal and one traditional signal
        db.store_signal('SUIUSDC', 3.55, sample_signal_data)
        traditional_signal = sample_signal_data.copy()
        traditional_signal['rl_enhanced'] = False
        db.store_signal('SUIUSDC', 3.56, traditional_signal)

        # Should only return RL signals
        rl_signals = db.get_recent_rl_signals('SUIUSDC', limit=10)
        assert len(rl_signals) == 1
        assert rl_signals[0]['rl_enhanced'] == True


@pytest.mark.unit
class TestTradeStorage:
    """Test trade storage and updates"""

    def test_store_trade(self, temp_database, sample_signal_data):
        """Test storing a trade"""
        db = TradingDatabase(temp_database)

        # First store a signal
        signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

        # Then store a trade
        trade_id = db.store_trade(
            signal_id=signal_id,
            symbol='SUIUSDC',
            side='BUY',
            quantity=100.0,
            entry_price=3.55,
            leverage=50,
            position_percentage=2.0,
            order_id='12345',
            liquidation_price=3.40
        )

        assert trade_id > 0

        # Verify trade was stored
        trades = db.get_recent_trades('SUIUSDC', limit=1)
        assert len(trades) == 1
        assert trades[0]['side'] == 'BUY'
        assert trades[0]['quantity'] == 100.0
        assert trades[0]['status'] == 'OPEN'

    def test_update_trade_exit(self, temp_database, sample_signal_data):
        """Test updating trade with exit information"""
        db = TradingDatabase(temp_database)

        signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)
        trade_id = db.store_trade(
            signal_id=signal_id,
            symbol='SUIUSDC',
            side='BUY',
            quantity=100.0,
            entry_price=3.55,
            leverage=50,
            position_percentage=2.0
        )

        # Update with exit
        db.update_trade_exit(
            trade_id=trade_id,
            exit_price=3.70,
            pnl=15.0,
            pnl_percentage=4.23,
            status='CLOSED'
        )

        # Verify update
        trades = db.get_recent_trades('SUIUSDC', limit=1)
        assert trades[0]['status'] == 'CLOSED'
        assert trades[0]['exit_price'] == 3.70
        assert trades[0]['pnl'] == 15.0
        assert trades[0]['pnl_percentage'] == 4.23

    def test_get_open_trades(self, temp_database, sample_signal_data):
        """Test filtering for open trades only"""
        db = TradingDatabase(temp_database)

        signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

        # Create one open and one closed trade
        trade1_id = db.store_trade(signal_id, 'SUIUSDC', 'BUY', 100.0, 3.55, 50, 2.0)
        trade2_id = db.store_trade(signal_id, 'SUIUSDC', 'BUY', 50.0, 3.60, 50, 2.0)

        db.update_trade_exit(trade2_id, 3.65, 2.5, 1.39, 'CLOSED')

        # Should only return open trade
        open_trades = db.get_open_trades('SUIUSDC')
        assert len(open_trades) == 1
        assert open_trades[0]['id'] == trade1_id


@pytest.mark.unit
class TestPerformanceMetrics:
    """Test performance metric calculations"""

    def test_calculate_performance_with_trades(self, temp_database, sample_signal_data):
        """Test performance calculation with winning and losing trades"""
        db = TradingDatabase(temp_database)

        signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)

        # Create winning trade
        trade1_id = db.store_trade(signal_id, 'SUIUSDC', 'BUY', 100.0, 3.55, 50, 2.0)
        db.update_trade_exit(trade1_id, 3.70, 15.0, 4.23, 'CLOSED')

        # Create losing trade
        trade2_id = db.store_trade(signal_id, 'SUIUSDC', 'BUY', 100.0, 3.60, 50, 2.0)
        db.update_trade_exit(trade2_id, 3.50, -10.0, -2.78, 'CLOSED')

        metrics = db.calculate_performance_metrics('SUIUSDC', days=30)

        assert metrics['total_trades'] == 2
        assert metrics['winning_trades'] == 1
        assert metrics['losing_trades'] == 1
        assert metrics['win_rate'] == 50.0
        assert metrics['total_pnl'] == 5.0
        assert metrics['avg_win'] == 15.0
        assert metrics['avg_loss'] == -10.0

    def test_calculate_performance_with_projections(self, temp_database, sample_signal_data):
        """Test performance projections are calculated"""
        db = TradingDatabase(temp_database)

        signal_id = db.store_signal('SUIUSDC', 3.55, sample_signal_data)
        trade_id = db.store_trade(signal_id, 'SUIUSDC', 'BUY', 100.0, 3.55, 50, 2.0)
        db.update_trade_exit(trade_id, 3.70, 15.0, 4.23, 'CLOSED')

        metrics = db.calculate_performance_metrics('SUIUSDC', days=30)

        assert 'projections' in metrics
        assert 'best_case_90d' in metrics['projections']
        assert 'worst_case_90d' in metrics['projections']
        assert 'expected_90d' in metrics['projections']
        assert 'confidence' in metrics['projections']


@pytest.mark.unit
class TestMarketContext:
    """Test market context storage and retrieval"""

    def test_store_market_context(self, temp_database):
        """Test storing cross-asset correlation data"""
        db = TradingDatabase(temp_database)

        market_context = {
            'timestamp': datetime.now().isoformat(),
            'btc_price': 95000.0,
            'btc_change_24h': 2.5,
            'btc_dominance': 55.2,
            'eth_price': 3500.0,
            'eth_change_24h': 3.1,
            'fear_greed_index': 75,
            'volatility_regime': 'MEDIUM',
            'market_trend': 'BULLISH',
            'correlation_signal': 'POSITIVE'
        }

        result = db.store_market_context(market_context)
        assert result == True

        # Verify storage
        contexts = db.get_recent_market_context(limit=1)
        assert len(contexts) == 1
        assert contexts[0]['btc_price'] == 95000.0
        assert contexts[0]['fear_greed_index'] == 75

    def test_get_market_context_correlation(self, temp_database):
        """Test correlation analysis from market context"""
        db = TradingDatabase(temp_database)

        # Store multiple context entries
        for i in range(5):
            context = {
                'timestamp': datetime.now().isoformat(),
                'btc_change_24h': 2.0 + i,
                'eth_change_24h': 2.5 + i,
                'market_trend': 'BULLISH'
            }
            db.store_market_context(context)

        correlation = db.get_market_context_correlation(hours=24)

        assert 'btc_eth_correlation' in correlation
        assert 'avg_btc_change' in correlation
        assert 'avg_eth_change' in correlation
        assert 'trend_distribution' in correlation
        assert correlation['data_points'] == 5


@pytest.mark.unit
class TestManualClosures:
    """Test manual closure detection and recording"""

    def test_record_manual_closure(self, temp_database):
        """Test recording a manually closed position"""
        db = TradingDatabase(temp_database)

        closure = {
            'timestamp': '2025-01-01 12:00:00',
            'type': 'FULL_CLOSE',
            'amount': 500.0,
            'entry_price': 3.50,
            'exit_price': 3.70
        }

        result = db.record_manual_closure(closure, 'SUIUSDC')
        assert result == True

        # Verify it was recorded
        trades = db.get_recent_trades('SUIUSDC', limit=1)
        assert len(trades) == 1
        assert trades[0]['side'] == 'SELL'
        assert trades[0]['quantity'] == 500.0
        assert 'MANUAL_' in trades[0]['order_id']

    def test_record_duplicate_closure(self, temp_database):
        """Test that duplicate closures are not recorded"""
        db = TradingDatabase(temp_database)

        closure = {
            'timestamp': '2025-01-01 12:00:00',
            'type': 'FULL_CLOSE',
            'amount': 500.0,
            'entry_price': 3.50,
            'exit_price': 3.70
        }

        # Record once
        result1 = db.record_manual_closure(closure, 'SUIUSDC')
        assert result1 == True

        # Try to record again
        result2 = db.record_manual_closure(closure, 'SUIUSDC')
        assert result2 == False


@pytest.mark.unit
def test_singleton_database(temp_database):
    """Test that get_database returns the same instance"""
    db1 = get_database(temp_database)
    db2 = get_database(temp_database)

    assert db1 is db2
