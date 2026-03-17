"""MongoDB connection."""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from core.config import MongoSettings


class MongoConnection:
    """Lazy-initialized MongoDB client."""

    def __init__(self, settings: MongoSettings) -> None:
        self._settings = settings
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None
        self._collection = None

    def _ensure_connected(self) -> None:
        if self._client is not None:
            return
        try:
            self._client = AsyncIOMotorClient(
                self._settings.uri,
                serverSelectionTimeoutMS=5000,
            )
            self._db = self._client[self._settings.db_name]
            self._collection = self._db[self._settings.collection_name]
        except Exception as exc:
            raise RuntimeError("Failed to init MongoDB client") from exc

    @property
    def collection(self):
        self._ensure_connected()
        return self._collection

    async def verify(self) -> bool:
        """Ping MongoDB to verify connectivity."""
        self._ensure_connected()
        try:
            await self._client.admin.command("ping")
            return True
        except PyMongoError as exc:
            raise RuntimeError("MongoDB connection check failed") from exc
