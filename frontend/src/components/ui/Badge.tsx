import type { PropsWithChildren } from "react";

interface BadgeProps extends PropsWithChildren {
  className?: string;
}

export function Badge({ children, className = "" }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>
      {children}
    </span>
  );
}
