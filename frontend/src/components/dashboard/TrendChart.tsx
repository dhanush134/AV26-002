import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DashboardResponse } from "../../types/api";
import { asArray, asRecord, toNumber } from "../../utils/formatters";
import { Card } from "../ui/Card";

const fallback = [
  { day: "Mon", heart_rate: 74, sleep_hours: 6.1, steps: 6100 },
  { day: "Tue", heart_rate: 72, sleep_hours: 6.6, steps: 7200 },
  { day: "Wed", heart_rate: 76, sleep_hours: 5.8, steps: 5200 },
  { day: "Thu", heart_rate: 70, sleep_hours: 7.1, steps: 8500 },
  { day: "Fri", heart_rate: 73, sleep_hours: 6.8, steps: 7600 },
  { day: "Sat", heart_rate: 69, sleep_hours: 7.4, steps: 9400 },
  { day: "Sun", heart_rate: 71, sleep_hours: 7.0, steps: 8800 },
];

export function TrendChart({ dashboard }: { dashboard: DashboardResponse }) {
  const trends = asRecord(dashboard.trends);
  const charts = asRecord(dashboard.charts);
  const hr = asArray<Record<string, unknown>>(charts.heart_rate_trend);
  const sleep = asArray<Record<string, unknown>>(charts.sleep_trend);
  const steps = asArray<Record<string, unknown>>(charts.steps_trend);
  const raw = asArray<Record<string, unknown>>(trends.daily ?? trends.vitals ?? dashboard.trends);
  const data = hr.length || sleep.length || steps.length
    ? Array.from({ length: Math.max(hr.length, sleep.length, steps.length) }).map((_, index) => {
        const stamp = String(hr[index]?.timestamp ?? sleep[index]?.timestamp ?? steps[index]?.timestamp ?? index + 1);
        return {
          day: stamp.includes("T") ? new Date(stamp).toLocaleDateString("en", { weekday: "short" }) : stamp,
          heart_rate: toNumber(hr[index]?.value, 72),
          sleep_hours: toNumber(sleep[index]?.value, 6.7),
          steps: Math.round(toNumber(steps[index]?.value, 7200) / 1000),
        };
      })
    : raw.length
    ? raw.map((row, index) => ({
        day: String(row.day ?? row.date ?? index + 1),
        heart_rate: toNumber(row.heart_rate ?? row.resting_hr, 72),
        sleep_hours: toNumber(row.sleep_hours, 6.7),
        steps: Math.round(toNumber(row.steps, 7200) / 1000),
      }))
    : fallback.map((row) => ({ ...row, steps: Math.round(row.steps / 1000) }));

  return (
    <Card title="Live Trends" className="min-h-[340px]">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="day" stroke="#94a3b8" tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ background: "#07101d", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 14 }}
              labelStyle={{ color: "#e2e8f0" }}
            />
            <Line type="monotone" dataKey="heart_rate" stroke="#fb7185" strokeWidth={3} dot={false} name="Heart rate" />
            <Line type="monotone" dataKey="sleep_hours" stroke="#a78bfa" strokeWidth={3} dot={false} name="Sleep hours" />
            <Line type="monotone" dataKey="steps" stroke="#34d399" strokeWidth={3} dot={false} name="Steps (k)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
