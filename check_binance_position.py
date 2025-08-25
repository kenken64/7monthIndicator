#!/usr/bin/env python3
"""
Check exact Binance position details
"""

import os
from binance.client import Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_binance_position():
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    client = Client(api_key, secret_key, testnet=False)
    symbol = "SUIUSDC"
    
    try:
        # Get detailed position information
        positions = client.futures_position_information(symbol=symbol)
        
        for pos in positions:
            if pos['symbol'] == symbol:
                logger.info(f"📊 Binance Position Details for {symbol}:")
                logger.info(f"   Position Amount: {pos['positionAmt']}")
                logger.info(f"   Entry Price: ${pos['entryPrice']}")
                logger.info(f"   Mark Price: ${pos['markPrice']}")
                logger.info(f"   Unrealized PnL: ${pos['unRealizedProfit']}")
                logger.info(f"   Position Side: {pos['positionSide']}")
                
                position_amt = float(pos['positionAmt'])
                if abs(position_amt) > 0.001:
                    side = "SHORT" if position_amt < 0 else "LONG"
                    logger.info(f"   Active Position: {side} {abs(position_amt)} units")
                else:
                    logger.info(f"   No active position")
                
                break
        
        # Also get recent trades to understand what happened
        logger.info("\n🔍 Recent Binance Trades (last 10):")
        trades = client.futures_account_trades(symbol=symbol, limit=10)
        
        for i, trade in enumerate(reversed(trades[-10:])):  # Show newest first
            side_emoji = "🟢" if trade['side'] == 'BUY' else "🔴"
            logger.info(f"   {i+1}. {side_emoji} {trade['side']} {trade['qty']} @ ${trade['price']} - {trade['time']}")
        
    except Exception as e:
        logger.error(f"❌ Error checking position: {e}")

if __name__ == "__main__":
    check_binance_position()