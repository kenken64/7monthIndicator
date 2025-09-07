#!/usr/bin/env python3
"""
Cross-Asset Correlation Module for Enhanced RL Trading Bot

This module provides market context awareness by analyzing correlations
and relationships between different crypto assets. It enhances the RL agent's
decision-making by incorporating broader market trends.

Features:
- BTC dominance and correlation analysis
- ETH-BTC relationship tracking  
- Market sentiment indicators
- Volatility regime detection
- Cross-asset momentum signals
"""

import numpy as np
import pandas as pd
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
import time

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Container for market context data"""
    btc_price: float
    btc_change_24h: float
    btc_dominance: float
    eth_price: float  
    eth_change_24h: float
    fear_greed_index: int
    volatility_regime: str  # 'low', 'medium', 'high'
    market_trend: str      # 'bullish', 'bearish', 'neutral'
    correlation_signal: str # 'positive', 'negative', 'neutral'
    timestamp: datetime

@dataclass
class CrossAssetSignal:
    """Cross-asset signal for enhanced state representation"""
    btc_trend: str        # 'up', 'down', 'sideways'
    eth_btc_ratio: str    # 'outperform', 'underperform', 'neutral'
    market_breadth: str   # 'strong', 'weak', 'neutral'  
    volatility_state: str # 'expanding', 'contracting', 'stable'
    regime_signal: str    # 'risk_on', 'risk_off', 'transition'

class CrossAssetAnalyzer:
    """
    Analyzes cross-asset relationships and market context for enhanced RL decisions
    """
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
        self.last_update = None
        self.cached_context = None
        self.price_history = {}
        
    def get_market_context(self) -> Optional[MarketContext]:
        """Get current market context with caching"""
        
        current_time = datetime.now()
        
        # Return cached data if still valid
        if (self.cached_context and self.last_update and 
            (current_time - self.last_update).seconds < self.cache_duration):
            return self.cached_context
        
        try:
            # Fetch BTC and ETH data from CoinGecko API
            btc_data = self._fetch_coingecko_data('bitcoin')
            eth_data = self._fetch_coingecko_data('ethereum')
            
            if not btc_data or not eth_data:
                logger.warning("Failed to fetch market data")
                return self.cached_context  # Return cached if available
            
            # Get BTC dominance
            btc_dominance = self._fetch_btc_dominance()
            
            # Get Fear & Greed Index
            fear_greed = self._fetch_fear_greed_index()
            
            # Calculate volatility regime
            volatility_regime = self._calculate_volatility_regime(btc_data)
            
            # Determine market trend
            market_trend = self._determine_market_trend(btc_data, eth_data)
            
            # Calculate correlation signal
            correlation_signal = self._calculate_correlation_signal(btc_data, eth_data)
            
            # Store price history for trend analysis
            self._update_price_history(btc_data, eth_data)
            
            market_context = MarketContext(
                btc_price=btc_data['current_price'],
                btc_change_24h=btc_data['price_change_percentage_24h'],
                btc_dominance=btc_dominance,
                eth_price=eth_data['current_price'],
                eth_change_24h=eth_data['price_change_percentage_24h'],
                fear_greed_index=fear_greed,
                volatility_regime=volatility_regime,
                market_trend=market_trend,
                correlation_signal=correlation_signal,
                timestamp=current_time
            )
            
            # Update cache
            self.cached_context = market_context
            self.last_update = current_time
            
            logger.info(f"Updated market context: BTC ${btc_data['current_price']:.0f} "
                       f"({btc_data['price_change_percentage_24h']:.1f}%), "
                       f"Dominance: {btc_dominance:.1f}%, Trend: {market_trend}")
            
            return market_context
            
        except Exception as e:
            logger.error(f"Error fetching market context: {e}")
            return self.cached_context
    
    def generate_cross_asset_signal(self, sui_price: float, sui_indicators: Dict) -> CrossAssetSignal:
        """Generate cross-asset signal for enhanced state representation"""
        
        market_context = self.get_market_context()
        
        if not market_context:
            # Fallback signal when market data unavailable
            return CrossAssetSignal(
                btc_trend='unknown',
                eth_btc_ratio='unknown', 
                market_breadth='unknown',
                volatility_state='unknown',
                regime_signal='unknown'
            )
        
        # Analyze BTC trend
        btc_trend = self._analyze_btc_trend(market_context)
        
        # Analyze ETH/BTC ratio performance
        eth_btc_ratio = self._analyze_eth_btc_ratio(market_context)
        
        # Assess market breadth
        market_breadth = self._assess_market_breadth(market_context)
        
        # Determine volatility state
        volatility_state = self._determine_volatility_state(market_context)
        
        # Classify market regime
        regime_signal = self._classify_market_regime(market_context)
        
        return CrossAssetSignal(
            btc_trend=btc_trend,
            eth_btc_ratio=eth_btc_ratio,
            market_breadth=market_breadth,
            volatility_state=volatility_state,
            regime_signal=regime_signal
        )
    
    def _fetch_coingecko_data(self, coin_id: str) -> Optional[Dict]:
        """Fetch coin data from CoinGecko API"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return {
                        'current_price': data[coin_id]['usd'],
                        'price_change_percentage_24h': data[coin_id].get('usd_24h_change', 0),
                        'volume_24h': data[coin_id].get('usd_24h_vol', 0)
                    }
            else:
                logger.warning(f"CoinGecko API returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching {coin_id} data: {e}")
            
        return None
    
    def _fetch_btc_dominance(self) -> float:
        """Fetch Bitcoin dominance percentage"""
        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                dominance = data['data']['market_cap_percentage'].get('btc', 50.0)
                return float(dominance)
                
        except Exception as e:
            logger.error(f"Error fetching BTC dominance: {e}")
            
        return 50.0  # Default fallback
    
    def _fetch_fear_greed_index(self) -> int:
        """Fetch Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    return int(data['data'][0]['value'])
                    
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
            
        return 50  # Neutral fallback
    
    def _calculate_volatility_regime(self, btc_data: Dict) -> str:
        """Calculate volatility regime based on price changes"""
        change_24h = abs(btc_data['price_change_percentage_24h'])
        
        if change_24h > 8.0:
            return 'high'
        elif change_24h > 3.0:
            return 'medium'
        else:
            return 'low'
    
    def _determine_market_trend(self, btc_data: Dict, eth_data: Dict) -> str:
        """Determine overall market trend"""
        btc_change = btc_data['price_change_percentage_24h']
        eth_change = eth_data['price_change_percentage_24h']
        
        avg_change = (btc_change + eth_change) / 2
        
        if avg_change > 2.0:
            return 'bullish'
        elif avg_change < -2.0:
            return 'bearish'
        else:
            return 'neutral'
    
    def _calculate_correlation_signal(self, btc_data: Dict, eth_data: Dict) -> str:
        """Calculate correlation signal between BTC and ETH"""
        btc_change = btc_data['price_change_percentage_24h']
        eth_change = eth_data['price_change_percentage_24h']
        
        # Simple correlation logic based on direction
        if (btc_change > 0 and eth_change > 0) or (btc_change < 0 and eth_change < 0):
            return 'positive'
        elif abs(btc_change) < 1.0 and abs(eth_change) < 1.0:
            return 'neutral'
        else:
            return 'negative'
    
    def _update_price_history(self, btc_data: Dict, eth_data: Dict):
        """Update price history for trend analysis"""
        timestamp = datetime.now()
        
        if 'btc' not in self.price_history:
            self.price_history['btc'] = []
        if 'eth' not in self.price_history:
            self.price_history['eth'] = []
        
        self.price_history['btc'].append({
            'timestamp': timestamp,
            'price': btc_data['current_price'],
            'change_24h': btc_data['price_change_percentage_24h']
        })
        
        self.price_history['eth'].append({
            'timestamp': timestamp,
            'price': eth_data['current_price'],
            'change_24h': eth_data['price_change_percentage_24h']
        })
        
        # Keep only last 100 entries
        self.price_history['btc'] = self.price_history['btc'][-100:]
        self.price_history['eth'] = self.price_history['eth'][-100:]
    
    def _analyze_btc_trend(self, context: MarketContext) -> str:
        """Analyze BTC trend direction"""
        if context.btc_change_24h > 2.0:
            return 'up_strong'
        elif context.btc_change_24h > 0.5:
            return 'up_weak'
        elif context.btc_change_24h < -2.0:
            return 'down_strong'
        elif context.btc_change_24h < -0.5:
            return 'down_weak'
        else:
            return 'sideways'
    
    def _analyze_eth_btc_ratio(self, context: MarketContext) -> str:
        """Analyze ETH performance relative to BTC"""
        eth_btc_performance = context.eth_change_24h - context.btc_change_24h
        
        if eth_btc_performance > 2.0:
            return 'outperform_strong'
        elif eth_btc_performance > 0.5:
            return 'outperform_weak'
        elif eth_btc_performance < -2.0:
            return 'underperform_strong'
        elif eth_btc_performance < -0.5:
            return 'underperform_weak'
        else:
            return 'neutral'
    
    def _assess_market_breadth(self, context: MarketContext) -> str:
        """Assess overall market breadth"""
        # Combine multiple factors
        score = 0
        
        # BTC dominance factor
        if context.btc_dominance > 45:
            score += 1
        elif context.btc_dominance < 40:
            score -= 1
            
        # Market trend factor
        if context.market_trend == 'bullish':
            score += 2
        elif context.market_trend == 'bearish':
            score -= 2
            
        # Fear & Greed factor
        if context.fear_greed_index > 70:
            score += 1
        elif context.fear_greed_index < 30:
            score -= 1
        
        if score >= 2:
            return 'strong'
        elif score <= -2:
            return 'weak'
        else:
            return 'neutral'
    
    def _determine_volatility_state(self, context: MarketContext) -> str:
        """Determine if volatility is expanding or contracting"""
        if context.volatility_regime == 'high':
            return 'expanding'
        elif context.volatility_regime == 'low':
            return 'contracting'
        else:
            return 'stable'
    
    def _classify_market_regime(self, context: MarketContext) -> str:
        """Classify current market regime"""
        # Risk-on/Risk-off classification
        risk_on_score = 0
        
        # Positive factors
        if context.btc_change_24h > 0:
            risk_on_score += 1
        if context.eth_change_24h > 0:
            risk_on_score += 1
        if context.fear_greed_index > 50:
            risk_on_score += 1
        if context.market_trend == 'bullish':
            risk_on_score += 2
            
        # Negative factors
        if context.volatility_regime == 'high' and context.market_trend == 'bearish':
            risk_on_score -= 2
        if context.fear_greed_index < 30:
            risk_on_score -= 2
            
        if risk_on_score >= 3:
            return 'risk_on'
        elif risk_on_score <= -1:
            return 'risk_off'
        else:
            return 'transition'

def main():
    """Test cross-asset correlation functionality"""
    analyzer = CrossAssetAnalyzer()
    
    print("🔍 Testing Cross-Asset Correlation Analysis...")
    
    # Get market context
    context = analyzer.get_market_context()
    if context:
        print(f"\n📊 Market Context:")
        print(f"  BTC: ${context.btc_price:.0f} ({context.btc_change_24h:+.1f}%)")
        print(f"  ETH: ${context.eth_price:.0f} ({context.eth_change_24h:+.1f}%)")
        print(f"  BTC Dominance: {context.btc_dominance:.1f}%")
        print(f"  Fear & Greed: {context.fear_greed_index}")
        print(f"  Volatility: {context.volatility_regime}")
        print(f"  Trend: {context.market_trend}")
        print(f"  Correlation: {context.correlation_signal}")
    
    # Generate cross-asset signal
    test_indicators = {'rsi': 45, 'price': 3.68}
    signal = analyzer.generate_cross_asset_signal(3.68, test_indicators)
    
    print(f"\n🎯 Cross-Asset Signal:")
    print(f"  BTC Trend: {signal.btc_trend}")
    print(f"  ETH/BTC Ratio: {signal.eth_btc_ratio}")
    print(f"  Market Breadth: {signal.market_breadth}")
    print(f"  Volatility State: {signal.volatility_state}")
    print(f"  Regime Signal: {signal.regime_signal}")

if __name__ == "__main__":
    main()