# CrewAI Integration Guide

## Overview

Your trading bot now has **CrewAI Multi-Agent AI System** fully integrated with **Circuit Breaker Protection** for market crash detection and automatic trading halt.

## What's New

### 🛡️ Circuit Breaker Protection
- **Automatic market crash detection** - Monitors BTC/ETH for >15% dumps
- **Instant trading halt** - All trading stops when crash detected
- **Background monitoring** - Runs 24/7 in separate thread
- **Telegram alerts** - Real-time notifications of circuit breaker triggers

### 🤖 5 AI Agents Working Together
1. **Market Guardian** (Highest Priority) - Circuit breaker monitoring
2. **Market Scanner** - Spike detection on your trading pairs
3. **Context Analyzer** - Cross-asset correlation analysis
4. **Risk Assessment** - Pre-trade validation
5. **Strategy Executor** - Trade execution coordination

### 📊 Enhanced Features
- **Spike Detection** - Automatically detects and capitalizes on price spikes
- **AI-Enhanced Signals** - Your existing signals enhanced with AI context
- **Multi-Layer Risk Management** - RL + AI agents + Circuit breaker
- **Complete Audit Trail** - All agent decisions logged to database

## Files Created

### Core Integration
- `crewai_integration.py` - Main integration layer
- `rl_bot_with_crewai.py` - Enhanced bot with CrewAI
- `circuit_breaker.py` - Circuit breaker state manager
- `crewai_agents.py` - All 5 AI agents
- `spike_agent_tools.py` - 13 custom tools for agents

### Configuration
- `config/crewai_spike_agent.yaml` - Complete system configuration

### Database
- `migrate_spike_schema.py` - Database migration (already run)
- New tables: `spike_detections`, `spike_trades`, `agent_decisions`

### Startup Scripts
- `scripts/start_crewai_bot.sh` - Start bot with CrewAI
- `scripts/stop_crewai_bot.sh` - Stop bot gracefully
- `scripts/status_crewai_bot.sh` - Check bot status

## Quick Start

### 1. Start the CrewAI-Enhanced Bot

```bash
cd /root/7monthIndicator
./scripts/start_crewai_bot.sh
```

This will start your bot with:
- ✅ RL enhancements (from existing bot)
- ✅ Circuit breaker protection (NEW)
- ✅ Market spike detection (NEW)
- ✅ AI agent analysis (NEW)

### 2. Check Status

```bash
./scripts/status_crewai_bot.sh
```

Shows:
- Bot running status
- Trading active/paused
- Circuit breaker state
- Recent log entries
- Configuration status

### 3. View Logs

```bash
tail -f logs/crewai_bot.log
```

### 4. Stop Bot

```bash
./scripts/stop_crewai_bot.sh
```

## How It Works

### Trading Flow with CrewAI

1. **Market Data Collection** (every 25 seconds)
   - Fetch klines from Binance
   - Calculate technical indicators

2. **Signal Generation** (Multi-layer)
   - Traditional technical analysis
   - RL enhancement (existing)
   - **NEW:** AI agent context analysis
   - **NEW:** Spike detection check

3. **Safety Validation** (Before any trade)
   - **NEW:** Circuit breaker check (market crash?)
   - **NEW:** AI agent validation
   - RL risk assessment
   - Position size calculation

4. **Trade Execution**
   - Only if all checks pass
   - Automatic TP/SL placement
   - Complete audit trail

5. **Background Monitoring** (Continuous)
   - Market Guardian checks for crashes every 60 seconds
   - Instant trading halt if crash detected
   - Automatic resume when market stabilizes

### Circuit Breaker Triggers

Trading automatically halts when:

**BTC Conditions:**
- 1-hour drop > 15%
- 4-hour drop > 20%

**ETH Conditions:**
- 1-hour drop > 15%
- 4-hour drop > 20%

**Actions Taken:**
1. Cancel all open orders
2. Pause all strategies
3. Send Telegram/Email alerts
4. Log event to database

**Resume:**
- Automatic when conditions improve
- Manual reset available (use with caution)

## Configuration

Edit `config/crewai_spike_agent.yaml` to customize:

### Circuit Breaker Settings

```yaml
circuit_breaker:
  enabled: true
  thresholds:
    btc:
      dump_1h_percent: 15.0  # Adjust threshold
      dump_4h_percent: 20.0
    eth:
      dump_1h_percent: 15.0
      dump_4h_percent: 20.0
```

### Spike Detection Settings

```yaml
spike_detection:
  enabled: true
  thresholds:
    price_spike_percent_5m: 3.0    # 3% spike in 5 min
    price_spike_percent_15m: 5.0   # 5% spike in 15 min
    volume_spike_multiplier: 3.0   # 3x volume
```

### Risk Management

```yaml
risk_management:
  max_position_size_percent: 2.0  # 2% max
  max_open_positions: 3
  require_agent_approval: true    # AI validation required
```

## Integration Modes

You have 3 ways to use the CrewAI system:

### Mode 1: Full Integration (Recommended)
Use `rl_bot_with_crewai.py` - All features enabled

```bash
./scripts/start_crewai_bot.sh
```

### Mode 2: Circuit Breaker Only
Add to your existing bot:

```python
from crewai_integration import is_trading_safe

def execute_trade(self, signal, price):
    # Add this check before trading
    if not is_trading_safe():
        logger.critical("🚨 Trade blocked - Circuit breaker!")
        return False

    # Your existing trade logic...
```

### Mode 3: Manual Integration
Use specific functions as needed:

```python
from crewai_integration import (
    validate_trade_before_execution,
    check_for_market_spikes,
    enhance_trading_signal
)

# Validate trade
allowed, reason = validate_trade_before_execution(
    'SUIUSDC', 'BUY', 100, 3.45
)

# Check for spikes
spike = check_for_market_spikes('SUIUSDC', 3.45)

# Enhance signal
enhanced = enhance_trading_signal(signal_data, market_data)
```

## Monitoring & Management

### Pause/Resume Trading

**Pause (generates signals but no trades):**
```bash
touch bot_pause.flag
```

**Resume:**
```bash
rm bot_pause.flag
```

### Manual Circuit Breaker Reset

```python
from crewai_integration import get_crewai_integration

integration = get_crewai_integration()
integration.manual_reset_circuit_breaker("Market stabilized")
```

⚠️ **Use with extreme caution!** Only reset when market is truly stable.

### View Statistics

```python
from crewai_integration import get_crewai_integration

integration = get_crewai_integration()
stats = integration.get_statistics()

print(f"Trades blocked: {stats['trades_blocked_by_circuit_breaker']}")
print(f"Spikes detected: {stats['spikes_detected']}")
print(f"Agent decisions: {stats['agent_decisions_made']}")
print(f"Circuit breaker triggers: {stats['circuit_breaker_triggers']}")
```

### Query Database

**Spike Detections:**
```sql
SELECT * FROM spike_detections
WHERE timestamp > datetime('now', '-24 hours')
ORDER BY timestamp DESC;
```

**Agent Decisions:**
```sql
SELECT * FROM agent_decisions
WHERE timestamp > datetime('now', '-24 hours')
ORDER BY timestamp DESC;
```

**Spike Trades:**
```sql
SELECT * FROM spike_trades
WHERE status = 'OPEN'
ORDER BY entry_timestamp DESC;
```

## Telegram Notifications

You'll receive alerts for:

### Circuit Breaker Triggers
```
🚨 CIRCUIT BREAKER TRIGGERED

⛔ ALL TRADING HALTED

Reason: BTC dropped 16.2% in 1 hour
State: TRIGGERED

Market Conditions:
• BTC 1h: -16.2%
• BTC 4h: -18.5%
• ETH 1h: -14.3%

🛡️ Bot will not execute any trades until market stabilizes.
```

### Trade Blocks
```
🚨 TRADE BLOCKED

⛔ Circuit breaker active

Signal: BUY SUIUSDC
Price: $3.4520

🛡️ Trading suspended for safety
```

### Spike Detections
```
📈 SPIKE DETECTED

Symbol: SUIUSDC
Price: $3.5200 (+5.2%)
Volume: 3.5x normal

🤖 AI agents analyzing opportunity...
```

## Cost Optimization

The system uses **GPT-4o-mini** for cost efficiency:

**Estimated Costs:**
- Circuit breaker checks: ~$0.10/day (1440 checks)
- Spike detection: ~$0.20/day (288 checks)
- Trade validation: ~$0.05/trade
- Context analysis: ~$0.10/day

**Total: ~$0.45-$2.00/day** depending on trading frequency

### To Reduce Costs Further

Edit `config/crewai_spike_agent.yaml`:

```yaml
agents:
  market_guardian:
    check_interval_seconds: 120  # Check every 2 min (from 60)

  market_scanner:
    check_interval_seconds: 600  # Check every 10 min (from 300)
```

## Troubleshooting

### Bot Won't Start

**Check OpenAI API Key:**
```bash
grep OPENAI_API_KEY .env
```

Must be present for CrewAI to work.

**Check Dependencies:**
```bash
pip install -r requirements.txt
```

**View Errors:**
```bash
tail -50 logs/crewai_bot.log
```

### Circuit Breaker Stuck

**Check State:**
```python
from circuit_breaker import get_circuit_breaker

cb = get_circuit_breaker()
status = cb.get_status()
print(status)
```

**Manual Reset (if needed):**
```python
cb.reset("Manual override - market stable")
```

### AI Agents Not Working

**Check OpenAI API Key:**
```bash
echo $OPENAI_API_KEY
```

**Test Agents:**
```bash
python test_crewai_system.py
```

**Check Logs:**
```bash
grep "CrewAI" logs/crewai_bot.log
```

### High API Costs

**Reduce check frequency** in config file
**Monitor usage:**
```python
from crewai_integration import get_crewai_integration

stats = get_crewai_integration().get_statistics()
print(f"Agent decisions: {stats['agent_decisions_made']}")
```

Each decision ≈ 1 API call ≈ $0.0001-0.001

## Testing

### Test Circuit Breaker

```bash
python test_crewai_system.py
```

Simulates market crash and verifies circuit breaker triggers.

### Test Integration

```bash
python crewai_integration.py
```

Tests initialization and basic functionality.

### Test Full System

1. Start bot in test mode (small positions)
2. Monitor logs for 1 hour
3. Verify circuit breaker checks every 60s
4. Check spike detection logs
5. Validate trade execution with AI

## Performance

**Expected Behavior:**
- Circuit breaker check: <2 seconds
- Spike detection: <3 seconds
- Trade validation: <4 seconds
- No impact on normal trading loop

**Resource Usage:**
- CPU: +5-10% (background monitoring)
- Memory: +100-200MB (AI agents)
- Network: +5-10 requests/minute (market data)

## Safety Features

### Multi-Layer Protection

1. **Circuit Breaker** - Market crash → Instant halt
2. **AI Agent Validation** - Bad trade → Block
3. **RL Risk Management** - High risk → Reduce size
4. **Position Limits** - Max 2% per trade
5. **Stop Loss** - Max 5% loss per trade

### What Gets Protected

✅ **Protected:**
- All trades executed by this bot
- Positions opened by this bot
- Stop loss and take profit orders

❌ **Not Protected:**
- Manual trades
- Trades from other bots
- Existing positions (before bot start)

## Comparison: Before vs After

### Before (RL-only)
- RL-enhanced signals
- 2% position size
- 15% TP, 5% SL
- Manual market crash handling

### After (RL + CrewAI)
- RL-enhanced signals ✅
- **+ AI agent context** 🆕
- **+ Circuit breaker protection** 🆕
- **+ Spike detection** 🆕
- 2% position size ✅
- **+ AI-adjusted sizing** 🆕
- 15% TP, 5% SL ✅
- **+ Automatic crash protection** 🆕

## Next Steps

### Recommended Actions

1. **Start with monitoring mode**
   ```bash
   touch bot_pause.flag  # Pause trading
   ./scripts/start_crewai_bot.sh
   ```

2. **Monitor for 24 hours**
   - Check circuit breaker is working
   - Verify spike detection
   - Review AI agent decisions

3. **Resume trading when confident**
   ```bash
   rm bot_pause.flag
   ```

4. **Fine-tune configuration**
   - Adjust circuit breaker thresholds
   - Customize spike detection
   - Optimize check intervals

5. **Monitor costs**
   - Track OpenAI API usage
   - Adjust check frequency if needed

## Support & Documentation

**Full Documentation:**
- `CREWAI_SPIKE_AGENT_README.md` - Complete technical docs
- `APPLICATION_LOGIC.md` - Bot architecture
- `TESTING_GUIDE.md` - Testing procedures

**Get Status:**
```bash
./scripts/status_crewai_bot.sh
```

**View Logs:**
```bash
tail -f logs/crewai_bot.log
```

**Get Help:**
Check logs first, then review configuration files.

---

## Summary

You now have a **production-ready, multi-agent AI trading system** with:

✅ **5 AI agents** working together
✅ **Circuit breaker** for crash protection
✅ **Spike detection** for opportunities
✅ **Complete audit trail** in database
✅ **Telegram notifications** for all events
✅ **Easy management scripts**
✅ **Cost-optimized** ($0.50-$2/day)

**To start trading:**
```bash
cd /root/7monthIndicator
./scripts/start_crewai_bot.sh
```

**Your bot is now significantly safer and smarter! 🚀**
