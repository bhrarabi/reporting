"""Document ingestion service."""

import copy
import re
from typing import Any, Dict, List

from core.database import MongoConnection


class DocumentService:
    """Handles bulk document insertion with run_id assignment."""

    def __init__(self, db: MongoConnection) -> None:
        self._db = db

    async def _next_run_id(self) -> str:
        """Get next run_id (run_1, run_2, ...)."""
        run_ids = await self._db.collection.distinct("run_id")
        max_num = 0
        for rid in run_ids:
            if not rid:
                continue
            m = re.match(r"^run_(\d+)$", str(rid), re.I)
            if m:
                max_num = max(max_num, int(m.group(1)))
        return f"run_{max_num + 1}"

    async def create(self, documents: List[Dict[str, Any]]) -> int:
        """Insert documents with a single run_id for the batch."""
        docs = [copy.deepcopy(d) for d in documents]
        run_id = await self._next_run_id()

        for doc in docs:
            doc["run_id"] = run_id
            doc["run_by_who"] = "Bahar"  # TODO: get from portal

        result = await self._db.collection.insert_many(docs)
        return len(result.inserted_ids)
