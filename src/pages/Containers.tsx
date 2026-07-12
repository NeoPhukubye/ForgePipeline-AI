import { Container, Search, ExternalLink, Tag } from "lucide-react";
import { useState } from "react";
import StatusBadge from "../components/StatusBadge";
import type { TaskStatus } from "../lib/types";

interface ContainerItem {
  id: string;
  name: string;
  image: string;
  tag: string;
  project: string;
  size: string;
  status: TaskStatus;
  pushed: string;
}

const initialContainers: ContainerItem[] = [
  { id: "1", name: "web-app", image: "987654321.dkr.ecr.us-east-1.amazonaws.com/web-app", tag: "latest", project: "web-app-staging", size: "142 MB", status: "COMPLETED", pushed: "2 min ago" },
  { id: "2", name: "api-gateway", image: "987654321.dkr.ecr.us-east-1.amazonaws.com/api-gateway", tag: "v2.1.0", project: "api-gateway", size: "89 MB", status: "RUNNING", pushed: "15 min ago" },
  { id: "3", name: "user-service", image: "987654321.dkr.ecr.us-east-1.amazonaws.com/user-svc", tag: "v1.8.3", project: "user-service", size: "204 MB", status: "COMPLETED", pushed: "3 hours ago" },
  { id: "4", name: "payment-worker", image: "987654321.dkr.ecr.us-east-1.amazonaws.com/payment-worker", tag: "v2.0.0", project: "payment-worker", size: "167 MB", status: "PENDING", pushed: "Just now" },
];

export default function Containers() {
  const [search, setSearch] = useState("");

  const filtered = initialContainers.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.image.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-foreground">Container Images</h2>
        <p className="mt-1 text-sm text-foreground/50">
          Docker images built and stored in your container registry
        </p>
      </div>

      {/* Search */}
      <div className="relative sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
        <input
          className="input-field pl-9"
          placeholder="Search containers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Empty state */}
      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-surface p-12 text-center">
          <Container className="mb-3 h-10 w-10 text-foreground/20" />
          <p className="text-sm font-medium text-foreground/50">No containers found</p>
          <p className="mt-1 text-xs text-foreground/40">
            {search ? "Try a different search term" : "Container images will appear here after builds complete"}
          </p>
        </div>
      )}

      {/* Container cards */}
      {filtered.length > 0 && (
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
                    <p className="text-xs text-foreground/40">{container.project}</p>
                  </div>
                </div>
                <StatusBadge status={container.status} size="sm" />
              </div>
              <div className="mt-3 space-y-1.5">
                <div className="flex items-center gap-2 text-xs text-foreground/60">
                  <Tag className="h-3 w-3 shrink-0" />
                  <span className="truncate">{container.image}:{container.tag}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-foreground/40">{container.size}</span>
                  <span className="text-foreground/40">Pushed {container.pushed}</span>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <button className="btn-secondary px-3 py-1.5 text-xs">
                  <ExternalLink className="h-3 w-3" />
                  View in ECR
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}