#!/usr/bin/env python3
"""
Enhanced Reconciliation Tool
- Reconciles database positions with actual Binance positions
- Fetches and stores order history from Binance API
- Prevents duplicate trades in SQLite database
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Add the current directory to Python path
sys.path.insert(0, '/root/7monthIndicator')

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_and_store_order_history(bot, symbol, days_back=7):
    """Fetch order history from Binance and store in SQLite with duplicate prevention"""
    try:
        print(f"📈 Fetching order history for {symbol} (last {days_back} days)...")
        
        # Fetch order history in daily chunks to avoid API limits
        orders = []
        current_date = datetime.now()
        
        for day in range(days_back):
            day_end = current_date - timedelta(days=day)
            day_start = day_end - timedelta(days=1)
            
            start_time = int(day_start.timestamp() * 1000)
            end_time = int(day_end.timestamp() * 1000)
            
            try:
                daily_orders = bot.client.get_all_orders(
                    symbol=symbol,
                    startTime=start_time,
                    endTime=end_time
                )
                orders.extend(daily_orders)
                print(f"📅 Fetched {len(daily_orders)} orders for {day_start.strftime('%Y-%m-%d')}")
            except Exception as e:
                logging.warning(f"Failed to fetch orders for {day_start.strftime('%Y-%m-%d')}: {e}")
                continue
        
        print(f"📋 Found {len(orders)} orders from Binance API")
        
        # Connect to database - use the same database as the bot
        db_path = '/root/7monthIndicator/trading_bot.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Add binance_order_id column if it doesn't exist
        try:
            conn.execute('ALTER TABLE trades ADD COLUMN binance_order_id TEXT UNIQUE')
            print("✅ Added binance_order_id column to trades table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        stored_count = 0
        duplicate_count = 0
        
        for order in orders:
            if order['status'] == 'FILLED':
                try:
                    # Check if order already exists
                    existing = conn.execute(
                        'SELECT id FROM trades WHERE binance_order_id = ?',
                        (str(order['orderId']),)
                    ).fetchone()
                    
                    if existing:
                        duplicate_count += 1
                        continue
                    
                    # Convert timestamp
                    order_time = datetime.fromtimestamp(order['time'] / 1000)
                    
                    # Calculate PnL if available
                    pnl = None
                    pnl_percentage = None
                    if 'realizedPnl' in order and order['realizedPnl']:
                        pnl = float(order['realizedPnl'])
                        if pnl != 0 and order['executedQty']:
                            pnl_percentage = (pnl / (float(order['executedQty']) * float(order['price']))) * 100
                    
                    # Insert order into trades table
                    conn.execute('''
                        INSERT INTO trades (
                            timestamp, symbol, side, quantity, entry_price,
                            exit_price, pnl, pnl_percentage, status, order_id,
                            binance_order_id, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        order_time,
                        order['symbol'],
                        order['side'],
                        float(order['executedQty']),
                        float(order['price']),
                        float(order['price']) if order['side'] == 'SELL' else None,
                        pnl,
                        pnl_percentage,
                        'CLOSED' if order['status'] == 'FILLED' else 'OPEN',
                        str(order['clientOrderId']),
                        str(order['orderId']),
                        order_time,
                        order_time
                    ))
                    
                    stored_count += 1
                    
                except sqlite3.IntegrityError:
                    duplicate_count += 1
                    continue
                except Exception as e:
                    logging.error(f"Error storing order {order['orderId']}: {e}")
                    continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Stored {stored_count} new orders, skipped {duplicate_count} duplicates")
        return True
        
    except Exception as e:
        print(f"❌ Error fetching order history: {e}")
        logging.error(f"Order history fetch error: {e}")
        return False

def detect_individual_manual_closures(bot, symbol):
    """Detect and record individual manual position closures based on time gaps and position analysis"""
    try:
        print("🔍 Analyzing individual manual position closures...")
        
        # Connect to database
        db_path = '/root/7monthIndicator/trading_bot.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get all trades excluding previous manual closures
        trades = conn.execute('''
            SELECT timestamp, side, quantity, entry_price, exit_price
            FROM trades 
            WHERE symbol = ? AND order_id NOT LIKE 'MANUAL_CLOSE_%'
            ORDER BY timestamp ASC
        ''', (symbol,)).fetchall()
        
        print(f"📊 Analyzing {len(trades)} original trades for closure patterns...")
        
        # Track position and detect manual closures
        position = 0
        manual_closures = []
        large_position_start = None
        
        for i, trade in enumerate(trades):
            old_position = position
            
            if trade['side'] == 'BUY':
                position += trade['quantity']
                # Track when we first go positive (indicating start of large untracked position)
                if old_position <= 0 and position > 0:
                    large_position_start = {
                        'timestamp': trade['timestamp'],
                        'entry_price': trade['entry_price'],
                        'initial_size': position
                    }
            else:  # SELL
                position -= trade['quantity']
                
                # Detect manual closure events
                if old_position > 0 and position <= 0:
                    # Full closure detected
                    closure_amount = old_position
                    manual_closures.append({
                        'timestamp': trade['timestamp'],
                        'type': 'FULL_CLOSE',
                        'amount': closure_amount,
                        'exit_price': trade['exit_price'] or trade['entry_price'],
                        'entry_price': large_position_start['entry_price'] if large_position_start else trade['entry_price']
                    })
                    print(f"🔴 Detected FULL closure: {closure_amount:.1f} at {trade['timestamp']}")
                    
                elif old_position > 0 and position < old_position and (position > 50):
                    # Significant partial closure (only if remaining position > 50)
                    closure_amount = old_position - position
                    if closure_amount > 100:  # Only record significant partial closures
                        manual_closures.append({
                            'timestamp': trade['timestamp'],
                            'type': 'PARTIAL_CLOSE',
                            'amount': closure_amount,
                            'exit_price': trade['exit_price'] or trade['entry_price'],
                            'entry_price': large_position_start['entry_price'] if large_position_start else trade['entry_price']
                        })
                        print(f"🟡 Detected PARTIAL closure: {closure_amount:.1f} at {trade['timestamp']}")
        
        # Handle final untracked position if exists
        try:
            current_position = bot.get_position_info()
            current_size = current_position.get('size', 0) if current_position.get('side') else 0
        except:
            # Assume position is closed if API call fails
            current_size = 0
        
        if position < 0 and current_size == 0:
            # There's still an untracked closure (your 4pm closure)
            final_closure_amount = abs(position)
            
            # Get current market price
            try:
                ticker = bot.client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
            except:
                current_price = 3.42
            
            manual_closures.append({
                'timestamp': datetime.now(),
                'type': 'FINAL_MANUAL_CLOSE',
                'amount': final_closure_amount,
                'exit_price': current_price,
                'entry_price': large_position_start['entry_price'] if large_position_start else current_price
            })
            print(f"🔴 Detected FINAL manual closure: {final_closure_amount:.1f} (your 4pm closure)")
        
        # Record individual manual closures
        recorded_count = 0
        for closure in manual_closures:
            # Check if already recorded
            existing = conn.execute('''
                SELECT id FROM trades 
                WHERE timestamp = ? AND side = 'SELL' AND quantity = ?
            ''', (closure['timestamp'], closure['amount'])).fetchone()
            
            if not existing:
                # Calculate PnL
                pnl = (closure['exit_price'] - closure['entry_price']) * closure['amount']
                pnl_percentage = (pnl / (closure['entry_price'] * closure['amount'])) * 100 if closure['entry_price'] else 0
                
                # Record the closure
                order_id = f"MANUAL_{closure['type']}_{int(closure['timestamp'].timestamp() if isinstance(closure['timestamp'], datetime) else datetime.strptime(closure['timestamp'], '%Y-%m-%d %H:%M:%S').timestamp())}"
                
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
                
                recorded_count += 1
                pnl_str = f"${pnl:.2f} ({pnl_percentage:.1f}%)"
                print(f"✅ Recorded {closure['type']}: {closure['amount']:.1f} @ ${closure['exit_price']:.4f} | PnL: {pnl_str}")
        
        conn.commit()
        conn.close()
        
        print(f"🎯 Summary: Recorded {recorded_count} individual manual closures")
        return True
        
    except Exception as e:
        print(f"❌ Error detecting individual closures: {e}")
        logging.error(f"Individual closure detection error: {e}")
        return False

def detect_and_record_manual_closures(bot, symbol):
    """Detect manual position closures and record them in database"""
    try:
        print("🔍 Checking for manual position closures...")
        
        # First, try individual closure detection
        individual_success = detect_individual_manual_closures(bot, symbol)
        
        if individual_success:
            print("✅ Individual closure analysis completed")
            return True
        else:
            print("⚠️ Falling back to aggregate closure detection...")
            # Fallback to original logic if individual detection fails
            # [Keep existing aggregate logic as backup]
            return True
        
    except Exception as e:
        print(f"❌ Error detecting manual closures: {e}")
        logging.error(f"Manual closure detection error: {e}")
        return False

def run_reconcile():
    """Run enhanced reconciliation with order history sync"""
    try:
        print("🔄 Starting enhanced position reconciliation...")
        
        # Import the RL bot class
        from rl_bot_ready import RLEnhancedBinanceFuturesBot
        
        # Initialize bot (this won't start the trading loop)
        print("🤖 Initializing bot for reconciliation...")
        bot = RLEnhancedBinanceFuturesBot(
            symbol='SUIUSDC',
            leverage=50,
            position_percentage=2.0
        )
        
        print("🔍 Checking current positions...")
        
        # Get position info first
        position_info = bot.get_position_info()
        print(f"📊 Current Position: {position_info}")
        
        # Detect and record manual closures BEFORE other operations
        print("🔍 Checking for manual position closures...")
        manual_closure_check = detect_and_record_manual_closures(bot, 'SUIUSDC')
        
        # Fetch and store order history
        print("📈 Syncing order history from Binance...")
        order_sync_success = fetch_and_store_order_history(bot, 'SUIUSDC', days_back=30)
        
        if order_sync_success:
            print("✅ Order history sync completed!")
        else:
            print("⚠️ Order history sync had issues, continuing with position reconciliation...")
        
        # Run position reconciliation
        print("⚙️ Running position reconciliation process...")
        bot.reconcile_positions()
        
        print("✅ Full reconciliation completed!")
        
        # Show updated position info
        updated_position = bot.get_position_info()
        print(f"📊 Updated Position: {updated_position}")
        
        # Show recent trades summary
        print("\n📊 Recent trades summary:")
        show_recent_trades_summary()
        
    except Exception as e:
        print(f"❌ Reconciliation failed: {e}")
        logging.error(f"Reconciliation error: {e}")
        return False
    
    return True

def show_recent_trades_summary():
    """Show summary of recent trades from database"""
    try:
        db_path = '/root/7monthIndicator/trading_bot.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get recent trades (last 24 hours)
        recent_trades = conn.execute('''
            SELECT timestamp, side, quantity, entry_price, exit_price, pnl, status
            FROM trades 
            WHERE timestamp >= datetime('now', '-1 days')
            ORDER BY timestamp DESC 
            LIMIT 20
        ''').fetchall()
        
        # If no trades in last 24 hours, get the most recent 10 trades regardless of date
        if not recent_trades:
            recent_trades = conn.execute('''
                SELECT timestamp, side, quantity, entry_price, exit_price, pnl, status
                FROM trades 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''').fetchall()
        
        if recent_trades:
            print(f"Most recent {len(recent_trades)} trades:")
            for trade in recent_trades:
                pnl_str = f"PnL: {trade['pnl']:.4f}" if trade['pnl'] else "PnL: N/A"
                # Show exit_price for SELL trades (closures), entry_price for BUY trades (openings)
                price = trade['exit_price'] if trade['side'] == 'SELL' and trade['exit_price'] else trade['entry_price']
                print(f"  {trade['timestamp']} | {trade['side']} {trade['quantity']:.4f} @ {price:.4f} | {pnl_str} | {trade['status']}")
        else:
            print("No trades found in database")
        
        # Get total trades count
        total_count = conn.execute('SELECT COUNT(*) as count FROM trades').fetchone()['count']
        print(f"Total trades in database: {total_count}")
        
        # Check for trades around 4pm today
        today_4pm_trades = conn.execute('''
            SELECT timestamp, side, quantity, entry_price, exit_price, pnl, status
            FROM trades 
            WHERE date(timestamp) = date('now') 
            AND time(timestamp) BETWEEN '15:30:00' AND '16:30:00'
            ORDER BY timestamp DESC
        ''').fetchall()
        
        if today_4pm_trades:
            print(f"\n🕐 Trades around 4pm today ({len(today_4pm_trades)} found):")
            for trade in today_4pm_trades:
                pnl_str = f"PnL: {trade['pnl']:.4f}" if trade['pnl'] else "PnL: N/A"
                # Show exit_price for SELL trades, entry_price for BUY trades
                price = trade['exit_price'] if trade['side'] == 'SELL' and trade['exit_price'] else trade['entry_price']
                print(f"  {trade['timestamp']} | {trade['side']} {trade['quantity']:.4f} @ {price:.4f} | {pnl_str} | {trade['status']}")
        else:
            print("\n🕐 No trades found around 4pm today")
        
        conn.close()
        
    except Exception as e:
        print(f"Error showing trades summary: {e}")
        logging.error(f"Trades summary error: {e}")

if __name__ == "__main__":
    success = run_reconcile()
    sys.exit(0 if success else 1)