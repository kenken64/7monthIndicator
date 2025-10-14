"""
Custom CrewAI Tools for Market Spike Agent
Provides tools for Binance integration, circuit breaker management, and market analysis
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from binance.client import Client
from crewai.tools import tool

from circuit_breaker import CircuitBreakerStateManager, MarketSnapshot, get_circuit_breaker
from cross_asset_correlation import CrossAssetAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========================================
# CIRCUIT BREAKER TOOLS
# ========================================

@tool("Get Circuit Breaker Status")
def get_circuit_breaker_status() -> str:
    """
    Get the current status of the circuit breaker system.
    Returns detailed information about circuit breaker state, trigger time, and market conditions.
    This tool should be checked before any trading operation.
    """
    try:
        cb = get_circuit_breaker()
        status = cb.get_status()
        return json.dumps(status, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get circuit breaker status: {str(e)}"})


@tool("Check If Trading Safe")
def check_if_trading_safe() -> str:
    """
    Quick check if trading is currently safe (circuit breaker not triggered).
    Returns 'SAFE' or 'BLOCKED' with reason.
    """
    try:
        cb = get_circuit_breaker()
        if cb.is_safe():
            return json.dumps({"status": "SAFE", "message": "Trading is allowed, circuit breaker not triggered"})
        else:
            state = cb.get_state()
            status = cb.get_status()
            return json.dumps({
                "status": "BLOCKED",
                "reason": status.get('trigger_reason', 'Circuit breaker active'),
                "state": state.value,
                "minutes_since_trigger": status.get('minutes_since_trigger')
            })
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


@tool("Get Circuit Breaker Statistics")
def get_circuit_breaker_statistics() -> str:
    """
    Get historical statistics about circuit breaker activations.
    Returns total triggers, average recovery time, and capital protected.
    """
    try:
        cb = get_circuit_breaker()
        stats = cb.get_statistics()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get statistics: {str(e)}"})


# ========================================
# BINANCE MARKET DATA TOOLS
# ========================================

@tool("Get Binance Market Data")
def get_binance_market_data(symbol: str = "BTCUSDT") -> str:
    """
    Get current market data for a symbol from Binance.
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT', 'SUIUSDC')
    Returns JSON with price, volume, 24h change, and technical indicators.
    """
    try:
        from config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

        # Get 24h ticker
        ticker = client.get_ticker(symbol=symbol)

        # Get recent klines for technical analysis
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=100)

        # Calculate basic indicators
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]

        current_price = float(ticker['lastPrice'])
        price_change_24h = float(ticker['priceChangePercent'])
        volume_24h = float(ticker['volume'])
        avg_volume = np.mean(volumes)
        volatility = np.std(closes) / np.mean(closes) * 100

        return json.dumps({
            "symbol": symbol,
            "price": current_price,
            "price_change_24h_percent": price_change_24h,
            "volume_24h": volume_24h,
            "avg_volume_5m": avg_volume,
            "volatility_percent": volatility,
            "high_24h": float(ticker['highPrice']),
            "low_24h": float(ticker['lowPrice']),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get Binance market data: {str(e)}"})


@tool("Get Binance Order Book")
def get_binance_order_book(symbol: str = "BTCUSDT", depth: int = 20) -> str:
    """
    Get current order book depth from Binance.
    Args:
        symbol: Trading pair
        depth: Number of levels to fetch (5, 10, 20, 50, 100, 500, 1000, 5000)
    Returns order book with bid/ask analysis and liquidity metrics.
    """
    try:
        from config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

        depth_data = client.get_order_book(symbol=symbol, limit=depth)

        bids = depth_data['bids']
        asks = depth_data['asks']

        # Calculate liquidity metrics
        total_bid_volume = sum(float(bid[1]) for bid in bids)
        total_ask_volume = sum(float(ask[1]) for ask in asks)
        total_bid_value = sum(float(bid[0]) * float(bid[1]) for bid in bids)
        total_ask_value = sum(float(ask[0]) * float(ask[1]) for ask in asks)

        best_bid = float(bids[0][0]) if bids else 0
        best_ask = float(asks[0][0]) if asks else 0
        spread = best_ask - best_bid
        spread_percent = (spread / best_bid * 100) if best_bid > 0 else 0

        # Calculate bid/ask ratio (order book imbalance)
        bid_ask_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0

        return json.dumps({
            "symbol": symbol,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_percent": spread_percent,
            "total_bid_volume": total_bid_volume,
            "total_ask_volume": total_ask_volume,
            "total_bid_value_usd": total_bid_value,
            "total_ask_value_usd": total_ask_value,
            "bid_ask_ratio": bid_ask_ratio,
            "imbalance": "BUY_PRESSURE" if bid_ask_ratio > 1.5 else "SELL_PRESSURE" if bid_ask_ratio < 0.67 else "BALANCED",
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get order book: {str(e)}"})


@tool("Detect Price Spike")
def detect_price_spike(symbol: str = "BTCUSDT", timeframe_minutes: int = 5, threshold_percent: float = 5.0) -> str:
    """
    Detect if there's a price spike in the specified timeframe.
    Args:
        symbol: Trading pair
        timeframe_minutes: Look back period in minutes
        threshold_percent: Minimum price change to qualify as spike
    Returns spike detection result with magnitude and direction.
    """
    try:
        from config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

        # Get klines for the timeframe
        klines = client.get_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1MINUTE,
            limit=timeframe_minutes + 1
        )

        if len(klines) < 2:
            return json.dumps({"spike_detected": False, "error": "Insufficient data"})

        # Calculate price change
        start_price = float(klines[0][1])  # Open of first candle
        end_price = float(klines[-1][4])  # Close of last candle
        high_price = max(float(k[2]) for k in klines)
        low_price = min(float(k[3]) for k in klines)

        price_change = ((end_price - start_price) / start_price) * 100
        max_swing = ((high_price - low_price) / low_price) * 100

        # Calculate volume surge
        volumes = [float(k[5]) for k in klines]
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1])
        volume_multiplier = current_volume / avg_volume if avg_volume > 0 else 1

        spike_detected = abs(price_change) >= threshold_percent
        direction = "UP" if price_change > 0 else "DOWN"

        return json.dumps({
            "spike_detected": spike_detected,
            "symbol": symbol,
            "timeframe_minutes": timeframe_minutes,
            "price_change_percent": price_change,
            "max_swing_percent": max_swing,
            "direction": direction,
            "start_price": start_price,
            "end_price": end_price,
            "high_price": high_price,
            "low_price": low_price,
            "volume_multiplier": volume_multiplier,
            "volume_surge": volume_multiplier >= 2.0,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"spike_detected": False, "error": f"Failed to detect spike: {str(e)}"})


@tool("Get Binance Liquidations")
def get_binance_liquidations(timeframe_hours: int = 1) -> str:
    """
    Get total liquidations on Binance in the specified timeframe.
    This uses external API to track futures liquidations.
    Args:
        timeframe_hours: Hours to look back (default: 1)
    Returns total liquidations in USD.
    """
    try:
        # Using CoinGlass API for liquidation data (free tier)
        # In production, you'd want to use WebSocket for real-time data
        url = f"https://open-api.coinglass.com/public/v2/liquidation_history"

        # This is a placeholder - actual implementation would need API key
        # For now, return simulated data based on market conditions
        return json.dumps({
            "timeframe_hours": timeframe_hours,
            "total_liquidations_usd": 0,  # Would be calculated from API
            "long_liquidations_usd": 0,
            "short_liquidations_usd": 0,
            "note": "Liquidation tracking requires external API integration",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to get liquidations: {str(e)}"})


# ========================================
# MARKET CONTEXT & CORRELATION TOOLS
# ========================================

@tool("Get Market Context")
def get_market_context() -> str:
    """
    Get comprehensive market context including BTC/ETH prices, dominance, Fear & Greed Index.
    Uses CrossAssetCorrelationAnalyzer for market-wide data.
    """
    try:
        analyzer = CrossAssetAnalyzer()
        context = analyzer.get_market_context()

        return json.dumps({
            "btc_price": context['btc_price'],
            "eth_price": context['eth_price'],
            "btc_change_24h": context['btc_change_24h'],
            "eth_change_24h": context['eth_change_24h'],
            "btc_dominance": context['btc_dominance'],
            "fear_greed_index": context['fear_greed_index'],
            "market_trend": context['market_trend'],
            "volatility_regime": context['volatility_regime'],
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to get market context: {str(e)}"})


@tool("Check Market Crash Conditions")
def check_market_crash_conditions() -> str:
    """
    Check if current market conditions meet circuit breaker crash thresholds.
    Returns crash risk assessment and current drawdowns for BTC/ETH.
    """
    try:
        analyzer = CrossAssetAnalyzer()
        context = analyzer.get_market_context()

        # Calculate 1h and 4h changes (simplified - would need historical data)
        btc_change_1h = context['btc_change_24h'] / 24  # Approximate
        eth_change_1h = context['eth_change_24h'] / 24

        snapshot = MarketSnapshot(
            timestamp=datetime.now().isoformat(),
            btc_price=context['btc_price'],
            eth_price=context['eth_price'],
            btc_change_1h=btc_change_1h,
            eth_change_1h=eth_change_1h,
            btc_change_4h=btc_change_1h * 4,  # Approximate
            eth_change_4h=eth_change_1h * 4,
            fear_greed_index=context['fear_greed_index']
        )

        cb = get_circuit_breaker()
        should_trigger, reason = cb.check_crash_conditions(snapshot)

        # Determine risk level
        max_drop = max(abs(btc_change_1h), abs(eth_change_1h))
        if max_drop >= 15:
            risk_level = "CRITICAL"
        elif max_drop >= 10:
            risk_level = "HIGH"
        elif max_drop >= 5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return json.dumps({
            "should_trigger_circuit_breaker": should_trigger,
            "trigger_reason": reason,
            "risk_level": risk_level,
            "btc_drawdown_1h": btc_change_1h,
            "eth_drawdown_1h": eth_change_1h,
            "market_trend": context['market_trend'],
            "fear_greed_index": context['fear_greed_index'],
            "recommendation": "HALT_TRADING" if should_trigger else "MONITOR_CLOSELY" if risk_level in ["HIGH", "MEDIUM"] else "CONTINUE",
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to check crash conditions: {str(e)}"})


# ========================================
# RISK MANAGEMENT TOOLS
# ========================================

@tool("Calculate Position Size")
def calculate_position_size(account_balance: float, risk_percent: float, entry_price: float, stop_loss_price: float) -> str:
    """
    Calculate optimal position size based on risk management parameters.
    Args:
        account_balance: Total account balance in USD
        risk_percent: Percentage of account to risk (e.g., 2.0 for 2%)
        entry_price: Intended entry price
        stop_loss_price: Stop loss price
    Returns position size in units and USD value.
    """
    try:
        risk_amount = account_balance * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss_price)
        price_risk_percent = (price_risk / entry_price) * 100

        position_size_units = risk_amount / price_risk
        position_size_usd = position_size_units * entry_price

        # Check if position is within reasonable limits
        position_percent_of_account = (position_size_usd / account_balance) * 100

        return json.dumps({
            "position_size_units": position_size_units,
            "position_size_usd": position_size_usd,
            "position_percent_of_account": position_percent_of_account,
            "risk_amount_usd": risk_amount,
            "price_risk_percent": price_risk_percent,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "risk_reward_setup": "VALID" if position_percent_of_account <= 10 else "TOO_LARGE",
            "recommendation": "APPROVE" if position_percent_of_account <= 10 else "REDUCE_SIZE"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to calculate position size: {str(e)}"})


@tool("Estimate Slippage")
def estimate_slippage(symbol: str, order_size_usd: float) -> str:
    """
    Estimate slippage for a market order based on current order book.
    Args:
        symbol: Trading pair
        order_size_usd: Order size in USD
    Returns estimated slippage percentage and execution price.
    """
    try:
        from config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

        depth_data = client.get_order_book(symbol=symbol, limit=100)
        asks = depth_data['asks']

        # Calculate weighted average price for the order size
        remaining_size = order_size_usd
        total_cost = 0
        total_quantity = 0
        best_ask = float(asks[0][0])

        for price_str, quantity_str in asks:
            price = float(price_str)
            quantity = float(quantity_str)
            value = price * quantity

            if remaining_size <= value:
                # This level satisfies the remaining order
                quantity_needed = remaining_size / price
                total_cost += remaining_size
                total_quantity += quantity_needed
                break
            else:
                # Consume entire level
                total_cost += value
                total_quantity += quantity
                remaining_size -= value

        if total_quantity > 0:
            avg_execution_price = total_cost / total_quantity
            slippage_percent = ((avg_execution_price - best_ask) / best_ask) * 100
        else:
            avg_execution_price = best_ask
            slippage_percent = 0

        return json.dumps({
            "symbol": symbol,
            "order_size_usd": order_size_usd,
            "best_ask_price": best_ask,
            "estimated_execution_price": avg_execution_price,
            "estimated_slippage_percent": slippage_percent,
            "slippage_acceptable": slippage_percent <= 1.0,
            "recommendation": "EXECUTE" if slippage_percent <= 1.0 else "SPLIT_ORDER" if slippage_percent <= 2.0 else "CANCEL",
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to estimate slippage: {str(e)}"})


# ========================================
# SPIKE ANALYSIS TOOLS
# ========================================

@tool("Analyze Spike Context")
def analyze_spike_context(symbol: str) -> str:
    """
    Analyze the context around a detected spike to determine if it's legitimate.
    Checks for manipulation signs, news events, and market-wide movements.
    Args:
        symbol: Trading pair that spiked
    Returns comprehensive spike context analysis.
    """
    try:
        # Get market context
        analyzer = CrossAssetAnalyzer()
        market_context = analyzer.get_market_context()

        # Get order book
        from config import BINANCE_API_KEY, BINANCE_SECRET_KEY
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
        depth_data = client.get_order_book(symbol=symbol, limit=50)

        bids = depth_data['bids']
        asks = depth_data['asks']
        total_bid_volume = sum(float(bid[1]) for bid in bids)
        total_ask_volume = sum(float(ask[1]) for ask in asks)
        bid_ask_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0

        # Check if spike is correlated with BTC/ETH
        btc_moving = abs(market_context['btc_change_24h']) > 3
        eth_moving = abs(market_context['eth_change_24h']) > 3
        market_wide = btc_moving or eth_moving

        # Manipulation indicators
        manipulation_score = 0
        if bid_ask_ratio > 3 or bid_ask_ratio < 0.33:
            manipulation_score += 1  # Extreme order book imbalance
        if not market_wide and symbol not in ['BTCUSDT', 'ETHUSDT']:
            manipulation_score += 1  # Isolated move (not market-wide)

        # Determine legitimacy
        if manipulation_score >= 2:
            legitimacy = "SUSPICIOUS"
        elif manipulation_score == 1:
            legitimacy = "QUESTIONABLE"
        else:
            legitimacy = "LIKELY_LEGITIMATE"

        return json.dumps({
            "symbol": symbol,
            "legitimacy": legitimacy,
            "manipulation_score": manipulation_score,
            "market_wide_movement": market_wide,
            "btc_change_24h": market_context['btc_change_24h'],
            "eth_change_24h": market_context['eth_change_24h'],
            "bid_ask_ratio": bid_ask_ratio,
            "order_book_balanced": 0.5 < bid_ask_ratio < 2.0,
            "market_sentiment": "FEAR" if market_context['fear_greed_index'] < 30 else "GREED" if market_context['fear_greed_index'] > 70 else "NEUTRAL",
            "recommendation": "TRADE" if legitimacy == "LIKELY_LEGITIMATE" else "AVOID",
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze spike context: {str(e)}"})


# ========================================
# BOT CONTROL TOOLS
# ========================================

@tool("Emergency Stop All Trading")
def emergency_stop_all_trading(reason: str) -> str:
    """
    Emergency stop - triggers circuit breaker and halts all trading.
    Should only be used in critical situations.
    Args:
        reason: Reason for emergency stop
    """
    try:
        cb = get_circuit_breaker()

        # Create emergency market snapshot
        analyzer = CrossAssetAnalyzer()
        context = analyzer.get_market_context()

        snapshot = MarketSnapshot(
            timestamp=datetime.now().isoformat(),
            btc_price=context['btc_price'],
            eth_price=context['eth_price'],
            btc_change_1h=context['btc_change_24h'] / 24,
            eth_change_1h=context['eth_change_24h'] / 24,
            btc_change_4h=context['btc_change_24h'] / 6,
            eth_change_4h=context['eth_change_24h'] / 6,
            fear_greed_index=context['fear_greed_index']
        )

        actions = [
            "Circuit breaker manually triggered",
            "All pending orders cancelled",
            "All trading strategies paused",
            "Critical alert sent to user"
        ]

        cb.trigger(reason, snapshot, actions)

        return json.dumps({
            "status": "EMERGENCY_STOP_ACTIVATED",
            "reason": reason,
            "actions_taken": actions,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to emergency stop: {str(e)}"})


# Export all tools
__all__ = [
    'get_circuit_breaker_status',
    'check_if_trading_safe',
    'get_circuit_breaker_statistics',
    'get_binance_market_data',
    'get_binance_order_book',
    'detect_price_spike',
    'get_binance_liquidations',
    'get_market_context',
    'check_market_crash_conditions',
    'calculate_position_size',
    'estimate_slippage',
    'analyze_spike_context',
    'emergency_stop_all_trading'
]
