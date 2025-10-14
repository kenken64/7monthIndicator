"""
Database Migration: Add Spike Detection Tables
Adds spike_detections and spike_trades tables for CrewAI spike agent
"""

import logging
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_spike_schema(db_path: str = "data/trading_bot.db"):
    """
    Add spike detection and spike trading tables to existing database
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Starting spike schema migration...")

        # Check if spike_detections table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spike_detections'")
        if not cursor.fetchone():
            logger.info("Creating spike_detections table...")
            cursor.execute('''
                CREATE TABLE spike_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detection_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    spike_type TEXT NOT NULL,  -- price_spike, volume_explosion, liquidation_cascade, etc.
                    direction TEXT NOT NULL,  -- UP, DOWN
                    magnitude_percent REAL NOT NULL,
                    timeframe_minutes INTEGER NOT NULL,
                    volume_multiplier REAL,
                    confidence_score REAL,

                    -- Market conditions at detection
                    btc_price REAL,
                    eth_price REAL,
                    market_trend TEXT,
                    circuit_breaker_safe BOOLEAN DEFAULT TRUE,

                    -- Analysis results
                    legitimacy TEXT,  -- LIKELY_LEGITIMATE, QUESTIONABLE, SUSPICIOUS
                    manipulation_score INTEGER,
                    market_correlation BOOLEAN,
                    order_book_balanced BOOLEAN,

                    -- Agent decisions
                    scanner_decision TEXT,
                    context_decision TEXT,
                    risk_decision TEXT,
                    final_decision TEXT,  -- TRADE, AVOID, MONITOR

                    -- Trade execution
                    executed BOOLEAN DEFAULT FALSE,
                    trade_id INTEGER,

                    -- Metadata
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trade_id) REFERENCES spike_trades (id)
                )
            ''')

            # Create indexes for spike_detections
            cursor.execute('CREATE INDEX idx_spike_detections_timestamp ON spike_detections(timestamp)')
            cursor.execute('CREATE INDEX idx_spike_detections_symbol ON spike_detections(symbol)')
            cursor.execute('CREATE INDEX idx_spike_detections_executed ON spike_detections(executed)')

            logger.info("✅ spike_detections table created")
        else:
            logger.info("spike_detections table already exists")

        # Check if spike_trades table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spike_trades'")
        if not cursor.fetchone():
            logger.info("Creating spike_trades table...")
            cursor.execute('''
                CREATE TABLE spike_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE NOT NULL,
                    detection_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,

                    -- Trade parameters
                    side TEXT NOT NULL,  -- BUY, SELL, LONG, SHORT
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    position_size_usd REAL NOT NULL,
                    leverage INTEGER DEFAULT 1,

                    -- Risk management
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    estimated_slippage_percent REAL,
                    actual_slippage_percent REAL,

                    -- Performance
                    pnl_usd REAL,
                    pnl_percent REAL,
                    holding_time_minutes INTEGER,
                    status TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED, STOPPED_OUT, LIQUIDATED

                    -- Market conditions
                    entry_btc_price REAL,
                    entry_market_trend TEXT,
                    circuit_breaker_checked BOOLEAN DEFAULT TRUE,

                    -- Execution details
                    order_id TEXT,
                    execution_timestamp TEXT,
                    exit_timestamp TEXT,
                    exit_reason TEXT,  -- TAKE_PROFIT, STOP_LOSS, MANUAL, CIRCUIT_BREAKER, TIMEOUT

                    -- Agent decisions
                    risk_approval TEXT,  -- JSON with risk analysis
                    execution_plan TEXT,  -- JSON with execution details

                    -- Metadata
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (detection_id) REFERENCES spike_detections (detection_id)
                )
            ''')

            # Create indexes for spike_trades
            cursor.execute('CREATE INDEX idx_spike_trades_timestamp ON spike_trades(timestamp)')
            cursor.execute('CREATE INDEX idx_spike_trades_symbol ON spike_trades(symbol)')
            cursor.execute('CREATE INDEX idx_spike_trades_status ON spike_trades(status)')
            cursor.execute('CREATE INDEX idx_spike_trades_detection_id ON spike_trades(detection_id)')

            logger.info("✅ spike_trades table created")
        else:
            logger.info("spike_trades table already exists")

        # Check if agent_decisions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_decisions'")
        if not cursor.fetchone():
            logger.info("Creating agent_decisions table...")
            cursor.execute('''
                CREATE TABLE agent_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT UNIQUE NOT NULL,
                    agent_name TEXT NOT NULL,  -- market_guardian, market_scanner, context_analyzer, risk_assessment, strategy_executor
                    task_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,

                    -- Input context
                    input_data TEXT,  -- JSON

                    -- Decision output
                    decision TEXT NOT NULL,  -- JSON with agent's recommendation
                    reasoning TEXT,
                    confidence_score REAL,

                    -- Related records
                    detection_id TEXT,
                    trade_id TEXT,
                    circuit_breaker_event_id TEXT,

                    -- Performance tracking
                    execution_time_ms INTEGER,
                    llm_tokens_used INTEGER,

                    -- Metadata
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (detection_id) REFERENCES spike_detections (detection_id),
                    FOREIGN KEY (trade_id) REFERENCES spike_trades (trade_id)
                )
            ''')

            # Create indexes for agent_decisions
            cursor.execute('CREATE INDEX idx_agent_decisions_timestamp ON agent_decisions(timestamp)')
            cursor.execute('CREATE INDEX idx_agent_decisions_agent_name ON agent_decisions(agent_name)')
            cursor.execute('CREATE INDEX idx_agent_decisions_detection_id ON agent_decisions(detection_id)')

            logger.info("✅ agent_decisions table created")
        else:
            logger.info("agent_decisions table already exists")

        conn.commit()
        logger.info("✅ Spike schema migration completed successfully")

        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Available tables: {', '.join(tables)}")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Spike Detection Schema Migration")
    print("=" * 60)

    success = migrate_spike_schema()

    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNew tables added:")
        print("  - spike_detections: Stores all detected spikes with analysis")
        print("  - spike_trades: Tracks executed spike trades with P&L")
        print("  - agent_decisions: Logs all agent decisions for audit trail")
    else:
        print("\n❌ Migration failed. Check logs for details.")
