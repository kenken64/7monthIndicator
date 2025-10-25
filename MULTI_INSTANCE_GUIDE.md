# Multi-Instance Trading Bot Setup Guide

## Overview

This guide explains how to run **multiple instances** of your trading bot simultaneously on different ports. This is useful for:

- Running different trading strategies in parallel
- Testing configurations side-by-side
- Trading multiple symbols simultaneously
- Separating production and testing environments

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Your Server                             │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Instance 1 (Port 5000)      Instance 2 (Port 5001) │
│  ├── RL Bot                  ├── RL Bot             │
│  ├── Chart Bot               ├── Chart Bot          │
│  ├── CrewAI Bot              ├── CrewAI Bot         │
│  └── Dashboard               └── Dashboard          │
│                                                      │
│  Separate:                   Separate:              │
│  - Databases                 - Databases            │
│  - Log files                 - Log files            │
│  - Data directories          - Data directories     │
│  - Shared folders            - Shared folders       │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Check Current Instance

First, check if you have an instance running on port 5000:

```bash
./docker-multi-instance.sh status
```

### 2. Start Both Instances

```bash
# Start both instance 1 (port 5000) and instance 2 (port 5001)
./docker-multi-instance.sh start
```

### 3. Access Dashboards

- **Instance 1**: http://localhost:5000
- **Instance 2**: http://localhost:5001

## Management Commands

### Starting Instances

```bash
# Start all instances (both 5000 and 5001)
./docker-multi-instance.sh start

# Start instance 1 only (port 5000)
./docker-multi-instance.sh start-1

# Start instance 2 only (port 5001)
./docker-multi-instance.sh start-2
```

### Stopping Instances

```bash
# Stop all instances
./docker-multi-instance.sh stop

# Stop instance 1 only
./docker-multi-instance.sh stop-1

# Stop instance 2 only
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

## File Structure

Each instance has its own isolated data:

```
7monthIndicator-deepseek/
├── docker-compose.yml                    # Instance 1 configuration
├── docker-compose.multi-instance.yml     # Instance 2 configuration
├── docker-multi-instance.sh              # Management script
│
├── Instance 1 Files (Port 5000):
│   ├── data/                            # Instance 1 data
│   ├── shared/                          # Instance 1 shared files
│   ├── trading_bot.db                   # Instance 1 database
│   ├── trading_data.db                  # Instance 1 trading data
│   ├── rl_trading_model.pkl             # Instance 1 RL model
│   ├── trading_bot.log                  # Instance 1 bot log
│   ├── chart_analysis.log               # Instance 1 chart log
│   └── news_sentiment.json              # Instance 1 news data
│
└── Instance 2 Files (Port 5001):
    ├── data2/                           # Instance 2 data
    ├── shared2/                         # Instance 2 shared files
    ├── trading_bot_2.db                 # Instance 2 database
    ├── trading_data_2.db                # Instance 2 trading data
    ├── rl_trading_model_2.pkl           # Instance 2 RL model
    ├── trading_bot_2.log                # Instance 2 bot log
    ├── chart_analysis_2.log             # Instance 2 chart log
    └── news_sentiment_2.json            # Instance 2 news data
```

## Configuration

### Shared Configuration

Both instances use the **same** `.env` file and share:
- API keys (Binance, DeepSeek/OpenAI, Telegram)
- Bot control PIN
- LLM provider settings

### Instance-Specific Settings

Each instance can have different:
- Trading symbols (configure in code/database)
- Trading strategies
- Risk parameters
- RL models

### Environment Variables

Instances automatically receive:

**Instance 1:**
```bash
FLASK_PORT=5000
INSTANCE_ID=1
```

**Instance 2:**
```bash
FLASK_PORT=5001
INSTANCE_ID=2
```

## Use Cases

### 1. Different Trading Symbols

**Instance 1:** Trade SUIUSDC
**Instance 2:** Trade BTCUSDC

Modify the symbol configuration for each instance's database or config files.

### 2. Different Strategies

**Instance 1:** Conservative (low leverage, tight stops)
**Instance 2:** Aggressive (higher leverage, wider stops)

### 3. Testing vs Production

**Instance 1:** Production trading (real money)
**Instance 2:** Paper trading (testing)

Set `PAPER_TRADING=true` for instance 2.

### 4. Different AI Providers

**Instance 1:** Uses OpenAI (for vision features)
**Instance 2:** Uses DeepSeek (cost savings)

Currently both use the same `.env`, but you can modify docker-compose files to use different env files.

## Advanced Configuration

### Using Different Environment Files

If you want completely different configurations:

1. Create `.env.instance2`:
```bash
cp .env .env.instance2
# Edit .env.instance2 with different settings
```

2. Modify `docker-compose.multi-instance.yml`:
```yaml
env_file:
  - .env.instance2  # Instead of .env
```

### Custom Ports

Edit `docker-compose.multi-instance.yml` to use different ports:

```yaml
ports:
  - "5002:5002"  # Change from 5001
environment:
  - FLASK_PORT=5002
```

### More Instances

To add instance 3, 4, etc.:

1. Copy `docker-compose.multi-instance.yml` to `docker-compose.instance3.yml`
2. Change all `-2` suffixes to `-3`
3. Change port from 5001 to 5002
4. Update container names to avoid conflicts
5. Create separate data directories: `data3/`, `shared3/`, etc.

## Docker Commands Reference

### Direct Docker Compose Commands

```bash
# Instance 1 (default docker-compose.yml)
docker compose ps                    # List services
docker compose logs -f rl-bot        # Follow bot logs
docker compose up -d                 # Start in background
docker compose down                  # Stop all services

# Instance 2 (multi-instance)
docker compose -f docker-compose.multi-instance.yml ps
docker compose -f docker-compose.multi-instance.yml logs -f rl-bot-2
docker compose -f docker-compose.multi-instance.yml up -d
docker compose -f docker-compose.multi-instance.yml down
```

### Container Management

```bash
# List all containers
docker ps

# View specific container logs
docker logs -f rl-trading-bot
docker logs -f rl-trading-bot-2

# Execute commands in container
docker exec -it rl-trading-bot bash
docker exec -it web-dashboard-2 bash

# Restart specific container
docker restart rl-trading-bot
docker restart web-dashboard-2
```

## Monitoring

### Resource Usage

```bash
# Monitor CPU, memory usage
docker stats

# Monitor specific instances
docker stats rl-trading-bot rl-trading-bot-2 web-dashboard web-dashboard-2
```

### Health Checks

```bash
# Check instance 1 dashboard health
curl http://localhost:5000/health

# Check instance 2 dashboard health
curl http://localhost:5001/health
```

### Logs

```bash
# Watch both instances (in separate terminals)
Terminal 1: docker compose logs -f
Terminal 2: docker compose -f docker-compose.multi-instance.yml logs -f

# Or use the management script
./docker-multi-instance.sh logs
```

## Networking

Each instance has its own isolated network:

- **Instance 1**: `trading-network`
- **Instance 2**: `trading-network-2`

Containers within the same instance can communicate with each other, but instances are isolated from each other.

## Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:5001 failed: port is already allocated`

**Solutions:**
1. Check what's using the port:
   ```bash
   lsof -i :5001
   ```

2. Stop the conflicting service, or

3. Change the port in `docker-compose.multi-instance.yml`

### Containers Won't Start

**Check logs:**
```bash
./docker-multi-instance.sh status
docker compose logs rl-bot-2
```

**Common issues:**
- Missing directories: Run `mkdir -p data2 shared2`
- Database conflicts: Check file permissions
- Resource limits: Ensure enough RAM/CPU

### Database Conflicts

**Issue:** Both instances trying to use same database file

**Solution:** Verify separate database files in docker-compose files:
- Instance 1: `trading_bot.db`
- Instance 2: `trading_bot_2.db`

### API Rate Limits

**Issue:** Both instances hitting Binance/LLM API rate limits

**Solutions:**
1. Stagger instance start times
2. Reduce API call frequency in configuration
3. Use different API keys if available

## Performance Considerations

### Resource Requirements

Running 2 instances requires approximately:
- **RAM**: 4-8 GB total (2-4 GB per instance)
- **CPU**: 2-4 cores recommended
- **Disk**: 10-20 GB for databases and logs

### Optimization Tips

1. **Shared Volumes:** Logs directory is shared to save disk space
2. **Resource Limits:** Add limits in docker-compose:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 2G
   ```

3. **Log Rotation:** Configure log rotation to prevent disk fill

## Security

### Shared Secrets

Both instances share the same secrets from:
```
secrets/
├── binance_api_key
├── binance_secret_key
├── openai_api_key
├── telegram_bot_token
└── ...
```

Ensure proper file permissions:
```bash
chmod 600 secrets/*
```

### Network Isolation

Instances cannot communicate with each other by default. This provides:
- Security isolation
- Network traffic separation
- Independent failure modes

## Backup Strategy

### Backup Both Instances

```bash
#!/bin/bash
# backup-all-instances.sh

DATE=$(date +%Y%m%d_%H%M%S)

# Backup instance 1
tar -czf backup_instance1_$DATE.tar.gz \
    data/ \
    trading_bot.db \
    trading_data.db \
    rl_trading_model.pkl

# Backup instance 2
tar -czf backup_instance2_$DATE.tar.gz \
    data2/ \
    trading_bot_2.db \
    trading_data_2.db \
    rl_trading_model_2.pkl
```

## Migration Guide

### Migrate Existing Instance to Multi-Instance

If you already have a running instance on port 5000:

1. **Your existing setup becomes Instance 1** (no changes needed)

2. **Start Instance 2:**
   ```bash
   ./docker-multi-instance.sh start-2
   ```

3. **Both instances will now run** on ports 5000 and 5001

### Migrate from Multi-Instance Back to Single

```bash
# Stop instance 2
./docker-multi-instance.sh stop-2

# Keep instance 1 running (or restart it)
./docker-restart.sh
```

## FAQ

**Q: Can I run more than 2 instances?**
A: Yes! Copy the multi-instance compose file and modify ports/names.

**Q: Do instances share the same trading capital?**
A: No, each instance has its own database and trading state.

**Q: Can instances trade the same symbol?**
A: Yes, but they'll compete for fills. Not recommended.

**Q: How do I differentiate Telegram notifications?**
A: Instances share the same Telegram config. Consider using different bot tokens or adding instance ID to messages.

**Q: Does this work with the old docker-restart.sh?**
A: Yes! `docker-restart.sh` manages instance 1, and `docker-multi-instance.sh` manages both.

## Summary

You now have a complete multi-instance setup that allows you to:

✅ Run multiple trading bots simultaneously
✅ Isolated databases and configurations per instance
✅ Easy management via command-line script
✅ Independent monitoring and logging
✅ Flexible port configuration

**Start both instances:**
```bash
./docker-multi-instance.sh start
```

**Access dashboards:**
- http://localhost:5000 (Instance 1)
- http://localhost:5001 (Instance 2)

Happy trading! 🚀📈
