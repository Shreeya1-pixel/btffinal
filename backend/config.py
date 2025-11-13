"""
Configuration management for the Neuroverse AI platform.
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    llm_inference_mode: Literal["cloud", "local"] = "cloud"
    openai_api_key: str = ""
    local_model_path: str = "models/llama-2-7b-chat"
    local_model_type: str = "llama"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost,http://localhost:80"
    
    # Session Configuration
    session_timeout: int = 3600
    max_memory_items: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from configuration."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()

