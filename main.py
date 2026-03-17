"""Test Reporting API - FastAPI application."""

from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import MongoSettings
from core.database import MongoConnection
from routes.document import DocumentRoutes
from routes.report import ReportRoutes
from services.document import DocumentService
from services.report import ReportService

# Config and database
settings = MongoSettings.from_env()
mongo = MongoConnection(settings)

# Services
document_service = DocumentService(mongo)
report_service = ReportService(mongo)

# App
app = FastAPI(title="Test Reporting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
DocumentRoutes(app, document_service, mongo)

api_router = APIRouter(prefix="/api/reports", tags=["reports"])
ReportRoutes(api_router, report_service)
app.include_router(api_router)

# Static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    """Serve the reporting dashboard."""
    index_path = STATIC_DIR / "dashboard" / "index.html"
    if index_path.exists():
        return FileResponse(
            index_path,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
    return {"message": "Dashboard not found. Run from project root."}
