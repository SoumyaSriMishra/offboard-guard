from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db.driver import execute_read, is_db_connected
from app.db.queries import query_full_graph_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/graph")
def render_graph_explorer(request: Request):
    db_connected = is_db_connected()
    return templates.TemplateResponse(
        request=request,
        name="graph.html",
        context={
            "db_connected": db_connected
        }
    )

@router.get("/api/graph/ghost-access")
def get_graph_data_api():
    try:
        data = execute_read(query_full_graph_data)
        return data
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}
