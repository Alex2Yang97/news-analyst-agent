import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Database URLs
    DATABASE_URL: str = "postgresql://news_analyst:news_analyst_password@localhost:5432/news_analyst_db"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://news_analyst:news_analyst_password@localhost:5432/news_analyst_db"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Chainlit settings
    CHAINLIT_AUTH_SECRET: str = os.getenv("CHAINLIT_AUTH_SECRET", "")

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
