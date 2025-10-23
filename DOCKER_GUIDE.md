# Docker Deployment Guide

This guide provides comprehensive information about deploying and managing the Trading Bot system using Docker.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Service Management](#service-management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

The Docker deployment containerizes three main services:
1. **RL Trading Bot** - Reinforcement Learning-based trading engine
2. **Chart Analysis Bot** - AI-powered chart analysis service
3. **Web Dashboard** - Flask-based monitoring dashboard

All services run in isolated containers with shared volumes for data persistence.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Docker Network                      │
│  (trading-network)                              │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │   RL Bot     │  │  Chart Bot   │  │  Web   │ │
│  │              │  │              │  │  Dash  │ │
│  │ rl_bot_ready │  │ chart_analysis│ │  :5000 │ │
│  └──────┬───────┘  └──────┬───────┘  └───┬────┘ │
│         │                 │               │      │
│         └─────────┬───────┴───────────────┘      │
│                   │                              │
└───────────────────┼──────────────────────────────┘
                    │
         ┌──────────▼───────────┐
         │  Shared Volumes      │
         │  - logs/             │
         │  - data/             │
         │  - shared/           │
         │  - *.db (databases)  │
         │  - *.pkl (models)    │
         └──────────────────────┘
```

## Prerequisites

### System Requirements
- Docker version 20.10 or higher
- Docker Compose version 2.0 or higher
- At least 2GB RAM available
- 5GB free disk space

### Install Docker

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

**macOS:**
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Or use Homebrew
brew install --cask docker
```

**Windows:**
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

### Verify Installation
```bash
docker --version
docker compose version
```

## Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd 7monthIndicator
```

### 2. Configure Environment
```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Required environment variables:
```env
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here
BOT_CONTROL_PIN=your_6_digit_pin
NEWS_API_KEY=your_newsapi_key_here
```

### 3. Build and Start Services
```bash
# Using the helper script (recommended)
./docker-restart.sh

# Or manually
docker-compose up -d --build
```

## Configuration

### Environment Variables

All services share the same `.env` file. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Binance API key | Yes |
| `BINANCE_SECRET_KEY` | Binance secret key | Yes |
| `OPENAI_API_KEY` | OpenAI API key for chart analysis | Yes |
| `BOT_CONTROL_PIN` | 6-digit PIN for bot control | Yes |
| `NEWS_API_KEY` | NewsAPI key for sentiment | Optional |
| `USE_LOCAL_SENTIMENT` | Use free sentiment analysis | Optional |

### Volume Mounts

The following directories are mounted as volumes:

```yaml
volumes:
  - ./logs:/app/logs              # Application logs
  - ./data:/app/data              # Trading data
  - ./shared:/app/shared          # Shared resources
  - ./.env:/app/.env              # Environment config
  - ./trading_bot.db:/app/trading_bot.db
  - ./trading_data.db:/app/trading_data.db
  - ./rl_trading_model.pkl:/app/rl_trading_model.pkl
```

### Port Mappings

- **5000:5000** - Web Dashboard (HTTP)

Access the dashboard at: `http://localhost:5000`

## Service Management

### Start All Services
```bash
./docker-restart.sh
# or
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### Restart a Specific Service
```bash
docker-compose restart rl-bot
docker-compose restart chart-bot
docker-compose restart web-dashboard
```

### View Service Status
```bash
docker-compose ps
```

### Scale Services (if needed)
```bash
# Not recommended for this use case as services maintain state
docker-compose up -d --scale chart-bot=2
```

## Monitoring

### View Logs

**All services:**
```bash
docker-compose logs -f
```

**Specific service:**
```bash
docker-compose logs -f rl-bot
docker-compose logs -f chart-bot
docker-compose logs -f web-dashboard
```

**Last N lines:**
```bash
docker-compose logs --tail=100 rl-bot
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Specific container
docker stats rl-trading-bot
```

### Health Checks

Each service has built-in health checks:

```bash
# View health status
docker-compose ps

# Detailed health info
docker inspect rl-trading-bot | grep -A 10 Health
```

Health check intervals:
- Check every: 30 seconds
- Timeout: 10 seconds
- Retries: 3 before marking unhealthy

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker-compose logs <service-name>
```

**Rebuild from scratch:**
```bash
docker-compose down
docker-compose up -d --build --force-recreate
```

### Permission Errors

**Fix volume permissions:**
```bash
sudo chown -R $USER:$USER logs/ data/ shared/
chmod -R 755 logs/ data/ shared/
```

### Port Already in Use

**Find and kill process using port 5000:**
```bash
# Linux/macOS
lsof -ti:5000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Database Locked Errors

**Stop all services and restart:**
```bash
docker-compose down
rm -f *.db-shm *.db-wal  # Remove SQLite temp files
docker-compose up -d
```

### Out of Disk Space

**Clean up Docker resources:**
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove all unused resources
docker system prune -a --volumes
```

### Container Keeps Restarting

**Check health check status:**
```bash
docker inspect <container-name> | grep -A 20 Health
```

**Disable health checks temporarily:**
Edit `docker-compose.yml` and comment out health check sections.

## Advanced Topics

### Custom Network Configuration

```yaml
# docker-compose.yml
networks:
  trading-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Resource Limits

Add resource constraints to prevent services from consuming too much:

```yaml
services:
  rl-bot:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Automated Backups

**Backup script example:**
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR=./backups/$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp *.db *.pkl $BACKUP_DIR/
cp -r shared/ $BACKUP_DIR/
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

### Docker Compose Overrides

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  web-dashboard:
    ports:
      - "5001:5000"  # Custom port
    environment:
      - DEBUG=true   # Enable debug mode
```

### Production Deployment

**Using Docker Swarm:**
```bash
docker swarm init
docker stack deploy -c docker-compose.yml trading-stack
```

**Using Kubernetes:**
```bash
# Convert to Kubernetes manifests
kompose convert -f docker-compose.yml
kubectl apply -f .
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Database Maintenance

```bash
# Access database directly
docker exec -it rl-trading-bot sqlite3 /app/trading_bot.db

# Backup databases
docker cp rl-trading-bot:/app/trading_bot.db ./backup/
```

### Log Rotation

Logs are stored in `./logs/` directory. Consider implementing log rotation:

```bash
# Add to crontab
0 0 * * * find /path/to/7monthIndicator/logs -name "*.log" -mtime +7 -delete
```

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive API keys
2. **Use secrets management** - For production, use Docker secrets or environment variable injection
3. **Network isolation** - Consider using Docker's built-in network isolation
4. **Regular updates** - Keep Docker and base images updated
5. **API key rotation** - Regularly rotate API keys

## Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify environment: `docker-compose config`
3. Check GitHub issues: [Project Issues](your-repo-url/issues)
4. Review main README.md for general troubleshooting

## Comparison: Docker vs. Native

| Feature | Docker Deployment | Native Deployment |
|---------|-------------------|-------------------|
| Setup Complexity | Low (automated) | Medium (manual) |
| Isolation | High (containerized) | Low (shared system) |
| Resource Usage | Slightly higher | Lower |
| Portability | High (works anywhere) | OS-dependent |
| Updates | Easy (rebuild) | Manual |
| Debugging | Moderate | Easier (direct access) |

---

For more information, see the main [README.md](README.md) file.
