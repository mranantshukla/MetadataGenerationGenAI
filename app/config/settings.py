# app/config/settings.py
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "Automated Metadata Generation System"
    API_VERSION: str = "2.0.0"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".pptx", ".xlsx"]
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    
    # Database Settings
    DATABASE_URL: Optional[str] = "sqlite:///./metadata.db"
    DATABASE_ECHO: bool = False
    
    # Redis Settings
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    
    # Celery Settings
    CELERY_BROKER_URL: Optional[str] = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: Optional[str] = "redis://localhost:6379/0"
    CELERY_ENABLED: bool = False
    
    # Model Settings
    MODEL_CACHE_DIR: str = "./models"
    USE_GPU: bool = False
    BATCH_SIZE: int = 8
    MAX_TEXT_LENGTH: int = 10000  # Max characters for processing
    
    # Security Settings
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENABLED: bool = False
    
    # Language Detection
    LANGUAGE_DETECTION_ENABLED: bool = True
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr", "de", "it"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

