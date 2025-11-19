"""
PyInstaller configuration and utilities for Celim_Desvio RPA
Following Clean Architecture principles and security best practices
"""

import sys
from pathlib import Path
from typing import Optional


def get_executable_directory() -> Path:
    """
    Get the directory where the executable is located.
    This works both for development and PyInstaller bundled executables.

    Returns:
        Path: The directory containing the executable or script
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running in PyInstaller bundle
        return Path(sys.executable).parent
    else:
        # Running in development
        return Path(__file__).parent.parent


def get_config_directory() -> Path:
    """
    Get the configuration directory for the application.
    This should be where .env and other config files are located.

    Returns:
        Path: The configuration directory path
    """
    exe_dir = get_executable_directory()

    # Look for config directory in the same folder as executable
    config_dir = exe_dir / "config"
    if not config_dir.exists():
        config_dir.mkdir(exist_ok=True)

    return config_dir


def find_env_file() -> Optional[Path]:
    """
    Find the .env file in the expected locations.
    Follows the order: executable_dir/config/.env -> executable_dir/.env -> None

    Returns:
        Optional[Path]: Path to .env file if found, None otherwise
    """
    exe_dir = get_executable_directory()

    # Priority order for .env file locations
    env_locations = [
        exe_dir / "config" / ".env",
        exe_dir / ".env",
        exe_dir / "core" / ".env",  # Fallback for development
    ]

    for env_path in env_locations:
        if env_path.exists():
            return env_path

    return None


def create_sample_env_file() -> None:
    """
    Create a sample .env file in the config directory for user reference.
    This helps users understand what configuration is needed.
    """
    config_dir = get_config_directory()
    sample_env_path = config_dir / ".env.sample"

    if not sample_env_path.exists():
        sample_content = """
# Environment variables for the application
IS_DEV=<True/False>
DOCUMENTATION_PATH=<your_documentation_path>
# Notion configuration
NOTION_TOKEN=<your_notion_token>
NOTION_ID=<your_notion_id>
# LLMs configuration
GEMINI_API_KEY=<your_gemini_api_key>
OPENAI_API_KEY=<your_openai_api_key>
# Telegram Bot configuration
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
TELEGRAM_WEBHOOK_URL=<your_telegram_webhook_url>
# NGROK configuration
NGROK_AUTH_TOKEN=<your_ngrok_auth_token>
# PsVector database configuration
POSTGRES_USER=<your_postgres_user>
POSTGRES_PASSWORD=<your_postgres_password>
POSTGRES_DB=<my_database_name>
POSTGRES_PORT=<my_database_port>
POSTGRES_USE_PERSISTENT=False
POSTGRES_PERSISTENT_PATH=<my_persistent_path>
# SQL Server configuration
SQLSERVER_HOST=<your_sqlserver_host>
SQLSERVER_USER=<your_sqlserver_user>
SQLSERVER_PASSWORD=<your_sqlserver_password>
SQLSERVER_DB=<your_sqlserver_db>
SQLSERVER_DRIVER=<your_sqlserver_driver>
# SQL Local configuration
MARIADB_HOST=<your_mariadb_host>
MARIADB_PORT=<your_mariadb_port>
MARIADB_USER=<your_mariadb_user>
MARIADB_PASSWORD=<your_mariadb_password>
# Secrets
SECRET_KEY=<your_secret_key>
ALGORITHM=<your_algorithm>
ACCESS_TOKEN_EXPIRE_MINUTES=<your_access_token_expire_minutes>
"""

        with open(sample_env_path, "w", encoding="utf-8") as f:
            f.write(sample_content)

        print(f"Sample configuration file created at: {sample_env_path}")
        print("Please copy it to .env and configure your actual values.")
