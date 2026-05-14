import { useEffect, useState } from "react";
import { GitCompare } from "lucide-react";
import { lifetwinApi } from "../api/lifetwinApi";
import { TwinComparison } from "../components/twin/TwinComparison";
import { Badge } from "../components/ui/Badge";
import { EmptyState } from "../components/ui/EmptyState";
import { LoadingState } from "../components/ui/LoadingState";
import { asRecord, pct } from "../utils/formatters";

export function TwinPage() {
  const [current, setCurrent] = useState<Record<string, unknown>>();
  const [ideal, setIdeal] = useState<Record<string, unknown>>();
  const [alignment, setAlignment] = useState(72);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const userId = localStorage.getItem("lifetwin_user_id");

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        const [currentData, idealData, dashboard] = await Promise.allSettled([
          lifetwinApi.getCurrentTwin(userId),
          lifetwinApi.getIdealTwin(userId),
          lifetwinApi.getDashboard(userId),
        ]);
        if (currentData.status === "fulfilled") {
          setCurrent(currentData.value);
          setAlignment(pct(currentData.value.twin_alignment_score, 72));
        }
        if (idealData.status === "fulfilled") setIdeal(idealData.value);
        if (dashboard.status === "fulfilled") {
          const status = asRecord(dashboard.value.current_status);
          setAlignment(pct(status.twin_alignment_score ?? dashboard.value.twin_alignment_score ?? dashboard.value.alignment_score, 72));
        }
      } catch {
        setError("Could not load twin data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [userId]);

  if (!userId) return <div className="page-wrap"><EmptyState title="No active twin" message="Launch the demo first to create a user twin." /></div>;
  if (loading) return <div className="page-wrap"><LoadingState label="Rendering current and ideal twins..." /></div>;

  const gapRecord = asRecord(current?.twin_gap);
  const gaps = Object.keys(gapRecord).length
    ? Object.entries(gapRecord).map(([key, value]) => {
        const row = asRecord(value);
        return `${key.replace(/_/g, " ")}: current ${String(row.current ?? "n/a")} vs target ${String(row.target ?? "n/a")}`;
      })
    : Array.isArray(asRecord(current).biggest_gaps) ? (asRecord(current).biggest_gaps as unknown[]) : [
    "Improve sleep consistency",
    "Increase daily walking",
    "Reduce lipid/metabolic risk",
    "Lower resting HR through recovery and activity",
  ];

  return (
    <div className="page-wrap space-y-5">
      <div>
        <Badge className="border-cyan-300/25 bg-cyan-300/10 text-cyan-100">Digital twin comparison</Badge>
        <h1 className="mt-4 text-4xl font-bold text-white">Current You vs Ideal Future Twin</h1>
        <p className="mt-3 max-w-3xl text-slate-300">
          LifeTwin models today’s signals against a durable healthspan target, then turns the gap into action.
        </p>
      </div>
      {error ? <p className="rounded-2xl border border-amber-300/25 bg-amber-300/10 p-4 text-sm text-amber-100">{error}</p> : null}
      <TwinComparison current={current} ideal={ideal} alignment={alignment} />
      <section className="glass-card">
        <div className="mb-5 flex items-center gap-3">
          <GitCompare className="h-5 w-5 text-amber-200" />
          <h2 className="text-lg font-semibold text-white">Biggest gaps to close</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {gaps.map((gap, index) => (
            <div key={index} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm font-medium text-slate-200">
              {String(gap)}
            </div>
          ))}
        </div>
      </section>
      <p className="medical-disclaimer">
        This is a preventive wellness insight, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
      </p>
    </div>
  );
}
