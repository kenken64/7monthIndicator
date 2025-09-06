# Claude Code Rules for 7monthIndicator Trading Bot

## Project Overview
This is a Python-based cryptocurrency trading bot system that uses Binance Futures API, reinforcement learning, technical analysis, and web dashboard monitoring.

## Code Style & Conventions

### Python Style
- Follow PEP 8 standards for Python code formatting
- Use type hints for function parameters and return values
- Use docstrings for classes and functions (Google style)
- Import statements: standard library first, then third-party, then local imports
- Use meaningful variable names and avoid abbreviations

### File Organization
- Main trading logic in `trading_bot.py` and related RL variants (`rl_trading_agent.py`, `rl_bot_ready.py`)
- Configuration centralized in `config.py`
- Database operations in `database.py`  
- Web interface in `web_dashboard.py` with templates and static files
- Chart analysis in `chart_analysis_bot.py` with PNG output generation
- Reinforcement learning models stored as `.pkl` files with versioning
- Utility scripts for analysis and reconciliation (`reconcile_positions.py`, `analyze_trades.py`)
- Service management via shell scripts (`start_*.sh`, `restart_both.sh`)

### Environment & Dependencies
- Use virtual environment (`venv/` directory)
- Dependencies managed in `requirements.txt`
- Environment variables in `.env` file (never commit secrets)
- Key dependencies: python-binance, pandas, numpy, ta-lib, flask, matplotlib, seaborn, newsapi-python
- MCP (Model Context Protocol) server integration available via `mcp_sqlite_server.py`

## Trading Bot Specific Rules

### Configuration
- All trading parameters should be defined in `config.py`
- Use `TRADING_CONFIG`, `INDICATOR_CONFIG`, and `SIGNAL_WEIGHTS` dictionaries
- Test mode should default to `use_testnet: True` for safety

### Logging
- Use the configured logging setup with both file and console handlers
- Log levels: INFO for normal operations, ERROR for exceptions, DEBUG for detailed analysis
- Log files: `trading_bot.log`, `chart_analysis_bot.log`, `web_dashboard.log`, `rl_bot.log`, `rl_retraining.log`
- Separate logs directory available for organized log management

### Error Handling
- Always wrap Binance API calls in try-except blocks
- Handle `BinanceAPIException` specifically
- Implement retry logic for network failures
- Never let the bot crash - log errors and continue

### Security
- Never hardcode API keys or secrets
- Always use environment variables for sensitive data
- Validate all user inputs
- Use testnet by default for development

## Database Rules
- Primary SQLite database in `trading_bot.db` (large file ~23MB with historical data)
- Additional database files: `trading_data.db` for specific data storage
- Use the database module functions from `database.py`
- Always close database connections properly
- Log all database operations
- MCP server provides SQL query interface to database

## Testing & Quality
- Run linting with: `python -m flake8 *.py`
- Type checking with: `python -m mypy *.py` (if mypy is available)
- Test API connections before live trading
- Always test with small amounts first

## Deployment
- Use shell scripts for service management (`start_*.sh`, `restart_both.sh`)
- PID files for process tracking (`*.pid` files)
- Log rotation for production environments
- Systemd service configuration available via `systemd-service.sh`
- Docker configuration available via `docker-start.sh`

## File Naming
- Snake_case for Python files
- Descriptive names for analysis and utility scripts
- Separate RL-related functionality with `rl_` prefix
- Chart analysis files with `chart_` prefix

## Development Workflow
1. Always test on testnet first
2. Use configuration files instead of hardcoded values  
3. Implement proper logging for debugging
4. Handle all exceptions gracefully
5. Document complex trading logic
6. Backup models and configurations before changes
7. **IMPORTANT**: After making any code changes to the project, always run `./restart_both.sh` to restart both the trading bot and web dashboard services

## Prohibited Actions
- Never commit API keys or secrets to version control
- Don't modify live trading parameters without extensive testing
- Avoid hardcoding trading symbols or parameters
- Never skip error handling for API calls
- Don't run multiple bot instances on the same account simultaneously

## Additional Features
- Market news sentiment analysis via NewsAPI integration
- Chart analysis with AI-powered insights and PNG generation
- Web dashboard with real-time monitoring at port 5000
- Reinforcement learning model training and retraining capabilities
- Position reconciliation and analysis tools
- MCP server for database querying and integration
- Automated model versioning and backup system

## ⚠️ CRITICAL REMINDER
**ALWAYS run `./restart_both.sh` after making ANY code changes to ensure all services are restarted with the updated code.**