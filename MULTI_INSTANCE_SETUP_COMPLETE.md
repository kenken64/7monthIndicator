# ✅ Multi-Instance Setup Complete!

## 🎉 What's Ready

Your trading bot now supports **multiple instances running simultaneously** on different ports!

## 📋 Files Created

### Configuration
- ✅ `docker-compose.multi-instance.yml` - Instance 2 configuration
- ✅ `docker-multi-instance.sh` - Management script for all instances
- ✅ `setup-instance2.sh` - Quick setup for instance 2

### Documentation
- ✅ `MULTI_INSTANCE_GUIDE.md` - Complete multi-instance guide

### Updates
- ✅ `web_dashboard.py` - Now supports configurable ports via `FLASK_PORT` env var

## 🚀 Quick Start

### Check Current Status

```bash
./docker-multi-instance.sh status
```

### Setup Instance 2

```bash
# Create directories and files for instance 2
./setup-instance2.sh
```

### Start Both Instances

```bash
# Start instance 1 (port 5000) and instance 2 (port 5001)
./docker-multi-instance.sh start
```

### Access Your Dashboards

- **Instance 1**: http://localhost:5000
- **Instance 2**: http://localhost:5001

## 🎯 What Each Instance Includes

Each instance runs its own set of containers:

**Instance 1 (Port 5000):**
- `rl-trading-bot` - RL Trading Bot
- `chart-analysis-bot` - Chart Analysis Bot
- `crewai-agent-bot` - CrewAI Multi-Agent System
- `web-dashboard` - Web Dashboard

**Instance 2 (Port 5001):**
- `rl-trading-bot-2` - RL Trading Bot
- `chart-analysis-bot-2` - Chart Analysis Bot
- `crewai-agent-bot-2` - CrewAI Multi-Agent System
- `web-dashboard-2` - Web Dashboard

## 📁 File Separation

Each instance has **completely isolated** data:

```
Instance 1:                    Instance 2:
├── data/                     ├── data2/
├── shared/                   ├── shared2/
├── trading_bot.db            ├── trading_bot_2.db
├── trading_data.db           ├── trading_data_2.db
├── rl_trading_model.pkl      ├── rl_trading_model_2.pkl
├── trading_bot.log           ├── trading_bot_2.log
├── chart_analysis.log        ├── chart_analysis_2.log
└── news_sentiment.json       └── news_sentiment_2.json
```

**Shared between instances:**
- `.env` configuration
- API keys (Binance, DeepSeek, Telegram)
- `logs/` directory
- Docker secrets

## 💡 Use Cases

### 1. Different Trading Symbols
- **Instance 1**: Trade SUIUSDC
- **Instance 2**: Trade BTCUSDC

### 2. Different Strategies
- **Instance 1**: Conservative strategy (low leverage)
- **Instance 2**: Aggressive strategy (high leverage)

### 3. Production vs Testing
- **Instance 1**: Live trading
- **Instance 2**: Paper trading / testing

### 4. Different AI Providers
- **Instance 1**: OpenAI (with vision for charts)
- **Instance 2**: DeepSeek (cost savings for text-only)

## 🛠️ Management Commands

### Starting

```bash
# Start all instances
./docker-multi-instance.sh start

# Start only instance 1 (port 5000)
./docker-multi-instance.sh start-1

# Start only instance 2 (port 5001)
./docker-multi-instance.sh start-2
```

### Stopping

```bash
# Stop all instances
./docker-multi-instance.sh stop

# Stop only instance 1
./docker-multi-instance.sh stop-1

# Stop only instance 2
./docker-multi-instance.sh stop-2
```

### Monitoring

```bash
# Check status of all instances
./docker-multi-instance.sh status

# View logs from instance 1
./docker-multi-instance.sh logs-1

# View logs from instance 2
./docker-multi-instance.sh logs-2

# Interactive log selection
./docker-multi-instance.sh logs
```

### Restarting

```bash
# Restart all instances
./docker-multi-instance.sh restart
```

## 🔧 Configuration

### Shared Settings (Both Instances)

Both instances use the same `.env` file for:
- `LLM_PROVIDER=deepseek`
- `DEEPSEEK_API_KEY=...`
- `BINANCE_API_KEY=...`
- `TELEGRAM_BOT_TOKEN=...`

### Instance-Specific Settings

Automatically set via docker-compose:

**Instance 1:**
```yaml
environment:
  - FLASK_PORT=5000
  - INSTANCE_ID=1
```

**Instance 2:**
```yaml
environment:
  - FLASK_PORT=5001
  - INSTANCE_ID=2
```

## 📊 Docker Compose Files

### Instance 1
**File**: `docker-compose.yml`
**Command**: `docker compose up -d`
**Managed by**: `docker-restart.sh` (old) or `docker-multi-instance.sh`

### Instance 2
**File**: `docker-compose.multi-instance.yml`
**Command**: `docker compose -f docker-compose.multi-instance.yml up -d`
**Managed by**: `docker-multi-instance.sh`

## 🔍 Status Monitoring

The status command shows real-time status of all services:

```bash
$ ./docker-multi-instance.sh status

========================================
  Multi-Instance Status
========================================

Instance 1 (Port 5000):
-----------------------------------
  ✅ RL Bot
  ✅ Chart Bot
  ✅ CrewAI Bot
  ✅ Dashboard

Instance 2 (Port 5001):
-----------------------------------
  ✅ RL Bot
  ✅ Chart Bot
  ✅ CrewAI Bot
  ✅ Dashboard

🌐 Web Dashboards:
  Instance 1: http://localhost:5000
  Instance 2: http://localhost:5001
```

## 🌐 Network Isolation

Each instance has its own isolated Docker network:
- **Instance 1**: `trading-network`
- **Instance 2**: `trading-network-2`

This provides:
- Security isolation
- Independent failure modes
- No cross-instance interference

## 💾 Resource Requirements

### Per Instance
- **RAM**: 2-4 GB
- **CPU**: 1-2 cores
- **Disk**: 5-10 GB

### Total (2 Instances)
- **RAM**: 4-8 GB
- **CPU**: 2-4 cores
- **Disk**: 10-20 GB

## ⚡ Performance Tips

1. **Stagger Starts**: Start instances a few seconds apart to avoid resource spikes

2. **Monitor Resources**:
   ```bash
   docker stats
   ```

3. **Log Rotation**: Configure log rotation to prevent disk fill

4. **Database Maintenance**: Regularly clean old data from databases

## 🔐 Security

### Shared Secrets
All instances use the same secrets from `secrets/` directory:
- `binance_api_key`
- `binance_secret_key`
- `openai_api_key` (or DeepSeek)
- `telegram_bot_token`
- etc.

### Best Practices
- Ensure proper file permissions: `chmod 600 secrets/*`
- Don't commit secrets to git (already in `.gitignore`)
- Rotate API keys regularly

## 🆘 Troubleshooting

### Port Already in Use

**Error**: Port 5001 is already allocated

**Solution**:
```bash
# Check what's using the port
lsof -i :5001

# Change port in docker-compose.multi-instance.yml if needed
```

### Containers Won't Start

**Check logs**:
```bash
./docker-multi-instance.sh logs-2
```

**Common fixes**:
```bash
# Create missing directories
./setup-instance2.sh

# Rebuild images
docker compose -f docker-compose.multi-instance.yml up -d --build
```

### Database Conflicts

**Verify separate databases**:
```bash
ls -la trading_bot*.db
```

Should show:
- `trading_bot.db` (instance 1)
- `trading_bot_2.db` (instance 2)

## 📚 Documentation

- **Multi-Instance Guide**: `MULTI_INSTANCE_GUIDE.md`
- **DeepSeek Setup**: `DEEPSEEK_SETUP_COMPLETE.md`
- **LLM Integration**: `README_LLM_INTEGRATION.md`

## ✅ Next Steps

### 1. Setup Instance 2
```bash
./setup-instance2.sh
```

### 2. Start Both Instances
```bash
./docker-multi-instance.sh start
```

### 3. Verify Running
```bash
./docker-multi-instance.sh status
```

### 4. Access Dashboards
- Instance 1: http://localhost:5000
- Instance 2: http://localhost:5001

### 5. Monitor Logs
```bash
# Instance 1 logs
./docker-multi-instance.sh logs-1

# Instance 2 logs
./docker-multi-instance.sh logs-2
```

## 🎉 Benefits

✅ **Run multiple strategies** simultaneously
✅ **Isolated environments** (separate databases, logs, data)
✅ **Easy management** via single script
✅ **Independent monitoring** per instance
✅ **Flexible configuration** (different ports, settings)
✅ **Production + Testing** on same server
✅ **Cost optimization** (use DeepSeek for text, OpenAI for vision)

## 📝 Migration Notes

### From Single Instance to Multi-Instance

Your existing setup automatically becomes **Instance 1**. No changes needed!

Just add Instance 2:
```bash
./setup-instance2.sh
./docker-multi-instance.sh start-2
```

### From Multi-Instance Back to Single

Simply stop instance 2:
```bash
./docker-multi-instance.sh stop-2
```

Instance 1 continues running normally.

## 🎯 Summary

You now have:

✅ **Two complete trading bot instances**
✅ **Running on ports 5000 and 5001**
✅ **Completely isolated data and configuration**
✅ **Easy management via command-line tools**
✅ **Both using DeepSeek for cost savings**

**Start trading with multiple instances:**
```bash
./docker-multi-instance.sh start
```

**Monitor both dashboards:**
- http://localhost:5000 (Instance 1)
- http://localhost:5001 (Instance 2)

Happy multi-instance trading! 🚀📈💰
