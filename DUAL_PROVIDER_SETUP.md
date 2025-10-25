# 🤖 Dual Provider Setup Guide - OpenAI + DeepSeek

## Overview

Your trading bot is now configured with **two independent instances**:

- **Instance 1 (Port 5000)**: Uses **OpenAI** - Full features including vision
- **Instance 2 (Port 5001)**: Uses **DeepSeek** - Cost-effective operations

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Your Trading System                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Instance 1 (OpenAI - Port 5000)                         │
│  ┌─────────────────────────────────────────────┐         │
│  │ Provider: OpenAI                            │         │
│  │ Services:                                   │         │
│  │   ✅ RL Bot                                 │         │
│  │   ✅ Chart Bot (with vision)               │         │
│  │   ✅ CrewAI Bot (all 5 agents)             │         │
│  │   ✅ Dashboard                              │         │
│  │                                             │         │
│  │ Config: .env.instance1                     │         │
│  │ Data: data/, trading_bot.db                │         │
│  └─────────────────────────────────────────────┘         │
│                                                           │
│  Instance 2 (DeepSeek - Port 5001)                       │
│  ┌─────────────────────────────────────────────┐         │
│  │ Provider: DeepSeek (85-95% cheaper!)       │         │
│  │ Services:                                   │         │
│  │   ✅ RL Bot                                 │         │
│  │   ✅ Chart Bot (text-only)                 │         │
│  │   ✅ Dashboard                              │         │
│  │                                             │         │
│  │ Config: .env.instance2                     │         │
│  │ Data: data2/, trading_bot_2.db             │         │
│  └─────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Instance 2 (DeepSeek)

```bash
./setup-instance2.sh
```

### 2. Start Individual Services

**Instance 2 - Start only RL Bot, Chart Bot, and Dashboard:**

```bash
# Start RL Bot (instance 2)
./docker-manage.sh start-2-rl

# Start Chart Bot (instance 2)
./docker-manage.sh start-2-chart

# Start Dashboard (instance 2)
./docker-manage.sh start-2-dash
```

**Or start all Instance 2 services at once:**

```bash
./docker-manage.sh start-2
```

### 3. Access Dashboards

- **Instance 1 (OpenAI)**: http://localhost:5000
- **Instance 2 (DeepSeek)**: http://localhost:5001

## Configuration Files

### Instance 1 Configuration (.env.instance1)

```bash
# Instance 1 - OpenAI Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
INSTANCE_ID=1
FLASK_PORT=5000
```

### Instance 2 Configuration (.env.instance2)

```bash
# Instance 2 - DeepSeek Provider
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-ae71a640f1344a5e9f13b34d69090c0b
INSTANCE_ID=2
FLASK_PORT=5001
```

## Management Commands

### Complete Instance Control

```bash
# Start/Stop entire instances
./docker-manage.sh start-1          # Start all Instance 1 services
./docker-manage.sh start-2          # Start all Instance 2 services
./docker-manage.sh stop-1           # Stop Instance 1
./docker-manage.sh stop-2           # Stop Instance 2
./docker-manage.sh restart-1        # Restart Instance 1
./docker-manage.sh restart-2        # Restart Instance 2
```

### Individual Service Control - Instance 1 (OpenAI)

```bash
# Start individual services
./docker-manage.sh start-1-rl       # Start RL Bot
./docker-manage.sh start-1-chart    # Start Chart Bot
./docker-manage.sh start-1-crewai   # Start CrewAI Bot
./docker-manage.sh start-1-dash     # Start Dashboard

# Stop individual services
./docker-manage.sh stop-1-rl        # Stop RL Bot
./docker-manage.sh stop-1-chart     # Stop Chart Bot
./docker-manage.sh stop-1-crewai    # Stop CrewAI Bot
./docker-manage.sh stop-1-dash      # Stop Dashboard
```

### Individual Service Control - Instance 2 (DeepSeek)

```bash
# Start individual services
./docker-manage.sh start-2-rl       # Start RL Bot
./docker-manage.sh start-2-chart    # Start Chart Bot
./docker-manage.sh start-2-dash     # Start Dashboard

# Stop individual services
./docker-manage.sh stop-2-rl        # Stop RL Bot
./docker-manage.sh stop-2-chart     # Stop Chart Bot
./docker-manage.sh stop-2-dash      # Stop Dashboard
```

### Combined Controls

```bash
# Start/stop both instances
./docker-manage.sh start-all        # Start both instances
./docker-manage.sh stop-all         # Stop both instances
./docker-manage.sh restart-all      # Restart both instances

# Status check
./docker-manage.sh status           # Show status of all services
```

### Logs

```bash
# Instance 1 logs
./docker-manage.sh logs-1           # All logs
./docker-manage.sh logs-1 rl        # RL Bot only
./docker-manage.sh logs-1 chart     # Chart Bot only
./docker-manage.sh logs-1 crewai    # CrewAI Bot only
./docker-manage.sh logs-1 dash      # Dashboard only

# Instance 2 logs
./docker-manage.sh logs-2           # All logs
./docker-manage.sh logs-2 rl        # RL Bot only
./docker-manage.sh logs-2 chart     # Chart Bot only
./docker-manage.sh logs-2 dash      # Dashboard only
```

## Service Comparison

### Instance 1 (OpenAI - Port 5000)

| Service | Status | Features |
|---------|--------|----------|
| RL Bot | ✅ | Full AI trading with OpenAI |
| Chart Bot | ✅ | **Vision analysis** of charts |
| CrewAI Bot | ✅ | All 5 AI agents |
| Dashboard | ✅ | Full monitoring |

**Best for:**
- Chart pattern recognition (vision)
- Complex multi-agent strategies
- Maximum AI capabilities

### Instance 2 (DeepSeek - Port 5001)

| Service | Status | Features |
|---------|--------|----------|
| RL Bot | ✅ | Full AI trading with DeepSeek |
| Chart Bot | ✅ | Text-based analysis |
| CrewAI Bot | ❌ | Not included |
| Dashboard | ✅ | Full monitoring |

**Best for:**
- Cost optimization (85-95% cheaper)
- Text-based market analysis
- High-volume operations
- Testing strategies

## Cost Comparison

### Instance 1 (OpenAI)

| Task | Model | Cost per 1M tokens |
|------|-------|-------------------|
| News Sentiment | gpt-5-nano | $2.00 input |
| Chart Analysis | gpt-4o | $5.00 input |
| CrewAI Agents | gpt-5-nano | $2.00 input |

**Monthly estimate**: $50-100 (moderate usage)

### Instance 2 (DeepSeek)

| Task | Model | Cost per 1M tokens |
|------|-------|-------------------|
| News Sentiment | deepseek-chat | $0.27 input |
| Chart Analysis | deepseek-chat | $0.27 input |

**Monthly estimate**: $5-10 (moderate usage)

**Savings**: ~85-95% compared to OpenAI!

## Use Case Examples

### Example 1: Start Instance 2 with Specific Services

**Goal**: Run only RL Bot and Dashboard on Instance 2 (DeepSeek)

```bash
# Start RL Bot
./docker-manage.sh start-2-rl

# Start Dashboard
./docker-manage.sh start-2-dash

# Check status
./docker-manage.sh status
```

### Example 2: Full Production Setup

**Goal**: Run both instances with all services

```bash
# Start Instance 1 (OpenAI - full features)
./docker-manage.sh start-1

# Start Instance 2 (DeepSeek - cost-effective)
./docker-manage.sh start-2

# Monitor status
./docker-manage.sh status
```

### Example 3: Testing Configuration

**Goal**: Test DeepSeek with minimal services

```bash
# Start only Dashboard on Instance 2
./docker-manage.sh start-2-dash

# Access dashboard
open http://localhost:5001

# If satisfied, add more services
./docker-manage.sh start-2-rl
./docker-manage.sh start-2-chart
```

## Status Monitoring

Run `./docker-manage.sh status` to see:

```
========================================
  Multi-Instance Status
========================================

Instance 1 - OpenAI (Port 5000):
-----------------------------------
  ✅ RL Bot
  ✅ Chart Bot
  ✅ CrewAI Bot
  ✅ Dashboard

Instance 2 - DeepSeek (Port 5001):
-----------------------------------
  ✅ RL Bot
  ✅ Chart Bot
  ✅ Dashboard

🌐 Web Dashboards:
  Instance 1 (OpenAI):  http://localhost:5000
  Instance 2 (DeepSeek): http://localhost:5001
```

## Docker Compose Files

### Instance 1
- **File**: `docker-compose.yml`
- **Env**: `.env.instance1`
- **Services**: rl-bot, chart-bot, crewai-bot, web-dashboard
- **Provider**: OpenAI

### Instance 2
- **File**: `docker-compose.instance2.yml`
- **Env**: `.env.instance2`
- **Services**: rl-bot-2, chart-bot-2, web-dashboard-2
- **Provider**: DeepSeek

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
./docker-manage.sh logs-2 rl
```

**Common issues:**
- Missing directories: Run `./setup-instance2.sh`
- Port conflict: Check `lsof -i :5001`
- Config error: Verify `.env.instance2`

### API Key Issues

**Instance 2 can't find DeepSeek key:**

1. Check secret file exists:
   ```bash
   cat secrets/deepseek_api_key
   ```

2. Verify permissions:
   ```bash
   chmod 600 secrets/deepseek_api_key
   ```

3. Check env file:
   ```bash
   grep DEEPSEEK_API_KEY .env.instance2
   ```

### Dashboard Not Accessible

**Port 5001 not responding:**

1. Check container status:
   ```bash
   docker ps | grep web-dashboard-2
   ```

2. Check container logs:
   ```bash
   ./docker-manage.sh logs-2 dash
   ```

3. Verify port mapping:
   ```bash
   docker compose -f docker-compose.instance2.yml ps
   ```

## Advanced Usage

### Different Trading Symbols per Instance

**Instance 1**: Trade SUIUSDC (OpenAI for chart patterns)
**Instance 2**: Trade BTCUSDC (DeepSeek for cost savings)

Modify the symbol in each instance's database or configuration.

### Paper Trading on Instance 2

Test strategies without risk on Instance 2:

1. Edit `.env.instance2`:
   ```bash
   PAPER_TRADING=true
   TEST_MODE=true
   ```

2. Restart Instance 2:
   ```bash
   ./docker-manage.sh restart-2
   ```

### Custom Service Combinations

**Scenario**: Only want RL Bot from Instance 2

```bash
# Stop all Instance 2 services
./docker-manage.sh stop-2

# Start only RL Bot
./docker-manage.sh start-2-rl
```

## Resource Requirements

### Instance 1 (All Services)
- RAM: 3-4 GB
- CPU: 2 cores
- Disk: 10 GB

### Instance 2 (3 Services)
- RAM: 2-3 GB
- CPU: 1-2 cores
- Disk: 5 GB

### Total (Both Instances)
- RAM: 5-7 GB
- CPU: 3-4 cores
- Disk: 15 GB

## Security

### API Keys

Both instances use Docker secrets:
- `secrets/binance_api_key`
- `secrets/openai_api_key`
- `secrets/deepseek_api_key`
- `secrets/telegram_bot_token`

Ensure proper permissions:
```bash
chmod 600 secrets/*
```

### Network Isolation

Each instance has its own network:
- Instance 1: `trading-network`
- Instance 2: `trading-network-2`

Services within different instances cannot communicate.

## Migration Path

### From Old Setup to Dual Provider

1. Your existing setup becomes Instance 1 (OpenAI)
2. Add Instance 2 (DeepSeek):
   ```bash
   ./setup-instance2.sh
   ./docker-manage.sh start-2
   ```

### From Dual Provider to Single Instance

Keep Instance 2, stop Instance 1:
```bash
./docker-manage.sh stop-1
# Only Instance 2 (DeepSeek) running
```

## Summary

You now have:

✅ **Instance 1**: OpenAI provider (full features)
✅ **Instance 2**: DeepSeek provider (cost-effective)
✅ **Individual service control** for each instance
✅ **Separate configurations** per instance
✅ **Complete isolation** between instances
✅ **Easy management** via `docker-manage.sh`

## Quick Reference

```bash
# Most common commands:

# Start Instance 2 (DeepSeek) services
./docker-manage.sh start-2-rl      # RL Bot
./docker-manage.sh start-2-chart   # Chart Bot
./docker-manage.sh start-2-dash    # Dashboard

# Or start all Instance 2 services
./docker-manage.sh start-2

# Check status
./docker-manage.sh status

# View logs
./docker-manage.sh logs-2

# Access dashboards
# Instance 1: http://localhost:5000
# Instance 2: http://localhost:5001
```

**Happy trading with dual providers!** 🚀📈💰
