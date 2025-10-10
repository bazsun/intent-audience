"""Configuration management for the Intent-Audience system."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://intent_user:intent_pass@localhost:5432/intent_audience",
        env="DATABASE_URL"
    )
    mongodb_url: str = Field(
        default="mongodb://intent_user:intent_pass@localhost:27017/intent_audience",
        env="MONGODB_URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # ML Configuration
    model_storage_path: str = Field(default="data/models/", env="MODEL_STORAGE_PATH")
    feature_store_path: str = Field(default="data/features/", env="FEATURE_STORE_PATH")
    ml_worker_count: int = Field(default=4, env="ML_WORKER_COUNT")
    
    # API Configuration
    api_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        env="API_SECRET_KEY"
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        env="CORS_ORIGINS"
    )
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Performance Settings
    max_customers_per_request: int = Field(
        default=100000,
        env="MAX_CUSTOMERS_PER_REQUEST"
    )
    audience_generation_timeout: int = Field(
        default=300,
        env="AUDIENCE_GENERATION_TIMEOUT"
    )
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Privacy Settings
    enable_pii_hashing: bool = Field(default=True, env="ENABLE_PII_HASHING")
    data_retention_days: int = Field(default=90, env="DATA_RETENTION_DAYS")
    audit_log_enabled: bool = Field(default=True, env="AUDIT_LOG_ENABLED")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()