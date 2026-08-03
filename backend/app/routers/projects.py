"""Projects CRUD router."""

import uuid
from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models.schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate):
    project_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO projects (id, name, description, source_repo_url, cloud_provider, deployment_target, deployment_region, environment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, body.name, body.description, body.source_repo_url,
             body.cloud_provider, body.deployment_target, body.deployment_region, body.environment),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return dict(row)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return dict(row)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str):
    with get_db() as conn:
        result = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
