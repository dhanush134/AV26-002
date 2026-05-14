import { CurrentTwinCard } from "./CurrentTwinCard";
import { IdealTwinCard } from "./IdealTwinCard";
import { TwinAlignment } from "./TwinAlignment";

interface TwinComparisonProps {
  current?: Record<string, unknown>;
  ideal?: Record<string, unknown>;
  alignment?: number;
}

export function TwinComparison({ current, ideal, alignment = 72 }: TwinComparisonProps) {
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_0.82fr_1fr]">
      <CurrentTwinCard twin={current} />
      <TwinAlignment value={alignment} />
      <IdealTwinCard twin={ideal} />
    </div>
  );
}
