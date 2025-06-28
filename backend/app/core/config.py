"""
Application configuration using Pydantic Settings for type safety and validation.
"""
from functools import lru_cache
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/splitwise"
    database_pool_size: int = 20
    database_max_overflow: int = 0
    database_pool_pre_ping: bool = True
    database_pool_recycle: int = 300
    database_echo: bool = False
    
    # API settings
    api_title: str = "Splitwise API"
    api_version: str = "1.0.0"
    api_description: str = "A simplified expense splitting application"
    debug: bool = False
    
    # CORS settings
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # External API settings
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 500
    deepseek_temperature: float = 0.7
    
    # Performance settings
    chatbot_response_cache_ttl: int = 300  # 5 minutes
    balance_cache_ttl: int = 60  # 1 minute
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Database connection retry settings
    db_max_retries: int = 30
    db_retry_delay: int = 2
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    @field_validator("deepseek_api_key", mode="before")
    @classmethod
    def get_deepseek_api_key(cls, v):
        return os.getenv("DEEPSEEK_API_KEY", v)


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
