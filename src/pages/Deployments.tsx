import { useEffect, useState } from "react";
import { RefreshCw, Search, Terminal, Eye } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../lib/api";
import type { Task, TaskLog, Project } from "../lib/api";
import type { TaskStatus } from "../lib/types";

export default function Deployments() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("all");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedLogs, setSelectedLogs] = useState<string | null>(null);
  const [logs, setLogs] = useState<Record<string, TaskLog[]>>({});
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [t, p] = await Promise.all([api.listTasks(), api.listProjects()]);
      setTasks(t);
      setProjects(p);
    } catch { /* offline */ }
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadLogs = async (taskId: string) => {
    if (selectedLogs === taskId) {
      setSelectedLogs(null);
      return;
    }
    try {
      const taskLogs = await api.getTaskLogs(taskId);
      setLogs((prev) => ({ ...prev, [taskId]: taskLogs }));
    } catch { /* ignore */ }
    setSelectedLogs(taskId);
  };

  const getProjectName = (projectId: string) =>
    projects.find((p) => p.id === projectId)?.name || "Unknown";

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "--";
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}m ${sec}s`;
  };

  const formatTime = (time: string | null) => {
    if (!time) return "Queued";
    const diff = Date.now() - new Date(time).getTime();
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return new Date(time).toLocaleDateString();
  };

  const filtered = tasks.filter((t) => {
    const matchesSearch = getProjectName(t.project_id).toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === "all" || t.status === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Deployments</h2>
          <p className="mt-1 text-sm text-foreground/50">
            Monitor containerization and deployment tasks
          </p>
        </div>
        <button onClick={load} className="btn-secondary">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

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
                filter === f ? "bg-primary text-white" : "text-foreground/60 hover:text-foreground"
              }`}
            >
              {f === "all" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      )}

      {!loading && filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-surface p-12 text-center">
          <Terminal className="mb-3 h-10 w-10 text-foreground/20" />
          <p className="text-sm font-medium text-foreground/50">No deployments found</p>
          <p className="mt-1 text-xs text-foreground/40">
            {search ? "Try a different search term" : "Trigger a deployment from your projects page"}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((task) => (
            <div key={task.id} className="rounded-xl border border-border bg-surface transition-all hover:border-foreground/20">
              <div className="flex items-center justify-between px-5 py-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium text-foreground">{getProjectName(task.project_id)}</p>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
                      task.task_type === "DEPLOY" ? "bg-accent/10 text-accent" : "bg-primary/10 text-primary"
                    }`}>
                      {task.task_type}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-foreground/40">
                    Started {formatTime(task.started_at)} · Duration: {formatDuration(task.duration_seconds)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={task.status as TaskStatus} />
                  <button
                    onClick={() => loadLogs(task.id)}
                    className="btn-secondary px-3 py-1.5 text-xs"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Logs
                  </button>
                </div>
              </div>

              {selectedLogs === task.id && (
                <div className="border-t border-border px-5 py-4">
                  <div className="log-viewer max-h-48 overflow-y-auto rounded-lg bg-black/40 p-3">
                    {(logs[task.id] || []).length === 0 && (
                      <p className="terminal-text text-foreground/40">No logs available yet...</p>
                    )}
                    {(logs[task.id] || []).map((log) => {
                      const level = log.level === "ERROR" ? "text-destructive"
                        : log.level === "WARN" ? "text-yellow-400"
                        : "text-accent";
                      return (
                        <p key={log.id} className={`terminal-text ${level}`}>
                          [{log.level}] {log.message}
                        </p>
                      );
                    })}
                    {task.error_message && (
                      <p className="terminal-text text-destructive">[ERROR] {task.error_message}</p>
                    )}
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
