"""Report API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import Response

from export.report_exporter import ReportExporter
from services.report import ReportService


class ReportRoutes:
    """Registers report-related HTTP routes."""

    def __init__(self, router: APIRouter, report_service: ReportService) -> None:
        self._router = router
        self._report_service = report_service
        self._exporter = ReportExporter()
        self._register()

    def _register(self) -> None:
        self._router.get("/runs")(self.get_runs)
        self._router.get("/runs/{run_id}")(self.get_run_tests)
        self._router.get("/runs/{run_id}/report")(self.get_run_report)
        self._router.get("/runs-by-module")(self.get_runs_by_module)
        self._router.get("/trend")(self.get_trend)
        self._router.get("/slowest-tests")(self.get_slowest_tests)
        self._router.get("/recent-failures")(self.get_recent_failures)
        self._router.get("/most-failing-tests")(self.get_most_failing_tests)
        self._router.get("/module-health")(self.get_module_health)
        self._router.get("/run-duration-trend")(self.get_run_duration_trend)
        self._router.get("/tests")(self.get_tests)
        self._router.get("/filter-options")(self.get_filter_options)
        self._router.post("/test-run-history")(self.get_test_run_history)
        self._router.get("/summary")(self.get_summary)
        self._router.get("/modules")(self.get_modules_summary)
        self._router.get("/export/run/{run_id}")(self.export_run_report)
        self._router.get("/export/tests")(self.export_tests)

    async def get_runs(
        self,
        limit: int = Query(10, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> Dict[str, Any]:
        """List test runs with summary."""
        try:
            return await self._report_service.get_runs(limit=limit, offset=offset)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch runs")

    async def get_run_tests(
        self,
        run_id: str,
        status: Optional[str] = Query(None),
        module: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        """Get all test results for a specific run."""
        try:
            return await self._report_service.get_run_tests(
                run_id=run_id,
                status=status,
                module=module,
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch run tests")

    async def get_run_report(self, run_id: str) -> Dict[str, Any]:
        """Get full report for a run: summary, modules, and tests."""
        try:
            return await self._report_service.get_run_report(run_id=run_id)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch run report")

    async def get_summary(self) -> Dict[str, Any]:
        """Get overall summary stats."""
        try:
            return await self._report_service.get_summary()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch summary")

    async def get_modules_summary(self) -> List[Dict[str, Any]]:
        """Get pass/fail breakdown by module."""
        try:
            return await self._report_service.get_modules_summary()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch modules summary")

    async def get_tests(
        self,
        module: Optional[str] = Query(None),
        run_id: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(10, ge=1, le=2000),
        offset: int = Query(0, ge=0),
    ) -> Dict[str, Any]:
        """List all test results with optional filters (module, run_id, status)."""
        try:
            return await self._report_service.get_tests(
                module=module,
                run_id=run_id,
                status=status,
                limit=limit,
                offset=offset,
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch tests")

    async def get_filter_options(self) -> Dict[str, List[str]]:
        """Get distinct run_ids and modules for filter dropdowns."""
        try:
            return await self._report_service.get_filter_options()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch filter options")

    async def get_test_run_history(
        self,
        body: Dict[str, Any] = Body(default_factory=dict),
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get last N run statuses per (test_name, module). Body: {tests: [{test_name, module}], limit?: 10}."""
        try:
            body = body or {}
            tests = body.get("tests") or []
            raw_limit = body.get("limit", 10)
            limit = min(int(raw_limit) if raw_limit is not None else 10, 20)
            return await self._report_service.get_test_run_history(tests=tests, limit=limit)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid request body")
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch test run history")

    async def get_runs_by_module(self) -> List[Dict[str, Any]]:
        """Get runs grouped by module."""
        try:
            return await self._report_service.get_runs_by_module()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch runs by module")

    async def get_trend(
        self,
        limit: int = Query(10, ge=1, le=90),
    ) -> List[Dict[str, Any]]:
        """Get pass/fail trend by date."""
        try:
            return await self._report_service.get_trend(limit=limit)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch trend")

    async def get_slowest_tests(
        self,
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
        module: Optional[str] = Query(None),
        run_id: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        """Get slowest tests by duration, with optional module and run_id filters."""
        try:
            return await self._report_service.get_slowest_tests(
                limit=limit,
                offset=offset,
                module=module,
                run_id=run_id,
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch slowest tests")

    async def get_recent_failures(
        self,
        limit: int = Query(10, ge=1, le=50),
        offset: int = Query(0, ge=0),
        module: Optional[str] = Query(None),
        run_id: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        """Get most recent failed tests, with optional module and run_id filters."""
        try:
            return await self._report_service.get_recent_failures(
                limit=limit,
                offset=offset,
                module=module,
                run_id=run_id,
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch recent failures")

    async def get_most_failing_tests(
        self,
        limit: int = Query(10, ge=1, le=50),
        offset: int = Query(0, ge=0),
    ) -> Dict[str, Any]:
        """Get tests that fail most often."""
        try:
            return await self._report_service.get_most_failing_tests(limit=limit, offset=offset)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch most failing tests")

    async def get_module_health(self) -> List[Dict[str, Any]]:
        """Get pass rate % per module."""
        try:
            return await self._report_service.get_module_health()
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch module health")

    async def get_run_duration_trend(
        self,
        limit: int = Query(10, ge=1, le=90),
    ) -> List[Dict[str, Any]]:
        """Get run duration trend by date."""
        try:
            return await self._report_service.get_run_duration_trend(limit=limit)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch run duration trend")

    async def export_run_report(
        self,
        run_id: str,
        format: str = Query("csv", pattern="^(csv|xlsx)$"),
    ) -> Response:
        """Export run report as CSV or Excel (xlsx)."""
        try:
            report = await self._report_service.get_run_report(run_id=run_id)
            if format == "csv":
                content = self._exporter.run_report_to_csv(report)
                return Response(
                    content=content,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f'attachment; filename="run_report_{run_id}.csv"'
                    },
                )
            if format == "xlsx":
                content = self._exporter.run_report_to_excel(report)
                return Response(
                    content=content,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={
                        "Content-Disposition": f'attachment; filename="run_report_{run_id}.xlsx"'
                    },
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    async def export_tests(
        self,
        format: str = Query("csv", pattern="^(csv|xlsx)$"),
        module: Optional[str] = Query(None),
        run_id: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(5000, ge=1, le=10000),
    ) -> Response:
        """Export test results as CSV or Excel (xlsx) with optional filters."""
        try:
            data = await self._report_service.get_tests(
                module=module,
                run_id=run_id,
                status=status,
                limit=limit,
                offset=0,
            )
            tests = data.get("tests", [])
            if format == "csv":
                content = self._exporter.to_csv(tests)
                filename = "test_results.csv"
                return Response(
                    content=content,
                    media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
                )
            if format == "xlsx":
                content = self._exporter.to_excel(tests)
                return Response(
                    content=content,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="test_results.xlsx"'},
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
