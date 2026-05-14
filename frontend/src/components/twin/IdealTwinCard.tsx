import { Sparkles } from "lucide-react";
import { asRecord, toNumber } from "../../utils/formatters";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

const rows = [
  ["Target BMI", "target_bmi", "23.2"],
  ["Target Sleep", "target_sleep_hours", "7.6 hrs"],
  ["Target Steps", "target_steps", "10k"],
  ["Target Resting HR", "target_resting_hr", "62 bpm"],
  ["Target BP", "target_blood_pressure", "118/76"],
  ["Target LDL", "target_ldl", "95 mg/dL"],
];

export function IdealTwinCard({ twin }: { twin?: Record<string, unknown> }) {
  const data = asRecord(twin);
  const idealTwin = asRecord(data.ideal_twin);
  const targetBp = asRecord(idealTwin.target_bp);
  const targets: Record<string, unknown> = {
    target_bmi: idealTwin.target_bmi_range,
    target_blood_pressure: targetBp.systolic && targetBp.diastolic ? `${targetBp.systolic}/${targetBp.diastolic}` : undefined,
    ...asRecord(data.targets),
    ...idealTwin,
    ...data,
  };

  return (
    <Card
      title={
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-emerald-300/15 text-emerald-100">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Ideal Future Twin</h2>
            <p className="text-xs text-slate-400">Age-80 healthspan target</p>
          </div>
        </div>
      }
      action={<Badge className="border-emerald-300/30 bg-emerald-300/10 text-emerald-100">Optimized</Badge>}
    >
      <div className="space-y-3">
        {rows.map(([label, key, fallback]) => (
          <div key={key} className="flex items-center justify-between rounded-2xl bg-white/[0.04] px-4 py-3">
            <span className="text-sm text-slate-400">{label}</span>
            <span className="font-semibold text-white">
              {key === "target_steps" && typeof targets[key] === "number"
                ? `${(toNumber(targets[key]) / 1000).toFixed(1)}k`
                : String(targets[key] ?? fallback)}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
