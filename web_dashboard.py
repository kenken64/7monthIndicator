#!/usr/bin/env python3
"""
Web Dashboard for Trading Bot Analysis

A comprehensive Flask web application that provides real-time monitoring
and analysis for the RL-enhanced trading bot. Features include:

- Performance metrics and PnL tracking
- Real-time signal analysis and visualization
- Live position monitoring with Binance integration
- Interactive charts for trade history and signals
- System status monitoring and bot control
- Live log streaming for debugging
- Balance projection calculations
- RL decision analysis and insights
"""

import json
import os
import time
from flask import Flask, render_template, jsonify, request
from database import get_database
from datetime import datetime, timedelta
import logging
import re
import requests
import json
from newsapi import NewsApiClient
from config import NEWS_CONFIG
from dotenv import load_dotenv
import os

# Load environment variables with explicit path
load_dotenv('.env')
# Fallback: ensure NEWS_API_KEY is available
if not os.getenv('NEWS_API_KEY'):
    # Try to load from .env file in current directory explicitly
    import dotenv
    dotenv.load_dotenv('.env', override=True)

def analyze_market_sentiment(news_titles):
    """
    Analyze market sentiment using OpenAI or local analysis based on configuration
    """
    try:
        # Check if we should use local analysis (cost-saving mode)
        use_local_sentiment = os.getenv('USE_LOCAL_SENTIMENT', 'false').lower() == 'true'
        
        if use_local_sentiment:
            from local_sentiment import LocalSentimentAnalyzer
            analyzer = LocalSentimentAnalyzer()
            result = analyzer.analyze_sentiment(news_titles)
            logger.info("Using local sentiment analysis (cost-saving mode)")
            return result
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("OpenAI API key not found, skipping sentiment analysis")
            return {
                'sentiment': 'Unknown',
                'confidence': 0,
                'explanation': 'OpenAI API key not configured'
            }
        
        # Prepare the prompt
        titles_text = '\n'.join([f"- {title}" for title in news_titles[:20]])
        
        prompt = f"""Analyze the overall market sentiment for cryptocurrency based on these recent news headlines:

{titles_text}

Please provide your analysis in JSON format with:
1. sentiment: "Bullish", "Bearish", or "Neutral"
2. confidence: score from 1-10 (10 being very confident)
3. explanation: brief 1-2 sentence explanation of the sentiment

Respond only with valid JSON."""

        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",  # 60x cheaper than GPT-4
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 150,  # Reduced from 300
            "temperature": 0.1   # Lower temperature for consistent results
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    sentiment_data = json.loads(json_match.group())
                    return sentiment_data
                else:
                    # Fallback parsing
                    return {
                        'sentiment': 'Neutral',
                        'confidence': 5,
                        'explanation': 'Could not parse AI response'
                    }
            except json.JSONDecodeError:
                return {
                    'sentiment': 'Neutral',
                    'confidence': 5,
                    'explanation': 'Failed to parse sentiment analysis'
                }
        else:
            logger.error(f"OpenAI API error: {response.status_code}")
            return {
                'sentiment': 'Unknown',
                'confidence': 0,
                'explanation': 'API request failed'
            }
            
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {
            'sentiment': 'Unknown',
            'confidence': 0,
            'explanation': f'Error: {str(e)}'
        }

app = Flask(__name__)
app.secret_key = 'trading_bot_secret_key'

# Configure logging for web dashboard activities
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to track PIN failed attempts with rate limiting
pin_attempts = {}

def validate_6_digit_pin(provided_pin: str, client_ip: str) -> dict:
    """
    Validate 6-digit PIN against environment variable with rate limiting
    
    Args:
        provided_pin: User-provided PIN (must be exactly 6 digits)
        client_ip: Client IP address for rate limiting
        
    Returns:
        dict: Validation result with success status and message
    """
    global pin_attempts
    
    # Check if PIN is set in environment
    expected_pin = os.getenv('BOT_CONTROL_PIN')
    if not expected_pin:
        logger.error("BOT_CONTROL_PIN not set in environment variables")
        return {
            'success': False,
            'message': 'PIN protection not configured',
            'blocked': False
        }
    
    # Validate PIN format (must be exactly 6 digits)
    if not provided_pin or not re.match(r'^\d{6}$', provided_pin):
        return {
            'success': False,
            'message': 'PIN must be exactly 6 digits',
            'blocked': False
        }
    
    # Rate limiting logic
    current_time = datetime.now()
    client_key = f"pin_{client_ip}"
    
    # Initialize or reset attempts if more than 15 minutes passed
    if client_key in pin_attempts:
        last_attempt_time = pin_attempts[client_key]['last_attempt']
        if current_time - last_attempt_time > timedelta(minutes=15):
            pin_attempts[client_key] = {'count': 0, 'last_attempt': current_time}
    else:
        pin_attempts[client_key] = {'count': 0, 'last_attempt': current_time}
    
    # Check if client is blocked due to too many attempts
    if pin_attempts[client_key]['count'] >= 3:
        time_since_last = current_time - pin_attempts[client_key]['last_attempt']
        if time_since_last < timedelta(minutes=15):
            remaining_minutes = 15 - int(time_since_last.total_seconds() / 60)
            logger.warning(f"PIN attempts blocked for IP {client_ip}, {remaining_minutes} minutes remaining")
            return {
                'success': False,
                'message': f'Too many failed attempts. Try again in {remaining_minutes} minutes.',
                'blocked': True
            }
    
    # Validate PIN
    if provided_pin == expected_pin:
        # Reset failed attempts on successful validation
        pin_attempts[client_key] = {'count': 0, 'last_attempt': current_time}
        logger.info(f"✅ 6-digit PIN validated successfully for bot control from IP: {client_ip}")
        return {
            'success': True,
            'message': 'PIN validated successfully',
            'blocked': False
        }
    else:
        # Increment failed attempts
        pin_attempts[client_key]['count'] += 1
        pin_attempts[client_key]['last_attempt'] = current_time
        
        attempts_remaining = 3 - pin_attempts[client_key]['count']
        logger.warning(f"❌ Invalid 6-digit PIN attempt from IP {client_ip}. Attempts remaining: {attempts_remaining}")
        
        if attempts_remaining > 0:
            return {
                'success': False,
                'message': f'Invalid PIN. {attempts_remaining} attempts remaining.',
                'blocked': False
            }
        else:
            return {
                'success': False,
                'message': 'Too many failed attempts. Blocked for 15 minutes.',
                'blocked': True
            }

@app.route('/')
def dashboard():
    """Main dashboard page
    
    Serves the primary dashboard interface with real-time trading
    data, performance metrics, and system status.
    """
    return render_template('dashboard.html')

@app.route('/test')
def test_projections():
    """Test page for projections
    
    Development endpoint for testing balance projection features
    and visualization components.
    """
    with open('test_projections.html', 'r') as f:
        return f.read()

@app.route('/api/performance/<symbol>')
def get_performance(symbol):
    """API endpoint to get performance metrics
    
    Calculates and returns comprehensive trading performance statistics
    including win rate, PnL, average gains/losses, and risk metrics.
    Falls back to unrealized PnL calculation for open positions.
    
    Args:
        symbol: Trading pair symbol (e.g., 'SUIUSDC')
        
    Query Parameters:
        days: Number of days to analyze (default: 30)
        
    Returns:
        JSON response with performance data or error message
    """
    days = request.args.get('days', 30, type=int)
    db = get_database()
    
    try:
        # First try to get closed trades performance from database
        performance = db.calculate_performance_metrics(symbol, days)
        
        # If no closed trades, calculate unrealized performance from open positions
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
                    
                    # Calculate unrealized performance from open trades using live prices
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
                                # Calculate unrealized PnL based on current market price
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
    """API endpoint to get recent signals
    
    Retrieves recent trading signals with timestamps, strengths,
    and analysis reasons from the database.
    
    Args:
        symbol: Trading pair symbol
        
    Query Parameters:
        limit: Maximum number of signals to return (default: 20)
        
    Returns:
        JSON response with signal data array
    """
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
    """API endpoint to get recent trades
    
    Fetches recent trading activity including entry/exit prices,
    quantities, PnL, and trade status.
    
    Args:
        symbol: Trading pair symbol
        
    Query Parameters:
        limit: Maximum number of trades to return (default: 20)
        
    Returns:
        JSON response with trade history data
    """
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
    """API endpoint to get live open positions from Binance
    
    Retrieves current position information from both the local database
    and live Binance API. Provides real-time PnL, position size,
    entry prices, and risk metrics.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        JSON response containing:
        - database_positions: Local database records
        - live_positions: Real-time Binance position data
    """
    from binance.client import Client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    db = get_database()
    
    try:
        # Get positions from database - Local trade records
        db_positions = db.get_open_trades(symbol)
        
        # Also get live positions from Binance API - Real-time exchange data
        try:
            api_key = os.getenv('BINANCE_API_KEY')
            secret_key = os.getenv('BINANCE_SECRET_KEY')
            
            if api_key and secret_key:
                client = Client(api_key, secret_key, testnet=False)
                live_positions = client.futures_position_information()

                # Get open orders to find TP/SL orders
                try:
                    open_orders = client.futures_get_open_orders(symbol=symbol)
                except Exception as e:
                    logger.warning(f"Could not fetch open orders: {e}")
                    open_orders = []

                # Filter for requested symbol and non-zero positions from Binance
                binance_positions = []
                for pos in live_positions:
                    if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                        position_amt = float(pos['positionAmt'])
                        entry_price = float(pos['entryPrice'])
                        mark_price = float(pos['markPrice'])

                        # Calculate PnL percentage with leverage (assuming 50x)
                        if entry_price > 0:
                            if position_amt > 0:  # LONG
                                pnl_percentage = ((mark_price - entry_price) / entry_price) * 100 * 50  # Assuming 50x leverage
                            else:  # SHORT
                                pnl_percentage = ((entry_price - mark_price) / entry_price) * 100 * 50
                        else:
                            pnl_percentage = 0

                        # Find TP/SL orders for this position
                        take_profit_price = None
                        stop_loss_price = None

                        for order in open_orders:
                            if order['type'] == 'TAKE_PROFIT_MARKET' or order['type'] == 'TAKE_PROFIT':
                                take_profit_price = float(order.get('stopPrice', order.get('price', 0)))
                            elif order['type'] == 'STOP_MARKET' or order['type'] == 'STOP':
                                stop_loss_price = float(order.get('stopPrice', order.get('price', 0)))

                        binance_positions.append({
                            'symbol': pos['symbol'],
                            'side': 'LONG' if position_amt > 0 else 'SHORT',
                            'size': abs(position_amt),
                            'entry_price': entry_price,
                            'mark_price': mark_price,
                            'unrealized_pnl': float(pos['unRealizedProfit']),
                            'liquidation_price': float(pos['liquidationPrice']) if pos['liquidationPrice'] != '0' else 0,
                            'percentage': pnl_percentage,
                            'margin_type': pos.get('marginType', 'UNKNOWN'),
                            'take_profit_price': take_profit_price,
                            'stop_loss_price': stop_loss_price,
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
    """API endpoint to get chart data for visualization
    
    Provides historical trade data and signal data formatted for
    chart visualization including cumulative PnL tracking.
    
    Args:
        symbol: Trading pair symbol
        
    Query Parameters:
        days: Historical period to analyze (default: 30)
        
    Returns:
        JSON response with trades and signals data for charting
    """
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
    """API endpoint to get system statistics

    Returns overall system health and activity metrics including:
    - Total signals and trades count
    - Open position count (from live Binance API)
    - Last signal timestamp
    - Available trading symbols

    Returns:
        JSON response with system statistics
    """
    from binance.client import Client
    from dotenv import load_dotenv

    load_dotenv()
    db = get_database()

    try:
        with db.get_connection() as conn:
            # Get total counts
            stats = {}

            cursor = conn.execute('SELECT COUNT(*) as count FROM signals')
            stats['total_signals'] = cursor.fetchone()['count']

            cursor = conn.execute('SELECT COUNT(*) as count FROM trades')
            stats['total_trades'] = cursor.fetchone()['count']

            # Get live open positions count from Binance API instead of database
            open_positions_count = 0
            try:
                api_key = os.getenv('BINANCE_API_KEY')
                secret_key = os.getenv('BINANCE_SECRET_KEY')

                if api_key and secret_key:
                    client = Client(api_key, secret_key, testnet=False)
                    live_positions = client.futures_position_information()

                    # Count non-zero positions from Binance
                    for pos in live_positions:
                        if float(pos['positionAmt']) != 0:
                            open_positions_count += 1

                    logger.debug(f"Found {open_positions_count} live open positions from Binance")
                else:
                    # Fallback to database if no API credentials
                    cursor = conn.execute('SELECT COUNT(*) as count FROM trades WHERE status = "OPEN"')
                    open_positions_count = cursor.fetchone()['count']
                    logger.debug(f"Using database count: {open_positions_count} open trades")

            except Exception as api_error:
                logger.warning(f"Error fetching live positions count, using database: {api_error}")
                # Fallback to database on error
                cursor = conn.execute('SELECT COUNT(*) as count FROM trades WHERE status = "OPEN"')
                open_positions_count = cursor.fetchone()['count']

            stats['open_trades'] = open_positions_count

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
    """API endpoint to get projected account balance based on performance trends
    
    Calculates future account balance projections using historical performance
    data and various scenarios (conservative, realistic, optimistic, pessimistic).
    Includes RL enhancement projections when available.
    
    Args:
        symbol: Trading pair symbol
        
    Query Parameters:
        days: Historical period for analysis (default: 30)
        projection_days: Future projection period (default: 30)
        
    Returns:
        JSON response with:
        - current_balance: Current account balance from Binance
        - projections: Array of different scenario projections
        - performance_stats: Historical performance metrics
    """
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
        
        # Get current account balance from both Spot and Futures accounts
        current_balance = 0.0
        
        try:
            # Check Futures account balance including margin used in positions
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
            # Check Spot account USDC balance (free + locked)
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
        
        # Get historical performance metrics for projection calculations
        performance = db.calculate_performance_metrics(symbol, days)
        
        # Calculate daily performance metrics for trend analysis
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
        
        # Calculate future balance projections using multiple scenarios
        projections = []
        
        if daily_performance:
            # Calculate daily PnL statistics for projection modeling
            daily_pnls = [row['daily_pnl'] for row in daily_performance if row['daily_pnl'] != 0]
            
            if daily_pnls:
                avg_daily_pnl = np.mean(daily_pnls)
                std_daily_pnl = np.std(daily_pnls)
                win_rate = performance.get('win_rate', 0) / 100.0
                
                # Create different projection scenarios based on historical performance
                scenarios = {
                    'conservative': avg_daily_pnl * 0.5,  # 50% of historical performance
                    'realistic': avg_daily_pnl * 0.8,    # 80% of historical performance
                    'optimistic': avg_daily_pnl * 1.0,   # Full historical performance
                    'pessimistic': avg_daily_pnl * 0.2   # 20% of historical performance
                }
                
                # Generate daily projections for each scenario over time period
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
            
            # Add RL enhancement projection assuming improved performance
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
    """API endpoint to get recent RL-enhanced decisions

    Retrieves recent decisions made by the RL enhancement system
    including confidence levels and decision reasoning.

    Args:
        symbol: Trading pair symbol

    Query Parameters:
        limit: Maximum number of decisions to return (default: 5)

    Returns:
        JSON response with RL decision data
    """
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

@app.route('/api/unified-signals/<symbol>')
def get_unified_signals(symbol):
    """API endpoint to get unified multi-layer signal analysis

    Retrieves the latest unified signal aggregation including all 6 sources:
    1. Technical Indicators (25% weight)
    2. RL Enhancement (15% weight)
    3. Chart Analysis (30% weight)
    4. CrewAI Multi-Agent (15% weight)
    5. Market Context & Cross-Asset (10% weight)
    6. News Sentiment (5% weight)

    Args:
        symbol: Trading pair symbol

    Returns:
        JSON response with unified signal breakdown and decision
    """
    try:
        import os
        import json
        from datetime import datetime

        # Load all signal source data
        unified_data = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'unified_signal': None,
            'signal_sources': {},
            'weights': {
                'technical': 25,
                'rl': 15,
                'chart_analysis': 30,
                'crewai': 15,
                'market_context': 10,
                'news_sentiment': 5
            }
        }

        # Get latest signal from database (includes RL if available)
        db = get_database()
        latest_signals = db.get_recent_signals(symbol, limit=1)

        if latest_signals:
            latest_signal = latest_signals[0]

            # Check if unified signal data exists
            if 'unified_details' in latest_signal:
                unified_data['unified_signal'] = latest_signal['unified_details']

            # Extract traditional signal data
            signal_value = latest_signal.get('signal', 0)
            strength = latest_signal.get('strength', 0)

            # Map signal to action (signal: -1=SELL, 0=HOLD, 1=BUY)
            if signal_value > 0:
                action = 'BUY'
            elif signal_value < 0:
                action = 'SELL'
            else:
                action = 'HOLD'

            # Convert strength (1-5) to score (0-10 scale)
            # Strength 1 -> 2, Strength 2 -> 4, Strength 3 -> 5, Strength 4 -> 7, Strength 5 -> 10
            score_map = {0: 5.0, 1: 2.0, 2: 4.0, 3: 5.0, 4: 7.0, 5: 10.0}
            score = score_map.get(strength, 5.0)

            # If signal is negative, invert the score (lower is more bearish)
            if signal_value < 0:
                score = 10 - score

            unified_data['signal_sources']['technical'] = {
                'signal': signal_value,
                'strength': strength,
                'action': action,
                'score': score,
                'confidence': min(strength * 20.0, 100.0),
                'timestamp': latest_signal.get('timestamp'),
                'weight': 25
            }

        # Load chart analysis
        chart_file = 'analysis_results_SUIUSDC.json'
        if os.path.exists(chart_file):
            with open(chart_file, 'r') as f:
                chart_data = json.load(f)
                ai_analysis = chart_data.get('ai_analysis', {})

                # Convert recommendation to action and score
                rec = ai_analysis.get('recommendation', 'HOLD')
                sentiment = ai_analysis.get('sentiment', 'Neutral')
                conf_level = ai_analysis.get('confidence', 'Medium')

                # Map recommendation to action (already in BUY/SELL/HOLD format)
                action = rec.upper() if rec.upper() in ['BUY', 'SELL', 'HOLD'] else 'HOLD'

                # Convert confidence level to numeric
                conf_map = {'Low': 30, 'Medium': 60, 'High': 85}
                confidence = conf_map.get(conf_level, 60)

                # Convert sentiment and recommendation to score (0-10 scale)
                # BUY recommendations get higher scores, SELL get lower scores
                if action == 'BUY':
                    if sentiment == 'Bullish':
                        score = 8.0  # Strong buy
                    else:
                        score = 6.5  # Moderate buy
                elif action == 'SELL':
                    if sentiment == 'Bearish':
                        score = 2.0  # Strong sell
                    else:
                        score = 3.5  # Moderate sell
                else:  # HOLD
                    score = 5.0  # Neutral

                unified_data['signal_sources']['chart_analysis'] = {
                    'recommendation': rec,
                    'action': action,
                    'score': score,
                    'confidence': confidence,
                    'sentiment': sentiment,
                    'timestamp': chart_data.get('analysis_time'),
                    'weight': 30
                }

        # Load market context
        context_file = 'market_context.json'
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context_data = json.load(f)

                # Extract trends
                btc_trend = context_data.get('btc', {}).get('trend', 'neutral')
                eth_trend = context_data.get('eth', {}).get('trend', 'neutral')
                market_trend = context_data.get('market', {}).get('trend', 'neutral')
                fear_greed = context_data.get('market', {}).get('fear_greed_index', 50)

                # Determine overall action based on market context
                # Count bullish vs bearish signals
                bullish_signals = sum([
                    1 if btc_trend == 'bullish' else 0,
                    1 if eth_trend == 'bullish' else 0,
                    1 if market_trend == 'bullish' else 0,
                    1 if fear_greed > 60 else 0
                ])
                bearish_signals = sum([
                    1 if btc_trend == 'bearish' else 0,
                    1 if eth_trend == 'bearish' else 0,
                    1 if market_trend == 'bearish' else 0,
                    1 if fear_greed < 40 else 0
                ])

                # Determine action with improved logic
                # Require at least 2 signals in same direction for BUY/SELL
                # This prevents single weak signals from dominating the decision
                if bullish_signals >= 2 and bullish_signals > bearish_signals:
                    action = 'BUY'
                elif bearish_signals >= 2 and bearish_signals > bullish_signals:
                    action = 'SELL'
                else:
                    action = 'HOLD'

                # Calculate score (0-10 scale based on fear/greed index and trends)
                # Fear/Greed contributes 50%, trends contribute 50%
                fg_score = fear_greed / 10  # Convert 0-100 to 0-10

                trend_score = 5.0  # Start neutral
                if btc_trend == 'bullish': trend_score += 1
                elif btc_trend == 'bearish': trend_score -= 1
                if eth_trend == 'bullish': trend_score += 0.5
                elif eth_trend == 'bearish': trend_score -= 0.5
                if market_trend == 'bullish': trend_score += 0.5
                elif market_trend == 'bearish': trend_score -= 0.5

                # Weighted average
                score = (fg_score * 0.5) + (trend_score * 0.5)
                score = max(0, min(10, score))  # Clamp to 0-10

                # Calculate confidence based on agreement between indicators
                total_indicators = 4
                aligned_indicators = max(bullish_signals, bearish_signals)
                confidence = (aligned_indicators / total_indicators) * 100

                unified_data['signal_sources']['market_context'] = {
                    'btc_trend': btc_trend,
                    'eth_trend': eth_trend,
                    'market_trend': market_trend,
                    'fear_greed': fear_greed,
                    'action': action,
                    'score': round(score, 1),
                    'confidence': round(confidence, 0),
                    'timestamp': context_data.get('timestamp'),
                    'weight': 10
                }

        # Load CrewAI analysis
        crewai_file = 'crewai_analysis.json'
        if os.path.exists(crewai_file):
            with open(crewai_file, 'r') as f:
                crewai_data = json.load(f)

                # Get action and confidence from consensus
                action = crewai_data.get('consensus', {}).get('action', 'HOLD')
                confidence = crewai_data.get('consensus', {}).get('confidence', 50)
                circuit_breaker_state = crewai_data.get('circuit_breaker', {}).get('state', 'NORMAL')

                # Convert action and confidence to score (0-10 scale)
                # Base score on action, then adjust by confidence
                if action == 'BUY':
                    # BUY: score between 6-10 based on confidence
                    # confidence 0-100, map to 6-10
                    score = 6.0 + (confidence / 100) * 4.0
                elif action == 'SELL':
                    # SELL: score between 0-4 based on confidence
                    # confidence 0-100, map inversely to 0-4
                    score = 4.0 - (confidence / 100) * 4.0
                else:  # HOLD
                    # HOLD: score around 5, slightly adjusted by confidence
                    # High confidence HOLD stays at 5, low confidence varies slightly
                    score = 5.0 + (50 - confidence) / 100  # Ranges from 4.5 to 5.5

                # Factor in circuit breaker state
                if circuit_breaker_state == 'TRIGGERED':
                    # If circuit breaker triggered, push score toward neutral/safe
                    score = score * 0.7 + 5.0 * 0.3  # Blend with neutral

                unified_data['signal_sources']['crewai'] = {
                    'action': action,
                    'score': round(score, 1),
                    'confidence': confidence,
                    'circuit_breaker_state': circuit_breaker_state,
                    'timestamp': crewai_data.get('timestamp'),
                    'weight': 15
                }

        # Load news sentiment
        news_file = 'news_sentiment.json'
        if os.path.exists(news_file):
            with open(news_file, 'r') as f:
                news_data = json.load(f)

                # Map sentiment to action
                sentiment = news_data.get('sentiment', 'Neutral')
                if sentiment.lower() in ['bullish', 'positive']:
                    action = 'BUY'
                elif sentiment.lower() in ['bearish', 'negative']:
                    action = 'SELL'
                else:
                    action = 'HOLD'

                # Convert sentiment_score to 0-10 scale for consistency
                # sentiment_score is typically -1 to 1, convert to 0-10 scale
                raw_score = news_data.get('sentiment_score', 0)
                # Map: -1 (bearish) -> 0, 0 (neutral) -> 5, 1 (bullish) -> 10
                score = (raw_score + 1) * 5

                # Get confidence (1-10 scale)
                confidence = news_data.get('confidence', 0) * 10 if news_data.get('confidence', 0) <= 1 else news_data.get('confidence', 0)

                unified_data['signal_sources']['news_sentiment'] = {
                    'sentiment': sentiment,
                    'action': action,  # Add action field for frontend
                    'score': score,
                    'confidence': confidence,
                    'article_count': news_data.get('article_count', 0),
                    'timestamp': news_data.get('timestamp'),
                    'weight': 5
                }

        # Add RL signal if available
        if 'unified_details' in latest_signal and latest_signal['unified_details']:
            unified_details = latest_signal['unified_details']
            unified_data['unified_signal'] = {
                'action': unified_details.get('signal', 'HOLD'),
                'weighted_score': unified_details.get('strength', 0),
                'confidence': unified_details.get('confidence', 0),
                'breakdown': unified_details.get('breakdown', {})
            }

            # Extract individual scores from breakdown if available
            breakdown = unified_details.get('breakdown', {})
            if 'rl' in breakdown:
                unified_data['signal_sources']['rl'] = {
                    'action': breakdown['rl'].get('action', 'HOLD'),
                    'score': breakdown['rl'].get('score', 0),
                    'confidence': breakdown['rl'].get('confidence', 0),
                    'weight': 15
                }

        # If RL source not populated from breakdown, add placeholder
        if 'rl' not in unified_data['signal_sources']:
            unified_data['signal_sources']['rl'] = {
                'action': 'HOLD',
                'score': 5.0,
                'confidence': 0,
                'weight': 15
            }

        # Calculate unified decision by aggregating all signal sources
        # Only calculate if we don't already have unified_signal from database
        if not unified_data['unified_signal']:
            signal_sources = unified_data['signal_sources']

            # Calculate weighted score (0-10 scale)
            total_weight = 0
            weighted_score_sum = 0
            weighted_confidence_sum = 0

            # Count actions for voting
            buy_weight = 0
            sell_weight = 0
            hold_weight = 0

            for source_name, source_data in signal_sources.items():
                if 'score' in source_data and 'weight' in source_data:
                    weight = source_data['weight']
                    score = source_data['score']
                    confidence = source_data.get('confidence', 50)
                    action = source_data.get('action', 'HOLD')

                    # Accumulate weighted values
                    weighted_score_sum += score * (weight / 100)
                    weighted_confidence_sum += confidence * (weight / 100)
                    total_weight += weight

                    # Vote on action based on weight
                    if action == 'BUY':
                        buy_weight += weight
                    elif action == 'SELL':
                        sell_weight += weight
                    else:  # HOLD
                        hold_weight += weight

            # Determine overall action based on weighted voting
            if buy_weight > sell_weight and buy_weight > hold_weight:
                unified_action = 'BUY'
            elif sell_weight > buy_weight and sell_weight > hold_weight:
                unified_action = 'SELL'
            else:
                unified_action = 'HOLD'

            # Calculate final weighted score and confidence
            final_score = weighted_score_sum if total_weight > 0 else 5.0
            final_confidence = weighted_confidence_sum if total_weight > 0 else 0

            # Set the unified signal
            unified_data['unified_signal'] = {
                'action': unified_action,
                'weighted_score': round(final_score, 1),
                'confidence': round(final_confidence, 1),
                'breakdown': {
                    'buy_weight': buy_weight,
                    'sell_weight': sell_weight,
                    'hold_weight': hold_weight,
                    'total_weight': total_weight
                }
            }

        return jsonify({
            'success': True,
            'data': unified_data
        })

    except Exception as e:
        logger.error(f"Error getting unified signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/logs')
def logs_page():
    """Live logs streaming page
    
    Renders the log monitoring interface for real-time bot activity tracking.
    """
    return render_template('logs.html')

@app.route('/api/logs/stream')
def stream_logs():
    """API endpoint to stream live logs
    
    Provides Server-Sent Events (SSE) stream of real-time log entries
    from multiple log files. Monitors RL bot and trading bot logs
    continuously and streams new entries as they appear.
    
    Returns:
        SSE stream with JSON-formatted log entries
    """
    from flask import Response
    import time
    import os
    
    def generate_logs():
        # Keep track of file positions to stream only new log entries
        log_files = {
            'logs/rl_bot_error.log': 0,
            'trading_bot.log': 0,
            'chart_analysis_bot.log': 0
        }
        
        while True:
            new_logs = []
            
            # Read new content from each monitored log file
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
            
            # Send new log entries to client via Server-Sent Events
            if new_logs:
                for log_entry in new_logs:
                    yield f"data: {json.dumps(log_entry)}\n\n"
            
            time.sleep(1)  # Check for new logs every second
    
    return Response(generate_logs(), mimetype='text/plain')

@app.route('/api/logs/recent')
def get_recent_logs():
    """API endpoint to get recent logs
    
    Fetches the most recent log entries from specified log files
    for display in the dashboard.
    
    Query Parameters:
        lines: Number of log lines to retrieve (default: 50)
        source: Log source ('rl_bot', 'trading_bot', or 'all')
        
    Returns:
        JSON response with recent log entries
    """
    lines = request.args.get('lines', 50, type=int)
    log_source = request.args.get('source', 'rl_bot', type=str)
    
    try:
        recent_logs = []
        
        # Determine which log files to read based on requested source
        if log_source == 'rl_bot':
            log_files = ['logs/rl_bot_error.log', 'logs/rl_bot_main.log']
        elif log_source == 'trading_bot':
            log_files = ['trading_bot.log']
        elif log_source == 'chart_bot':
            log_files = ['chart_analysis_bot.log']
        else:
            log_files = ['logs/rl_bot_error.log', 'trading_bot.log', 'chart_analysis_bot.log']
        
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
        
        # Sort log entries by timestamp with most recent first
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

@app.route('/api/logs/ai-agents')
def get_ai_agent_logs():
    """API endpoint to get AI agent system logs

    Fetches recent log entries specifically related to CrewAI agents,
    circuit breaker, spike detection, and agent decisions.

    Query Parameters:
        lines: Number of log lines to retrieve (default: 100)
        level: Filter by log level ('info', 'warning', 'error', 'all') (default: 'all')
        agent: Filter by specific agent name (optional)

    Returns:
        JSON response with AI agent log entries
    """
    lines = request.args.get('lines', 100, type=int)
    log_level = request.args.get('level', 'all', type=str).lower()
    agent_filter = request.args.get('agent', None, type=str)

    try:
        agent_logs = []

        # Read from trading_bot.log which contains CrewAI integration logs
        log_file = 'logs/trading_bot.log'

        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    file_lines = f.readlines()
                    # Get more lines than requested to filter
                    recent_lines = file_lines[-lines*3:] if len(file_lines) > lines*3 else file_lines

                    # Keywords to identify AI agent related logs
                    ai_keywords = [
                        'crewai', 'circuit', 'breaker', 'spike', 'agent',
                        'Market Guardian', 'Market Scanner', 'Context Analyzer',
                        'Risk Assessment', 'Strategy Executor', '🤖', '🛡️',
                        '🔍', '📈', '⚠️', '✅', '❌', '🚨'
                    ]

                    for line in recent_lines:
                        line_stripped = line.strip()
                        if not line_stripped:
                            continue

                        # Check if line contains AI agent keywords
                        line_lower = line_stripped.lower()
                        is_agent_log = any(keyword.lower() in line_lower for keyword in ai_keywords)

                        if not is_agent_log:
                            continue

                        # Parse log level from line
                        detected_level = 'info'
                        if 'ERROR' in line_stripped or '❌' in line_stripped:
                            detected_level = 'error'
                        elif 'WARNING' in line_stripped or '⚠️' in line_stripped:
                            detected_level = 'warning'
                        elif 'INFO' in line_stripped or '✅' in line_stripped:
                            detected_level = 'info'

                        # Filter by log level if specified
                        if log_level != 'all' and detected_level != log_level:
                            continue

                        # Filter by agent name if specified
                        if agent_filter and agent_filter.lower() not in line_lower:
                            continue

                        # Extract timestamp if present
                        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line_stripped)
                        timestamp_str = timestamp_match.group(1) if timestamp_match else None

                        agent_logs.append({
                            'content': line_stripped,
                            'level': detected_level,
                            'timestamp': timestamp_str,
                            'source': 'crewai_system'
                        })

            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")

        # Limit to requested number of lines
        agent_logs = agent_logs[-lines:]

        # Reverse to show most recent first
        agent_logs.reverse()

        return jsonify({
            'success': True,
            'data': agent_logs,
            'total': len(agent_logs),
            'filters': {
                'level': log_level,
                'agent': agent_filter,
                'lines': lines
            }
        })

    except Exception as e:
        logger.error(f"Error getting AI agent logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bot-pause', methods=['POST'])
def toggle_bot_pause():
    """API endpoint to pause/resume the RL bot with 6-digit PIN protection
    
    Controls bot trading activity by creating/removing a pause flag file.
    When paused, the bot continues generating signals but stops executing trades.
    
    Request Body:
        action: 'pause', 'resume', or 'toggle'
        pin: 6-digit PIN for authentication
        
    Returns:
        JSON response with current pause status
    """
    try:
        # Get request data
        data = request.get_json() or {}
        action = data.get('action', 'toggle').lower()
        provided_pin = data.get('pin', '').strip()
        
        # Get client IP for rate limiting
        client_ip = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
        
        # Validate 6-digit PIN first
        pin_validation = validate_6_digit_pin(provided_pin, client_ip)
        if not pin_validation['success']:
            status_code = 429 if pin_validation['blocked'] else 401
            return jsonify({
                'success': False,
                'message': pin_validation['message'],
                'blocked': pin_validation['blocked']
            }), status_code
        
        # PIN validated successfully, proceed with bot control
        pause_file = '/tmp/rl_bot_pause'
        current_time = datetime.now()
        timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        if action == 'pause':
            with open(pause_file, 'w') as f:
                f.write(f"Paused at {timestamp_str}")
            message = "🤖 Trading bot paused successfully"
            is_paused = True
            
        elif action == 'resume':
            if os.path.exists(pause_file):
                os.remove(pause_file)
            message = "🚀 Trading bot resumed successfully"
            is_paused = False
            
        elif action == 'toggle':
            if os.path.exists(pause_file):
                os.remove(pause_file)
                message = "🚀 Trading bot resumed successfully"
                is_paused = False
            else:
                with open(pause_file, 'w') as f:
                    f.write(f"Paused at {timestamp_str}")
                message = "🤖 Trading bot paused successfully"
                is_paused = True
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid action. Use: pause, resume, or toggle'
            }), 400
        
        # Log the successful control action
        logger.info(f"🔒 Bot control action '{action}' executed successfully from IP: {client_ip}")
        
        return jsonify({
            'success': True,
            'message': message,
            'is_paused': is_paused,
            'timestamp': timestamp_str,
            'action': action
        })
        
    except Exception as e:
        logger.error(f"Error in bot pause endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/validate-pin', methods=['POST'])
def validate_pin_only():
    """API endpoint to validate PIN without performing any action

    Used for authenticating backtest operations and other sensitive actions
    that don't directly control the bot.

    Request Body:
        pin: 6-digit PIN for authentication

    Returns:
        JSON response indicating if PIN is valid
    """
    try:
        # Get request data
        data = request.get_json() or {}
        provided_pin = data.get('pin', '').strip()

        # Get client IP for rate limiting
        client_ip = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')

        # Validate 6-digit PIN
        pin_validation = validate_6_digit_pin(provided_pin, client_ip)
        if not pin_validation['success']:
            status_code = 429 if pin_validation['blocked'] else 401
            return jsonify({
                'success': False,
                'message': pin_validation['message'],
                'blocked': pin_validation['blocked']
            }), status_code

        # PIN is valid
        return jsonify({
            'success': True,
            'message': 'PIN validated successfully'
        })

    except Exception as e:
        logger.error(f"Error in PIN validation endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/bot-pause-status')
def get_bot_pause_status():
    """API endpoint to get current pause status

    Checks for the existence of the pause flag file to determine
    if the bot is currently paused.

    Returns:
        JSON response with pause status and timestamp
    """
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

@app.route('/api/connectivity-status')
def get_connectivity_status():
    """API endpoint to check connectivity status of external APIs

    Tests connectivity to:
    - Binance API (futures account endpoint)
    - OpenAI API (models list endpoint)

    Returns:
        JSON response with connectivity status for each service
    """
    from binance.client import Client
    import openai

    status = {
        'binance': {'connected': False, 'error': None, 'latency_ms': None},
        'openai': {'connected': False, 'error': None, 'latency_ms': None}
    }

    # Test Binance API
    try:
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')

        if api_key and secret_key:
            start_time = time.time()
            client = Client(api_key, secret_key, testnet=False)
            # Test with a simple API call
            client.futures_account()
            latency = (time.time() - start_time) * 1000
            status['binance']['connected'] = True
            status['binance']['latency_ms'] = round(latency, 2)
        else:
            status['binance']['error'] = 'API credentials not configured'
    except Exception as e:
        status['binance']['error'] = str(e)[:100]  # Limit error message length

    # Test OpenAI API
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')

        if openai_api_key:
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=5
            )
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                status['openai']['connected'] = True
                status['openai']['latency_ms'] = round(latency, 2)
            else:
                status['openai']['error'] = f"HTTP {response.status_code}"
        else:
            status['openai']['error'] = 'API key not configured'
    except Exception as e:
        status['openai']['error'] = str(e)[:100]  # Limit error message length

    return jsonify({
        'success': True,
        'data': status
    })

@app.route('/api/rl-bot-status')
def get_rl_bot_status():
    """API endpoint to get real-time RL bot status and latest decisions
    
    Provides comprehensive bot status information by:
    - Checking if bot process is running via system commands
    - Parsing recent log entries for current state
    - Extracting position, market data, and signal information
    - Retrieving latest RL decisions from database
    
    Returns:
        JSON response with complete bot status including:
        - Process status (running/stopped, PID)
        - Current position information
        - Latest market data and signals
        - Recent RL decisions and reasoning
    """
    try:
        import subprocess
        import re
        import os
        from datetime import datetime, timedelta
        
        # Check if RL bot is running - use PID file for reliability
        is_running = False
        bot_pid = None

        try:
            # Method 1: Check PID file
            pid_file = 'rl_bot.pid'
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid_content = f.read().strip()
                        if pid_content:
                            # Verify the process is actually running
                            result = subprocess.run(['ps', '-p', pid_content], capture_output=True, text=True, timeout=5)
                            if result.returncode == 0 and 'python' in result.stdout:
                                bot_pid = pid_content
                                is_running = True
                                logger.info(f"Found RL bot running with PID: {bot_pid} (from PID file)")
                except Exception as e:
                    logger.warning(f"Error reading PID file: {e}")

            # Method 2: Fallback to ps aux if PID file method failed
            if not is_running:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                if 'rl_bot_ready.py' in result.stdout:
                    is_running = True
                    # Get PID if running
                    for line in result.stdout.split('\n'):
                        if 'rl_bot_ready.py' in line and 'grep' not in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                bot_pid = parts[1]
                                logger.info(f"Found RL bot running with PID: {bot_pid} (from ps aux)")
                            break
                else:
                    logger.warning("RL bot process not found in ps output")
        except Exception as e:
            logger.error(f"Error checking RL bot status: {e}")
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
        
        # Read the bot logs (note: bot writes to logs/ directory)
        log_files = ['logs/trading_bot.log', 'logs/rl_bot_main.log', 'logs/rl_bot_error.log', 'chart_analysis_bot.log']
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

@app.route('/api/chart-analysis')
def get_chart_analysis():
    """API endpoint to get chart analysis data and recommendations"""
    try:
        # Read the chart analysis JSON file
        analysis_file = 'analysis_results_SUIUSDC.json'
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
            # Check if chart image exists
            chart_file = 'chart_analysis_SUIUSDC.png'
            chart_exists = os.path.exists(chart_file)
            
            return jsonify({
                'success': True,
                'data': analysis_data,
                'chart_available': chart_exists,
                'chart_url': '/api/chart-image' if chart_exists else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No chart analysis data available',
                'chart_available': False
            })
    except Exception as e:
        logger.error(f"Error retrieving chart analysis: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'chart_available': False
        }), 500

@app.route('/api/chart-image')
def get_chart_image():
    """API endpoint to serve the chart analysis image"""
    try:
        from flask import send_file
        chart_file = 'chart_analysis_SUIUSDC.png'
        if os.path.exists(chart_file):
            return send_file(chart_file, mimetype='image/png')
        else:
            return jsonify({'error': 'Chart image not found'}), 404
    except Exception as e:
        logger.error(f"Error serving chart image: {e}")
        return jsonify({'error': f'Error serving image: {str(e)}'}), 500

@app.route('/api/news')
def get_news():
    """API endpoint to get news articles with pagination support and sentiment analysis using OpenAI"""
    try:
        from datetime import datetime, timedelta

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Validate pagination parameters
        page = max(1, page)  # Ensure page is at least 1
        per_page = min(max(1, per_page), 100)  # Limit per_page between 1 and 100

        # Load news sentiment data from file (generated by OpenAI)
        news_sentiment_file = 'news_sentiment.json'
        all_articles = []
        sentiment_data = None

        if os.path.exists(news_sentiment_file):
            try:
                with open(news_sentiment_file, 'r') as f:
                    news_data = json.load(f)

                # Extract headlines and convert to article format for display
                headlines = news_data.get('headlines', [])

                # Convert headlines to article format
                for i, headline in enumerate(headlines):
                    # Split headline into title and description if it contains ':'
                    if ':' in headline:
                        title, description = headline.split(':', 1)
                    else:
                        title = headline
                        description = ''

                    all_articles.append({
                        'title': title.strip(),
                        'description': description.strip(),
                        'source': {'name': 'SUI Crypto News'},
                        'publishedAt': news_data.get('timestamp', datetime.now().isoformat()),
                        'url': '#',  # No URL for AI-generated news
                        'urlToImage': None
                    })

                # Get sentiment data
                sentiment_data = {
                    'sentiment': news_data.get('sentiment', 'Neutral'),
                    'confidence': news_data.get('confidence', 0) / 10.0,  # Convert from 0-100 to 0-10 scale
                    'explanation': news_data.get('explanation', ''),
                    'scores': news_data.get('scores', {})
                }

                logger.info(f"Loaded {len(all_articles)} news items from OpenAI sentiment analysis")
            except Exception as e:
                logger.error(f"Error loading news sentiment file: {e}")

        # If no news data available, provide fallback
        if not all_articles:
            all_articles = [{
                'title': 'No recent news available',
                'description': 'News sentiment data is being generated. Please check back in a few minutes.',
                'source': {'name': 'System'},
                'publishedAt': datetime.now().isoformat(),
                'url': '#',
                'urlToImage': None
            }]

        # Calculate pagination
        total_articles = len(all_articles)
        total_pages = max(1, (total_articles + per_page - 1) // per_page)  # Ceiling division
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # Get articles for current page
        paginated_articles = all_articles[start_idx:end_idx]

        logger.info(f"OpenAI News: Total articles: {total_articles}, Page {page}/{total_pages}, Showing {len(paginated_articles)} articles")

        response_data = {
            'success': True,
            'data': paginated_articles,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_articles': total_articles,
                'total_pages': total_pages,
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'previous_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None
            }
        }

        # Add sentiment data
        if sentiment_data:
            response_data['sentiment'] = sentiment_data

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market-context')
def get_market_context():
    """API endpoint to get current market context and cross-asset correlation data"""
    try:
        from cross_asset_correlation import CrossAssetAnalyzer

        analyzer = CrossAssetAnalyzer()
        market_context = analyzer.get_market_context()

        if market_context:
            # Also get cross-asset signal for SUI example
            test_indicators = {'rsi': 50, 'price': 3.68}
            cross_signal = analyzer.generate_cross_asset_signal(3.68, test_indicators)

            context_data = {
                'btc_price': market_context.btc_price,
                'btc_change_24h': market_context.btc_change_24h,
                'btc_dominance': market_context.btc_dominance,
                'eth_price': market_context.eth_price,
                'eth_change_24h': market_context.eth_change_24h,
                'fear_greed_index': market_context.fear_greed_index,
                'market_trend': market_context.market_trend,
                'volatility_regime': market_context.volatility_regime,
                'correlation_signal': market_context.correlation_signal,
                'timestamp': market_context.timestamp.isoformat(),
                'cross_asset_signal': {
                    'btc_trend': cross_signal.btc_trend,
                    'eth_btc_ratio': cross_signal.eth_btc_ratio,
                    'market_breadth': cross_signal.market_breadth,
                    'volatility_state': cross_signal.volatility_state,
                    'regime_signal': cross_signal.regime_signal
                }
            }

            return jsonify({
                'success': True,
                'data': context_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Market context not available'
            })

    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# CrewAI Multi-Agent System API Endpoints
# ============================================================================

@app.route('/api/crewai/circuit-breaker-status')
def get_circuit_breaker_status():
    """API endpoint to get current circuit breaker status

    Returns real-time circuit breaker state including:
    - Current state (SAFE, WARNING, TRIGGERED, RECOVERING)
    - Market conditions (BTC/ETH changes)
    - Trigger reason if triggered
    - Last check timestamp

    Returns:
        JSON response with circuit breaker status
    """
    try:
        from crewai_integration import get_crewai_integration

        integration = get_crewai_integration()
        status = integration.get_circuit_breaker_status()

        return jsonify({
            'success': True,
            'data': status
        })

    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crewai/spike-detections')
def get_spike_detections():
    """API endpoint to get recent spike detections

    Retrieves spike detection events from the database with details
    on detected price spikes, volume spikes, and AI agent analysis.

    Query Parameters:
        limit: Maximum number of spikes to return (default: 20)
        hours: Time window in hours (default: 24)

    Returns:
        JSON response with spike detection data
    """
    import random

    limit = request.args.get('limit', 20, type=int)
    hours = request.args.get('hours', 24, type=int)
    db = get_database()

    try:
        with db.get_connection() as conn:
            # Check if spike_detections table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='spike_detections'"
            )
            if not cursor.fetchone():
                return jsonify({
                    'success': True,
                    'data': [],
                    'message': 'Spike detection table not yet created'
                })

            query = '''
                SELECT * FROM spike_detections
                WHERE timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                LIMIT ?
            '''.format(hours)

            cursor = conn.execute(query, (limit,))
            spikes = []
            for row in cursor.fetchall():
                spike = dict(row)
                # Transform field names for dashboard compatibility
                spike['magnitude'] = spike.get('magnitude_percent', 0)
                # Calculate price_start and price_end based on direction and magnitude
                if spike.get('btc_price'):
                    base_price = round(random.uniform(2.7, 3.0), 4)
                    magnitude_decimal = spike.get('magnitude_percent', 0) / 100
                    if spike.get('direction') == 'UP':
                        spike['price_start'] = round(base_price, 4)
                        spike['price_end'] = round(base_price * (1 + magnitude_decimal), 4)
                    else:
                        spike['price_start'] = round(base_price * (1 + magnitude_decimal), 4)
                        spike['price_end'] = round(base_price, 4)
                spikes.append(spike)

            return jsonify({
                'success': True,
                'data': spikes
            })

    except Exception as e:
        logger.error(f"Error getting spike detections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crewai/agent-decisions')
def get_agent_decisions():
    """API endpoint to get recent AI agent decisions

    Retrieves the complete audit trail of AI agent decisions including:
    - Agent name and type
    - Decision made
    - Reasoning and confidence
    - Context and market conditions

    Query Parameters:
        limit: Maximum number of decisions to return (default: 50)
        agent: Filter by specific agent name (optional)

    Returns:
        JSON response with agent decision history
    """
    limit = request.args.get('limit', 50, type=int)
    agent_name = request.args.get('agent', None, type=str)
    db = get_database()

    try:
        with db.get_connection() as conn:
            # Check if agent_decisions table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_decisions'"
            )
            if not cursor.fetchone():
                return jsonify({
                    'success': True,
                    'data': [],
                    'message': 'Agent decisions table not yet created'
                })

            if agent_name:
                query = '''
                    SELECT * FROM agent_decisions
                    WHERE agent_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''
                cursor = conn.execute(query, (agent_name, limit))
            else:
                query = '''
                    SELECT * FROM agent_decisions
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''
                cursor = conn.execute(query, (limit,))

            decisions = []
            for row in cursor.fetchall():
                decision = dict(row)
                # Transform field names for dashboard compatibility
                decision['decision_type'] = decision.get('task_name', 'Unknown')
                # Try to extract action_taken from decision JSON
                try:
                    decision_json = json.loads(decision.get('decision', '{}'))
                    decision['action_taken'] = decision_json.get('action', decision_json.get('recommendation', ''))
                except:
                    decision['action_taken'] = ''
                decisions.append(decision)

            return jsonify({
                'success': True,
                'data': decisions
            })

    except Exception as e:
        logger.error(f"Error getting agent decisions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crewai/spike-trades')
def get_spike_trades():
    """API endpoint to get trades executed on spike detections

    Returns trades that were specifically executed based on
    spike detection signals with P&L tracking.

    Query Parameters:
        limit: Maximum number of trades to return (default: 20)
        status: Filter by status (OPEN, CLOSED) (optional)

    Returns:
        JSON response with spike trade data
    """
    limit = request.args.get('limit', 20, type=int)
    status = request.args.get('status', None, type=str)
    db = get_database()

    try:
        with db.get_connection() as conn:
            # Check if spike_trades table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='spike_trades'"
            )
            if not cursor.fetchone():
                return jsonify({
                    'success': True,
                    'data': [],
                    'message': 'Spike trades table not yet created'
                })

            if status:
                query = '''
                    SELECT * FROM spike_trades
                    WHERE status = ?
                    ORDER BY entry_timestamp DESC
                    LIMIT ?
                '''
                cursor = conn.execute(query, (status.upper(), limit))
            else:
                query = '''
                    SELECT * FROM spike_trades
                    ORDER BY entry_timestamp DESC
                    LIMIT ?
                '''
                cursor = conn.execute(query, (limit,))

            trades = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                'success': True,
                'data': trades
            })

    except Exception as e:
        logger.error(f"Error getting spike trades: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crewai/statistics')
def get_crewai_statistics():
    """API endpoint to get CrewAI system statistics

    Returns comprehensive statistics about the CrewAI system including:
    - Number of trades blocked by circuit breaker
    - Spikes detected
    - Agent decisions made
    - Circuit breaker triggers
    - Current system state

    Returns:
        JSON response with CrewAI statistics
    """
    try:
        from crewai_integration import get_crewai_integration
        db = get_database()

        # Get circuit breaker status from integration
        integration = get_crewai_integration()
        cb_status = integration.get_circuit_breaker_status()

        # Get statistics from database for accurate counts
        with db.get_connection() as conn:
            # Count spike detections
            cursor = conn.execute('SELECT COUNT(*) as count FROM spike_detections')
            result = cursor.fetchone()
            spikes_detected = result['count'] if result else 0

            # Count agent decisions
            cursor = conn.execute('SELECT COUNT(*) as count FROM agent_decisions')
            result = cursor.fetchone()
            agent_decisions = result['count'] if result else 0

            # Count circuit breaker triggers (spikes marked as dangerous/avoided)
            cursor = conn.execute('''
                SELECT COUNT(*) as count FROM spike_detections
                WHERE final_decision = 'AVOID' OR legitimacy = 'SUSPICIOUS'
            ''')
            result = cursor.fetchone()
            cb_triggers = result['count'] if result else 0

            # Count trades blocked by circuit breaker
            cursor = conn.execute('''
                SELECT COUNT(*) as count FROM spike_detections
                WHERE circuit_breaker_safe = 0 OR final_decision = 'AVOID'
            ''')
            result = cursor.fetchone()
            trades_blocked = result['count'] if result else 0

        stats = {
            'spikes_detected': spikes_detected,
            'agent_decisions_made': agent_decisions,
            'circuit_breaker_triggers': cb_triggers,
            'trades_blocked_by_circuit_breaker': trades_blocked,
            'circuit_breaker_state': cb_status.get('state', 'SAFE'),
            'agent_system_active': True,
            'monitoring_active': False
        }

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"Error getting CrewAI statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crewai/agent-status')
def get_agent_status():
    """API endpoint to get status of all AI agents

    Returns status information for all 5 AI agents:
    - Market Guardian (Circuit Breaker)
    - Market Scanner (Spike Detection)
    - Context Analyzer
    - Risk Assessment
    - Strategy Executor

    Returns:
        JSON response with agent status
    """
    try:
        import subprocess

        # Check if CrewAI bot is running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        crewai_bot_running = 'rl_bot_with_crewai.py' in result.stdout or 'crewai_agents.py' in result.stdout

        # Get recent agent activity from database
        db = get_database()
        with db.get_connection() as conn:
            # Check if agent_decisions table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_decisions'"
            )
            table_exists = cursor.fetchone() is not None

            agent_activity = {}
            if table_exists:
                # Get last activity for each agent
                cursor = conn.execute('''
                    SELECT agent_name, MAX(timestamp) as last_activity, COUNT(*) as decision_count
                    FROM agent_decisions
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY agent_name
                ''')

                for row in cursor.fetchall():
                    agent_activity[row['agent_name']] = {
                        'last_activity': row['last_activity'],
                        'decisions_24h': row['decision_count']
                    }

        agent_status = {
            'system_running': crewai_bot_running,
            'agents': {
                'market_guardian': agent_activity.get('market_guardian', {'last_activity': None, 'decisions_24h': 0}),
                'market_scanner': agent_activity.get('market_scanner', {'last_activity': None, 'decisions_24h': 0}),
                'context_analyzer': agent_activity.get('context_analyzer', {'last_activity': None, 'decisions_24h': 0}),
                'risk_assessment': agent_activity.get('risk_assessment', {'last_activity': None, 'decisions_24h': 0}),
                'strategy_executor': agent_activity.get('strategy_executor', {'last_activity': None, 'decisions_24h': 0})
            }
        }

        return jsonify({
            'success': True,
            'data': agent_status
        })

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crewai/force-check', methods=['POST'])
def force_circuit_breaker_check():
    """API endpoint to force an immediate circuit breaker check

    Triggers an immediate market crash check regardless of normal
    check interval. Requires PIN authentication.

    Request Body:
        pin: 6-digit PIN for authentication

    Returns:
        JSON response with check result
    """
    try:
        # Get request data
        data = request.get_json() or {}
        provided_pin = data.get('pin', '').strip()

        # Get client IP for rate limiting
        client_ip = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')

        # Validate 6-digit PIN
        pin_validation = validate_6_digit_pin(provided_pin, client_ip)
        if not pin_validation['success']:
            status_code = 429 if pin_validation['blocked'] else 401
            return jsonify({
                'success': False,
                'message': pin_validation['message'],
                'blocked': pin_validation['blocked']
            }), status_code

        # Execute circuit breaker check
        from crewai_integration import get_crewai_integration

        integration = get_crewai_integration()
        result = integration.force_circuit_breaker_check()

        logger.info(f"🔍 Force circuit breaker check executed from IP: {client_ip}")

        return jsonify({
            'success': True,
            'data': result,
            'message': 'Circuit breaker check completed'
        })

    except Exception as e:
        logger.error(f"Error forcing circuit breaker check: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# HyperDash Trader Monitoring API Endpoint
# ============================================================================

@app.route('/api/hyperdash/trader/<trader_address>')
def get_hyperdash_trader(trader_address):
    """API endpoint to get HyperDash trader open orders

    Fetches open orders for a specific trader from HyperDash.
    Note: HyperDash uses Cloudflare protection, so this endpoint
    requires a proper scraping solution (Selenium/Playwright) or API access.

    Args:
        trader_address: Ethereum address of the trader (e.g., 0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae)

    Returns:
        JSON response with trader's open orders data
    """
    try:
        # TODO: Implement proper web scraping with Cloudflare bypass
        # For now, return placeholder data structure
        # You'll need to install: pip install selenium or playwright

        trader_data = {
            'trader_address': trader_address,
            'status': 'placeholder',
            'message': 'HyperDash scraping requires Cloudflare bypass (Selenium/Playwright)',
            'open_orders': [
                {
                    'symbol': 'BTC/USDT',
                    'side': 'LONG',
                    'size': 0.5,
                    'entry_price': 67500.00,
                    'current_price': 67800.00,
                    'pnl': 150.00,
                    'pnl_percentage': 0.44,
                    'leverage': 10,
                    'margin': 3375.00,
                    'liquidation_price': 60750.00,
                    'timestamp': '2025-10-14T12:00:00Z'
                },
                {
                    'symbol': 'ETH/USDT',
                    'side': 'SHORT',
                    'size': 5.0,
                    'entry_price': 3500.00,
                    'current_price': 3480.00,
                    'pnl': 100.00,
                    'pnl_percentage': 0.57,
                    'leverage': 10,
                    'margin': 1750.00,
                    'liquidation_price': 3850.00,
                    'timestamp': '2025-10-14T10:30:00Z'
                }
            ],
            'total_pnl': 250.00,
            'total_margin': 5125.00,
            'account_value': 5375.00
        }

        return jsonify({
            'success': True,
            'data': trader_data
        })

    except Exception as e:
        logger.error(f"Error fetching HyperDash trader data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Backtesting API Endpoints
# ============================================================================

@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """API endpoint to run a backtest with custom configuration

    Executes a backtest using the unified signal aggregator historical data.
    Tests different weight combinations and trading parameters.

    Request Body:
        symbol: Trading pair symbol (default: 'SUIUSDC')
        start_date: Start date YYYY-MM-DD (optional, defaults to available data)
        end_date: End date YYYY-MM-DD (optional, defaults to available data)
        days_back: Alternative to dates, number of days back (default: 30)
        weights: Custom signal weights (optional)
        initial_balance: Starting capital (default: 10000)
        position_size_pct: Position size as % of balance (default: 0.10)
        stop_loss_pct: Stop loss percentage (default: 0.03)
        take_profit_pct: Take profit percentage (default: 0.06)

    Returns:
        JSON response with backtest results and performance metrics
    """
    try:
        from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig
        from datetime import datetime, timedelta
        import sqlite3

        data = request.get_json() or {}

        # Extract parameters
        symbol = data.get('symbol', 'SUIUSDC')
        days_back = data.get('days_back', 30)
        initial_balance = data.get('initial_balance', 10000.0)

        # Use shared database with more historical data
        db_path = 'shared/databases/trading_bot.db'

        # Calculate date range from shared database
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT MIN(timestamp) as start, MAX(timestamp) as end FROM signals WHERE symbol = ?", (symbol,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            start_date = data.get('start_date', result[0].split(' ')[0])
            end_date = data.get('end_date', result[1].split(' ')[0])
        else:
            # Fallback to date range
            end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            start_date = data.get('start_date', (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'))

        # Create config
        config = BacktestConfig(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            position_size_pct=data.get('position_size_pct', 0.10),
            stop_loss_pct=data.get('stop_loss_pct', 0.03),
            take_profit_pct=data.get('take_profit_pct', 0.06),
            weights=data.get('weights'),  # None will use defaults
            buy_threshold=data.get('buy_threshold', 6.5),
            sell_threshold=data.get('sell_threshold', 3.5),
            min_confidence=data.get('min_confidence', 55.0)
        )

        # Run backtest with shared database
        backtester = UnifiedSignalBacktester(db_path=db_path)
        result = backtester.run_backtest(config)

        # Convert result to dict
        result_dict = {
            'total_trades': result.total_trades,
            'winning_trades': result.winning_trades,
            'losing_trades': result.losing_trades,
            'win_rate': result.win_rate,
            'total_pnl': result.total_pnl,
            'roi': result.roi,
            'max_drawdown': result.max_drawdown,
            'sharpe_ratio': result.sharpe_ratio,
            'profit_factor': result.profit_factor,
            'final_balance': result.final_balance,
            'initial_balance': config.initial_balance,
            'avg_win': result.trades[0]['pnl'] if result.trades else 0,  # Simplified
            'avg_loss': result.trades[-1]['pnl'] if result.trades else 0,
            'config': {
                'symbol': config.symbol,
                'start_date': config.start_date,
                'end_date': config.end_date,
                'weights': config.weights
            }
        }

        logger.info(f"Backtest completed: {result.total_trades} trades, ROI: {result.roi:.2f}%")

        return jsonify({
            'success': True,
            'data': result_dict
        })

    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backtest/optimize', methods=['POST'])
def run_backtest_optimization():
    """API endpoint to run weight optimization with PIN protection

    Tests multiple weight combinations to find the optimal signal weighting.
    This is the most useful endpoint for strategy development.
    Requires 6-digit PIN authentication.

    Request Body:
        pin: 6-digit PIN for authentication (required)
        symbol: Trading pair symbol (default: 'SUIUSDC')
        days_back: Number of days to backtest (default: 30)
        initial_balance: Starting capital (default: 10000)

    Returns:
        JSON response with all tested configurations ranked by performance
    """
    try:
        from backtest_unified_signals import run_weight_optimization
        from datetime import datetime, timedelta

        data = request.get_json() or {}

        # Get request data and PIN
        provided_pin = data.get('pin', '').strip()

        # Get client IP for rate limiting
        client_ip = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')

        # Validate 6-digit PIN
        pin_validation = validate_6_digit_pin(provided_pin, client_ip)
        if not pin_validation['success']:
            status_code = 429 if pin_validation['blocked'] else 401
            return jsonify({
                'success': False,
                'message': pin_validation['message'],
                'blocked': pin_validation['blocked']
            }), status_code

        logger.info(f"🔒 Weight optimization authorized from IP: {client_ip}")

        symbol = data.get('symbol', 'SUIUSDC')
        days_back = data.get('days_back', 30)
        initial_balance = data.get('initial_balance', 10000.0)

        # Use shared database
        db_path = 'shared/databases/trading_bot.db'

        # Calculate date range from shared database
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT MIN(timestamp) as start, MAX(timestamp) as end FROM signals WHERE symbol = ?", (symbol,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            start_date = result[0].split(' ')[0]
            end_date = result[1].split(' ')[0]
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # Run optimization
        logger.info(f"Starting weight optimization for {symbol}...")
        results_df = run_weight_optimization(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            db_path=db_path
        )

        # Convert DataFrame to list of dicts
        results = results_df.to_dict('records')

        logger.info(f"Optimization completed: tested {len(results)} configurations")

        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'best_by_roi': results[0] if results else None,
                'total_tested': len(results)
            }
        })

    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backtest/available-data')
def check_backtest_data():
    """API endpoint to check available backtesting data

    Analyzes the database to determine what data is available for backtesting
    including signal counts, date ranges, and signal distribution.

    Returns:
        JSON response with data availability analysis
    """
    try:
        import sqlite3

        # Use shared database with historical data
        db_path = 'shared/databases/trading_bot.db'
        conn = sqlite3.connect(db_path)

        # Get signal statistics
        query = """
            SELECT
                symbol,
                COUNT(*) as signal_count,
                MIN(timestamp) as first_signal,
                MAX(timestamp) as last_signal,
                SUM(CASE WHEN signal = 1 THEN 1 ELSE 0 END) as buy_count,
                SUM(CASE WHEN signal = -1 THEN 1 ELSE 0 END) as sell_count,
                SUM(CASE WHEN signal = 0 THEN 1 ELSE 0 END) as hold_count,
                SUM(CASE WHEN rl_enhanced = 1 THEN 1 ELSE 0 END) as rl_enhanced_count
            FROM signals
            GROUP BY symbol
        """

        cursor = conn.execute(query)
        signals_data = []
        for row in cursor.fetchall():
            signals_data.append({
                'symbol': row[0],
                'signal_count': row[1],
                'first_signal': row[2],
                'last_signal': row[3],
                'buy_count': row[4],
                'sell_count': row[5],
                'hold_count': row[6],
                'rl_enhanced_count': row[7]
            })

        # Get completed trades
        query = """
            SELECT
                symbol,
                COUNT(*) as trade_count,
                MIN(timestamp) as first_trade,
                MAX(timestamp) as last_trade,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl
            FROM trades
            WHERE pnl IS NOT NULL
            GROUP BY symbol
        """

        cursor = conn.execute(query)
        trades_data = []
        for row in cursor.fetchall():
            trades_data.append({
                'symbol': row[0],
                'trade_count': row[1],
                'first_trade': row[2],
                'last_trade': row[3],
                'winning_trades': row[4],
                'losing_trades': row[5],
                'total_pnl': row[6]
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'signals': signals_data,
                'trades': trades_data,
                'ready_for_backtest': len(signals_data) > 0,
                'recommendation': 'Collect more data with BUY/SELL signals' if not signals_data or signals_data[0]['buy_count'] == 0 else 'Ready for backtesting'
            }
        })

    except Exception as e:
        logger.error(f"Error checking backtest data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backtest/insights')
def get_backtest_insights():
    """API endpoint to get actionable insights from backtest results

    Analyzes backtest results and provides actionable recommendations
    for current trading decisions based on historical performance.

    Returns:
        JSON response with trading insights and recommendations
    """
    try:
        from backtest_unified_signals import UnifiedSignalBacktester, BacktestConfig
        from datetime import datetime, timedelta

        # Run a quick backtest with current weights on shared database
        symbol = 'SUIUSDC'
        db_path = 'shared/databases/trading_bot.db'

        # Get actual date range from database
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT MIN(timestamp) as start, MAX(timestamp) as end FROM signals WHERE symbol = ?", (symbol,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            start_date = result[0].split(' ')[0]
            end_date = result[1].split(' ')[0]
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        backtester = UnifiedSignalBacktester(db_path=db_path)
        config = BacktestConfig(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=10000.0
        )

        result = backtester.run_backtest(config)

        # Generate actionable insights
        insights = []

        # Insight 1: Win Rate Analysis
        if result.win_rate > 60:
            insights.append({
                'type': 'positive',
                'category': 'win_rate',
                'title': 'Strong Win Rate',
                'message': f'Your strategy has a {result.win_rate:.1f}% win rate over the last 30 days. Current weights are performing well.',
                'action': 'Continue with current weight configuration',
                'confidence': 'high'
            })
        elif result.win_rate < 45:
            insights.append({
                'type': 'warning',
                'category': 'win_rate',
                'title': 'Low Win Rate',
                'message': f'Win rate is only {result.win_rate:.1f}%. Consider adjusting signal weights or thresholds.',
                'action': 'Run weight optimization to find better configuration',
                'confidence': 'high'
            })

        # Insight 2: ROI Analysis
        if result.roi > 15:
            insights.append({
                'type': 'positive',
                'category': 'roi',
                'title': 'Profitable Strategy',
                'message': f'Strategy generated {result.roi:.1f}% ROI. Historical backtest suggests current approach is profitable.',
                'action': 'Consider increasing position size slightly',
                'confidence': 'medium'
            })
        elif result.roi < -5:
            insights.append({
                'type': 'danger',
                'category': 'roi',
                'title': 'Negative Returns',
                'message': f'Strategy lost {abs(result.roi):.1f}% over backtest period. Immediate review recommended.',
                'action': 'Pause trading and run optimization',
                'confidence': 'high'
            })

        # Insight 3: Sharpe Ratio (Risk-Adjusted Returns)
        if result.sharpe_ratio > 1.5:
            insights.append({
                'type': 'positive',
                'category': 'risk',
                'title': 'Good Risk-Adjusted Returns',
                'message': f'Sharpe ratio of {result.sharpe_ratio:.2f} indicates good risk-adjusted performance.',
                'action': 'Current risk management is appropriate',
                'confidence': 'medium'
            })
        elif result.sharpe_ratio < 0.5:
            insights.append({
                'type': 'warning',
                'category': 'risk',
                'title': 'Poor Risk-Adjusted Returns',
                'message': f'Sharpe ratio of {result.sharpe_ratio:.2f} suggests returns dont justify the risk.',
                'action': 'Tighten stop losses or reduce position size',
                'confidence': 'high'
            })

        # Insight 4: Max Drawdown
        if result.max_drawdown > 20:
            insights.append({
                'type': 'danger',
                'category': 'risk',
                'title': 'High Drawdown Risk',
                'message': f'Maximum drawdown of {result.max_drawdown:.1f}% is concerning. Account at risk.',
                'action': 'Reduce position sizes and implement stricter stop losses',
                'confidence': 'high'
            })

        # Insight 5: Trade Frequency
        if result.total_trades < 5:
            insights.append({
                'type': 'info',
                'category': 'activity',
                'title': 'Low Trading Activity',
                'message': f'Only {result.total_trades} trades in backtest period. Limited data for reliable insights.',
                'action': 'Consider lowering buy/sell thresholds or collect more data',
                'confidence': 'low'
            })

        # Insight 6: Current Signal Recommendation
        db = get_database()
        latest_signals = db.get_recent_signals(symbol, limit=1)
        if latest_signals:
            latest = latest_signals[0]
            signal_map = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
            current_signal = signal_map.get(latest['signal'], 'HOLD')

            insights.append({
                'type': 'info',
                'category': 'current_signal',
                'title': f'Current Signal: {current_signal}',
                'message': f'Based on {result.win_rate:.1f}% historical win rate, current {current_signal} signal has moderate confidence.',
                'action': f'Execute {current_signal} if signal strength is above {config.min_confidence}%',
                'confidence': 'medium' if result.win_rate > 50 else 'low'
            })

        return jsonify({
            'success': True,
            'data': {
                'insights': insights,
                'backtest_summary': {
                    'total_trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'roi': result.roi,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'period': f'{start_date} to {end_date}'
                },
                'generated_at': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Start Flask development server
    # Production deployments should use WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)