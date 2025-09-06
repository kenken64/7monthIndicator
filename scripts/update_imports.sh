#!/bin/bash
# Update import paths for modular structure

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔄 Updating import paths..."

# Function to update imports in a file
update_file_imports() {
    local file=$1
    local service_name=$2
    
    if [ ! -f "$file" ]; then
        echo "  ⚠️  File not found: $file"
        return
    fi
    
    echo "  🔧 Updating imports in: $file"
    
    # Create backup
    cp "$file" "$file.backup"
    
    # Update imports to use absolute paths from project root
    # Replace direct imports with core module imports
    sed -i 's|import config|import sys; sys.path.append("'$PROJECT_ROOT'"); from core.config import *|g' "$file"
    sed -i 's|import database|import sys; sys.path.append("'$PROJECT_ROOT'"); from core.database import *|g' "$file"
    sed -i 's|from config|from core.config|g' "$file"
    sed -i 's|from database|from core.database|g' "$file"
    
    # Add environment loader import at the top if it doesn't exist
    if ! grep -q "from core.utils.env_loader import" "$file"; then
        # Add after the shebang and docstring if they exist
        if head -1 "$file" | grep -q "^#!"; then
            # Has shebang
            if head -5 "$file" | grep -q '"""'; then
                # Has docstring, add after it
                sed -i '/^"""/,/^"""/{
                    /^"""$/{
                        a\
import sys\
from pathlib import Path\
sys.path.append(str(Path(__file__).parent.parent.parent))\
from core.utils.env_loader import load_service_env, get_project_root\
from core.utils.common import setup_logging
                    }
                }' "$file"
            else
                # No docstring, add after shebang
                sed -i '1a\
import sys\
from pathlib import Path\
sys.path.append(str(Path(__file__).parent.parent.parent))\
from core.utils.env_loader import load_service_env, get_project_root\
from core.utils.common import setup_logging' "$file"
            fi
        else
            # No shebang, add at the very beginning
            sed -i '1i\
import sys\
from pathlib import Path\
sys.path.append(str(Path(__file__).parent.parent.parent))\
from core.utils.env_loader import load_service_env, get_project_root\
from core.utils.common import setup_logging' "$file"
        fi
    fi
    
    # Add service environment loading after imports
    if ! grep -q "load_service_env(" "$file"; then
        # Find the main function or if __name__ == "__main__" block and add before it
        if grep -q 'if __name__ == "__main__"' "$file"; then
            sed -i '/if __name__ == "__main__"/{
                i\
# Load service environment\
load_service_env("'$service_name'")
            }' "$file"
        elif grep -q "def main(" "$file"; then
            sed -i '/def main(/{
                i\
# Load service environment\
load_service_env("'$service_name'")
            }' "$file"
        else
            # Add at the end of imports section
            sed -i '/^import\|^from.*import/,$!b; /^$/{ a\
# Load service environment\
load_service_env("'$service_name'")\

                q
            }' "$file"
        fi
    fi
}

# Update Trading Service files
echo "🤖 Updating trading service imports..."
for file in services/trading/*.py; do
    update_file_imports "$file" "trading"
done

# Update Web Dashboard files
echo "🌐 Updating web dashboard imports..."
for file in services/web-dashboard/*.py; do
    update_file_imports "$file" "web-dashboard"  
done

# Update Chart Analysis files
echo "📊 Updating chart analysis imports..."
for file in services/chart-analysis/*.py; do
    update_file_imports "$file" "chart-analysis"
done

# Update MCP Server files
echo "🔗 Updating MCP server imports..."
for file in services/mcp-server/*.py; do
    update_file_imports "$file" "mcp-server"
done

echo "✅ Import paths updated!"
echo "📁 Backup files created with .backup extension"
echo "🧪 Test the services to ensure imports work correctly"