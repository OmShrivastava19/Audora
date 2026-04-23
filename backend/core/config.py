"""Configuration management for Audora backend."""
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
import json


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        """Initialize settings from .env file and environment."""
        # Load from root .env file
        self._load_env()

        # Private keys (never sent to frontend)
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.FIREBASE_SERVICE_ACCOUNT_KEY: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")

        # Firebase admin config (loaded from ini-style section in .env)
        self.FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "audora-36200")
        self.FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "")
        self.FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")

        # Public keys (sent to frontend)
        self.FIREBASE_WEB_API_KEY: str = os.getenv("FIREBASE_WEB_API_KEY", "")
        self.OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "")
        self.OAUTH_CLIENT_SECRET: str = os.getenv("OAUTH_CLIENT_SECRET", "")

        # Server settings
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.ALLOWED_ORIGINS: list = self._parse_origins()

    def _load_env(self):
        """Load .env file from project root."""
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            self._load_simple_env(env_path)

    @staticmethod
    def _load_simple_env(path: Path):
        """Load simple KEY=VALUE format .env file."""
        if path.exists():
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and not os.getenv(key):
                            os.environ[key] = value

    def _parse_origins(self) -> list:
        """Parse CORS allowed origins from environment."""
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://localhost:3000")
        return [o.strip() for o in origins_str.split(",") if o.strip()]

    def get_public_config(self) -> dict:
        """Return only the configuration that is safe to send to the frontend."""
        return {
            "FIREBASE_WEB_API_KEY": self.FIREBASE_WEB_API_KEY,
            "OAUTH_CLIENT_ID": self.OAUTH_CLIENT_ID,
            "DEBUG": self.DEBUG,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
