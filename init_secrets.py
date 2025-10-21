"""
Initialize Docker Secrets into Environment Variables
This module loads Docker secrets and sets them as environment variables
so existing code can continue using os.getenv() without modification.
"""

import os
from pathlib import Path


def init_secrets():
    """
    Load Docker secrets into environment variables if they're not already set.
    This allows existing code to work without modification.
    """
    SECRETS_DIR = Path("/run/secrets")

    # Mapping of secret files to environment variable names
    SECRET_MAPPINGS = {
        "binance_api_key": "BINANCE_API_KEY",
        "binance_secret_key": "BINANCE_SECRET_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
        "telegram_chat_id": "TELEGRAM_CHAT_ID",
        "bot_control_pin": "BOT_CONTROL_PIN",
        "news_api_key": "NEWS_API_KEY",
    }

    secrets_loaded = []

    for secret_file, env_var in SECRET_MAPPINGS.items():
        # Skip if environment variable is already set
        if os.getenv(env_var):
            continue

        # Try to read from Docker secrets
        secret_path = SECRETS_DIR / secret_file
        if secret_path.exists():
            try:
                secret_value = secret_path.read_text().strip()
                os.environ[env_var] = secret_value
                secrets_loaded.append(env_var)
            except Exception as e:
                print(f"Warning: Failed to load secret {secret_file}: {e}")

    if secrets_loaded:
        print(f"✅ Loaded {len(secrets_loaded)} secrets from Docker secrets")
    else:
        print("ℹ️  Using environment variables (development mode)")


# Auto-initialize when imported
init_secrets()
