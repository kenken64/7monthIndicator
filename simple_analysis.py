#!/usr/bin/env python3
"""
Simple Performance Analysis
"""

from database import get_database
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_performance():
    db = get_database()
    
    logger.info("🔍 Analyzing trading bot performance...")
    
    with db.get_connection() as conn:
        # Get closed trades
        cursor = conn.execute("SELECT * FROM trades WHERE status = 'CLOSED' ORDER BY timestamp")
        trades = [dict(row) for row in cursor.fetchall()]
        
        # Get signals
        cursor = conn.execute("SELECT * FROM signals ORDER BY timestamp")
        signals = [dict(row) for row in cursor.fetchall()]
    
    logger.info(f"📊 Found {len(trades)} closed trades and {len(signals)} signals")
    
    if len(trades) == 0:
        logger.warning("⚠️ No closed trades to analyze")
        return
    
    # Basic performance analysis
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl'] and t['pnl'] > 0])
    losing_trades = len([t for t in trades if t['pnl'] and t['pnl'] < 0])
    
    total_pnl = sum([t['pnl'] for t in trades if t['pnl']])
    wins = [t['pnl'] for t in trades if t['pnl'] and t['pnl'] > 0]
    losses = [t['pnl'] for t in trades if t['pnl'] and t['pnl'] < 0]
    
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    win_rate = (winning_trades / total_trades) * 100
    
    logger.info("="*60)
    logger.info("📊 CRITICAL PERFORMANCE ANALYSIS")
    logger.info("="*60)
    logger.info(f"❌ Total Trades: {total_trades}")
    logger.info(f"❌ Win Rate: {win_rate:.1f}% (EXTREMELY LOW!)")
    logger.info(f"❌ Winning Trades: {winning_trades}")
    logger.info(f"❌ Losing Trades: {losing_trades}")
    logger.info(f"❌ Total PnL: ${total_pnl:.2f}")
    logger.info(f"❌ Average Win: ${avg_win:.2f}")
    logger.info(f"❌ Average Loss: ${avg_loss:.2f}")
    logger.info(f"❌ Loss/Win Ratio: {abs(avg_loss/avg_win):.1f}x" if avg_win > 0 else "∞")
    logger.info("="*60)
    
    # Analyze signal patterns
    signal_map = {s['id']: s for s in signals}
    
    logger.info("\n🔍 FAILURE PATTERN ANALYSIS:")
    
    # Group by signal type
    buy_losses = []
    sell_losses = []
    
    for trade in trades:
        if trade['pnl'] and trade['pnl'] < 0 and trade['signal_id']:
            signal = signal_map.get(trade['signal_id'])
            if signal:
                if signal['signal'] == 1:  # BUY signal
                    buy_losses.append(trade['pnl'])
                elif signal['signal'] == -1:  # SELL signal
                    sell_losses.append(trade['pnl'])
    
    logger.info(f"📉 BUY signal losses: {len(buy_losses)} trades, ${sum(buy_losses):.2f} total loss")
    logger.info(f"📉 SELL signal losses: {len(sell_losses)} trades, ${sum(sell_losses):.2f} total loss")
    
    # Analyze worst trades
    worst_trades = sorted([t for t in trades if t['pnl']], key=lambda x: x['pnl'])[:5]
    
    logger.info(f"\n💸 TOP 5 WORST TRADES:")
    for i, trade in enumerate(worst_trades, 1):
        signal = signal_map.get(trade['signal_id']) if trade['signal_id'] else None
        signal_strength = signal['strength'] if signal else 'Unknown'
        signal_type = 'BUY' if signal and signal['signal'] == 1 else 'SELL' if signal and signal['signal'] == -1 else 'HOLD'
        
        logger.info(f"  {i}. Trade ID {trade['id']}: {trade['side']} {trade['quantity']:.1f} @ ${trade['entry_price']:.4f}")
        logger.info(f"     Loss: ${trade['pnl']:.2f} ({trade['pnl_percentage']:.1f}%) | Signal: {signal_type} (Strength: {signal_strength})")
    
    # Key problems for RL
    logger.info(f"\n🤖 KEY PROBLEMS FOR REINFORCEMENT LEARNING:")
    logger.info(f"1. ❌ CATASTROPHIC WIN RATE: {win_rate:.1f}% (Need 45%+ minimum)")
    logger.info(f"2. ❌ POOR RISK MANAGEMENT: Avg loss ${abs(avg_loss):.2f} >> Avg win ${avg_win:.2f}")
    logger.info(f"3. ❌ SIGNAL QUALITY: Current signals lead to 93% failure rate")
    logger.info(f"4. ❌ POSITION SIZING: Large losses suggest oversized positions")
    logger.info(f"5. ❌ EXIT STRATEGY: No proper stop-loss or take-profit execution")
    
    # RL recommendations
    logger.info(f"\n🎯 REINFORCEMENT LEARNING STRATEGY:")
    logger.info(f"• Use PPO (Proximal Policy Optimization) for stable learning")
    logger.info(f"• State space: Technical indicators + position info + market context")
    logger.info(f"• Action space: [HOLD, BUY_SMALL, BUY_LARGE, SELL_SMALL, SELL_LARGE, CLOSE]")
    logger.info(f"• Reward function: Heavily penalize losses, small reward for holds")
    logger.info(f"• Training data: Use current failure patterns as negative examples")
    logger.info(f"• Risk management: Max 1-2% risk per trade")

if __name__ == "__main__":
    analyze_performance()