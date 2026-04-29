"""FastAPI application for the Audit Readiness Dashboard."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.demo_data import get_dashboard_data, get_projects, get_controls, get_deadlines
from src.models import CoverageStatus, to_dict

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Audit Readiness Dashboard", version="1.0.0")

# Mount static files (CSS)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# --- CORS middleware ---
from starlette.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve the main dashboard HTML page."""
    data = get_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"data": data},
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "audit-readiness-dashboard"}


@app.get("/api/dashboard")
async def api_dashboard():
    """Return full dashboard data as JSON."""
    data = get_dashboard_data()
    return JSONResponse(content=to_dict(data))


@app.get("/api/projects")
async def api_projects():
    """Return list of all projects."""
    projects = get_projects()
    return JSONResponse(content=to_dict(projects))


@app.get("/api/projects/{project_id}")
async def api_project_detail(project_id: str):
    """Return detail for a single project."""
    projects = get_projects()
    for p in projects:
        if p.project_id == project_id.upper():
            return JSONResponse(content=to_dict(p))
    return JSONResponse(content={"error": "Project not found"}, status_code=404)


@app.get("/api/controls")
async def api_controls(category: str = None):
    """Return control coverage matrix, optionally filtered by category."""
    controls = get_controls()
    if category:
        controls = [c for c in controls if c.category.lower() == category.lower()]
    return JSONResponse(content=to_dict(controls))


@app.get("/api/controls/gaps")
async def api_control_gaps():
    """Return only controls with GAP or PARTIAL coverage."""
    controls = get_controls()
    gaps = [c for c in controls if c.status in (CoverageStatus.GAP, CoverageStatus.PARTIAL)]
    return JSONResponse(content=to_dict(gaps))


@app.get("/api/deadlines")
async def api_deadlines():
    """Return upcoming deadlines sorted by date."""
    deadlines = get_deadlines()
    return JSONResponse(content=to_dict(deadlines))


@app.get("/api/stats")
async def api_stats():
    """Return summary statistics."""
    data = get_dashboard_data()
    return JSONResponse(content=to_dict(data.summary))
