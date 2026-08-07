"""Pydantic models for request/response schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


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


# --- Users ---

class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class UserCreate(BaseModel):
    username: str
    email: str
    role: UserRole = UserRole.DEVELOPER


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: str
    updated_at: str


# --- Deployments ---

class DeploymentStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    LIVE = "LIVE"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


class DeploymentResponse(BaseModel):
    id: str
    project_id: str
    task_id: Optional[str]
    environment: str
    cloud_provider: Optional[str]
    region: Optional[str]
    status: DeploymentStatus
    deployed_by: Optional[str]
    deployed_at: Optional[str]
    url: Optional[str]
    created_at: str


# --- Artifacts ---

class ArtifactResponse(BaseModel):
    id: int
    task_id: str
    artifact_type: str
    key: str
    value: str
    created_at: str


# --- Dashboard ---

class DashboardStats(BaseModel):
    total_projects: int
    total_deployments: int
    total_containers: int
    active_tasks: int
    success_rate: float
