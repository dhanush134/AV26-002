import { HeartPulse } from "lucide-react";
import { asRecord, toNumber } from "../../utils/formatters";
import { Card } from "../ui/Card";
import { RiskBadge } from "../ui/RiskBadge";

const rows = [
  ["BMI", "bmi", "26.1"],
  ["Sleep", "sleep_hours", "6.4 hrs"],
  ["Steps", "steps", "7.2k"],
  ["Resting HR", "resting_hr", "72 bpm"],
  ["Blood Pressure", "blood_pressure", "128/84"],
  ["LDL", "ldl", "132 mg/dL"],
];

export function CurrentTwinCard({ twin }: { twin?: Record<string, unknown> }) {
  const data = asRecord(twin);
  const currentTwin = asRecord(data.current_twin);
  const vitals = {
    ...asRecord(currentTwin.profile),
    ...asRecord(currentTwin.latest_wearable),
    ...asRecord(currentTwin.latest_labs),
    ...asRecord(data.vitals),
    ...data,
  };

  return (
    <Card
      title={
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-rose-400/15 text-rose-100">
            <HeartPulse size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Current You</h2>
            <p className="text-xs text-slate-400">Today’s physiological twin</p>
          </div>
        </div>
      }
      action={<RiskBadge level={data.risk_state ?? data.risk_level ?? "moderate"} />}
    >
      <div className="space-y-3">
        {rows.map(([label, key, fallback]) => (
          <div key={key} className="flex items-center justify-between rounded-2xl bg-white/[0.04] px-4 py-3">
            <span className="text-sm text-slate-400">{label}</span>
            <span className="font-semibold text-white">
              {key === "blood_pressure"
                ? `${vitals.bp_systolic ?? "128"}/${vitals.bp_diastolic ?? "84"}`
                : key === "resting_hr"
                  ? `${vitals.resting_hr ?? vitals.resting_heart_rate ?? "72"} bpm`
                  : key === "steps" && typeof vitals[key] === "number"
                    ? `${(toNumber(vitals[key]) / 1000).toFixed(1)}k`
                    : String(vitals[key] ?? fallback)}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
