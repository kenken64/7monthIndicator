#!/usr/bin/env python3
"""
Final Position Reconciliation
Match database exactly to current Binance position
"""

import os
from binance.client import Client
from dotenv import load_dotenv
from database import get_database
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def final_reconciliation():
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    client = Client(api_key, secret_key, testnet=False)
    db = get_database()
    symbol = "SUIUSDC"
    
    try:
        # Get current Binance position
        positions = client.futures_position_information(symbol=symbol)
        current_position = None
        
        for pos in positions:
            if pos['symbol'] == symbol:
                position_amt = float(pos['positionAmt'])
                if abs(position_amt) > 0.001:
                    current_position = {
                        'amount': position_amt,
                        'entry_price': float(pos['entryPrice']),
                        'side': 'SELL' if position_amt < 0 else 'BUY',
                        'quantity': abs(position_amt)
                    }
                break
        
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        logger.info("🔄 Final Reconciliation Process")
        logger.info(f"Current Binance Position: {current_position}")
        logger.info(f"Current Price: ${current_price:.4f}")
        
        # Get all open trades from database
        open_trades = db.get_open_trades(symbol)
        logger.info(f"Database Open Trades: {len(open_trades)}")
        
        if current_position:
            # Strategy: Close all old trades and create new one matching Binance
            logger.info("📊 Closing all database trades and creating new matching trade...")
            
            total_closed_pnl = 0
            closed_count = 0
            
            # Close all existing trades
            for trade in open_trades:
                # Calculate PnL
                if trade['side'] == 'BUY':
                    pnl = (current_price - trade['entry_price']) * trade['quantity']
                else:  # SELL
                    pnl = (trade['entry_price'] - current_price) * trade['quantity']
                
                pnl_percentage = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
                
                db.update_trade_exit(
                    trade_id=trade['id'],
                    exit_price=current_price,
                    pnl=pnl,
                    pnl_percentage=pnl_percentage,
                    status='CLOSED'
                )
                
                total_closed_pnl += pnl
                closed_count += 1
                
                logger.info(f"✅ Closed Trade {trade['id']}: {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.4f}, PnL: ${pnl:.2f}")
            
            # Create new trade matching current Binance position
            trade_id = db.store_trade(
                signal_id=0,  # No signal ID for reconciliation
                symbol=symbol,
                side=current_position['side'],
                quantity=current_position['quantity'],
                entry_price=current_position['entry_price'],
                leverage=50,  # Assuming 50x leverage
                position_percentage=51,  # Assuming 51% position size
                order_id=f"RECONCILE_{int(current_price * 10000)}",
                liquidation_price=None
            )
            
            logger.info(f"🆕 Created new trade matching Binance: ID={trade_id}")
            logger.info(f"   {current_position['side']} {current_position['quantity']} @ ${current_position['entry_price']:.4f}")
            logger.info(f"💰 Total PnL from closed trades: ${total_closed_pnl:.2f}")
            
        else:
            # No position on Binance - close all trades
            logger.info("🔄 No position on Binance - closing all database trades")
            
            for trade in open_trades:
                if trade['side'] == 'BUY':
                    pnl = (current_price - trade['entry_price']) * trade['quantity']
                else:  # SELL
                    pnl = (trade['entry_price'] - current_price) * trade['quantity']
                
                pnl_percentage = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
                
                db.update_trade_exit(
                    trade_id=trade['id'],
                    exit_price=current_price,
                    pnl=pnl,
                    pnl_percentage=pnl_percentage,
                    status='CLOSED'
                )
                
                logger.info(f"✅ Closed Trade {trade['id']}: {trade['side']} {trade['quantity']} @ ${trade['entry_price']:.4f}, PnL: ${pnl:.2f}")
        
        # Final verification
        final_open_trades = db.get_open_trades(symbol)
        db_position = 0
        for trade in final_open_trades:
            if trade['side'] == 'BUY':
                db_position += trade['quantity']
            else:
                db_position -= trade['quantity']
        
        binance_position = current_position['amount'] if current_position else 0
        
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM trades WHERE status = 'CLOSED'")
            closed_total = cursor.fetchone()['count']
        
        logger.info(f"🎉 Reconciliation Complete!")
        logger.info(f"   Binance Position: {binance_position}")
        logger.info(f"   Database Position: {db_position}")
        logger.info(f"   Match: {abs(binance_position - db_position) < 0.001}")
        logger.info(f"   Total Closed Trades: {closed_total}")
        logger.info(f"   Open Trades: {len(final_open_trades)}")
        
    except Exception as e:
        logger.error(f"❌ Error in final reconciliation: {e}")

if __name__ == "__main__":
    final_reconciliation()