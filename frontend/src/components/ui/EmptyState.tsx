import { Activity } from "lucide-react";
import { Button } from "./Button";

interface EmptyStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ title, message, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-dashed border-white/15 bg-white/[0.035] p-8 text-center">
      <Activity className="mx-auto mb-4 h-10 w-10 text-cyan-200" />
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm text-slate-300">{message}</p>
      {actionLabel && onAction ? (
        <Button onClick={onAction} className="mt-6">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
