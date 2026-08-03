import { useEffect, useState } from "react";
import { Container, Search, Tag } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../lib/api";
import type { ContainerImage, Project } from "../lib/api";

export default function Containers() {
  const [search, setSearch] = useState("");
  const [containers, setContainers] = useState<ContainerImage[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [c, p] = await Promise.all([api.listContainers(), api.listProjects()]);
        setContainers(c);
        setProjects(p);
      } catch { /* offline */ }
      setLoading(false);
    };
    load();
  }, []);

  const getProjectName = (id: string) => projects.find((p) => p.id === id)?.name || "Unknown";

  const formatSize = (bytes: number | null) => {
    if (!bytes) return "—";
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
  };

  const formatTime = (time: string | null) => {
    if (!time) return "—";
    const diff = Date.now() - new Date(time).getTime();
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return new Date(time).toLocaleDateString();
  };

  const filtered = containers.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.image_uri.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Container Images</h2>
        <p className="mt-1 text-sm text-foreground/50">
          Docker images built and stored in your container registry
        </p>
      </div>

      <div className="relative sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
        <input
          className="input-field pl-9"
          placeholder="Search containers..."
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
          <Container className="mb-3 h-10 w-10 text-foreground/20" />
          <p className="text-sm font-medium text-foreground/50">No containers found</p>
          <p className="mt-1 text-xs text-foreground/40">
            {search ? "Try a different search term" : "Container images will appear here after builds complete"}
          </p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {filtered.map((container) => (
            <div key={container.id} className="card-hover rounded-xl border border-border bg-surface p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Container className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{container.name}</p>
                    <p className="text-xs text-foreground/40">{getProjectName(container.project_id)}</p>
                  </div>
                </div>
                <StatusBadge status="COMPLETED" size="sm" />
              </div>
              <div className="mt-3 space-y-1.5">
                <div className="flex items-center gap-2 text-xs text-foreground/60">
                  <Tag className="h-3 w-3 shrink-0" />
                  <span className="truncate">{container.image_uri}:{container.tag}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-foreground/40">{formatSize(container.size_bytes)}</span>
                  <span className="text-foreground/40">Pushed {formatTime(container.pushed_at)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
