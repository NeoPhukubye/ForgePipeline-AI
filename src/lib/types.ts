export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string;
  source_repo_url: string;
  cloud_provider: string | null;
  deployment_region: string | null;
  created_at: string;
  updated_at: string;
}

export type TaskType = "CONTAINERIZE" | "DEPLOY";
export type TaskStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Task {
  id: string;
  project_id: string;
  task_type: TaskType;
  status: TaskStatus;
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface TaskLog {
  id: string;
  task_id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR";
  message: string;
}

export interface DeploymentArtifact {
  id: string;
  task_id: string;
  artifact_type: "DOCKER_IMAGE_URL" | "CLOUD_RESOURCE_URL" | "ECS_SERVICE_ARN";
  value: string;
  created_at: string;
}