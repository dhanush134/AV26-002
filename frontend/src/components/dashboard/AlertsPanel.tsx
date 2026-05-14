import { AlertTriangle } from "lucide-react";
import { DashboardResponse } from "../../types/api";
import { asArray, asRecord, toText } from "../../utils/formatters";
import { Card } from "../ui/Card";
import { RiskBadge } from "../ui/RiskBadge";

export function AlertsPanel({ dashboard, alerts }: { dashboard?: DashboardResponse; alerts?: unknown[] }) {
  const items = asArray(alerts).length ? asArray(alerts) : asArray(dashboard?.alerts ?? dashboard?.recent_alerts);
  const fallback = [
    { severity: "moderate", title: "Sleep debt detected", message: "Three-day sleep average is below your target range." },
    { severity: "low", title: "Activity improving", message: "Walking trend is moving toward your ideal twin baseline." },
  ];
  const list = items.length ? items : fallback;

  return (
    <Card title="Recent Alerts">
      <div className="space-y-3">
        {list.slice(0, 5).map((item, index) => {
          const alert = asRecord(item);
          return (
            <div key={index} className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-1 h-5 w-5 text-amber-200" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-white">{toText(alert.title ?? alert.type, "Preventive alert")}</h3>
                    <RiskBadge level={alert.severity ?? alert.risk_level} />
                  </div>
                  <p className="mt-1 text-sm leading-6 text-slate-300">{toText(alert.message ?? alert.description, "Your twin detected a change worth watching.")}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
