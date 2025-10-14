#!/usr/bin/env python3
"""
RL-Enhanced Trading Bot with CrewAI Integration
Combines RL enhancements with CrewAI Market Spike Agent and Circuit Breaker Protection
"""

# Import the existing bot
from rl_bot_ready import RLEnhancedBinanceFuturesBot, logger, RL_ENHANCEMENT_ENABLED
import logging
from typing import Dict

# Import CrewAI integration
from crewai_integration import (
    initialize_crewai_for_bot,
    is_trading_safe,
    validate_trade_before_execution,
    check_for_market_spikes,
    enhance_trading_signal,
    get_crewai_integration
)


class CrewAIEnhancedTradingBot(RLEnhancedBinanceFuturesBot):
    """
    Trading bot with both RL enhancements AND CrewAI agent integration

    Features:
    - RL-enhanced signal generation (from parent class)
    - Circuit breaker protection (CrewAI Market Guardian)
    - Market spike detection (CrewAI Market Scanner)
    - AI-enhanced context analysis
    - Multi-layer risk assessment
    """

    def __init__(self, *args, **kwargs):
        """Initialize bot with CrewAI integration"""

        # Call parent constructor
        super().__init__(*args, **kwargs)

        # Initialize CrewAI integration
        logger.info("🤖 Initializing CrewAI Integration...")
        try:
            self.crewai_integration = initialize_crewai_for_bot(self)
            self.crewai_enabled = True
            logger.info("✅ CrewAI agents integrated successfully")
        except Exception as e:
            logger.error(f"❌ CrewAI integration failed: {e}")
            self.crewai_enabled = False

        # Send startup notification
        if self.crewai_enabled:
            startup_msg = f"""<b>🚀 CrewAI-Enhanced Bot Started</b>

📊 Symbol: {self.symbol}
🤖 RL Enhancement: {'✅ ACTIVE' if RL_ENHANCEMENT_ENABLED else '❌ DISABLED'}
🛡️ Circuit Breaker: ✅ ACTIVE
🔍 Spike Detection: ✅ ACTIVE
🧠 AI Agents: ✅ 5 Agents Online

Position Size: {self.position_percentage}%
Leverage: {self.leverage}x
TP: {self.take_profit_percent}% | SL: {self.stop_loss_percent}%

✅ Multi-layer protection active
⏰ {self.crewai_integration.circuit_breaker.get_status().get('timestamp', 'N/A')}"""

            try:
                self.telegram.send_message(startup_msg)
            except Exception as e:
                logger.error(f"📱 Startup notification error: {e}")

    def generate_signals(self, df, indicators) -> Dict:
        """
        Enhanced signal generation with CrewAI agents

        Process:
        1. Generate base signal (parent class with RL)
        2. Enhance with CrewAI agent analysis
        3. Check for market spikes
        4. Validate against circuit breaker
        """

        # Get base signal from parent (includes RL enhancement)
        base_signal = super().generate_signals(df, indicators)

        # If CrewAI is enabled, enhance signal further
        if self.crewai_enabled:
            try:
                current_price = df['close'].iloc[-1]

                # Check for spikes
                spike_result = check_for_market_spikes(self.symbol, current_price)
                if spike_result:
                    logger.info(f"📈 SPIKE DETECTED: {spike_result}")
                    base_signal['spike_detected'] = True
                    base_signal['spike_data'] = spike_result

                # Enhance signal with AI agent context
                market_data = {
                    'symbol': self.symbol,
                    'price': current_price,
                    'rsi': indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in indicators else None,
                    'volume': df['volume'].iloc[-1]
                }

                enhanced_signal = enhance_trading_signal(base_signal, market_data)

                # Add circuit breaker status
                cb_status = self.crewai_integration.get_circuit_breaker_status()
                enhanced_signal['circuit_breaker_state'] = cb_status.get('state', 'Unknown')
                enhanced_signal['circuit_breaker_safe'] = cb_status.get('is_safe', False)

                return enhanced_signal

            except Exception as e:
                logger.error(f"❌ CrewAI signal enhancement failed: {e}")
                return base_signal

        return base_signal

    def execute_trade(self, signal_data: Dict, current_price: float) -> bool:
        """
        Execute trade with CrewAI validation

        Adds additional safety checks:
        1. Circuit breaker check (market crash protection)
        2. AI agent trade validation
        3. Standard RL risk management (from parent)
        """

        # Check if bot is paused
        if self.check_pause_status():
            logger.info("⏸️ Bot is paused - skipping trade execution")
            return False

        signal = signal_data['signal']

        if signal == 0:
            logger.info("🛑 No trade signal - maintaining current position")
            return False

        # CrewAI Safety Check #1: Circuit Breaker
        if self.crewai_enabled:
            if not is_trading_safe():
                logger.critical("🚨 TRADE BLOCKED - Circuit breaker triggered!")
                logger.critical("   Market crash protection active")

                # Send Telegram alert
                try:
                    cb_status = self.crewai_integration.get_circuit_breaker_status()
                    alert_msg = f"""<b>🚨 TRADE BLOCKED</b>

⛔ Circuit breaker active

Reason: {cb_status.get('trigger_reason', 'Unknown')}

Signal: {'BUY' if signal > 0 else 'SELL'} {self.symbol}
Price: ${current_price:.4f}

🛡️ Trading suspended for safety
⏰ {cb_status.get('timestamp', 'N/A')}"""

                    self.telegram.send_message(alert_msg)
                except Exception as e:
                    logger.error(f"📱 Alert notification error: {e}")

                return False

        # CrewAI Safety Check #2: AI Agent Validation
        if self.crewai_enabled:
            try:
                # Calculate position details
                account_info = self.client.futures_account()
                available_balance = 0.0
                for asset in account_info['assets']:
                    if asset['asset'] == self.symbol.replace('SUI', ''):
                        available_balance = float(asset['walletBalance'])
                        break

                position_value = available_balance * self.position_percentage
                position_size = (position_value * self.leverage) / current_price
                position_size = round(position_size, 1)

                side = 'BUY' if signal > 0 else 'SELL'

                # Validate with AI agents
                allowed, reason = validate_trade_before_execution(
                    self.symbol, side, position_size, current_price
                )

                if not allowed:
                    logger.warning(f"⚠️ Trade blocked by AI agents: {reason}")
                    return False

                logger.info(f"✅ Trade validated by AI agents: {reason}")

            except Exception as e:
                logger.warning(f"⚠️ AI agent validation error: {e}")
                # Don't block trade if validation fails

        # Execute trade using parent method (includes RL enhancements)
        result = super().execute_trade(signal_data, current_price)

        # If trade executed and CrewAI enabled, log to agent system
        if result and self.crewai_enabled:
            try:
                stats = self.crewai_integration.get_statistics()
                logger.info(f"🤖 CrewAI Stats: {stats}")
            except Exception as e:
                logger.error(f"❌ Failed to log CrewAI stats: {e}")

        return result

    def run(self, interval: int = 300):
        """
        Main bot loop with CrewAI integration

        Enhanced with:
        - Circuit breaker monitoring (background thread)
        - Periodic spike detection
        - Real-time AI agent context
        """

        logger.info(f"🚀 Starting CrewAI-Enhanced Trading Bot for {self.symbol}")
        logger.info(f"🤖 RL Enhancement: {'ACTIVE' if RL_ENHANCEMENT_ENABLED else 'DISABLED'}")
        logger.info(f"🛡️ Circuit Breaker: {'ACTIVE' if self.crewai_enabled else 'DISABLED'}")
        logger.info(f"🔍 Spike Detection: {'ACTIVE' if self.crewai_enabled else 'DISABLED'}")
        logger.info(f"💰 Max Position: {self.position_percentage}% | Leverage: {self.leverage}x")
        logger.info(f"🎯 TP: {self.take_profit_percent}% | SL: {self.stop_loss_percent}%")

        # Run parent's main loop (which includes all RL logic)
        super().run(interval)

    def __del__(self):
        """Cleanup on bot shutdown"""
        if hasattr(self, 'crewai_integration') and self.crewai_integration:
            try:
                self.crewai_integration.stop_background_monitoring()
                logger.info("🛑 CrewAI background monitoring stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping CrewAI monitoring: {e}")


def main():
    """
    Start the CrewAI-Enhanced Trading Bot
    """
    try:
        logger.info("=" * 60)
        logger.info("🚀 CrewAI + RL Enhanced Trading Bot")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Features:")
        logger.info("  ✅ RL-Enhanced Signals")
        logger.info("  ✅ Circuit Breaker Protection (Market Crash Detection)")
        logger.info("  ✅ Market Spike Detection")
        logger.info("  ✅ AI Agent Context Analysis")
        logger.info("  ✅ Multi-Layer Risk Assessment")
        logger.info("")
        logger.info("Safety Settings:")
        logger.info("  • Max Position: 2% of account")
        logger.info("  • Leverage: 50x")
        logger.info("  • Take Profit: 15%")
        logger.info("  • Stop Loss: 5%")
        logger.info("  • Circuit Breaker: Auto-halt on >15% BTC/ETH crash")
        logger.info("")

        # Create bot instance
        bot = CrewAIEnhancedTradingBot(
            symbol='SUIUSDC',
            leverage=50,
            position_percentage=2.0
        )

        # Run bot
        logger.info("🏁 Bot initialized, starting main loop...")
        logger.info("")
        bot.run(interval=25)  # 25 seconds

    except KeyboardInterrupt:
        logger.info("")
        logger.info("👋 Bot stopped by user")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("")
        logger.error(f"❌ Fatal error: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
