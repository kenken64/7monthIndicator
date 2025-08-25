#!/usr/bin/env python3
"""
Database module for Binance Futures Trading Bot
Handles SQLite database operations for signals and trades
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
    """SQLite database handler for trading bot signals and trades"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        """Initialize database connection and create tables"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            self.create_tables(conn)
            self.migrate_schema(conn)
            logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
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
        """Migrate database schema to the latest version"""
        try:
            # Check if rl_enhanced column exists
            cursor = conn.execute("PRAGMA table_info(signals)")
            columns = [row['name'] for row in cursor.fetchall()]
            if 'rl_enhanced' not in columns:
                logger.info("Migrating database schema: adding 'rl_enhanced' column to signals table.")
                conn.execute('ALTER TABLE signals ADD COLUMN rl_enhanced BOOLEAN DEFAULT FALSE')
        except Exception as e:
            logger.error(f"Error migrating database schema: {e}")
    
    def create_tables(self, conn):
        """Create all necessary database tables"""
        
        # Signals table - stores all signal calculations
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
        
        # Trades table - stores executed trades
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
        
        # Market data table - stores OHLCV data for analysis
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
        
        # Performance metrics table
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
        
        # Create indexes for better performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp)')
        
        logger.info("Database tables created/verified")
    
    def store_signal(self, symbol: str, price: float, signal_data: Dict) -> int:
        """Store signal analysis in database"""
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
        """Store executed trade in database"""
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
                
                # Mark signal as executed
                conn.execute('UPDATE signals SET executed = TRUE WHERE id = ?', (signal_id,))
                
                logger.info(f"Trade stored: ID={trade_id}, Symbol={symbol}, Side={side}, Quantity={quantity}")
                return trade_id
        except Exception as e:
            logger.error(f"Error storing trade: {e}")
            return 0
    
    def update_trade_exit(self, trade_id: int, exit_price: float, pnl: float, 
                         pnl_percentage: float, status: str = 'CLOSED'):
        """Update trade with exit information"""
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
        """Store market data for analysis"""
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
        """Get recent signals from database"""
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
        """Get recent RL-enhanced signals from the database"""
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
        """Get recent trades from database"""
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
        """Get open trades"""
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
        """Calculate performance metrics for given period"""
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
                    return {
                        'total_trades': row['total_trades'],
                        'winning_trades': row['winning_trades'] or 0,
                        'losing_trades': row['losing_trades'] or 0,
                        'win_rate': win_rate,
                        'total_pnl': row['total_pnl'] or 0,
                        'avg_win': row['avg_win'] or 0,
                        'avg_loss': row['avg_loss'] or 0,
                        'max_loss': row['max_loss'] or 0,
                        'days': days
                    }
                else:
                    return {'total_trades': 0, 'days': days}
                    
        except Exception as e:
            logger.error(f"Error calculating performance: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to keep database size manageable"""
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
        """Export table data to CSV"""
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

# Singleton instance
_db_instance = None

def get_database(db_path: str = "trading_bot.db") -> TradingDatabase:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = TradingDatabase(db_path)
    return _db_instance