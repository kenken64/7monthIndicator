#!/usr/bin/env python3
"""
Database module for Binance Futures Trading Bot

A comprehensive SQLite database handler that manages all trading bot data including:
- Trading signals and their analysis results
- Executed trades with entry/exit prices and PnL tracking
- Market data (OHLCV) for historical analysis
- Performance metrics and statistics
- Automatic schema migrations and data cleanup

The module provides a singleton pattern for database access and uses
context managers for safe transaction handling.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

class TradingDatabase:
    """SQLite database handler for trading bot signals and trades
    
    This class manages all database operations for the trading bot including:
    - Table creation and schema migrations
    - Signal storage with RL enhancement flags
    - Trade execution tracking with PnL calculations
    - Performance metrics calculation
    - Data export and cleanup operations
    
    Uses SQLite with row factory for dictionary-like access to records.
    """
    
    def __init__(self, db_path: str = "data/trading_bot.db"):
        """Initialize database connection and create tables
        
        Args:
            db_path: Path to SQLite database file (default: 'data/trading_bot.db')
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist
        
        Initializes the complete database schema including all tables,
        indexes, and performs any necessary schema migrations.
        """
        with self.get_connection() as conn:
            self.create_tables(conn)
            self.migrate_schema(conn)
            logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections
        
        Provides safe database access with automatic transaction handling.
        Commits on success, rolls back on exceptions, and always closes connections.
        
        Yields:
            sqlite3.Connection: Database connection with row factory enabled
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def migrate_schema(self, conn):
        """Migrate database schema to the latest version
        
        Handles database schema evolution by adding new columns or tables
        as needed for new features without breaking existing data.
        
        Args:
            conn: SQLite database connection
        """
        try:
            # Check if rl_enhanced column exists
            cursor = conn.execute("PRAGMA table_info(signals)")
            columns = [row['name'] for row in cursor.fetchall()]
            if 'rl_enhanced' not in columns:
                logger.info("Migrating database schema: adding 'rl_enhanced' column to signals table.")
                conn.execute('ALTER TABLE signals ADD COLUMN rl_enhanced BOOLEAN DEFAULT FALSE')
            
            # Check if market_context table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_context'")
            if not cursor.fetchone():
                logger.info("Creating market_context table for cross-asset data.")
                self.create_market_context_table(conn)
        except Exception as e:
            logger.error(f"Error migrating database schema: {e}")
    
    def create_market_context_table(self, conn):
        """Create market_context table for storing cross-asset correlation data
        
        Args:
            conn: SQLite database connection
        """
        conn.execute('''
            CREATE TABLE market_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                btc_price REAL,
                btc_change_24h REAL,
                btc_dominance REAL,
                eth_price REAL,
                eth_change_24h REAL,
                fear_greed_index INTEGER,
                volatility_regime TEXT,
                market_trend TEXT,
                correlation_signal TEXT,
                btc_trend TEXT,
                eth_btc_ratio TEXT,
                market_breadth TEXT,
                volatility_state TEXT,
                regime_signal TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index on timestamp for efficient querying
        conn.execute('CREATE INDEX idx_market_context_timestamp ON market_context(timestamp)')
        logger.info("Market context table created successfully")
    
    def create_tables(self, conn):
        """Create all necessary database tables
        
        Creates the complete database schema with:
        - signals: Trading signal analysis results
        - trades: Executed trade records with PnL tracking
        - market_data: OHLCV data for analysis
        - performance: Daily performance metrics
        - Indexes for query optimization
        
        Args:
            conn: SQLite database connection
        """
        
        # Signals table - stores all signal calculations with RL enhancement flags
        conn.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                signal INTEGER NOT NULL,  -- -1, 0, 1 (sell, hold, buy)
                strength INTEGER NOT NULL,
                reasons TEXT,  -- JSON array of signal reasons
                indicators TEXT,  -- JSON object with all indicator values
                rl_enhanced BOOLEAN DEFAULT FALSE,
                executed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trades table - stores executed trades with comprehensive PnL tracking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                signal_id INTEGER,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,  -- BUY, SELL
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                pnl REAL,
                pnl_percentage REAL,
                leverage INTEGER,
                position_size_percentage REAL,
                status TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED, CANCELLED
                order_id TEXT,
                liquidation_price REAL,
                stop_loss_price REAL,
                take_profit_price REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (signal_id) REFERENCES signals (id)
            )
        ''')
        
        # Market data table - stores OHLCV candlestick data for technical analysis
        conn.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol, timeframe)
            )
        ''')
        
        # Performance metrics table - daily aggregated trading statistics
        conn.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                symbol TEXT NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                avg_win REAL DEFAULT 0,
                avg_loss REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                balance REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, symbol)
            )
        ''')
        
        # Create indexes for query optimization on frequently accessed columns
        conn.execute('CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp)')
        
        logger.info("Database tables created/verified")
    
    def store_signal(self, symbol: str, price: float, signal_data: Dict) -> int:
        """Store signal analysis in database
        
        Records trading signal with all analysis data including RL enhancements,
        technical indicators, and reasoning for audit trail.
        
        Args:
            symbol: Trading pair symbol (e.g., 'SUIUSDC')
            price: Current market price when signal generated
            signal_data: Dictionary containing signal details, strength, reasons, and indicators
            
        Returns:
            int: Database ID of stored signal (0 if failed)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    INSERT INTO signals (symbol, price, signal, strength, reasons, indicators, rl_enhanced)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    price,
                    signal_data.get('signal', 0),
                    signal_data.get('strength', 0),
                    json.dumps(signal_data.get('reasons', [])),
                    json.dumps(signal_data.get('indicators', {})),
                    signal_data.get('rl_enhanced', False)
                ))
                signal_id = cursor.lastrowid
                logger.info(f"Signal stored: ID={signal_id}, Symbol={symbol}, Signal={signal_data.get('signal')}")
                return signal_id
        except Exception as e:
            logger.error(f"Error storing signal: {e}")
            return 0
    
    def store_trade(self, signal_id: int, symbol: str, side: str, quantity: float, 
                   entry_price: float, leverage: int, position_percentage: float, 
                   order_id: str = None, liquidation_price: float = None) -> int:
        """Store executed trade in database
        
        Records a new trade execution linking it to the originating signal.
        Also marks the originating signal as executed.
        
        Args:
            signal_id: ID of signal that triggered this trade
            symbol: Trading pair symbol
            side: Trade direction ('BUY' or 'SELL')
            quantity: Position size
            entry_price: Price at which position was entered
            leverage: Futures leverage used
            position_percentage: Percentage of account used for this trade
            order_id: Exchange order ID for tracking
            liquidation_price: Calculated liquidation price
            
        Returns:
            int: Database ID of stored trade (0 if failed)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    INSERT INTO trades (signal_id, symbol, side, quantity, entry_price, 
                                      leverage, position_size_percentage, order_id, liquidation_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_id,
                    symbol,
                    side,
                    quantity,
                    entry_price,
                    leverage,
                    position_percentage,
                    order_id,
                    liquidation_price
                ))
                trade_id = cursor.lastrowid
                
                # Mark signal as executed to prevent duplicate trades
                conn.execute('UPDATE signals SET executed = TRUE WHERE id = ?', (signal_id,))
                
                logger.info(f"Trade stored: ID={trade_id}, Symbol={symbol}, Side={side}, Quantity={quantity}")
                return trade_id
        except Exception as e:
            logger.error(f"Error storing trade: {e}")
            return 0
    
    def update_trade_exit(self, trade_id: int, exit_price: float, pnl: float, 
                         pnl_percentage: float, status: str = 'CLOSED'):
        """Update trade with exit information
        
        Updates an existing trade record with closing details including
        exit price and calculated PnL metrics.
        
        Args:
            trade_id: Database ID of trade to update
            exit_price: Price at which position was closed
            pnl: Profit/Loss amount in account currency
            pnl_percentage: PnL as percentage of position size
            status: New trade status (default: 'CLOSED')
        """
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE trades 
                    SET exit_price = ?, pnl = ?, pnl_percentage = ?, status = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (exit_price, pnl, pnl_percentage, status, trade_id))
                logger.info(f"Trade updated: ID={trade_id}, Exit=${exit_price}, PnL={pnl_percentage:.2f}%")
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
    
    def store_market_data(self, symbol: str, timeframe: str, ohlcv_data: List[Dict]):
        """Store market data for analysis
        
        Stores OHLCV candlestick data for historical analysis and backtesting.
        Uses INSERT OR REPLACE to handle duplicate timestamps.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candlestick timeframe (e.g., '5m', '1h')
            ohlcv_data: List of candlestick dictionaries with OHLCV data
        """
        try:
            with self.get_connection() as conn:
                for candle in ohlcv_data:
                    conn.execute('''
                        INSERT OR REPLACE INTO market_data 
                        (timestamp, symbol, timeframe, open_price, high_price, low_price, close_price, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        candle['timestamp'],
                        symbol,
                        timeframe,
                        candle['open'],
                        candle['high'],
                        candle['low'],
                        candle['close'],
                        candle['volume']
                    ))
                logger.debug(f"Stored {len(ohlcv_data)} candles for {symbol} {timeframe}")
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
    
    def get_recent_signals(self, symbol: str = None, limit: int = 10) -> List[Dict]:
        """Get recent signals from database
        
        Retrieves recent trading signals with parsed JSON data for display
        in dashboards and analysis tools.
        
        Args:
            symbol: Filter by trading pair (None for all symbols)
            limit: Maximum number of signals to return
            
        Returns:
            List[Dict]: Recent signals with parsed reasons and indicators
        """
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM signals 
                    WHERE symbol = ? OR ? IS NULL
                    ORDER BY timestamp DESC 
                    LIMIT ?
                '''
                cursor = conn.execute(query, (symbol, symbol, limit))
                signals = []
                for row in cursor.fetchall():
                    signal = dict(row)
                    signal['reasons'] = json.loads(signal['reasons']) if signal['reasons'] else []
                    signal['indicators'] = json.loads(signal['indicators']) if signal['indicators'] else {}
                    signals.append(signal)
                return signals
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    def get_recent_rl_signals(self, symbol: str = None, limit: int = 5) -> List[Dict]:
        """Get recent RL-enhanced signals from the database
        
        Filters for signals that have been processed by the RL enhancement
        system, useful for analyzing RL decision patterns.
        
        Args:
            symbol: Filter by trading pair (None for all symbols)
            limit: Maximum number of RL signals to return
            
        Returns:
            List[Dict]: Recent RL-enhanced signals with parsed data
        """
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM signals 
                    WHERE (symbol = ? OR ? IS NULL) AND rl_enhanced = 1
                    ORDER BY timestamp DESC 
                    LIMIT ?
                '''
                cursor = conn.execute(query, (symbol, symbol, limit))
                signals = []
                for row in cursor.fetchall():
                    signal = dict(row)
                    signal['reasons'] = json.loads(signal['reasons']) if signal['reasons'] else []
                    signal['indicators'] = json.loads(signal['indicators']) if signal['indicators'] else {}
                    signals.append(signal)
                return signals
        except Exception as e:
            logger.error(f"Error getting recent RL signals: {e}")
            return []

    def get_recent_trades(self, symbol: str = None, limit: int = 10) -> List[Dict]:
        """Get recent trades from database
        
        Retrieves recent trade executions with linked signal information
        for performance analysis and dashboard display.
        
        Args:
            symbol: Filter by trading pair (None for all symbols)
            limit: Maximum number of trades to return
            
        Returns:
            List[Dict]: Recent trades with signal details
        """
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT t.*, s.signal, s.strength 
                    FROM trades t
                    LEFT JOIN signals s ON t.signal_id = s.id
                    WHERE t.symbol = ? OR ? IS NULL
                    ORDER BY t.timestamp DESC 
                    LIMIT ?
                '''
                cursor = conn.execute(query, (symbol, symbol, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_open_trades(self, symbol: str = None) -> List[Dict]:
        """Get currently open trades
        
        Retrieves all trades with 'OPEN' status for position tracking
        and risk management.
        
        Args:
            symbol: Filter by trading pair (None for all symbols)
            
        Returns:
            List[Dict]: Currently open trades
        """
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM trades 
                    WHERE status = 'OPEN' AND (symbol = ? OR ? IS NULL)
                    ORDER BY timestamp DESC
                '''
                cursor = conn.execute(query, (symbol, symbol))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting open trades: {e}")
            return []
    
    def calculate_performance_metrics(self, symbol: str, days: int = 30) -> Dict:
        """Calculate comprehensive performance metrics for given period
        
        Computes detailed trading statistics including win rates, PnL metrics,
        and future projections based on historical performance.
        
        Args:
            symbol: Trading pair to analyze
            days: Historical period to analyze
            
        Returns:
            Dict: Complete performance metrics with projections
        """
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
                        AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss,
                        MIN(pnl) as max_loss
                    FROM trades 
                    WHERE symbol = ? AND status = 'CLOSED' 
                    AND timestamp >= datetime('now', '-{} days')
                '''.format(days)
                
                cursor = conn.execute(query, (symbol,))
                row = cursor.fetchone()
                
                if row and row['total_trades'] > 0:
                    win_rate = (row['winning_trades'] / row['total_trades']) * 100
                    
                    # Calculate future projections using historical performance trends
                    avg_daily_pnl = (row['total_pnl'] or 0) / days if days > 0 else 0
                    avg_win = row['avg_win'] or 0
                    avg_loss = row['avg_loss'] or 0
                    
                    # Project for 90 days
                    projection_days = 90
                    expected_trades_90d = (row['total_trades'] / days) * projection_days if days > 0 else 0
                    
                    # Best case: assume higher win rate and average wins
                    best_case_wins = expected_trades_90d * min(win_rate * 1.2, 100) / 100
                    best_case_losses = expected_trades_90d - best_case_wins
                    best_case_pnl = (best_case_wins * avg_win * 1.3) + (best_case_losses * avg_loss)
                    
                    # Worst case: assume lower win rate and higher losses  
                    worst_case_wins = expected_trades_90d * max(win_rate * 0.6, 0) / 100
                    worst_case_losses = expected_trades_90d - worst_case_wins
                    worst_case_pnl = (worst_case_wins * avg_win * 0.7) + (worst_case_losses * avg_loss * 1.5)
                    
                    # Expected case: current performance trends
                    expected_pnl_90d = avg_daily_pnl * projection_days
                    
                    return {
                        'total_trades': row['total_trades'],
                        'winning_trades': row['winning_trades'] or 0,
                        'losing_trades': row['losing_trades'] or 0,
                        'win_rate': win_rate,
                        'total_pnl': row['total_pnl'] or 0,
                        'avg_win': avg_win,
                        'avg_loss': avg_loss,
                        'max_loss': row['max_loss'] or 0,
                        'days': days,
                        'projections': {
                            'best_case_90d': round(best_case_pnl, 2),
                            'worst_case_90d': round(worst_case_pnl, 2),
                            'expected_90d': round(expected_pnl_90d, 2),
                            'confidence': min(row['total_trades'] * 2, 100)  # Higher confidence with more trades
                        }
                    }
                else:
                    return {'total_trades': 0, 'days': days}
                    
        except Exception as e:
            logger.error(f"Error calculating performance: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to keep database size manageable
        
        Removes old records based on data retention policies:
        - Signals: Keep for specified days (default 90)
        - Market data: Keep for 30 days
        - Closed trades: Keep for 1 year, open trades forever
        
        Args:
            days_to_keep: Number of days to retain signal data
        """
        try:
            with self.get_connection() as conn:
                # Keep signals for 90 days
                conn.execute('''
                    DELETE FROM signals 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days_to_keep))
                
                # Keep market data for 30 days
                conn.execute('''
                    DELETE FROM market_data 
                    WHERE timestamp < datetime('now', '-30 days')
                ''')
                
                # Keep closed trades for 1 year, open trades forever
                conn.execute('''
                    DELETE FROM trades 
                    WHERE status = 'CLOSED' AND timestamp < datetime('now', '-365 days')
                ''')
                
                logger.info(f"Cleaned up data older than {days_to_keep} days")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def export_data(self, table: str, filename: str = None) -> str:
        """Export table data to CSV file
        
        Exports complete table contents to CSV format for external analysis
        or backup purposes.
        
        Args:
            table: Name of table to export
            filename: Output filename (auto-generated if None)
            
        Returns:
            str: Path to exported file (None if failed)
        """
        import csv
        
        if not filename:
            filename = f"{table}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(f"SELECT * FROM {table}")
                
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow([description[0] for description in cursor.description])
                    
                    # Write data
                    writer.writerows(cursor.fetchall())
                
                logger.info(f"Data exported to {filename}")
                return filename
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None

    def get_all_trades(self, symbol: str, exclude_manual: bool = False) -> List[Dict]:
        """Get all trades for analysis, optionally excluding manual closures
        
        Retrieves complete trade history for position analysis and reconciliation.
        Can exclude manually created closure records to analyze only bot trades.
        
        Args:
            symbol: Trading pair symbol
            exclude_manual: Whether to exclude manual closure records
            
        Returns:
            List[Dict]: Historical trade records
        """
        try:
            with self.get_connection() as conn:
                if exclude_manual:
                    cursor = conn.execute('''
                        SELECT timestamp, side, quantity, entry_price, exit_price, pnl
                        FROM trades 
                        WHERE symbol = ? AND (order_id NOT LIKE 'MANUAL_%' OR order_id IS NULL)
                        ORDER BY timestamp ASC
                    ''', (symbol,))
                else:
                    cursor = conn.execute('''
                        SELECT timestamp, side, quantity, entry_price, exit_price, pnl
                        FROM trades 
                        WHERE symbol = ?
                        ORDER BY timestamp ASC
                    ''', (symbol,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting all trades: {e}")
            return []

    def get_recent_trades(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get recent trades with proper formatting"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT timestamp, side, quantity, entry_price, exit_price, pnl, status
                    FROM trades 
                    WHERE symbol = ? AND timestamp >= datetime('now', '-7 days')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (symbol, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []

    def get_total_trades_count(self, symbol: str) -> int:
        """Get total number of trades for a symbol"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) as count FROM trades WHERE symbol = ?', (symbol,))
                result = cursor.fetchone()
                return result['count'] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting trades count: {e}")
            return 0

    def record_manual_closure(self, closure: Dict, symbol: str) -> bool:
        """Record an individual manual closure in the database
        
        Creates a trade record for manually closed positions that were
        detected during position reconciliation.
        
        Args:
            closure: Dictionary with closure details (timestamp, amount, prices, type)
            symbol: Trading pair symbol
            
        Returns:
            bool: True if recorded successfully, False if already exists or failed
        """
        try:
            with self.get_connection() as conn:
                # Check if already exists
                cursor = conn.execute('''
                    SELECT id FROM trades 
                    WHERE timestamp = ? AND side = 'SELL' AND quantity = ?
                ''', (closure['timestamp'], closure['amount']))
                
                if cursor.fetchone():
                    logger.debug(f"Manual closure already recorded: {closure['amount']} at {closure['timestamp']}")
                    return False
                
                # Calculate PnL
                pnl = (closure['exit_price'] - closure['entry_price']) * closure['amount']
                pnl_percentage = (pnl / (closure['entry_price'] * closure['amount'])) * 100 if closure['entry_price'] > 0 else 0
                
                # Create order ID
                ts_str = str(closure['timestamp']).replace(' ', '_').replace(':', '').replace('-', '')
                order_id = f"MANUAL_{closure['type']}_{ts_str}"
                
                # Insert into database
                conn.execute('''
                    INSERT INTO trades (
                        timestamp, symbol, side, quantity, entry_price,
                        exit_price, pnl, pnl_percentage, status, order_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    closure['timestamp'],
                    symbol,
                    'SELL',
                    closure['amount'],
                    closure['entry_price'],
                    closure['exit_price'],
                    pnl,
                    pnl_percentage,
                    'CLOSED',
                    order_id,
                    datetime.now(),
                    datetime.now()
                ))
                
                logger.info(f"✅ Recorded {closure['type']}: {closure['amount']:.1f} @ ${closure['exit_price']:.4f}")
                return True
                
        except Exception as e:
            logger.error(f"Error recording manual closure: {e}")
            return False
    
    def store_market_context(self, market_context: Dict) -> bool:
        """Store market context and cross-asset correlation data
        
        Args:
            market_context: Dictionary containing market context data
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO market_context (
                        timestamp, btc_price, btc_change_24h, btc_dominance,
                        eth_price, eth_change_24h, fear_greed_index,
                        volatility_regime, market_trend, correlation_signal,
                        btc_trend, eth_btc_ratio, market_breadth,
                        volatility_state, regime_signal
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    market_context.get('timestamp', datetime.now().isoformat()),
                    market_context.get('btc_price'),
                    market_context.get('btc_change_24h'),
                    market_context.get('btc_dominance'),
                    market_context.get('eth_price'),
                    market_context.get('eth_change_24h'),
                    market_context.get('fear_greed_index'),
                    market_context.get('volatility_regime'),
                    market_context.get('market_trend'),
                    market_context.get('correlation_signal'),
                    market_context.get('btc_trend'),
                    market_context.get('eth_btc_ratio'),
                    market_context.get('market_breadth'),
                    market_context.get('volatility_state'),
                    market_context.get('regime_signal')
                ))
                
                logger.debug(f"Stored market context at {market_context.get('timestamp')}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing market context: {e}")
            return False
    
    def get_recent_market_context(self, limit: int = 24) -> List[Dict]:
        """Get recent market context data
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: List of market context records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM market_context
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting recent market context: {e}")
            return []
    
    def get_market_context_correlation(self, hours: int = 24) -> Dict:
        """Get market context correlation analysis
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dict: Correlation analysis results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT btc_change_24h, eth_change_24h, market_trend,
                           volatility_regime, regime_signal
                    FROM market_context
                    WHERE created_at >= datetime('now', '-{} hours')
                    ORDER BY created_at DESC
                '''.format(hours))
                
                data = [dict(row) for row in cursor.fetchall()]
                
                if not data:
                    return {}
                
                # Calculate correlation statistics
                btc_changes = [d['btc_change_24h'] for d in data if d['btc_change_24h'] is not None]
                eth_changes = [d['eth_change_24h'] for d in data if d['eth_change_24h'] is not None]
                
                # Simple correlation calculation
                correlation = 0.0
                if len(btc_changes) == len(eth_changes) and len(btc_changes) > 1:
                    import numpy as np
                    correlation = np.corrcoef(btc_changes, eth_changes)[0, 1] if len(btc_changes) > 1 else 0.0
                
                # Trend analysis
                trends = [d['market_trend'] for d in data if d['market_trend']]
                trend_counts = {}
                for trend in trends:
                    trend_counts[trend] = trend_counts.get(trend, 0) + 1
                
                return {
                    'btc_eth_correlation': correlation,
                    'avg_btc_change': sum(btc_changes) / len(btc_changes) if btc_changes else 0,
                    'avg_eth_change': sum(eth_changes) / len(eth_changes) if eth_changes else 0,
                    'trend_distribution': trend_counts,
                    'data_points': len(data)
                }
                
        except Exception as e:
            logger.error(f"Error getting market context correlation: {e}")
            return {}

# Singleton instance - ensures only one database connection across the application
_db_instance = None

def get_database(db_path: str = "data/trading_bot.db") -> TradingDatabase:
    """Get singleton database instance
    
    Returns the global database instance, creating it if necessary.
    Ensures only one database connection is used throughout the application.
    
    Args:
        db_path: Path to database file (only used on first call)
        
    Returns:
        TradingDatabase: Singleton database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = TradingDatabase(db_path)
    return _db_instance