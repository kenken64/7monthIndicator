"""Environment configuration loader for modular services"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_service_env(service_name=None):
    """Load global + service-specific environment variables
    
    Args:
        service_name (str, optional): Name of the service (trading, web-dashboard, etc.)
        
    Returns:
        dict: Environment variables as a dictionary
    """
    project_root = Path(__file__).parent.parent.parent
    
    # Load global environment first
    global_env = project_root / '.env'
    if global_env.exists():
        load_dotenv(global_env)
        print(f"✅ Loaded global environment: {global_env}")
    else:
        print(f"⚠️  Global .env file not found: {global_env}")
    
    # Load service-specific environment (overrides global)
    if service_name:
        service_env = project_root / 'services' / service_name / '.env'
        if service_env.exists():
            load_dotenv(service_env)
            print(f"✅ Loaded service environment: {service_env}")
        else:
            print(f"⚠️  Service .env file not found: {service_env}")
    
    return dict(os.environ)

def get_project_root():
    """Get absolute path to project root
    
    Returns:
        Path: Absolute path to project root directory
    """
    return Path(__file__).parent.parent.parent.absolute()

def get_database_path(db_name='trading_bot.db'):
    """Get absolute path to database file
    
    Args:
        db_name (str): Database filename
        
    Returns:
        str: Absolute path to database file
    """
    return str(get_project_root() / 'data' / db_name)

def get_log_path(log_name):
    """Get absolute path to log file
    
    Args:
        log_name (str): Log filename
        
    Returns:
        str: Absolute path to log file
    """
    return str(get_project_root() / 'logs' / log_name)