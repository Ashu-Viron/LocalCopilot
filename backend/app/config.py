"""Configuration module for AI Workspace backend."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App configuration
    APP_NAME: str = "AI Workspace"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS configuration
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    # Workspace configuration
    WORKSPACE_PATH: str = os.getenv("WORKSPACE_PATH", "./workspace")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
    
    # FreeTheAI API Configuration (OpenAI-compatible)
    FREETHEAI_API_KEY: str = os.getenv("FREETHEAI_API_KEY", "")
    FREETHEAI_BASE_URL: str = os.getenv("FREETHEAI_BASE_URL", "https://api.freetheai.xyz/v1")
    
    # Legacy A4F API Configuration (deprecated, kept for backward compatibility)
    A4F_API_KEY: str = os.getenv("A4F_API_KEY", "")
    A4F_BASE_URL: str = os.getenv("A4F_BASE_URL", "https://api.a4f.co/v1")
    
    # Legacy API keys (optional, for direct provider access)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Security
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "your-secret-key-change-in-production")
    
    # Agent configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "300"))
    
    # Database configuration (Neon Postgres)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def workspace_dir(self) -> Path:
        """Get the workspace directory as a Path object."""
        return Path(self.WORKSPACE_PATH).resolve()
    
    def validate_workspace(self) -> bool:
        """Validate that workspace directory exists and is accessible."""
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error validating workspace: {e}")
            return False


# Create a global settings instance
settings = Settings()
