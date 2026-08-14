from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from app.db.driver import execute_read, is_db_connected
from app.db.queries import query_all_employees, query_employee_blast_radius

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/employees")
def render_employee_directory(
    request: Request,
    search: str = Query("", description="Search by name, email, or department"),
    status: str = Query("all", description="Filter by status: all, active, offboarded")
):
    db_connected = is_db_connected()
    employees = execute_read(query_all_employees, search=search, status_filter=status)
    error_message = None if db_connected else "Running in Offline Demo Mode using local graph seed dataset."

    return templates.TemplateResponse(
        request=request,
        name="employees.html",
        context={
            "db_connected": db_connected,
            "error_message": error_message,
            "employees": employees,
            "search": search,
            "status_filter": status
        }
    )

@router.get("/employees/{employee_id}")
def render_employee_detail(request: Request, employee_id: str):
    db_connected = is_db_connected()
    blast_radius = execute_read(query_employee_blast_radius, employee_id=employee_id)
    error_message = None if db_connected else "Running in Offline Demo Mode using local graph seed dataset."

    if not blast_radius or not blast_radius.get("employee"):
        error_message = f"Employee ID '{employee_id}' not found."

    employee_info = blast_radius.get("employee", {}) if blast_radius else {}

    return templates.TemplateResponse(
        request=request,
        name="employee.html",
        context={
            "db_connected": db_connected,
            "error_message": error_message,
            "employee_id": employee_id,
            "employee": employee_info,
            "blast_radius": blast_radius
        }
    )

@router.get("/api/employees/{employee_id}/blast-radius")
def get_employee_blast_radius_api(employee_id: str):
    data = execute_read(query_employee_blast_radius, employee_id=employee_id)
    if not data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return data
