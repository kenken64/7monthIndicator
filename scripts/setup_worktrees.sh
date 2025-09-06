#!/bin/bash
# Git worktree setup script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🌳 Setting up git worktrees for modular architecture...${NC}"
echo ""

# First, commit the current modular structure to main
echo -e "${BLUE}📝 Committing modular structure to main branch...${NC}"
git add .
git commit -m "feat: Migrate to modular git worktree structure

🏗️  Architecture Changes:
- Split monolith into 4 independent services
- Created core/ for shared components (config, database, utilities)
- Added service-specific environment configurations
- Updated import paths for modular structure
- Created individual service startup scripts

🤖 Services:
- services/trading/ - RL-enhanced trading bot
- services/web-dashboard/ - Flask web interface  
- services/chart-analysis/ - AI-powered chart analysis
- services/mcp-server/ - Model Context Protocol server

📦 Core Components:
- core/config.py - Centralized configuration
- core/database.py - Database management
- core/utils/ - Shared utilities and environment loading

🔧 Management:
- scripts/restart_all.sh - Master service control
- Individual service startup scripts
- Service-specific requirements.txt files

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Modular structure committed to main${NC}"
else
    echo -e "${RED}❌ Failed to commit modular structure${NC}"
    exit 1
fi

echo ""

# Create service branches
services=("trading-service" "web-dashboard" "chart-analysis" "mcp-server")
service_dirs=("trading" "web-dashboard" "chart-analysis" "mcp-server")

for i in "${!services[@]}"; do
    service="${services[$i]}"
    service_dir="${service_dirs[$i]}"
    
    echo -e "${BLUE}📝 Creating branch: $service${NC}"
    git checkout -b "$service" main
    
    # Remove other services' directories but keep core and scripts
    echo -e "  🗂️  Cleaning up branch for $service_dir service..."
    
    # Remove other service directories
    for other_dir in "${service_dirs[@]}"; do
        if [ "$other_dir" != "$service_dir" ]; then
            if [ -d "services/$other_dir" ]; then
                git rm -rf "services/$other_dir"
                echo -e "    ❌ Removed services/$other_dir"
            fi
        fi
    done
    
    # Commit the service-specific branch
    git commit -m "feat: Create $service branch with service-specific files

Contains only:
- core/ - Shared components
- services/$service_dir/ - Service-specific files
- scripts/ - Management scripts  
- data/ - Shared data
- logs/ - Centralized logging

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>" --allow-empty

    echo -e "${GREEN}  ✅ Branch $service created${NC}"
    
    # Return to main
    git checkout main
    sleep 1
done

echo ""
echo -e "${BLUE}🔗 Creating git worktrees...${NC}"

# Create worktrees directory if it doesn't exist
mkdir -p services

# Create worktrees for each service
for i in "${!services[@]}"; do
    service="${services[$i]}"
    service_dir="${service_dirs[$i]}"
    worktree_path="services/$service_dir"
    
    echo -e "${BLUE}🔗 Creating worktree: $service_dir -> $service${NC}"
    
    # Remove existing directory if it exists
    if [ -d "$worktree_path" ]; then
        echo -e "  🧹 Removing existing $worktree_path directory..."
        rm -rf "$worktree_path"
    fi
    
    # Create the worktree
    git worktree add "$worktree_path" "$service"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✅ Worktree created: $worktree_path${NC}"
        
        # Make service script executable in the worktree
        if [ -f "$worktree_path/start_service.sh" ]; then
            chmod +x "$worktree_path/start_service.sh"
        fi
    else
        echo -e "${RED}  ❌ Failed to create worktree: $worktree_path${NC}"
    fi
    
    sleep 1
done

echo ""
echo -e "${GREEN}✅ Git worktrees setup complete!${NC}"
echo ""

# Show worktree status
echo -e "${PURPLE}📊 Worktree Status:${NC}"
git worktree list

echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo -e "  1. Each service can now be developed independently"
echo -e "  2. Use ${BLUE}cd services/<service>${NC} to work on specific services"
echo -e "  3. Each worktree has its own git history and branches"
echo -e "  4. Use ${BLUE}./scripts/restart_all.sh${NC} to manage all services"
echo -e "  5. Test services individually with ${BLUE}./start_service.sh${NC} in each service directory"

echo ""
echo -e "${BLUE}🚀 Ready to start modular services!${NC}"