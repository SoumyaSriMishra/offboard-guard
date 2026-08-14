import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.db.driver import check_connectivity, close_driver, is_db_connected
from app.routers import dashboard, employees, graph
from app.models.schemas import HealthCheckResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("offboardguard")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OffboardGuard application...")
    connected = check_connectivity()
    if not connected:
        logger.warning("DB connectivity check failed at startup. Application will start in graceful degraded mode.")
    yield
    logger.info("Shutting down OffboardGuard application...")
    close_driver()

app = FastAPI(
    title="OffboardGuard — Graph-Based Permission Analyzer",
    description="Graph database permission & offboarding risk analyzer for detecting Ghost Access",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(dashboard.router)
app.include_router(employees.router)
app.include_router(graph.router)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/img/wexa-icon.svg", media_type="image/svg+xml")

@app.get("/health")
def health_check(request: Request, format: str = ""):
    connected = is_db_connected()
    accept_header = request.headers.get("accept", "")

    # If JSON is explicitly requested (e.g. via curl, API client, or ?format=json)
    if format.lower() == "json" or "application/json" in accept_header and "text/html" not in accept_header:
        return JSONResponse(content={
            "status": "healthy" if connected else "degraded",
            "database_connected": connected,
            "message": "CognoDB connection active" if connected else "CognoDB is unreachable or disconnected"
        })

    # Render styled Wexa HTML page for browser navigation
    return templates.TemplateResponse(
        request=request,
        name="health.html",
        context={
            "db_connected": connected,
            "db_uri": settings.COGNO_URI
        }
    )
