from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Employee(BaseModel):
    id: str
    name: str
    email: str
    department: str
    status: str
    offboarded_at: Optional[str] = None
    reachable_resources_count: int = 0

class GhostAccessChain(BaseModel):
    employee_id: str
    employee_name: str
    employee_email: str
    department: str
    offboarded_at: Optional[str] = None
    resource_id: str
    resource_name: str
    resource_type: str
    environment: str
    sensitivity: str
    hops: int
    path_nodes: List[Dict[str, Any]] = []
    path_relationships: List[Dict[str, Any]] = []

class DashboardStats(BaseModel):
    total_employees: int = 0
    active_employees: int = 0
    offboarded_employees: int = 0
    ghost_chains_count: int = 0
    ghost_resources_count: int = 0
    top_risky_resources: List[Dict[str, Any]] = []

class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    status: Optional[str] = None
    environment: Optional[str] = None
    sensitivity: Optional[str] = None
    department: Optional[str] = None

class GraphEdge(BaseModel):
    id: Any
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    label: str

    class Config:
        populate_by_name = True

class GraphDataResponse(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

class HealthCheckResponse(BaseModel):
    status: str
    database_connected: bool
    message: str
