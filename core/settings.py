import sys
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

from helper.dotenv_load_helper import find_env_file, create_sample_env_file

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
    jwt_secret: str
    redis_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    @property
    def get_postgres_dsn(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        
settings = Settings()