import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DashboardResponse } from "../../types/api";
import { asArray, asRecord, titleCase, toNumber } from "../../utils/formatters";
import { Card } from "../ui/Card";

export function RiskBreakdownChart({ dashboard }: { dashboard: DashboardResponse }) {
  const risks = asRecord(dashboard.risk_breakdown);
  const charts = asRecord(dashboard.charts);
  const chartBreakdown = asArray<Record<string, unknown>>(charts.risk_breakdown);
  const riskScores = asRecord(dashboard.risk_scores);
  const fallback = { cardio: 42, metabolic: 55, sleep: 63, activity: 36, lifestyle: 48 };
  const source = Object.keys(risks).length ? risks : Object.keys(riskScores).length ? riskScores : fallback;
  const data = chartBreakdown.length
    ? chartBreakdown.map((item) => ({
        name: titleCase(String(item.label ?? "Risk")),
        risk: Math.round(toNumber(item.value, 0)),
      }))
    : Object.entries(source).map(([name, value]) => ({
    name: titleCase(name.replace(/_score$/, "")),
    risk: Math.round(toNumber(value, 0)),
  }));

  return (
    <Card title="Risk Breakdown" className="min-h-[340px]">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey="name" stroke="#94a3b8" tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.05)" }}
              contentStyle={{ background: "#07101d", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 14 }}
            />
            <Bar dataKey="risk" radius={[10, 10, 4, 4]} fill="url(#riskGradient)" />
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#67e8f9" />
                <stop offset="100%" stopColor="#34d399" />
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
