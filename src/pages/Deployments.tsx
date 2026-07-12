import { useState } from "react";
import { RefreshCw, Search, Terminal, Eye } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import type { TaskStatus } from "../lib/types";

interface DeploymentItem {
  id: string;
  project: string;
  type: "CONTAINERIZE" | "DEPLOY";
  status: TaskStatus;
  started: string;
  duration: string;
  logs: string[];
}

const initialDeployments: DeploymentItem[] = [
  {
    id: "1",
    project: "web-app-staging",
    type: "DEPLOY",
    status: "COMPLETED",
    started: "2 min ago",
    duration: "4m 12s",
    logs: [
      "[INFO] Starting deployment pipeline...",
      "[INFO] Pulling Docker image: 987654321.dkr.ecr.us-east-1.amazonaws.com/web-app:latest",
      "[INFO] Creating ECS task definition revision...",
      "[INFO] Updating ECS service: web-app-service-staging",
      "[INFO] Deployment successful. New tasks are running.",
    ],
  },
  {
    id: "2",
    project: "api-gateway",
    type: "CONTAINERIZE",
    status: "RUNNING",
    started: "15 min ago",
    duration: "12m 08s",
    logs: [
      "[INFO] Cloning repository: github.com/org/api-gateway",
      "[INFO] Analyzing codebase...",
      "[INFO] Detected: Node.js 20, Express.js",
      "[INFO] Generating multi-stage Dockerfile...",
      "[INFO] Building Docker image...",
      "[WARN] npm audit found 3 moderate vulnerabilities",
      "[INFO] Pushing image to ECR...",
    ],
  },
  {
    id: "3",
    project: "analytics-service",
    type: "DEPLOY",
    status: "FAILED",
    started: "2 hours ago",
    duration: "8m 45s",
    logs: [
      "[INFO] Starting deployment pipeline...",
      "[INFO] Pulling Docker image...",
      "[INFO] Creating ECS task definition revision...",
      "[ERROR] Service deployment failed: ResourceInitializationError",
      "[ERROR] Unable to pull container image: timeout exceeded",
      "[INFO] Initiating rollback to previous revision...",
      "[INFO] Rollback completed successfully.",
    ],
  },
  {
    id: "4",
    project: "user-service",
    type: "CONTAINERIZE",
    status: "COMPLETED",
    started: "3 hours ago",
    duration: "3m 20s",
    logs: [
      "[INFO] Cloning repository: github.com/org/user-svc",
      "[INFO] Analyzing codebase...",
      "[INFO] Detected: Python 3.11, FastAPI",
      "[INFO] Generating optimized multi-stage Dockerfile...",
      "[INFO] Building Docker image...",
      "[INFO] Image size optimized: 142MB final stage",
      "[INFO] Pushing image to ECR...",
    ],
  },
  {
    id: "5",
    project: "payment-worker",
    type: "DEPLOY",
    status: "PENDING",
    started: "Just now",
    duration: "--",
    logs: [
      "[INFO] Deployment queued. Waiting for available executor...",
    ],
  },
];

export default function Deployments() {
  const [search, setSearch] = useState("");
  const [selectedLogs, setSelectedLogs] = useState<DeploymentItem | null>(null);
  const [filter, setFilter] = useState<string>("all");

  const filtered = initialDeployments.filter((d) => {
    const matchesSearch = d.project.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === "all" || d.status === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Deployments</h2>
          <p className="mt-1 text-sm text-foreground/50">
            Monitor containerization and deployment tasks
          </p>
        </div>
        <button className="btn-secondary">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <input
            className="input-field pl-9"
            placeholder="Search deployments..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-1.5 rounded-lg border border-border bg-surface p-1">
          {["all", "RUNNING", "COMPLETED", "FAILED", "PENDING"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                filter === f
                  ? "bg-primary text-white"
                  : "text-foreground/60 hover:text-foreground"
              }`}
            >
              {f === "all" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Deployments list */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-surface p-12 text-center">
          <Terminal className="mb-3 h-10 w-10 text-foreground/20" />
          <p className="text-sm font-medium text-foreground/50">No deployments found</p>
          <p className="mt-1 text-xs text-foreground/40">
            {search ? "Try a different search term" : "Trigger a deployment from your projects page"}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((deployment) => (
            <div
              key={deployment.id}
              className="rounded-xl border border-border bg-surface transition-all hover:border-foreground/20"
            >
              <div className="flex items-center justify-between px-5 py-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium text-foreground">{deployment.project}</p>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
                      deployment.type === "DEPLOY"
                        ? "bg-accent/10 text-accent"
                        : "bg-primary/10 text-primary"
                    }`}>
                      {deployment.type}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-foreground/40">
                    Started {deployment.started} · Duration: {deployment.duration}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={deployment.status} />
                  <button
                    onClick={() => setSelectedLogs(selectedLogs?.id === deployment.id ? null : deployment)}
                    className="btn-secondary px-3 py-1.5 text-xs"
                    aria-label={`View logs for ${deployment.project}`}
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Logs
                  </button>
                </div>
              </div>

              {/* Log viewer */}
              {selectedLogs?.id === deployment.id && (
                <div className="border-t border-border px-5 py-4">
                  <div className="log-viewer max-h-48 overflow-y-auto rounded-lg bg-black/40 p-3">
                    {deployment.logs.map((line, i) => {
                      const level = line.includes("[ERROR]") ? "text-destructive"
                        : line.includes("[WARN]") ? "text-yellow-400"
                        : line.includes("[INFO]") ? "text-accent"
                        : "text-foreground/60";
                      return (
                        <p key={i} className={`terminal-text ${level}`}>
                          {line}
                        </p>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}