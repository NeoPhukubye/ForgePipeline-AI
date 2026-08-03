const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8080/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Types matching backend schemas ---

export interface Project {
  id: string;
  name: string;
  description: string;
  source_repo_url: string;
  cloud_provider: string | null;
  deployment_target: string | null;
  deployment_region: string | null;
  environment: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  project_id: string;
  task_type: "CONTAINERIZE" | "DEPLOY" | "ANALYZE";
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  created_at: string;
}

export interface TaskLog {
  id: number;
  task_id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "DEBUG";
  message: string;
}

export interface ContainerImage {
  id: string;
  project_id: string;
  name: string;
  image_uri: string;
  tag: string;
  size_bytes: number | null;
  pushed_at: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_projects: number;
  total_deployments: number;
  total_containers: number;
  active_tasks: number;
  success_rate: number;
}

// --- API functions ---

export const api = {
  // Projects
  listProjects: () => request<Project[]>("/projects"),
  createProject: (data: { name: string; source_repo_url: string; cloud_provider?: string; deployment_target?: string; deployment_region?: string; environment?: string }) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" }),

  // Tasks
  listTasks: (params?: { project_id?: string; status?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set("project_id", params.project_id);
    if (params?.status) searchParams.set("status", params.status);
    const qs = searchParams.toString();
    return request<Task[]>(`/tasks${qs ? `?${qs}` : ""}`);
  },
  getTask: (id: string) => request<Task>(`/tasks/${id}`),
  getTaskLogs: (id: string) => request<TaskLog[]>(`/tasks/${id}/logs`),
  triggerDeploy: (data: { project_id: string; task_type?: "DEPLOY" | "CONTAINERIZE"; dry_run?: boolean }) =>
    request<Task>("/tasks/deploy", { method: "POST", body: JSON.stringify(data) }),

  // Containers
  listContainers: (project_id?: string) => {
    const qs = project_id ? `?project_id=${project_id}` : "";
    return request<ContainerImage[]>(`/containers${qs}`);
  },

  // Dashboard
  getStats: () => request<DashboardStats>("/dashboard/stats"),

  // Health
  health: () => request<{ status: string }>("/health"),
};
