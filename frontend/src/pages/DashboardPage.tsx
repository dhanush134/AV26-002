import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { lifetwinApi } from "../api/lifetwinApi";
import { AlertsPanel } from "../components/dashboard/AlertsPanel";
import { HeroStatus } from "../components/dashboard/HeroStatus";
import { RiskBreakdownChart } from "../components/dashboard/RiskBreakdownChart";
import { TodayActions } from "../components/dashboard/TodayActions";
import { TrendChart } from "../components/dashboard/TrendChart";
import { VitalCards } from "../components/dashboard/VitalCards";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { LoadingState } from "../components/ui/LoadingState";
import type { DashboardResponse } from "../types/api";

export function DashboardPage() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [alerts, setAlerts] = useState<unknown[]>([]);
  const [routine, setRoutine] = useState<Record<string, unknown> | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const userId = localStorage.getItem("lifetwin_user_id");

  const load = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [dashboardData, alertData, routineData] = await Promise.allSettled([
        lifetwinApi.getDashboard(userId),
        lifetwinApi.getAlerts(userId),
        lifetwinApi.getDailyRoutine(userId),
      ]);
      if (dashboardData.status === "fulfilled") setDashboard(dashboardData.value);
      else throw dashboardData.reason;
      if (alertData.status === "fulfilled") setAlerts(alertData.value);
      else setAlerts(Array.isArray(dashboardData.value.recent_alerts) ? dashboardData.value.recent_alerts : []);
      if (routineData.status === "fulfilled") setRoutine(routineData.value);
    } catch {
      setError("LifeTwin could not load the dashboard. Check the backend and retry.");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const createDemo = async () => {
    const demo = await lifetwinApi.runFullDemo();
    localStorage.setItem("lifetwin_user_id", String(demo.user_id ?? demo.id ?? ""));
    window.location.reload();
  };

  if (!userId) {
    return (
      <div className="page-wrap">
        <EmptyState title="Create a demo twin" message="Launch the backend demo seed first, then the dashboard will stream the generated user state." actionLabel="Launch Demo" onAction={createDemo} />
      </div>
    );
  }

  if (loading) return <div className="page-wrap"><LoadingState /></div>;

  if (error || !dashboard) {
    return (
      <div className="page-wrap">
        <EmptyState title="Backend unavailable" message={error || "No dashboard data was returned."} actionLabel="Retry" onAction={load} />
      </div>
    );
  }

  return (
    <div className="page-wrap space-y-5">
      <HeroStatus dashboard={dashboard} onReplay={() => navigate("/simulation")} />
      <VitalCards dashboard={dashboard} />
      <div className="grid gap-5 xl:grid-cols-2">
        <RiskBreakdownChart dashboard={dashboard} />
        <TrendChart dashboard={dashboard} />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1fr_0.95fr]">
        <TopRiskFactors dashboard={dashboard} />
        <TodayActions dashboard={dashboard} routine={routine} />
      </div>
      <AlertsPanel dashboard={dashboard} alerts={alerts} />
      <p className="medical-disclaimer">
        This is a preventive wellness insight, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
      </p>
      <Button variant="secondary" onClick={load}>Refresh Dashboard</Button>
    </div>
  );
}

function TopRiskFactors({ dashboard }: { dashboard: DashboardResponse }) {
  const items = Array.isArray(dashboard.top_risk_factors) && dashboard.top_risk_factors.length
    ? dashboard.top_risk_factors
    : [
        { category: "Sleep", factor: "Inconsistent sleep window", severity: "moderate", suggested_action: "Move bedtime 30 minutes earlier." },
        { category: "Activity", factor: "Low post-meal walking", severity: "moderate", suggested_action: "Add a 15-minute walk after lunch." },
        { category: "Metabolic", factor: "LDL and BMI drift", severity: "high", suggested_action: "Prioritize fiber, steps, and lab follow-up." },
      ];

  return (
    <section className="glass-card">
      <h2 className="mb-5 text-lg font-semibold text-white">Top Risk Factors</h2>
      <div className="space-y-3">
        {items.slice(0, 5).map((item, index) => {
          const row = typeof item === "object" && item ? (item as Record<string, unknown>) : {};
          return (
            <div key={index} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-white">{String(row.factor ?? "Risk factor")}</p>
                <span className="rounded-full border border-amber-300/25 bg-amber-300/10 px-2.5 py-1 text-xs font-semibold text-amber-100">
                  {String(row.severity ?? "moderate")}
                </span>
              </div>
              <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{String(row.category ?? "Lifestyle")}</p>
              <p className="mt-3 text-sm leading-6 text-slate-300">{String(row.suggested_action ?? row.action ?? "Improve the linked preventive habit.")}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
