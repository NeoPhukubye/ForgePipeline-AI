import { useEffect, useState } from "react";
import { Plus, Search, GitBranch, Rocket } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../lib/api";
import type { Project, Task } from "../lib/api";
import type { TaskStatus } from "../lib/types";

export default function Projects() {
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  // Form state
  const [formName, setFormName] = useState("");
  const [formRepo, setFormRepo] = useState("");
  const [formCloud, setFormCloud] = useState("aws-ecs");
  const [formRegion, setFormRegion] = useState("us-east-1");

  const load = async () => {
    try {
      const [p, t] = await Promise.all([api.listProjects(), api.listTasks()]);
      setProjects(p);
      setTasks(t);
    } catch { /* backend offline */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!formName || !formRepo) return;
    setCreating(true);
    try {
      await api.createProject({
        name: formName,
        source_repo_url: formRepo,
        deployment_target: formCloud,
        deployment_region: formRegion,
      });
      setFormName("");
      setFormRepo("");
      setShowNew(false);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to create project");
    }
    setCreating(false);
  };

  const handleDeploy = async (projectId: string) => {
    try {
      await api.triggerDeploy({ project_id: projectId, task_type: "DEPLOY" });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to trigger deploy");
    }
  };

  const getProjectStatus = (projectId: string): TaskStatus => {
    const task = tasks.find((t) => t.project_id === projectId);
    return (task?.status || "PENDING") as TaskStatus;
  };

  const getProjectUpdated = (project: Project): string => {
    const task = tasks.find((t) => t.project_id === project.id);
    if (task?.started_at) {
      const diff = Date.now() - new Date(task.started_at).getTime();
      if (diff < 60000) return "Just now";
      if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
      return new Date(task.started_at).toLocaleDateString();
    }
    return new Date(project.updated_at).toLocaleDateString();
  };

  const filtered = projects.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.source_repo_url.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">Projects</h2>
          <p className="mt-1 text-sm text-foreground/50">
            Manage your containerization and deployment projects
          </p>
        </div>
        <button onClick={() => setShowNew(!showNew)} className="btn-primary">
          <Plus className="h-4 w-4" />
          New Project
        </button>
      </div>

      {showNew && (
        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Create New Project</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Project Name</label>
              <input className="input-field" placeholder="e.g. my-web-app" value={formName} onChange={(e) => setFormName(e.target.value)} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Git Repository URL</label>
              <input className="input-field" placeholder="https://github.com/org/repo" value={formRepo} onChange={(e) => setFormRepo(e.target.value)} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Deployment Target</label>
              <select className="input-field" value={formCloud} onChange={(e) => setFormCloud(e.target.value)}>
                <option value="aws-ecs">AWS ECS</option>
                <option value="gcp-run">Google Cloud Run</option>
                <option value="azure-container-apps">Azure Container Apps</option>
                <option value="kubernetes">Kubernetes</option>
                <option value="aws-lambda">AWS Lambda</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground/70">Region</label>
              <select className="input-field" value={formRegion} onChange={(e) => setFormRegion(e.target.value)}>
                <option value="us-east-1">US East (N. Virginia)</option>
                <option value="us-west-2">US West (Oregon)</option>
                <option value="eu-west-1">EU West (Ireland)</option>
                <option value="eu-central-1">EU Central (Frankfurt)</option>
                <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button onClick={handleCreate} disabled={creating || !formName || !formRepo} className="btn-primary disabled:opacity-50">
              {creating ? "Creating..." : "Create Project"}
            </button>
            <button onClick={() => setShowNew(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
        <input
          className="input-field pl-9"
          placeholder="Search projects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-surface p-12 text-center">
          <GitBranch className="mb-3 h-10 w-10 text-foreground/20" />
          <p className="text-sm font-medium text-foreground/50">No projects found</p>
          <p className="mt-1 text-xs text-foreground/40">
            {search ? "Try a different search term" : "Create your first project to get started"}
          </p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-5 py-3 text-left text-xs font-semibold text-foreground/60">Project</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-foreground/60">Repository</th>
                <th className="hidden px-5 py-3 text-left text-xs font-semibold text-foreground/60 md:table-cell">Target</th>
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
                    <p className="text-xs text-foreground/40">Updated {getProjectUpdated(project)}</p>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-foreground/70">{project.source_repo_url}</span>
                  </td>
                  <td className="hidden px-5 py-3.5 text-foreground/70 md:table-cell">{project.deployment_target || "—"}</td>
                  <td className="hidden px-5 py-3.5 text-foreground/70 md:table-cell">{project.deployment_region || "—"}</td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={getProjectStatus(project.id)} size="sm" />
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={() => handleDeploy(project.id)}
                      className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/10"
                    >
                      <Rocket className="h-3.5 w-3.5" />
                      Deploy
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
