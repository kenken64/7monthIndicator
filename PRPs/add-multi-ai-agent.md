# Product Requirements Document Prompt
## CrewAI-Powered Market Spike AI Agent for Cryptocurrency Trading Bot

Please generate a comprehensive Product Requirements Document for the following enhancement:

---

## **PRODUCT CONTEXT**

### Product Information
- **Existing Product**: AI-Driven Cryptocurrency Binance Futures Trading System v3.0
- **Current Architecture**: Python
- **Primary Exchange**: Binance (Futures)
- **New Enhancement**: Market Spike AI Agent powered by CrewAI with Circuit Breaker Protection
- **Integration Type**: Embedded module within existing bot
- **Target Release**: Q4
- **Document Owner**: Kenneth Phang

### Key Features
1. **Market Spike Detection & Trading** - Identify and capitalize on sudden price movements
2. **Market Crash Circuit Breaker** - Automatically halt all bot trading when market dumps >15%

### Why CrewAI?
Describe your rationale for choosing CrewAI:
- Multi-agent collaboration for complex spike analysis
- Role-based agent specialization (analyst, risk manager, executor)
- Task orchestration capabilities
- Easy integration with existing Python infrastructure

---

## **1. EXECUTIVE SUMMARY**

Provide a 3-4 paragraph overview covering:
- Current state of your crypto trading bot (capabilities, limitations)
- What market spike opportunities are currently missed or poorly handled
- How the CrewAI-powered spike agent will enhance the bot
- Expected impact on trading performance and user value
- High-level architecture approach for embedding CrewAI

**Example Structure:**
> "Our crypto trading bot currently [describe current capabilities]. However, the bot struggles with [specific spike-related challenges like rapid price movements, flash crashes, pump-and-dump detection]. By integrating a CrewAI-powered Market Spike Agent, we will create a multi-agent system where specialized AI agents collaborate to detect, analyze, and respond to market spikes with [X]% faster detection and [Y]% improved accuracy. This enhancement will embed seamlessly into our existing infrastructure while adding minimal latency..."

---

## **2. PROBLEM STATEMENT**

### 2.1 Current Bot Limitations
**Market Spike Handling Today:**
- How does your bot currently detect price anomalies on Binance (if at all)?
- What's the average detection lag for significant price movements?
- How many profitable spike opportunities are missed per day/week?
- What's the false signal rate on current spike detection?

**Critical Gap - Market Crash Protection:**
- **Current Risk**: Bot continues trading during market-wide crashes (>15% dumps)
- **Real Scenario**: May 2021 crypto crash - Bitcoin dropped 30% in hours, altcoins 50%+
- **Problem**: Without circuit breaker, bot can:
  - Execute buy orders into falling knife scenarios
  - Open new positions during liquidation cascades
  - Deplete capital trying to "buy the dip" during capitulation
  - Get caught in flash crashes that don't recover
- **Impact**: Potential for catastrophic losses during black swan events

**Binance-Specific Challenges:**
- Binance has highest liquidity but also highest manipulation risk
- Futures market can trigger cascading liquidations affecting spot prices
- Flash crashes more severe on Binance due to high leverage usage
- Need to monitor both spot and futures for accurate market sentiment
- Binance rate limits require efficient API usage
- Multiple market types: Spot, USD-M Futures, COIN-M Futures

### 2.2 Why Current Solutions Fall Short
- Single-threaded analysis can't process multi-factor spike signals fast enough
- Lack of context-awareness (news, social sentiment, on-chain data)
- No collaborative decision-making between analysis, risk, and execution
- Difficulty distinguishing genuine opportunities from manipulated spikes

### 2.3 Desired Future State
Define success:
- Sub-second spike detection across [X] trading pairs
- Multi-dimensional analysis (price, volume, order book, on-chain metrics)
- Intelligent risk assessment before execution
- Adaptive response strategies based on spike characteristics
- Seamless operation without disrupting existing bot strategies

---

## **3. GOALS & OBJECTIVES**

### Business Goals
1. **Revenue**: Capture [X]% more profitable spike trading opportunities on Binance
2. **Risk Reduction**: Decrease false positive trades by [Y]%
3. **Capital Protection**: Prevent catastrophic losses during market crashes (>15% protection trigger)
4. **Competitive Edge**: Outperform market makers by [Z] seconds on spike detection
5. **Scalability**: Monitor [N] Binance trading pairs simultaneously without performance degradation

### User/Trader Goals
1. Never miss significant market movements during sleep/offline periods
2. Automatic intelligent response to spikes based on predefined risk preferences
3. **CRITICAL**: Automatic bot shutdown when market crashes >15% (capital preservation)
4. Confidence that risk management protects capital during volatile events
5. Clear visibility into what the AI agents are doing and why
6. Peace of mind during extreme market conditions

### Technical Goals
1. Embed CrewAI with <100ms additional latency overhead
2. Maintain existing bot stability (99.9% uptime)
3. Modular architecture allowing agent updates without bot redeployment
4. Efficient resource usage (<500MB additional memory)

### Success Metrics (KPIs)
**Detection Performance:**
- Spike detection latency: Target <500ms from Binance price change
- True positive rate: >85%
- False positive rate: <10%
- Coverage: 100% of configured Binance trading pairs

**Trading Performance:**
- Average profit per spike trade: [X]%
- Win rate on spike trades: >[Y]%
- Sharpe ratio improvement: +[Z] points
- Maximum drawdown during spikes: <[N]%

**Circuit Breaker Performance (Critical):**
- Market crash detection latency: <2 seconds from 15% dump trigger
- Bot shutdown execution time: <5 seconds after detection
- False circuit breaker triggers: <1 per month
- Capital preserved during market crashes: Track savings vs. unprotected scenario
- Recovery time after market stabilizes: <30 seconds to resume trading

**System Performance:**
- Agent response time: <1 second for analysis completion
- System uptime: 99.95%+ during volatile periods
- Memory footprint: <500MB additional
- CPU usage: <20% additional on average
- Binance API rate limit compliance: 100% (no rate limit violations)

---

## **4. CREWAI ARCHITECTURE**

### 4.1 Agent Design

Define the specialized agents in your crew:

#### **Agent 1: Market Scanner Agent**
- **Role**: "Binance Market Surveillance Specialist"
- **Goal**: "Detect anomalous price movements across all monitored Binance trading pairs in real-time"
- **Backstory**: [Create a persona - e.g., "A vigilant market watcher who never sleeps, trained on millions of Binance price patterns"]
- **Responsibilities**:
  - Stream real-time price/volume data from Binance WebSocket
  - Calculate rolling statistics (moving averages, volatility, Z-scores)
  - Identify deviations exceeding spike thresholds
  - Monitor both spot and futures markets for correlation
  - Generate spike alerts with confidence scores
- **Tools Needed**:
  - BinanceWebSocketTool (real-time price/volume feeds)
  - BinanceOrderBookTool (depth analysis)
  - StatisticalAnalysisTool (anomaly detection)
  - TimeSeriesAnalyzerTool

#### **Agent 2: Market Guardian Agent** ⚠️ **NEW - CIRCUIT BREAKER**
- **Role**: "Market Crash Protection Specialist"
- **Goal**: "Monitor market-wide conditions and immediately halt all bot trading when systemic crashes are detected"
- **Backstory**: [e.g., "A battle-tested risk manager who survived the 2021 and 2022 crypto crashes, now dedicated to protecting capital during black swan events"]
- **Responsibilities**:
  - **PRIMARY**: Continuously monitor BTC, ETH, and total market cap for >15% drops
  - Calculate market-wide sentiment (fear index, liquidation cascades)
  - Detect flash crash patterns vs. healthy corrections
  - Trigger emergency bot shutdown when crash threshold met
  - Assess market recovery conditions before allowing resume
  - Send critical alerts to user when circuit breaker activates
- **Activation Triggers**:
  - BTC drops >15% in 1 hour OR >20% in 4 hours
  - ETH drops >15% in 1 hour OR >25% in 4 hours  
  - Total market cap drops >20% in 4 hours
  - Binance futures liquidations exceed $500M in 1 hour
  - Multiple top-10 coins all down >15% simultaneously
- **Tools Needed**:
  - BinanceMarketDataTool (multi-pair price tracking)
  - MarketCapMonitorTool (total market metrics)
  - LiquidationTrackerTool (futures liquidation data)
  - BotControlTool (ability to pause/resume bot)
  - EmergencyAlertTool (critical notifications)
  - MarketRecoveryAnalyzerTool (safe to resume trading?)

#### **Agent 3: Context Analyzer Agent**
- **Role**: "Crypto Intelligence Analyst"
- **Goal**: "Provide comprehensive context for market spikes on Binance to distinguish legitimate opportunities from manipulation"
- **Backstory**: [Create a persona]
- **Responsibilities**:
  - Analyze recent news/social sentiment for the asset
  - Check on-chain metrics (large transfers, whale movements)
  - Identify correlated movements across related assets on Binance
  - Detect pump-and-dump patterns
  - Assess Binance liquidity depth and market impact
  - Cross-reference spot vs. futures price divergence
- **Tools Needed**:
  - NewsSentimentTool (crypto news aggregation)
  - TwitterSentimentTool (social buzz detection)
  - OnChainDataTool (Etherscan, BSCScan for whale movements)
  - CorrelationAnalysisTool
  - ManipulationDetectorTool
  - BinanceSpotVsFuturesTool (divergence detection)

#### **Agent 4: Risk Assessment Agent**
- **Role**: "Crypto Risk Manager"
- **Goal**: "Evaluate risk-reward profile and determine position sizing for spike opportunities while ensuring circuit breaker isn't triggered"
- **Backstory**: [Create a persona]
- **Responsibilities**:
  - Calculate position size based on account balance and volatility
  - Assess slippage risk given current Binance order book
  - Determine stop-loss and take-profit levels
  - Check correlation with existing positions
  - Validate against daily/weekly loss limits
  - **NEW**: Verify market conditions are stable (no 15% dump in progress)
  - **NEW**: Coordinate with Market Guardian before approving trades
- **Tools Needed**:
  - PortfolioAnalyzerTool
  - BinanceSlippageCalculatorTool
  - RiskMetricsCalculatorTool
  - PositionSizingOptimizerTool
  - MarketStabilityCheckerTool (communicates with Market Guardian)

#### **Agent 5: Strategy Executor Agent**
- **Role**: "Binance Trade Execution Specialist"
- **Goal**: "Execute optimal entry/exit strategies for approved spike opportunities on Binance"
- **Backstory**: [Create a persona]
- **Responsibilities**:
  - Select optimal entry strategy (market, limit, POST-ONLY)
  - Execute orders on Binance Spot or Futures
  - Monitor position and adjust stops dynamically
  - Execute exit strategy based on spike resolution
  - Log all actions for post-trade analysis
  - **NEW**: Respect circuit breaker status (no execution if guardian triggered)
- **Tools Needed**:
  - BinanceOrderExecutionTool (spot/futures orders)
  - OrderRoutingOptimizerTool
  - PositionMonitoringTool
  - ExecutionQualityAnalyzerTool
  - CircuitBreakerStatusTool

### 4.2 Task Workflow

Define the sequential or parallel tasks:

**Task 0: Market Guardian Monitoring** ⚠️ **CONTINUOUS PARALLEL TASK**
- **Agent**: Market Guardian Agent
- **Type**: Continuous background monitoring (runs independently)
- **Description**: "Continuously monitor BTC, ETH, and market-wide metrics. If any asset drops >15% in 1 hour OR total market cap drops >20% in 4 hours, immediately trigger circuit breaker to halt ALL bot trading activities"
- **Expected Output**: "Circuit breaker status: SAFE / TRIGGERED with detailed crash report"
- **Context**: Real-time Binance market data, liquidation feeds
- **Priority**: HIGHEST - Pre-empts all other tasks
- **Action on Trigger**: 
  1. Set global circuit breaker flag
  2. Cancel all pending orders
  3. Send critical alert to user
  4. Log crash event with full context
  5. Monitor for recovery conditions

**Task 1: Spike Detection**
- **Agent**: Market Scanner Agent
- **Description**: "Continuously monitor [list Binance trading pairs] and identify price movements exceeding [X]% in [Y] timeframe or volume spikes over [Z] standard deviations"
- **Expected Output**: "Spike alert with: asset, magnitude, direction, volume profile, timestamp, confidence score"
- **Context**: Real-time Binance WebSocket data
- **Pre-Check**: Verify circuit breaker is NOT active before proceeding

**Task 2: Market Stability Check**
- **Agent**: Market Guardian Agent
- **Description**: "For detected spike, verify this is an isolated event and not part of a broader market crash. Confirm circuit breaker conditions are not approaching threshold"
- **Expected Output**: "Market stability report: STABLE / WARNING / CRITICAL with current drawdown percentages"
- **Context**: Output from Task 1, current market conditions
- **Action if CRITICAL**: Abort spike trading, prepare for potential circuit breaker

**Task 3: Context Analysis**
- **Agent**: Context Analyzer Agent
- **Description**: "For detected spike, analyze: recent news sentiment, social media buzz, on-chain activity, correlated asset movements on Binance, and manipulation likelihood"
- **Expected Output**: "Context report with: spike catalyst (news/whale/unknown), manipulation probability, Binance liquidity assessment, spot vs futures divergence"
- **Context**: Outputs from Task 1 & 2
- **Condition**: Only runs if Task 2 shows STABLE market

**Task 4: Risk Evaluation**
- **Agent**: Risk Assessment Agent
- **Description**: "Evaluate trade viability considering: current portfolio exposure, account balance, market conditions, Binance slippage estimates, and risk parameters. Double-check with Market Guardian that circuit breaker is not active"
- **Expected Output**: "Risk report with: go/no-go recommendation, suggested position size, stop-loss level, take-profit targets, maximum acceptable slippage"
- **Context**: Outputs from Tasks 1, 2, 3, current portfolio state, circuit breaker status

**Task 5: Trade Execution** (Conditional)
- **Agent**: Strategy Executor Agent
- **Description**: "If approved by Risk Agent AND circuit breaker is NOT active, execute entry at optimal price on Binance, set protective stops, and monitor position until exit conditions met"
- **Expected Output**: "Execution report with: entry price, position size, stops placed, monitoring status"
- **Context**: Outputs from Tasks 1-4
- **Conditions**: 
  - Risk Assessment gives approval
  - Circuit breaker status = SAFE
  - Binance API connection healthy

**Task 6: Post-Trade Analysis** (Async)
- **Agent**: Context Analyzer Agent
- **Description**: "After position closed, analyze outcome vs. prediction to improve future spike detection"
- **Expected Output**: "Performance report for model retraining"
- **Context**: Complete trade lifecycle data

**Task 7: Recovery Assessment** (After Circuit Breaker Trigger)
- **Agent**: Market Guardian Agent
- **Description**: "After circuit breaker activation, continuously assess market recovery. When conditions normalize (no further >5% drops in 1 hour, liquidations <$100M/hr, market stable for 30+ minutes), recommend resuming bot operations"
- **Expected Output**: "Recovery status report: RECOVERING / SAFE_TO_RESUME"
- **Action**: User notification with recommendation to resume trading

### 4.3 Crew Configuration

```python
# Example crew setup structure

# Market Guardian runs as a separate continuous monitoring crew
guardian_crew = Crew(
    agents=[market_guardian_agent],
    tasks=[market_monitoring_task],
    process=Process.sequential,
    verbose=True,
    memory=True,
    max_rpm=100,
)

# Main spike detection and trading crew
spike_trading_crew = Crew(
    agents=[
        market_scanner_agent, 
        context_analyzer_agent, 
        risk_assessment_agent, 
        strategy_executor_agent
    ],
    tasks=[
        spike_detection_task,
        stability_check_task,
        context_analysis_task,
        risk_evaluation_task,
        execution_task
    ],
    process=Process.sequential,  # or Process.hierarchical for manager coordination
    verbose=True,
    memory=True,  # Enable memory for context retention
    max_rpm=100,  # Rate limiting
    # Share circuit breaker state with guardian crew
    shared_state={'circuit_breaker': CircuitBreakerState()}
)
```

**Crew Process Type**: Hybrid (Sequential for spike trading + Parallel guardian monitoring)
- **Guardian Crew**: Runs continuously in parallel, independent of spike trading
- **Spike Trading Crew**: Sequential task execution, but checks guardian status before each critical decision
- Why: Circuit breaker must operate independently to protect against all threats, not just spike-related

**Communication Between Crews**:
- Shared memory/state for circuit breaker status
- Event-driven alerts from Guardian → Spike Trading Crew
- Guardian can interrupt spike trading workflow at any point

**Memory Configuration**:
- Short-term memory: Recent spike patterns (last 24 hours), recent market crashes
- Long-term memory: Historical spike outcomes, historical crash events and recovery times
- Entity memory: Tracked assets and their spike behavior profiles, crash correlation patterns
- Shared memory: Circuit breaker state, current market health score

---

## **5. INTEGRATION ARCHITECTURE**

### 5.1 Embedding into Existing Bot

**Current Bot Architecture:**
```
[Describe your current architecture - example below]
Example:
- Main Bot Core: Python FastAPI application
- Strategy Engine: Custom trading logic (DCA, Grid, etc.)
- Exchange Connector: Binance API via python-binance library
- Database: PostgreSQL for trade history
- Message Queue: Redis for order management
- WebSocket Manager: Handles Binance real-time streams
```

**Integration Points:**

1. **Entry Point**:
   - CrewAI agents initialized on bot startup as separate threads/processes
   - **Guardian Crew**: Starts immediately, runs 24/7 as daemon
   - **Spike Trading Crew**: Event-driven initialization when spike detected

2. **Data Flow**:
   ```
   Binance WebSocket → Bot Data Adapter → Market Scanner Agent → 
   Market Guardian (Stability Check) → Context Analyzer Agent → 
   Risk Assessment Agent → [Risk Approval?] → Strategy Executor Agent → 
   Binance API (Order Placement)
   
   [PARALLEL FLOW - ALWAYS RUNNING]
   Binance WebSocket (BTC/ETH/Market) → Market Guardian Agent → 
   [Crash Detected?] → Circuit Breaker Trigger → Bot Control Interface → 
   HALT ALL BOT OPERATIONS
   ```

3. **Circuit Breaker Integration** ⚠️ **CRITICAL**:
   ```
   Market Guardian Agent
          ↓
   Circuit Breaker State Manager (Shared Memory/Redis)
          ↓
   Bot Control Interface
          ↓
   ┌─────────────────────────────────┐
   │  Blocks ALL Trading Operations: │
   │  - Existing strategies paused   │
   │  - New orders rejected          │
   │  - Pending orders cancelled     │
   │  - Spike trading disabled       │
   └─────────────────────────────────┘
   ```

4. **Existing Component Interactions**:
   - **Access Current State**: CrewAI agents query bot's portfolio manager for positions, balance, exposure
   - **Use Exchange Connectors**: CrewAI agents use bot's existing Binance connection pool (no duplicate connections)
   - **Risk Management**: CrewAI risk checks run BEFORE bot's existing risk engine (double validation)
   - **Strategy Coordination**: Circuit breaker disables ALL strategies, not just spike trading
   - **Conflict Prevention**: Spike trading gets separate order queue with priority flag

**Binance-Specific Integration:**

1. **WebSocket Connections**:
   - Reuse bot's existing Binance WebSocket connections (avoid rate limits)
   - Subscribe to additional streams if needed:
     - `!miniTicker@arr` (all market mini-ticker)
     - `btcusdt@aggTrade` (BTC aggregated trades)
     - `btcusdt@depth20@100ms` (order book updates)
     - Futures: `btcusdt_perp@forceOrder` (liquidations)

2. **API Rate Limits** (Critical for Binance):
   - Spot: 1200 requests/minute, 6100 requests/5min
   - Futures: 2400 requests/minute
   - Strategy: Prioritize WebSocket data, use REST only for execution
   - Implement request queuing to avoid bans

3. **Market Data Sources**:
   ```python
   # Primary: Binance WebSocket (real-time)
   - Price updates: <100ms latency
   - Order book: 100ms snapshots
   - Trade feed: Every trade
   
   # Fallback: Binance REST API
   - If WebSocket disconnects
   - For historical data queries
   ```

### 5.2 Technical Integration Requirements

**CrewAI Setup:**
- CrewAI version: [specify, e.g., 0.30.0+]
- LLM provider: [OpenAI GPT-4-turbo / Anthropic Claude 3.5 Sonnet / Local LLM?]
- API key management and rotation
- Fallback if LLM API is down (rule-based mode for guardian)

**Custom Tools Development:**
List tools that need to be created:

**1. Binance Integration Tools:**
   - **BinanceWebSocketTool**: Real-time price/volume subscription management
   - **BinanceOrderBookTool**: Depth analysis and liquidity assessment
   - **BinanceSpotOrderTool**: Place/cancel spot market orders
   - **BinanceFuturesDataTool**: Monitor futures prices and funding rates
   - **BinanceLiquidationTool**: Track liquidation events
   - **BinanceAccountTool**: Query balance, positions, open orders

**2. Circuit Breaker Tools** ⚠️:
   - **MarketGuardianTool**: Calculate market-wide drawdown percentages
   - **CircuitBreakerControlTool**: Set/clear circuit breaker flag
   - **BotControlTool**: Pause/resume bot operations programmatically
   - **EmergencyOrderCancelTool**: Cancel all pending orders instantly
   - **RecoveryAssessmentTool**: Evaluate if market has stabilized

**3. Analysis Tools:**
   - **OnChainDataTool**: Query Etherscan/BSCScan for whale movements
   - **SentimentAnalysisTool**: Scrape crypto news and Twitter
   - **CorrelationAnalysisTool**: Multi-asset correlation on Binance
   - **ManipulationDetectorTool**: Pump-and-dump pattern recognition
   - **PortfolioStateTool**: Access current bot portfolio
   - **RiskCalculatorTool**: Apply bot's risk rules

**State Management:**
- **Shared State**: Circuit breaker status accessible to all agents and main bot
- **Concurrency Control**: Thread-safe access to circuit breaker flag (Redis with locks)
- **State Persistence**: Agent memory + circuit breaker state survives bot restarts
- **Recovery State**: Track recovery progress after circuit breaker trigger

**Configuration Management:**
```yaml
# config/crewai_spike_agent.yaml
circuit_breaker:
  enabled: true
  thresholds:
    btc_dump_1h: 15.0  # percent
    eth_dump_1h: 15.0
    market_dump_4h: 20.0
    liquidations_1h: 500000000  # $500M
  recovery_conditions:
    stabilization_period: 1800  # 30 minutes
    max_drawdown_allowed: 5.0  # during recovery period
    min_liquidations: 100000000  # <$100M/hr
  actions_on_trigger:
    - cancel_all_orders
    - pause_all_strategies
    - close_positions: false  # optional: close all positions
    - notify_user: true
    - log_crash_event: true

spike_detection:
  enabled: true
  binance:
    spot_pairs: ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    futures_pairs: ["BTCUSDT", "ETHUSDT"]
    websocket_streams: ["!miniTicker@arr", "@depth20@100ms"]
  
agents:
  market_guardian:
    enabled: true
    priority: highest
    monitoring_interval_ms: 1000
    llm_model: "gpt-4-turbo"  # or "claude-3-5-sonnet"
  
  market_scanner:
    enabled: true
    check_circuit_breaker: true  # don't process spikes if guardian triggered
```

**Performance Considerations:**

**Latency Optimization:**
- Guardian agent checks every 1 second (configurable)
- Use cached market data where possible
- Pre-calculate rolling statistics to avoid lag
- Async/await patterns throughout
- Direct Binance WebSocket (no polling)

**Resource Management:**
- Guardian process: Dedicated CPU core, 100MB memory budget
- Spike crew: Shared resources, 400MB memory budget
- Queue depth limits: Max 10 pending spike analyses
- Agent timeout: 5 seconds max per analysis
- Graceful degradation: If guardian fails, default to SAFE mode (halt trading)

---

## **6. BINANCE & CRYPTO-SPECIFIC REQUIREMENTS**

### 6.1 Binance Market Characteristics

**24/7 Operation:**
- Continuous monitoring with no market close
- Agent fatigue prevention (rotating emphasis, periodic recalibration)
- Off-hours spike handling (lower liquidity considerations)
- Weekend volatility (traditional markets closed, crypto active)

**Binance-Specific Behaviors:**
- **Highest Liquidity**: Generally best prices and depth
- **Spot vs Futures**: Futures can lead spot on major moves
- **Liquidation Cascades**: Futures liquidations can trigger spot crashes
- **Funding Rates**: Extreme rates signal overleveraged positions
- **Binance Launchpad**: New token listings cause related asset volatility
- **Maintenance Windows**: Scheduled downtime 00:00-01:00 UTC occasionally

**Multiple Market Types on Binance:**
- **Spot**: BTCUSDT, ETHUSDT (physical settlement)
- **USD-M Futures**: BTCUSDT perpetual (cash settled)
- **COIN-M Futures**: BTCUSD quarterly (coin settled)
- Each market can show different signals

**Binance Rate Limits:**
- Spot REST: 1200 req/min, 6100 req/5min
- Futures REST: 2400 req/min
- WebSocket: 10 connections, 300 msgs/second per connection
- **Violation = IP ban**: Must carefully manage request budgets

### 6.2 Circuit Breaker Activation Criteria ⚠️

**Primary Triggers (ANY condition activates circuit breaker):**

1. **Bitcoin Crash Trigger**:
   - BTC drops >15% in 1 hour (from peak to current)
   - BTC drops >20% in 4 hours
   - BTC flash crash: >10% in 5 minutes

2. **Ethereum Crash Trigger**:
   - ETH drops >15% in 1 hour
   - ETH drops >25% in 4 hours
   - ETH flash crash: >12% in 5 minutes

3. **Market-Wide Crash Trigger**:
   - Total crypto market cap drops >20% in 4 hours
   - Top 10 coins (by market cap) all down >15% simultaneously
   - Crypto Fear & Greed Index drops to "Extreme Fear" (<10) within 1 hour

4. **Binance-Specific Triggers**:
   - Binance Futures liquidations exceed $500M in 1 hour
   - Binance spot trading volume drops >80% suddenly (exchange issue)
   - Funding rate reaches extremes (>1% 8-hour rate, indicates panic)

5. **Systemic Risk Triggers**:
   - Major stablecoin (USDT/USDC) depegs >3%
   - Large exchange (Coinbase, Kraken) reports outage/hack
   - Regulatory news indicates trading halt possibility

**Calculation Method:**
```python
# Example: BTC 15% dump in 1 hour
btc_current_price = get_binance_price("BTCUSDT")
btc_1h_high = get_rolling_high("BTCUSDT", period="1h")
drawdown = ((btc_1h_high - btc_current_price) / btc_1h_high) * 100

if drawdown >= 15.0:
    trigger_circuit_breaker(reason="BTC dropped {drawdown:.1f}% in 1 hour")
```

**False Positive Prevention:**
- Require confirmation from multiple data sources (spot + futures)
- 10-second stabilization check (ensure not just a wick)
- Verify Binance API is functioning (not data error)
- Cross-check with other exchanges for correlation

### 6.3 Circuit Breaker Actions

**Immediate Actions (within 5 seconds):**
1. Set global `CIRCUIT_BREAKER_ACTIVE = True` flag
2. Cancel ALL pending orders on Binance (spot & futures)
3. Pause ALL trading strategies (DCA, Grid, Spike, etc.)
4. Log detailed crash event with full market snapshot
5. Send CRITICAL alert to user (all channels: app, email, SMS)

**Position Management (user configurable):**
- **Option A (Conservative)**: Close all positions at market
- **Option B (Default)**: Keep positions, set tight stop-losses
- **Option C (Aggressive)**: Keep positions, no action (user monitors)

**User Notification Content:**
```
🚨 CIRCUIT BREAKER ACTIVATED 🚨

Reason: Bitcoin dropped 17.3% in 52 minutes
Current BTC: $42,150 (was $50,850)
Market Cap: -$180B (-18.5%)
Liquidations: $687M in last hour

Actions Taken:
✓ All orders cancelled
✓ All strategies paused
✓ Bot is in SAFE MODE

Your Positions:
- 0.5 BTC: -$4,350 unrealized loss
- 10 ETH: -$2,800 unrealized loss

Recommendation: Wait for market stabilization
Bot will auto-resume when safe (ETA: ~45 min)
```

### 6.4 Recovery & Resume Conditions

**Recovery Assessment (runs every 30 seconds after trigger):**

Circuit breaker will auto-clear when ALL conditions met:
1. **Stabilization Period**: No further >5% drops for 30 minutes
2. **Liquidation Slowdown**: <$100M liquidations per hour
3. **Market Recovery**: BTC recovered >50% of initial drop
4. **Volume Normalization**: Trading volume returns to >70% of average
5. **Manual Override**: User can manually resume earlier (with warning)

**Resume Process:**
1. Market Guardian sets `CIRCUIT_BREAKER_ACTIVE = False`
2. Send notification: "Market stabilized, bot resuming operations"
3. Re-enable trading strategies (user can select which ones)
4. Resume spike detection (but with increased caution for 1 hour)
5. Log recovery event for analysis

### 6.5 Spike Detection Criteria (Binance-focused)

Define Binance-specific spike types to detect:

**Type 1: Spot Price Spike (Pump/Dump)**
- Threshold: [X]% move in [Y] minutes
- Volume requirement: [Z]x average Binance spot volume
- Order book: Minimum $100K liquidity within 1%
- Examples: BTC sudden 8% pump in 10 minutes on 4x volume

**Type 2: Futures-Spot Divergence**
- Threshold: Futures price diverges >2% from spot
- Duration: Sustained for >5 minutes
- Signal: Arbitrage opportunity or forced liquidations
- Action: Trade the cheaper market (usually spot)

**Type 3: Volume Explosion**
- Threshold: Volume > 5 standard deviations from 24h average
- Price impact: Any direction (up, down, or sideways)
- Binance ranking: Coin jumps >10 positions on volume leaderboard
- Signal: Major whale accumulation or news event

**Type 4: Order Book Imbalance**
- Threshold: Bid/ask ratio > 3:1 or < 1:3 (top 10 levels)
- Size: Imbalance represents >$1M
- Duration: Sustained >30 seconds
- Signal: Incoming large market order, get ahead of it

**Type 5: Liquidation Cascade**
- Threshold: >$50M liquidations in 5 minutes for one asset
- Direction: Usually triggers opposite direction price spike
- Example: Long liquidations → price dumps → short opportunity
- Binance data: Available via `forceOrder` stream

**Type 6: News Catalyst Spike**
- Trigger: Major crypto news + immediate price reaction
- Sources: CoinDesk, CoinTelegraph, Twitter verified accounts
- Confirmation: Price moves >5% within 2 minutes of news
- Strategy: Momentum trade in direction of news sentiment

### 6.3 Manipulation Detection

**Pump-and-Dump Indicators:**
- Coordinated social media pumping
- Low liquidity + sudden volume
- New wallet addresses appearing
- Rapid reversal pattern history

**Wash Trading Detection:**
- Order patterns suggesting self-trading
- Suspicious volume without price movement
- Same addresses on both sides

**Rug Pull Signals:**
- Liquidity removal detection
- Token contract anomalies
- Developer wallet dumping

**Risk Mitigation:**
- Blacklist known pump groups/tokens
- Minimum liquidity requirements
- Maximum position size on suspicious spikes

### 6.4 On-Chain Data Integration

**Data Sources:**
- Ethereum: Etherscan API, Alchemy, Infura
- BSC: BscScan API
- Solana: Solana Beach, SolScan
- Multi-chain: The Graph, Dune Analytics

**Key Metrics to Monitor:**
- Large token transfers (whale alerts)
- DEX liquidity adds/removes
- Smart contract interactions (liquidations, swaps)
- Gas prices (network congestion indicator)
- Wallet clustering (coordinated activity)

**Integration Method:**
- Real-time webhook subscriptions where available
- Polling intervals for others ([specify frequency])
- Caching to avoid rate limits

---

## **7. FUNCTIONAL REQUIREMENTS**

### 7.0 Circuit Breaker Features ⚠️ **HIGHEST PRIORITY**

**Must Have:**
- [ ] Continuous monitoring of BTC, ETH, and total market cap
- [ ] Automatic detection of >15% dumps within 1 hour
- [ ] Immediate bot shutdown (<5 seconds from detection to halt)
- [ ] Cancellation of all pending Binance orders
- [ ] Pause of all trading strategies (not just spike agent)
- [ ] Critical alert notification to user (all channels)
- [ ] Detailed crash event logging with full market context
- [ ] Automatic recovery assessment and resume capability
- [ ] Manual override to resume trading early (with warnings)
- [ ] False positive prevention (multi-source confirmation)

**Should Have:**
- [ ] Configurable circuit breaker thresholds per asset
- [ ] Multiple severity levels (WARNING / CRITICAL)
- [ ] Optional automatic position closing on trigger
- [ ] Historical crash event database for pattern learning
- [ ] Graduated resume (start with small positions)
- [ ] Dry-run mode for testing circuit breaker without real impact

**Could Have:**
- [ ] Predictive crash probability (AI predicts crash before it happens)
- [ ] Smart position hedging (auto-open shorts on crash detection)
- [ ] Social sentiment integration (detect panic before price crashes)
- [ ] Integration with hardware kill switch (physical button to halt trading)

### 7.1 Core Spike Detection Features

**Must Have:**
- [ ] Real-time monitoring of [specify: 10, 20, 50+] Binance trading pairs
- [ ] Multi-timeframe analysis (1m, 5m, 15m, 1h)
- [ ] Configurable spike thresholds per trading pair
- [ ] Bidirectional detection (pumps and dumps)
- [ ] Confidence scoring for each detected spike
- [ ] Deduplication of spike alerts (don't alert on same spike multiple times)
- [ ] Integration with circuit breaker (no spike trading during crash)
- [ ] Spot and futures market monitoring
- [ ] Respect Binance rate limits (no API bans)

**Should Have:**
- [ ] Futures-spot divergence detection
- [ ] Historical spike pattern matching
- [ ] Spike severity classification (minor, moderate, major, extreme)
- [ ] Predicted spike duration estimation
- [ ] Related asset co-movement detection on Binance
- [ ] Liquidation cascade detection

**Could Have:**
- [ ] Predictive spike probability (pre-spike signals)
- [ ] Spike type classification (news-driven, whale-driven, technical, etc.)
- [ ] Market microstructure analysis (spoofing, layering detection)
- [ ] Cross-exchange comparison (Binance vs. Coinbase prices)

### 7.2 Context Analysis Features

**Must Have:**
- [ ] Recent news sentiment for spiking asset (last 24 hours)
- [ ] Order book liquidity assessment
- [ ] Basic manipulation probability score
- [ ] Correlation with BTC/ETH (market-wide movement check)

**Should Have:**
- [ ] Social media sentiment analysis (Twitter, Reddit)
- [ ] On-chain large transfer detection (whale movements)
- [ ] Trading volume authenticity verification
- [ ] Historical behavior analysis for this asset
- [ ] Sector/category-wide movement analysis

**Could Have:**
- [ ] Natural language explanation of spike cause
- [ ] News source credibility scoring
- [ ] Influencer impact analysis
- [ ] Protocol-specific event detection (governance, upgrades)

### 7.3 Risk Management Features

**Must Have:**
- [ ] Circuit breaker status check before any trade
- [ ] Position size calculation based on account risk percentage
- [ ] Stop-loss placement recommendations
- [ ] Binance slippage estimation before execution
- [ ] Maximum concurrent spike trades limit
- [ ] Daily loss limit enforcement
- [ ] Correlation check with existing positions
- [ ] Market stability verification (no crash in progress)

**Should Have:**
- [ ] Dynamic position sizing based on confidence score AND market conditions
- [ ] Multi-level take-profit targets
- [ ] Trailing stop-loss during favorable moves
- [ ] Portfolio heat map (total risk exposure)
- [ ] Kelly Criterion or similar optimal sizing
- [ ] Reduced position sizes during high volatility periods
- [ ] Increased caution for 1 hour after circuit breaker recovery

**Could Have:**
- [ ] Options hedging suggestions for large positions
- [ ] Cross-market position netting (spot + futures)
- [ ] Correlation-adjusted portfolio risk
- [ ] VaR (Value at Risk) calculations

### 7.4 Execution Features

**Must Have:**
- [ ] Verify circuit breaker is NOT active before execution
- [ ] Binance market order execution capability
- [ ] Binance limit order with timeout
- [ ] Automatic stop-loss placement
- [ ] Position monitoring until exit
- [ ] Execution retry logic on failures
- [ ] Partial fill handling
- [ ] Order cancellation when circuit breaker triggers

**Should Have:**
- [ ] Smart order routing (spot vs. futures)
- [ ] POST-ONLY orders to avoid taker fees when possible
- [ ] Iceberg orders (hidden volume) for large positions
- [ ] Bracket orders (entry, SL, TP all at once)
- [ ] TWAP (Time-Weighted Average Price) for large positions

**Could Have:**
- [ ] Flash loan integration for undercollateralized positions
- [ ] Futures hedging (open opposing futures position)
- [ ] MEV protection strategies

### 7.5 Monitoring & Reporting

**Must Have:**
- [ ] Real-time spike alert feed
- [ ] **Circuit breaker status dashboard** (prominent display)
- [ ] **Crash event log** with full market snapshots
- [ ] Agent decision logs (why each action was taken)
- [ ] Trade execution history
- [ ] Performance dashboard (win rate, P&L, etc.)
- [ ] Error logging and alerting
- [ ] Binance API health monitoring

**Should Have:**
- [ ] Historical spike database with outcomes
- [ ] Agent performance metrics (accuracy per agent)
- [ ] Comparative analysis (spike trades vs. regular trades)
- [ ] Configuration audit trail
- [ ] A/B testing framework for agent prompts
- [ ] **Circuit breaker test mode** (simulate crashes)
- [ ] Recovery time analytics (how long until market stabilizes)

**Could Have:**
- [ ] ML model drift detection
- [ ] Agent conversation replay (debugging)
- [ ] Simulation mode (paper trading spikes)
- [ ] Video recording of crash events (chart snapshots)

---

## **8. NON-FUNCTIONAL REQUIREMENTS**

### 8.1 Performance

- **Spike Detection Latency**: <500ms from price change to alert
- **Agent Analysis Time**: <2 seconds for complete crew workflow
- **Order Execution Time**: <1 second from approval to exchange
- **System Throughput**: Handle [X] spike events per minute
- **Concurrent Monitoring**: [N] trading pairs without degradation

### 8.2 Reliability

- **Uptime**: 99.95%+ during market hours (24/7 for crypto)
- **Fault Tolerance**: Graceful degradation if one agent fails
- **Data Accuracy**: >99.9% (no ghost spikes from bad data)
- **Idempotency**: Same spike detected only once
- **Disaster Recovery**: Resume within [X] minutes of failure

### 8.3 Scalability

- **Horizontal Scaling**: Support for distributed agent deployment
- **Vertical Scaling**: Efficient use of resources up to [X] pairs
- **Database Scaling**: Handle [Y] spike records per day
- **API Rate Limits**: Stay within exchange limits (graceful backoff)

### 8.4 Security

- **API Key Protection**: Encrypted storage, no hardcoded secrets
- **Exchange Account Security**: 2FA, IP whitelisting, withdrawal limits
- **Audit Logging**: All trading decisions and executions logged
- **Access Control**: Role-based access to agent configuration
- **Data Privacy**: No sensitive data sent to external LLM APIs

### 8.5 Maintainability

- **Code Quality**: Type hints, docstrings, unit tests (>80% coverage)
- **Configuration**: All parameters in config files (not hardcoded)
- **Logging**: Structured logging (JSON) for easy parsing
- **Monitoring**: Prometheus/Grafana metrics export
- **Documentation**: Architecture diagrams, API docs, runbooks

### 8.6 Testability

- **Unit Tests**: Each tool and agent testable in isolation
- **Integration Tests**: Crew workflows testable end-to-end
- **Simulation Mode**: Paper trading mode for safe testing
- **Backtesting**: Historical spike data replay
- **Chaos Engineering**: Resilience testing (API failures, etc.)

---

## **9. USER INTERFACE & CONTROLS**

### 9.1 Configuration Interface

**Circuit Breaker Configuration** ⚠️ **TOP PRIORITY**:
```yaml
circuit_breaker:
  enabled: true  # Master switch
  
  # Crash detection thresholds
  thresholds:
    btc:
      dump_1h_percent: 15.0
      dump_4h_percent: 20.0
      flash_crash_5m_percent: 10.0
    eth:
      dump_1h_percent: 15.0
      dump_4h_percent: 25.0
      flash_crash_5m_percent: 12.0
    market_wide:
      total_mcap_4h_percent: 20.0
      top10_simultaneous_percent: 15.0
    binance_specific:
      liquidations_1h_usd: 500000000  # $500M
      funding_rate_extreme: 1.0  # 1% per 8h
  
  # What to do when triggered
  actions:
    cancel_all_orders: true
    pause_all_strategies: true
    close_all_positions: false  # Conservative: true, Aggressive: false
    set_tight_stops: true  # If not closing positions
    notify_channels: ["app", "email", "sms", "telegram"]
  
  # Recovery conditions
  recovery:
    auto_resume: true
    stabilization_minutes: 30
    max_drop_during_recovery: 5.0
    min_volume_recovery_percent: 70
    require_btc_50pct_recovery: true
    manual_override_allowed: true
```

**Agent Configuration:**
- Enable/disable entire CrewAI spike agent
- Enable/disable Market Guardian separately (circuit breaker)
- Enable/disable individual agents within crew
- Adjust agent prompts/instructions
- Set LLM model and parameters (temperature, etc.)

**Spike Detection Settings:**
```yaml
spike_detection:
  enabled: true
  check_circuit_breaker: true  # Don't trade spikes during crashes
  
  binance:
    spot_pairs: ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
    futures_pairs: ["BTCUSDT", "ETHUSDT"]
    monitor_liquidations: true
    
  thresholds:
    default:
      price_change_percent: 5.0
      timeframe_minutes: 5
      volume_multiplier: 2.0
      min_liquidity_usd: 100000
    
    # Per-pair overrides (Binance specific)
    BTCUSDT:
      price_change_percent: 3.0  # Less volatile
    SOLUSDT:
      price_change_percent: 10.0  # More volatile
  
  filters:
    max_spread_percent: 2.0
    blacklisted_tokens: []
    min_24h_volume_usd: 10000000
```

**Risk Management Settings:**
```yaml
risk_management:
  # Position sizing
  max_position_size_percent: 5.0  # of total portfolio
  max_concurrent_spikes: 3
  
  # Loss limits
  daily_loss_limit_percent: 10.0
  per_trade_max_loss: 2.0
  
  # During/after crashes
  reduce_size_after_circuit_breaker: true  # 50% of normal for 1 hour
  increase_stops_after_crash: true  # Tighter stops
  
  # Exit parameters
  stop_loss_percent: 2.0
  take_profit_percent: 8.0
  max_slippage_percent: 1.0
  trailing_stop_enabled: true
```

**Execution Settings:**
```yaml
execution:
  mode: "auto"  # auto, semi-auto, alert-only
  
  binance:
    order_type: "market"  # market, limit, post_only
    time_in_force: "gtc"  # gtc, ioc, fok
    use_futures: false  # Trade on futures market
    leverage: 1  # If using futures
    
  retry:
    max_attempts: 3
    delay_seconds: 1
    exponential_backoff: true
  
  respect_circuit_breaker: true  # CRITICAL: Don't execute if guardian triggered
```

### 9.2 Monitoring Dashboard

**Circuit Breaker Status Panel** ⚠️ **(TOP OF DASHBOARD)**:
```
┌─ MARKET GUARDIAN STATUS ─────────────────────────┐
│ Status: 🟢 SAFE / 🔴 TRIGGERED                   │
│                                                    │
│ Current Drawdowns:                                │
│ BTC:  -2.3% (1h)  | Threshold: -15%  [████░░░░]  │
│ ETH:  -3.1% (1h)  | Threshold: -15%  [█████░░░]  │
│ Market: -4.2% (4h) | Threshold: -20%  [████░░░░] │
│                                                    │
│ Liquidations (1h): $87M / $500M      [███░░░░░░]  │
│                                                    │
│ Last Trigger: 2 days ago (BTC -18% crash)         │
│ Downtime: 47 minutes | Capital Saved: ~$3,200     │
│                                                    │
│ [Test Circuit Breaker] [View History]             │
└────────────────────────────────────────────────────┘
```

**Real-Time View:**
- Active spike alerts (scrolling feed)
- Agent status indicators (working, idle, error)
- Current positions opened from spikes
- Live P&L for spike trades
- Binance API connection health
- Rate limit usage (percentage of limit used)

**Historical View:**
- Spike detection history (table/chart)
- Circuit breaker activation log
- Win/loss statistics by spike type
- Agent performance metrics
- Missed opportunities analysis
- Recovery times after crashes

**Controls:**
- **EMERGENCY STOP** button (halt all spike trading immediately)
- Circuit breaker manual trigger (test or force activation)
- Manual spike submission (user-identified opportunity)
- Override specific agent decision
- Adjust thresholds on the fly
- Resume after circuit breaker (with confirmation)

### 9.3 Alert & Notification System

**Alert Channels:**
- [ ] In-app notifications (web/mobile)
- [ ] Email alerts
- [ ] SMS for CRITICAL events only
- [ ] Telegram bot integration
- [ ] Discord webhook
- [ ] Custom webhook endpoint

**Alert Levels:**
- **Info**: Spike detected but didn't meet entry criteria
- **Warning**: Market Guardian detects approaching crash threshold (BTC -12%)
- **High**: Spike auto-traded, monitor position
- **CRITICAL**: Circuit breaker activated, bot halted

**Circuit Breaker Alert Content:**
```
🚨🚨🚨 CIRCUIT BREAKER ACTIVATED 🚨🚨🚨

Trigger: Bitcoin crashed 17.3% in 52 minutes
Time: 2024-03-15 14:27:18 UTC

Market Snapshot:
- BTC: $42,150 ← $50,850 (-17.3%)
- ETH: $2,240 ← $2,680 (-16.4%)
- Total Market: $1.82T ← $2.14T (-15.0%)
- Liquidations: $687M (last hour)

Your Portfolio Impact:
- Unrealized Loss: -$7,150 (-8.3%)
- Open Positions: 2 (BTC, ETH)
- Orders Cancelled: 5
- All strategies: PAUSED

Actions Taken:
✓ All pending orders cancelled
✓ Bot trading completely halted
✓ Tight stops set on existing positions
✓ Market recovery monitoring active

What Happens Next:
⏳ Bot will monitor market for stabilization
⏳ Auto-resume when safe (est. 30-60 min)
⚠️ You can manually resume earlier (risky)

[View Details] [Manual Resume] [Close Positions]
```

**Recovery Notification:**
```
✅ Market Stabilized - Bot Resuming

Recovery Time: 43 minutes
BTC Recovered: 52% of drop (now $46,220)
Market Stable: Yes (no drops >5% for 30 min)

Your Portfolio:
- Final Impact: -$2,340 (-2.7%)
- Positions: 2 still open
- Status: All strategies re-enabled

Circuit Breaker Protection Saved: ~$4,810

Bot is now active and trading normally.
[Dashboard] [Settings]
```

---

## **10. DATA REQUIREMENTS**

### 10.1 Real-Time Data Streams

**Exchange Data:**
- OHLCV (Open, High, Low, Close, Volume) - per second updates
- Order book snapshots - top 20 levels, <100ms latency
- Trade feed - all trades as they occur
- Ticker data - best bid/ask, 24h stats

**Data Sources:**
- [ ] Binance WebSocket
- [ ] Coinbase WebSocket
- [ ] Kraken WebSocket
- [ ] Aggregate via [your data provider]

### 10.2 Historical Data

**Backtesting Dataset:**
- Minimum [X] months of historical spike data
- Labeled outcomes (profitable, unprofitable, false positive)
- Market conditions during each spike (bull, bear, sideways)

**Training Data for ML Models:**
- Feature engineering dataset
- Spike patterns library
- Asset behavior profiles

### 10.3 External Data

**News & Sentiment:**
- CryptoNews APIs
- Twitter API (X) with crypto keywords
- Reddit r/cryptocurrency, asset-specific subs
- Telegram crypto channels

**On-Chain Data:**
- Blockchain explorer APIs
- DEX aggregators (1inch, CoinGecko)
- Analytics platforms (Glassnode, Nansen)

**Market Data:**
- Crypto Fear & Greed Index
- Funding rates (perpetual futures)
- Options market (put/call ratios)

### 10.4 Data Storage

**Time-Series Database:**
- Tick data: [retention period]
- Spike events: permanent
- Agent decisions: [retention period]

**Relational Database:**
- Configuration history
- User preferences
- Trade ledger
- Performance analytics

**Cache Layer:**
- Redis for frequently accessed data
- API response caching
- Agent memory (recent context)

---

## **11. DEPENDENCIES & INTEGRATION**

### 11.1 Internal Dependencies

**Existing Bot Components:**
- [ ] Exchange connector module (version/status)
- [ ] Portfolio manager (version/status)
- [ ] Risk engine (version/status)
- [ ] Order execution engine (version/status)
- [ ] Database layer (version/status)

**Required Updates to Existing Components:**
- Exchange connector: Add spike-specific data subscriptions
- Portfolio manager: Expose API for agent queries
- Risk engine: Accept risk checks from external source (CrewAI)
- Order execution: Priority queue for spike trades

### 11.2 External Dependencies

**CrewAI Framework:**
- [ ] crewai library (version X.Y.Z)
- [ ] crewai-tools (version X.Y.Z)
- [ ] Required Python version

**LLM Provider:**
- [ ] OpenAI API (GPT-4 recommended) OR
- [ ] Anthropic API (Claude 3.5 Sonnet) OR
- [ ] Local LLM (Ollama, llama.cpp)
- API key management strategy
- Cost estimation: [$X per 1000 spike analyses]

**Python Libraries:**
- [ ] langchain / langchain-community
- [ ] pydantic for data validation
- [ ] asyncio for async operations
- [ ] ccxt for exchange integration
- [ ] web3.py for on-chain data
- [ ] pandas/numpy for data analysis

**External APIs:**
- [ ] CoinGecko API (pricing fallback)
- [ ] Etherscan API (on-chain data)
- [ ] News APIs (news sentiment)
- [ ] Twitter API (social sentiment)

### 11.3 Infrastructure

**Compute Resources:**
- CPU: [requirements]
- Memory: [requirements]
- Storage: [requirements]
- Network: Low latency connection to exchanges

**Deployment:**
- Containerization: Docker
- Orchestration: [Docker Compose, Kubernetes, none]
- Cloud provider: [AWS, GCP, Azure, on-premise]

---

## **12. DEVELOPMENT PLAN**

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Basic CrewAI integration with one simple agent

- [ ] Set up CrewAI development environment
- [ ] Create Market Scanner Agent (basic spike detection)
- [ ] Develop initial custom tools (ExchangeDataTool)
- [ ] Integrate with existing bot's data pipeline
- [ ] Unit tests for tools and agent

**Deliverable**: Single agent detecting spikes, outputting to logs

### Phase 2: Multi-Agent Crew (Weeks 3-4)
**Goal**: Complete crew with all four agents collaborating

- [ ] Develop Context Analyzer Agent
- [ ] Develop Risk Assessment Agent
- [ ] Develop Strategy Executor Agent
- [ ] Create task workflow and handoffs
- [ ] Implement crew memory and context sharing

**Deliverable**: Full crew analyzing spikes, recommending trades (not executing)

### Phase 3: Risk-Safe Execution (Weeks 5-6)
**Goal**: Live execution with strict risk controls

- [ ] Integrate with bot's order execution engine
- [ ] Implement all risk management checks
- [ ] Add position monitoring and exit logic
- [ ] Create emergency stop mechanisms
- [ ] Comprehensive integration testing

**Deliverable**: Live trading with small position limits

### Phase 4: Production Hardening (Weeks 7-8)
**Goal**: Production-ready with monitoring and error handling

- [ ] Implement monitoring dashboard
- [ ] Add logging and alerting
- [ ] Performance optimization (latency reduction)
- [ ] Failure recovery mechanisms
- [ ] Load testing with multiple concurrent spikes

**Deliverable**: Production-ready system

### Phase 5: Enhancement & Scaling (Weeks 9-12)
**Goal**: Advanced features and scale to more pairs

- [ ] Add on-chain data integration
- [ ] Implement advanced manipulation detection
- [ ] Scale to [X] trading pairs
- [ ] A/B testing framework
- [ ] ML model continuous learning

**Deliverable**: Enhanced system with full feature set

---

## **13. TESTING STRATEGY**

### 13.1 Unit Testing
- Individual tool functions (>80% coverage target)
- Agent prompt/response validation
- Risk calculation logic
- Data parsing and transformation

### 13.2 Integration Testing
- End-to-end crew workflows
- Interaction with existing bot components
- Exchange API integration (testnet/sandbox)
- Database read/write operations

### 13.3 Simulation Testing
**Paper Trading Mode:**
- Run against live market data
- Execute "virtual" trades
- Track what P&L would have been
- Validate agent decisions without risk

**Historical Backtesting:**
- Replay historical spike events
- Measure detection accuracy
- Calculate strategy performance metrics
- Compare to baseline (no spike agent)

### 13.4 Chaos Engineering
**Failure Scenarios:**
- [ ] Exchange API timeout
- [ ] LLM API downtime
- [ ] Database connection loss
- [ ] Network partition
- [ ] Out of memory condition
- [ ] Malformed data handling

**Expected Behavior:**
- Graceful degradation (disable spike trading, continue regular bot)
- Clear error messages and alerts
- Automatic recovery when services return
- No data corruption or orphaned trades

### 13.5 Performance Testing
- Load testing: [X] concurrent spike events
- Stress testing: Peak market volatility simulation
- Latency testing: Measure each component's latency
- Memory profiling: Check for leaks over 24h run

### 13.6 Security Testing
- API key exposure check
- SQL injection on user inputs
- Rate limit compliance testing
- Access control validation

---

## **14. RISKS & MITIGATION**

### 14.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM API downtime causes missed spikes | Medium | High | Implement fallback to rule-based detection; cache common LLM responses |
| CrewAI adds too much latency (>5s) | Medium | High | Optimize prompts; use parallel tasks; set strict timeouts; consider local LLM |
| Agent makes catastrophic trading decision | Low | Critical | Multi-layer risk checks; kill switches; strict position limits; human-in-loop for large trades |
| Memory leak causes bot crash | Low | High | Rigorous memory profiling; periodic agent restarts; monitoring alerts |
| Data feed outage creates ghost spikes | Medium | Medium | Multi-source validation; outlier detection; exchange connectivity monitoring |

### 14.2 Market Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Pump-and-dump scheme causes losses | High | Medium | Manipulation detection; liquidity requirements; smaller position sizes; fast exits |
| Flash crash triggers inappropriate trades | Medium | High | Circuit breakers; volatility filters; human confirmation for extreme moves |
| Slippage exceeds expectations | Medium | Medium | Order book depth analysis; slippage limits; split orders |
| Correlated spikes drain account | Low | Critical | Portfolio-level risk limits; correlation checks; daily loss limits |

### 14.3 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Configuration error disables spike detection | Medium | Medium | Config validation; automated tests; gradual rollout |
| Bugs in production cause losses | Low | Critical | Extensive testing; gradual feature rollout; easy rollback mechanism |
| Cost overruns from LLM API usage | Medium | Low | Set API budget limits; optimize token usage; monitor costs |
| User misconfigures agent (too aggressive) | High | Medium | Sensible defaults; configuration validation; warning messages |

---

## **15. SUCCESS CRITERIA & VALIDATION**

### 15.1 Launch Criteria (Go/No-Go Checklist)

**Functionality:**
- [ ] All four agents functioning correctly
- [ ] Spike detection accuracy >80% on validation set
- [ ] Risk management enforcing all limits
- [ ] Successful completion of 100 paper trades with 0 rule violations

**Performance:**
- [ ] Average detection latency <500ms (measured over 1000 spikes)
- [ ] Agent analysis completion <3s (p95)
- [ ] Zero crashes during 72-hour continuous operation
- [ ] Memory usage stable over 24-hour run

**Integration:**
- [ ] No negative impact on existing bot strategies
- [ ] Compatible with bot's existing risk engine
- [ ] All existing bot features still functional
- [ ] Configuration changes possible without bot restart

**Safety:**
- [ ] Emergency stop mechanism tested and working
- [ ] Position size limits enforced correctly
- [ ] Daily loss limit triggers correctly
- [ ] Cannot open more than max concurrent positions

### 15.2 Phase 1 Success Metrics (First 2 Weeks Live)

**Target Goals:**
- Detect >90% of genuine market spikes (validated manually)
- False positive rate <20%
- Zero critical bugs causing unintended trades
- Zero position size limit violations
- System uptime >99%

**Expected Performance:**
- 5-10 spike trades per day (across all pairs)
- Win rate >50%
- Average win size > average loss size
- Maximum drawdown <3% of account

**Learning Outcomes:**
- Identify most common false positive patterns
- Calibrate thresholds per trading pair
- Validate agent decision logic
- Gather data for model improvements

### 15.3 Phase 2 Success Metrics (Month 1-3)

**Performance Targets:**
- Win rate >60% on spike trades
- Sharpe ratio of spike trades >1.5
- Contribution to overall bot profit: +[X]%
- Average spike profit: [Y]% of position
- Detection accuracy >90%

**Operational Targets:**
- System uptime >99.9%
- Average detection latency <400ms
- Zero uncontrolled losses (all risk limits held)
- Configuration changes deployed <1hr

**Feature Completeness:**
- All "Must Have" features deployed
- 80% of "Should Have" features deployed
- User satisfaction score >4/5

### 15.4 Long-Term Success (6+ Months)

**Business Impact:**
- Overall bot profitability increased by [X]%
- Spike-specific strategies generating [Y]% of profits
- User retention improved by [Z]%
- Competitive advantage in spike detection

**Technical Maturity:**
- Agent learning from historical outcomes
- Adaptive thresholds self-optimizing
- Less than [N] false positives per day
- Minimal manual intervention required

---

## **16. ROLLOUT & DEPLOYMENT**

### 16.1 Alpha Phase (Internal Testing)

**Duration**: 2 weeks
**Participants**: Development team only
**Scope**:
- 3-5 trading pairs (high liquidity: BTC, ETH, SOL)
- Small position sizes (max $100 per trade)
- Alert-only mode (no auto-execution initially)

**Objectives**:
- Validate agent communication
- Tune spike detection thresholds
- Fix critical bugs
- Establish baseline metrics

**Exit Criteria**:
- 100 spike events analyzed
- All critical bugs resolved
- Detection latency <1s
- Zero crashes

### 16.2 Beta Phase (Limited Users)

**Duration**: 4 weeks
**Participants**: 10-20 selected users (opt-in)
**Scope**:
- 10-20 trading pairs
- Medium position sizes (up to 2% of account)
- Semi-auto mode (agents recommend, users approve)

**Objectives**:
- Gather user feedback
- Validate in diverse market conditions
- Identify edge cases
- Measure real trading performance

**Exit Criteria**:
- 500+ spike events processed
- Win rate >55%
- User satisfaction >4/5
- No critical bugs

### 16.3 General Availability

**Rollout Strategy**: Gradual rollout
- Week 1: 10% of users (lowest risk profiles)
- Week 2: 25% of users
- Week 3: 50% of users
- Week 4: 100% of users

**Feature Flags**:
- Ability to disable for individual users if issues arise
- Gradual increase in max position sizes
- Phased rollout of advanced features

**Communication**:
- Release notes and documentation
- Video tutorial on configuring agents
- FAQ and troubleshooting guide
- Office hours for user questions

### 16.4 Rollback Plan

**Triggers for Rollback**:
- Critical bug causing unintended trades
- System instability affecting main bot
- Detection accuracy drops below 70%
- Multiple user complaints about losses

**Rollback Procedure**:
1. Immediately disable CrewAI spike agent via feature flag
2. Allow existing positions to close normally
3. Investigate root cause
4. Fix and redeploy to alpha environment
5. Re-validate before re-enabling

---

## **17. COST ANALYSIS**

### 17.1 Development Costs

- Developer time: [X] weeks × [Y] engineers = [Z] hours
- Infrastructure setup: [cost]
- Testing environment: [cost]
- Total development: $[amount]

### 17.2 Operational Costs

**LLM API Costs:**
- Estimated API calls per day: [N]
- Tokens per call (avg): [M]
- Cost per 1M tokens: $[X]
- Monthly LLM cost: $[amount]

**Infrastructure:**
- Additional server resources: $[amount]/month
- Database storage: $[amount]/month
- Data API subscriptions: $[amount]/month
- Total monthly operational: $[amount]

### 17.3 ROI Projection

**Assumptions:**
- 10 profitable spike trades per day
- Average profit per trade: [X]%
- Average position size: $[Y]
- Monthly trading days: 30

**Projected Revenue:**
- Monthly profit: $[calculated]
- Annual profit: $[calculated]
- Break-even: [N] months

---

## **18. DOCUMENTATION REQUIREMENTS**

### 18.1 User Documentation
- [ ] Quick start guide for enabling spike agent
- [ ] Configuration reference (all parameters explained)
- [ ] Best practices for threshold tuning
- [ ] Troubleshooting guide
- [ ] FAQ

### 18.2 Technical Documentation
- [ ] Architecture diagram (system overview)
- [ ] Agent interaction diagram (sequence flows)
- [ ] API reference (for custom tool development)
- [ ] Data model documentation
- [ ] Deployment guide

### 18.3 Operational Documentation
- [ ] Monitoring dashboard guide
- [ ] Alerting runbook (how to respond to alerts)
- [ ] Incident response procedures
- [ ] Performance tuning guide
- [ ] Backup and recovery procedures

---

## **19. OPEN QUESTIONS**

List questions that need answers before proceeding:

1. **LLM Provider**: OpenAI vs. Anthropic vs. local LLM? (cost, latency, quality tradeoffs)
2. **Agent Autonomy**: Fully autonomous or human-in-the-loop for large trades?
3. **Threshold Tuning**: Manual vs. ML-based adaptive thresholds?
4. **Multi-Exchange Execution**: Should spike trades execute across multiple exchanges simultaneously?
5. **Memory Duration**: How long should agents remember past spike patterns (hours, days, weeks)?
6. **Failure Mode**: If risk agent rejects, should we alert user or silently skip?
7. **Cost Limits**: What's our monthly budget for LLM API calls?
8. **Slippage Tolerance**: What's acceptable slippage before aborting trade?
9. **Correlation Handling**: How to handle multiple correlated assets spiking simultaneously?
10. **User Control**: Should users be able to edit agent prompts directly?

---

## **20. APPENDICES**

### Appendix A: Glossary

- **Spike**: A rapid price movement exceeding defined thresholds
- **CrewAI**: Multi-agent orchestration framework
- **Agent**: An AI entity with specific role, goal, and tools
- **Task**: A specific job assigned to an agent
- **Crew**: A group of agents working together
- **Tool**: A function that agents can call to interact with systems
- **Pump**: Sudden upward price movement
- **Dump**: Sudden downward price movement
- **Slippage**: Difference between expected and actual execution price
- **Flash Crash**: Extreme rapid price drop (often recovers quickly)
- **Whale**: Large holder whose trades significantly impact price
- **On-Chain**: Data stored on blockchain (vs. exchange internal data)

### Appendix B: CrewAI Prompt Examples

**Market Scanner Agent Prompt:**
```
You are an expert crypto market surveillance specialist. Your job is to continuously monitor price and volume data across cryptocurrency markets and identify anomalous movements that could represent trading opportunities.

Your specific responsibilities:
1. Analyze real-time price changes across all monitored trading pairs
2. Calculate statistical deviations from normal behavior
3. Identify volume spikes that accompany price movements
4. Assign confidence scores to detected anomalies
5. Generate structured spike alerts for further analysis

Focus on precision and speed. False negatives (missed spikes) are acceptable, but minimize false positives (alerting on non-spikes) as they waste resources.

Output format: JSON with spike details including asset, magnitude, direction, volume, timestamp, and confidence score.
```

### Appendix C: Example Tool Implementation

```python
from crewai_tools import tool

@tool("Exchange Data Tool")
def get_current_price(symbol: str, exchange: str = "binance") -> dict:
    """
    Fetches current price and volume data for a trading pair.
    
    Args:
        symbol: Trading pair (e.g. "BTC/USDT")
        exchange: Exchange name (default: binance)
    
    Returns:
        dict with price, volume, bid, ask, timestamp
    """
    # Your implementation here using existing bot's exchange connector
    pass
```

### Appendix D: Risk Calculation Formulas

**Position Size Formula:**
```
position_size = (account_balance * risk_percent) / stop_loss_distance
```

**Kelly Criterion:**
```
kelly_percent = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
position_size = kelly_percent * account_balance * kelly_fraction
```

### Appendix E: Backtesting Data Requirements

- Historical OHLCV data: 1-minute granularity, 6+ months
- Labeled spike events with outcomes
- Market condition tags (bull/bear/sideways)
- Exchange downtime periods to exclude
- Known manipulation events to train on

---

## **APPROVAL & SIGN-OFF**

This PRD must be reviewed and approved by:

- [ ] **Product Owner**: _________________ Date: _______
- [ ] **Lead Developer**: _________________ Date: _______
- [ ] **Data Scientist/ML Engineer**: _________________ Date: _______
- [ ] **Risk Manager**: _________________ Date: _______
- [ ] **DevOps Engineer**: _________________ Date: _______

**Version History:**
- v1.0 - [Date] - Initial draft
- v1.1 - [Date] - Incorporated feedback from [team]

**Next Review Date**: _________________

---

## **HOW TO USE THIS PROMPT**

1. **Fill in all bracketed fields** with your specific information
2. **Customize sections** based on your bot's current architecture
3. **Remove irrelevant sections** (e.g., if not using certain features)
4. **Add sections** specific to your needs
5. **Review with your team** before finalizing
6. **Feed to AI** (Claude, GPT-4) to generate detailed PRD content
7. **Iterate** based on AI output and team feedback

**Pro Tips:**
- Be specific about current pain points and desired outcomes
- Include actual performance metrics from your current bot
- Reference specific crypto pairs you want to focus on
- Clarify your LLM budget constraints early
- Consider starting with a smaller scope for faster MVP

This document should evolve as you learn from implementation!
