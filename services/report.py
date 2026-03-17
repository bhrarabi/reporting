"""Report aggregation service."""

from typing import Any, Dict, List, Optional

from core.database import MongoConnection


class ReportService:
    """Fetches and aggregates test report data from MongoDB."""

    def __init__(self, db: MongoConnection) -> None:
        self._db = db

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB doc to JSON-serializable dict."""
        out = dict(doc)
        if "_id" in out:
            out["_id"] = str(out["_id"])
        return out

    @property
    def _collection(self):
        return self._db.collection

    async def get_runs(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List runs with summary."""
        pipeline = [
            {"$sort": {"start_time": -1}},
            {
                "$group": {
                    "_id": "$run_id",
                    "start_time": {"$first": "$start_time"},
                    "end_time": {"$last": "$end_time"},
                    "total_tests": {"$sum": 1},
                    "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}},
                    "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
                    "duration": {"$sum": "$duration"},
                }
            },
            {"$sort": {"start_time": -1}},
            {"$skip": offset},
            {"$limit": limit},
            {"$project": {"_id": 0, "run_id": "$_id", "start_time": 1, "end_time": 1, "total_tests": 1, "passed": 1, "failed": 1, "duration": {"$round": ["$duration", 2]}}},
        ]
        runs = await self._collection.aggregate(pipeline).to_list(length=None)
        total_res = await self._collection.aggregate([{"$group": {"_id": "$run_id"}}, {"$count": "total"}]).to_list(length=1)
        total = total_res[0]["total"] if total_res else 0
        return {"runs": runs, "total": total}

    async def get_run_tests(
        self,
        run_id: str,
        status: Optional[str] = None,
        module: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get tests for a run with optional filters."""
        query: Dict[str, Any] = {"run_id": run_id}
        if status:
            query["status"] = status
        if module:
            query["module"] = module
        docs = await self._collection.find(query).sort("start_time", 1).to_list(length=None)
        return [self._serialize(d) for d in docs]

    async def get_run_report(self, run_id: str) -> Dict[str, Any]:
        """Get full report: summary, modules, tests."""
        match = {"run_id": run_id}

        summary_res = await self._collection.aggregate([
            {"$match": match},
            {"$group": {"_id": None, "total_tests": {"$sum": 1}, "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}, "duration": {"$sum": "$duration"}, "start_time": {"$min": "$start_time"}, "end_time": {"$max": "$end_time"}}},
            {"$project": {"_id": 0, "total_tests": 1, "passed": 1, "failed": 1, "duration": {"$round": ["$duration", 2]}, "start_time": 1, "end_time": 1}},
        ]).to_list(length=1)
        summary = summary_res[0] if summary_res else {"total_tests": 0, "passed": 0, "failed": 0, "duration": 0, "start_time": None, "end_time": None}

        modules = await self._collection.aggregate([
            {"$match": match},
            {"$group": {"_id": {"$ifNull": ["$module", ""]}, "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}, "total": {"$sum": 1}, "duration": {"$sum": "$duration"}}},
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "module": "$_id", "passed": 1, "failed": 1, "total": 1, "duration": {"$round": ["$duration", 2]}}},
        ]).to_list(length=None)

        tests = await self.get_run_tests(run_id=run_id)
        return {"run_id": run_id, "summary": summary, "modules": modules, "tests": tests}

    async def get_summary(self) -> Dict[str, Any]:
        """Get overall summary stats."""
        res = await self._collection.aggregate([
            {"$group": {"_id": None, "total_tests": {"$sum": 1}, "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}, "total_duration": {"$sum": "$duration"}}},
            {"$project": {"_id": 0, "total_tests": 1, "passed": 1, "failed": 1, "total_duration": {"$round": ["$total_duration", 2]}}},
        ]).to_list(length=1)
        return res[0] if res else {"total_tests": 0, "passed": 0, "failed": 0, "total_duration": 0}

    async def get_modules_summary(self) -> List[Dict[str, Any]]:
        """Get pass/fail by module."""
        return await self._collection.aggregate([
            {"$group": {"_id": "$module", "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}, "total": {"$sum": 1}, "duration": {"$sum": "$duration"}}},
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "module": "$_id", "passed": 1, "failed": 1, "total": 1, "duration": {"$round": ["$duration", 2]}}},
        ]).to_list(length=None)

    async def get_tests(
        self,
        module: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List tests with optional filters."""
        query: Dict[str, Any] = {}
        if module:
            query["module"] = module
        if run_id:
            query["run_id"] = run_id
        if status:
            query["status"] = status
        total = await self._collection.count_documents(query)
        docs = await self._collection.find(query).sort("start_time", -1).skip(offset).limit(limit).to_list(length=None)
        return {"tests": [self._serialize(d) for d in docs], "total": total}

    async def get_test_run_history(self, tests: List[Dict[str, str]], limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get last N run statuses per (test_name, module)."""
        if not tests:
            return {}
        or_ = []
        seen = set()
        for t in tests[:300]:
            tn, m = t.get("test_name"), t.get("module")
            if m is None or m == "":
                m = None
            if (tn, m) in seen:
                continue
            seen.add((tn, m))
            if m:
                or_.append({"test_name": tn, "module": m})
            else:
                or_.append({"test_name": tn, "module": ""})
                or_.append({"test_name": tn, "module": None})
        rows = await self._collection.aggregate([
            {"$match": {"$or": or_}},
            {"$sort": {"start_time": -1}},
            {"$group": {"_id": {"test_name": "$test_name", "module": {"$ifNull": ["$module", ""]}, "run_id": "$run_id"}, "status": {"$first": "$status"}, "start_time": {"$first": "$start_time"}, "duration": {"$first": "$duration"}}},
            {"$sort": {"start_time": -1}},
            {"$group": {"_id": {"test_name": "$_id.test_name", "module": "$_id.module"}, "runs": {"$push": {"run_id": "$_id.run_id", "status": "$status", "start_time": "$start_time", "duration": "$duration"}}}},
            {"$project": {"runs": {"$slice": ["$runs", limit]}}},
        ]).to_list(length=None)
        return {f"{r['_id']['test_name']}|{r['_id']['module']}": r["runs"] for r in rows}

    async def get_filter_options(self) -> Dict[str, List[str]]:
        """Get distinct run_ids and modules."""
        runs = await self._collection.distinct("run_id")
        modules = await self._collection.distinct("module")
        return {"run_ids": sorted(runs, reverse=True) if runs else [], "modules": sorted(modules) if modules else []}

    async def get_runs_by_module(self) -> List[Dict[str, Any]]:
        """Get runs grouped by module."""
        return await self._collection.aggregate([
            {"$sort": {"start_time": -1}},
            {"$group": {"_id": {"run_id": "$run_id", "module": "$module"}, "start_time": {"$first": "$start_time"}, "end_time": {"$last": "$end_time"}, "total_tests": {"$sum": 1}, "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}, "duration": {"$sum": "$duration"}}},
            {"$sort": {"start_time": -1}},
            {"$project": {"_id": 0, "run_id": "$_id.run_id", "module": "$_id.module", "start_time": 1, "end_time": 1, "total_tests": 1, "passed": 1, "failed": 1, "duration": {"$round": ["$duration", 2]}}},
        ]).to_list(length=None)

    async def get_trend(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pass/fail trend by date."""
        return await self._collection.aggregate([
            {"$match": {"start_time": {"$exists": True, "$ne": None}}},
            {"$addFields": {"_date": {"$cond": [{"$eq": [{"$type": "$start_time"}, "string"]}, {"$substr": ["$start_time", 0, 10]}, {"$dateToString": {"format": "%Y-%m-%d", "date": "$start_time"}}]}}},
            {"$group": {"_id": "$_date", "total": {"$sum": 1}, "passed": {"$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}}},
            {"$sort": {"_id": -1}},
            {"$limit": limit},
            {"$project": {"_id": 0, "date": "$_id", "total": 1, "passed": 1, "failed": 1}},
        ]).to_list(length=None)

    async def get_slowest_tests(
        self,
        limit: int = 10,
        offset: int = 0,
        module: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get slowest tests by duration."""
        q: Dict[str, Any] = {}
        if module:
            q["module"] = module
        if run_id:
            q["run_id"] = run_id
        total = await self._collection.count_documents(q)
        docs = await self._collection.find(q).sort("duration", -1).skip(offset).limit(limit).to_list(length=None)
        return {"items": [self._serialize(d) for d in docs], "total": total}

    async def get_recent_failures(
        self,
        limit: int = 10,
        offset: int = 0,
        module: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get most recent failures."""
        q: Dict[str, Any] = {"status": "failed"}
        if module:
            q["module"] = module
        if run_id:
            q["run_id"] = run_id
        total = await self._collection.count_documents(q)
        docs = await self._collection.find(q).sort("start_time", -1).skip(offset).limit(limit).to_list(length=None)
        return {"items": [self._serialize(d) for d in docs], "total": total}

    async def get_most_failing_tests(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Get tests that fail most often."""
        pipeline = [
            {"$match": {"test_name": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$test_name", "total": {"$sum": 1}, "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}, "module": {"$first": "$module"}, "last_failure": {"$max": "$start_time"}}},
            {"$match": {"failed": {"$gt": 0}}},
            {"$sort": {"failed": -1}},
            {"$facet": {
                "total": [{"$count": "count"}],
                "items": [{"$skip": offset}, {"$limit": limit}, {"$project": {"_id": 0, "test_name": "$_id", "failed": 1, "total": 1, "module": 1, "last_failure": 1}}],
            }},
        ]
        res = await self._collection.aggregate(pipeline).to_list(length=1)
        total = res[0]["total"][0]["count"] if res and res[0].get("total") and res[0]["total"] else 0
        items = res[0].get("items", []) if res else []
        return {"items": items, "total": total}

    async def get_module_health(self) -> List[Dict[str, Any]]:
        """Get pass rate % per module."""
        modules = await self.get_modules_summary()
        return [
            {"module": m.get("module", ""), "pass_rate": round((m["passed"] / m["total"] * 100), 1) if m.get("total") else 0, "passed": m.get("passed", 0), "failed": m.get("failed", 0), "total": m.get("total", 0)}
            for m in modules
        ]

    async def get_run_duration_trend(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get duration trend by date."""
        return await self._collection.aggregate([
            {"$match": {"start_time": {"$exists": True, "$ne": None}}},
            {"$addFields": {"_date": {"$cond": [{"$eq": [{"$type": "$start_time"}, "string"]}, {"$substr": ["$start_time", 0, 10]}, {"$dateToString": {"format": "%Y-%m-%d", "date": "$start_time"}}]}}},
            {"$group": {"_id": "$_date", "duration": {"$sum": "$duration"}, "count": {"$sum": 1}}},
            {"$sort": {"_id": -1}},
            {"$limit": limit},
            {"$project": {"_id": 0, "date": "$_id", "duration": {"$round": ["$duration", 2]}, "count": 1}},
        ]).to_list(length=None)
