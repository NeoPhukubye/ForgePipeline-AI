import { useEffect, useState } from "react";
import { FolderKanban, Rocket, Container, Activity } from "lucide-react";
import StatCard from "../components/StatCard";
import ActivityFeed from "../components/ActivityFeed";
import StatusBadge from "../components/StatusBadge";
import { api } from "../lib/api";
import type { DashboardStats, Project, Task } from "../lib/api";
import type { TaskStatus } from "../lib/types";

const fallbackActivities = [
  { id: "1", type: "deploy" as const, project: "web-app-staging", message: "Deployed to AWS ECS Fargate (us-east-1)", timestamp: "2 minutes ago" },
  { id: "2", type: "containerize" as const, project: "api-gateway", message: "Docker image built and pushed to ECR", timestamp: "15 minutes ago" },
  { id: "3", type: "commit" as const, project: "web-app-staging", message: "Source repository cloned and analyzed", timestamp: "1 hour ago" },
  { id: "4", type: "error" as const, project: "analytics-service", message: "Containerization failed — Dockerfile generation error", timestamp: "2 hours ago" },
];

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, p, t] = await Promise.all([
          api.getStats(),
          api.listProjects(),
          api.listTasks(),
        ]);
        setStats(s);
        setProjects(p);
        setTasks(t);
        setConnected(true);
      } catch {
        setConnected(false);
      }
    };
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const activities = tasks.slice(0, 5).map((t) => ({
    id: t.id,
    type: t.task_type === "DEPLOY" ? "deploy" as const : t.status === "FAILED" ? "error" as const : "containerize" as const,
    project: projects.find((p) => p.id === t.project_id)?.name || "Unknown",
    message: t.error_message || `${t.task_type} task ${t.status.toLowerCase()}`,
    timestamp: t.started_at ? new Date(t.started_at).toLocaleString() : "Queued",
  }));

  const displayActivities = connected ? activities : fallbackActivities;

  const recentProjects = (connected ? projects : []).slice(0, 4).map((p) => {
    const latestTask = tasks.find((t) => t.project_id === p.id);
    return {
      id: p.id,
      name: p.name,
      repo: p.source_repo_url,
      status: (latestTask?.status || "PENDING") as TaskStatus,
      cloud: p.deployment_target || p.cloud_provider || "—",
    };
  });

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Dashboard</h2>
          <p className="mt-1 text-sm text-foreground/50">
            Overview of your deployment pipeline and recent activity
          </p>
        </div>
        {!connected && (
          <span className="rounded-full bg-yellow-500/10 px-3 py-1 text-xs font-medium text-yellow-500">
            Backend offline — showing demo data
          </span>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Projects"
          value={stats?.total_projects ?? 12}
          icon={<FolderKanban className="h-5 w-5" />}
          trend={{ value: connected ? `${stats?.active_tasks ?? 0} active tasks` : "+2 this week", positive: true }}
        />
        <StatCard
          title="Deployments"
          value={stats?.total_deployments ?? 47}
          icon={<Rocket className="h-5 w-5" />}
          trend={{ value: connected ? `${stats?.success_rate ?? 0}% success rate` : "+12% vs last month", positive: true }}
          subtitle="Total"
        />
        <StatCard
          title="Containers"
          value={stats?.total_containers ?? 89}
          icon={<Container className="h-5 w-5" />}
          trend={{ value: "Built & pushed", positive: true }}
          subtitle="Images"
        />
        <StatCard
          title="Active Tasks"
          value={stats?.active_tasks ?? 3}
          icon={<Activity className="h-5 w-5" />}
          trend={{ value: "In progress", positive: true }}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <div className="rounded-xl border border-border bg-surface">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <h3 className="text-sm font-semibold text-foreground">Recent Projects</h3>
              <span className="text-xs text-foreground/40">{recentProjects.length} shown</span>
            </div>
            <div className="divide-y divide-border">
              {recentProjects.length === 0 && (
                <p className="px-5 py-6 text-center text-sm text-foreground/40">
                  {connected ? "No projects yet. Create one to get started." : "Start the backend to see real data."}
                </p>
              )}
              {recentProjects.map((project) => (
                <div key={project.id} className="flex items-center justify-between px-5 py-3.5 transition-colors hover:bg-muted/50">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">{project.name}</p>
                    <p className="truncate text-xs text-foreground/40">{project.repo}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="hidden text-xs text-foreground/50 sm:block">{project.cloud}</span>
                    <StatusBadge status={project.status} size="sm" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <ActivityFeed activities={displayActivities} />
        </div>
      </div>
    </div>
  );
}
