# Core configuration module
import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # API Configuration
    finnhub_api_key: str = Field(..., description="Finnhub API key")
    api_timeout: int = Field(default=30, ge=5, le=120, description="API timeout in seconds")
    api_max_retries: int = Field(default=3, ge=1, le=10, description="Maximum API retry attempts")
    
    # Processing Configuration
    max_workers: int = Field(
        default_factory=lambda: min(10, os.cpu_count() or 4),
        ge=1, le=20,
        description="Maximum worker threads"
    )
    page_size: int = Field(default=100, ge=1, le=1000, description="Default page size for processing")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=300, description="API rate limit per minute")
    
    # File Configuration
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="Maximum file size in MB")
    allowed_extensions: List[str] = Field(default=[".csv"], description="Allowed file extensions")
    upload_dir: Path = Field(default=Path("data"), description="Upload directory path")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_rotation: str = Field(default="10 MB", description="Log rotation size")
    log_retention: str = Field(default="10 days", description="Log retention period")
    
    # Application Configuration
    app_name: str = Field(default="Finding Tickers", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
