"""Configuration management for the application."""

import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Flask settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("FLASK_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./translation_system.db"
    )
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-jwt-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # ML Model settings
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "./models")
    DEVICE: str = os.getenv("DEVICE", "cpu")
    MODEL_CACHE_DIR: str = os.path.expanduser("~/.cache/huggingface/hub")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "3600"))  # 1 hour
    
    # Redis settings (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_REDIS: bool = os.getenv("USE_REDIS", "False").lower() == "true"
    
    # API settings
    API_TITLE: str = "AI Language Translation API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = ["txt", "pdf", "doc", "docx"]
    
    # Translation settings
    MAX_TEXT_LENGTH: int = 5000  # Maximum characters to translate
    DEFAULT_BATCH_SIZE: int = 32
    TRANSLATION_TIMEOUT: int = 30  # seconds
    
    # Supported languages
    SUPPORTED_LANGUAGES: dict = {
        "en": "English",
        "hi": "Hindi",
        "kn": "Kannada",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "pt": "Portuguese",
        "te": "Telugu",
        "ta": "Tamil",
        "ml": "Malayalam"
    }
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
