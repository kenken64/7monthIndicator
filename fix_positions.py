#!/usr/bin/env python3
"""
Advanced Position Fix Script
This script handles partial position closures and complex reconciliation
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

def fix_positions():
    """Advanced position reconciliation with partial closure handling"""
    
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
        
        symbol = "SUIUSDC"
        
        logger.info("🔄 Starting advanced position reconciliation...")
        
        # Get live position from Binance
        positions = client.futures_position_information(symbol=symbol)
        live_position_amt = 0
        
        for pos in positions:
            if pos['symbol'] == symbol:
                live_position_amt = float(pos['positionAmt'])
                break
        
        # Get open trades from database
        open_trades = db.get_open_trades(symbol)
        
        # Calculate database position
        db_position_amt = 0
        for trade in open_trades:
            if trade['side'] == 'BUY':
                db_position_amt += trade['quantity']
            else:  # SELL
                db_position_amt -= trade['quantity']
        
        logger.info(f"📊 Position Analysis:")
        logger.info(f"   Binance Position: {live_position_amt}")
        logger.info(f"   Database Position: {db_position_amt}")
        logger.info(f"   Database Open Trades: {len(open_trades)}")
        logger.info(f"   Difference: {abs(live_position_amt - db_position_amt):.4f}")
        
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        logger.info(f"   Current Price: ${current_price:.4f}")
        
        if abs(live_position_amt) < 0.001:
            # No position on Binance - close all database trades
            logger.info("🔄 No position on Binance - closing all database trades")
            
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
                
                logger.info(f"✅ Closed Trade {trade['id']}: {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.4f} → ${current_price:.4f}, PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
        
        elif abs(abs(live_position_amt) - abs(db_position_amt)) > 0.001:
            # Partial closure - some trades were closed
            logger.info("🔄 Partial position closure detected")
            
            # Calculate how much was closed
            closed_amount = abs(db_position_amt) - abs(live_position_amt)
            logger.info(f"   Estimated closed amount: {closed_amount:.4f}")
            
            # Strategy: Close older trades first (FIFO)
            remaining_to_close = closed_amount
            open_trades.sort(key=lambda x: x['timestamp'])  # Sort by timestamp (oldest first)
            
            for trade in open_trades:
                if remaining_to_close <= 0.001:
                    break
                
                trade_quantity = trade['quantity']
                
                if trade_quantity <= remaining_to_close:
                    # Close entire trade
                    if trade['side'] == 'BUY':
                        pnl = (current_price - trade['entry_price']) * trade_quantity
                    else:  # SELL
                        pnl = (trade['entry_price'] - current_price) * trade_quantity
                    
                    pnl_percentage = (pnl / (trade['entry_price'] * trade_quantity)) * 100
                    
                    db.update_trade_exit(
                        trade_id=trade['id'],
                        exit_price=current_price,
                        pnl=pnl,
                        pnl_percentage=pnl_percentage,
                        status='CLOSED'
                    )
                    
                    remaining_to_close -= trade_quantity
                    logger.info(f"✅ Closed Trade {trade['id']}: {trade['side']} {trade_quantity} @ ${trade['entry_price']:.4f} → ${current_price:.4f}, PnL: ${pnl:.2f}")
                    
                # Note: For partial trade closure within a single trade, you'd need more complex logic
                # For now, we're using FIFO (First In, First Out) approach
        
        else:
            logger.info("✅ Positions already match - no reconciliation needed")
        
        # Show final stats
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM trades WHERE status = 'OPEN'")
            open_count = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM trades WHERE status = 'CLOSED'")
            closed_count = cursor.fetchone()['count']
        
        logger.info(f"📈 Final status: {open_count} open trades, {closed_count} closed trades")
        
        # Verify reconciliation
        open_trades_after = db.get_open_trades(symbol)
        db_position_after = 0
        for trade in open_trades_after:
            if trade['side'] == 'BUY':
                db_position_after += trade['quantity']
            else:  # SELL
                db_position_after -= trade['quantity']
        
        logger.info(f"📊 After reconciliation:")
        logger.info(f"   Binance Position: {live_position_amt}")
        logger.info(f"   Database Position: {db_position_after}")
        logger.info(f"   Match: {abs(live_position_amt - db_position_after) < 0.001}")
        
    except Exception as e:
        logger.error(f"❌ Critical error during reconciliation: {e}")

if __name__ == "__main__":
    fix_positions()