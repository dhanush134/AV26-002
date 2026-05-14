import type { ReactNode } from "react";
import { ArrowUpRight } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: ReactNode;
  tone?: "emerald" | "cyan" | "amber" | "rose" | "violet";
}

const tones = {
  emerald: "from-emerald-300/20 to-emerald-500/5 text-emerald-200",
  cyan: "from-cyan-300/20 to-cyan-500/5 text-cyan-200",
  amber: "from-amber-300/20 to-amber-500/5 text-amber-100",
  rose: "from-rose-300/20 to-rose-500/5 text-rose-100",
  violet: "from-violet-300/20 to-blue-500/5 text-violet-100",
};

export function StatCard({ label, value, unit, icon, tone = "cyan" }: StatCardProps) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-gradient-to-br ${tones[tone]} p-4 shadow-glow-blue`}>
      <div className="mb-4 flex items-center justify-between">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/10">{icon ?? <ArrowUpRight size={18} />}</div>
        <ArrowUpRight size={16} className="opacity-70" />
      </div>
      <p className="text-xs uppercase tracking-[0.22em] text-slate-400">{label}</p>
      <div className="mt-2 flex items-end gap-1">
        <span className="text-2xl font-semibold text-white">{value}</span>
        {unit ? <span className="pb-1 text-xs text-slate-400">{unit}</span> : null}
      </div>
    </div>
  );
}
