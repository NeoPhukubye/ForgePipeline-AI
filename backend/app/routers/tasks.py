"""Tasks and deployment pipeline router."""

import os
import sys
import threading
import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

# Add parent project to path for forgepipeline_ai imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ..database import get_db
from ..models.schemas import (
    DeployRequest,
    TaskLogResponse,
    TaskResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _log(conn, task_id: str, level: str, message: str):
    conn.execute(
        "INSERT INTO task_logs (task_id, level, message) VALUES (?, ?, ?)",
        (task_id, level, message),
    )
    conn.commit()


def _run_pipeline(task_id: str, project_id: str, task_type: str, dry_run: bool):
    """Background thread that runs the ForgePipeline agent pipeline."""
    from forgepipeline_ai import (
        ExecutionEngine,
        IntentParser,
        PlanningAgent,
    )

    with get_db() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'RUNNING', started_at = datetime('now') WHERE id = ?",
            (task_id,),
        )
        conn.commit()
        _log(conn, task_id, "INFO", "Pipeline started")

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            conn.execute(
                "UPDATE tasks SET status = 'FAILED', error_message = 'Project not found' WHERE id = ?",
                (task_id,),
            )
            return

        project = dict(project)

    start_time = time.time()

    try:
        with get_db() as conn:
            # Parse intent
            parser = IntentParser()
            intent = parser.parse(
                repo=project["source_repo_url"],
                target=project.get("deployment_target") or "aws-ecs",
                env=project.get("environment") or "staging",
            )
            action = intent.get("action", "deploy")
            platform = intent.get("target_platform", "unknown")
            _log(conn, task_id, "INFO", f"Intent parsed: {action} to {platform}")

            # Create plan
            planner = PlanningAgent()
            plan = planner.create_plan(intent)
            _log(conn, task_id, "INFO", f"Plan created with {plan.total_steps} steps")

            # Execute
            engine = ExecutionEngine(dry_run=dry_run)

            def on_step_start(step):
                with get_db() as c:
                    _log(c, task_id, "INFO", f"Executing: {step.description}")

            def on_step_complete(step):
                with get_db() as c:
                    _log(c, task_id, "INFO", f"Completed: {step.description}")

            def on_step_fail(step, error):
                with get_db() as c:
                    _log(c, task_id, "ERROR", f"Failed: {step.description} - {error}")

            engine.on_step_start(on_step_start)
            engine.on_step_complete(on_step_complete)
            engine.on_step_fail(on_step_fail)

            ctx = engine.execute_plan(plan, intent)

            duration = time.time() - start_time

            if ctx.errors:
                conn.execute(
                    """UPDATE tasks SET status = 'FAILED', completed_at = datetime('now'),
                       duration_seconds = ?, error_message = ? WHERE id = ?""",
                    (duration, "; ".join(ctx.errors), task_id),
                )
                _log(conn, task_id, "ERROR", f"Pipeline failed: {ctx.errors[0]}")
            else:
                conn.execute(
                    """UPDATE tasks SET status = 'COMPLETED', completed_at = datetime('now'),
                       duration_seconds = ? WHERE id = ?""",
                    (duration, task_id),
                )
                _log(conn, task_id, "INFO", f"Pipeline completed successfully in {duration:.1f}s")

                # Store artifacts
                if ctx.analysis:
                    for key, val in ctx.analysis.to_dict().items():
                        conn.execute(
                            "INSERT INTO artifacts (task_id, artifact_type, key, value) VALUES (?, ?, ?, ?)",
                            (task_id, "ANALYSIS", key, str(val)),
                        )

                if ctx.dockerfile_content:
                    conn.execute(
                        "INSERT INTO artifacts (task_id, artifact_type, key, value) VALUES (?, ?, ?, ?)",
                        (task_id, "DOCKERFILE", "content", ctx.dockerfile_content),
                    )

                if ctx.full_image_ref:
                    container_id = str(uuid.uuid4())
                    name = ctx.image_name or "app"
                    conn.execute(
                        """INSERT INTO containers (id, project_id, task_id, name, image_uri, tag, pushed_at)
                           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (container_id, project_id, task_id, name, ctx.full_image_ref, ctx.image_tag or "latest"),
                    )

    except Exception as e:
        duration = time.time() - start_time
        with get_db() as conn:
            conn.execute(
                """UPDATE tasks SET status = 'FAILED', completed_at = datetime('now'),
                   duration_seconds = ?, error_message = ? WHERE id = ?""",
                (duration, str(e), task_id),
            )
            _log(conn, task_id, "ERROR", f"Unexpected error: {e}")


@router.post("/deploy", response_model=TaskResponse, status_code=202)
def trigger_deploy(body: DeployRequest):
    task_id = str(uuid.uuid4())
    with get_db() as conn:
        # Verify project exists
        project = conn.execute("SELECT id FROM projects WHERE id = ?", (body.project_id,)).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        conn.execute(
            "INSERT INTO tasks (id, project_id, task_type, status) VALUES (?, ?, ?, 'PENDING')",
            (task_id, body.project_id, body.task_type.value),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    # Run pipeline in background
    thread = threading.Thread(
        target=_run_pipeline,
        args=(task_id, body.project_id, body.task_type.value, body.dry_run),
        daemon=True,
    )
    thread.start()

    return dict(row)


@router.get("", response_model=list[TaskResponse])
def list_tasks(project_id: Optional[str] = None, status: Optional[str] = None):
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT 50"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@router.get("/{task_id}/logs", response_model=list[TaskLogResponse])
def get_task_logs(task_id: str):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM task_logs WHERE task_id = ? ORDER BY timestamp ASC",
            (task_id,),
        ).fetchall()
    return [dict(r) for r in rows]
