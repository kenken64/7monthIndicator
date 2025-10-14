"""
Circuit Breaker State Manager for CrewAI Market Spike Agent
Manages circuit breaker state, crash detection, and recovery assessment
"""

import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    SAFE = "SAFE"  # Market is safe, trading allowed
    WARNING = "WARNING"  # Market approaching crash threshold
    TRIGGERED = "TRIGGERED"  # Circuit breaker activated
    RECOVERING = "RECOVERING"  # Market recovering, monitoring for stability


@dataclass
class MarketSnapshot:
    """Market snapshot at a given time"""
    timestamp: str
    btc_price: float
    eth_price: float
    btc_change_1h: float
    eth_change_1h: float
    btc_change_4h: float
    eth_change_4h: float
    market_cap: Optional[float] = None
    market_cap_change_4h: Optional[float] = None
    liquidations_1h: Optional[float] = None
    funding_rate: Optional[float] = None
    volume_drop: Optional[float] = None
    fear_greed_index: Optional[int] = None


@dataclass
class CircuitBreakerEvent:
    """Circuit breaker event record"""
    event_id: str
    state: str
    trigger_reason: str
    timestamp: str
    market_snapshot: Dict
    actions_taken: List[str]
    recovery_timestamp: Optional[str] = None
    recovery_duration_minutes: Optional[float] = None
    capital_protected_usd: Optional[float] = None


class CircuitBreakerStateManager:
    """
    Manages circuit breaker state with thread-safe operations
    Provides shared state across all CrewAI agents and main trading bot
    """

    def __init__(self, db_path: str = "data/trading_bot.db", config_path: str = "config/crewai_spike_agent.yaml"):
        self.db_path = db_path
        self.config_path = config_path

        # Thread-safe state management
        self._state_lock = threading.RLock()
        self._current_state = CircuitBreakerState.SAFE
        self._trigger_time: Optional[datetime] = None
        self._trigger_reason: Optional[str] = None
        self._last_check_time: Optional[datetime] = None
        self._recovery_start_time: Optional[datetime] = None

        # Market snapshot history for trend analysis
        self._market_history: List[MarketSnapshot] = []
        self._max_history_size = 1000

        # Configuration (loaded from YAML)
        self.config = self._load_config()

        # Initialize database
        self._init_database()

        logger.info("Circuit Breaker State Manager initialized")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return {
                'circuit_breaker': {
                    'thresholds': {
                        'btc': {'dump_1h_percent': 15.0, 'dump_4h_percent': 20.0, 'flash_crash_5m_percent': 10.0},
                        'eth': {'dump_1h_percent': 15.0, 'dump_4h_percent': 25.0, 'flash_crash_5m_percent': 12.0},
                        'market_wide': {'total_mcap_4h_percent': 20.0},
                        'binance_specific': {'liquidations_1h_usd': 500000000}
                    },
                    'recovery': {
                        'stabilization_minutes': 30,
                        'max_drop_during_recovery': 5.0
                    }
                }
            }

    def _init_database(self):
        """Initialize database tables for circuit breaker events"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Circuit breaker events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS circuit_breaker_events (
                    event_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    trigger_reason TEXT,
                    timestamp TEXT NOT NULL,
                    market_snapshot TEXT,
                    actions_taken TEXT,
                    recovery_timestamp TEXT,
                    recovery_duration_minutes REAL,
                    capital_protected_usd REAL
                )
            ''')

            # Market crashes historical table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_crashes (
                    crash_id TEXT PRIMARY KEY,
                    asset TEXT NOT NULL,
                    crash_start_time TEXT NOT NULL,
                    crash_end_time TEXT,
                    max_drawdown_percent REAL,
                    recovery_time_minutes REAL,
                    triggered_circuit_breaker INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')

            conn.commit()
            logger.info("Circuit breaker database tables initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state (thread-safe)"""
        with self._state_lock:
            return self._current_state

    def is_safe(self) -> bool:
        """Check if circuit breaker is in SAFE state"""
        return self.get_state() == CircuitBreakerState.SAFE

    def is_triggered(self) -> bool:
        """Check if circuit breaker is triggered"""
        return self.get_state() == CircuitBreakerState.TRIGGERED

    def get_status(self) -> Dict:
        """Get detailed circuit breaker status"""
        with self._state_lock:
            status = {
                'state': self._current_state.value,
                'is_safe': self._current_state == CircuitBreakerState.SAFE,
                'trigger_time': self._trigger_time.isoformat() if self._trigger_time else None,
                'trigger_reason': self._trigger_reason,
                'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
                'recovery_start_time': self._recovery_start_time.isoformat() if self._recovery_start_time else None
            }

            # Add time since trigger if triggered
            if self._trigger_time:
                elapsed = (datetime.now() - self._trigger_time).total_seconds() / 60
                status['minutes_since_trigger'] = round(elapsed, 1)

            # Add latest market snapshot
            if self._market_history:
                status['latest_market_snapshot'] = asdict(self._market_history[-1])

            return status

    def add_market_snapshot(self, snapshot: MarketSnapshot):
        """Add market snapshot to history (thread-safe)"""
        with self._state_lock:
            self._market_history.append(snapshot)
            if len(self._market_history) > self._max_history_size:
                self._market_history.pop(0)  # Remove oldest

    def check_crash_conditions(self, snapshot: MarketSnapshot) -> Tuple[bool, Optional[str]]:
        """
        Check if current market conditions meet crash thresholds
        Returns (should_trigger, reason)
        """
        thresholds = self.config['circuit_breaker']['thresholds']

        # BTC crash checks
        if abs(snapshot.btc_change_1h) >= thresholds['btc']['dump_1h_percent']:
            return True, f"BTC dropped {abs(snapshot.btc_change_1h):.1f}% in 1 hour (threshold: {thresholds['btc']['dump_1h_percent']}%)"

        if abs(snapshot.btc_change_4h) >= thresholds['btc']['dump_4h_percent']:
            return True, f"BTC dropped {abs(snapshot.btc_change_4h):.1f}% in 4 hours (threshold: {thresholds['btc']['dump_4h_percent']}%)"

        # ETH crash checks
        if abs(snapshot.eth_change_1h) >= thresholds['eth']['dump_1h_percent']:
            return True, f"ETH dropped {abs(snapshot.eth_change_1h):.1f}% in 1 hour (threshold: {thresholds['eth']['dump_1h_percent']}%)"

        if abs(snapshot.eth_change_4h) >= thresholds['eth']['dump_4h_percent']:
            return True, f"ETH dropped {abs(snapshot.eth_change_4h):.1f}% in 4 hours (threshold: {thresholds['eth']['dump_4h_percent']}%)"

        # Market-wide crash
        if snapshot.market_cap_change_4h and abs(snapshot.market_cap_change_4h) >= thresholds['market_wide']['total_mcap_4h_percent']:
            return True, f"Total market cap dropped {abs(snapshot.market_cap_change_4h):.1f}% in 4 hours"

        # Liquidations check
        if snapshot.liquidations_1h and snapshot.liquidations_1h >= thresholds['binance_specific']['liquidations_1h_usd']:
            return True, f"Binance liquidations ${snapshot.liquidations_1h/1e6:.0f}M in 1 hour (threshold: ${thresholds['binance_specific']['liquidations_1h_usd']/1e6:.0f}M)"

        return False, None

    def trigger(self, reason: str, market_snapshot: MarketSnapshot, actions: List[str]):
        """Trigger circuit breaker"""
        with self._state_lock:
            if self._current_state == CircuitBreakerState.TRIGGERED:
                logger.warning(f"Circuit breaker already triggered: {self._trigger_reason}")
                return

            self._current_state = CircuitBreakerState.TRIGGERED
            self._trigger_time = datetime.now()
            self._trigger_reason = reason

            # Log event
            event = CircuitBreakerEvent(
                event_id=f"CB_{int(time.time() * 1000)}",
                state="TRIGGERED",
                trigger_reason=reason,
                timestamp=self._trigger_time.isoformat(),
                market_snapshot=asdict(market_snapshot),
                actions_taken=actions
            )

            self._save_event(event)

            logger.critical(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
            logger.critical(f"Actions taken: {', '.join(actions)}")

    def set_warning(self, reason: str):
        """Set circuit breaker to WARNING state"""
        with self._state_lock:
            if self._current_state == CircuitBreakerState.SAFE:
                self._current_state = CircuitBreakerState.WARNING
                logger.warning(f"⚠️ CIRCUIT BREAKER WARNING: {reason}")

    def check_recovery(self, snapshot: MarketSnapshot) -> Tuple[bool, Optional[str]]:
        """
        Check if market has recovered enough to resume trading
        Returns (can_resume, reason)
        """
        if self._current_state != CircuitBreakerState.TRIGGERED:
            return False, "Circuit breaker not triggered"

        recovery_config = self.config['circuit_breaker']['recovery']

        # Check if enough time has passed
        if not self._trigger_time:
            return False, "No trigger time set"

        elapsed_minutes = (datetime.now() - self._trigger_time).total_seconds() / 60
        stabilization_minutes = recovery_config['stabilization_minutes']

        if elapsed_minutes < stabilization_minutes:
            return False, f"Waiting for stabilization period ({elapsed_minutes:.0f}/{stabilization_minutes} minutes)"

        # Check if there are large drops during recovery
        max_drop_threshold = recovery_config['max_drop_during_recovery']

        if not self._recovery_start_time:
            self._recovery_start_time = datetime.now()

        # Get market snapshots during recovery period
        recovery_snapshots = [
            s for s in self._market_history
            if datetime.fromisoformat(s.timestamp) >= self._recovery_start_time
        ]

        if recovery_snapshots:
            # Check for drops during recovery
            for snap in recovery_snapshots:
                if abs(snap.btc_change_1h) >= max_drop_threshold or abs(snap.eth_change_1h) >= max_drop_threshold:
                    return False, f"Market still volatile: BTC {snap.btc_change_1h:.1f}%, ETH {snap.eth_change_1h:.1f}% (1h)"

        # Check if BTC recovered at least 50% of initial drop
        require_50pct_recovery = recovery_config.get('require_btc_50pct_recovery', True)
        if require_50pct_recovery:
            # This would require tracking initial drop amount - simplified check here
            if snapshot.btc_change_1h < -2.0:  # Still dropping
                return False, f"BTC still dropping: {snapshot.btc_change_1h:.1f}% (1h)"

        return True, "Market has stabilized, safe to resume"

    def resume(self, capital_protected: Optional[float] = None):
        """Resume trading after circuit breaker recovery"""
        with self._state_lock:
            if self._current_state != CircuitBreakerState.TRIGGERED:
                logger.warning("Circuit breaker not triggered, cannot resume")
                return

            recovery_time = datetime.now()
            duration = (recovery_time - self._trigger_time).total_seconds() / 60 if self._trigger_time else None

            self._current_state = CircuitBreakerState.SAFE

            logger.info(f"✅ CIRCUIT BREAKER RESUMED after {duration:.0f} minutes")
            if capital_protected:
                logger.info(f"💰 Capital protected: ${capital_protected:.2f}")

            # Update last event with recovery info
            self._update_recovery_info(recovery_time.isoformat(), duration, capital_protected)

            # Reset state
            self._trigger_time = None
            self._trigger_reason = None
            self._recovery_start_time = None

    def _save_event(self, event: CircuitBreakerEvent):
        """Save circuit breaker event to database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO circuit_breaker_events
                (event_id, state, trigger_reason, timestamp, market_snapshot, actions_taken,
                 recovery_timestamp, recovery_duration_minutes, capital_protected_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.state,
                event.trigger_reason,
                event.timestamp,
                json.dumps(event.market_snapshot),
                json.dumps(event.actions_taken),
                event.recovery_timestamp,
                event.recovery_duration_minutes,
                event.capital_protected_usd
            ))

            conn.commit()
            logger.debug(f"Circuit breaker event saved: {event.event_id}")
        except Exception as e:
            logger.error(f"Failed to save circuit breaker event: {e}")
        finally:
            if conn:
                conn.close()

    def _update_recovery_info(self, recovery_timestamp: str, duration: float, capital_protected: Optional[float]):
        """Update recovery information for latest event"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE circuit_breaker_events
                SET recovery_timestamp = ?, recovery_duration_minutes = ?, capital_protected_usd = ?
                WHERE event_id = (SELECT event_id FROM circuit_breaker_events ORDER BY timestamp DESC LIMIT 1)
            ''', (recovery_timestamp, duration, capital_protected))

            conn.commit()
            logger.debug("Circuit breaker recovery info updated")
        except Exception as e:
            logger.error(f"Failed to update recovery info: {e}")
        finally:
            if conn:
                conn.close()

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """Get recent circuit breaker events"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT event_id, state, trigger_reason, timestamp, market_snapshot,
                       actions_taken, recovery_timestamp, recovery_duration_minutes, capital_protected_usd
                FROM circuit_breaker_events
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            events = []
            for row in cursor.fetchall():
                events.append({
                    'event_id': row[0],
                    'state': row[1],
                    'trigger_reason': row[2],
                    'timestamp': row[3],
                    'market_snapshot': json.loads(row[4]) if row[4] else None,
                    'actions_taken': json.loads(row[5]) if row[5] else None,
                    'recovery_timestamp': row[6],
                    'recovery_duration_minutes': row[7],
                    'capital_protected_usd': row[8]
                })

            return events
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_statistics(self) -> Dict:
        """Get circuit breaker statistics"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count total triggers
            cursor.execute('SELECT COUNT(*) FROM circuit_breaker_events WHERE state = "TRIGGERED"')
            total_triggers = cursor.fetchone()[0]

            # Average recovery time
            cursor.execute('SELECT AVG(recovery_duration_minutes) FROM circuit_breaker_events WHERE recovery_duration_minutes IS NOT NULL')
            avg_recovery = cursor.fetchone()[0] or 0

            # Total capital protected
            cursor.execute('SELECT SUM(capital_protected_usd) FROM circuit_breaker_events WHERE capital_protected_usd IS NOT NULL')
            total_protected = cursor.fetchone()[0] or 0

            # Last trigger
            cursor.execute('SELECT timestamp, trigger_reason FROM circuit_breaker_events WHERE state = "TRIGGERED" ORDER BY timestamp DESC LIMIT 1')
            last_trigger = cursor.fetchone()

            return {
                'total_triggers': total_triggers,
                'avg_recovery_minutes': round(avg_recovery, 1),
                'total_capital_protected_usd': round(total_protected, 2),
                'last_trigger_time': last_trigger[0] if last_trigger else None,
                'last_trigger_reason': last_trigger[1] if last_trigger else None
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
        finally:
            if conn:
                conn.close()


# Global circuit breaker state manager instance
_circuit_breaker_instance: Optional[CircuitBreakerStateManager] = None


def get_circuit_breaker() -> CircuitBreakerStateManager:
    """Get global circuit breaker instance (singleton pattern)"""
    global _circuit_breaker_instance
    if _circuit_breaker_instance is None:
        _circuit_breaker_instance = CircuitBreakerStateManager()
    return _circuit_breaker_instance
