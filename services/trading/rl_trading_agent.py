#!/usr/bin/env python3
"""
Reinforcement Learning Trading Agent
Using PPO to learn optimal trading strategies from historical failures
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import gym
from gym import spaces
from database import get_database
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingEnvironment(gym.Env):
    """
    Trading Environment for RL Agent
    State: Technical indicators + position info
    Actions: HOLD, BUY_SMALL, BUY_LARGE, SELL_SMALL, SELL_LARGE, CLOSE
    Reward: Profit/Loss with risk penalties
    """
    
    def __init__(self, historical_data: pd.DataFrame):
        super(TradingEnvironment, self).__init__()
        
        self.data = historical_data.reset_index(drop=True)
        self.current_step = 0
        self.max_steps = len(self.data) - 1
        
        # Trading state
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.position_size = 0
        self.entry_price = 0
        self.balance = 1000  # Starting balance
        self.max_risk_per_trade = 0.02  # 2% max risk per trade
        
        # Action space: [HOLD, BUY_SMALL, BUY_LARGE, SELL_SMALL, SELL_LARGE, CLOSE]
        self.action_space = spaces.Discrete(6)
        
        # State space: 15 features (technical indicators + position info)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(15,), dtype=np.float32
        )
        
        # Track performance
        self.trades_history = []
        self.total_reward = 0
        
    def reset(self):
        """Reset environment to initial state"""
        self.current_step = 50  # Start after enough data for indicators
        self.position = 0
        self.position_size = 0
        self.entry_price = 0
        self.balance = 1000
        self.total_reward = 0
        self.trades_history = []
        
        return self._get_observation()
    
    def _get_observation(self) -> np.ndarray:
        """Get current state observation"""
        if self.current_step >= len(self.data):
            self.current_step = len(self.data) - 1
            
        row = self.data.iloc[self.current_step]
        
        # Technical indicators (normalized)
        current_price = row['price']
        obs = [
            (row.get('rsi', 50) - 50) / 50,  # RSI normalized to [-1, 1]
            row.get('macd', 0) / current_price,  # MACD normalized by price
            row.get('macd_histogram', 0) / current_price,
            (row.get('ema_9', current_price) - current_price) / current_price,
            (row.get('ema_21', current_price) - current_price) / current_price,
            (row.get('ema_50', current_price) - current_price) / current_price,
            (row.get('ema_200', current_price) - current_price) / current_price,
            (row.get('vwap', current_price) - current_price) / current_price,
            
            # Position information
            self.position,  # Current position: -1, 0, 1
            self.position_size / 1000 if self.position_size > 0 else 0,  # Normalized position size
            
            # Risk metrics
            (current_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0,  # Unrealized P&L
            self.balance / 1000,  # Normalized balance
            
            # Market context
            row.get('signal_strength', 0) / 10,  # Original signal strength normalized
            row.get('volatility', 0.01) / 0.05,  # Volatility normalized
            (self.current_step % 24) / 24  # Time of day normalized
        ]
        
        return np.array(obs, dtype=np.float32)
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and return new state, reward, done, info"""
        
        reward = 0
        info = {}
        
        if self.current_step >= self.max_steps:
            return self._get_observation(), reward, True, info
        
        current_price = self.data.iloc[self.current_step]['price']
        
        # Execute action
        if action == 0:  # HOLD
            reward = -0.001  # Small cost for holding (encourages action)
            
        elif action == 1:  # BUY_SMALL
            if self.position <= 0:  # Can buy if not already long
                reward = self._execute_trade('BUY', 0.01, current_price)  # 1% of balance
                
        elif action == 2:  # BUY_LARGE  
            if self.position <= 0:
                reward = self._execute_trade('BUY', 0.02, current_price)  # 2% of balance
                
        elif action == 3:  # SELL_SMALL
            if self.position >= 0:  # Can sell if not already short
                reward = self._execute_trade('SELL', 0.01, current_price)
                
        elif action == 4:  # SELL_LARGE
            if self.position >= 0:
                reward = self._execute_trade('SELL', 0.02, current_price)
                
        elif action == 5:  # CLOSE
            if self.position != 0:
                reward = self._close_position(current_price)
        
        # Risk penalty for holding losing positions too long
        if self.position != 0 and self.entry_price > 0:
            unrealized_pnl_pct = ((current_price - self.entry_price) / self.entry_price) * self.position
            if unrealized_pnl_pct < -0.05:  # More than 5% loss
                reward -= 0.01  # Additional penalty
        
        self.current_step += 1
        self.total_reward += reward
        
        done = self.current_step >= self.max_steps or self.balance <= 500  # Stop if 50% drawdown
        
        return self._get_observation(), reward, done, info
    
    def _execute_trade(self, side: str, risk_percent: float, price: float) -> float:
        """Execute a trade and return reward"""
        
        # Close existing position first if opposite direction
        if (side == 'BUY' and self.position < 0) or (side == 'SELL' and self.position > 0):
            close_reward = self._close_position(price)
        else:
            close_reward = 0
        
        # Calculate position size based on risk
        risk_amount = self.balance * risk_percent
        position_size = risk_amount / price  # Simplified, ignoring leverage
        
        # Update position
        if side == 'BUY':
            self.position = 1
            self.position_size = position_size
        else:  # SELL
            self.position = -1
            self.position_size = position_size
            
        self.entry_price = price
        
        # Small negative reward for transaction cost
        transaction_reward = -0.002
        
        return close_reward + transaction_reward
    
    def _close_position(self, current_price: float) -> float:
        """Close current position and return reward"""
        if self.position == 0 or self.entry_price == 0:
            return 0
        
        # Calculate P&L
        if self.position > 0:  # Long position
            pnl_pct = (current_price - self.entry_price) / self.entry_price
        else:  # Short position  
            pnl_pct = (self.entry_price - current_price) / self.entry_price
        
        pnl_amount = self.balance * 0.02 * pnl_pct  # Assuming 2% risk per trade
        
        # Update balance
        self.balance += pnl_amount
        
        # Record trade
        self.trades_history.append({
            'entry_price': self.entry_price,
            'exit_price': current_price,
            'side': 'LONG' if self.position > 0 else 'SHORT',
            'pnl': pnl_amount,
            'pnl_pct': pnl_pct
        })
        
        # Reset position
        self.position = 0
        self.position_size = 0
        self.entry_price = 0
        
        # Reward structure: 
        # - Positive PnL gets positive reward (scaled)
        # - Negative PnL gets negative reward (heavily penalized)
        if pnl_pct > 0:
            reward = pnl_pct * 10  # 10x multiplier for profits
        else:
            reward = pnl_pct * 20  # 20x penalty for losses
        
        return reward

class PPOAgent:
    """
    Proximal Policy Optimization Agent for Trading
    """
    
    def __init__(self, state_dim: int, action_dim: int, lr: float = 3e-4):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        
        # Networks
        self.policy_net = self._build_network(state_dim, action_dim, 'policy')
        self.value_net = self._build_network(state_dim, 1, 'value')
        
        # Optimizers
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=lr)
        
        # PPO hyperparameters
        self.eps_clip = 0.2
        self.gamma = 0.99
        self.lamda = 0.95
        
    def _build_network(self, input_dim: int, output_dim: int, network_type: str):
        """Build neural network"""
        if network_type == 'policy':
            return nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim),
                nn.Softmax(dim=-1)
            )
        else:  # value network
            return nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim)
            )
    
    def get_action(self, state: np.ndarray) -> Tuple[int, float]:
        """Select action using current policy"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        with torch.no_grad():
            action_probs = self.policy_net(state_tensor)
            dist = Categorical(action_probs)
            action = dist.sample()
            
        return action.item(), dist.log_prob(action).item()
    
    def update(self, states: List[np.ndarray], actions: List[int], 
               rewards: List[float], log_probs: List[float]):
        """Update policy using PPO"""
        
        # Convert to tensors
        states_tensor = torch.FloatTensor(states)
        actions_tensor = torch.LongTensor(actions)
        rewards_tensor = torch.FloatTensor(rewards)
        old_log_probs = torch.FloatTensor(log_probs)
        
        # Calculate advantages
        values = self.value_net(states_tensor).squeeze()
        advantages = self._calculate_advantages(rewards, values.detach().numpy())
        advantages_tensor = torch.FloatTensor(advantages)
        
        # Normalize advantages
        advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (advantages_tensor.std() + 1e-8)
        
        # PPO update
        for _ in range(4):  # Multiple epochs
            # Policy update
            action_probs = self.policy_net(states_tensor)
            dist = Categorical(action_probs)
            new_log_probs = dist.log_prob(actions_tensor)
            
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages_tensor
            surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantages_tensor
            policy_loss = -torch.min(surr1, surr2).mean()
            
            self.policy_optimizer.zero_grad()
            policy_loss.backward()
            self.policy_optimizer.step()
            
            # Value update
            value_loss = nn.MSELoss()(values, torch.FloatTensor(rewards))
            
            self.value_optimizer.zero_grad()
            value_loss.backward()
            self.value_optimizer.step()
    
    def _calculate_advantages(self, rewards: List[float], values: np.ndarray) -> List[float]:
        """Calculate GAE advantages"""
        advantages = []
        advantage = 0
        
        for i in reversed(range(len(rewards))):
            if i == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[i + 1]
                
            delta = rewards[i] + self.gamma * next_value - values[i]
            advantage = delta + self.gamma * self.lamda * advantage
            advantages.insert(0, advantage)
            
        return advantages

class RLTradingSystem:
    """
    Complete RL Trading System
    """
    
    def __init__(self):
        self.db = get_database()
        self.agent = None
        self.env = None
        
    def prepare_training_data(self) -> pd.DataFrame:
        """Prepare historical data for training"""
        logger.info("📊 Preparing training data from database...")
        
        with self.db.get_connection() as conn:
            # Get signals with indicators
            query = """
                SELECT timestamp, symbol, price, signal, strength, indicators
                FROM signals 
                ORDER BY timestamp
            """
            cursor = conn.execute(query)
            data = [dict(row) for row in cursor.fetchall()]
        
        if not data:
            raise ValueError("No training data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Parse indicators
        for i, row in df.iterrows():
            if row['indicators']:
                indicators = json.loads(row['indicators']) if isinstance(row['indicators'], str) else row['indicators']
                for key, value in indicators.items():
                    df.at[i, key] = value
        
        # Add volatility and other features
        df['volatility'] = df['price'].pct_change().rolling(10).std()
        df = df.fillna(method='bfill').fillna(0)
        
        logger.info(f"✅ Prepared {len(df)} data points for training")
        return df
    
    def train_agent(self, episodes: int = 100):
        """Train the RL agent"""
        logger.info(f"🤖 Starting RL training for {episodes} episodes...")
        
        # Prepare data
        training_data = self.prepare_training_data()
        
        # Initialize environment and agent
        self.env = TradingEnvironment(training_data)
        self.agent = PPOAgent(
            state_dim=self.env.observation_space.shape[0],
            action_dim=self.env.action_space.n
        )
        
        best_reward = -float('inf')
        rewards_history = []
        
        for episode in range(episodes):
            state = self.env.reset()
            episode_reward = 0
            episode_states = []
            episode_actions = []
            episode_rewards = []
            episode_log_probs = []
            
            done = False
            while not done:
                action, log_prob = self.agent.get_action(state)
                next_state, reward, done, _ = self.env.step(action)
                
                episode_states.append(state)
                episode_actions.append(action)
                episode_rewards.append(reward)
                episode_log_probs.append(log_prob)
                
                episode_reward += reward
                state = next_state
            
            # Update agent
            self.agent.update(episode_states, episode_actions, episode_rewards, episode_log_probs)
            
            rewards_history.append(episode_reward)
            
            if episode_reward > best_reward:
                best_reward = episode_reward
                # Save best model
                torch.save(self.agent.policy_net.state_dict(), 'best_policy_model.pth')
                torch.save(self.agent.value_net.state_dict(), 'best_value_model.pth')
            
            if episode % 10 == 0:
                avg_reward = np.mean(rewards_history[-10:])
                trades_count = len(self.env.trades_history)
                win_rate = len([t for t in self.env.trades_history if t['pnl'] > 0]) / max(trades_count, 1) * 100
                
                logger.info(f"Episode {episode}: Avg Reward: {avg_reward:.3f}, Trades: {trades_count}, Win Rate: {win_rate:.1f}%")
        
        logger.info(f"🎉 Training complete! Best reward: {best_reward:.3f}")
        return rewards_history
    
    def load_trained_agent(self):
        """Load pre-trained agent"""
        try:
            self.agent = PPOAgent(15, 6)  # State dim, action dim
            self.agent.policy_net.load_state_dict(torch.load('best_policy_model.pth'))
            self.agent.value_net.load_state_dict(torch.load('best_value_model.pth'))
            logger.info("✅ Loaded pre-trained RL agent")
            return True
        except FileNotFoundError:
            logger.warning("⚠️ No pre-trained model found")
            return False
    
    def get_rl_action(self, indicators: Dict) -> Dict:
        """Get action from trained RL agent"""
        if not self.agent:
            return {'action': 'HOLD', 'confidence': 0}
        
        # Convert indicators to state vector
        state = self._indicators_to_state(indicators)
        action, _ = self.agent.get_action(state)
        
        action_names = ['HOLD', 'BUY_SMALL', 'BUY_LARGE', 'SELL_SMALL', 'SELL_LARGE', 'CLOSE']
        
        return {
            'action': action_names[action],
            'confidence': 0.8,  # Could calculate confidence from action probabilities
            'raw_action': action
        }
    
    def _indicators_to_state(self, indicators: Dict) -> np.ndarray:
        """Convert indicators dictionary to state vector"""
        current_price = indicators.get('price', 3.7)
        
        state = [
            (indicators.get('rsi', 50) - 50) / 50,
            indicators.get('macd', 0) / current_price,
            indicators.get('macd_histogram', 0) / current_price,
            (indicators.get('ema_9', current_price) - current_price) / current_price,
            (indicators.get('ema_21', current_price) - current_price) / current_price,
            (indicators.get('ema_50', current_price) - current_price) / current_price,
            (indicators.get('ema_200', current_price) - current_price) / current_price,
            (indicators.get('vwap', current_price) - current_price) / current_price,
            0,  # Position (would come from trading bot state)
            0,  # Position size
            0,  # Unrealized P&L
            1,  # Normalized balance
            indicators.get('signal_strength', 0) / 10,
            0.01 / 0.05,  # Default volatility
            (datetime.now().hour % 24) / 24
        ]
        
        return np.array(state, dtype=np.float32)

def main():
    """Train and test RL trading agent"""
    rl_system = RLTradingSystem()
    
    # Train the agent
    rewards_history = rl_system.train_agent(episodes=50)
    
    logger.info("🎯 Training Results:")
    logger.info(f"Final avg reward: {np.mean(rewards_history[-10:]):.3f}")
    
    # Test trained agent
    test_indicators = {
        'rsi': 45,
        'macd': -0.01,
        'macd_histogram': 0.005,
        'ema_9': 3.65,
        'ema_21': 3.67,
        'price': 3.68,
        'vwap': 3.70
    }
    
    rl_action = rl_system.get_rl_action(test_indicators)
    logger.info(f"🤖 RL Action recommendation: {rl_action}")

if __name__ == "__main__":
    main()