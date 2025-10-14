# Log Rotation for Trading Bot System

This system now includes comprehensive log rotation functionality to manage log file sizes and prevent disk space issues.

## Automatic Log Rotation

### During Service Restart
- **Integrated with restart_all.sh**: Log rotation happens automatically when you restart all services
- **Threshold**: Logs larger than 1MB are automatically rotated
- **Location**: Rotated logs are stored in `logs/rotated/` directory
- **Cleanup**: Old rotated logs older than 7 days are automatically cleaned up

### Manual Log Rotation

#### Standalone Script
Use the dedicated log rotation script for manual control:

```bash
# Basic rotation (rotate logs > 1MB, cleanup > 7 days)
./scripts/rotate_logs.sh

# Custom threshold and cleanup period
./scripts/rotate_logs.sh rotate 500K 3    # Rotate > 500KB, cleanup > 3 days

# Force rotate all logs regardless of size
./scripts/rotate_logs.sh force

# Only clean up old rotated logs
./scripts/rotate_logs.sh clean 14         # Clean logs older than 14 days

# Show help
./scripts/rotate_logs.sh help
```

#### System Integration with logrotate
For production environments, install the logrotate configuration:

```bash
# Install logrotate config (requires sudo)
sudo cp scripts/logrotate.conf /etc/logrotate.d/trading-bot

# Test the configuration
sudo logrotate -d /etc/logrotate.d/trading-bot

# Force manual run
sudo logrotate -f /etc/logrotate.d/trading-bot
```

## Log File Coverage

The rotation system monitors these locations:
- `/root/7monthIndicator/*.log` - Main application logs
- `/root/7monthIndicator/logs/*.log` - Service logs
- `/root/7monthIndicator/services/*/**.log` - Service-specific logs

## Rotation Features

### Automatic Features
- ✅ **Size-based rotation**: Files > 1MB (configurable)
- ✅ **Timestamped archives**: `filename_YYYYMMDD_HHMMSS.log` format
- ✅ **Automatic compression**: Compresses rotated logs to .tar.gz (86% space savings!)
- ✅ **Empty file recreation**: New empty log files with proper permissions
- ✅ **Automatic cleanup**: Removes old compressed archives older than specified days
- ✅ **Summary reporting**: Shows rotation statistics and compression savings
- ✅ **Safe operation**: Only rotates actual log files, preserves permissions

### Manual Control Options
- 🔧 **Custom thresholds**: Specify minimum size for rotation
- 🔧 **Flexible cleanup**: Configure retention period for rotated logs
- 🔧 **Force rotation**: Rotate all logs regardless of size
- 🔧 **Compression control**: Enable/disable compression per operation
- 🔧 **Selective cleanup**: Clean only old archives without new rotation
- 🔧 **Compress-only mode**: Compress existing rotated logs without rotation

## Usage Examples

### Regular Maintenance
```bash
# Weekly maintenance (run via cron)
0 2 * * 0 /root/7monthIndicator/scripts/rotate_logs.sh rotate 1M 7

# Daily cleanup of very old logs
0 3 * * * /root/7monthIndicator/scripts/rotate_logs.sh clean 30
```

### Disk Space Management
```bash
# Emergency rotation for all logs with compression
./scripts/rotate_logs.sh force

# Compress existing rotated logs without new rotation
./scripts/rotate_logs.sh compress

# Aggressive cleanup (smaller threshold, no compression)
./scripts/rotate_logs.sh rotate 100K 1 false

# Aggressive cleanup with compression
./scripts/rotate_logs.sh rotate 100K 1 true
```

### Service Restart with Rotation
```bash
# Standard restart (includes automatic log rotation)
./scripts/restart_all.sh
```

## Monitoring

### Check Current Log Sizes
```bash
# Show largest log files
find /root/7monthIndicator -name "*.log" -type f -exec ls -lah {} \; | sort -k5 -hr | head -10

# Show rotated logs
ls -lah /root/7monthIndicator/logs/rotated/
```

### Disk Usage
```bash
# Total log space used
du -sh /root/7monthIndicator/logs/ /root/7monthIndicator/*.log

# Rotated logs space
du -sh /root/7monthIndicator/logs/rotated/
```

## Configuration

### Adjust Rotation Thresholds
Edit the rotation parameters in `scripts/restart_all.sh`:
```bash
# Change the default threshold from 1M to 500K
rotate_logs "500K" "7"
```

### Logrotate Configuration
Modify `scripts/logrotate.conf` for system-level integration:
- `size`: Minimum file size for rotation
- `rotate`: Number of rotated files to keep
- `daily/weekly/monthly`: Rotation frequency
- `compress`: Enable compression of rotated logs

## Benefits

1. **Prevents disk space issues**: Automatically manages growing log files
2. **Maintains performance**: Smaller active log files improve I/O performance
3. **Preserves history**: Rotated logs are kept for troubleshooting
4. **Zero downtime**: Log rotation doesn't interrupt running services
5. **Automated maintenance**: Integrated with service restart process
6. **Flexible control**: Manual override options for special situations

The log rotation system ensures your trading bot system remains stable and maintainable with minimal manual intervention.