"""
Application settings and configuration.

Loads configuration from environment variables using pydantic-settings.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # SAP AI Core Configuration
    aicore_auth_url: str
    aicore_client_id: str
    aicore_client_secret: str
    aicore_base_url: str
    aicore_resource_group: str = "default"
    
    # Gemini Model Configuration
    model_name: str = "gemini-1.5-flash"
    max_tokens: int = 4096
    temperature: float = 0.3
    
    # SURA API Keys (comma-separated list)
    sura_internal_keys: str = "sura_internal_key_001"
    
    # Application Configuration
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

_settings: Optional[Settings] = None    


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        # Load .env file if it exists
        from dotenv import load_dotenv
        load_dotenv()
        _settings = Settings()
    return _settings
