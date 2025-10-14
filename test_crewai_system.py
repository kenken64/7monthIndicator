"""
Comprehensive Test Suite for CrewAI Market Spike Agent System
Tests circuit breaker, spike detection, agents, and database integration
"""

import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print_section("TEST 1: Circuit Breaker System")

    try:
        from circuit_breaker import get_circuit_breaker, MarketSnapshot

        cb = get_circuit_breaker()

        # Test 1.1: Get status
        print("1.1 Testing get_status()...")
        status = cb.get_status()
        print(f"✅ Current state: {status['state']}")
        print(f"   Is safe: {status['is_safe']}")

        # Test 1.2: Check crash conditions (simulate safe market)
        print("\n1.2 Testing check_crash_conditions() with SAFE market...")
        safe_snapshot = MarketSnapshot(
            timestamp=datetime.now().isoformat(),
            btc_price=50000,
            eth_price=2800,
            btc_change_1h=-2.0,  # Safe: <15%
            eth_change_1h=-1.5,
            btc_change_4h=-3.0,
            eth_change_4h=-2.5
        )

        should_trigger, reason = cb.check_crash_conditions(safe_snapshot)
        print(f"✅ Should trigger: {should_trigger} (Expected: False)")
        assert not should_trigger, "Circuit breaker shouldn't trigger for safe conditions"

        # Test 1.3: Check crash conditions (simulate crash)
        print("\n1.3 Testing check_crash_conditions() with CRASH scenario...")
        crash_snapshot = MarketSnapshot(
            timestamp=datetime.now().isoformat(),
            btc_price=42000,
            eth_price=2240,
            btc_change_1h=-17.5,  # CRASH: >15%
            eth_change_1h=-16.0,
            btc_change_4h=-18.0,
            eth_change_4h=-17.0,
            liquidations_1h=600000000  # $600M liquidations
        )

        should_trigger, reason = cb.check_crash_conditions(crash_snapshot)
        print(f"✅ Should trigger: {should_trigger} (Expected: True)")
        print(f"   Reason: {reason}")
        assert should_trigger, "Circuit breaker should trigger for crash conditions"

        # Test 1.4: Get statistics
        print("\n1.4 Testing get_statistics()...")
        stats = cb.get_statistics()
        print(f"✅ Statistics retrieved:")
        print(f"   Total triggers: {stats.get('total_triggers', 0)}")
        print(f"   Avg recovery time: {stats.get('avg_recovery_minutes', 0):.1f} min")
        print(f"   Capital protected: ${stats.get('total_capital_protected_usd', 0):.2f}")

        print("\n✅ Circuit Breaker tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Circuit Breaker test FAILED: {e}")
        logger.error(f"Circuit breaker test error: {e}", exc_info=True)
        return False


def test_crewai_tools():
    """Test custom CrewAI tools"""
    print_section("TEST 2: CrewAI Custom Tools")

    try:
        # Test 2.1: Circuit breaker status tool
        print("2.1 Testing get_circuit_breaker_status tool...")
        from spike_agent_tools import get_circuit_breaker_status

        status_json = get_circuit_breaker_status()
        status = json.loads(status_json)
        print(f"✅ Tool returned: state={status.get('state')}, is_safe={status.get('is_safe')}")

        # Test 2.2: Check if trading safe
        print("\n2.2 Testing check_if_trading_safe tool...")
        from spike_agent_tools import check_if_trading_safe

        safe_json = check_if_trading_safe()
        safe_result = json.loads(safe_json)
        print(f"✅ Trading status: {safe_result.get('status')}")

        # Test 2.3: Get market context
        print("\n2.3 Testing get_market_context tool...")
        from spike_agent_tools import get_market_context

        context_json = get_market_context()
        context = json.loads(context_json)
        print(f"✅ Market context retrieved:")
        print(f"   BTC: ${context.get('btc_price', 0):.2f} ({context.get('btc_change_24h', 0):+.2f}%)")
        print(f"   ETH: ${context.get('eth_price', 0):.2f} ({context.get('eth_change_24h', 0):+.2f}%)")
        print(f"   Fear & Greed: {context.get('fear_greed_index', 'N/A')}")

        # Test 2.4: Calculate position size
        print("\n2.4 Testing calculate_position_size tool...")
        from spike_agent_tools import calculate_position_size

        position_json = calculate_position_size(
            account_balance=10000.0,
            risk_percent=2.0,
            entry_price=50000.0,
            stop_loss_price=49000.0
        )
        position = json.loads(position_json)
        print(f"✅ Position size calculated:")
        print(f"   Units: {position.get('position_size_units', 0):.4f}")
        print(f"   USD: ${position.get('position_size_usd', 0):.2f}")
        print(f"   % of account: {position.get('position_percent_of_account', 0):.2f}%")

        print("\n✅ CrewAI Tools tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ CrewAI Tools test FAILED: {e}")
        logger.error(f"CrewAI tools test error: {e}", exc_info=True)
        return False


def test_database_schema():
    """Test database schema and tables"""
    print_section("TEST 3: Database Schema")

    try:
        import sqlite3

        conn = sqlite3.connect("data/trading_bot.db")
        cursor = conn.cursor()

        # Test 3.1: Check required tables exist
        print("3.1 Verifying required tables...")
        required_tables = [
            'circuit_breaker_events',
            'market_crashes',
            'spike_detections',
            'spike_trades',
            'agent_decisions'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' MISSING")
                raise Exception(f"Required table '{table}' not found")

        # Test 3.2: Check table structures
        print("\n3.2 Checking table structures...")

        # Check spike_detections columns
        cursor.execute("PRAGMA table_info(spike_detections)")
        columns = [row[1] for row in cursor.fetchall()]
        required_columns = ['detection_id', 'symbol', 'spike_type', 'magnitude_percent', 'circuit_breaker_safe']

        for col in required_columns:
            if col in columns:
                print(f"✅ spike_detections has column '{col}'")
            else:
                raise Exception(f"spike_detections missing column '{col}'")

        # Test 3.3: Check indexes
        print("\n3.3 Checking indexes...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='spike_detections'")
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"✅ spike_detections has {len(indexes)} indexes: {', '.join(indexes)}")

        conn.close()

        print("\n✅ Database Schema tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Database Schema test FAILED: {e}")
        logger.error(f"Database schema test error: {e}", exc_info=True)
        return False


def test_agent_initialization():
    """Test CrewAI agent initialization"""
    print_section("TEST 4: CrewAI Agent Initialization")

    try:
        # Test 4.1: Initialize agent system
        print("4.1 Initializing agent system...")
        from crewai_agents import initialize_agent_system

        system = initialize_agent_system()
        print("✅ Agent system initialized")

        # Test 4.2: Check system status
        print("\n4.2 Checking system status...")
        status = system.get_system_status()

        print(f"✅ System status retrieved:")
        print(f"   Circuit Breaker: {status['circuit_breaker']['state']}")

        for agent_name, agent_status in status['agents'].items():
            status_icon = "✅" if agent_status == "active" else "❌"
            print(f"   {status_icon} {agent_name}: {agent_status}")

        for crew_name, crew_status in status['crews'].items():
            status_icon = "✅" if crew_status == "active" else "❌"
            print(f"   {status_icon} {crew_name}: {crew_status}")

        # Verify all agents are active
        assert all(s == "active" for s in status['agents'].values()), "Not all agents active"
        assert all(s == "active" for s in status['crews'].values()), "Not all crews active"

        print("\n✅ Agent Initialization tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Agent Initialization test FAILED: {e}")
        logger.error(f"Agent initialization test error: {e}", exc_info=True)
        return False


def test_configuration():
    """Test configuration loading"""
    print_section("TEST 5: Configuration System")

    try:
        import yaml

        # Test 5.1: Load config file
        print("5.1 Loading configuration file...")
        with open("config/crewai_spike_agent.yaml", 'r') as f:
            config = yaml.safe_load(f)

        print("✅ Configuration loaded successfully")

        # Test 5.2: Verify critical settings
        print("\n5.2 Verifying critical settings...")

        assert config['circuit_breaker']['enabled'] == True, "Circuit breaker must be enabled"
        print("✅ Circuit breaker enabled")

        assert config['circuit_breaker']['thresholds']['btc']['dump_1h_percent'] == 15.0
        print("✅ BTC crash threshold: 15%")

        assert config['spike_detection']['enabled'] == True, "Spike detection must be enabled"
        print("✅ Spike detection enabled")

        assert config['risk_management']['max_position_size_percent'] <= 10.0, "Position size too large"
        print(f"✅ Max position size: {config['risk_management']['max_position_size_percent']}%")

        assert config['execution']['respect_circuit_breaker'] == True, "Must respect circuit breaker"
        print("✅ Execution respects circuit breaker")

        # Test 5.3: Check agent configurations
        print("\n5.3 Checking agent configurations...")
        required_agents = ['market_guardian', 'market_scanner', 'context_analyzer', 'risk_assessment', 'strategy_executor']

        for agent in required_agents:
            assert agent in config['agents'], f"Missing agent config: {agent}"
            assert config['agents'][agent]['enabled'] == True, f"Agent {agent} must be enabled"
            print(f"✅ Agent '{agent}' configured and enabled")

        print("\n✅ Configuration tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Configuration test FAILED: {e}")
        logger.error(f"Configuration test error: {e}", exc_info=True)
        return False


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 70)
    print(" " * 15 + "CREWAI SPIKE AGENT TEST SUITE")
    print("=" * 70)

    results = {
        "Circuit Breaker": test_circuit_breaker(),
        "CrewAI Tools": test_crewai_tools(),
        "Database Schema": test_database_schema(),
        "Configuration": test_configuration(),
        "Agent Initialization": test_agent_initialization()
    }

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("-" * 70)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - System ready for deployment!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review errors above")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
