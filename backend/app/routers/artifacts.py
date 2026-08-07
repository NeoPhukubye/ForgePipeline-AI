"""Artifacts router - browse pipeline artifacts."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models.schemas import ArtifactResponse

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("", response_model=list[ArtifactResponse])
def list_artifacts(task_id: Optional[str] = None, artifact_type: Optional[str] = None):
    query = "SELECT * FROM artifacts WHERE 1=1"
    params = []
    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)
    if artifact_type:
        query += " AND artifact_type = ?"
        params.append(artifact_type)
    query += " ORDER BY created_at DESC LIMIT 100"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return dict(row)
