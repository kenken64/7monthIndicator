# Docker Quick Reference Card

## Essential Commands

### Setup & Start
```bash
# Check prerequisites
./check-docker-prereqs.sh

# Start all services (recommended)
./docker-restart.sh

# Manual start
docker-compose up -d --build
```

### Stop & Restart
```bash
# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart rl-bot
docker-compose restart chart-bot
docker-compose restart web-dashboard
```

### Monitoring
```bash
# View all logs (live)
docker-compose logs -f

# View specific service logs
docker-compose logs -f rl-bot
docker-compose logs -f chart-bot
docker-compose logs -f web-dashboard

# View last 100 lines
docker-compose logs --tail=100 rl-bot

# Check service status
docker-compose ps

# Resource usage
docker stats
```

### Debugging
```bash
# Enter container shell
docker exec -it rl-trading-bot bash
docker exec -it chart-analysis-bot bash
docker exec -it web-dashboard bash

# View container details
docker inspect rl-trading-bot

# Check health status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Maintenance
```bash
# Rebuild specific service
docker-compose up -d --build rl-bot

# Force recreate containers
docker-compose up -d --force-recreate

# Pull latest images
docker-compose pull

# Remove all containers and volumes
docker-compose down -v
```

### Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove all unused resources
docker system prune -a --volumes

# Free up space (aggressive)
docker system prune -a --volumes --force
```

### Backup & Restore
```bash
# Backup databases
docker cp rl-trading-bot:/app/trading_bot.db ./backup/
docker cp rl-trading-bot:/app/rl_trading_model.pkl ./backup/

# Restore databases
docker cp ./backup/trading_bot.db rl-trading-bot:/app/
docker-compose restart rl-bot
```

## Service URLs

- **Web Dashboard**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

## File Structure

```
7monthIndicator/
├── Dockerfile                    # Container build instructions
├── docker-compose.yml            # Service orchestration
├── .dockerignore                 # Files to exclude from image
├── docker-restart.sh             # Easy restart script
├── check-docker-prereqs.sh       # Prerequisites checker
├── .env                          # Environment variables (DO NOT COMMIT)
├── logs/                         # Application logs (mounted volume)
├── data/                         # Trading data (mounted volume)
├── shared/                       # Shared resources (mounted volume)
├── *.db                          # Database files (mounted)
└── *.pkl                         # ML models (mounted)
```

## Troubleshooting Quick Fixes

### Service won't start
```bash
docker-compose logs <service-name>
docker-compose up -d --build --force-recreate
```

### Port already in use
```bash
lsof -ti:5000 | xargs kill -9
```

### Database locked
```bash
docker-compose down
rm -f *.db-shm *.db-wal
docker-compose up -d
```

### Out of disk space
```bash
docker system prune -a --volumes
```

### Permission errors
```bash
sudo chown -R $USER:$USER logs/ data/ shared/
```

### Container keeps restarting
```bash
docker logs rl-trading-bot --tail=50
docker inspect rl-trading-bot | grep -A 20 Health
```

## Environment Variables

Required in `.env` file:
```env
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
OPENAI_API_KEY=your_openai_key
BOT_CONTROL_PIN=123456
NEWS_API_KEY=your_newsapi_key    # Optional
USE_LOCAL_SENTIMENT=true          # Optional (cost-saving)
```

## Health Checks

Services are monitored every 30 seconds:
- **RL Bot**: Process check
- **Chart Bot**: Process check
- **Web Dashboard**: HTTP check on port 5000

View health status:
```bash
docker-compose ps
```

## Common Workflows

### Daily Startup
```bash
./docker-restart.sh
# Access: http://localhost:5000
```

### Check Performance
```bash
docker stats
docker-compose logs -f web-dashboard
```

### Update Code
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### Backup Before Changes
```bash
# Backup databases and models
cp *.db *.pkl ./backup/
cp -r shared/ ./backup/
```

### View Real-time Trading Activity
```bash
docker-compose logs -f rl-bot | grep -i "trade\|position\|order"
```

## Performance Optimization

### Limit Resources
Edit `docker-compose.yml`:
```yaml
services:
  rl-bot:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

### Optimize Logs
```bash
# Limit log size
docker-compose logs --tail=1000 > important_logs.txt
# Clear old logs
truncate -s 0 logs/*.log
```

## Production Checklist

- [ ] `.env` file configured with real API keys
- [ ] All required API keys obtained and tested
- [ ] Firewall rules configured (if exposing ports)
- [ ] Backup strategy in place
- [ ] Log rotation configured
- [ ] Resource limits set (if needed)
- [ ] Health monitoring setup
- [ ] Alert system configured

## Security Notes

1. **Never commit `.env`** - Contains sensitive keys
2. **Use strong BOT_CONTROL_PIN** - Protects bot controls
3. **Rotate API keys regularly** - Security best practice
4. **Limit network exposure** - Don't expose ports unnecessarily
5. **Monitor logs for anomalies** - Check for unauthorized access

## Need Help?

1. Check logs: `docker-compose logs -f`
2. Verify config: `docker-compose config`
3. Read [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
4. Review [README.md](README.md)
5. Check GitHub issues

---

**Access Dashboard**: http://localhost:5000
**Quick Start**: `./docker-restart.sh`
