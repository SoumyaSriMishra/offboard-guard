from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db.driver import execute_read, is_db_connected
from app.db.queries import query_dashboard_stats, query_ghost_access_chains
from app.models.schemas import DashboardStats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def render_dashboard(request: Request):
    db_connected = is_db_connected()
    stats = execute_read(query_dashboard_stats)
    ghost_chains = execute_read(query_ghost_access_chains, limit=25, environment="production")
    error_message = None if db_connected else "CognoDB cloud instance address could not be DNS resolved. Running in Offline Demo Mode using local graph seed dataset."

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "db_connected": db_connected,
            "error_message": error_message,
            "stats": stats,
            "ghost_chains": ghost_chains
        }
    )

@router.get("/api/stats", response_model=DashboardStats)
def get_dashboard_stats_api():
    try:
        data = execute_read(query_dashboard_stats)
        return DashboardStats(**data)
    except Exception:
        return DashboardStats()
