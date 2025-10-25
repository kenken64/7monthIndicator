# ✅ Dual Provider Multi-Instance Setup Complete!

## 🎉 What's Ready

Your trading bot is now configured with **TWO independent instances** running different AI providers with **individual service control**!

## 📋 Summary

### Instance 1 - OpenAI (Port 5000)
- **Provider**: OpenAI
- **Config**: `.env.instance1`
- **Services**:
  - ✅ RL Bot
  - ✅ Chart Bot (with vision)
  - ✅ CrewAI Bot (all 5 agents)
  - ✅ Dashboard
- **Best for**: Full AI features, chart pattern recognition

### Instance 2 - DeepSeek (Port 5001)
- **Provider**: DeepSeek (85-95% cheaper!)
- **Config**: `.env.instance2`
- **Services**:
  - ✅ RL Bot
  - ✅ Chart Bot (text-only)
  - ✅ Dashboard
- **Best for**: Cost optimization, high-volume operations

## 🚀 Quick Start

### Step 1: Setup Instance 2

```bash
./setup-instance2.sh
```

### Step 2: Start Instance 2 Services

**Option A - Start all services:**
```bash
./docker-manage.sh start-2
```

**Option B - Start individual services:**
```bash
# Start RL Bot only
./docker-manage.sh start-2-rl

# Start Chart Bot only
./docker-manage.sh start-2-chart

# Start Dashboard only
./docker-manage.sh start-2-dash
```

### Step 3: Check Status

```bash
./docker-manage.sh status
```

### Step 4: Access Dashboards

- **Instance 1 (OpenAI)**: http://localhost:5000
- **Instance 2 (DeepSeek)**: http://localhost:5001

## 📁 Files Created

### Configuration Files
- ✅ `.env.instance1` - OpenAI configuration
- ✅ `.env.instance2` - DeepSeek configuration
- ✅ `docker-compose.instance2.yml` - Instance 2 services
- ✅ `secrets/deepseek_api_key` - DeepSeek API key

### Management Scripts
- ✅ `docker-manage.sh` - Advanced multi-instance manager
- ✅ `setup-instance2.sh` - Quick setup script

### Documentation
- ✅ `DUAL_PROVIDER_SETUP.md` - Complete guide
- ✅ `DEEPSEEK_SETUP_COMPLETE.md` - DeepSeek integration
- ✅ `MULTI_INSTANCE_GUIDE.md` - Multi-instance documentation
- ✅ `README_LLM_INTEGRATION.md` - LLM provider docs

### Updated Files
- ✅ `docker-compose.yml` - Uses `.env.instance1`
- ✅ `web_dashboard.py` - Configurable port support

## 🛠️ Management Commands Reference

### Full Instance Control

```bash
# Start/stop entire instances
./docker-manage.sh start-1          # Start Instance 1 (OpenAI)
./docker-manage.sh start-2          # Start Instance 2 (DeepSeek)
./docker-manage.sh stop-1           # Stop Instance 1
./docker-manage.sh stop-2           # Stop Instance 2
./docker-manage.sh restart-1        # Restart Instance 1
./docker-manage.sh restart-2        # Restart Instance 2
```

### Individual Service Control - Instance 2

```bash
# Start services individually
./docker-manage.sh start-2-rl       # RL Bot
./docker-manage.sh start-2-chart    # Chart Bot
./docker-manage.sh start-2-dash     # Dashboard

# Stop services individually
./docker-manage.sh stop-2-rl        # RL Bot
./docker-manage.sh stop-2-chart     # Chart Bot
./docker-manage.sh stop-2-dash      # Dashboard
```

### Combined Control

```bash
./docker-manage.sh start-all        # Start both instances
./docker-manage.sh stop-all         # Stop both instances
./docker-manage.sh restart-all      # Restart both instances
./docker-manage.sh status           # Show status
```

### Logs

```bash
# Instance 2 logs
./docker-manage.sh logs-2           # All logs
./docker-manage.sh logs-2 rl        # RL Bot only
./docker-manage.sh logs-2 chart     # Chart Bot only
./docker-manage.sh logs-2 dash      # Dashboard only
```

## 💡 Common Use Cases

### Use Case 1: Start Only RL Bot and Dashboard on Instance 2

**Perfect for minimal resource usage:**

```bash
./docker-manage.sh start-2-rl       # Start RL Bot
./docker-manage.sh start-2-dash     # Start Dashboard
```

Access at: http://localhost:5001

### Use Case 2: Full Production Setup

**Run both instances with all services:**

```bash
# Instance 1 (OpenAI - full features)
./docker-manage.sh start-1

# Instance 2 (DeepSeek - cost savings)
./docker-manage.sh start-2
```

Access both dashboards:
- http://localhost:5000 (OpenAI)
- http://localhost:5001 (DeepSeek)

### Use Case 3: Testing DeepSeek

**Test before committing resources:**

```bash
# Start only dashboard to test configuration
./docker-manage.sh start-2-dash

# If working well, add RL Bot
./docker-manage.sh start-2-rl

# Finally add Chart Bot
./docker-manage.sh start-2-chart
```

## 💰 Cost Savings

| Feature | Instance 1 (OpenAI) | Instance 2 (DeepSeek) | Savings |
|---------|--------------------|-----------------------|---------|
| News Sentiment | $2.00/1M tokens | $0.27/1M tokens | **86%** |
| Chart Analysis | $5.00/1M tokens | $0.27/1M tokens | **95%** |
| CrewAI Agents | $2.00/1M tokens | $0.27/1M tokens | **86%** |

**Monthly estimate:**
- Instance 1 (OpenAI): $50-100
- Instance 2 (DeepSeek): $5-10
- **Total savings with Instance 2: $45-90/month**

## 🔍 Status Check

When you run `./docker-manage.sh status`, you'll see:

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

## ⚙️ Configuration Details

### Instance 1 (.env.instance1)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
INSTANCE_ID=1
FLASK_PORT=5000
```

### Instance 2 (.env.instance2)
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-ae71a640f1344a5e9f13b34d69090c0b
INSTANCE_ID=2
FLASK_PORT=5001
```

## 📊 Feature Comparison

| Feature | Instance 1 (OpenAI) | Instance 2 (DeepSeek) |
|---------|--------------------|-----------------------|
| RL Trading Bot | ✅ | ✅ |
| Chart Analysis | ✅ Vision Support | ✅ Text Only |
| CrewAI Agents | ✅ All 5 Agents | ❌ Not Included |
| Dashboard | ✅ | ✅ |
| News Sentiment | ✅ | ✅ |
| Cost per 1M tokens | $2-5 | $0.27 |

## 🆘 Troubleshooting

### Instance 2 Won't Start

**Check environment files exist:**
```bash
ls -la .env.instance*
```

**Verify DeepSeek API key:**
```bash
cat secrets/deepseek_api_key
```

**Check logs:**
```bash
./docker-manage.sh logs-2
```

### Port Conflicts

**Port 5001 already in use:**
```bash
# Check what's using the port
lsof -i :5001

# Kill the process or change port in docker-compose.instance2.yml
```

### Service Not Starting

**Check individual service logs:**
```bash
./docker-manage.sh logs-2 rl        # RL Bot logs
./docker-manage.sh logs-2 chart     # Chart Bot logs
./docker-manage.sh logs-2 dash      # Dashboard logs
```

**Rebuild containers:**
```bash
./docker-manage.sh stop-2
docker compose -f docker-compose.instance2.yml up -d --build
```

## 🎯 Next Steps

### Immediate Actions

1. **Setup Instance 2:**
   ```bash
   ./setup-instance2.sh
   ```

2. **Start your preferred services:**
   ```bash
   # Minimal setup (just RL bot and dashboard)
   ./docker-manage.sh start-2-rl
   ./docker-manage.sh start-2-dash

   # OR full setup (all instance 2 services)
   ./docker-manage.sh start-2
   ```

3. **Verify running:**
   ```bash
   ./docker-manage.sh status
   ```

4. **Access dashboard:**
   - Open http://localhost:5001

### Optional Actions

- **Start Instance 1** if you need OpenAI features:
  ```bash
  ./docker-manage.sh start-1
  ```

- **Monitor both instances:**
  ```bash
  watch ./docker-manage.sh status
  ```

## 📚 Documentation

Comprehensive guides available:

1. **DUAL_PROVIDER_SETUP.md** - This dual provider setup
2. **DEEPSEEK_SETUP_COMPLETE.md** - DeepSeek integration details
3. **MULTI_INSTANCE_GUIDE.md** - Multi-instance architecture
4. **README_LLM_INTEGRATION.md** - LLM provider documentation
5. **LLM_PROVIDER_GUIDE.md** - Technical implementation guide

## ✨ Key Features

✅ **Dual Provider Support**
- Instance 1: OpenAI (full features)
- Instance 2: DeepSeek (cost savings)

✅ **Individual Service Control**
- Start/stop services independently
- Granular resource management

✅ **Complete Isolation**
- Separate databases
- Separate data directories
- Independent configurations

✅ **Easy Management**
- Single script controls everything
- Clear status reporting
- Service-specific log viewing

✅ **Cost Optimization**
- Save 85-95% with DeepSeek
- Use OpenAI only when needed
- Flexible hybrid approach

## 🎊 Summary

You now have:

✅ **Instance 1 (OpenAI)** - Full AI features on port 5000
✅ **Instance 2 (DeepSeek)** - Cost-effective on port 5001
✅ **Individual service control** for both instances
✅ **Separate configurations** per provider
✅ **Complete management script** (`docker-manage.sh`)
✅ **Comprehensive documentation**

## 🚀 Ready to Go!

**Your setup is complete and ready to use!**

### Start Instance 2 Now:

```bash
# Quick start - all services
./docker-manage.sh start-2

# OR selective start
./docker-manage.sh start-2-rl      # RL Bot
./docker-manage.sh start-2-chart   # Chart Bot
./docker-manage.sh start-2-dash    # Dashboard

# Check status
./docker-manage.sh status

# Access dashboard
# http://localhost:5001
```

**Happy trading with dual providers!** 🚀📈💰

---

**Need help?** Check the documentation or run:
```bash
./docker-manage.sh help
```
