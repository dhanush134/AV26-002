import { Activity, Footprints, HeartPulse, Moon, Scale, Waves } from "lucide-react";
import { DashboardResponse } from "../../types/api";
import { asRecord, compactNumber, toNumber } from "../../utils/formatters";
import { StatCard } from "../ui/StatCard";

export function VitalCards({ dashboard }: { dashboard: DashboardResponse }) {
  const vitals = { ...asRecord(dashboard.latest_vitals), ...asRecord(dashboard.vitals) };
  const user = asRecord(dashboard.user);
  const status = asRecord(dashboard.current_status);

  const items = [
    { label: "Heart rate", value: Math.round(toNumber(vitals.heart_rate ?? vitals.resting_heart_rate ?? vitals.resting_hr, 72)), unit: "bpm", icon: <HeartPulse size={18} />, tone: "rose" as const },
    { label: "SpO2", value: Math.round(toNumber(vitals.spo2, 98)), unit: "%", icon: <Waves size={18} />, tone: "cyan" as const },
    { label: "Sleep", value: toNumber(vitals.sleep_hours, 6.6).toFixed(1), unit: "hrs", icon: <Moon size={18} />, tone: "violet" as const },
    { label: "Steps", value: compactNumber(vitals.steps ?? 7200), icon: <Footprints size={18} />, tone: "emerald" as const },
    { label: "BMI", value: toNumber(vitals.bmi ?? user.bmi, 26.1).toFixed(1), icon: <Scale size={18} />, tone: "amber" as const },
    { label: "Anomaly", value: Math.round(toNumber(vitals.anomaly_score ?? status.anomaly_score ?? dashboard.anomaly_score, 18)), unit: "/100", icon: <Activity size={18} />, tone: "cyan" as const },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {items.map((item) => (
        <StatCard key={item.label} {...item} />
      ))}
    </div>
  );
}
