"""
CrewAI Agents and Crew Orchestration for Market Spike Agent
Implements all 5 specialized agents with circuit breaker protection
"""

import json
import logging
import os
from typing import Dict, List, Optional

import yaml
from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

from spike_agent_tools import (
    analyze_spike_context,
    calculate_position_size,
    check_if_trading_safe,
    check_market_crash_conditions,
    detect_price_spike,
    emergency_stop_all_trading,
    estimate_slippage,
    get_binance_market_data,
    get_binance_order_book,
    get_circuit_breaker_statistics,
    get_circuit_breaker_status,
    get_market_context,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketSpikeAgentSystem:
    """
    Main system orchestrating all CrewAI agents for market spike detection
    and circuit breaker protection
    """

    def __init__(self, config_path: str = "config/crewai_spike_agent.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize LLM
        self.llm = self._init_llm()

        # Initialize agents
        self.market_guardian_agent = None
        self.market_scanner_agent = None
        self.context_analyzer_agent = None
        self.risk_assessment_agent = None
        self.strategy_executor_agent = None

        # Initialize crews
        self.guardian_crew = None
        self.spike_trading_crew = None

        # Build the system
        self._build_agents()
        self._build_crews()

        logger.info("Market Spike Agent System initialized successfully")

    def _load_config(self) -> Dict:
        """Load configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _init_llm(self) -> ChatOpenAI:
        """Initialize Language Model"""
        llm_config = self.config.get('llm', {})
        model = llm_config.get('model', 'gpt-4o-mini')
        temperature = llm_config.get('temperature', 0.2)

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key
        )

    def _build_agents(self):
        """Build all specialized agents"""

        # ========================================
        # AGENT 1: MARKET GUARDIAN (CIRCUIT BREAKER)
        # ========================================
        guardian_config = self.config['agents']['market_guardian']

        self.market_guardian_agent = Agent(
            role=guardian_config['role'],
            goal=guardian_config['goal'],
            backstory=guardian_config['backstory'],
            tools=[
                check_market_crash_conditions,
                get_circuit_breaker_status,
                get_circuit_breaker_statistics,
                get_market_context,
                emergency_stop_all_trading
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,  # Guardian makes independent decisions
            max_iter=5
        )

        logger.info("✅ Market Guardian Agent (Circuit Breaker) created")

        # ========================================
        # AGENT 2: MARKET SCANNER (SPIKE DETECTION)
        # ========================================
        scanner_config = self.config['agents']['market_scanner']

        self.market_scanner_agent = Agent(
            role=scanner_config['role'],
            goal=scanner_config['goal'],
            backstory=scanner_config['backstory'],
            tools=[
                detect_price_spike,
                get_binance_market_data,
                get_binance_order_book,
                check_if_trading_safe
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

        logger.info("✅ Market Scanner Agent created")

        # ========================================
        # AGENT 3: CONTEXT ANALYZER
        # ========================================
        context_config = self.config['agents']['context_analyzer']

        self.context_analyzer_agent = Agent(
            role=context_config['role'],
            goal=context_config['goal'],
            backstory=context_config['backstory'],
            tools=[
                analyze_spike_context,
                get_market_context,
                get_binance_market_data,
                get_binance_order_book
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

        logger.info("✅ Context Analyzer Agent created")

        # ========================================
        # AGENT 4: RISK ASSESSMENT
        # ========================================
        risk_config = self.config['agents']['risk_assessment']

        self.risk_assessment_agent = Agent(
            role=risk_config['role'],
            goal=risk_config['goal'],
            backstory=risk_config['backstory'],
            tools=[
                calculate_position_size,
                estimate_slippage,
                check_if_trading_safe,
                get_circuit_breaker_status,
                get_market_context
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

        logger.info("✅ Risk Assessment Agent created")

        # ========================================
        # AGENT 5: STRATEGY EXECUTOR
        # ========================================
        executor_config = self.config['agents']['strategy_executor']

        self.strategy_executor_agent = Agent(
            role=executor_config['role'],
            goal=executor_config['goal'],
            backstory=executor_config['backstory'],
            tools=[
                check_if_trading_safe,
                get_binance_market_data,
                estimate_slippage
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )

        logger.info("✅ Strategy Executor Agent created")

    def _build_crews(self):
        """Build agent crews with task workflows"""

        # ========================================
        # GUARDIAN CREW (Continuous Monitoring)
        # ========================================

        # Task: Continuous market monitoring for crashes
        market_monitoring_task = Task(
            description="""
            Continuously monitor BTC, ETH, and market-wide conditions for crash scenarios.

            Your responsibilities:
            1. Check current BTC and ETH prices and recent changes (1h, 4h)
            2. Monitor total market cap and Fear & Greed Index
            3. Assess if any crash threshold is met:
               - BTC >15% drop in 1 hour
               - ETH >15% drop in 1 hour
               - Market cap >20% drop in 4 hours
               - Liquidations >$500M in 1 hour
            4. If crash detected, immediately trigger circuit breaker
            5. If market recovering, assess recovery conditions

            Be vigilant and decisive. Capital protection is your #1 priority.
            """,
            agent=self.market_guardian_agent,
            expected_output="""
            JSON report with:
            - Circuit breaker status (SAFE/WARNING/TRIGGERED)
            - Current market conditions (BTC/ETH drawdowns)
            - Risk level (LOW/MEDIUM/HIGH/CRITICAL)
            - Recommendation (CONTINUE/MONITOR/HALT_TRADING)
            - Reason for any state changes
            """
        )

        self.guardian_crew = Crew(
            agents=[self.market_guardian_agent],
            tasks=[market_monitoring_task],
            process=Process.sequential,
            verbose=True
        )

        logger.info("✅ Guardian Crew created")

        # ========================================
        # SPIKE TRADING CREW (Event-Driven)
        # ========================================

        # Task 1: Spike Detection
        spike_detection_task = Task(
            description="""
            Scan monitored trading pairs for price spikes.

            For the given symbol:
            1. Check if circuit breaker is SAFE (DO NOT proceed if not safe)
            2. Detect price spikes in 5-minute timeframe
            3. Check if spike magnitude exceeds threshold (varies by symbol)
            4. Verify volume surge accompanies price spike
            5. Calculate spike confidence score

            Only flag high-confidence spikes for further analysis.
            """,
            agent=self.market_scanner_agent,
            expected_output="""
            JSON with:
            - spike_detected: true/false
            - symbol: trading pair
            - magnitude: price change percentage
            - direction: UP/DOWN
            - volume_surge: true/false
            - confidence: 0-1 score
            - circuit_breaker_safe: true/false
            """
        )

        # Task 2: Market Stability Check
        stability_check_task = Task(
            description="""
            For the detected spike, verify market stability.

            Check:
            1. Is this an isolated spike or market-wide movement?
            2. Are BTC/ETH showing similar patterns?
            3. Is circuit breaker approaching trigger threshold?
            4. What's the current market sentiment (Fear & Greed)?

            Return STABLE/WARNING/CRITICAL status.
            Only allow spike trading if STABLE.
            """,
            agent=self.market_guardian_agent,
            expected_output="""
            JSON with:
            - stability_status: STABLE/WARNING/CRITICAL
            - market_wide_movement: true/false
            - btc_eth_correlation: 0-1
            - circuit_breaker_risk: LOW/MEDIUM/HIGH
            - recommendation: PROCEED/ABORT
            """
        )

        # Task 3: Context Analysis
        context_analysis_task = Task(
            description="""
            Analyze spike context to determine legitimacy.

            Investigate:
            1. Order book balance (bid/ask ratio)
            2. Is spike correlated with BTC/ETH?
            3. Signs of manipulation (extreme imbalance, low liquidity)
            4. Market sentiment and recent news
            5. Legitimacy score

            Classify as: LIKELY_LEGITIMATE, QUESTIONABLE, SUSPICIOUS
            """,
            agent=self.context_analyzer_agent,
            expected_output="""
            JSON with:
            - legitimacy: LIKELY_LEGITIMATE/QUESTIONABLE/SUSPICIOUS
            - manipulation_score: 0-3
            - market_correlation: true/false
            - order_book_balanced: true/false
            - recommendation: TRADE/AVOID
            - reasoning: explanation
            """
        )

        # Task 4: Risk Evaluation
        risk_evaluation_task = Task(
            description="""
            Evaluate risk-reward for the spike trade opportunity.

            Calculate:
            1. Verify circuit breaker is SAFE (critical check)
            2. Optimal position size based on account balance and risk %
            3. Expected slippage for the order size
            4. Stop loss and take profit levels
            5. Risk-reward ratio

            Only approve if:
            - Circuit breaker is SAFE
            - Slippage <1%
            - Position size reasonable (<5% of account)
            - Risk-reward >2:1
            """,
            agent=self.risk_assessment_agent,
            expected_output="""
            JSON with:
            - approval: APPROVED/REJECTED
            - circuit_breaker_safe: true/false
            - position_size_usd: amount
            - estimated_slippage: percentage
            - stop_loss: price
            - take_profit: price
            - risk_reward_ratio: number
            - rejection_reason: if rejected
            """
        )

        # Task 5: Trade Execution (Conditional)
        execution_task = Task(
            description="""
            Execute spike trade if approved by Risk Agent.

            Pre-execution checks:
            1. MUST verify circuit breaker is SAFE (CRITICAL)
            2. Double-check slippage estimate
            3. Confirm order parameters

            Execution:
            1. Prepare order with calculated parameters
            2. Return execution plan (NO actual execution in this task)
            3. Log decision for tracking

            If circuit breaker triggers during execution, ABORT immediately.
            """,
            agent=self.strategy_executor_agent,
            expected_output="""
            JSON with:
            - execution_plan: EXECUTE/ABORT
            - order_type: MARKET/LIMIT
            - symbol: trading pair
            - side: BUY/SELL
            - quantity: amount
            - entry_price: expected price
            - stop_loss: price
            - take_profit: price
            - circuit_breaker_checked: true/false
            - ready_to_execute: true/false
            """
        )

        self.spike_trading_crew = Crew(
            agents=[
                self.market_scanner_agent,
                self.market_guardian_agent,
                self.context_analyzer_agent,
                self.risk_assessment_agent,
                self.strategy_executor_agent
            ],
            tasks=[
                spike_detection_task,
                stability_check_task,
                context_analysis_task,
                risk_evaluation_task,
                execution_task
            ],
            process=Process.sequential,
            verbose=True
        )

        logger.info("✅ Spike Trading Crew created")

    def monitor_market_guardian(self) -> Dict:
        """
        Run the guardian crew to monitor for market crashes.
        This should run continuously in a separate thread.
        """
        try:
            logger.info("🛡️ Running Market Guardian monitoring cycle...")
            result = self.guardian_crew.kickoff()
            logger.info(f"Guardian result: {result}")
            return {"success": True, "result": str(result)}
        except Exception as e:
            logger.error(f"Guardian monitoring error: {e}")
            return {"success": False, "error": str(e)}

    def analyze_spike(self, symbol: str, timeframe_minutes: int = 5, threshold_percent: float = 5.0) -> Dict:
        """
        Analyze a potential spike for the given symbol.
        Runs the full spike trading crew workflow.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe_minutes: Detection timeframe
            threshold_percent: Minimum spike threshold

        Returns:
            Complete analysis and execution recommendation
        """
        try:
            logger.info(f"🔍 Analyzing spike for {symbol}...")

            # Inject context into crew
            inputs = {
                "symbol": symbol,
                "timeframe_minutes": timeframe_minutes,
                "threshold_percent": threshold_percent
            }

            result = self.spike_trading_crew.kickoff(inputs=inputs)
            logger.info(f"Spike analysis complete: {result}")

            return {
                "success": True,
                "symbol": symbol,
                "result": str(result)
            }
        except Exception as e:
            logger.error(f"Spike analysis error: {e}")
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }

    def get_system_status(self) -> Dict:
        """Get current status of all agents and crews"""
        from circuit_breaker import get_circuit_breaker

        cb = get_circuit_breaker()
        cb_status = cb.get_status()
        cb_stats = cb.get_statistics()

        return {
            "circuit_breaker": {
                "state": cb_status['state'],
                "is_safe": cb_status['is_safe'],
                "statistics": cb_stats
            },
            "agents": {
                "market_guardian": "active" if self.market_guardian_agent else "not_initialized",
                "market_scanner": "active" if self.market_scanner_agent else "not_initialized",
                "context_analyzer": "active" if self.context_analyzer_agent else "not_initialized",
                "risk_assessment": "active" if self.risk_assessment_agent else "not_initialized",
                "strategy_executor": "active" if self.strategy_executor_agent else "not_initialized"
            },
            "crews": {
                "guardian_crew": "active" if self.guardian_crew else "not_initialized",
                "spike_trading_crew": "active" if self.spike_trading_crew else "not_initialized"
            }
        }


# Singleton instance
_agent_system_instance: Optional[MarketSpikeAgentSystem] = None


def get_agent_system() -> MarketSpikeAgentSystem:
    """Get global agent system instance (singleton)"""
    global _agent_system_instance
    if _agent_system_instance is None:
        _agent_system_instance = MarketSpikeAgentSystem()
    return _agent_system_instance


def initialize_agent_system():
    """Initialize the agent system on startup"""
    try:
        logger.info("Initializing CrewAI Market Spike Agent System...")
        system = get_agent_system()
        status = system.get_system_status()
        logger.info(f"System initialized successfully: {status}")
        return system
    except Exception as e:
        logger.error(f"Failed to initialize agent system: {e}")
        raise


if __name__ == "__main__":
    # Test the system
    print("=" * 60)
    print("CrewAI Market Spike Agent System - Test Mode")
    print("=" * 60)

    # Initialize
    system = initialize_agent_system()

    # Get status
    status = system.get_system_status()
    print("\n📊 System Status:")
    print(json.dumps(status, indent=2))

    # Test guardian monitoring
    print("\n🛡️ Testing Market Guardian...")
    guardian_result = system.monitor_market_guardian()
    print(f"Guardian Result: {guardian_result}")

    # Test spike analysis
    print("\n🔍 Testing Spike Analysis for BTCUSDT...")
    spike_result = system.analyze_spike("BTCUSDT", timeframe_minutes=5, threshold_percent=3.0)
    print(f"Spike Analysis Result: {spike_result}")

    print("\n✅ Test complete!")
