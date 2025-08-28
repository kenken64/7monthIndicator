#!/usr/bin/env python3
"""
Lightweight RL Trading Agent

A simple yet effective Q-Learning based trading agent that doesn't require
heavy machine learning frameworks. Features include:

- Tabular Q-Learning with discretized market states
- Technical indicator integration (RSI, MACD, VWAP, EMA)
- Timing-aware state representation (market hours, days)
- Built-in trading simulator for training
- Model persistence and performance tracking
- Conservative risk management approach

The system learns from historical trading data to make informed decisions
while maintaining simplicity and transparency in its decision-making process.
"""

import numpy as np
import pandas as pd
import json
import pickle
from database import get_database
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Any
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleTradingAgent:
    """
    Simple Q-Learning agent for trading
    
    Implements tabular Q-learning with discretized market states for trading
    decision making. The agent learns optimal actions (BUY, SELL, HOLD, CLOSE)
    based on technical indicators and market timing patterns.
    
    Features:
    - State discretization of continuous market indicators
    - Epsilon-greedy exploration policy
    - Q-value updates using standard Q-learning formula
    - Model persistence for trained agents
    - Training statistics and performance tracking
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=0.1):
        """Initialize Q-Learning agent with hyperparameters
        
        Args:
            learning_rate: Learning rate for Q-value updates (default: 0.1)
            discount_factor: Future reward discount factor (default: 0.95)
            epsilon: Exploration rate for epsilon-greedy policy (default: 0.1)
        """
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        
        # Q-table: state -> action -> Q-value (tabular representation)
        self.q_table = {}
        
        # Action space: [HOLD, BUY, SELL, CLOSE] - all possible trading actions
        self.actions = ['HOLD', 'BUY', 'SELL', 'CLOSE']
        self.num_actions = len(self.actions)
        
        # Learning statistics for tracking training progress
        self.training_history = []
        self.total_episodes = 0
        
    def discretize_state(self, indicators: Dict) -> str:
        """Convert continuous indicators to discrete state with timing features"""
        
        # Get key indicators
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        macd_hist = indicators.get('macd_histogram', 0)
        price = indicators.get('price', 3.7)
        vwap = indicators.get('vwap', price)
        ema_9 = indicators.get('ema_9', price)
        ema_21 = indicators.get('ema_21', price)
        
        # Get timing features
        timestamp = indicators.get('timestamp')
        hour_state = 'unknown'
        day_state = 'unknown'
        session_state = 'unknown'
        
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                # Hour of day (market hours consideration)
                hour = dt.hour
                if 9 <= hour < 12:  # Morning session
                    hour_state = 'morning'
                elif 12 <= hour < 15:  # Midday session  
                    hour_state = 'midday'
                elif 15 <= hour < 17:  # Afternoon session
                    hour_state = 'afternoon'
                else:  # After hours/pre-market
                    hour_state = 'off_hours'
                
                # Day of week
                day = dt.weekday()  # 0=Monday, 6=Sunday
                if day < 5:  # Monday to Friday
                    day_state = 'weekday'
                else:  # Weekend
                    day_state = 'weekend'
                
                # Market session (combining hour and day)
                if day_state == 'weekday' and 9 <= hour < 16:
                    session_state = 'market_hours'
                else:
                    session_state = 'off_market'
                    
            except (ValueError, AttributeError) as e:
                # If timestamp parsing fails, use defaults
                pass
        
        # Discretize technical indicators
        rsi_state = 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'
        
        macd_state = 'bullish' if macd > 0 else 'bearish'
        macd_hist_state = 'rising' if macd_hist > 0 else 'falling'
        
        price_vs_vwap = 'above_vwap' if price > vwap else 'below_vwap'
        price_vs_ema9 = 'above_ema9' if price > ema_9 else 'below_ema9'
        price_vs_ema21 = 'above_ema21' if price > ema_21 else 'below_ema21'
        
        # Create enhanced state string with timing features
        state = f"{rsi_state}_{macd_state}_{macd_hist_state}_{price_vs_vwap}_{price_vs_ema9}_{price_vs_ema21}_{hour_state}_{session_state}"
        
        return state
    
    def get_action(self, state: str, training: bool = True) -> str:
        """Get action using epsilon-greedy policy"""
        
        if state not in self.q_table:
            self.q_table[state] = [0.0] * self.num_actions
        
        if training and random.random() < self.epsilon:
            # Exploration: random action
            action_idx = random.randint(0, self.num_actions - 1)
        else:
            # Exploitation: best action
            q_values = self.q_table[state]
            action_idx = np.argmax(q_values)
        
        return self.actions[action_idx]
    
    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """Update Q-value using Q-learning formula"""
        
        if state not in self.q_table:
            self.q_table[state] = [0.0] * self.num_actions
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0] * self.num_actions
        
        action_idx = self.actions.index(action)
        
        # Q-learning update
        current_q = self.q_table[state][action_idx]
        max_next_q = max(self.q_table[next_state])
        
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action_idx] = new_q
    
    def save_model(self, filename: str = 'rl_trading_model.pkl'):
        """Save Q-table to file"""
        model_data = {
            'q_table': self.q_table,
            'training_history': self.training_history,
            'total_episodes': self.total_episodes
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"💾 Model saved to {filename}")
    
    def load_model(self, filename: str = 'rl_trading_model.pkl'):
        """Load Q-table from file"""
        try:
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = model_data.get('q_table', {})
            self.training_history = model_data.get('training_history', [])
            self.total_episodes = model_data.get('total_episodes', 0)
            
            logger.info(f"📂 Model loaded from {filename}")
            logger.info(f"   States learned: {len(self.q_table)}")
            logger.info(f"   Episodes trained: {self.total_episodes}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"⚠️ Model file {filename} not found")
            return False

class TradingSimulator:
    """
    Simple trading simulator for RL training
    """
    
    def __init__(self, data: List[Dict]):
        self.data = data
        self.current_idx = 0
        self.position = None  # None, 'LONG', 'SHORT'
        self.entry_price = 0
        self.balance = 1000
        self.initial_balance = 1000
        self.trades_history = []
        
    def reset(self):
        """Reset simulator state"""
        self.current_idx = 20  # Start with enough history
        self.position = None
        self.entry_price = 0
        self.balance = 1000
        self.initial_balance = 1000
        self.trades_history = []
        
        return self.get_current_indicators()
    
    def get_current_indicators(self) -> Dict:
        """Get current market indicators"""
        if self.current_idx >= len(self.data):
            return {}
        
        return self.data[self.current_idx]
    
    def step(self, action: str) -> Tuple[Dict, float, bool]:
        """Execute action and return (next_state, reward, done)"""
        
        if self.current_idx >= len(self.data) - 1:
            return {}, 0, True
        
        current_price = self.data[self.current_idx].get('price', 3.7)
        reward = 0
        
        # Execute action
        if action == 'BUY' and not self.position:
            self.position = 'LONG'
            self.entry_price = current_price
            reward = -0.001  # Small transaction cost
            
        elif action == 'SELL' and not self.position:
            self.position = 'SHORT'
            self.entry_price = current_price
            reward = -0.001
            
        elif action == 'CLOSE' and self.position:
            # Close position and calculate reward
            if self.position == 'LONG':
                pnl_pct = (current_price - self.entry_price) / self.entry_price
            else:  # SHORT
                pnl_pct = (self.entry_price - current_price) / self.entry_price
            
            # Reward based on PnL
            if pnl_pct > 0:
                reward = pnl_pct * 50  # 50x reward for profits
            else:
                reward = pnl_pct * 100  # 100x penalty for losses (discourage losses)
            
            # Update balance
            pnl_amount = self.balance * 0.02 * pnl_pct  # 2% risk per trade
            self.balance += pnl_amount
            
            # Record trade
            self.trades_history.append({
                'entry_price': self.entry_price,
                'exit_price': current_price,
                'position': self.position,
                'pnl_pct': pnl_pct,
                'pnl_amount': pnl_amount
            })
            
            # Reset position
            self.position = None
            self.entry_price = 0
            
        elif action == 'HOLD':
            # Small penalty for holding (encourages action)
            reward = -0.0001
            
            # Additional penalty for holding losing positions
            if self.position and self.entry_price > 0:
                if self.position == 'LONG':
                    unrealized_pnl = (current_price - self.entry_price) / self.entry_price
                else:
                    unrealized_pnl = (self.entry_price - current_price) / self.entry_price
                
                if unrealized_pnl < -0.02:  # More than 2% loss
                    reward -= 0.001  # Extra penalty for holding losers
        
        # Move to next step
        self.current_idx += 1
        next_indicators = self.get_current_indicators()
        
        # Check if done
        done = (self.current_idx >= len(self.data) - 1) or (self.balance <= 500)
        
        return next_indicators, reward, done
    
    def get_performance_stats(self) -> Dict:
        """Calculate performance statistics"""
        if not self.trades_history:
            return {'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
        
        winning_trades = len([t for t in self.trades_history if t['pnl_pct'] > 0])
        total_trades = len(self.trades_history)
        win_rate = (winning_trades / total_trades) * 100
        total_pnl = sum([t['pnl_amount'] for t in self.trades_history])
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'final_balance': self.balance,
            'return_pct': ((self.balance - self.initial_balance) / self.initial_balance) * 100
        }

class LightweightRLSystem:
    """
    Complete lightweight RL trading system
    """
    
    def __init__(self):
        self.db = get_database()
        self.agent = SimpleTradingAgent()
        self.simulator = None
        
    def prepare_training_data(self) -> List[Dict]:
        """Prepare training data from database"""
        logger.info("📊 Preparing training data...")
        
        with self.db.get_connection() as conn:
            query = """
                SELECT timestamp, symbol, price, signal, strength, indicators
                FROM signals 
                ORDER BY timestamp
            """
            cursor = conn.execute(query)
            data = []
            
            for row in cursor.fetchall():
                row_dict = dict(row)
                
                # Parse indicators JSON
                if row_dict['indicators']:
                    indicators = json.loads(row_dict['indicators'])
                    row_dict.update(indicators)
                
                data.append(row_dict)
        
        logger.info(f"✅ Prepared {len(data)} data points")
        return data
    
    def train_agent(self, episodes: int = 100):
        """Train the RL agent"""
        logger.info(f"🤖 Training RL agent for {episodes} episodes...")
        
        training_data = self.prepare_training_data()
        self.simulator = TradingSimulator(training_data)
        
        best_performance = -float('inf')
        
        for episode in range(episodes):
            # Reset environment
            current_indicators = self.simulator.reset()
            current_state = self.agent.discretize_state(current_indicators)
            
            episode_reward = 0
            steps = 0
            
            while True:
                # Get action
                action = self.agent.get_action(current_state, training=True)
                
                # Execute action
                next_indicators, reward, done = self.simulator.step(action)
                
                if done or not next_indicators:
                    break
                
                next_state = self.agent.discretize_state(next_indicators)
                
                # Update Q-value
                self.agent.update_q_value(current_state, action, reward, next_state)
                
                # Move to next state
                current_state = next_state
                episode_reward += reward
                steps += 1
                
                if steps > 1000:  # Prevent infinite loops
                    break
            
            # Track performance
            performance = self.simulator.get_performance_stats()
            self.agent.training_history.append(performance)
            self.agent.total_episodes += 1
            
            # Log progress
            if episode % 10 == 0 or episode == episodes - 1:
                logger.info(f"Episode {episode+1}/{episodes}:")
                logger.info(f"  Reward: {episode_reward:.3f}")
                logger.info(f"  Trades: {performance['total_trades']}")
                logger.info(f"  Win Rate: {performance['win_rate']:.1f}%")
                logger.info(f"  Final Balance: ${performance.get('final_balance', 1000):.2f}")
                logger.info(f"  Return: {performance.get('return_pct', 0):.1f}%")
                
            # Save best model
            if performance.get('return_pct', 0) > best_performance:
                best_performance = performance['return_pct']
                self.agent.save_model()
        
        logger.info(f"🎉 Training complete! Best return: {best_performance:.1f}%")
        
        # Decay exploration
        self.agent.epsilon = max(0.01, self.agent.epsilon * 0.95)
        
        return self.agent.training_history
    
    def get_trading_recommendation(self, indicators: Dict) -> Dict:
        """Get trading recommendation from trained agent"""
        state = self.agent.discretize_state(indicators)
        action = self.agent.get_action(state, training=False)
        
        # Get Q-values for confidence
        confidence = 0.5
        if state in self.agent.q_table:
            q_values = self.agent.q_table[state]
            max_q = max(q_values)
            min_q = min(q_values)
            if max_q != min_q:
                confidence = (max_q - min_q) / (abs(max_q) + abs(min_q) + 1e-8)
        
        return {
            'action': action,
            'confidence': min(confidence, 1.0),
            'state': state,
            'trained': len(self.agent.q_table) > 0
        }
    
    def analyze_learned_patterns(self):
        """Analyze what the agent has learned"""
        if not self.agent.q_table:
            logger.warning("⚠️ No trained model to analyze")
            return
        
        logger.info("🔍 ANALYZING LEARNED PATTERNS:")
        logger.info(f"Total states learned: {len(self.agent.q_table)}")
        
        # Find best states for each action
        action_preferences = {action: [] for action in self.agent.actions}
        
        for state, q_values in self.agent.q_table.items():
            best_action_idx = np.argmax(q_values)
            best_action = self.agent.actions[best_action_idx]
            best_q_value = q_values[best_action_idx]
            
            action_preferences[best_action].append((state, best_q_value))
        
        # Show top states for each action
        for action, state_values in action_preferences.items():
            if state_values:
                state_values.sort(key=lambda x: x[1], reverse=True)
                logger.info(f"\n📊 Best {action} states:")
                
                for i, (state, q_val) in enumerate(state_values[:3]):
                    logger.info(f"  {i+1}. {state} (Q-value: {q_val:.3f})")

def main():
    """Train and test lightweight RL system"""
    rl_system = LightweightRLSystem()
    
    # Try to load existing model
    if not rl_system.agent.load_model():
        # Train new model
        logger.info("🚀 No existing model found. Starting fresh training...")
        training_history = rl_system.train_agent(episodes=50)
        
        # Show final training results
        if training_history:
            final_stats = training_history[-1]
            logger.info(f"\n🏆 FINAL TRAINING RESULTS:")
            logger.info(f"Win Rate: {final_stats['win_rate']:.1f}%")
            logger.info(f"Total Return: {final_stats['return_pct']:.1f}%")
            logger.info(f"Total Trades: {final_stats['total_trades']}")
    
    # Analyze learned patterns
    rl_system.analyze_learned_patterns()
    
    # Test with current market conditions
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
    logger.info(f"\n🤖 CURRENT RECOMMENDATION:")
    logger.info(f"Action: {recommendation['action']}")
    logger.info(f"Confidence: {recommendation['confidence']:.1%}")
    logger.info(f"Market State: {recommendation['state']}")
    
    return rl_system

if __name__ == "__main__":
    main()