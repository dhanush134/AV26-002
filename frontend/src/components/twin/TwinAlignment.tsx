import { ProgressRing } from "../ui/ProgressRing";

export function TwinAlignment({ value = 72 }: { value?: number }) {
  return (
    <div className="glass-card flex flex-col items-center justify-center text-center">
      <ProgressRing value={value} />
      <h2 className="mt-5 text-2xl font-bold text-white">You are {Math.round(value)}% aligned with your age-80 health twin.</h2>
      <p className="mt-3 max-w-sm text-sm leading-6 text-slate-300">
        The remaining gap is mostly lifestyle rhythm: sleep consistency, walking volume, recovery, and lipid-metabolic risk.
      </p>
    </div>
  );
}
