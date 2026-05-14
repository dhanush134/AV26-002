import { useState } from "react";
import { lifetwinApi } from "../api/lifetwinApi";
import { AdjustmentResult } from "../components/daily/AdjustmentResult";
import { DailyCheckinForm } from "../components/daily/DailyCheckinForm";
import { EmptyState } from "../components/ui/EmptyState";
import type { DailyCheckinPayload } from "../types/api";

export function DailyCheckinPage() {
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<Record<string, unknown>>();
  const [error, setError] = useState("");
  const userId = localStorage.getItem("lifetwin_user_id");

  const submit = async (payload: DailyCheckinPayload) => {
    if (!userId) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await lifetwinApi.submitDailyCheckin(userId, payload);
      setResult(response);
    } catch {
      setError("Daily check-in could not be submitted. Please retry after confirming the backend is online.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!userId) return <div className="page-wrap"><EmptyState title="No active twin" message="Launch the demo before submitting a daily check-in." /></div>;

  return (
    <div className="page-wrap space-y-5">
      <div>
        <h1 className="text-4xl font-bold text-white">Daily Check-in</h1>
        <p className="mt-3 max-w-2xl text-slate-300">A quick daily reflection that lets the AI twin adapt tomorrow’s prevention plan.</p>
      </div>
      {error ? <p className="rounded-2xl border border-rose-400/25 bg-rose-500/10 p-4 text-sm text-rose-100">{error}</p> : null}
      <div className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
        <DailyCheckinForm onSubmit={submit} submitting={submitting} />
        <AdjustmentResult result={result} />
      </div>
      <p className="medical-disclaimer">
        This is a preventive wellness insight, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
      </p>
    </div>
  );
}
