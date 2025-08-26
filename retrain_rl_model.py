#!/usr/bin/env python3
"""
Enhanced RL Model Retraining Script
Uses database signals and trades to retrain the RL model with improved reward system
"""

import os
import sys
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from database import get_database
from lightweight_rl import LightweightRLSystem, SimpleTradingAgent, TradingSimulator
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rl_retraining.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedRLRetrainer:
    """Enhanced RL model retrainer with improved data processing and reward system"""
    
    def __init__(self):
        self.db = get_database()
        self.agent = SimpleTradingAgent(learning_rate=0.15, discount_factor=0.9, epsilon=0.2)
        self.training_data = []
        
    def prepare_enhanced_training_data(self, days_back: int = 30) -> list:
        """Prepare enhanced training data from database with better features"""
        logger.info(f"📊 Preparing enhanced training data from last {days_back} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.db.get_connection() as conn:
            # Get signals with their outcomes by joining with trades
            query = """
                SELECT 
                    s.timestamp,
                    s.symbol,
                    s.price,
                    s.signal,
                    s.strength,
                    s.indicators,
                    s.rl_enhanced,
                    t.side,
                    t.entry_price,
                    t.exit_price,
                    t.pnl,
                    t.pnl_percentage,
                    t.status
                FROM signals s
                LEFT JOIN trades t ON s.id = t.signal_id
                WHERE s.timestamp >= ?
                ORDER BY s.timestamp
            """
            
            cursor = conn.execute(query, (cutoff_date,))
            raw_data = cursor.fetchall()
            
            processed_data = []
            for row in raw_data:
                row_dict = dict(row)
                
                # Parse indicators JSON
                if row_dict['indicators']:
                    try:
                        indicators = json.loads(row_dict['indicators'])
                        # Add all indicator values to the row
                        for key, value in indicators.items():
                            if isinstance(value, (int, float)):
                                row_dict[key] = value
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse indicators for row at {row_dict['timestamp']}")
                        continue
                
                # Calculate outcome label for supervised learning aspects
                outcome = 'unknown'
                if row_dict['pnl_percentage'] is not None:
                    if row_dict['pnl_percentage'] > 2:
                        outcome = 'good_profit'
                    elif row_dict['pnl_percentage'] > 0:
                        outcome = 'small_profit'
                    elif row_dict['pnl_percentage'] > -2:
                        outcome = 'small_loss'
                    else:
                        outcome = 'bad_loss'
                
                row_dict['outcome'] = outcome
                processed_data.append(row_dict)
            
            logger.info(f"✅ Processed {len(processed_data)} data points")
            
            # Show outcome distribution
            outcome_counts = {}
            for row in processed_data:
                outcome = row['outcome']
                outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            
            logger.info("📈 Outcome distribution:")
            for outcome, count in outcome_counts.items():
                logger.info(f"   {outcome}: {count}")
            
            return processed_data
    
    def create_enhanced_simulator(self, data: list):
        """Create enhanced trading simulator with better reward system"""
        
        class EnhancedTradingSimulator(TradingSimulator):
            def __init__(self, data):
                super().__init__(data)
                self.consecutive_losses = 0
                self.consecutive_wins = 0
                
            def step(self, action: str):
                """Enhanced step function with better rewards"""
                if self.current_idx >= len(self.data) - 1:
                    return {}, 0, True
                
                current_data = self.data[self.current_idx]
                current_price = current_data.get('price', 3.7)
                reward = 0
                
                # Get real outcome if available (for enhanced learning)
                real_outcome = current_data.get('outcome', 'unknown')
                
                # Execute action
                if action == 'BUY' and not self.position:
                    self.position = 'LONG'
                    self.entry_price = current_price
                    
                    # Enhanced reward based on known outcomes
                    if real_outcome in ['good_profit', 'small_profit']:
                        reward = 0.05  # Positive reward for good timing
                    elif real_outcome in ['bad_loss']:
                        reward = -0.1  # Penalty for bad timing
                    else:
                        reward = -0.001  # Small transaction cost
                        
                elif action == 'SELL' and not self.position:
                    self.position = 'SHORT'
                    self.entry_price = current_price
                    
                    # Similar logic for SELL
                    if real_outcome in ['good_profit', 'small_profit']:
                        reward = 0.05
                    elif real_outcome in ['bad_loss']:
                        reward = -0.1
                    else:
                        reward = -0.001
                        
                elif action == 'CLOSE' and self.position:
                    # Close position and calculate enhanced reward
                    if self.position == 'LONG':
                        pnl_pct = (current_price - self.entry_price) / self.entry_price
                    else:  # SHORT
                        pnl_pct = (self.entry_price - current_price) / self.entry_price
                    
                    # Enhanced reward system
                    if pnl_pct > 0.02:  # >2% profit
                        reward = pnl_pct * 100 + 0.1  # Big reward for good profits
                        self.consecutive_wins += 1
                        self.consecutive_losses = 0
                    elif pnl_pct > 0:  # Small profit
                        reward = pnl_pct * 50 + 0.05
                        self.consecutive_wins += 1
                        self.consecutive_losses = 0
                    elif pnl_pct > -0.02:  # Small loss
                        reward = pnl_pct * 75  # Moderate penalty
                        self.consecutive_losses += 1
                        self.consecutive_wins = 0
                    else:  # Big loss
                        reward = pnl_pct * 150 - 0.2  # Heavy penalty for big losses
                        self.consecutive_losses += 1
                        self.consecutive_wins = 0
                    
                    # Bonus/penalty for streaks
                    if self.consecutive_wins >= 3:
                        reward += 0.05  # Bonus for winning streaks
                    elif self.consecutive_losses >= 3:
                        reward -= 0.1  # Extra penalty for losing streaks
                    
                    # Update balance
                    pnl_amount = self.balance * 0.02 * pnl_pct
                    self.balance += pnl_amount
                    
                    # Record trade
                    self.trades_history.append({
                        'entry_price': self.entry_price,
                        'exit_price': current_price,
                        'position': self.position,
                        'pnl_pct': pnl_pct,
                        'pnl_amount': pnl_amount,
                        'reward': reward
                    })
                    
                    self.position = None
                    self.entry_price = 0
                    
                elif action == 'HOLD':
                    # Enhanced HOLD logic
                    base_reward = -0.0001  # Small penalty for inaction
                    
                    # Reward HOLD when outcome is unknown or neutral
                    if real_outcome == 'unknown':
                        base_reward = 0  # No penalty for holding in uncertain times
                    elif real_outcome in ['bad_loss']:
                        base_reward = 0.01  # Reward for avoiding bad trades
                    
                    # Penalty for holding losing positions too long
                    if self.position and self.entry_price > 0:
                        if self.position == 'LONG':
                            unrealized_pnl = (current_price - self.entry_price) / self.entry_price
                        else:
                            unrealized_pnl = (self.entry_price - current_price) / self.entry_price
                        
                        if unrealized_pnl < -0.03:  # >3% loss
                            base_reward -= 0.01  # Penalty for not cutting losses
                    
                    reward = base_reward
                
                # Move to next step
                self.current_idx += 1
                next_data = self.get_current_indicators()
                
                # Check if done
                done = (self.current_idx >= len(self.data) - 1) or (self.balance <= 500)
                
                return next_data, reward, done
        
        return EnhancedTradingSimulator(data)
    
    def retrain_model(self, episodes: int = 200, save_every: int = 50):
        """Retrain the RL model with enhanced learning"""
        logger.info(f"🤖 Starting enhanced RL model retraining with {episodes} episodes...")
        
        # Load existing model as starting point
        model_loaded = self.agent.load_model()
        if model_loaded:
            logger.info("📂 Loaded existing model as starting point")
        else:
            logger.info("🆕 Starting with fresh model")
        
        # Prepare training data
        training_data = self.prepare_enhanced_training_data()
        if not training_data:
            logger.error("❌ No training data available!")
            return False
        
        # Create enhanced simulator
        simulator = self.create_enhanced_simulator(training_data)
        
        best_performance = -float('inf')
        recent_performances = []
        
        for episode in range(episodes):
            # Reset environment
            current_indicators = simulator.reset()
            if not current_indicators:
                logger.warning(f"⚠️ Episode {episode}: No indicators available, skipping")
                continue
                
            current_state = self.agent.discretize_state(current_indicators)
            
            episode_reward = 0
            steps = 0
            max_steps = min(500, len(training_data) // 2)
            
            while steps < max_steps:
                # Get action
                action = self.agent.get_action(current_state, training=True)
                
                # Execute action
                next_indicators, reward, done = simulator.step(action)
                
                if done or not next_indicators:
                    break
                
                next_state = self.agent.discretize_state(next_indicators)
                
                # Update Q-value
                self.agent.update_q_value(current_state, action, reward, next_state)
                
                # Move to next state
                current_state = next_state
                episode_reward += reward
                steps += 1
            
            # Track performance
            performance = simulator.get_performance_stats()
            self.agent.training_history.append(performance)
            self.agent.total_episodes += 1
            
            # Keep track of recent performances
            recent_performances.append(performance.get('return_pct', 0))
            if len(recent_performances) > 20:
                recent_performances = recent_performances[-20:]
            
            # Log progress
            if episode % 10 == 0 or episode == episodes - 1:
                avg_recent = sum(recent_performances) / len(recent_performances) if recent_performances else 0
                logger.info(f"Episode {episode+1}/{episodes}:")
                logger.info(f"  Episode reward: {episode_reward:.3f}")
                logger.info(f"  Trades: {performance['total_trades']}")
                logger.info(f"  Win rate: {performance['win_rate']:.1f}%")
                logger.info(f"  Return: {performance.get('return_pct', 0):.1f}%")
                logger.info(f"  Avg recent return: {avg_recent:.1f}%")
                logger.info(f"  States learned: {len(self.agent.q_table)}")
            
            # Save model periodically and when performance improves
            current_performance = performance.get('return_pct', 0)
            if current_performance > best_performance:
                best_performance = current_performance
                self.agent.save_model()
                logger.info(f"💾 Saved improved model! Best return: {best_performance:.1f}%")
            
            if (episode + 1) % save_every == 0:
                backup_name = f'rl_trading_model_episode_{episode+1}.pkl'
                self.agent.save_model(backup_name)
                logger.info(f"💾 Saved backup: {backup_name}")
        
        # Final model save
        self.agent.save_model()
        
        # Gradually reduce exploration
        self.agent.epsilon = max(0.05, self.agent.epsilon * 0.9)
        logger.info(f"🎯 Reduced exploration rate to {self.agent.epsilon:.3f}")
        
        logger.info(f"🎉 Retraining complete! Best performance: {best_performance:.1f}%")
        
        return True
    
    def analyze_training_results(self):
        """Analyze the results of retraining"""
        if not self.agent.training_history:
            logger.warning("⚠️ No training history to analyze")
            return
        
        logger.info("🔍 TRAINING RESULTS ANALYSIS:")
        
        # Calculate averages
        recent_history = self.agent.training_history[-50:] if len(self.agent.training_history) >= 50 else self.agent.training_history
        
        if recent_history:
            avg_win_rate = sum(h['win_rate'] for h in recent_history) / len(recent_history)
            avg_return = sum(h.get('return_pct', 0) for h in recent_history) / len(recent_history)
            avg_trades = sum(h['total_trades'] for h in recent_history) / len(recent_history)
            
            logger.info(f"📊 Recent Performance (last {len(recent_history)} episodes):")
            logger.info(f"   Average win rate: {avg_win_rate:.1f}%")
            logger.info(f"   Average return: {avg_return:.1f}%")
            logger.info(f"   Average trades per episode: {avg_trades:.1f}")
            logger.info(f"   Total states learned: {len(self.agent.q_table)}")
            logger.info(f"   Total episodes: {self.agent.total_episodes}")
        
        # Show learning progress
        if len(self.agent.training_history) >= 20:
            early_avg = sum(h.get('return_pct', 0) for h in self.agent.training_history[:10]) / 10
            late_avg = sum(h.get('return_pct', 0) for h in self.agent.training_history[-10:]) / 10
            improvement = late_avg - early_avg
            
            logger.info(f"📈 Learning Progress:")
            logger.info(f"   Early episodes avg return: {early_avg:.1f}%")
            logger.info(f"   Recent episodes avg return: {late_avg:.1f}%")
            logger.info(f"   Improvement: {improvement:+.1f}%")

def main():
    """Main retraining function"""
    logger.info("🚀 Starting Enhanced RL Model Retraining...")
    
    # Check if database has enough data
    db = get_database()
    with db.get_connection() as conn:
        cursor = conn.execute('SELECT COUNT(*) as count FROM signals WHERE indicators IS NOT NULL')
        data_count = cursor.fetchone()['count']
        
        if data_count < 50:
            logger.error(f"❌ Insufficient data for training: only {data_count} signals available")
            logger.info("💡 Let the bot run for a few more hours to collect more data")
            return False
        
        logger.info(f"✅ Found {data_count} signals for training")
    
    # Create retrainer
    retrainer = EnhancedRLRetrainer()
    
    # Retrain model
    success = retrainer.retrain_model(episodes=150)
    
    if success:
        # Analyze results
        retrainer.analyze_training_results()
        
        # Test new model
        logger.info("🧪 Testing retrained model...")
        rl_system = LightweightRLSystem()
        rl_system.agent = retrainer.agent
        
        test_indicators = {
            'rsi': 45,
            'macd': -0.01,
            'macd_histogram': 0.005,
            'price': 3.68,
            'vwap': 3.70,
            'ema_9': 3.65,
            'ema_21': 3.67
        }
        
        recommendation = rl_system.get_trading_recommendation(test_indicators)
        logger.info(f"🤖 RETRAINED MODEL RECOMMENDATION:")
        logger.info(f"   Action: {recommendation['action']}")
        logger.info(f"   Confidence: {recommendation['confidence']:.1%}")
        logger.info(f"   State: {recommendation['state']}")
        
        logger.info("✅ Retraining completed successfully!")
        return True
    else:
        logger.error("❌ Retraining failed!")
        return False

if __name__ == "__main__":
    main()