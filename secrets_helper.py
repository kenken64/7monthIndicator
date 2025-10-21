"""
Docker Secrets Helper Module
Reads secrets from Docker secrets location (/run/secrets/) or falls back to environment variables.
"""

import os
from pathlib import Path


class SecretsManager:
    """Manager for reading Docker secrets or environment variables"""

    SECRETS_DIR = Path("/run/secrets")

    @staticmethod
    def get_secret(secret_name: str, env_var_name: str = None) -> str:
        """
        Get a secret value from Docker secrets or environment variables.

        Args:
            secret_name: Name of the secret file in /run/secrets/
            env_var_name: Name of the environment variable (defaults to secret_name in uppercase)

        Returns:
            Secret value as string

        Raises:
            ValueError: If secret is not found in either location
        """
        if env_var_name is None:
            env_var_name = secret_name.upper()

        # Try to read from Docker secrets first
        secret_file = SecretsManager.SECRETS_DIR / secret_name
        if secret_file.exists():
            try:
                return secret_file.read_text().strip()
            except Exception as e:
                print(f"Warning: Failed to read secret from {secret_file}: {e}")

        # Fall back to environment variable
        value = os.getenv(env_var_name)
        if value:
            return value

        # If neither exists, raise an error
        raise ValueError(
            f"Secret '{secret_name}' not found in Docker secrets or environment variable '{env_var_name}'"
        )

    @staticmethod
    def get_secret_safe(secret_name: str, env_var_name: str = None, default: str = None) -> str:
        """
        Get a secret value safely, returning default if not found.

        Args:
            secret_name: Name of the secret file in /run/secrets/
            env_var_name: Name of the environment variable (defaults to secret_name in uppercase)
            default: Default value to return if secret is not found

        Returns:
            Secret value as string, or default if not found
        """
        try:
            return SecretsManager.get_secret(secret_name, env_var_name)
        except ValueError:
            return default


# Convenience functions for common secrets
def get_binance_api_key() -> str:
    """Get Binance API key"""
    return SecretsManager.get_secret("binance_api_key", "BINANCE_API_KEY")


def get_binance_secret_key() -> str:
    """Get Binance secret key"""
    return SecretsManager.get_secret("binance_secret_key", "BINANCE_SECRET_KEY")


def get_openai_api_key() -> str:
    """Get OpenAI API key"""
    return SecretsManager.get_secret("openai_api_key", "OPENAI_API_KEY")


def get_telegram_bot_token() -> str:
    """Get Telegram bot token"""
    return SecretsManager.get_secret("telegram_bot_token", "TELEGRAM_BOT_TOKEN")


def get_telegram_chat_id() -> str:
    """Get Telegram chat ID"""
    return SecretsManager.get_secret("telegram_chat_id", "TELEGRAM_CHAT_ID")


def get_bot_control_pin() -> str:
    """Get bot control PIN"""
    return SecretsManager.get_secret("bot_control_pin", "BOT_CONTROL_PIN")


def get_news_api_key() -> str:
    """Get News API key"""
    return SecretsManager.get_secret("news_api_key", "NEWS_API_KEY")


# Example usage
if __name__ == "__main__":
    print("Testing secrets manager...")
    try:
        print(f"Binance API Key: {get_binance_api_key()[:10]}...")
        print(f"OpenAI API Key: {get_openai_api_key()[:10]}...")
        print("All secrets loaded successfully!")
    except ValueError as e:
        print(f"Error: {e}")
