import { ArrowRight } from "lucide-react";
import { asArray, asRecord, pct, toNumber, toText } from "../../utils/formatters";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

export function AdjustmentResult({ result }: { result?: Record<string, unknown> }) {
  if (!result) return null;
  const data = asRecord(result);
  const previous = pct(data.previous_alignment ?? data.previous_alignment_score, 72);
  const next = pct(data.new_alignment ?? data.new_alignment_score ?? data.alignment_score, previous + 2);
  const missed = asArray(data.missed_items);
  const adjustments = asArray(data.tomorrow_adjustments ?? data.adjustments);

  return (
    <Card title="AI Twin Adaptation">
      <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-center">
        <div className="rounded-2xl bg-white/[0.04] p-4 text-center">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Previous</p>
          <p className="mt-2 text-4xl font-bold text-white">{previous}%</p>
        </div>
        <ArrowRight className="mx-auto h-6 w-6 text-cyan-200" />
        <div className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4 text-center">
          <p className="text-xs uppercase tracking-[0.22em] text-emerald-200">New alignment</p>
          <p className="mt-2 text-4xl font-bold text-white">{next}%</p>
          <Badge className="mt-2 border-emerald-300/30 bg-emerald-300/10 text-emerald-100">
            {toNumber(next - previous, 0) >= 0 ? "+" : ""}
            {next - previous} delta
          </Badge>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="font-semibold text-white">Missed items</h3>
          <div className="mt-3 space-y-2">
            {(missed.length ? missed : ["Sleep wind-down", "Walking target"]).map((item, index) => (
              <p key={index} className="rounded-xl bg-white/[0.04] px-3 py-2 text-sm text-slate-300">
                {toText(item, "Routine item")}
              </p>
            ))}
          </div>
        </div>
        <div>
          <h3 className="font-semibold text-white">Tomorrow adjustments</h3>
          <div className="mt-3 space-y-2">
            {(adjustments.length ? adjustments : ["Move walk earlier", "Simplify dinner target"]).map((item, index) => (
              <p key={index} className="rounded-xl bg-white/[0.04] px-3 py-2 text-sm text-slate-300">
                {toText(asRecord(item).recommended_action ?? asRecord(item).action ?? item, "Plan adjustment")}
              </p>
            ))}
          </div>
        </div>
      </div>
      <p className="mt-5 text-sm leading-6 text-emerald-100">
        {toText(data.encouraging_message ?? data.message, "Your twin adjusted the plan. Small recoveries today protect tomorrow's trajectory.")}
      </p>
    </Card>
  );
}
