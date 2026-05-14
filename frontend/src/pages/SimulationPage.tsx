import { useState } from "react";
import { Zap } from "lucide-react";
import { lifetwinApi } from "../api/lifetwinApi";
import { AlertsPanel } from "../components/dashboard/AlertsPanel";
import { RiskBreakdownChart } from "../components/dashboard/RiskBreakdownChart";
import { VitalCards } from "../components/dashboard/VitalCards";
import { ScenarioSelector } from "../components/simulation/ScenarioSelector";
import { SimulationConsole } from "../components/simulation/SimulationConsole";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { RiskBadge } from "../components/ui/RiskBadge";
import type { DashboardResponse } from "../types/api";
import { asRecord, toNumber } from "../utils/formatters";

export function SimulationPage() {
  const [selected, setSelected] = useState("cardiac_strain");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");
  const userId = localStorage.getItem("lifetwin_user_id");

  const run = async () => {
    if (!userId) return;
    setRunning(true);
    setError("");
    try {
      const replay = await lifetwinApi.replayScenario(userId, selected, 30);
      setResult(replay);
    } catch {
      setError("Scenario replay failed. Confirm the backend simulation endpoint is available.");
    } finally {
      window.setTimeout(() => setRunning(false), 850);
    }
  };

  if (!userId) return <div className="page-wrap"><EmptyState title="No demo user" message="Launch the demo before replaying health scenarios." /></div>;

  return (
    <div className="page-wrap space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-white">Scenario Replay</h1>
          <p className="mt-3 max-w-3xl text-slate-300">
            Inject a wearable/lifestyle signal pattern and watch LifeTwin update risk, alerts, and the preventive plan.
          </p>
        </div>
        <Button onClick={run} disabled={running}>
          <Zap size={18} /> {running ? "Running..." : "Run Scenario"}
        </Button>
      </div>

      {error ? <p className="rounded-2xl border border-rose-400/25 bg-rose-500/10 p-4 text-sm text-rose-100">{error}</p> : null}

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <ScenarioSelector selected={selected} onSelect={setSelected} />
        <SimulationConsole running={running} />
      </div>

      {result ? (
        <div className="space-y-5">
          <Card title="Simulation Result">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl bg-white/[0.04] p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">New risk level</p>
                <div className="mt-3"><RiskBadge level={asRecord(result.current_status).overall_risk_level ?? result.overall_risk_level ?? result.risk_level} /></div>
              </div>
              <div className="rounded-2xl bg-white/[0.04] p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Anomaly score</p>
                <p className="mt-2 text-3xl font-bold text-white">{toNumber(asRecord(result.vitals).anomaly_score ?? asRecord(result.current_status).anomaly_score ?? result.anomaly_score, 31)}</p>
              </div>
              <div className="rounded-2xl bg-white/[0.04] p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Alerts created</p>
                <p className="mt-2 text-3xl font-bold text-white">{Array.isArray(result.alerts) ? result.alerts.length : Array.isArray(result.recent_alerts) ? result.recent_alerts.length : 1}</p>
              </div>
            </div>
          </Card>
          <VitalCards dashboard={result} />
          <div className="grid gap-5 xl:grid-cols-2">
            <RiskBreakdownChart dashboard={result} />
            <AlertsPanel dashboard={result} />
          </div>
        </div>
      ) : null}

      <p className="medical-disclaimer">
        This is a preventive wellness insight, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
      </p>
    </div>
  );
}
