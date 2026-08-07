"""Users CRUD router."""

import uuid

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(role: str | None = None, active_only: bool = True):
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    if role:
        query += " AND role = ?"
        params.append(role)
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY created_at DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate):
    user_id = str(uuid.uuid4())
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (body.username, body.email),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Username or email already exists")

        conn.execute(
            """INSERT INTO users (id, username, email, role)
               VALUES (?, ?, ?, ?)""",
            (user_id, body.username, body.email, body.role.value),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, role: str | None = None, is_active: bool | None = None):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        updates = []
        params = []
        if role is not None:
            updates.append("role = ?")
            params.append(role)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(int(is_active))

        if updates:
            updates.append("updated_at = datetime('now')")
            params.append(user_id)
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params
            )

        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str):
    with get_db() as conn:
        result = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
