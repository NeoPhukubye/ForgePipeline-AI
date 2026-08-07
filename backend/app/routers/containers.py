"""Containers and dashboard router."""

from fastapi import APIRouter

from ..database import get_db
from ..models.schemas import ContainerResponse, DashboardStats

router = APIRouter(tags=["containers"])


@router.get("/containers", response_model=list[ContainerResponse])
def list_containers(project_id: str | None = None):
    query = "SELECT * FROM containers"
    params = []
    if project_id:
        query += " WHERE project_id = ?"
        params.append(project_id)
    query += " ORDER BY created_at DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats():
    with get_db() as conn:
        total_projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        total_deployments = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE task_type IN ('DEPLOY', 'CONTAINERIZE')"
        ).fetchone()[0]
        total_containers = conn.execute("SELECT COUNT(*) FROM containers").fetchone()[0]
        active_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('PENDING', 'RUNNING')").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'COMPLETED'").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        success_rate = (completed / total * 100) if total > 0 else 0.0

    return DashboardStats(
        total_projects=total_projects,
        total_deployments=total_deployments,
        total_containers=total_containers,
        active_tasks=active_tasks,
        success_rate=round(success_rate, 1),
    )
