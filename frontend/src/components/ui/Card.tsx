import type { PropsWithChildren, ReactNode } from "react";

interface CardProps extends PropsWithChildren {
  className?: string;
  title?: ReactNode;
  action?: ReactNode;
}

export function Card({ children, className = "", title, action }: CardProps) {
  return (
    <section className={`glass-card ${className}`}>
      {(title || action) && (
        <div className="mb-5 flex items-start justify-between gap-4">
          {typeof title === "string" ? <h2 className="text-lg font-semibold text-white">{title}</h2> : title}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
