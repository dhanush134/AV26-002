import { useState } from "react";
import { Send } from "lucide-react";
import type { DailyCheckinPayload } from "../../types/api";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

const optionGroups = {
  sleep_quality: ["Poor", "Average", "Good"],
  exercise_done: ["None", "Walk", "Gym", "Cardio"],
  food_quality: ["Poor", "Average", "Clean"],
  stress_level: ["Low", "Medium", "High"],
};

const initial: DailyCheckinPayload = {
  sleep_quality: "Average",
  exercise_done: "Walk",
  food_quality: "Average",
  alcohol_used: false,
  smoking_done: false,
  stress_level: "Medium",
  steps_completed: 7200,
  sleep_hours: 6.5,
  notes: "",
};

interface DailyCheckinFormProps {
  onSubmit: (payload: DailyCheckinPayload) => Promise<void>;
  submitting: boolean;
}

export function DailyCheckinForm({ onSubmit, submitting }: DailyCheckinFormProps) {
  const [form, setForm] = useState(initial);

  const set = <K extends keyof DailyCheckinPayload>(key: K, value: DailyCheckinPayload[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  return (
    <Card title="Daily Twin Check-in">
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(form);
        }}
      >
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(optionGroups).map(([key, options]) => (
            <label key={key} className="block">
              <span className="mb-2 block text-sm font-medium text-slate-300">{key.replace(/_/g, " ")}</span>
              <div className="grid grid-cols-3 gap-2">
                {options.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => set(key as keyof DailyCheckinPayload, option as never)}
                    className={`rounded-xl border px-3 py-2 text-sm font-semibold transition ${
                      form[key as keyof DailyCheckinPayload] === option
                        ? "border-cyan-300/55 bg-cyan-300/15 text-white"
                        : "border-white/10 bg-white/[0.04] text-slate-300"
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </label>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label>
            <span className="mb-2 block text-sm font-medium text-slate-300">Steps completed</span>
            <input className="field" type="number" value={form.steps_completed} onChange={(event) => set("steps_completed", Number(event.target.value))} />
          </label>
          <label>
            <span className="mb-2 block text-sm font-medium text-slate-300">Sleep hours</span>
            <input className="field" type="number" step="0.1" value={form.sleep_hours} onChange={(event) => set("sleep_hours", Number(event.target.value))} />
          </label>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] p-4">
            <span className="text-sm font-medium text-white">Alcohol used</span>
            <input type="checkbox" checked={form.alcohol_used} onChange={(event) => set("alcohol_used", event.target.checked)} />
          </label>
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] p-4">
            <span className="text-sm font-medium text-white">Smoking done</span>
            <input type="checkbox" checked={form.smoking_done} onChange={(event) => set("smoking_done", event.target.checked)} />
          </label>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-300">Notes</span>
          <textarea
            className="field min-h-28 resize-y"
            placeholder="I slept late, skipped walking, and ate heavy dinner."
            value={form.notes}
            onChange={(event) => set("notes", event.target.value)}
          />
        </label>

        <Button type="submit" disabled={submitting}>
          <Send size={17} />
          {submitting ? "Adapting twin..." : "Submit Check-in"}
        </Button>
      </form>
    </Card>
  );
}
