#!/usr/bin/env python3
"""
Environment Setup Script for Trading Bot

This script helps set up and validate all environment variables needed
for the trading bot system to function properly.
"""

import os
import sys
from pathlib import Path
import shutil
from typing import Dict, List, Tuple

class EnvironmentSetup:
    """Environment variable setup and validation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env'
        self.comprehensive_env = self.project_root / '.env.comprehensive'
        
        # Critical environment variables that must be set
        self.critical_vars = [
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY', 
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID',
            'OPENAI_API_KEY',
            'BOT_CONTROL_PIN'
        ]
        
        # Default values for optional variables
        self.default_values = {
            'SYMBOL': 'SUIUSDC',
            'LEVERAGE': '50',
            'POSITION_PERCENT': '51.0',
            'RISK_PERCENT': '2.0',
            'TRADING_INTERVAL': '300',
            'MIN_SIGNAL_STRENGTH': '3',
            'FLASK_HOST': '0.0.0.0',
            'FLASK_PORT': '5000',
            'FLASK_ENV': 'production',
            'FLASK_DEBUG': 'false',
            'USE_TESTNET': 'false',
            'RL_ENHANCED_MODE': 'true',
            'USE_ENHANCED_REWARDS': 'true',
            'CHART_ANALYSIS_INTERVAL': '900',
            'CHART_TIMEFRAME': '15m',
            'DATABASE_PATH': 'data/trading_bot.db',
            'LOG_LEVEL': 'INFO'
        }
        
    def check_current_env(self) -> Dict[str, str]:
        """Check current environment variables"""
        current_env = {}
        
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        current_env[key.strip()] = value.strip()
        
        return current_env
    
    def validate_critical_vars(self, env_vars: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """Validate critical environment variables"""
        missing = []
        invalid = []
        
        for var in self.critical_vars:
            if var not in env_vars or not env_vars[var]:
                missing.append(var)
            elif env_vars[var] in ['your_api_key_here', 'your_token_here', 'your_key_here']:
                invalid.append(var)
                
        return missing, invalid
    
    def create_env_from_template(self) -> bool:
        """Create .env from comprehensive template"""
        try:
            if not self.comprehensive_env.exists():
                print(f"❌ Template file not found: {self.comprehensive_env}")
                return False
                
            # Copy comprehensive template to .env
            shutil.copy(self.comprehensive_env, self.env_file)
            print(f"✅ Created .env from comprehensive template")
            return True
            
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    
    def update_service_env_files(self, base_env: Dict[str, str]) -> bool:
        """Update service-specific .env files"""
        services = ['trading', 'web-dashboard', 'chart-analysis', 'mcp-server']
        
        try:
            for service in services:
                service_env_path = self.project_root / 'services' / service / '.env'
                
                if service_env_path.parent.exists():
                    # Create service-specific env with base variables plus service-specific ones
                    service_env = base_env.copy()
                    
                    # Add service-specific configurations
                    if service == 'trading':
                        service_env.update({
                            'USE_TESTNET': base_env.get('USE_TESTNET', 'false'),
                            'SYMBOL': base_env.get('SYMBOL', 'SUIUSDC'),
                            'LEVERAGE': base_env.get('LEVERAGE', '50'),
                            'POSITION_PERCENT': base_env.get('POSITION_PERCENT', '51.0'),
                            'RISK_PERCENT': base_env.get('RISK_PERCENT', '2.0'),
                            'TRADING_INTERVAL': base_env.get('TRADING_INTERVAL', '300'),
                            'MIN_SIGNAL_STRENGTH': base_env.get('MIN_SIGNAL_STRENGTH', '3')
                        })
                    elif service == 'web-dashboard':
                        service_env.update({
                            'FLASK_HOST': base_env.get('FLASK_HOST', '0.0.0.0'),
                            'FLASK_PORT': base_env.get('FLASK_PORT', '5000'),
                            'FLASK_ENV': base_env.get('FLASK_ENV', 'production'),
                            'FLASK_DEBUG': base_env.get('FLASK_DEBUG', 'false'),
                            'DASHBOARD_UPDATE_INTERVAL': base_env.get('DASHBOARD_UPDATE_INTERVAL', '30'),
                            'MAX_CHART_HISTORY_DAYS': base_env.get('MAX_CHART_HISTORY_DAYS', '90')
                        })
                    elif service == 'chart-analysis':
                        service_env.update({
                            'CHART_ANALYSIS_INTERVAL': base_env.get('CHART_ANALYSIS_INTERVAL', '900'),
                            'CHART_SYMBOL': base_env.get('SYMBOL', 'SUIUSDC'),
                            'CHART_TIMEFRAME': base_env.get('CHART_TIMEFRAME', '15m'),
                            'CHART_HISTORY_HOURS': base_env.get('CHART_HISTORY_HOURS', '24'),
                            'CHART_OUTPUT_DIR': base_env.get('CHART_OUTPUT_DIR', 'output'),
                            'AI_MODEL': base_env.get('AI_MODEL', 'gpt-4o'),
                            'MAX_ANALYSIS_RETRIES': base_env.get('MAX_ANALYSIS_RETRIES', '3')
                        })
                    
                    # Write service-specific .env file
                    with open(service_env_path, 'w') as f:
                        f.write("# Auto-generated service-specific environment file\n")
                        f.write(f"# Service: {service}\n")
                        f.write(f"# Generated by setup_env.py\n\n")
                        
                        # Write critical variables first
                        for var in self.critical_vars:
                            if var in service_env:
                                f.write(f"{var}={service_env[var]}\n")
                        f.write("\n")
                        
                        # Write other variables
                        for key, value in sorted(service_env.items()):
                            if key not in self.critical_vars:
                                f.write(f"{key}={value}\n")
                    
                    print(f"✅ Updated service environment: {service}")
        
        except Exception as e:
            print(f"❌ Error updating service env files: {e}")
            return False
        
        return True
    
    def interactive_setup(self) -> bool:
        """Interactive setup of critical environment variables"""
        print("\n🔧 Interactive Environment Setup")
        print("=" * 50)
        
        current_env = self.check_current_env()
        
        # Get user input for critical variables
        for var in self.critical_vars:
            current_value = current_env.get(var, '')
            
            if var == 'BINANCE_API_KEY':
                prompt = "Enter your Binance API Key: "
            elif var == 'BINANCE_SECRET_KEY':
                prompt = "Enter your Binance Secret Key: "
            elif var == 'TELEGRAM_BOT_TOKEN':
                prompt = "Enter your Telegram Bot Token: "
            elif var == 'TELEGRAM_CHAT_ID':
                prompt = "Enter your Telegram Chat ID: "
            elif var == 'OPENAI_API_KEY':
                prompt = "Enter your OpenAI API Key: "
            elif var == 'BOT_CONTROL_PIN':
                prompt = "Enter a 6-digit Bot Control PIN: "
            else:
                prompt = f"Enter {var}: "
            
            if current_value and current_value not in ['your_api_key_here', 'your_token_here']:
                use_current = input(f"{var} is already set. Keep current value? (y/n): ").lower().strip()
                if use_current == 'y':
                    continue
            
            new_value = input(prompt).strip()
            if new_value:
                current_env[var] = new_value
        
        # Add default values for missing optional variables
        for key, default_value in self.default_values.items():
            if key not in current_env:
                current_env[key] = default_value
        
        # Write updated .env file
        try:
            with open(self.env_file, 'w') as f:
                f.write("# Trading Bot Environment Configuration\n")
                f.write("# Generated by setup_env.py\n\n")
                
                # Write critical variables first
                f.write("# Critical Configuration\n")
                for var in self.critical_vars:
                    if var in current_env:
                        f.write(f"{var}={current_env[var]}\n")
                f.write("\n")
                
                # Write other variables
                f.write("# Optional Configuration\n")
                for key, value in sorted(current_env.items()):
                    if key not in self.critical_vars:
                        f.write(f"{key}={value}\n")
            
            print(f"✅ Environment file updated: {self.env_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error writing .env file: {e}")
            return False
    
    def validate_setup(self) -> bool:
        """Validate the complete environment setup"""
        print("\n🔍 Validating Environment Setup...")
        
        current_env = self.check_current_env()
        missing, invalid = self.validate_critical_vars(current_env)
        
        if missing:
            print(f"❌ Missing critical variables: {', '.join(missing)}")
            return False
        
        if invalid:
            print(f"⚠️  Invalid values (still using placeholders): {', '.join(invalid)}")
            return False
        
        print("✅ All critical environment variables are set!")
        
        # Check service files
        services = ['trading', 'web-dashboard', 'chart-analysis', 'mcp-server']
        for service in services:
            service_env_path = self.project_root / 'services' / service / '.env'
            if service_env_path.exists():
                print(f"✅ Service environment exists: {service}")
            else:
                print(f"⚠️  Service environment missing: {service}")
        
        return True
    
    def run_setup(self):
        """Run the complete environment setup process"""
        print("🚀 Trading Bot Environment Setup")
        print("=" * 50)
        
        # Check if .env exists
        if not self.env_file.exists():
            print("📝 No .env file found. Creating from template...")
            if not self.create_env_from_template():
                print("❌ Failed to create .env file")
                return False
        
        # Validate current setup
        current_env = self.check_current_env()
        missing, invalid = self.validate_critical_vars(current_env)
        
        if missing or invalid:
            print(f"⚠️  Found {len(missing + invalid)} issues with environment setup")
            run_interactive = input("Run interactive setup? (y/n): ").lower().strip()
            
            if run_interactive == 'y':
                if not self.interactive_setup():
                    print("❌ Interactive setup failed")
                    return False
                current_env = self.check_current_env()
        
        # Update service-specific .env files
        if not self.update_service_env_files(current_env):
            print("⚠️  Some service environment updates failed")
        
        # Final validation
        return self.validate_setup()

def main():
    setup = EnvironmentSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'validate':
            success = setup.validate_setup()
            sys.exit(0 if success else 1)
        elif command == 'interactive':
            success = setup.interactive_setup() and setup.validate_setup()
            sys.exit(0 if success else 1)
        elif command == 'template':
            success = setup.create_env_from_template()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python setup_env.py [validate|interactive|template]")
            sys.exit(1)
    else:
        # Run full setup
        success = setup.run_setup()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()