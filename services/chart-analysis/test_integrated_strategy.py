#!/usr/bin/env python3
"""
Test script for the integrated RL + Multi-Timeframe strategy
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_multi_timeframe_integration():
    """Test the integrated RL + Multi-Timeframe strategy"""
    
    print("\n" + "="*80)
    print("🧪 TESTING INTEGRATED RL + MULTI-TIMEFRAME STRATEGY")
    print("="*80)
    
    try:
        # Import the enhanced bot
        from rl_bot_ready import RLEnhancedBinanceFuturesBot
        
        print("✅ Successfully imported RLEnhancedBinanceFuturesBot")
        
        # Test with confluence enabled
        print("\n📊 Testing with Multi-Timeframe Confluence ENABLED...")
        bot = RLEnhancedBinanceFuturesBot('SUIUSDC', leverage=20, position_percentage=2.0)
        
        # Verify confluence configuration
        print(f"🔄 Confluence Enabled: {bot.enable_confluence}")
        print(f"📈 Timeframes: {bot.timeframes}")
        print(f"⚖️ Min Alignment Required: {bot.min_timeframes_aligned}")
        
        # Test market data fetch
        print("\n🌐 Testing market data fetch...")
        df = bot.get_market_data()
        if df is not None and len(df) > 50:
            print(f"✅ Market data fetched: {len(df)} candles")
            
            # Test indicator calculation
            print("\n📊 Testing technical indicators...")
            indicators = bot.calculate_indicators(df)
            if indicators:
                print(f"✅ Indicators calculated: {list(indicators.keys())}")
                
                # Test multi-timeframe data fetch
                print("\n🔄 Testing multi-timeframe data fetch...")
                multi_data = bot.get_multi_timeframe_data()
                if multi_data:
                    print(f"✅ Multi-timeframe data fetched for: {list(multi_data.keys())}")
                    for tf_name, tf_df in multi_data.items():
                        print(f"   {tf_name} ({bot.timeframes[tf_name]}): {len(tf_df)} candles")
                else:
                    print("⚠️ Multi-timeframe data fetch failed or returned empty")
                
                # Test signal generation (the main integration point)
                print("\n🎯 Testing integrated signal generation...")
                signal_result = bot.generate_signals(df, indicators)
                
                # Display results
                print(f"\n📈 SIGNAL RESULTS:")
                print(f"   Final Signal: {signal_result.get('signal', 'N/A')}")
                print(f"   Strength: {signal_result.get('strength', 'N/A')}/6")
                print(f"   RL Enhanced: {signal_result.get('rl_enhanced', 'N/A')}")
                
                # Show confluence data if available
                if 'confluence_data' in signal_result:
                    conf = signal_result['confluence_data']
                    print(f"\n🔄 CONFLUENCE DATA:")
                    print(f"   Confluence Signal: {conf.get('signal', 'N/A')}")
                    print(f"   Confluence Strength: {conf.get('strength', 'N/A')}")
                    print(f"   Bullish Timeframes: {conf.get('bullish_count', 'N/A')}")
                    print(f"   Bearish Timeframes: {conf.get('bearish_count', 'N/A')}")
                
                # Show reasons
                reasons = signal_result.get('reasons', [])
                print(f"\n📝 TOP REASONS:")
                for i, reason in enumerate(reasons[:5], 1):
                    print(f"   {i}. {reason}")
                
                # Test with confluence disabled
                print(f"\n" + "-"*60)
                print("🧪 Testing with Multi-Timeframe Confluence DISABLED...")
                bot.enable_confluence = False
                
                signal_result_no_conf = bot.generate_signals(df, indicators)
                print(f"   Signal (No Confluence): {signal_result_no_conf.get('signal', 'N/A')}")
                print(f"   Strength (No Confluence): {signal_result_no_conf.get('strength', 'N/A')}")
                
                # Compare results
                print(f"\n⚖️ COMPARISON:")
                print(f"   With Confluence: Signal={signal_result.get('signal', 'N/A')}, Strength={signal_result.get('strength', 'N/A')}")
                print(f"   Without Confluence: Signal={signal_result_no_conf.get('signal', 'N/A')}, Strength={signal_result_no_conf.get('strength', 'N/A')}")
                
                print(f"\n✅ Integration test completed successfully!")
                
            else:
                print("❌ Failed to calculate indicators")
        else:
            print("❌ Failed to fetch market data or insufficient data")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*80)

def test_configuration_options():
    """Test different configuration options"""
    
    print("\n🔧 TESTING CONFIGURATION OPTIONS")
    print("-" * 50)
    
    try:
        from rl_bot_ready import RLEnhancedBinanceFuturesBot
        
        # Test different timeframe configurations
        configurations = [
            {
                'name': 'Conservative (2 TF alignment)',
                'min_alignment': 2,
                'weights': {'fast': 1.0, 'medium': 1.5, 'slow': 2.0}
            },
            {
                'name': 'Aggressive (1 TF alignment)', 
                'min_alignment': 1,
                'weights': {'fast': 2.0, 'medium': 1.5, 'slow': 1.0}
            },
            {
                'name': 'Balanced (Equal weights)',
                'min_alignment': 2,
                'weights': {'fast': 1.0, 'medium': 1.0, 'slow': 1.0}
            }
        ]
        
        for config in configurations:
            print(f"\n📊 Testing: {config['name']}")
            bot = RLEnhancedBinanceFuturesBot('SUIUSDC')
            bot.min_timeframes_aligned = config['min_alignment']
            bot.confluence_weights = config['weights']
            
            print(f"   Min alignment: {bot.min_timeframes_aligned}")
            print(f"   Weights: {bot.confluence_weights}")
            print(f"   ✅ Configuration set successfully")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

if __name__ == "__main__":
    # Run the main integration test
    test_multi_timeframe_integration()
    
    # Test configuration options
    test_configuration_options()
    
    print(f"\n🎉 All tests completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")