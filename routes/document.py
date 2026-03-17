"""Document ingestion routes."""

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException

from core.database import MongoConnection
from services.document import DocumentService


class DocumentRoutes:
    """Registers document-related HTTP routes and lifecycle hooks."""

    def __init__(
        self,
        app: FastAPI,
        document_service: DocumentService,
        mongo_connection: MongoConnection,
    ) -> None:
        self._app = app
        self._document_service = document_service
        self._mongo_connection = mongo_connection
        self._register()

    def _register(self) -> None:
        self._app.on_event("startup")(self.startup_event)
        self._app.post("/documents/bulk")(self.create_documents)

    async def startup_event(self) -> None:
        """Verify MongoDB connection on application startup."""
        await self._mongo_connection.verify()

    async def create_documents(self, documents: List[Dict[str, Any]]) -> dict:
        """Receive a list of JSON documents and insert them into MongoDB."""
        try:
            inserted_count = await self._document_service.create(documents)
            return {"test_results_count": inserted_count}
        except Exception:
            raise HTTPException(
                status_code=500, detail="Failed to insert documents into MongoDB"
            )
