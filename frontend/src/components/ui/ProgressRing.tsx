import { pct } from "../../utils/formatters";

interface ProgressRingProps {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
}

export function ProgressRing({ value, size = 148, stroke = 12, label = "aligned" }: ProgressRingProps) {
  const normalized = pct(value);
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (normalized / 100) * circumference;

  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="rgba(255,255,255,0.1)" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#ringGradient)"
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
        <defs>
          <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6ee7b7" />
            <stop offset="55%" stopColor="#67e8f9" />
            <stop offset="100%" stopColor="#60a5fa" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-bold text-white">{normalized}%</div>
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
      </div>
    </div>
  );
}
