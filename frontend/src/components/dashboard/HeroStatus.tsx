import { motion } from "framer-motion";
import { ShieldCheck, Sparkles } from "lucide-react";
import { DashboardResponse } from "../../types/api";
import { asRecord, pct, toNumber, toText } from "../../utils/formatters";
import { RiskBadge } from "../ui/RiskBadge";
import { ProgressRing } from "../ui/ProgressRing";
import { Button } from "../ui/Button";

interface HeroStatusProps {
  dashboard: DashboardResponse;
  onReplay: () => void;
}

export function HeroStatus({ dashboard, onReplay }: HeroStatusProps) {
  const user = asRecord(dashboard.user);
  const status = asRecord(dashboard.current_status);
  const name = toText(user.full_name ?? user.name ?? dashboard.name, "Demo Patient");
  const alignment = pct(status.twin_alignment_score ?? dashboard.twin_alignment_score ?? dashboard.alignment_score, 72);
  const healthspan = toNumber(user.target_age ?? dashboard.healthspan_target_age, 82);
  const summary = toText(
    status.summary_message ?? dashboard.summary,
    "Your twin is stable today. The highest leverage move is tightening sleep consistency and walking volume.",
  );

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-white/[0.12] via-cyan-300/[0.08] to-emerald-300/[0.08] p-6 shadow-glow-blue backdrop-blur-2xl"
    >
      <div className="absolute right-10 top-8 h-40 w-40 rounded-full bg-cyan-300/10 blur-3xl" />
      <div className="relative grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
        <div>
          <div className="mb-5 flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1 text-xs font-semibold text-cyan-100">
              <Sparkles size={14} /> Live preventive twin
            </span>
            <RiskBadge level={status.overall_risk_level ?? dashboard.overall_risk_level ?? dashboard.risk_level} />
          </div>
          <h1 className="max-w-4xl text-4xl font-bold leading-tight text-white md:text-6xl">
            {name}'s health twin is {alignment}% aligned.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">{summary}</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Button onClick={onReplay}>
              <ShieldCheck size={18} /> Replay Health Scenario
            </Button>
            <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Healthspan target</p>
              <p className="text-xl font-semibold text-white">Age {healthspan}</p>
            </div>
          </div>
        </div>
        <div className="mx-auto">
          <ProgressRing value={alignment} size={176} label="twin match" />
        </div>
      </div>
    </motion.section>
  );
}
