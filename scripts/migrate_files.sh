#!/bin/bash
# File reorganization migration script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Starting file migration..."

# Create additional service directories and subdirectories
mkdir -p services/trading/models/backups
mkdir -p services/chart-analysis/output  
mkdir -p services/mcp-server/queries
mkdir -p services/web-dashboard/static
mkdir -p services/web-dashboard/templates

# Migrate Trading Service files
echo "🤖 Migrating trading service files..."
trading_files=(
    "rl_bot_ready.py"
    "rl_trading_agent.py" 
    "lightweight_rl.py"
    "retrain_rl_model.py"
    "trading_bot_integrated.py"
    "create_rl_bot.py"
    "rl_integration.py"
    "trading_bot_rl.py"
    "start_rl_bot.py"
    "trading_bot.py"
    "rl_patch.py"
    "rl_enhancement_patch.py"
    "integrate_rl_now.py"
)

for file in "${trading_files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" services/trading/
        echo "  ✅ Copied $file to services/trading/"
    else
        echo "  ⚠️  File not found: $file"
    fi
done

# Move RL models
echo "📦 Moving RL models..."
find . -maxdepth 1 -name "*.pkl" -type f | while read file; do
    if [ -f "$file" ]; then
        cp "$file" services/trading/models/
        echo "  ✅ Copied model: $(basename "$file")"
    fi
done

# Migrate Web Dashboard files  
echo "🌐 Migrating web dashboard files..."
if [ -f "web_dashboard.py" ]; then
    cp web_dashboard.py services/web-dashboard/
    echo "  ✅ Copied web_dashboard.py"
fi

if [ -d "static" ]; then
    cp -r static/* services/web-dashboard/static/ 2>/dev/null
    echo "  ✅ Copied static files"
fi

if [ -d "templates" ]; then
    cp -r templates/* services/web-dashboard/templates/ 2>/dev/null
    echo "  ✅ Copied templates"
fi

# Migrate Chart Analysis files
echo "📊 Migrating chart analysis files..."
chart_files=(
    "chart_analysis_bot.py"
    "multi_timeframe_strategy.py"
    "enhanced_trading_bot.py" 
    "test_integrated_strategy.py"
)

for file in "${chart_files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" services/chart-analysis/
        echo "  ✅ Copied $file to services/chart-analysis/"
    else
        echo "  ⚠️  File not found: $file"
    fi
done

# Move chart outputs
echo "📈 Moving chart files..."
find . -maxdepth 1 -name "*.png" -type f | while read file; do
    if [ -f "$file" ]; then
        cp "$file" services/chart-analysis/output/
        echo "  ✅ Copied chart: $(basename "$file")"
    fi
done

# Migrate MCP Server files
echo "🔗 Migrating MCP server files..."
if [ -f "mcp_sqlite_server.py" ]; then
    cp mcp_sqlite_server.py services/mcp-server/
    echo "  ✅ Copied mcp_sqlite_server.py"
fi

# Move shell scripts to scripts directory  
echo "📜 Migrating shell scripts..."
script_files=(
    "start_web_dashboard.sh"
    "start_rl_bot.sh" 
    "start_chart_bot.sh"
    "start_mcp_server.sh"
    "restart_both.sh"
    "docker-start.sh"
    "systemd-service.sh"
    "start_bot.sh"
    "run_analysis.sh"
)

for file in "${script_files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" scripts/
        echo "  ✅ Copied $file to scripts/"
    else
        echo "  ⚠️  Script not found: $file"
    fi
done

# Move data files
echo "💾 Organizing data files..."
find . -maxdepth 1 -name "*.db" -type f | while read file; do
    if [ -f "$file" ]; then
        cp "$file" data/
        echo "  ✅ Copied database: $(basename "$file")"
    fi
done

# Create requirements.txt for each service
echo "📋 Creating service-specific requirements.txt files..."

# Trading service requirements
cat > services/trading/requirements.txt << 'EOF'
python-binance==1.0.19
pandas>=2.2.0
numpy>=1.26.0
ta-lib>=0.4.28
python-dotenv==1.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
matplotlib>=3.8.0
seaborn>=0.13.0
EOF

# Web dashboard requirements  
cat > services/web-dashboard/requirements.txt << 'EOF'
flask>=3.0.0
python-dotenv==1.0.0
pandas>=2.2.0
numpy>=1.26.0
matplotlib>=3.8.0
seaborn>=0.13.0
requests>=2.31.0
EOF

# Chart analysis requirements
cat > services/chart-analysis/requirements.txt << 'EOF'
python-binance==1.0.19
pandas>=2.2.0
numpy>=1.26.0
ta-lib>=0.4.28
matplotlib>=3.8.0
seaborn>=0.13.0
python-dotenv==1.0.0
requests>=2.31.0
openai>=1.0.0
newsapi-python>=0.2.7
pillow>=10.0.0
EOF

# MCP server requirements
cat > services/mcp-server/requirements.txt << 'EOF'
mcp>=1.0.0
sqlite3
python-dotenv==1.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
EOF

echo "✅ File migration complete!"
echo "📊 Migration Summary:"
echo "  🤖 Trading files: $(ls -1 services/trading/*.py 2>/dev/null | wc -l) files"
echo "  🌐 Web dashboard: $(ls -1 services/web-dashboard/ 2>/dev/null | wc -l) items"  
echo "  📊 Chart analysis: $(ls -1 services/chart-analysis/*.py 2>/dev/null | wc -l) files"
echo "  🔗 MCP server: $(ls -1 services/mcp-server/*.py 2>/dev/null | wc -l) files"
echo "  📜 Scripts: $(ls -1 scripts/*.sh 2>/dev/null | wc -l) scripts"
echo "  💾 Data files: $(ls -1 data/ 2>/dev/null | wc -l) files"