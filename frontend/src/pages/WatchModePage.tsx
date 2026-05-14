import { useState } from "react";
import { Radio, Watch } from "lucide-react";
import { lifetwinApi } from "../api/lifetwinApi";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import type { WearableReadingPayload } from "../types/api";

export function WatchModePage() {
  const userId = localStorage.getItem("lifetwin_user_id");
  const [form, setForm] = useState<WearableReadingPayload>({ heart_rate: 76, spo2: 98, steps: 7400, active_minutes: 36, sleep_hours: 6.7 });
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");

  const update = <K extends keyof WearableReadingPayload>(key: K, value: WearableReadingPayload[K]) => setForm((current) => ({ ...current, [key]: value }));

  const send = async () => {
    if (!userId) return;
    setSending(true);
    setMessage("");
    try {
      await lifetwinApi.createWearableReading(userId, { ...form, captured_at: new Date().toISOString() });
      await lifetwinApi.calculateRisk(userId).catch(() => undefined);
      setMessage("Watch reading sent. Risk engine refresh requested.");
    } catch {
      setMessage("Wearable reading could not be sent. Confirm the backend endpoint is available.");
    } finally {
      setSending(false);
    }
  };

  if (!userId) return <div className="page-wrap"><EmptyState title="Demo mode needs a user" message="Launch the demo before sending watch readings." /></div>;

  return (
    <div className="page-wrap space-y-5">
      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <div className="flex items-center gap-4">
            <div className="grid h-16 w-16 place-items-center rounded-3xl bg-cyan-300/15 text-cyan-100">
              <Watch size={30} />
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.22em] text-slate-500">Samsung Watch / Wearable Input Layer</p>
              <h1 className="mt-2 text-3xl font-bold text-white">Wearable Mode</h1>
            </div>
          </div>
          <div className="mt-6 rounded-3xl border border-emerald-300/25 bg-emerald-300/10 p-5">
            <div className="flex items-center gap-3">
              <Radio className="h-5 w-5 text-emerald-200" />
              <p className="font-semibold text-emerald-100">Demo mode active</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Manual readings simulate the same signal path future integrations will use for Samsung Health, Apple Health,
              Fitbit, and Garmin.
            </p>
          </div>
        </Card>

        <Card title="Send Watch Reading">
          <div className="grid gap-4 md:grid-cols-2">
            {([
              ["heart_rate", "Heart rate"],
              ["spo2", "SpO2"],
              ["steps", "Steps"],
              ["active_minutes", "Active minutes"],
              ["sleep_hours", "Sleep hours"],
            ] as const).map(([key, label]) => (
              <label key={key}>
                <span className="mb-2 block text-sm font-medium text-slate-300">{label}</span>
                <input
                  className="field"
                  type="number"
                  step={key === "sleep_hours" ? "0.1" : "1"}
                  value={form[key]}
                  onChange={(event) => update(key, Number(event.target.value))}
                />
              </label>
            ))}
          </div>
          <Button className="mt-5" onClick={send} disabled={sending}>
            {sending ? "Sending..." : "Send Watch Reading"}
          </Button>
          {message ? <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-sm text-slate-200">{message}</p> : null}
        </Card>
      </div>
      <p className="medical-disclaimer">
        This is a preventive wellness insight, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
      </p>
    </div>
  );
}
