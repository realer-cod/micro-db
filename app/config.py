from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Database connection
    database_url: str = "postgresql+asyncpg://admin:admin123@localhost:5432/proxy_stats"
    
    # PostgreSQL settings (для Docker Compose)
    postgres_db: str = "proxy_stats"
    postgres_user: str = "admin" 
    postgres_password: str = "admin123"
    
    # API
    secret_key: str = "your-secret-key-change-in-production"
    debug: bool = True
    
    # App
    app_name: str = "Proxy Stats API"
    version: str = "0.1.0"
     # Время в минутах, после которого курсы валют считаются устаревшими
    CURRENCY_UPDATE_THRESHOLD_MINUTES: int = Field(1440, description="Cache lifetime for currency rates in minutes")
    CRYPTOCOMPARE_API_KEY: str
    class Config:
        env_file = ".env"

settings = Settings()
