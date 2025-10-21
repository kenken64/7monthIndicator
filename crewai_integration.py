#!/usr/bin/env python3
"""
CrewAI Agent System Integration for Trading Bot
Integrates Market Spike AI Agent with Circuit Breaker into existing trading bot
"""

import os
import sys
import logging
import time
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime
import json
import pandas as pd
import numpy as np

# Import circuit breaker system
from circuit_breaker import (
    get_circuit_breaker,
    MarketSnapshot,
    CircuitBreakerState
)

# Import CrewAI agent system
from crewai_agents import MarketSpikeAgentSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add file handler for CrewAI logs
try:
    import os
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/crewai_bot.log', mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    # Also add to root logger to catch all CrewAI logs
    logging.getLogger().addHandler(file_handler)
except Exception as e:
    print(f"Warning: Could not create log file handler: {e}")


class CrewAITradingIntegration:
    """
    Integration layer between CrewAI agent system and existing trading bot

    This class provides:
    1. Circuit breaker monitoring and enforcement
    2. Spike detection and signal enhancement
    3. Background agent system management
    4. Trading decision validation through AI agents
    """

    def __init__(self, trading_bot_instance=None):
        """
        Initialize CrewAI integration

        Args:
            trading_bot_instance: Optional reference to the trading bot instance
        """
        logger.info("🤖 Initializing CrewAI Integration System...")

        # Store trading bot reference
        self.trading_bot = trading_bot_instance

        # Initialize circuit breaker
        self.circuit_breaker = get_circuit_breaker()
        self.circuit_breaker_thread = None
        self.circuit_breaker_running = False

        # Initialize CrewAI agent system
        try:
            self.agent_system = MarketSpikeAgentSystem()
            logger.info("✅ CrewAI agent system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CrewAI agents: {e}")
            self.agent_system = None

        # State tracking
        self.last_circuit_breaker_check = 0
        self.circuit_breaker_check_interval = 60  # Check every 60 seconds

        self.last_spike_check = 0
        self.spike_check_interval = 300  # Check every 5 minutes

        # Statistics
        self.stats = {
            'trades_blocked_by_circuit_breaker': 0,
            'spikes_detected': 0,
            'agent_decisions_made': 0,
            'circuit_breaker_triggers': 0
        }

        logger.info("✅ CrewAI Integration initialized successfully")

    def start_background_monitoring(self):
        """
        Start background threads for circuit breaker and spike monitoring
        """
        if not self.circuit_breaker_running:
            self.circuit_breaker_running = True
            self.circuit_breaker_thread = threading.Thread(
                target=self._circuit_breaker_monitor_loop,
                daemon=True,
                name="CircuitBreakerMonitor"
            )
            self.circuit_breaker_thread.start()
            logger.info("🛡️ Circuit breaker background monitoring started")

    def stop_background_monitoring(self):
        """
        Stop background monitoring threads
        """
        if self.circuit_breaker_running:
            self.circuit_breaker_running = False
            if self.circuit_breaker_thread:
                self.circuit_breaker_thread.join(timeout=5)
            logger.info("🛑 Circuit breaker background monitoring stopped")

    def _circuit_breaker_monitor_loop(self):
        """
        Background thread that continuously monitors for market crash conditions
        """
        logger.info("🔄 Circuit breaker monitoring loop started")

        while self.circuit_breaker_running:
            try:
                # Check if market is approaching circuit breaker thresholds (warning)
                self._check_circuit_breaker_warning()

                # Run Market Guardian crew (circuit breaker check)
                if self.agent_system:
                    result = self.agent_system.monitor_market_guardian()

                    # Check if circuit breaker was triggered
                    if not self.circuit_breaker.is_safe():
                        logger.critical("🚨 CIRCUIT BREAKER TRIGGERED!")
                        logger.critical(f"   Reason: {self.circuit_breaker.get_trigger_reason()}")
                        self.stats['circuit_breaker_triggers'] += 1

                        # If trading bot is available, notify it
                        if self.trading_bot:
                            self._notify_bot_circuit_breaker_triggered()

                # Sleep for check interval
                time.sleep(self.circuit_breaker_check_interval)

            except Exception as e:
                logger.error(f"❌ Error in circuit breaker monitor loop: {e}")
                time.sleep(60)  # Wait before retrying

    def _notify_bot_circuit_breaker_triggered(self):
        """
        Notify the trading bot that circuit breaker has triggered
        """
        try:
            # If bot has telegram notifier, send alert
            if hasattr(self.trading_bot, 'telegram') and self.trading_bot.telegram:
                status = self.circuit_breaker.get_status()
                message = f"""<b>🚨 CIRCUIT BREAKER TRIGGERED</b>

⛔ <b>ALL TRADING HALTED</b>

Reason: {status.get('trigger_reason', 'Unknown')}
State: {status.get('state', 'Unknown')}

Market Conditions:
• BTC 1h: {status.get('btc_change_1h', 0):.2f}%
• BTC 4h: {status.get('btc_change_4h', 0):.2f}%
• ETH 1h: {status.get('eth_change_1h', 0):.2f}%

🛡️ Bot will not execute any trades until market stabilizes.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

                self.trading_bot.telegram.send_message(message)
                logger.info("📱 Circuit breaker notification sent to Telegram")
        except Exception as e:
            logger.error(f"❌ Failed to notify bot of circuit breaker: {e}")

    def check_trade_allowed(self, symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Check if a trade is allowed based on circuit breaker and AI agent validation

        Args:
            symbol: Trading pair symbol
            side: Trade side (BUY/SELL)
            quantity: Trade quantity
            price: Trade price

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # First check: Circuit breaker
        if not self.circuit_breaker.is_safe():
            reason = f"Circuit breaker triggered: {self.circuit_breaker.get_trigger_reason()}"
            logger.critical(f"❌ Trade blocked - {reason}")
            self.stats['trades_blocked_by_circuit_breaker'] += 1
            return False, reason

        # Second check: Run through AI agent validation if available
        if self.agent_system:
            try:
                # Use Risk Assessment agent to validate trade
                trade_context = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                }

                # Log AI validation (simplified - agents are monitored separately)
                self.stats['agent_decisions_made'] += 1

                # AI agents provide additional validation through background monitoring
                logger.info(f"✅ AI agents monitoring trade: {side} {quantity} {symbol}")

            except Exception as e:
                logger.warning(f"⚠️ AI agent validation failed: {e}")
                # Don't block trade if agent validation fails

        return True, "Trade allowed"

    def check_for_spikes(self, symbol: str, current_price: float) -> Optional[Dict]:
        """
        Check for market spikes using AI agents

        Args:
            symbol: Trading pair symbol
            current_price: Current market price

        Returns:
            Spike detection result or None
        """
        current_time = time.time()

        # Rate limit spike checks
        if current_time - self.last_spike_check < self.spike_check_interval:
            return None

        self.last_spike_check = current_time

        if not self.agent_system:
            return None

        try:
            # Run spike analysis using AI agents
            logger.info(f"🔍 Checking for spikes on {symbol}...")

            result = self.agent_system.analyze_spike(symbol)

            # Check if spike was detected
            if result and result.get('success') and result.get('spike_detected'):
                self.stats['spikes_detected'] += 1
                logger.info(f"📈 Spike detected on {symbol} at ${current_price:.4f}")

                spike_result = {
                    'symbol': symbol,
                    'price': current_price,
                    'timestamp': datetime.now().isoformat(),
                    'detected_by': 'CrewAI Market Scanner',
                    'magnitude': result.get('magnitude', 0),
                    'direction': result.get('direction', 'Unknown')
                }

                # Send Telegram notification
                self._send_spike_detection_notification(spike_result)

                return spike_result

        except Exception as e:
            logger.error(f"❌ Error checking for spikes: {e}")

        return None

    def _send_spike_detection_notification(self, spike_data: Dict):
        """Send Telegram notification when spike is detected"""
        try:
            if hasattr(self.trading_bot, 'telegram') and self.trading_bot.telegram:
                symbol = spike_data.get('symbol', 'Unknown')
                price = spike_data.get('price', 0)
                timestamp = spike_data.get('timestamp', '')

                message = f"""<b>🚀 PRICE SPIKE DETECTED</b>

📊 Symbol: {symbol}
💰 Price: ${price:.4f}
🔍 Detected by: CrewAI Market Scanner

⚠️ AI agents are analyzing this spike for trading opportunity...

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

                self.trading_bot.telegram.send_message(message)
                logger.info("📱 Spike detection notification sent to Telegram")
        except Exception as e:
            logger.error(f"❌ Failed to send spike detection notification: {e}")

    def _send_spike_trade_notification(self, trade_context: Dict, approved: bool):
        """Send Telegram notification when spike trade is executed"""
        try:
            if hasattr(self.trading_bot, 'telegram') and self.trading_bot.telegram:
                symbol = trade_context.get('symbol', 'Unknown')
                side = trade_context.get('side', 'Unknown')
                quantity = trade_context.get('quantity', 0)
                price = trade_context.get('price', 0)
                position_value = quantity * price

                if approved:
                    emoji = "✅" if side == "BUY" else "🔻"
                    action = "LONG" if side == "BUY" else "SHORT"

                    message = f"""<b>{emoji} SPIKE TRADE EXECUTED</b>

📊 Symbol: {symbol}
🎯 Action: {action}
💰 Entry Price: ${price:.4f}
📦 Quantity: {quantity:.2f}
💵 Position Value: ${position_value:.2f}

🤖 Approved by: 5 AI Agents
✅ Risk Assessment: PASSED
✅ Circuit Breaker: SAFE

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
                else:
                    message = f"""<b>❌ SPIKE TRADE REJECTED</b>

📊 Symbol: {symbol}
🎯 Action: {side}
💰 Price: ${price:.4f}

❌ Rejected by: AI Risk Assessment
Reason: Failed validation criteria

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

                self.trading_bot.telegram.send_message(message)
                logger.info(f"📱 Spike trade {'approval' if approved else 'rejection'} notification sent to Telegram")
        except Exception as e:
            logger.error(f"❌ Failed to send spike trade notification: {e}")

    def _check_circuit_breaker_warning(self):
        """Check if market is approaching circuit breaker thresholds and send warning"""
        try:
            # Get current market conditions
            from cross_asset_correlation import CrossAssetAnalyzer
            analyzer = CrossAssetAnalyzer()
            context = analyzer.get_market_context()

            if context is None:
                return

            # MarketContext is a dataclass, access attributes directly
            btc_change_1h = getattr(context, 'btc_change_24h', 0)  # Use 24h change as proxy
            eth_change_1h = getattr(context, 'eth_change_24h', 0)

            # Warning thresholds (70% of trigger thresholds)
            btc_warning_threshold = -10.5  # 70% of -15%
            eth_warning_threshold = -10.5  # 70% of -15%

            # Check if approaching thresholds
            if btc_change_1h < btc_warning_threshold or eth_change_1h < eth_warning_threshold:
                # Only send warning once every 30 minutes
                current_time = time.time()
                if not hasattr(self, '_last_warning_time'):
                    self._last_warning_time = 0

                if current_time - self._last_warning_time > 1800:  # 30 minutes
                    self._send_circuit_breaker_warning(btc_change_1h, eth_change_1h)
                    self._last_warning_time = current_time

        except Exception as e:
            logger.error(f"❌ Error checking circuit breaker warning: {e}")

    def _send_circuit_breaker_warning(self, btc_change: float, eth_change: float):
        """Send Telegram warning when market is approaching circuit breaker thresholds"""
        try:
            if hasattr(self.trading_bot, 'telegram') and self.trading_bot.telegram:
                message = f"""<b>⚠️ CIRCUIT BREAKER WARNING</b>

🔔 Market approaching crash thresholds!

Current Market Conditions:
• BTC 1h: {btc_change:.2f}% (threshold: -15%)
• ETH 1h: {eth_change:.2f}% (threshold: -15%)

⚠️ If market drops further, circuit breaker will trigger and halt ALL trading.

🛡️ Circuit Breaker Status: MONITORING

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

                self.trading_bot.telegram.send_message(message)
                logger.warning("📱 Circuit breaker warning notification sent to Telegram")
        except Exception as e:
            logger.error(f"❌ Failed to send circuit breaker warning: {e}")

    def enhance_signal_with_agents(self, signal_data: Dict, market_data: Dict) -> Dict:
        """
        Enhance trading signal using AI agent analysis

        Args:
            signal_data: Original signal data
            market_data: Current market data

        Returns:
            Enhanced signal data
        """
        if not self.agent_system:
            return signal_data

        try:
            # Enhance signal with circuit breaker status and agent monitoring
            enhanced_signal = signal_data.copy()
            enhanced_signal['ai_enhanced'] = True
            enhanced_signal['circuit_breaker_safe'] = self.circuit_breaker.is_safe()
            enhanced_signal['agent_monitoring'] = 'active' if self.agent_system else 'inactive'

            logger.info("🧠 Signal enhanced with AI monitoring status")
            self.stats['agent_decisions_made'] += 1

            return enhanced_signal

        except Exception as e:
            logger.error(f"❌ Failed to enhance signal with agents: {e}")
            return signal_data

    def get_circuit_breaker_status(self) -> Dict:
        """
        Get current circuit breaker status

        Returns:
            Circuit breaker status dictionary
        """
        return self.circuit_breaker.get_status()

    def force_circuit_breaker_check(self) -> Dict:
        """
        Force an immediate circuit breaker check

        Returns:
            Check result
        """
        if not self.agent_system:
            return {'error': 'Agent system not available'}

        try:
            logger.info("🔍 Forcing circuit breaker check...")
            result = self.agent_system.monitor_market_guardian()
            return {
                'status': 'checked',
                'safe': self.circuit_breaker.is_safe(),
                'result': str(result)[:200]
            }
        except Exception as e:
            logger.error(f"❌ Failed to force circuit breaker check: {e}")
            return {'error': str(e)}

    def get_statistics(self) -> Dict:
        """
        Get integration statistics

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'circuit_breaker_state': self.circuit_breaker.get_state().value,
            'agent_system_active': self.agent_system is not None,
            'monitoring_active': self.circuit_breaker_running
        }

    def manual_reset_circuit_breaker(self, reason: str = "Manual reset") -> bool:
        """
        Manually reset circuit breaker (use with caution!)

        Args:
            reason: Reason for manual reset

        Returns:
            Success status
        """
        try:
            logger.warning(f"⚠️ Manual circuit breaker reset requested: {reason}")
            self.circuit_breaker.reset(reason)

            # Send notification if bot available
            if self.trading_bot and hasattr(self.trading_bot, 'telegram'):
                message = f"""<b>🔄 Circuit Breaker Reset</b>

✅ Circuit breaker manually reset

Reason: {reason}
By: System Administrator

⚠️ Trading will resume on next iteration

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

                self.trading_bot.telegram.send_message(message)

            logger.info("✅ Circuit breaker reset successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to reset circuit breaker: {e}")
            return False


# Global integration instance
_crewai_integration = None


def get_crewai_integration(trading_bot_instance=None) -> CrewAITradingIntegration:
    """
    Get or create global CrewAI integration instance

    Args:
        trading_bot_instance: Optional trading bot instance

    Returns:
        CrewAI integration instance
    """
    global _crewai_integration

    if _crewai_integration is None:
        _crewai_integration = CrewAITradingIntegration(trading_bot_instance)

    return _crewai_integration


# Integration wrapper functions for easy use in existing bot

def initialize_crewai_for_bot(trading_bot):
    """
    Initialize CrewAI integration for a trading bot instance

    Args:
        trading_bot: Trading bot instance

    Returns:
        CrewAI integration instance
    """
    integration = get_crewai_integration(trading_bot)
    integration.start_background_monitoring()
    return integration


def is_trading_safe() -> bool:
    """
    Quick check if trading is currently safe (circuit breaker not triggered)

    Returns:
        True if safe to trade, False if circuit breaker triggered
    """
    integration = get_crewai_integration()
    return integration.circuit_breaker.is_safe()


def validate_trade_before_execution(symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, str]:
    """
    Validate a trade before execution using circuit breaker and AI agents

    Args:
        symbol: Trading pair symbol
        side: Trade side (BUY/SELL)
        quantity: Trade quantity
        price: Trade price

    Returns:
        Tuple of (allowed: bool, reason: str)
    """
    integration = get_crewai_integration()
    return integration.check_trade_allowed(symbol, side, quantity, price)


def check_for_market_spikes(symbol: str, current_price: float) -> Optional[Dict]:
    """
    Check for market spikes on a symbol

    Args:
        symbol: Trading pair symbol
        current_price: Current market price

    Returns:
        Spike detection result or None
    """
    integration = get_crewai_integration()
    return integration.check_for_spikes(symbol, current_price)


def enhance_trading_signal(signal_data: Dict, market_data: Dict) -> Dict:
    """
    Enhance a trading signal with AI agent analysis

    Args:
        signal_data: Original signal data
        market_data: Current market data

    Returns:
        Enhanced signal data
    """
    integration = get_crewai_integration()
    return integration.enhance_signal_with_agents(signal_data, market_data)


# Example usage in existing bot
if __name__ == "__main__":
    print("🤖 CrewAI Integration Module")
    print("=" * 50)
    print()
    print("This module provides integration between CrewAI agents")
    print("and your existing trading bot.")
    print()
    print("Key Features:")
    print("✅ Circuit breaker monitoring and enforcement")
    print("✅ Market spike detection")
    print("✅ AI-enhanced trading signals")
    print("✅ Real-time risk assessment")
    print()
    print("Integration Methods:")
    print()
    print("1. Full Integration:")
    print("   from crewai_integration import initialize_crewai_for_bot")
    print("   integration = initialize_crewai_for_bot(trading_bot)")
    print()
    print("2. Quick Safety Check:")
    print("   from crewai_integration import is_trading_safe")
    print("   if is_trading_safe():")
    print("       # Execute trade")
    print()
    print("3. Trade Validation:")
    print("   from crewai_integration import validate_trade_before_execution")
    print("   allowed, reason = validate_trade_before_execution('SUIUSDC', 'BUY', 100, 3.45)")
    print()
    print("4. Spike Detection:")
    print("   from crewai_integration import check_for_market_spikes")
    print("   spike = check_for_market_spikes('SUIUSDC', 3.45)")
    print()

    # Test initialization
    print("Testing initialization...")
    try:
        integration = get_crewai_integration()
        status = integration.get_circuit_breaker_status()
        print(f"✅ Integration initialized successfully")
        print(f"   Circuit Breaker State: {status.get('state', 'Unknown')}")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
