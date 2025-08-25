#!/usr/bin/env python3
"""
Debug RL log parsing
"""
import re
from datetime import datetime, timedelta

# Sample log line from the RL bot
test_lines = [
    "2025-08-25 03:16:47,566 - INFO - 📊 ENHANCED DECISION:",
    "2025-08-25 03:16:47,566 - INFO -    Original: Signal=1, Strength=4",
    "2025-08-25 03:16:47,566 - INFO -    RL: Action=HOLD, Confidence=50.0%",
    "2025-08-25 03:16:47,566 - INFO -    Final: Signal=0, Strength=0",
    "2025-08-25 03:16:47,566 - INFO -    Reason: Safety first: Original=1, RL=HOLD, insufficient confidence",
    "2025-08-25 03:16:47,566 - INFO - 📍 Position: No open position",
    "2025-08-25 03:16:47,567 - INFO - 💹 SUIUSDC: $3.7205 | RSI: 73.9 | VWAP: $3.6943",
    "2025-08-25 03:16:47,567 - INFO - 🎯 Signal: ⚪ HOLD (Strength: 0)"
]

print("Testing RL log parsing...")

for line in test_lines:
    print(f"\nTesting: {line}")
    
    # Test timestamp extraction
    timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
    if timestamp_match:
        timestamp_str = timestamp_match.group(1)
        print(f"  Timestamp: {timestamp_str}")
        
        try:
            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            time_diff = datetime.now() - log_time
            print(f"  Time diff: {time_diff} (within 60 min: {time_diff < timedelta(minutes=60)})")
        except Exception as e:
            print(f"  Time parsing error: {e}")
    
    # Test RL Enhanced Decision
    if '📊 ENHANCED DECISION:' in line:
        print("  ✓ RL Enhanced Decision detected")
    
    # Test original signal
    if 'Original: Signal=' in line and 'Strength=' in line:
        match = re.search(r'Original: Signal=([^,]+), Strength=(\d+)', line)
        if match:
            print(f"  ✓ Original signal: {match.group(1)}, strength: {match.group(2)}")
        else:
            print("  ✗ Original signal pattern failed")
    
    # Test RL action
    if 'RL: Action=' in line and 'Confidence=' in line:
        match = re.search(r'RL: Action=([^,]+), Confidence=([^%]+)', line)
        if match:
            print(f"  ✓ RL action: {match.group(1)}, confidence: {match.group(2)}")
        else:
            print("  ✗ RL action pattern failed")
    
    # Test market data
    if '💹' in line and 'RSI:' in line and 'VWAP:' in line:
        market_match = re.search(r'💹 ([^:]+): \$([^|]+) \| RSI: ([^|]+) \| VWAP: \$([^$]+)', line)
        if market_match:
            print(f"  ✓ Market data: {market_match.group(1)} @ ${market_match.group(2)}, RSI: {market_match.group(3)}, VWAP: ${market_match.group(4)}")
        else:
            print("  ✗ Market data pattern failed")
    
    # Test signal info
    if '🎯 Signal:' in line:
        signal_match = re.search(r'🎯 Signal: [⚪🟢🔴] (\w+) \(Strength: (\d+)\)', line)
        if signal_match:
            print(f"  ✓ Signal: {signal_match.group(1)}, strength: {signal_match.group(2)}")
        else:
            print("  ✗ Signal pattern failed")