"""Application configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class MongoSettings:
    """MongoDB configuration loaded from environment."""

    uri: str
    db_name: str
    collection_name: str

    @staticmethod
    def _get_env(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"Required env var '{key}' is not set.")
        return value

    @classmethod
    def from_env(cls) -> "MongoSettings":
        """Load .env and build settings."""
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        return cls(
            uri=cls._get_env("MONGO_URI"),
            db_name=cls._get_env("MONGO_DB_NAME"),
            collection_name=cls._get_env("MONGO_COLLECTION_NAME"),
        )
