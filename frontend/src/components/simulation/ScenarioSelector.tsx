import { Card } from "../ui/Card";
import { scenarios } from "../../utils/scenarios";

interface ScenarioSelectorProps {
  selected: string;
  onSelect: (scenario: string) => void;
}

export function ScenarioSelector({ selected, onSelect }: ScenarioSelectorProps) {
  return (
    <Card title="Scenario Replay">
      <div className="grid gap-3">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => onSelect(scenario.id)}
            className={`rounded-2xl border p-4 text-left transition ${
              selected === scenario.id ? "border-cyan-300/55 bg-cyan-300/12" : "border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 text-cyan-100">
                <scenario.icon size={18} />
              </div>
              <div>
                <p className="font-semibold text-white">{scenario.label}</p>
                <p className="mt-1 text-sm leading-6 text-slate-300">{scenario.description}</p>
                <p className="mt-2 text-xs font-medium text-emerald-200">{scenario.notice}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
}
