#!/usr/bin/env python3
"""
Enhanced Reward System for RL Trading Bot

This module provides an advanced reward calculation system that goes beyond simple PnL
to incorporate risk-adjusted metrics, portfolio statistics, and behavioral incentives
for better trading performance.

Features:
- Risk-adjusted returns (Sharpe ratio components)
- Consecutive wins/losses tracking with streak bonuses/penalties
- Drawdown penalties for risk management
- Volatility-adjusted rewards
- Portfolio heat management
- Maximum adverse excursion (MAE) penalties
- Time-based reward decay for position holding
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradeMetrics:
    """Container for individual trade metrics"""
    pnl_pct: float
    pnl_amount: float
    entry_price: float
    exit_price: float
    position_type: str
    duration_minutes: int
    max_adverse_excursion: float  # Worst drawdown during trade
    max_favorable_excursion: float  # Best profit during trade
    volume_at_entry: float = 0.0
    volatility_at_entry: float = 0.0

@dataclass
class PortfolioMetrics:
    """Container for portfolio-level metrics"""
    total_return: float
    win_rate: float
    profit_factor: float  # Gross profit / Gross loss
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float
    consecutive_wins: int
    consecutive_losses: int
    total_trades: int
    avg_win_pct: float
    avg_loss_pct: float
    recent_volatility: float
    risk_free_rate: float = 0.02  # 2% annual risk-free rate

class EnhancedRewardCalculator:
    """
    Advanced reward calculation system for RL trading
    
    This class calculates rewards based on multiple factors:
    1. Base PnL reward/penalty
    2. Risk-adjusted performance (Sharpe ratio component)  
    3. Streak bonuses/penalties
    4. Drawdown management
    5. Volatility adjustment
    6. Time decay factors
    """
    
    def __init__(self):
        self.trade_history: List[TradeMetrics] = []
        self.portfolio_metrics = PortfolioMetrics(
            total_return=0.0, win_rate=0.0, profit_factor=1.0, 
            sharpe_ratio=0.0, max_drawdown=0.0, current_drawdown=0.0,
            consecutive_wins=0, consecutive_losses=0, total_trades=0,
            avg_win_pct=0.0, avg_loss_pct=0.0, recent_volatility=0.02
        )
        
        # Reward system parameters
        self.base_reward_multiplier = 50.0
        self.base_penalty_multiplier = 75.0  # Asymmetric - penalize losses more
        self.streak_bonus_cap = 2.5
        self.drawdown_penalty_multiplier = 3.0
        self.volatility_adjustment_factor = 1.5
        self.time_decay_factor = 0.95  # Per hour holding penalty
        
    def calculate_enhanced_reward(
        self, 
        trade_metrics: Optional[TradeMetrics] = None,
        action: str = "HOLD",
        current_position_duration: int = 0,
        market_indicators: Dict = None
    ) -> float:
        """
        Calculate enhanced reward based on multiple factors
        
        Args:
            trade_metrics: Metrics for completed trade (None for HOLD/entry actions)
            action: Current action taken (BUY, SELL, CLOSE, HOLD)
            current_position_duration: Minutes holding current position
            market_indicators: Current market state for context
        
        Returns:
            Enhanced reward value
        """
        if market_indicators is None:
            market_indicators = {}
            
        # Base reward calculation
        base_reward = 0.0
        
        if trade_metrics:
            # Trade completed - calculate comprehensive reward
            base_reward = self._calculate_trade_reward(trade_metrics)
            self.trade_history.append(trade_metrics)
            self._update_portfolio_metrics()
            
        elif action == "HOLD":
            # Holding position - apply time decay and risk penalties
            base_reward = self._calculate_hold_reward(current_position_duration, market_indicators)
            
        elif action in ["BUY", "SELL"]:
            # Entry action - small transaction cost with opportunity bonus
            base_reward = self._calculate_entry_reward(action, market_indicators)
            
        # Apply additional reward components
        enhanced_reward = self._apply_reward_enhancements(base_reward, action, market_indicators)
        
        return enhanced_reward
    
    def _calculate_trade_reward(self, trade: TradeMetrics) -> float:
        """Calculate base reward for completed trade"""
        
        # Base PnL reward
        if trade.pnl_pct > 0:
            base_reward = trade.pnl_pct * self.base_reward_multiplier
        else:
            base_reward = trade.pnl_pct * self.base_penalty_multiplier
            
        # Risk-adjusted component (reward efficiency)
        risk_adjustment = self._calculate_risk_adjustment(trade)
        
        # Maximum Adverse Excursion penalty (reward risk management)
        mae_penalty = min(0, trade.max_adverse_excursion * 10)  # Penalize large drawdowns
        
        # Duration efficiency bonus/penalty
        duration_factor = self._calculate_duration_factor(trade)
        
        total_reward = (base_reward + risk_adjustment + mae_penalty) * duration_factor
        
        logger.debug(f"Trade reward components: base={base_reward:.4f}, risk_adj={risk_adjustment:.4f}, "
                    f"mae_penalty={mae_penalty:.4f}, duration_factor={duration_factor:.4f}")
                    
        return total_reward
    
    def _calculate_risk_adjustment(self, trade: TradeMetrics) -> float:
        """Calculate risk-adjusted reward component"""
        
        # Reward trades that perform well relative to market volatility
        if trade.volatility_at_entry > 0:
            volatility_adjusted_return = trade.pnl_pct / trade.volatility_at_entry
            risk_bonus = volatility_adjusted_return * 5.0
        else:
            risk_bonus = 0.0
            
        # Bonus for favorable risk/reward ratio
        if trade.max_favorable_excursion > 0 and trade.max_adverse_excursion < 0:
            risk_reward_ratio = trade.max_favorable_excursion / abs(trade.max_adverse_excursion)
            if risk_reward_ratio > 2.0:  # At least 2:1 risk/reward achieved
                risk_bonus += 0.1 * min(risk_reward_ratio, 5.0)  # Cap bonus
                
        return risk_bonus
    
    def _calculate_duration_factor(self, trade: TradeMetrics) -> float:
        """Calculate duration-based reward factor"""
        
        # Encourage quick profits, penalize holding losers
        if trade.pnl_pct > 0:
            # Bonus for quick wins (within 1 hour)
            if trade.duration_minutes <= 60:
                return 1.2
            # Slight penalty for very long winners (opportunity cost)
            elif trade.duration_minutes > 240:  # 4 hours
                return 0.9
            else:
                return 1.0
        else:
            # Penalty increases with duration for losing trades
            hours_held = trade.duration_minutes / 60.0
            return max(0.5, 1.0 - (hours_held * 0.1))  # -10% per hour, min 50%
    
    def _calculate_hold_reward(self, duration_minutes: int, market_indicators: Dict) -> float:
        """Calculate reward for holding position"""
        
        # Base holding cost (encourages action)
        base_cost = -0.0001
        
        # Time decay penalty (increases with duration)  
        hours_held = duration_minutes / 60.0
        time_penalty = -0.001 * (hours_held ** 1.2)  # Exponential increase
        
        # Market condition penalty (holding in adverse conditions)
        market_penalty = 0.0
        rsi = market_indicators.get('rsi', 50)
        if rsi > 80 or rsi < 20:  # Extreme RSI - action likely needed
            market_penalty = -0.0005
            
        return base_cost + time_penalty + market_penalty
    
    def _calculate_entry_reward(self, action: str, market_indicators: Dict) -> float:
        """Calculate reward for entry actions"""
        
        # Base transaction cost
        base_cost = -0.001
        
        # Opportunity bonus for entering in good conditions
        opportunity_bonus = 0.0
        rsi = market_indicators.get('rsi', 50)
        
        if action == "BUY" and rsi < 35:  # Buying oversold
            opportunity_bonus = 0.0005
        elif action == "SELL" and rsi > 65:  # Selling overbought  
            opportunity_bonus = 0.0005
            
        return base_cost + opportunity_bonus
    
    def _apply_reward_enhancements(self, base_reward: float, action: str, market_indicators: Dict) -> float:
        """Apply additional reward enhancements based on portfolio state"""
        
        enhanced_reward = base_reward
        
        # Streak bonuses/penalties
        streak_factor = self._calculate_streak_factor()
        enhanced_reward *= streak_factor
        
        # Drawdown penalty
        drawdown_penalty = self._calculate_drawdown_penalty()
        enhanced_reward += drawdown_penalty
        
        # Portfolio heat penalty (risk management)
        heat_penalty = self._calculate_portfolio_heat_penalty()
        enhanced_reward += heat_penalty
        
        # Sharpe ratio bonus (reward consistent performance)
        sharpe_bonus = self.portfolio_metrics.sharpe_ratio * 0.01
        enhanced_reward += sharpe_bonus
        
        logger.debug(f"Reward enhancements: streak_factor={streak_factor:.3f}, "
                    f"drawdown_penalty={drawdown_penalty:.4f}, heat_penalty={heat_penalty:.4f}, "
                    f"sharpe_bonus={sharpe_bonus:.4f}")
        
        return enhanced_reward
    
    def _calculate_streak_factor(self) -> float:
        """Calculate streak-based reward multiplier"""
        
        if self.portfolio_metrics.consecutive_wins > 0:
            # Bonus for winning streaks (compound growth simulation)
            streak_bonus = min(self.streak_bonus_cap, 
                             1.0 + (self.portfolio_metrics.consecutive_wins * 0.15))
            return streak_bonus
            
        elif self.portfolio_metrics.consecutive_losses > 0:
            # Penalty for losing streaks (prevent blowups)
            streak_penalty = max(0.4, 
                               1.0 - (self.portfolio_metrics.consecutive_losses * 0.1))
            return streak_penalty
            
        return 1.0
    
    def _calculate_drawdown_penalty(self) -> float:
        """Calculate penalty based on current drawdown"""
        
        if self.portfolio_metrics.current_drawdown > 0.05:  # >5% drawdown
            penalty = -self.portfolio_metrics.current_drawdown * self.drawdown_penalty_multiplier
            return penalty
        return 0.0
    
    def _calculate_portfolio_heat_penalty(self) -> float:
        """Calculate penalty for excessive portfolio risk"""
        
        # Simple risk measure - recent volatility vs returns
        if self.portfolio_metrics.recent_volatility > 0.05:  # >5% volatility
            if self.portfolio_metrics.total_return < self.portfolio_metrics.recent_volatility:
                # Poor risk-adjusted performance
                return -0.005
        return 0.0
    
    def _update_portfolio_metrics(self):
        """Update portfolio-level metrics after new trade"""
        
        if not self.trade_history:
            return
            
        # Calculate basic metrics
        returns = [trade.pnl_pct for trade in self.trade_history]
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]
        
        self.portfolio_metrics.total_trades = len(self.trade_history)
        self.portfolio_metrics.win_rate = len(winning_trades) / len(returns) if returns else 0
        
        if winning_trades:
            self.portfolio_metrics.avg_win_pct = np.mean(winning_trades)
        if losing_trades:
            self.portfolio_metrics.avg_loss_pct = np.mean(losing_trades)
            
        # Profit factor
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 1  # Avoid division by zero
        self.portfolio_metrics.profit_factor = gross_profit / gross_loss
        
        # Total return (compound)
        self.portfolio_metrics.total_return = np.prod([1 + r for r in returns]) - 1
        
        # Sharpe ratio (simplified)
        if len(returns) > 1:
            excess_return = np.mean(returns) - (self.portfolio_metrics.risk_free_rate / 252)
            volatility = np.std(returns)
            self.portfolio_metrics.sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
        # Drawdown calculations
        cumulative_returns = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        
        self.portfolio_metrics.max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        self.portfolio_metrics.current_drawdown = abs(drawdown[-1]) if len(drawdown) > 0 else 0
        
        # Streak calculations
        self._update_streaks()
        
        # Recent volatility (last 10 trades)
        recent_returns = returns[-10:] if len(returns) >= 10 else returns
        self.portfolio_metrics.recent_volatility = np.std(recent_returns) if len(recent_returns) > 1 else 0.02
    
    def _update_streaks(self):
        """Update consecutive wins/losses streaks"""
        
        if not self.trade_history:
            return
            
        # Count from the end
        consecutive_wins = 0
        consecutive_losses = 0
        
        for trade in reversed(self.trade_history):
            if trade.pnl_pct > 0:
                if consecutive_losses > 0:
                    break
                consecutive_wins += 1
            elif trade.pnl_pct < 0:
                if consecutive_wins > 0:
                    break
                consecutive_losses += 1
            else:  # Break even trades reset streaks
                break
                
        self.portfolio_metrics.consecutive_wins = consecutive_wins
        self.portfolio_metrics.consecutive_losses = consecutive_losses
    
    def get_reward_breakdown(self) -> Dict:
        """Get detailed breakdown of last reward calculation for debugging"""
        
        return {
            'portfolio_metrics': {
                'total_return': self.portfolio_metrics.total_return,
                'win_rate': self.portfolio_metrics.win_rate,
                'sharpe_ratio': self.portfolio_metrics.sharpe_ratio,
                'max_drawdown': self.portfolio_metrics.max_drawdown,
                'consecutive_wins': self.portfolio_metrics.consecutive_wins,
                'consecutive_losses': self.portfolio_metrics.consecutive_losses,
                'profit_factor': self.portfolio_metrics.profit_factor
            },
            'recent_trades': len(self.trade_history),
            'parameters': {
                'base_reward_multiplier': self.base_reward_multiplier,
                'base_penalty_multiplier': self.base_penalty_multiplier,
                'streak_bonus_cap': self.streak_bonus_cap
            }
        }

    def reset_metrics(self):
        """Reset all metrics for new training episode"""
        self.trade_history.clear()
        self.portfolio_metrics = PortfolioMetrics(
            total_return=0.0, win_rate=0.0, profit_factor=1.0, 
            sharpe_ratio=0.0, max_drawdown=0.0, current_drawdown=0.0,
            consecutive_wins=0, consecutive_losses=0, total_trades=0,
            avg_win_pct=0.0, avg_loss_pct=0.0, recent_volatility=0.02
        )