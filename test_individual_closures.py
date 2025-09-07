#!/usr/bin/env python3
import sqlite3
from datetime import datetime

db_path = '/root/7monthIndicator/data/trading_bot.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Get trades excluding manual closures
trades = conn.execute('''
    SELECT timestamp, side, quantity, entry_price, exit_price
    FROM trades 
    WHERE order_id NOT LIKE 'MANUAL_%'
    ORDER BY timestamp ASC
''').fetchall()

print('🔍 Recording individual manual closures to database...')

position = 0
manual_closures = []
large_position_start = None

for trade in trades:
    old_position = position
    
    if trade['side'] == 'BUY':
        position += trade['quantity']
        if old_position <= 0 and position > 0:
            large_position_start = {
                'timestamp': trade['timestamp'],
                'entry_price': trade['entry_price']
            }
    else:
        position -= trade['quantity']
        
        if old_position > 0 and position <= 0:
            # Full closure
            closure_amount = old_position
            exit_price = trade['exit_price'] if trade['exit_price'] else trade['entry_price']
            entry_price = large_position_start['entry_price'] if large_position_start else trade['entry_price']
            
            manual_closures.append({
                'timestamp': trade['timestamp'],
                'type': 'FULL_CLOSE',
                'amount': closure_amount,
                'exit_price': exit_price,
                'entry_price': entry_price
            })
        elif old_position > 0 and position < old_position:
            # Partial closure
            closure_amount = old_position - position
            if closure_amount > 100:  # Only significant partials
                exit_price = trade['exit_price'] if trade['exit_price'] else trade['entry_price']
                entry_price = large_position_start['entry_price'] if large_position_start else trade['entry_price']
                
                manual_closures.append({
                    'timestamp': trade['timestamp'],
                    'type': 'PARTIAL_CLOSE',
                    'amount': closure_amount,
                    'exit_price': exit_price,
                    'entry_price': entry_price
                })

# Add final closure (your 4pm)
if position < 0:
    final_amount = abs(position)
    entry_price = large_position_start['entry_price'] if large_position_start else 3.42
    
    manual_closures.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': 'FINAL_MANUAL_CLOSE',
        'amount': final_amount,
        'exit_price': 3.42,
        'entry_price': entry_price
    })

# Insert closures into database
recorded_count = 0
for closure in manual_closures:
    # Check if already exists
    existing = conn.execute('''
        SELECT id FROM trades 
        WHERE timestamp = ? AND side = 'SELL' AND quantity = ?
    ''', (closure['timestamp'], closure['amount'])).fetchone()
    
    if not existing:
        # Calculate PnL
        pnl = (closure['exit_price'] - closure['entry_price']) * closure['amount']
        pnl_percentage = (pnl / (closure['entry_price'] * closure['amount'])) * 100 if closure['entry_price'] > 0 else 0
        
        # Create order ID
        ts_str = closure['timestamp'].replace(' ', '_').replace(':', '').replace('-', '')
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
            'SUIUSDC',
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
        
        recorded_count += 1
        pnl_str = f"${pnl:.2f} ({pnl_percentage:.1f}%)"
        print(f"✅ Recorded {closure['type']}: {closure['amount']:.1f} @ ${closure['exit_price']:.4f} | PnL: {pnl_str}")

conn.commit()
conn.close()

print(f"\n🎯 Successfully recorded {recorded_count} individual manual closures!")
print("Now they should appear in recent trades.")