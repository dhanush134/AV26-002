import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { Activity, Dna, Dumbbell, HeartPulse, Moon, Share2, Sparkles, Zap } from "lucide-react";

const COLORS = {
  bg: "#060810",
  surface: "#0D1117",
  card: "#111827",
  border: "#1F2937",
  accent: "#00D4AA",
  accentDim: "#00D4AA22",
  purple: "#8B5CF6",
  blue: "#3B82F6",
  textPrimary: "#F9FAFB",
  textSecondary: "#9CA3AF",
  textMuted: "#4B5563",
};

const TABS = ["routine", "biomarkers", "nutrition", "twin"] as const;

type Tab = (typeof TABS)[number];

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
@keyframes orbit {
  from { transform: rotate(0deg) translateX(80px) rotate(0deg); }
  to { transform: rotate(360deg) translateX(80px) rotate(-360deg); }
}
.lt-shell { min-height: 100vh; background: #060810; color: #F9FAFB; font-family: "DM Sans", Inter, system-ui, sans-serif; }
.lt-dashboard { padding-bottom: 78px; }
.lt-topbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 20px 32px; border-bottom: 1px solid #1F2937; background: rgba(6, 8, 16, 0.92); backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 50; }
.lt-brand { display: flex; align-items: center; gap: 12px; min-width: 210px; }
.lt-tabs { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.lt-user-pill { display: flex; align-items: center; gap: 10px; background: #111827; border: 1px solid #1F2937; border-radius: 999px; padding: 8px 16px; font-size: 13px; font-weight: 700; white-space: nowrap; }
.lt-page { padding: 40px 32px; max-width: 1120px; margin: 0 auto; }
.lt-grid-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.lt-bottom { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(13, 17, 23, 0.94); border-top: 1px solid #1F2937; padding: 12px 32px; display: flex; align-items: center; justify-content: space-between; gap: 16px; backdrop-filter: blur(20px); z-index: 60; }
@media (max-width: 920px) {
  .lt-topbar { align-items: flex-start; flex-direction: column; padding: 18px; }
  .lt-tabs { justify-content: flex-start; width: 100%; overflow-x: auto; flex-wrap: nowrap; }
  .lt-user-pill { display: none; }
  .lt-page { padding: 28px 18px 94px; }
  .lt-grid-cards { grid-template-columns: 1fr; }
  .lt-bottom { align-items: flex-start; flex-direction: column; padding: 12px 18px; }
}
`;

const cardStyle: CSSProperties = {
  background: COLORS.card,
  border: `1px solid ${COLORS.border}`,
  borderRadius: 16,
};

export function TwinPage() {
  const [age] = useState(34);
  const [targetAge] = useState(65);
  const [activeTab, setActiveTab] = useState<Tab>("twin");
  const bioAge = 38;
  const twinAge = 56;
  const clampedScore = 43;

  return (
    <div className="lt-shell lt-dashboard">
      <style>{appCss}</style>
      <TopNav age={age} activeTab={activeTab} setActiveTab={setActiveTab} />
      <TwinTab age={age} targetAge={targetAge} bioAge={bioAge} twinAge={twinAge} clampedScore={clampedScore} />
      <div className="lt-bottom">
        <div style={{ color: COLORS.textMuted, fontSize: 12 }}>
          Twin match: <strong style={{ color: COLORS.accent }}>{clampedScore}%</strong> | Bio age:{" "}
          <strong style={{ color: "#F5B942" }}>{bioAge}</strong> | Target at {targetAge}:{" "}
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

function TwinOrb({
  age,
  score,
  label,
  color,
  size = 120,
  animated = false,
}: {
  age: number;
  score?: number;
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
          {score ? <div style={{ fontSize: size * 0.1, color: COLORS.accent, fontWeight: 900, marginTop: 2 }}>{score}%</div> : null}
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

function TopNav({ age, activeTab, setActiveTab }: { age: number; activeTab: Tab; setActiveTab: (tab: Tab) => void }) {
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

      <div className="lt-user-pill">
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: COLORS.accent, animation: "glow 2s ease-in-out infinite" }} />
        <span>Demo User, {age}</span>
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
