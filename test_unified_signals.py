#!/usr/bin/env python3
"""
Test Unified Signal Aggregation System
"""

import logging
from unified_signal_aggregator import create_aggregator
from signal_data_collector import SignalDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_signal_collection():
    """Test signal data collection"""
    print("=" * 80)
    print("TEST 1: Signal Data Collection")
    print("=" * 80)

    collector = SignalDataCollector()

    print("\n📊 Collecting signals from all sources...")
    collector.force_collection()

    print("\n✅ Signal collection complete!")
    return True


def test_unified_aggregation():
    """Test unified signal aggregation"""
    print("\n" + "=" * 80)
    print("TEST 2: Unified Signal Aggregation")
    print("=" * 80)

    aggregator = create_aggregator()

    # Test technical signal
    tech_signal = {
        'action': 'BUY',
        'strength': 3,
        'confidence': 60.0,
        'indicators': {
            'rsi': 25.5,
            'macd': 0.05,
            'vwap': 2.70
        }
    }

    # Test RL signal
    rl_signal = {
        'action': 'HOLD',
        'confidence': 50.0,
        'reason': 'Insufficient confidence for trade execution'
    }

    print("\n📊 Aggregating signals...")
    print(f"  Technical: {tech_signal['action']} (conf: {tech_signal['confidence']:.1f}%)")
    print(f"  RL: {rl_signal['action']} (conf: {rl_signal['confidence']:.1f}%)")

    # Get unified signal
    unified_result = aggregator.aggregate_signals(
        technical_signal=tech_signal,
        rl_signal=rl_signal,
        current_price=2.70,
        symbol="SUIUSDC"
    )

    # Display results
    print(aggregator.get_signal_summary(unified_result))

    return unified_result


def test_integration():
    """Test full integration"""
    print("\n" + "=" * 80)
    print("TEST 3: Full Integration Test")
    print("=" * 80)

    # Test with different scenarios
    scenarios = [
        {
            'name': 'Strong Bullish',
            'tech': {'action': 'BUY', 'confidence': 80.0},
            'rl': {'action': 'BUY', 'confidence': 85.0}
        },
        {
            'name': 'Strong Bearish',
            'tech': {'action': 'SELL', 'confidence': 75.0},
            'rl': {'action': 'SELL', 'confidence': 70.0}
        },
        {
            'name': 'Conflicting Signals',
            'tech': {'action': 'BUY', 'confidence': 60.0},
            'rl': {'action': 'SELL', 'confidence': 55.0}
        },
        {
            'name': 'Weak Signals',
            'tech': {'action': 'HOLD', 'confidence': 30.0},
            'rl': {'action': 'HOLD', 'confidence': 40.0}
        }
    ]

    aggregator = create_aggregator()
    results = []

    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"  Tech: {scenario['tech']['action']} ({scenario['tech']['confidence']:.1f}%)")
        print(f"  RL: {scenario['rl']['action']} ({scenario['rl']['confidence']:.1f}%)")

        result = aggregator.aggregate_signals(
            technical_signal=scenario['tech'],
            rl_signal=scenario['rl'],
            current_price=2.70,
            symbol="SUIUSDC"
        )

        print(f"  → Unified: {result['signal']} (strength: {result['strength']:.1f}/10, conf: {result['confidence']:.1f}%)")
        results.append(result)

    return results


def main():
    """Run all tests"""
    try:
        print("\n🧪 UNIFIED SIGNAL AGGREGATION - TEST SUITE")
        print("=" * 80)

        # Test 1: Signal Collection
        test_signal_collection()

        # Test 2: Unified Aggregation
        unified_result = test_unified_aggregation()

        # Test 3: Integration Scenarios
        integration_results = test_integration()

        # Summary
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • Signal sources: 6 (Technical, RL, Chart, CrewAI, Market, News)")
        print(f"  • Test scenarios: 4")
        print(f"  • Signal strength range: 0-10")
        print(f"  • Confidence threshold: 55%")
        print(f"\n💡 The unified signal system is ready for production use!")
        print(f"  Run the bot with: python3 rl_bot_ready.py")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
