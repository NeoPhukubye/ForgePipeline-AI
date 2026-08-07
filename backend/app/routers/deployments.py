"""Deployments router - deployment history and management."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models.schemas import DeploymentResponse, DeploymentStatus

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("", response_model=list[DeploymentResponse])
def list_deployments(
    project_id: Optional[str] = None,
    environment: Optional[str] = None,
    status: Optional[str] = None,
):
    query = "SELECT * FROM deployments WHERE 1=1"
    params = []
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if environment:
        query += " AND environment = ?"
        params.append(environment)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT 50"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deployment_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return dict(row)


@router.patch("/{deployment_id}/status", response_model=DeploymentResponse)
def update_deployment_status(deployment_id: str, status: DeploymentStatus):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deployment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")

        conn.execute(
            "UPDATE deployments SET status = ? WHERE id = ?",
            (status.value, deployment_id),
        )
        row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deployment_id,)).fetchone()
    return dict(row)


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
def rollback_deployment(deployment_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deployment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")
        if dict(row)["status"] != "LIVE":
            raise HTTPException(status_code=400, detail="Can only rollback LIVE deployments")

        conn.execute(
            "UPDATE deployments SET status = 'ROLLED_BACK' WHERE id = ?",
            (deployment_id,),
        )
        row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deployment_id,)).fetchone()
    return dict(row)
