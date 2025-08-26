#!/usr/bin/env python3
"""
Web Dashboard for Trading Bot Analysis
Flask web application to display trading signals and performance metrics
"""

import json
import os
import time
from flask import Flask, render_template, jsonify, request
from database import get_database
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
app.secret_key = 'trading_bot_secret_key'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/performance/<symbol>')
def get_performance(symbol):
    """API endpoint to get performance metrics"""
    days = request.args.get('days', 30, type=int)
    db = get_database()
    
    try:
        # First try to get closed trades performance
        performance = db.calculate_performance_metrics(symbol, days)
        
        # If no closed trades, calculate from open positions with current prices
        if performance.get('total_trades', 0) == 0:
            from binance.client import Client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            api_key = os.getenv('BINANCE_API_KEY')
            secret_key = os.getenv('BINANCE_SECRET_KEY')
            
            if api_key and secret_key:
                try:
                    client = Client(api_key, secret_key, testnet=False)
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    
                    # Calculate unrealized performance from open trades
                    with db.get_connection() as conn:
                        query = '''
                            SELECT * FROM trades 
                            WHERE symbol = ? AND status = 'OPEN' 
                            AND timestamp >= datetime('now', '-{} days')
                        '''.format(days)
                        
                        cursor = conn.execute(query, (symbol,))
                        open_trades = [dict(row) for row in cursor.fetchall()]
                        
                        if open_trades:
                            total_pnl = 0
                            winning_trades = 0
                            losing_trades = 0
                            wins = []
                            losses = []
                            
                            for trade in open_trades:
                                # Calculate unrealized PnL
                                if trade['side'] == 'BUY':
                                    pnl = (current_price - trade['entry_price']) * trade['quantity']
                                else:  # SELL
                                    pnl = (trade['entry_price'] - current_price) * trade['quantity']
                                
                                total_pnl += pnl
                                
                                if pnl > 0:
                                    winning_trades += 1
                                    wins.append(pnl)
                                elif pnl < 0:
                                    losing_trades += 1
                                    losses.append(pnl)
                            
                            total_trades = len(open_trades)
                            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                            avg_win = sum(wins) / len(wins) if wins else 0
                            avg_loss = sum(losses) / len(losses) if losses else 0
                            max_loss = min(losses) if losses else 0
                            
                            performance = {
                                'total_trades': total_trades,
                                'winning_trades': winning_trades,
                                'losing_trades': losing_trades,
                                'win_rate': win_rate,
                                'total_pnl': total_pnl,
                                'avg_win': avg_win,
                                'avg_loss': avg_loss,
                                'max_loss': max_loss,
                                'days': days,
                                'is_unrealized': True
                            }
                        
                except Exception as api_error:
                    logger.error(f"Error calculating unrealized performance: {api_error}")
        
        return jsonify({
            'success': True,
            'data': performance
        })
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/signals/<symbol>')
def get_signals(symbol):
    """API endpoint to get recent signals"""
    limit = request.args.get('limit', 20, type=int)
    db = get_database()
    
    try:
        signals = db.get_recent_signals(symbol, limit)
        return jsonify({
            'success': True,
            'data': signals
        })
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trades/<symbol>')
def get_trades(symbol):
    """API endpoint to get recent trades"""
    limit = request.args.get('limit', 20, type=int)
    db = get_database()
    
    try:
        trades = db.get_recent_trades(symbol, limit)
        return jsonify({
            'success': True,
            'data': trades
        })
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/open-positions/<symbol>')
def get_open_positions(symbol):
    """API endpoint to get live open positions from Binance"""
    from binance.client import Client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    db = get_database()
    
    try:
        # Get positions from database
        db_positions = db.get_open_trades(symbol)
        
        # Also get live positions from Binance API
        try:
            api_key = os.getenv('BINANCE_API_KEY')
            secret_key = os.getenv('BINANCE_SECRET_KEY')
            
            if api_key and secret_key:
                client = Client(api_key, secret_key, testnet=False)
                live_positions = client.futures_position_information()
                
                # Filter for requested symbol and non-zero positions
                binance_positions = []
                for pos in live_positions:
                    if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                        position_amt = float(pos['positionAmt'])
                        entry_price = float(pos['entryPrice'])
                        mark_price = float(pos['markPrice'])
                        
                        # Calculate PnL percentage with leverage
                        if entry_price > 0:
                            if position_amt > 0:  # LONG
                                pnl_percentage = ((mark_price - entry_price) / entry_price) * 100 * 50  # Assuming 50x leverage
                            else:  # SHORT
                                pnl_percentage = ((entry_price - mark_price) / entry_price) * 100 * 50
                        else:
                            pnl_percentage = 0
                        
                        binance_positions.append({
                            'symbol': pos['symbol'],
                            'side': 'LONG' if position_amt > 0 else 'SHORT',
                            'size': abs(position_amt),
                            'entry_price': entry_price,
                            'mark_price': mark_price,
                            'unrealized_pnl': float(pos['unRealizedProfit']),
                            'liquidation_price': float(pos['liquidationPrice']) if pos['liquidationPrice'] != '0' else 0,
                            'percentage': pnl_percentage,
                            'margin_type': pos['marginType'],
                            'source': 'binance_live'
                        })
                
                return jsonify({
                    'success': True,
                    'data': {
                        'database_positions': db_positions,
                        'live_positions': binance_positions
                    }
                })
            else:
                logger.warning("No Binance API credentials found")
                
        except Exception as api_error:
            logger.error(f"Error fetching live positions: {api_error}")
        
        # Fallback to database positions only
        return jsonify({
            'success': True,
            'data': {
                'database_positions': db_positions,
                'live_positions': []
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting open positions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chart-data/<symbol>')
def get_chart_data(symbol):
    """API endpoint to get chart data for visualization"""
    days = request.args.get('days', 30, type=int)
    db = get_database()
    
    try:
        with db.get_connection() as conn:
            # Get closed trades for PnL chart
            trades_query = '''
                SELECT timestamp, pnl, side, quantity, entry_price, exit_price
                FROM trades 
                WHERE symbol = ? AND status = 'CLOSED'
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp
            '''.format(days)
            
            cursor = conn.execute(trades_query, (symbol,))
            trades = []
            cumulative_pnl = 0
            
            for row in cursor.fetchall():
                trade = dict(row)
                cumulative_pnl += trade['pnl'] or 0
                trade['cumulative_pnl'] = cumulative_pnl
                trades.append(trade)
            
            # Get signals for signal strength chart
            signals_query = '''
                SELECT timestamp, signal, strength, price
                FROM signals
                WHERE symbol = ? 
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp
            '''.format(days)
            
            cursor = conn.execute(signals_query, (symbol,))
            signals = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'success': True,
                'data': {
                    'trades': trades,
                    'signals': signals
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system-stats')
def get_system_stats():
    """API endpoint to get system statistics"""
    db = get_database()
    
    try:
        with db.get_connection() as conn:
            # Get total counts
            stats = {}
            
            cursor = conn.execute('SELECT COUNT(*) as count FROM signals')
            stats['total_signals'] = cursor.fetchone()['count']
            
            cursor = conn.execute('SELECT COUNT(*) as count FROM trades')
            stats['total_trades'] = cursor.fetchone()['count']
            
            cursor = conn.execute('SELECT COUNT(*) as count FROM trades WHERE status = "OPEN"')
            stats['open_trades'] = cursor.fetchone()['count']
            
            # Get last signal time
            cursor = conn.execute('SELECT MAX(timestamp) as last_signal FROM signals')
            stats['last_signal'] = cursor.fetchone()['last_signal']
            
            # Get symbols
            cursor = conn.execute('SELECT DISTINCT symbol FROM signals ORDER BY symbol')
            stats['symbols'] = [row['symbol'] for row in cursor.fetchall()]
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/projected-balance/<symbol>')
def get_projected_balance(symbol):
    """API endpoint to get projected account balance based on performance trends"""
    days = request.args.get('days', 30, type=int)
    projection_days = request.args.get('projection_days', 30, type=int)
    
    db = get_database()
    
    try:
        from binance.client import Client
        import os
        from dotenv import load_dotenv
        import numpy as np
        
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'API credentials not available'
            }), 400
        
        client = Client(api_key, secret_key, testnet=False)
        
        # Get current account balance (check both Spot and Futures)
        current_balance = 0.0
        
        try:
            # Check Futures account balance (total wallet balance, not just available)
            futures_account = client.futures_account()
            
            # Get total wallet balance (includes margin used in positions)
            total_wallet = float(futures_account['totalWalletBalance'])
            
            # Also check individual USDC balance in futures
            futures_usdc = 0.0
            for asset in futures_account['assets']:
                if asset['asset'] == 'USDC':
                    futures_usdc = float(asset['walletBalance'])
                    break
            
            current_balance += futures_usdc
            logger.info(f"Futures USDC balance: ${futures_usdc} (Total wallet: ${total_wallet})")
        except Exception as e:
            logger.warning(f"Could not get futures balance: {e}")
        
        try:
            # Check Spot account USDC balance
            account = client.get_account()
            for asset in account['balances']:
                if asset['asset'] == 'USDC':
                    spot_usdc = float(asset['free']) + float(asset['locked'])
                    current_balance += spot_usdc
                    logger.info(f"Spot USDC balance: ${spot_usdc}")
                    break
        except Exception as e:
            logger.warning(f"Could not get spot balance: {e}")
            
        logger.info(f"Total account balance: ${current_balance}")
        
        # Get historical performance
        performance = db.calculate_performance_metrics(symbol, days)
        
        # Calculate daily performance metrics
        with db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    SUM(CASE WHEN pnl IS NOT NULL THEN pnl ELSE 0 END) as daily_pnl,
                    COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as trades_closed
                FROM trades 
                WHERE symbol = ? AND timestamp >= date('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            '''.format(days), (symbol,))
            
            daily_performance = cursor.fetchall()
        
        # Calculate projections
        projections = []
        
        if daily_performance:
            # Calculate daily PnL statistics
            daily_pnls = [row['daily_pnl'] for row in daily_performance if row['daily_pnl'] != 0]
            
            if daily_pnls:
                avg_daily_pnl = np.mean(daily_pnls)
                std_daily_pnl = np.std(daily_pnls)
                win_rate = performance.get('win_rate', 0) / 100.0
                
                # Create different projection scenarios
                scenarios = {
                    'conservative': avg_daily_pnl * 0.5,  # 50% of historical performance
                    'realistic': avg_daily_pnl * 0.8,    # 80% of historical performance
                    'optimistic': avg_daily_pnl * 1.0,   # Full historical performance
                    'pessimistic': avg_daily_pnl * 0.2   # 20% of historical performance
                }
                
                # Generate daily projections for each scenario
                for scenario_name, daily_return in scenarios.items():
                    projected_balance = current_balance
                    scenario_projections = []
                    
                    for day in range(1, projection_days + 1):
                        # Add some randomization based on historical volatility
                        if scenario_name == 'realistic':
                            # Add slight volatility to realistic scenario
                            daily_variation = np.random.normal(0, std_daily_pnl * 0.1)
                            projected_return = daily_return + daily_variation
                        else:
                            projected_return = daily_return
                        
                        projected_balance += projected_return
                        
                        # Ensure balance doesn't go negative
                        projected_balance = max(0, projected_balance)
                        
                        scenario_projections.append({
                            'day': day,
                            'balance': round(projected_balance, 2),
                            'cumulative_pnl': round(projected_balance - current_balance, 2)
                        })
                    
                    projections.append({
                        'scenario': scenario_name,
                        'daily_return': round(daily_return, 2),
                        'projections': scenario_projections
                    })
            
            # Add RL enhancement projection if RL bot is active
            try:
                # Check if RL bot is running and has better performance potential
                rl_multiplier = 1.5  # Assume RL can improve performance by 50%
                rl_daily_return = avg_daily_pnl * rl_multiplier * 0.3  # Conservative RL estimate
                
                projected_balance = current_balance
                rl_projections = []
                
                for day in range(1, projection_days + 1):
                    projected_balance += rl_daily_return
                    projected_balance = max(0, projected_balance)
                    
                    rl_projections.append({
                        'day': day,
                        'balance': round(projected_balance, 2),
                        'cumulative_pnl': round(projected_balance - current_balance, 2)
                    })
                
                projections.append({
                    'scenario': 'rl_enhanced',
                    'daily_return': round(rl_daily_return, 2),
                    'projections': rl_projections
                })
                
            except:
                pass
        
        return jsonify({
            'success': True,
            'data': {
                'current_balance': current_balance,
                'historical_period_days': days,
                'projection_period_days': projection_days,
                'projections': projections,
                'performance_stats': {
                    'avg_daily_pnl': round(np.mean(daily_pnls) if daily_pnls else 0, 2),
                    'win_rate': performance.get('win_rate', 0),
                    'total_trades': performance.get('total_trades', 0),
                    'profitable_trades': performance.get('profitable_trades', 0)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating projected balance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rl-decisions/<symbol>')
def get_rl_decisions(symbol):
    """API endpoint to get recent RL-enhanced decisions"""
    limit = request.args.get('limit', 5, type=int)
    db = get_database()
    
    try:
        signals = db.get_recent_rl_signals(symbol, limit)
        return jsonify({
            'success': True,
            'data': signals
        })
    except Exception as e:
        logger.error(f"Error getting RL decisions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/logs')
def logs_page():
    """Live logs streaming page"""
    return render_template('logs.html')

@app.route('/api/logs/stream')
def stream_logs():
    """API endpoint to stream live logs"""
    from flask import Response
    import time
    import os
    
    def generate_logs():
        # Keep track of last read position for each log file
        log_files = {
            'logs/rl_bot_error.log': 0,
            'trading_bot.log': 0
        }
        
        while True:
            new_logs = []
            
            # Read new content from each log file
            for log_file, last_pos in log_files.items():
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            f.seek(last_pos)
                            new_content = f.read()
                            if new_content:
                                lines = new_content.strip().split('\n')
                                for line in lines:
                                    if line.strip():
                                        new_logs.append({
                                            'source': log_file,
                                            'content': line,
                                            'timestamp': time.time()
                                        })
                                log_files[log_file] = f.tell()
                    except Exception as e:
                        logger.error(f"Error reading {log_file}: {e}")
            
            # Send new logs if any
            if new_logs:
                for log_entry in new_logs:
                    yield f"data: {json.dumps(log_entry)}\n\n"
            
            time.sleep(1)  # Check for new logs every second
    
    return Response(generate_logs(), mimetype='text/plain')

@app.route('/api/logs/recent')
def get_recent_logs():
    """API endpoint to get recent logs"""
    lines = request.args.get('lines', 50, type=int)
    log_source = request.args.get('source', 'rl_bot', type=str)
    
    try:
        recent_logs = []
        
        # Determine which log files to read based on source
        if log_source == 'rl_bot':
            log_files = ['logs/rl_bot_error.log', 'logs/rl_bot_main.log']
        elif log_source == 'trading_bot':
            log_files = ['trading_bot.log']
        else:
            log_files = ['logs/rl_bot_error.log', 'trading_bot.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        file_lines = f.readlines()
                        # Get the last N lines
                        recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                        
                        for line in recent_lines:
                            line = line.strip()
                            if line:
                                recent_logs.append({
                                    'source': log_file,
                                    'content': line,
                                    'timestamp': time.time()
                                })
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
        
        # Sort by timestamp (most recent first)
        recent_logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'data': recent_logs[:lines]  # Limit to requested number of lines
        })
        
    except Exception as e:
        logger.error(f"Error getting recent logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bot-pause', methods=['POST'])
def toggle_bot_pause():
    """API endpoint to pause/resume the RL bot"""
    try:
        action = request.json.get('action', 'toggle')
        pause_file = 'bot_pause.flag'
        
        if action == 'pause' or (action == 'toggle' and not os.path.exists(pause_file)):
            # Create pause file
            with open(pause_file, 'w') as f:
                f.write(f"Paused at {datetime.now().isoformat()}\n")
            status = 'paused'
            logger.info("🛑 Bot paused via dashboard")
        else:
            # Remove pause file
            if os.path.exists(pause_file):
                os.remove(pause_file)
            status = 'running'
            logger.info("▶️ Bot resumed via dashboard")
        
        return jsonify({
            'success': True,
            'status': status,
            'message': f'Bot {status} successfully'
        })
        
    except Exception as e:
        logger.error(f"Error toggling bot pause: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bot-pause-status')
def get_bot_pause_status():
    """API endpoint to get current pause status"""
    try:
        pause_file = 'bot_pause.flag'
        is_paused = os.path.exists(pause_file)
        
        pause_info = {}
        if is_paused:
            try:
                with open(pause_file, 'r') as f:
                    pause_info['paused_at'] = f.read().strip()
            except:
                pause_info['paused_at'] = 'Unknown'
        
        return jsonify({
            'success': True,
            'data': {
                'is_paused': is_paused,
                'status': 'paused' if is_paused else 'running',
                **pause_info
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting pause status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rl-bot-status')
def get_rl_bot_status():
    """API endpoint to get real-time RL bot status and latest decisions"""
    try:
        import subprocess
        import re
        import os
        from datetime import datetime, timedelta
        
        # Check if RL bot is running
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            is_running = 'rl_bot_ready.py' in result.stdout
            
            # Get PID if running
            bot_pid = None
            if is_running:
                for line in result.stdout.split('\n'):
                    if 'rl_bot_ready.py' in line and 'grep' not in line:
                        parts = line.split()
                        if len(parts) > 1:
                            bot_pid = parts[1]
                        break
        except:
            is_running = False
            bot_pid = None
        
        # Get latest RL decision from the database
        db = get_database()
        latest_rl_decision = db.get_recent_rl_signals(limit=1)
        
        # Parse the latest RL bot log entries
        bot_status = {
            'running': is_running,
            'pid': bot_pid,
            'last_update': None,
            'current_signal': None,
            'rl_decision': latest_rl_decision[0] if latest_rl_decision else None,
            'position_info': None,
            'market_data': None,
            'next_update': None
        }
        
        # Read the RL bot logs
        log_files = ['trading_bot.log', 'logs/rl_bot_main.log', 'logs/rl_bot_error.log']
        latest_entries = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 50 lines to find recent RL decisions
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        latest_entries.extend(recent_lines)
                        logger.info(f"Read {len(recent_lines)} lines from {log_file}")
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
                    continue
        
        if latest_entries:
            # Parse the log entries for RL bot information
            for line in latest_entries:
                line = line.strip()
                
                # Extract timestamp
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    try:
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        # Only consider entries from last 60 minutes
                        if datetime.now() - log_time > timedelta(minutes=60):
                            continue
                    except:
                        continue
                
                # Parse position info
                if '📍 Position:' in line:
                    if 'No open position' in line:
                        bot_status['position_info'] = {'status': 'No position'}
                    else:
                        pos_match = re.search(r'📍 Position: (LONG|SHORT) ([0-9.]+)', line)
                        if pos_match:
                            bot_status['position_info'] = {
                                'side': pos_match.group(1),
                                'size': float(pos_match.group(2)),
                                'timestamp': timestamp_str
                            }
                
                # Parse PnL info
                if '💰 PnL:' in line:
                    pnl_match = re.search(r'💰 PnL: [🟢🔴] $([^)]+) \(([^)]+)\)', line)
                    if pnl_match and bot_status['position_info']:
                        bot_status['position_info']['pnl'] = pnl_match.group(1)
                        bot_status['position_info']['pnl_percentage'] = pnl_match.group(2)
                
                # Parse market data
                if '💹' in line and 'RSI:' in line and 'VWAP:' in line:
                    market_match = re.search(r'💹 ([^:]+): \$([^|]+) \| RSI: ([^|]+) \| VWAP: \$([^$]+)', line)
                    if market_match:
                        bot_status['market_data'] = {
                            'symbol': market_match.group(1),
                            'price': float(market_match.group(2)),
                            'rsi': float(market_match.group(3)),
                            'vwap': float(market_match.group(4)),
                            'timestamp': timestamp_str
                        }
                
                # Parse signal info
                if '🎯 Signal:' in line:
                    signal_match = re.search(r'🎯 Signal: [⚪🟢🔴] (\w+) \(Strength: (\d+)\)', line)
                    if signal_match:
                        bot_status['current_signal'] = {
                            'action': signal_match.group(1),
                            'strength': int(signal_match.group(2)),
                            'timestamp': timestamp_str
                        }
                
                # Parse next update time
                if '⏰ Next update in' in line:
                    bot_status['next_update'] = timestamp_str
                    bot_status['last_update'] = timestamp_str
        
        return jsonify({
            'success': True,
            'data': bot_status
        })
        
    except Exception as e:
        logger.error(f"Error getting RL bot status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)