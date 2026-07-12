import { FolderKanban, Rocket, Container, Activity } from "lucide-react";
import StatCard from "../components/StatCard";
import ActivityFeed from "../components/ActivityFeed";
import StatusBadge from "../components/StatusBadge";
import type { TaskStatus } from "../lib/types";

const recentActivities = [
  {
    id: "1",
    type: "deploy" as const,
    project: "web-app-staging",
    message: "Deployed to AWS ECS Fargate (us-east-1)",
    timestamp: "2 minutes ago",
  },
  {
    id: "2",
    type: "containerize" as const,
    project: "api-gateway",
    message: "Docker image built and pushed to ECR",
    timestamp: "15 minutes ago",
  },
  {
    id: "3",
    type: "commit" as const,
    project: "web-app-staging",
    message: "Source repository cloned and analyzed",
    timestamp: "1 hour ago",
  },
  {
    id: "4",
    type: "error" as const,
    project: "analytics-service",
    message: "Containerization failed — Dockerfile generation error",
    timestamp: "2 hours ago",
  },
  {
    id: "5",
    type: "containerize" as const,
    project: "user-service",
    message: "Multi-stage Dockerfile generated successfully",
    timestamp: "3 hours ago",
  },
];

const recentProjects = [
  { id: "1", name: "web-app-staging", repo: "github.com/org/web-app", status: "COMPLETED" as TaskStatus, cloud: "AWS ECS" },
  { id: "2", name: "api-gateway", repo: "github.com/org/api-gateway", status: "RUNNING" as TaskStatus, cloud: "AWS ECS" },
  { id: "3", name: "user-service", repo: "github.com/org/user-svc", status: "COMPLETED" as TaskStatus, cloud: "AWS ECS" },
  { id: "4", name: "analytics-service", repo: "github.com/org/analytics", status: "FAILED" as TaskStatus, cloud: "AWS ECS" },
];

export default function Dashboard() {
  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {/* Welcome */}
      <div>
        <h2 className="text-xl font-bold text-foreground">Dashboard</h2>
        <p className="mt-1 text-sm text-foreground/50">
          Overview of your deployment pipeline and recent activity
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Projects"
          value={12}
          icon={<FolderKanban className="h-5 w-5" />}
          trend={{ value: "+2 this week", positive: true }}
        />
        <StatCard
          title="Deployments"
          value={47}
          icon={<Rocket className="h-5 w-5" />}
          trend={{ value: "+12% vs last month", positive: true }}
          subtitle="Total successful"
        />
        <StatCard
          title="Containers"
          value={89}
          icon={<Container className="h-5 w-5" />}
          trend={{ value: "+8 this week", positive: true }}
          subtitle="Built & pushed"
        />
        <StatCard
          title="Active Tasks"
          value={3}
          icon={<Activity className="h-5 w-5" />}
          trend={{ value: "2 running, 1 pending", positive: true }}
          subtitle="In progress"
        />
      </div>

      {/* Recent Projects + Activity */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Recent Projects Table */}
        <div className="lg:col-span-3">
          <div className="rounded-xl border border-border bg-surface">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <h3 className="text-sm font-semibold text-foreground">Recent Projects</h3>
              <span className="text-xs text-foreground/40">4 active</span>
            </div>
            <div className="divide-y divide-border">
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

        {/* Activity Feed */}
        <div className="lg:col-span-2">
          <ActivityFeed activities={recentActivities} />
        </div>
      </div>
    </div>
  );
}