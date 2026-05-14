import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { Activity, Circle, Dna, Dumbbell, HeartPulse, Moon, Share2, Sparkles, Sun, TestTube2, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

const COLORS = {
  bg: "#060810",
  surface: "#0D1117",
  card: "#111827",
  border: "#1F2937",
  accent: "#00D4AA",
  accentDim: "#00D4AA22",
  accentMid: "#00D4AA55",
  gold: "#F5B942",
  goldDim: "#F5B94222",
  red: "#FF4757",
  redDim: "#FF475722",
  blue: "#3B82F6",
  purple: "#8B5CF6",
  textPrimary: "#F9FAFB",
  textSecondary: "#9CA3AF",
  textMuted: "#4B5563",
};

const TABS = ["routine", "biomarkers", "nutrition", "twin"] as const;

type Tab = (typeof TABS)[number];
type BiomarkerKey =
  | "ldl"
  | "hdl"
  | "triglycerides"
  | "alt"
  | "creatinine"
  | "vitaminD"
  | "b12"
  | "hba1c"
  | "systolic"
  | "diastolic"
  | "sleepHrs"
  | "steps";

type Biomarkers = Record<BiomarkerKey, number>;

interface RoutineItem {
  time: string;
  activity: string;
  duration: string;
  impact: "High" | "Med" | "Low";
  done: boolean;
}

const appCss = `
@keyframes pulse-ring {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.4); }
  70% { transform: scale(1); box-shadow: 0 0 0 20px rgba(0, 212, 170, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 212, 170, 0); }
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@keyframes glow {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}
@keyframes scan {
  0% { top: 0%; }
  100% { top: 100%; }
}
@keyframes countUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes orbit {
  from { transform: rotate(0deg) translateX(80px) rotate(0deg); }
  to { transform: rotate(360deg) translateX(80px) rotate(-360deg); }
}
.lt-shell { min-height: 100vh; background: #060810; color: #F9FAFB; font-family: "DM Sans", Inter, system-ui, sans-serif; }
.lt-dashboard { padding-bottom: 78px; }
.lt-topbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 20px 32px; border-bottom: 1px solid #1F2937; background: rgba(6, 8, 16, 0.92); backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 50; }
.lt-brand { display: flex; align-items: center; gap: 12px; min-width: 210px; }
.lt-tabs { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.lt-user-pill { display: flex; align-items: center; justify-content: center; width: 52px; height: 52px; background: linear-gradient(135deg, rgba(139,92,246,0.95), rgba(59,130,246,0.95) 52%, rgba(45,212,191,0.9)); border: 2px solid rgba(255,255,255,0.14); border-radius: 999px; color: #F9FAFB; font-size: 15px; font-weight: 900; white-space: nowrap; cursor: pointer; box-shadow: 0 10px 30px rgba(59,130,246,0.25); transition: transform 0.2s ease, box-shadow 0.2s ease; }
.lt-user-pill:hover { transform: translateY(-1px) scale(1.02); box-shadow: 0 14px 36px rgba(45,212,191,0.24); }
.lt-page { padding: 40px 32px; max-width: 1120px; margin: 0 auto; }
.lt-grid-two { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 24px; }
.lt-grid-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.lt-grid-half { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.lt-nutrition { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.lt-bottom { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(13, 17, 23, 0.94); border-top: 1px solid #1F2937; padding: 12px 32px; display: flex; align-items: center; justify-content: space-between; gap: 16px; backdrop-filter: blur(20px); z-index: 60; }
@media (max-width: 920px) {
  .lt-topbar { align-items: flex-start; flex-direction: column; padding: 18px; }
  .lt-tabs { justify-content: flex-start; width: 100%; overflow-x: auto; flex-wrap: nowrap; }
  .lt-user-pill { display: none; }
  .lt-page { padding: 28px 18px 94px; }
  .lt-grid-two, .lt-nutrition, .lt-grid-cards, .lt-grid-half { grid-template-columns: 1fr; }
  .lt-bottom { align-items: flex-start; flex-direction: column; padding: 12px 18px; }
}
`;

const cardStyle: CSSProperties = {
  background: COLORS.card,
  border: `1px solid ${COLORS.border}`,
  borderRadius: 16,
};

export function TwinPage() {
  const navigate = useNavigate();
  const [age] = useState(34);
  const [targetAge] = useState(65);
  const [activeTab, setActiveTab] = useState<Tab>("twin");
  const [biomarkers, setBiomarkers] = useState<Biomarkers>({
    ldl: 128,
    hdl: 48,
    triglycerides: 160,
    alt: 32,
    creatinine: 1.1,
    vitaminD: 22,
    b12: 310,
    hba1c: 5.4,
    systolic: 128,
    diastolic: 82,
    sleepHrs: 6.2,
    steps: 4800,
  });
  const [routine, setRoutine] = useState<RoutineItem[]>([
    { time: "6:00 AM", activity: "10-min sunlight walk", duration: "10 min", impact: "High", done: true },
    { time: "6:30 AM", activity: "Cold shower + breathwork", duration: "15 min", impact: "Med", done: true },
    { time: "7:00 AM", activity: "High-protein breakfast (30g)", duration: "20 min", impact: "High", done: false },
    { time: "8:30 AM", activity: "Vitamin D3 + K2 + Omega-3", duration: "1 min", impact: "High", done: false },
    { time: "12:30 PM", activity: "Mediterranean lunch, no sugar", duration: "30 min", impact: "High", done: false },
    { time: "5:30 PM", activity: "Zone 2 cardio or strength", duration: "40 min", impact: "High", done: false },
    { time: "8:00 PM", activity: "Last meal (16:8 IF window)", duration: "30 min", impact: "Med", done: false },
    { time: "9:30 PM", activity: "Blue-light off, magnesium", duration: "5 min", impact: "Med", done: false },
    { time: "10:00 PM", activity: "Sleep (target 7.5 hrs)", duration: "7.5 hrs", impact: "High", done: false },
  ]);

  const supplements = useMemo(
    () => [
      { name: "Vitamin D3", dose: "5000 IU", reason: "Level at 22 ng/mL (target 50+)", priority: "Critical" },
      { name: "Vitamin B12", dose: "1000 mcg", reason: "Level at 310 pg/mL (target 600+)", priority: "Critical" },
      { name: "Omega-3 EPA/DHA", dose: "2g", reason: "High triglycerides (160)", priority: "High" },
      { name: "Magnesium Glycinate", dose: "400 mg", reason: "Sleep quality & BP support", priority: "High" },
      { name: "CoQ10", dose: "200 mg", reason: "Cardiovascular longevity", priority: "Med" },
      { name: "NMN", dose: "500 mg", reason: "NAD+ precursor - cellular aging", priority: "Research" },
    ],
    [],
  );

  const doneCount = routine.filter((item) => item.done).length;
  const matchScore = Math.round(
    (doneCount / routine.length) * 100 * 0.4 +
      (biomarkers.sleepHrs / 8) * 100 * 0.2 +
      (biomarkers.steps / 10000) * 100 * 0.2 +
      Math.max(0, 100 - (biomarkers.ldl - 100) * 2) * 0.2,
  );
  const clampedScore = Math.min(98, Math.max(12, matchScore));
  const bioAge = Math.round(age + (clampedScore < 60 ? 4 : clampedScore < 80 ? 1 : -3));
  const twinAge = Math.round(targetAge - (100 - clampedScore) * 0.15);

  const updateBio = (key: BiomarkerKey, value: number) => {
    setBiomarkers((current) => ({ ...current, [key]: value }));
  };

  const toggleRoutine = (index: number) => {
    setRoutine((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, done: !item.done } : item)));
  };

  return (
    <div className="lt-shell lt-dashboard">
      <style>{appCss}</style>
      <TopNav age={age} activeTab={activeTab} setActiveTab={setActiveTab} onHome={() => navigate("/")} />

      {activeTab === "routine" ? (
        <RoutineTab
          age={age}
          targetAge={targetAge}
          routine={routine}
          biomarkers={biomarkers}
          clampedScore={clampedScore}
          doneCount={doneCount}
          toggleRoutine={toggleRoutine}
        />
      ) : null}

      {activeTab === "biomarkers" ? <BiomarkersTab biomarkers={biomarkers} updateBio={updateBio} bioAge={bioAge} /> : null}

      {activeTab === "nutrition" ? <NutritionTab age={age} supplements={supplements} /> : null}

      {activeTab === "twin" ? (
        <TwinTab age={age} targetAge={targetAge} bioAge={bioAge} twinAge={twinAge} clampedScore={clampedScore} />
      ) : null}

      <div className="lt-bottom">
        <div style={{ color: COLORS.textMuted, fontSize: 12 }}>
          Twin match: <strong style={{ color: COLORS.accent }}>{clampedScore}%</strong> | Bio age:{" "}
          <strong style={{ color: COLORS.gold }}>{bioAge}</strong> | Target at {targetAge}:{" "}
          <strong style={{ color: COLORS.accent }}>bio {twinAge}</strong>
        </div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <GhostButton>Edit Data</GhostButton>
          <PrimaryButton>
            Share Progress <Share2 size={16} />
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}

function ProgressBar({
  value,
  max = 100,
  color = COLORS.accent,
  height = 6,
  animated = true,
}: {
  value: number;
  max?: number;
  color?: string;
  height?: number;
  animated?: boolean;
}) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => setWidth(Math.min(100, Math.max(0, (value / max) * 100))), 180);
    return () => window.clearTimeout(timer);
  }, [value, max]);

  return (
    <div style={{ background: COLORS.border, borderRadius: 99, height, overflow: "hidden", width: "100%" }}>
      <div
        style={{
          height: "100%",
          borderRadius: 99,
          background: `linear-gradient(90deg, ${color}, ${color}88)`,
          width: `${width}%`,
          transition: animated ? "width 1.2s cubic-bezier(0.4, 0, 0.2, 1)" : "none",
          boxShadow: `0 0 12px ${color}66`,
        }}
      />
    </div>
  );
}

function BiomarkerInput({
  label,
  value,
  onChange,
  unit,
  min,
  max,
  optimal,
  sublabel,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  unit: string;
  min: number;
  max: number;
  optimal: number;
  sublabel?: string;
}) {
  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const optPct = Math.min(100, Math.max(0, ((optimal - min) / (max - min)) * 100));
  const diff = Math.abs(value - optimal);
  const signalColor = diff < (max - min) * 0.1 ? COLORS.accent : value > optimal ? COLORS.gold : COLORS.red;

  return (
    <div style={{ ...cardStyle, padding: "16px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 14, marginBottom: 10 }}>
        <div>
          <div style={{ color: COLORS.textPrimary, fontWeight: 700, fontSize: 14 }}>{label}</div>
          {sublabel ? <div style={{ color: COLORS.textMuted, fontSize: 11, marginTop: 2 }}>{sublabel}</div> : null}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: signalColor, boxShadow: `0 0 8px ${signalColor}` }} />
          <input
            type="number"
            value={value}
            onChange={(event) => onChange(Number(event.target.value))}
            style={{
              background: COLORS.surface,
              border: `1px solid ${COLORS.border}`,
              color: COLORS.textPrimary,
              borderRadius: 8,
              padding: "4px 8px",
              width: 76,
              fontSize: 14,
              fontWeight: 800,
              textAlign: "right",
              outline: "none",
            }}
          />
          <span style={{ color: COLORS.textMuted, fontSize: 11, minWidth: 34 }}>{unit}</span>
        </div>
      </div>
      <div style={{ position: "relative", height: 8 }}>
        <ProgressBar value={pct} color={signalColor} />
        <div
          title={`Optimal: ${optimal}`}
          style={{
            position: "absolute",
            top: -2,
            left: `${optPct}%`,
            width: 2,
            height: 12,
            background: COLORS.accent + "AA",
            borderRadius: 2,
            transform: "translateX(-50%)",
          }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5 }}>
        <span style={{ color: COLORS.textMuted, fontSize: 10 }}>{min}</span>
        <span style={{ color: COLORS.accent, fontSize: 10 }}>
          Optimal: {optimal} {unit}
        </span>
        <span style={{ color: COLORS.textMuted, fontSize: 10 }}>{max}</span>
      </div>
    </div>
  );
}

function TwinOrb({
  age,
  label,
  color,
  size = 120,
  animated = false,
}: {
  age: number;
  label: string;
  color: string;
  size?: number;
  animated?: boolean;
}) {
  const orbiters = [HeartPulse, Dna, Activity, Sparkles];

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
      <div style={{ position: "relative", width: size, height: size }}>
        <div
          style={{
            width: size,
            height: size,
            borderRadius: "50%",
            background: `radial-gradient(circle at 35% 35%, ${color}55, ${color}11)`,
            border: `2px solid ${color}66`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            animation: animated ? "pulse-ring 3s ease-in-out infinite, float 4s ease-in-out infinite" : "float 6s ease-in-out infinite",
            boxShadow: `0 0 40px ${color}33, inset 0 0 30px ${color}11`,
            position: "relative",
            overflow: "hidden",
          }}
        >
          {animated ? (
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                height: 1,
                background: `linear-gradient(90deg, transparent, ${color}AA, transparent)`,
                animation: "scan 2s linear infinite",
                top: 0,
              }}
            />
          ) : null}
          <div style={{ fontSize: size * 0.22, fontWeight: 950, color, lineHeight: 1 }}>{age}</div>
          <div style={{ fontSize: size * 0.08, color: color + "99", fontWeight: 800, letterSpacing: 2, textTransform: "uppercase" }}>
            YRS
          </div>
        </div>
        {animated
          ? orbiters.map((Icon, index) => (
              <div
                key={index}
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  marginLeft: -8,
                  marginTop: -8,
                  animation: `orbit ${3 + index * 0.5}s linear infinite`,
                  animationDelay: `${index * 0.7}s`,
                  opacity: 0.75,
                  color,
                }}
              >
                <Icon size={16} />
              </div>
            ))
          : null}
      </div>
      <div style={{ textAlign: "center" }}>
        <div style={{ color: COLORS.textPrimary, fontWeight: 800, fontSize: 14 }}>{label}</div>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  unit,
  delta,
  color = COLORS.accent,
}: {
  icon: ReactNode;
  label: string;
  value: string | number;
  unit?: string;
  delta?: number;
  color?: string;
}) {
  return (
    <div style={{ ...cardStyle, padding: 16, animation: "countUp 0.5s ease forwards" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ color, display: "grid", placeItems: "center" }}>{icon}</div>
        {typeof delta === "number" ? (
          <div
            style={{
              fontSize: 10,
              fontWeight: 800,
              color: delta > 0 ? COLORS.accent : COLORS.red,
              background: delta > 0 ? COLORS.accentDim : COLORS.redDim,
              padding: "2px 8px",
              borderRadius: 99,
            }}
          >
            {delta > 0 ? "+" : ""}
            {delta}%
          </div>
        ) : null}
      </div>
      <div style={{ marginTop: 12 }}>
        <div style={{ color: COLORS.textMuted, fontSize: 11, letterSpacing: 1, textTransform: "uppercase", marginBottom: 4 }}>{label}</div>
        <div style={{ color, fontSize: 24, fontWeight: 950, lineHeight: 1 }}>
          {value}
          {unit ? <span style={{ fontSize: 12, color: COLORS.textMuted, fontWeight: 600, marginLeft: 4 }}>{unit}</span> : null}
        </div>
      </div>
    </div>
  );
}

function Chip({
  children,
  active,
  onClick,
  color = COLORS.accent,
}: {
  children: ReactNode;
  active?: boolean;
  onClick?: () => void;
  color?: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? color + "22" : COLORS.surface,
        border: `1px solid ${active ? color : COLORS.border}`,
        color: active ? color : COLORS.textSecondary,
        borderRadius: 99,
        padding: "7px 16px",
        fontSize: 13,
        fontWeight: 700,
        cursor: "pointer",
        transition: "all 0.2s",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </button>
  );
}

function DailyRoutineCard({ time, activity, duration, impact, done, onToggle }: RoutineItem & { onToggle: () => void }) {
  const impactColor = impact === "High" ? COLORS.accent : impact === "Med" ? COLORS.gold : COLORS.textMuted;

  return (
    <button
      onClick={onToggle}
      style={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        gap: 16,
        background: done ? COLORS.accentDim : COLORS.card,
        border: `1px solid ${done ? COLORS.accentMid : COLORS.border}`,
        borderRadius: 16,
        padding: "14px 18px",
        cursor: "pointer",
        textAlign: "left",
      }}
    >
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: "50%",
          border: `1px solid ${done ? COLORS.accent : COLORS.border}`,
          background: done ? COLORS.accent : COLORS.surface,
          color: done ? COLORS.bg : COLORS.textMuted,
          display: "grid",
          placeItems: "center",
          flexShrink: 0,
        }}
      >
        {done ? <span style={{ fontWeight: 900, fontSize: 13 }}>✓</span> : <Circle size={13} />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: COLORS.textPrimary, fontWeight: 800, fontSize: 14 }}>{activity}</div>
        <div style={{ color: COLORS.textMuted, fontSize: 11, marginTop: 2 }}>
          {time} | {duration}
        </div>
      </div>
      <div
        style={{
          fontSize: 10,
          fontWeight: 900,
          color: impactColor,
          background: impactColor + "22",
          padding: "3px 10px",
          borderRadius: 99,
          letterSpacing: 0.5,
        }}
      >
        {impact}
      </div>
    </button>
  );
}

function ScoreRing({ score, doneCount, total }: { score: number; doneCount: number; total: number }) {
  const r = 70;
  const circumference = 2 * Math.PI * r;

  return (
    <div style={{ ...cardStyle, borderRadius: 20, padding: 24, textAlign: "center" }}>
      <div style={{ fontSize: 11, letterSpacing: 2, color: COLORS.textMuted, textTransform: "uppercase", marginBottom: 16 }}>
        TWIN MATCH TODAY
      </div>
      <div style={{ position: "relative", display: "inline-block" }}>
        <svg width={160} height={160} viewBox="0 0 160 160">
          <circle cx={80} cy={80} r={r} fill="none" stroke={COLORS.border} strokeWidth={10} />
          <circle
            cx={80}
            cy={80}
            r={r}
            fill="none"
            stroke={COLORS.accent}
            strokeWidth={10}
            strokeDasharray={`${circumference}`}
            strokeDashoffset={`${circumference * (1 - score / 100)}`}
            strokeLinecap="round"
            transform="rotate(-90 80 80)"
            style={{ transition: "stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1)", filter: `drop-shadow(0 0 8px ${COLORS.accent})` }}
          />
          <text x={80} y={76} textAnchor="middle" fill={COLORS.textPrimary} fontSize={32} fontWeight={900}>
            {score}
          </text>
          <text x={80} y={96} textAnchor="middle" fill={COLORS.textMuted} fontSize={12}>
            % match
          </text>
        </svg>
      </div>
      <div style={{ marginTop: 16, color: COLORS.textMuted, fontSize: 13 }}>
        {doneCount} of {total} habits done
      </div>
      <div style={{ marginTop: 8 }}>
        <ProgressBar value={(doneCount / total) * 100} color={COLORS.accent} height={4} />
      </div>
    </div>
  );
}

function SectionLabel({ children, color = COLORS.accent }: { children: ReactNode; color?: string }) {
  return (
    <div
      style={{
        color,
        fontSize: 11,
        fontWeight: 800,
        letterSpacing: 2,
        marginBottom: 12,
        textTransform: "uppercase",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {children}
    </div>
  );
}

function PrimaryButton({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
        border: "none",
        color: COLORS.bg,
        borderRadius: 14,
        padding: "14px 28px",
        fontSize: 14,
        fontWeight: 900,
        cursor: "pointer",
        boxShadow: `0 8px 30px ${COLORS.accent}33`,
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {children}
    </button>
  );
}

function GhostButton({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: COLORS.card,
        border: `1px solid ${COLORS.border}`,
        color: COLORS.textSecondary,
        borderRadius: 12,
        padding: "12px 22px",
        fontSize: 14,
        fontWeight: 700,
        cursor: "pointer",
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {children}
    </button>
  );
}

function TopNav({
  age,
  activeTab,
  setActiveTab,
  onHome,
}: {
  age: number;
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  onHome: () => void;
}) {
  return (
    <div className="lt-topbar">
      <div className="lt-brand">
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 10,
            background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
            display: "grid",
            placeItems: "center",
            color: COLORS.bg,
          }}
        >
          <Dna size={19} strokeWidth={3} />
        </div>
        <div>
          <div style={{ fontWeight: 900, fontSize: 16, letterSpacing: -0.5 }}>LifeTwin AI</div>
          <div style={{ fontSize: 10, color: COLORS.textMuted, letterSpacing: 1 }}>LONGEVITY DIGITAL TWIN</div>
        </div>
      </div>

      <div className="lt-tabs">
        {TABS.map((tab) => (
          <Chip key={tab} active={activeTab === tab} onClick={() => setActiveTab(tab)}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </Chip>
        ))}
      </div>

      <button className="lt-user-pill" onClick={onHome} title="Go to home page" aria-label="Go to home page">
        P
      </button>
    </div>
  );
}

function RoutineTab({
  age,
  targetAge,
  routine,
  biomarkers,
  clampedScore,
  doneCount,
  toggleRoutine,
}: {
  age: number;
  targetAge: number;
  routine: RoutineItem[];
  biomarkers: Biomarkers;
  clampedScore: number;
  doneCount: number;
  toggleRoutine: (index: number) => void;
}) {
  return (
    <div className="lt-page">
      <div className="lt-grid-two">
        <div>
          <div style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: 0 }}>Today's Protocol</h2>
            <p style={{ color: COLORS.textSecondary, marginTop: 6, fontSize: 14 }}>
              Tailored for Pruthvi, {age} · targeting age {targetAge} twin
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {routine.map((item, index) => (
              <DailyRoutineCard key={`${item.time}-${item.activity}`} {...item} onToggle={() => toggleRoutine(index)} />
            ))}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <ScoreRing score={clampedScore} doneCount={doneCount} total={routine.length} />
          <div className="lt-grid-half">
            <MetricCard icon={<Moon size={21} />} label="Sleep" value={biomarkers.sleepHrs} unit="hrs" delta={-18} color={COLORS.purple} />
            <MetricCard icon={<Activity size={21} />} label="Steps" value={`${(biomarkers.steps / 1000).toFixed(1)}k`} delta={-52} color={COLORS.gold} />
            <MetricCard icon={<HeartPulse size={21} />} label="BP" value={`${biomarkers.systolic}/${biomarkers.diastolic}`} color={COLORS.red} />
            <MetricCard icon={<TestTube2 size={21} />} label="HbA1c" value={biomarkers.hba1c} unit="%" delta={5} color={COLORS.accent} />
          </div>
        </div>
      </div>
    </div>
  );
}

function BiomarkersTab({ biomarkers, updateBio, bioAge }: { biomarkers: Biomarkers; updateBio: (key: BiomarkerKey, value: number) => void; bioAge: number }) {
  return (
    <div className="lt-page" style={{ maxWidth: 900 }}>
      <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: "0 0 8px" }}>Your Biomarker Panel</h2>
      <p style={{ color: COLORS.textSecondary, marginBottom: 32, fontSize: 14 }}>
        Enter your latest lab values. The twin recalibrates in real-time.
      </p>

      <BiomarkerSection color={COLORS.accent} title="Lipid Profile" icon={<HeartPulse size={14} />}>
        <BiomarkerInput label="LDL Cholesterol" value={biomarkers.ldl} onChange={(value) => updateBio("ldl", value)} unit="mg/dL" min={50} max={220} optimal={90} sublabel="Target <100 for longevity" />
        <BiomarkerInput label="HDL Cholesterol" value={biomarkers.hdl} onChange={(value) => updateBio("hdl", value)} unit="mg/dL" min={20} max={100} optimal={65} sublabel="Higher is better" />
        <BiomarkerInput label="Triglycerides" value={biomarkers.triglycerides} onChange={(value) => updateBio("triglycerides", value)} unit="mg/dL" min={50} max={400} optimal={100} sublabel="Target <100 optimal" />
      </BiomarkerSection>

      <BiomarkerSection color={COLORS.gold} title="Vitamins & Hormones" icon={<Sun size={14} />}>
        <BiomarkerInput label="Vitamin D" value={biomarkers.vitaminD} onChange={(value) => updateBio("vitaminD", value)} unit="ng/mL" min={5} max={100} optimal={60} sublabel="Severely deficient <20" />
        <BiomarkerInput label="Vitamin B12" value={biomarkers.b12} onChange={(value) => updateBio("b12", value)} unit="pg/mL" min={100} max={1200} optimal={700} sublabel="Optimal 600-800" />
      </BiomarkerSection>

      <BiomarkerSection color={COLORS.purple} title="Metabolic & Organ" icon={<Activity size={14} />}>
        <BiomarkerInput label="HbA1c" value={biomarkers.hba1c} onChange={(value) => updateBio("hba1c", value)} unit="%" min={4} max={9} optimal={5.0} sublabel="Optimal <5.2%" />
        <BiomarkerInput label="ALT (Liver)" value={biomarkers.alt} onChange={(value) => updateBio("alt", value)} unit="U/L" min={5} max={100} optimal={20} sublabel="Optimal 10-25" />
        <BiomarkerInput label="Creatinine" value={biomarkers.creatinine} onChange={(value) => updateBio("creatinine", value)} unit="mg/dL" min={0.5} max={2.5} optimal={0.9} sublabel="Kidney function marker" />
      </BiomarkerSection>

      <div
        style={{
          background: `linear-gradient(135deg, ${COLORS.accentDim}, ${COLORS.goldDim})`,
          border: `1px solid ${COLORS.accent}33`,
          borderRadius: 16,
          padding: 20,
        }}
      >
        <div style={{ fontWeight: 700, color: COLORS.accent, marginBottom: 8 }}>
          <Sparkles size={16} style={{ display: "inline-block", marginRight: 8, verticalAlign: "text-bottom" }} />
          AI Analysis
        </div>
        <p style={{ color: COLORS.textSecondary, fontSize: 14, margin: 0, lineHeight: 1.7 }}>
          Your lipid panel shows elevated LDL (128) and borderline triglycerides (160) - classic pattern of refined carb
          excess plus sedentary load. Critical Vitamin D deficiency (22 ng/mL) is suppressing immune function, testosterone,
          and longevity pathways. B12 at 310 pg/mL is suboptimal for neurological health (target 600+).{" "}
          <strong style={{ color: COLORS.textPrimary }}>Projected bio age: {bioAge}.</strong> With protocol adherence,
          10-year longevity gain is achievable.
        </p>
      </div>
    </div>
  );
}

function BiomarkerSection({ title, color, icon, children }: { title: string; color: string; icon: ReactNode; children: ReactNode }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <SectionLabel color={color}>
        {icon} {title}
      </SectionLabel>
      <div className="lt-grid-half">{children}</div>
    </div>
  );
}

function NutritionTab({ age, supplements }: { age: number; supplements: Array<{ name: string; dose: string; reason: string; priority: string }> }) {
  const meals = [
    {
      meal: "Breakfast 7:00 AM",
      items: ["3 eggs + 1 whole (protein 24g)", "Avocado 1/2 (healthy fats)", "Spinach saute (iron, folate)", "Black coffee (no sugar)"],
      tag: "Protein-forward, anti-inflammatory",
    },
    {
      meal: "Lunch 12:30 PM",
      items: ["Grilled salmon 150g (Omega-3)", "Quinoa 1/2 cup (complete protein)", "Rainbow salad + olive oil", "Turmeric lemon dressing"],
      tag: "Mediterranean · LDL optimiser",
    },
    {
      meal: "Snack 4:00 PM",
      items: ["Walnuts 30g (ALA Omega-3)", "Green tea (EGCG antioxidant)"],
      tag: "Brain + lipid support",
    },
    {
      meal: "Dinner 7:30 PM",
      items: ["Chicken breast 150g", "Roasted vegetables", "Lentil soup (fibre, B9)", "Last meal before 8 PM"],
      tag: "IF window closes · gut health",
    },
  ];

  const macros = [
    { label: "Protein", target: "140g", current: 90, color: COLORS.accent },
    { label: "Healthy Fats", target: "70g", current: 60, color: COLORS.gold },
    { label: "Complex Carbs", target: "150g", current: 80, color: COLORS.purple },
    { label: "Fibre", target: "35g", current: 45, color: COLORS.blue },
  ];

  return (
    <div className="lt-page" style={{ maxWidth: 1000 }}>
      <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: "0 0 8px" }}>Personalised Nutrition Stack</h2>
      <p style={{ color: COLORS.textSecondary, marginBottom: 32, fontSize: 14 }}>
        Formulated for your exact biomarkers. Not generic - built for Pruthvi, {age}.
      </p>

      <div className="lt-nutrition" style={{ marginBottom: 32 }}>
        <div>
          <SectionLabel color={COLORS.gold}>Your Personalised Stack</SectionLabel>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {supplements.map((item) => {
              const priorityColor =
                item.priority === "Critical" ? COLORS.red : item.priority === "High" ? COLORS.gold : item.priority === "Research" ? COLORS.purple : COLORS.accent;
              const priorityBackground =
                item.priority === "Critical" ? COLORS.redDim : item.priority === "High" ? COLORS.goldDim : item.priority === "Research" ? "#8B5CF622" : COLORS.accentDim;

              return (
                <div
                  key={item.name}
                  style={{
                    ...cardStyle,
                    borderRadius: 14,
                    padding: "14px 18px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 16,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: COLORS.textPrimary }}>{item.name}</div>
                    <div style={{ color: COLORS.textMuted, fontSize: 11, marginTop: 3 }}>{item.reason}</div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontWeight: 900, color: COLORS.accent, fontSize: 14 }}>{item.dose}</div>
                    <div
                      style={{
                        fontSize: 9,
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: 99,
                        marginTop: 4,
                        color: priorityColor,
                        background: priorityBackground,
                        letterSpacing: 0.5,
                      }}
                    >
                      {item.priority.toUpperCase()}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <SectionLabel color={COLORS.accent}>Today's Diet Protocol</SectionLabel>
          {meals.map((meal) => (
            <div key={meal.meal} style={{ ...cardStyle, borderRadius: 14, padding: "16px 18px", marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 10 }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: COLORS.textPrimary }}>{meal.meal}</div>
                <div style={{ fontSize: 9, color: COLORS.accent, background: COLORS.accentDim, padding: "2px 8px", borderRadius: 99, fontWeight: 700 }}>
                  {meal.tag}
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {meal.items.map((item) => (
                  <div key={item} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ width: 4, height: 4, borderRadius: "50%", background: COLORS.accent, flexShrink: 0 }} />
                    <span style={{ color: COLORS.textSecondary, fontSize: 12 }}>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div style={{ ...cardStyle, borderRadius: 14, padding: 16, marginTop: 4 }}>
            <div style={{ color: COLORS.textMuted, fontSize: 11, fontWeight: 700, letterSpacing: 1, marginBottom: 12, textTransform: "uppercase" }}>
              Daily Macro Targets
            </div>
            {macros.map((macro) => (
              <div key={macro.label} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ color: COLORS.textPrimary, fontSize: 12, fontWeight: 700 }}>{macro.label}</span>
                  <span style={{ color: COLORS.textMuted, fontSize: 11 }}>Target {macro.target}</span>
                </div>
                <ProgressBar value={macro.current} color={macro.color} height={5} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function TwinTab({
  age,
  targetAge,
  bioAge,
  twinAge,
  clampedScore,
}: {
  age: number;
  targetAge: number;
  bioAge: number;
  twinAge: number;
  clampedScore: number;
}) {
  const gaps = [
    { label: "Cardiovascular", current: 62, ideal: 95, icon: <HeartPulse size={22} /> },
    { label: "Metabolic", current: 71, ideal: 92, icon: <Zap size={22} /> },
    { label: "Cellular Aging", current: 55, ideal: 88, icon: <Dna size={22} /> },
    { label: "Sleep Quality", current: 58, ideal: 95, icon: <Moon size={22} /> },
    { label: "Inflammation", current: 68, ideal: 90, icon: <Activity size={22} /> },
    { label: "Movement", current: 74, ideal: 91, icon: <Dumbbell size={22} /> },
  ];

  return (
    <div className="lt-page" style={{ maxWidth: 1040 }}>
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <div style={{ fontSize: 11, letterSpacing: 3, color: COLORS.accent, textTransform: "uppercase", fontWeight: 900, marginBottom: 12 }}>
          Your Digital Twin System
        </div>
        <h1 style={{ fontSize: 44, fontWeight: 950, letterSpacing: -2, lineHeight: 1.1, margin: 0 }}>
          Meet your{" "}
          <span
            style={{
              background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            future self
          </span>
        </h1>
        <p style={{ color: COLORS.textSecondary, marginTop: 12, fontSize: 16 }}>
          Mock longevity interface based on the PDF format: current self, ideal twin, and gap closure.
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 60, marginBottom: 48, flexWrap: "wrap" }}>
        <div style={{ textAlign: "center" }}>
          <TwinOrb age={age} label="You Today" color={COLORS.blue} size={140} />
          <div style={{ marginTop: 12, color: COLORS.textMuted, fontSize: 12 }}>Biological age: {bioAge}</div>
        </div>
        <div style={{ textAlign: "center", width: 180 }}>
          <div style={{ fontSize: 42, fontWeight: 950, color: COLORS.accent }}>{clampedScore}%</div>
          <div style={{ color: COLORS.textMuted, fontSize: 12, marginTop: 4, marginBottom: 10 }}>Match to ideal</div>
          <ProgressBar value={clampedScore} color={COLORS.accent} height={4} />
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
            {["Sleep", "Diet", "Movement"].map((item) => (
              <span key={item} style={{ fontSize: 10, color: COLORS.textMuted }}>
                {"->"} {item}
              </span>
            ))}
          </div>
        </div>
        <div style={{ textAlign: "center" }}>
          <TwinOrb age={targetAge} label={`Ideal You at ${targetAge}`} color={COLORS.accent} size={140} animated />
          <div style={{ marginTop: 12, color: COLORS.accent, fontSize: 12 }}>Projected bio age: {twinAge}</div>
        </div>
      </div>

      <div className="lt-grid-cards">
        {gaps.map((gap) => (
          <div key={gap.label} style={{ ...cardStyle, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={{ color: COLORS.purple }}>{gap.icon}</div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 20, fontWeight: 950, color: COLORS.accent }}>{gap.ideal}%</div>
                <div style={{ fontSize: 10, color: COLORS.textMuted }}>ideal</div>
              </div>
            </div>
            <div style={{ color: COLORS.textPrimary, fontWeight: 800, fontSize: 13, marginBottom: 8 }}>{gap.label}</div>
            <ProgressBar value={gap.current} color={COLORS.purple} height={4} />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
              <span style={{ fontSize: 10, color: COLORS.textMuted }}>Now: {gap.current}%</span>
              <span style={{ fontSize: 10, color: COLORS.textMuted }}>Gap: {gap.ideal - gap.current}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
