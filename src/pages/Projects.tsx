import { useState } from "react";
import { Plus, Search, ExternalLink, GitBranch } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import type { TaskStatus } from "../lib/types";

interface ProjectItem {
  id: string;
  name: string;
  repo: string;
  status: TaskStatus;
  cloud: string;
  region: string;
  updated: string;
}

const initialProjects: ProjectItem[] = [
  { id: "1", name: "web-app-staging", repo: "github.com/org/web-app", status: "COMPLETED", cloud: "AWS ECS", region: "us-east-1", updated: "2 min ago" },
  { id: "2", name: "api-gateway", repo: "github.com/org/api-gateway", status: "RUNNING", cloud: "AWS ECS", region: "eu-west-1", updated: "15 min ago" },
  { id: "3", name: "user-service", repo: "github.com/org/user-svc", status: "COMPLETED", cloud: "AWS ECS", region: "us-east-1", updated: "3 hours ago" },
  { id: "4", name: "analytics-service", repo: "github.com/org/analytics", status: "FAILED", cloud: "AWS ECS", region: "us-east-1", updated: "2 hours ago" },
  { id: "5", name: "payment-worker", repo: "github.com/org/payment-worker", status: "PENDING", cloud: "AWS ECS", region: "eu-west-1", updated: "Just now" },
  { id: "6", name: "notification-svc", repo: "github.com/org/notif-svc", status: "COMPLETED", cloud: "AWS ECS", region: "us-east-1", updated: "1 day ago" },
];

export default function Projects() {
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [projects] = useState(initialProjects);

  const filtered = projects.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.repo.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Projects</h2>
          <p className="mt-1 text-sm text-foreground/50">
            Manage your containerization and deployment projects
          </p>
        </div>
        <button
          onClick={() => setShowNew(!showNew)}
          className="btn-primary"
        >
          <Plus className="h-4 w-4" />
          New Project
        </button>
      </div>

      {/* New Project Form */}
      {showNew && (
        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Create New Project</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Project Name</label>
              <input className="input-field" placeholder="e.g. my-web-app" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Git Repository URL</label>
              <input className="input-field" placeholder="https://github.com/org/repo" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Cloud Provider</label>
              <select className="input-field">
                <option value="aws">AWS</option>
                <option value="gcp">Google Cloud</option>
                <option value="azure">Azure</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Region</label>
              <select className="input-field">
                <option value="us-east-1">US East (N. Virginia)</option>
                <option value="eu-west-1">EU West (Ireland)</option>
                <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button className="btn-primary">
              Create Project
            </button>
            <button onClick={() => setShowNew(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
        <input
          className="input-field pl-9"
          placeholder="Search projects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Empty state */}
      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-surface p-12 text-center">
          <GitBranch className="mb-3 h-10 w-10 text-foreground/20" />
          <p className="text-sm font-medium text-foreground/50">No projects found</p>
          <p className="mt-1 text-xs text-foreground/40">
            {search ? "Try a different search term" : "Create your first project to get started"}
          </p>
        </div>
      )}

      {/* Table */}
      {filtered.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-5 py-3 text-left text-xs font-semibold text-foreground/60">Project</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-foreground/60">Repository</th>
                <th className="hidden px-5 py-3 text-left text-xs font-semibold text-foreground/60 md:table-cell">Cloud</th>
                <th className="hidden px-5 py-3 text-left text-xs font-semibold text-foreground/60 md:table-cell">Region</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-foreground/60">Status</th>
                <th className="px-5 py-3 text-right text-xs font-semibold text-foreground/60">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((project) => (
                <tr key={project.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-5 py-3.5">
                    <p className="font-medium text-foreground">{project.name}</p>
                    <p className="text-xs text-foreground/40">Updated {project.updated}</p>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-foreground/70">{project.repo}</span>
                  </td>
                  <td className="hidden px-5 py-3.5 text-foreground/70 md:table-cell">{project.cloud}</td>
                  <td className="hidden px-5 py-3.5 text-foreground/70 md:table-cell">{project.region}</td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={project.status} size="sm" />
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/10"
                      aria-label={`View ${project.name} details`}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}