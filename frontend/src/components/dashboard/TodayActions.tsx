import { CheckCircle2, Circle } from "lucide-react";
import { DashboardResponse } from "../../types/api";
import { asArray, asRecord, toText } from "../../utils/formatters";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

export function TodayActions({ dashboard, routine }: { dashboard?: DashboardResponse; routine?: Record<string, unknown> }) {
  const routineActions = asArray(routine?.actions ?? routine?.items);
  const items = asArray(dashboard?.today_actions ?? dashboard?.recommended_actions);
  const fallback = [
    { title: "Walk 25 minutes after lunch", priority: "high", completed: false },
    { title: "Start sleep wind-down before 10:45 PM", priority: "medium", completed: false },
    { title: "Add protein and fiber to dinner", priority: "medium", completed: true },
  ];
  const list = routineActions.length ? routineActions : items.length ? items : fallback;

  return (
    <Card title="Today's Actions">
      <div className="space-y-3">
        {list.slice(0, 6).map((item, index) => {
          const action = asRecord(item);
          const done = Boolean(action.completed ?? action.done);
          return (
            <div key={index} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              {done ? <CheckCircle2 className="h-5 w-5 text-emerald-300" /> : <Circle className="h-5 w-5 text-slate-500" />}
              <div className="min-w-0 flex-1">
                <p className="font-medium text-white">{toText(action.title ?? action.action ?? action.recommended_action ?? action.name, "Preventive action")}</p>
                <p className="mt-1 text-xs text-slate-400">{toText(action.reason ?? action.description, "Selected by your adaptive routine.")}</p>
              </div>
              <Badge className="border-cyan-300/25 bg-cyan-300/10 text-cyan-100">{toText(action.priority, "medium")}</Badge>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
