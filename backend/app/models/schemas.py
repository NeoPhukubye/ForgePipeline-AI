"""Pydantic models for request/response schemas."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TaskType(str, Enum):
    CONTAINERIZE = "CONTAINERIZE"
    DEPLOY = "DEPLOY"
    ANALYZE = "ANALYZE"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


# --- Projects ---

class ProjectCreate(BaseModel):
    name: str
    source_repo_url: str
    description: str = ""
    cloud_provider: Optional[str] = None
    deployment_target: Optional[str] = None
    deployment_region: Optional[str] = None
    environment: str = "staging"


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    source_repo_url: str
    cloud_provider: Optional[str]
    deployment_target: Optional[str]
    deployment_region: Optional[str]
    environment: str
    created_at: str
    updated_at: str


# --- Tasks ---

class TaskResponse(BaseModel):
    id: str
    project_id: str
    task_type: TaskType
    status: TaskStatus
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    created_at: str


class TaskLogResponse(BaseModel):
    id: int
    task_id: str
    timestamp: str
    level: LogLevel
    message: str


# --- Deployments ---

class DeployRequest(BaseModel):
    project_id: str
    task_type: TaskType = TaskType.DEPLOY
    dry_run: bool = False


class AnalyzeRequest(BaseModel):
    project_id: str


# --- Containers ---

class ContainerResponse(BaseModel):
    id: str
    project_id: str
    name: str
    image_uri: str
    tag: str
    size_bytes: Optional[int]
    pushed_at: Optional[str]
    created_at: str


# --- Dashboard ---

class DashboardStats(BaseModel):
    total_projects: int
    total_deployments: int
    total_containers: int
    active_tasks: int
    success_rate: float
