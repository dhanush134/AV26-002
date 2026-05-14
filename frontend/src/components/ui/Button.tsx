import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, PropsWithChildren {
  variant?: ButtonVariant;
}

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-emerald-300 via-cyan-300 to-blue-400 text-slate-950 shadow-glow hover:brightness-110",
  secondary: "border border-white/15 bg-white/10 text-white hover:bg-white/15",
  ghost: "text-slate-200 hover:bg-white/10",
  danger: "border border-rose-400/35 bg-rose-500/15 text-rose-100 hover:bg-rose-500/25",
};

export function Button({ children, className = "", variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
