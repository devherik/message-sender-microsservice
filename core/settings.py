import os
import sys
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

from helpers.dotenv_load_helper import find_env_file, create_sample_env_file

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    env_path = find_env_file()
    if env_path:
        load_dotenv(env_path)
    else:
        create_sample_env_file()
        print("No .env file found. A sample .env file has been created.")
except Exception as e:
    print(f"Error loading .env file: {e}")


class Settings(BaseSettings):
    debug_mode: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"
    environment: str = os.getenv("DEVELOPMENT_ENV", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "your-default-secret")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    postgres_user: str = os.getenv("POSTGRES_USER", "user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_db: str = os.getenv("POSTGRES_DB", "messages_db")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", 5432))

    @property
    def get_postgres_dsn(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        
settings = Settings()