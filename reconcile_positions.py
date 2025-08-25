#!/usr/bin/env python3
"""
Standalone Position Reconciliation Script
This script reconciles all open trades in the database with actual Binance positions
"""

import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
from database import get_database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reconcile_all_positions():
    """Reconcile all open positions in database with Binance"""
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        logger.error("❌ Binance API credentials not found in .env file")
        return
    
    try:
        # Initialize Binance client and database
        client = Client(api_key, secret_key, testnet=False)
        db = get_database()
        
        logger.info("🔄 Starting position reconciliation...")
        
        # Get all symbols with open trades
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT symbol FROM trades WHERE status = 'OPEN'")
            symbols = [row['symbol'] for row in cursor.fetchall()]
        
        logger.info(f"📊 Found {len(symbols)} symbols with open trades: {', '.join(symbols)}")
        
        total_reconciled = 0
        
        for symbol in symbols:
            try:
                # Get live position from Binance
                positions = client.futures_position_information(symbol=symbol)
                live_position_amt = 0
                
                for pos in positions:
                    if pos['symbol'] == symbol:
                        live_position_amt = float(pos['positionAmt'])
                        break
                
                # Get open trades from database
                open_trades = db.get_open_trades(symbol)
                
                if abs(live_position_amt) < 0.001 and len(open_trades) > 0:
                    # Position closed on Binance but still open in database
                    logger.info(f"🔄 {symbol}: Position closed on Binance, {len(open_trades)} open trades in database")
                    
                    # Get current price
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    
                    # Close all open trades in database
                    for trade in open_trades:
                        # Calculate PnL
                        if trade['side'] == 'BUY':
                            pnl = (current_price - trade['entry_price']) * trade['quantity']
                        else:  # SELL
                            pnl = (trade['entry_price'] - current_price) * trade['quantity']
                        
                        # Calculate PnL percentage
                        pnl_percentage = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
                        
                        # Update trade to closed
                        db.update_trade_exit(
                            trade_id=trade['id'],
                            exit_price=current_price,
                            pnl=pnl,
                            pnl_percentage=pnl_percentage,
                            status='CLOSED'
                        )
                        
                        total_reconciled += 1
                        
                        logger.info(f"✅ Trade {trade['id']}: {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.4f} → ${current_price:.4f}, PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
                
                elif len(open_trades) > 0:
                    # Calculate database position
                    db_position_amt = 0
                    for trade in open_trades:
                        if trade['side'] == 'BUY':
                            db_position_amt += trade['quantity']
                        else:  # SELL
                            db_position_amt -= trade['quantity']
                    
                    if abs(abs(live_position_amt) - abs(db_position_amt)) > 0.001:
                        logger.warning(f"⚠️ {symbol}: Position mismatch - Binance: {live_position_amt}, Database: {db_position_amt}")
                    else:
                        logger.info(f"✅ {symbol}: Positions match - {len(open_trades)} open trades")
                else:
                    logger.info(f"✅ {symbol}: No open trades to reconcile")
                    
            except BinanceAPIException as e:
                logger.error(f"❌ Error processing {symbol}: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error with {symbol}: {e}")
        
        logger.info(f"🎉 Reconciliation complete! Updated {total_reconciled} trades")
        
        # Show final stats
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM trades WHERE status = 'OPEN'")
            open_count = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM trades WHERE status = 'CLOSED'")
            closed_count = cursor.fetchone()['count']
        
        logger.info(f"📈 Final status: {open_count} open trades, {closed_count} closed trades")
        
    except Exception as e:
        logger.error(f"❌ Critical error during reconciliation: {e}")

if __name__ == "__main__":
    reconcile_all_positions()