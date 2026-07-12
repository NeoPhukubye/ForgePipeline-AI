import { Clock, GitCommit, Container, Rocket, AlertCircle } from "lucide-react";

interface Activity {
  id: string;
  type: "containerize" | "deploy" | "error" | "commit";
  project: string;
  message: string;
  timestamp: string;
}

const iconMap = {
  containerize: Container,
  deploy: Rocket,
  error: AlertCircle,
  commit: GitCommit,
};

const colorMap = {
  containerize: "text-primary",
  deploy: "text-accent",
  error: "text-destructive",
  commit: "text-foreground/60",
};

const bgMap = {
  containerize: "bg-primary/10",
  deploy: "bg-accent/10",
  error: "bg-destructive/10",
  commit: "bg-foreground/5",
};

interface ActivityFeedProps {
  activities: Activity[];
}

export default function ActivityFeed({ activities }: ActivityFeedProps) {
  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-surface p-10 text-center">
        <Clock className="mb-3 h-10 w-10 text-foreground/20" />
        <p className="text-sm font-medium text-foreground/50">No recent activity</p>
        <p className="mt-1 text-xs text-foreground/40">
          Activity from containerizations and deployments will show up here.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-surface">
      <div className="border-b border-border px-5 py-3">
        <h3 className="text-sm font-semibold text-foreground">Recent Activity</h3>
      </div>
      <div className="divide-y divide-border">
        {activities.map((activity) => {
          const Icon = iconMap[activity.type];
          return (
            <div key={activity.id} className="flex items-start gap-3 px-5 py-3">
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${bgMap[activity.type]}`}>
                <Icon className={`h-4 w-4 ${colorMap[activity.type]}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-foreground">
                  <span className="font-medium">{activity.project}</span>{" "}
                  {activity.message}
                </p>
                <p className="mt-0.5 text-xs text-foreground/40">{activity.timestamp}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}