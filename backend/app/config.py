"""Configuration for InkQ backend."""
import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Get the root directory (two levels up from this file)
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


def parse_cors_origins(value: Optional[str]) -> List[str]:
    """Parse CORS origins from environment variable.
    
    Supports JSON array format: '["http://localhost:4173", "http://localhost:4321"]'
    Falls back to comma-separated values or single value.
    """
    if not value:
        return ["http://localhost:4321"]  # Default for dev
    
    # Try parsing as JSON array first
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Fall back to comma-separated or single value
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    # Required: must be provided via environment or .env
    inkq_pg_url: str = Field(..., env="INKQ_PG_URL")

    # API
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

    # CORS - parsed from BACKEND_CORS_ORIGINS env var
    # This will be set after instantiation via model_post_init
    backend_cors_origins: List[str] = ["http://localhost:4321"]

    # Media storage
    media_root: str = os.getenv("MEDIA_ROOT", str(ROOT_DIR / "media"))
    media_url_prefix: str = os.getenv("MEDIA_URL_PREFIX", "/media")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    def model_post_init(self, __context) -> None:
        """Parse CORS origins from environment variable after initialization."""
        env_value = os.getenv("BACKEND_CORS_ORIGINS")
        if env_value:
            self.backend_cors_origins = parse_cors_origins(env_value)

    class Config:
        # Load variables from project root .env if it exists, otherwise rely on real environment
        env_file = str(ENV_FILE) if ENV_FILE.exists() else None
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Ignore extra fields in .env file (like INKQ_API_URL for frontend)
        extra = "ignore"


try:
    settings = Settings()
except Exception as exc:  # pragma: no cover - defensive startup guard
    raise RuntimeError(
        "Failed to load InkQ backend settings. "
        "Ensure INKQ_PG_URL is set in the environment or in the project root .env file."
    ) from exc

