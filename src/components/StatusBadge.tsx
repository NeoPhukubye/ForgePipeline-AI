import type { TaskStatus } from "../lib/types";

interface StatusBadgeProps {
  status: TaskStatus;
  size?: "sm" | "md";
}

const labels: Record<TaskStatus, string> = {
  PENDING: "Pending",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
};

const statusConfig: Record<TaskStatus, { dotClass: string; bgClass: string; textClass: string }> = {
  PENDING: {
    dotClass: "bg-[oklch(0.6_0.03_250)]",
    bgClass: "bg-[oklch(0.6_0.03_250)]/10",
    textClass: "text-[oklch(0.6_0.03_250)]",
  },
  RUNNING: {
    dotClass: "bg-[oklch(0.72_0.15_220)]",
    bgClass: "bg-[oklch(0.72_0.15_220)]/10",
    textClass: "text-[oklch(0.72_0.15_220)]",
  },
  COMPLETED: {
    dotClass: "bg-accent",
    bgClass: "bg-accent/10",
    textClass: "text-accent",
  },
  FAILED: {
    dotClass: "bg-destructive",
    bgClass: "bg-destructive/10",
    textClass: "text-destructive",
  },
};

export default function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const config = statusConfig[status];
  const dotSize = size === "sm" ? "w-1.5 h-1.5" : "w-2 h-2";
  const padding = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-0.5 text-xs";
  const animate = status === "RUNNING" ? "animate-pulse" : "";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${padding} ${config.bgClass} ${config.textClass}`}
    >
      <span className={`${dotSize} rounded-full ${config.dotClass} ${animate}`} />
      {labels[status]}
    </span>
  );
}