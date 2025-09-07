#!/usr/bin/env python3
"""
Test Enhanced Reward System

Simple test script to verify the enhanced reward system works correctly
and compare it against the traditional reward system.
"""

import sys
import json
import numpy as np
from enhanced_reward_system import EnhancedRewardCalculator, TradeMetrics
from lightweight_rl import TradingSimulator
from database import get_database

def test_enhanced_rewards():
    """Test the enhanced reward system with sample data"""
    
    print("🧪 Testing Enhanced Reward System...")
    
    # Create sample market data
    sample_data = []
    for i in range(100):
        # Simulate price movement and indicators
        price = 3.7 + (np.sin(i * 0.1) * 0.1) + (np.random.random() - 0.5) * 0.05
        rsi = 50 + (np.sin(i * 0.2) * 30)
        
        sample_data.append({
            'price': price,
            'rsi': rsi,
            'macd': np.random.random() - 0.5,
            'volume': 1000 + np.random.random() * 500,
            'volatility': 0.02 + np.random.random() * 0.03
        })
    
    print(f"✅ Generated {len(sample_data)} sample data points")
    
    # Test traditional vs enhanced reward systems
    print("\n📊 Comparing Traditional vs Enhanced Reward Systems:")
    
    # Traditional system
    traditional_sim = TradingSimulator(sample_data, use_enhanced_rewards=False)
    traditional_rewards = []
    
    # Enhanced system
    enhanced_sim = TradingSimulator(sample_data, use_enhanced_rewards=True)
    enhanced_rewards = []
    
    # Run parallel simulations
    actions = ['BUY', 'HOLD', 'HOLD', 'CLOSE', 'SELL', 'HOLD', 'CLOSE']
    
    # Traditional simulation
    trad_state = traditional_sim.reset()
    for action in actions:
        next_state, reward, done = traditional_sim.step(action)
        traditional_rewards.append(reward)
        if done:
            break
    
    # Enhanced simulation
    enh_state = enhanced_sim.reset()
    for action in actions:
        next_state, reward, done = enhanced_sim.step(action)
        enhanced_rewards.append(reward)
        if done:
            break
    
    # Compare results
    print(f"\n📈 Traditional System:")
    print(f"   Rewards: {[f'{r:.6f}' for r in traditional_rewards]}")
    print(f"   Total Reward: {sum(traditional_rewards):.6f}")
    print(f"   Final Balance: ${traditional_sim.balance:.2f}")
    print(f"   Trades: {len(traditional_sim.trades_history)}")
    
    print(f"\n🚀 Enhanced System:")
    print(f"   Rewards: {[f'{r:.6f}' for r in enhanced_rewards]}")
    print(f"   Total Reward: {sum(enhanced_rewards):.6f}")
    print(f"   Final Balance: ${enhanced_sim.balance:.2f}")
    print(f"   Trades: {len(enhanced_sim.trades_history)}")
    
    # Show enhanced reward breakdown
    if enhanced_sim.reward_calculator:
        breakdown = enhanced_sim.reward_calculator.get_reward_breakdown()
        print(f"\n🔍 Enhanced Reward System Breakdown:")
        print(f"   Portfolio Metrics: {breakdown['portfolio_metrics']}")
        print(f"   Recent Trades: {breakdown['recent_trades']}")
    
    print(f"\n✅ Enhanced Reward System Test Complete!")
    
    return True

def test_with_real_data():
    """Test with real market data from database"""
    
    print("\n🗄️  Testing with Real Market Data...")
    
    try:
        db = get_database()
        
        with db.get_connection() as conn:
            # Get recent market data
            query = """
                SELECT timestamp, symbol, price, signal, strength, indicators
                FROM signals 
                WHERE indicators IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 200
            """
            cursor = conn.execute(query)
            real_data = []
            
            for row in cursor.fetchall():
                row_dict = dict(row)
                
                # Parse indicators JSON
                if row_dict['indicators']:
                    indicators = json.loads(row_dict['indicators'])
                    row_dict.update(indicators)
                
                real_data.append(row_dict)
        
        if len(real_data) < 50:
            print("⚠️  Insufficient real data for testing")
            return False
        
        print(f"✅ Loaded {len(real_data)} real data points")
        
        # Test enhanced system with real data
        enhanced_sim = TradingSimulator(real_data, use_enhanced_rewards=True)
        
        # Simple trading sequence
        state = enhanced_sim.reset()
        total_reward = 0
        
        # Simulate some trades
        actions_sequence = ['BUY', 'HOLD', 'HOLD', 'CLOSE', 'HOLD', 'SELL', 'HOLD', 'CLOSE']
        
        for action in actions_sequence:
            next_state, reward, done = enhanced_sim.step(action)
            total_reward += reward
            
            print(f"   Action: {action:5s} | Reward: {reward:8.6f} | Balance: ${enhanced_sim.balance:7.2f}")
            
            if done or not next_state:
                break
        
        print(f"\n📊 Real Data Test Results:")
        print(f"   Total Reward: {total_reward:.6f}")
        print(f"   Final Balance: ${enhanced_sim.balance:.2f}")
        print(f"   Total Trades: {len(enhanced_sim.trades_history)}")
        
        if enhanced_sim.trades_history:
            winning_trades = [t for t in enhanced_sim.trades_history if t['pnl_pct'] > 0]
            win_rate = len(winning_trades) / len(enhanced_sim.trades_history) * 100
            print(f"   Win Rate: {win_rate:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing with real data: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Enhanced Reward System Testing Suite")
    print("=" * 50)
    
    # Test basic functionality
    success1 = test_enhanced_rewards()
    
    # Test with real data
    success2 = test_with_real_data()
    
    if success1 and success2:
        print("\n🎉 All Enhanced Reward System Tests Passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)