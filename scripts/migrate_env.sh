#!/bin/bash
# Environment configuration migration script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔧 Migrating environment configuration..."

# Copy global .env if exists
if [ -f ".env" ]; then
    echo "✅ Global .env already exists"
else
    echo "⚠️  Creating global .env from example"
    cp .env.example .env
fi

# Create service-specific .env files from examples
services=("trading" "web-dashboard" "chart-analysis" "mcp-server")
for service in "${services[@]}"; do
    service_env="services/$service/.env"
    service_example="services/$service/.env.example"
    
    if [ -f "$service_env" ]; then
        echo "✅ $service .env already exists"
    else
        if [ -f "$service_example" ]; then
            echo "📝 Creating $service .env from example"
            cp "$service_example" "$service_env"
        else
            echo "❌ Missing $service_example"
        fi
    fi
done

echo "✅ Environment migration complete!"
echo "⚠️  Remember to update .env files with your actual values"