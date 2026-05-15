import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { Activity, AlertTriangle, Bell, ChevronDown, ChevronUp, Circle, Dna, Dumbbell, HeartPulse, Moon, RefreshCw, Sparkles, Sun, TestTube2, Wind, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

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

const TABS = ["routine", "biomarkers", "nutrition", "twin", "alerts"] as const;
const INTAKE_STORAGE_KEY = "lifetwin_intake_draft_v1";
const USER_STORAGE_KEY = "lifetwin_intake_user_id_v1";
const ADAPTIVE_ROUTINE_STORAGE_KEY = "lifetwin_adaptive_routine_v1";
const ADAPTIVE_NUTRITION_STORAGE_KEY = "lifetwin_adaptive_nutrition_v1";
const BIOMARKER_ANALYSIS_STORAGE_KEY = "lifetwin_biomarker_analysis_v1";
const ADAPTIVE_PLAN_PENDING_STORAGE_KEY = "lifetwin_adaptive_plan_pending_v1";
const ADAPTIVE_PLAN_UPDATED_EVENT = "lifetwin-adaptive-plan-updated";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
  | "steps"
  | "heartRate"
  | "stress";

type Biomarkers = Record<BiomarkerKey, number>;

type IntakeDraft = {
  form?: {
    currentAge?: string;
    height?: string;
    weight?: string;
    pulseRate?: string;
    stress?: string;
    exercise?: string;
    dailySteps?: string;
    sleepHours?: string;
    targetTwinAge?: string;
    hba1c?: string;
    bpSystolic?: string;
    bpDiastolic?: string;
    vitaminD?: string;
    vitaminB12?: string;
  };
};

type ApiUser = {
  id: string;
};

type ApiLabReport = {
  hba1c?: number | null;
  bp_systolic?: number | null;
  bp_diastolic?: number | null;
  vitamin_d?: number | null;
  vitamin_b12?: number | null;
};

type IntakeBiomarkers = {
  hba1c?: number;
  systolic?: number;
  diastolic?: number;
  vitaminD?: number;
  b12?: number;
};

interface RoutineItem {
  id?: string;
  time: string;
  activity: string;
  duration: string;
  impact: "High" | "Med" | "Low";
  done: boolean;
  why?: string;
  strictRule?: string;
  progressionNote?: string;
  category?: string;
}

type NegativeChoice =
  | "alcohol"
  | "smoking"
  | "high_sugar"
  | "fried_food"
  | "late_heavy_meal"
  | "missed_sleep_window"
  | "missed_workout"
  | "very_high_stress"
  | "low_water"
  | "excess_caffeine";

type AdaptivePlanActivity = {
  id: string;
  time_window: string;
  title: string;
  category: string;
  target: string;
  why: string;
  priority: "critical" | "high" | "medium" | "low";
  strict_rule: string;
  progression_note: string;
};

type AdaptiveMeal = {
  meal: "breakfast" | "lunch" | "snack" | "dinner";
  composition: string;
  north_indian_veg: string[];
  north_indian_non_veg: string[];
  south_indian_veg: string[];
  south_indian_non_veg: string[];
  note: string;
};

type AdaptiveNutrition = {
  macro_distribution: {
    protein_percent: number;
    carbs_percent: number;
    fats_percent: number;
    fiber_grams: number;
    water_liters: number;
  };
  meals: AdaptiveMeal[];
  supplement_guidance: Array<{
    name: string;
    priority: "critical" | "high" | "medium" | "optional" | "avoid";
    why: string;
    suggested_timing: string;
    safety_note: string;
  }>;
};

type AdaptivePlanResponse = {
  plan_date: string;
  generated_by: "openai";
  model_used: string;
  strictness: "strict" | "progressive" | "recovery";
  summary: string;
  timeline: {
    estimated_weeks: number;
    confidence: "low" | "medium" | "high";
    summary: string;
    next_review_date: string;
    assumptions: string[];
  };
  activities: AdaptivePlanActivity[];
  negative_options: NegativeChoice[];
  checkin_prompt: string;
  nutrition: AdaptiveNutrition;
  safety_notes: string[];
};

type RoutinePlanResponse = Omit<AdaptivePlanResponse, "nutrition">;
type NutritionPlanResponse = Pick<AdaptivePlanResponse, "plan_date" | "generated_by" | "model_used" | "summary" | "nutrition" | "safety_notes">;

type BiomarkerAnalysisResponse = {
  generated_by: "openai";
  model_used: string;
  summary: string;
  key_findings: string[];
  watch_items: string[];
  next_actions: string[];
  safety_notes: string[];
};

type WearableReading = {
  id?: string;
  timestamp: string;
  heart_rate?: number | null;
  resting_heart_rate?: number | null;
  steps?: number | null;
  active_minutes?: number | null;
  sleep_hours?: number | null;
  sleep_quality?: number | null;
  stress_score?: number | null;
  spo2?: number | null;
  source?: string;
};

type AlertItem = {
  id: string;
  severity: "info" | "warning" | "critical";
  title: string;
  message: string;
  recommended_action: string;
  source: string;
  timestamp?: string;
};

type DemoWatchPoint = WearableReading & {
  event?: "stress" | "break" | "walk" | "fall";
  altitude_delta_m?: number;
  acceleration_g?: number;
};

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
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes loading-sweep {
  0%, 100% { transform: translateX(-15%); opacity: 0.55; }
  50% { transform: translateX(65%); opacity: 1; }
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
@media (max-width: 920px) {
  .lt-topbar { align-items: flex-start; flex-direction: column; padding: 18px; }
  .lt-tabs { justify-content: flex-start; width: 100%; overflow-x: auto; flex-wrap: nowrap; }
  .lt-user-pill { display: none; }
  .lt-page { padding: 28px 18px 94px; }
  .lt-grid-two, .lt-nutrition, .lt-grid-cards, .lt-grid-half { grid-template-columns: 1fr; }
}
`;

const cardStyle: CSSProperties = {
  background: COLORS.card,
  border: `1px solid ${COLORS.border}`,
  borderRadius: 16,
};

function numberFromDraft(value: string | undefined) {
  if (!value?.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function apiErrorText(raw: string, fallback: string) {
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw) as { error?: { message?: string } };
    return parsed.error?.message || raw;
  } catch {
    return raw;
  }
}

function loadIntakeBiomarkers(): IntakeBiomarkers {
  try {
    const saved = localStorage.getItem(INTAKE_STORAGE_KEY);
    if (!saved) return {};
    const parsed = JSON.parse(saved) as IntakeDraft;
    const form = parsed.form;
    if (!form) return {};
    return {
      hba1c: numberFromDraft(form.hba1c),
      systolic: numberFromDraft(form.bpSystolic),
      diastolic: numberFromDraft(form.bpDiastolic),
      vitaminD: numberFromDraft(form.vitaminD),
      b12: numberFromDraft(form.vitaminB12),
    };
  } catch {
    return {};
  }
}

async function getSingleUserId() {
  const existingUserId = localStorage.getItem(USER_STORAGE_KEY);
  if (existingUserId) return existingUserId;
  const response = await fetch(`${API_BASE_URL}/api/v1/users?limit=1`);
  if (!response.ok) return undefined;
  const users = (await response.json()) as ApiUser[];
  const userId = users[0]?.id;
  if (userId) localStorage.setItem(USER_STORAGE_KEY, userId);
  return userId;
}

async function fetchLatestBiomarkersFromDb(): Promise<IntakeBiomarkers | undefined> {
  const userId = await getSingleUserId();
  if (!userId) return undefined;
  const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/lab-reports/latest`);
  if (!response.ok) return undefined;
  const report = (await response.json()) as ApiLabReport;
  return {
    hba1c: report.hba1c ?? undefined,
    systolic: report.bp_systolic ?? undefined,
    diastolic: report.bp_diastolic ?? undefined,
    vitaminD: report.vitamin_d ?? undefined,
    b12: report.vitamin_b12 ?? undefined,
  };
}

function loadIntakeForm() {
  try {
    const saved = localStorage.getItem(INTAKE_STORAGE_KEY);
    if (!saved) return undefined;
    return (JSON.parse(saved) as IntakeDraft).form;
  } catch {
    return undefined;
  }
}

function loadCachedRoutinePlan(): RoutinePlanResponse | null {
  try {
    const saved = localStorage.getItem(ADAPTIVE_ROUTINE_STORAGE_KEY);
    if (!saved) return null;
    const parsed = JSON.parse(saved) as { generated_by?: string };
    if (parsed.generated_by !== "openai") {
      localStorage.removeItem(ADAPTIVE_ROUTINE_STORAGE_KEY);
      return null;
    }
    return parsed as RoutinePlanResponse;
  } catch {
    return null;
  }
}

function loadCachedNutritionPlan(): NutritionPlanResponse | null {
  try {
    const saved = localStorage.getItem(ADAPTIVE_NUTRITION_STORAGE_KEY);
    if (!saved) return null;
    const parsed = JSON.parse(saved) as { generated_by?: string };
    if (parsed.generated_by !== "openai") {
      localStorage.removeItem(ADAPTIVE_NUTRITION_STORAGE_KEY);
      return null;
    }
    return parsed as NutritionPlanResponse;
  } catch {
    return null;
  }
}

function loadCachedBiomarkerAnalysis(): BiomarkerAnalysisResponse | null {
  try {
    const saved = localStorage.getItem(BIOMARKER_ANALYSIS_STORAGE_KEY);
    if (!saved) return null;
    const parsed = JSON.parse(saved) as { generated_by?: string };
    if (parsed.generated_by !== "openai") {
      localStorage.removeItem(BIOMARKER_ANALYSIS_STORAGE_KEY);
      return null;
    }
    return parsed as BiomarkerAnalysisResponse;
  } catch {
    return null;
  }
}

function adaptiveImpact(priority: AdaptivePlanActivity["priority"]): RoutineItem["impact"] {
  if (priority === "critical" || priority === "high") return "High";
  if (priority === "medium") return "Med";
  return "Low";
}

function activitiesToRoutine(activities: AdaptivePlanActivity[]): RoutineItem[] {
  return activities.map((item) => ({
    id: item.id,
    time: item.time_window,
    activity: item.title,
    duration: item.target,
    impact: adaptiveImpact(item.priority),
    done: false,
    why: item.why,
    strictRule: item.strict_rule,
    progressionNote: item.progression_note,
    category: item.category,
  }));
}

function buildMetricsPayload(biomarkers: Biomarkers) {
  const form = loadIntakeForm();
  return {
    age: numberFromDraft(form?.currentAge),
    weight_kg: numberFromDraft(form?.weight),
    height_cm: numberFromDraft(form?.height),
    stress_score: numberFromDraft(form?.stress),
    heart_rate_bpm: numberFromDraft(form?.pulseRate),
    sleep_hours: numberFromDraft(form?.sleepHours) ?? biomarkers.sleepHrs,
    steps: numberFromDraft(form?.dailySteps) ?? biomarkers.steps,
    workout_info: form?.exercise ? `Workout/exercise minutes or note: ${form.exercise}` : undefined,
    biomarkers: {
      hba1c: biomarkers.hba1c,
      bp_systolic: Math.round(biomarkers.systolic),
      bp_diastolic: Math.round(biomarkers.diastolic),
      ldl: biomarkers.ldl,
      hdl: biomarkers.hdl,
      triglycerides: biomarkers.triglycerides,
      vitamin_d: biomarkers.vitaminD,
      vitamin_b12: biomarkers.b12,
      sgpt: biomarkers.alt,
      creatinine: biomarkers.creatinine,
    },
  };
}

function formatPlanDate(value?: string) {
  const date = value ? new Date(`${value}T00:00:00`) : new Date();
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function nextDateString(value?: string) {
  const base = value ? new Date(`${value}T00:00:00`) : new Date();
  base.setDate(base.getDate() + 1);
  return base.toISOString().slice(0, 10);
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function higherIsBetterPercent(value: number, ideal: number) {
  return clampPercent((value / ideal) * 100);
}

function lowerIsBetterPercent(value: number, ideal: number, max: number) {
  if (value <= ideal) return 100;
  return clampPercent(100 - ((value - ideal) / (max - ideal)) * 100);
}

function calculateBmi(heightCm?: number, weightKg?: number) {
  if (!heightCm || !weightKg) return undefined;
  const heightM = heightCm / 100;
  if (heightM <= 0) return undefined;
  return Number((weightKg / (heightM * heightM)).toFixed(1));
}

const NEGATIVE_LABELS: Record<NegativeChoice, string> = {
  alcohol: "Alcohol",
  smoking: "Smoking",
  high_sugar: "High sugar",
  fried_food: "Fried food",
  late_heavy_meal: "Late heavy meal",
  missed_sleep_window: "Missed sleep window",
  missed_workout: "Missed workout",
  very_high_stress: "Very high stress",
  low_water: "Low water",
  excess_caffeine: "Excess caffeine",
};

const SYNTHETIC_WATCH_DEMO: DemoWatchPoint[] = [
  { timestamp: "2026-05-15T08:00:00+05:30", heart_rate: 78, stress_score: 38, steps: 900, sleep_hours: 6.4, event: "break", source: "synthetic" },
  { timestamp: "2026-05-15T10:30:00+05:30", heart_rate: 112, stress_score: 84, steps: 1600, active_minutes: 0, event: "stress", source: "synthetic" },
  { timestamp: "2026-05-15T11:00:00+05:30", heart_rate: 82, stress_score: 54, steps: 2400, active_minutes: 8, event: "walk", source: "synthetic" },
  { timestamp: "2026-05-15T15:20:00+05:30", heart_rate: 128, stress_score: 92, steps: 2600, altitude_delta_m: -1.8, acceleration_g: 2.9, event: "fall", source: "synthetic" },
  { timestamp: "2026-05-15T19:30:00+05:30", heart_rate: 88, stress_score: 48, steps: 6200, active_minutes: 32, event: "walk", source: "synthetic" },
];

function readingTimeLabel(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function readingDateLabel(timestamp: string) {
  return new Date(timestamp).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

function readingDateTimeLabel(timestamp: string) {
  const date = new Date(timestamp);
  return `${date.toLocaleDateString(undefined, { day: "numeric", month: "short" })} ${date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

function wearableChartData(readings: WearableReading[], preferDateLabels = false) {
  const sorted = readings.slice().sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  const uniqueTimeLabels = new Set(sorted.map((item) => readingTimeLabel(item.timestamp))).size;
  const useDateLabels = preferDateLabels || (sorted.length > 1 && uniqueTimeLabels <= Math.ceil(sorted.length * 0.35));

  return sorted
    .map((item, index) => ({
      time: useDateLabels ? readingDateLabel(item.timestamp) : readingTimeLabel(item.timestamp),
      tooltipTime: readingDateTimeLabel(item.timestamp),
      point: index + 1,
      bpm: item.heart_rate ?? item.resting_heart_rate ?? null,
      stress: item.stress_score ?? null,
      steps: item.steps ?? null,
      sleep: item.sleep_hours ?? null,
    }));
}

function deriveWearableAlerts(readings: WearableReading[]): AlertItem[] {
  const sorted = readings.slice().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  const latest = sorted[0];
  const alerts: AlertItem[] = [];
  if (!latest) return alerts;
  const latestBpm = latest.heart_rate ?? latest.resting_heart_rate;

  if (latest.stress_score != null && latest.stress_score >= 80) {
    alerts.push({
      id: "derived-stress",
      severity: "warning",
      title: "Stress is running high",
      message: `Latest stress score is ${Math.round(latest.stress_score)}.`,
      recommended_action: "Take a 1-minute breathing break now.",
      source: "wearable",
      timestamp: latest.timestamp,
    });
  }
  if (latestBpm != null && latestBpm >= 110 && (latest.active_minutes ?? 0) <= 5) {
    alerts.push({
      id: "derived-high-bpm-rest",
      severity: "critical",
      title: "High BPM while inactive",
      message: `BPM is ${latestBpm} with low activity recorded.`,
      recommended_action: "Sit down, hydrate, recheck the watch fit, and avoid intense activity if this repeats.",
      source: "wearable",
      timestamp: latest.timestamp,
    });
  }
  if ((latest.steps ?? 0) < 2500) {
    alerts.push({
      id: "derived-walk",
      severity: "info",
      title: "Movement is low",
      message: `Steps are at ${latest.steps ?? 0}.`,
      recommended_action: "Take a 10-minute walk if your body feels okay.",
      source: "wearable",
      timestamp: latest.timestamp,
    });
  }
  if (latest.sleep_hours != null && latest.sleep_hours < 6) {
    alerts.push({
      id: "derived-sleep",
      severity: "warning",
      title: "Short sleep detected",
      message: `Last sleep was ${latest.sleep_hours.toFixed(1)} hours.`,
      recommended_action: "Keep workout intensity easy and protect tonight's sleep window.",
      source: "wearable",
      timestamp: latest.timestamp,
    });
  }
  return alerts;
}

function deriveSyntheticAlerts(readings: DemoWatchPoint[]): AlertItem[] {
  const alerts: AlertItem[] = [];
  readings.forEach((item, index) => {
    if (item.event === "fall") {
      alerts.push({
        id: `demo-fall-${index}`,
        severity: "critical",
        title: "Possible fall or height drop",
        message: `Synthetic watch stream shows ${item.acceleration_g}g impact and ${item.altitude_delta_m}m altitude change.`,
        recommended_action: "Show emergency prompt: Are you okay? Notify contact if no response.",
        source: "synthetic demo",
        timestamp: item.timestamp,
      });
    }
    if (item.event === "stress") {
      alerts.push({
        id: `demo-stress-${index}`,
        severity: "warning",
        title: "Stress spike",
        message: `Stress ${item.stress_score}, BPM ${item.heart_rate}.`,
        recommended_action: "Take a deep breath for one minute.",
        source: "synthetic demo",
        timestamp: item.timestamp,
      });
    }
    if (item.event === "walk") {
      alerts.push({
        id: `demo-walk-${index}`,
        severity: "info",
        title: "Walk recovery",
        message: "Steps and active minutes are increasing after an alert.",
        recommended_action: "Continue light walking until BPM settles.",
        source: "synthetic demo",
        timestamp: item.timestamp,
      });
    }
  });
  return alerts;
}

export function TwinPage() {
  const navigate = useNavigate();
  const intakeForm = loadIntakeForm();
  const [age] = useState(numberFromDraft(intakeForm?.currentAge) ?? 34);
  const [targetAge] = useState(numberFromDraft(intakeForm?.targetTwinAge) ?? 65);
  const [activeTab, setActiveTab] = useState<Tab>("routine");
  const [intakeBiomarkers, setIntakeBiomarkers] = useState<IntakeBiomarkers>(() => loadIntakeBiomarkers());
  const [routinePlan, setRoutinePlan] = useState<RoutinePlanResponse | null>(() => loadCachedRoutinePlan());
  const [nutritionPlan, setNutritionPlan] = useState<NutritionPlanResponse | null>(() => loadCachedNutritionPlan());
  const [routineLoading, setRoutineLoading] = useState(false);
  const [nutritionLoading, setNutritionLoading] = useState(false);
  const [checkinSubmitting, setCheckinSubmitting] = useState(false);
  const [adaptiveMessage, setAdaptiveMessage] = useState("");
  const [negativeChoices, setNegativeChoices] = useState<NegativeChoice[]>([]);
  const [dailyNotes, setDailyNotes] = useState("");
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
    sleepHrs: numberFromDraft(intakeForm?.sleepHours) ?? 6.2,
    steps: numberFromDraft(intakeForm?.dailySteps) ?? 4800,
    heartRate: numberFromDraft(intakeForm?.pulseRate) ?? 78,
    stress: numberFromDraft(intakeForm?.stress) ?? 62,
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

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [activeTab]);

  useEffect(() => {
    if (routinePlan?.activities.length) {
      setRoutine(activitiesToRoutine(routinePlan.activities));
    }
  }, [routinePlan]);

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

  useEffect(() => {
    let cancelled = false;

    const hydrateBiomarkers = async () => {
      const latest = await fetchLatestBiomarkersFromDb();
      if (!latest || cancelled) return;
      setIntakeBiomarkers(latest);
      setBiomarkers((current) => ({
        ...current,
        hba1c: latest.hba1c ?? current.hba1c,
        systolic: latest.systolic ?? current.systolic,
        diastolic: latest.diastolic ?? current.diastolic,
        vitaminD: latest.vitaminD ?? current.vitaminD,
        b12: latest.b12 ?? current.b12,
      }));
    };

    hydrateBiomarkers();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setBiomarkers((current) => ({
      ...current,
      hba1c: intakeBiomarkers.hba1c ?? current.hba1c,
      systolic: intakeBiomarkers.systolic ?? current.systolic,
      diastolic: intakeBiomarkers.diastolic ?? current.diastolic,
      vitaminD: intakeBiomarkers.vitaminD ?? current.vitaminD,
      b12: intakeBiomarkers.b12 ?? current.b12,
    }));
  }, [intakeBiomarkers]);

  useEffect(() => {
    const syncCachedAdaptivePlan = () => {
      const nextRoutine = loadCachedRoutinePlan();
      const nextNutrition = loadCachedNutritionPlan();
      const pending = localStorage.getItem(ADAPTIVE_PLAN_PENDING_STORAGE_KEY) === "true";

      if (nextRoutine) setRoutinePlan(nextRoutine);
      if (nextNutrition) setNutritionPlan(nextNutrition);

      setRoutineLoading(pending && !nextRoutine);
      setNutritionLoading(pending && !nextNutrition);

      if (pending && nextRoutine && !nextNutrition) {
        setAdaptiveMessage("Routine is ready. Nutrition is still generating...");
      } else if (pending && !nextRoutine) {
        setAdaptiveMessage("AI is generating your routine and nutrition...");
      } else if (nextRoutine || nextNutrition) {
        setAdaptiveMessage("AI plan ready.");
      } else {
        setAdaptiveMessage("Submit intake details first to generate the adaptive AI plan.");
      }
    };

    syncCachedAdaptivePlan();
    window.addEventListener(ADAPTIVE_PLAN_UPDATED_EVENT, syncCachedAdaptivePlan);
    return () => window.removeEventListener(ADAPTIVE_PLAN_UPDATED_EVENT, syncCachedAdaptivePlan);
  }, []);

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
    if (checkinSubmitting) return;
    setRoutine((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, done: !item.done } : item)));
  };

  const refreshAdaptivePlan = async () => {
    const userId = await getSingleUserId();
    if (!userId) {
      setAdaptiveMessage("Submit intake details first to generate the adaptive AI plan.");
      return;
    }
    setRoutineLoading(true);
    setNutritionLoading(true);
    setAdaptiveMessage("Refreshing plan from the latest metrics...");
    const body = JSON.stringify({ metrics: buildMetricsPayload(biomarkers) });
    const routineRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/routine`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
    })
      .then(async (routineResponse) => {
        if (!routineResponse.ok) throw new Error(apiErrorText(await routineResponse.text(), "OpenAI routine generation failed."));
        const nextRoutine = (await routineResponse.json()) as RoutinePlanResponse;
        localStorage.setItem(ADAPTIVE_ROUTINE_STORAGE_KEY, JSON.stringify(nextRoutine));
        setRoutinePlan(nextRoutine);
        return nextRoutine;
      })
      .finally(() => setRoutineLoading(false));
    const nutritionRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/nutrition`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
    })
      .then(async (nutritionResponse) => {
        if (!nutritionResponse.ok) throw new Error(apiErrorText(await nutritionResponse.text(), "OpenAI nutrition generation failed."));
        const nextNutrition = (await nutritionResponse.json()) as NutritionPlanResponse;
        localStorage.setItem(ADAPTIVE_NUTRITION_STORAGE_KEY, JSON.stringify(nextNutrition));
        setNutritionPlan(nextNutrition);
      })
      .finally(() => setNutritionLoading(false));
    try {
      const nextRoutine = await routineRequest;
      await nutritionRequest;
      setNegativeChoices([]);
      setDailyNotes("");
      setAdaptiveMessage(`Plan refreshed. Timeline: ${nextRoutine.timeline.estimated_weeks} weeks.`);
    } catch (error) {
      setAdaptiveMessage(error instanceof Error ? error.message : "OpenAI plan refresh failed.");
    }
  };

  const submitDailyCheckin = async () => {
    if (checkinSubmitting) return;
    const userId = await getSingleUserId();
    if (!userId) {
      setAdaptiveMessage("Submit intake details first to submit a check-in.");
      return;
    }
    const completed = routine.filter((item) => item.done).map((item, index) => item.id || `routine-${index}`);
    const skipped = routine.filter((item) => !item.done).map((item, index) => item.id || `routine-${index}`);
    setCheckinSubmitting(true);
    setRoutineLoading(true);
    setNutritionLoading(true);
    setAdaptiveMessage("AI is reviewing today and recalculating tomorrow's routine and nutrition...");
    try {
      const feedback = {
        completed_activity_ids: completed,
        skipped_activity_ids: skipped,
        negative_choices: negativeChoices,
        notes: dailyNotes || null,
      };
      const checkinPayload = {
        plan_date: routinePlan?.plan_date,
        metrics: buildMetricsPayload(biomarkers),
        feedback,
      };
      const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/checkin-log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(checkinPayload),
      });
      if (!response.ok) throw new Error(apiErrorText(await response.text(), "Could not save today's check-in."));
      const nextPlanDate = nextDateString(routinePlan?.plan_date || nutritionPlan?.plan_date);
      const nextPlanPayload = JSON.stringify({
        plan_date: nextPlanDate,
        metrics: buildMetricsPayload(biomarkers),
        previous_day: feedback,
      });
      const routineRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/routine`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: nextPlanPayload,
      })
        .then(async (routineResponse) => {
          if (!routineResponse.ok) throw new Error(apiErrorText(await routineResponse.text(), "OpenAI routine generation failed."));
          const nextRoutine = (await routineResponse.json()) as RoutinePlanResponse;
          localStorage.setItem(ADAPTIVE_ROUTINE_STORAGE_KEY, JSON.stringify(nextRoutine));
          setRoutinePlan(nextRoutine);
          setAdaptiveMessage("Routine updated. Nutrition is still recalculating...");
          return nextRoutine;
        })
        .finally(() => setRoutineLoading(false));
      const nutritionRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/nutrition`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: nextPlanPayload,
      })
        .then(async (nutritionResponse) => {
          if (!nutritionResponse.ok) throw new Error(apiErrorText(await nutritionResponse.text(), "OpenAI nutrition generation failed."));
          const nextNutrition = (await nutritionResponse.json()) as NutritionPlanResponse;
          localStorage.setItem(ADAPTIVE_NUTRITION_STORAGE_KEY, JSON.stringify(nextNutrition));
          setNutritionPlan(nextNutrition);
          setAdaptiveMessage("Routine and nutrition are updated for tomorrow.");
        })
        .finally(() => setNutritionLoading(false));
      const [routineResult, nutritionResult] = await Promise.allSettled([routineRequest, nutritionRequest]);
      if (routineResult.status === "rejected") {
        throw routineResult.reason instanceof Error ? routineResult.reason : new Error("OpenAI routine generation failed.");
      }
      if (nutritionResult.status === "rejected") {
        throw nutritionResult.reason instanceof Error ? nutritionResult.reason : new Error("OpenAI nutrition generation failed.");
      }
      const nextRoutine = routineResult.value;
      setNegativeChoices([]);
      setDailyNotes("");
      setAdaptiveMessage(`Tomorrow's plan is ready. Timeline: ${nextRoutine.timeline.estimated_weeks} weeks.`);
    } catch (error) {
      setAdaptiveMessage(error instanceof Error ? error.message : "OpenAI check-in plan generation failed.");
    } finally {
      setCheckinSubmitting(false);
      setRoutineLoading(false);
      setNutritionLoading(false);
    }
  };

  return (
    <div className="lt-shell lt-dashboard">
      <style>{appCss}</style>
      <TopNav age={age} activeTab={activeTab} setActiveTab={setActiveTab} onHome={() => navigate("/")} />

      {activeTab === "routine" ? (
        <RoutineTab
          age={age}
          routine={routine}
          biomarkers={biomarkers}
          clampedScore={clampedScore}
          doneCount={doneCount}
          routinePlan={routinePlan}
          adaptiveLoading={routineLoading || nutritionLoading}
          checkinSubmitting={checkinSubmitting}
          adaptiveMessage={adaptiveMessage}
          negativeChoices={negativeChoices}
          dailyNotes={dailyNotes}
          toggleRoutine={toggleRoutine}
          setNegativeChoices={setNegativeChoices}
          setDailyNotes={setDailyNotes}
          onRefreshPlan={refreshAdaptivePlan}
          onSubmitCheckin={submitDailyCheckin}
        />
      ) : null}

      {activeTab === "biomarkers" ? (
        <BiomarkersTab
          biomarkers={biomarkers}
          intakeBiomarkers={intakeBiomarkers}
          updateBio={updateBio}
          onAddDetails={() => navigate("/")}
        />
      ) : null}

      {activeTab === "nutrition" ? (
        <NutritionTab age={age} supplements={supplements} nutrition={nutritionPlan?.nutrition} plan={nutritionPlan} loading={nutritionLoading} />
      ) : null}

      {activeTab === "twin" ? <TwinTab clampedScore={clampedScore} routinePlan={routinePlan} /> : null}

      {activeTab === "alerts" ? <AlertsTab /> : null}

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

function BloodPressureInput({
  systolic,
  diastolic,
  onSystolicChange,
  onDiastolicChange,
}: {
  systolic: number;
  diastolic: number;
  onSystolicChange: (value: number) => void;
  onDiastolicChange: (value: number) => void;
}) {
  const systolicDiff = Math.abs(systolic - 120);
  const diastolicDiff = Math.abs(diastolic - 80);
  const combinedDiff = systolicDiff + diastolicDiff;
  const signalColor = combinedDiff <= 10 ? COLORS.accent : combinedDiff <= 24 ? COLORS.gold : COLORS.red;
  const pct = Math.min(100, Math.max(0, ((systolic - 90) / (180 - 90)) * 100));
  const optPct = Math.min(100, Math.max(0, ((120 - 90) / (180 - 90)) * 100));

  return (
    <div style={{ ...cardStyle, padding: "16px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 14, marginBottom: 10 }}>
        <div>
          <div style={{ color: COLORS.textPrimary, fontWeight: 700, fontSize: 14 }}>BP</div>
          <div style={{ color: COLORS.textMuted, fontSize: 11, marginTop: 2 }}>Normal target around 120/80</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: signalColor, boxShadow: `0 0 8px ${signalColor}` }} />
          <input
            aria-label="Systolic BP"
            type="number"
            value={systolic}
            onChange={(event) => onSystolicChange(Number(event.target.value))}
            style={{
              background: COLORS.surface,
              border: `1px solid ${COLORS.border}`,
              color: COLORS.textPrimary,
              borderRadius: 8,
              padding: "4px 8px",
              width: 62,
              fontSize: 14,
              fontWeight: 800,
              textAlign: "right",
              outline: "none",
            }}
          />
          <span style={{ color: COLORS.textMuted, fontSize: 13, fontWeight: 800 }}>/</span>
          <input
            aria-label="Diastolic BP"
            type="number"
            value={diastolic}
            onChange={(event) => onDiastolicChange(Number(event.target.value))}
            style={{
              background: COLORS.surface,
              border: `1px solid ${COLORS.border}`,
              color: COLORS.textPrimary,
              borderRadius: 8,
              padding: "4px 8px",
              width: 62,
              fontSize: 14,
              fontWeight: 800,
              textAlign: "right",
              outline: "none",
            }}
          />
          <span style={{ color: COLORS.textMuted, fontSize: 11, minWidth: 34 }}>mmHg</span>
        </div>
      </div>
      <div style={{ position: "relative", height: 8 }}>
        <ProgressBar value={pct} color={signalColor} />
        <div
          title="Optimal: 120/80"
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
        <span style={{ color: COLORS.textMuted, fontSize: 10 }}>90</span>
        <span style={{ color: COLORS.accent, fontSize: 10 }}>Optimal: 120/80 mmHg</span>
        <span style={{ color: COLORS.textMuted, fontSize: 10 }}>180</span>
      </div>
    </div>
  );
}

function HumanBmiOutline({
  label,
  bmi,
  color,
  ideal = false,
}: {
  label: string;
  bmi?: number;
  color: string;
  ideal?: boolean;
}) {
  const safeBmi = bmi ?? 23;
  const widthScale = Math.max(0.82, Math.min(1.34, safeBmi / 23));
  const shoulderWidth = 44 * widthScale;
  const waistWidth = 34 * widthScale;
  const hipWidth = 40 * widthScale;
  const center = 80;
  const bodyPath = [
    `M ${center - shoulderWidth / 2} 48`,
    `C ${center - shoulderWidth / 2 - 10} 64 ${center - waistWidth / 2 - 6} 88 ${center - waistWidth / 2} 104`,
    `C ${center - hipWidth / 2} 126 ${center - 22 * widthScale} 146 ${center - 17 * widthScale} 172`,
    `L ${center - 8 * widthScale} 172`,
    `C ${center - 8 * widthScale} 140 ${center - 4 * widthScale} 122 ${center} 112`,
    `C ${center + 4 * widthScale} 122 ${center + 8 * widthScale} 140 ${center + 8 * widthScale} 172`,
    `L ${center + 17 * widthScale} 172`,
    `C ${center + 22 * widthScale} 146 ${center + hipWidth / 2} 126 ${center + waistWidth / 2} 104`,
    `C ${center + waistWidth / 2 + 6} 88 ${center + shoulderWidth / 2 + 10} 64 ${center + shoulderWidth / 2} 48`,
  ].join(" ");

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
      <div style={{ ...cardStyle, width: 190, height: 240, display: "grid", placeItems: "center", borderColor: `${color}55`, boxShadow: ideal ? `0 0 34px ${color}22` : "none" }}>
        <svg width={150} height={205} viewBox="0 0 160 205" role="img" aria-label={`${label} BMI outline`}>
          <defs>
            <linearGradient id={`bodyFill-${ideal ? "ideal" : "current"}`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={`${color}44`} />
              <stop offset="100%" stopColor={`${color}08`} />
            </linearGradient>
          </defs>
          <circle cx={80} cy={27} r={17} fill={`${color}18`} stroke={color} strokeWidth={2.4} />
          <path d={bodyPath} fill={`url(#bodyFill-${ideal ? "ideal" : "current"})`} stroke={color} strokeWidth={2.8} strokeLinejoin="round" />
          <path d={`M ${center - shoulderWidth / 2} 54 C 42 72 36 88 33 108`} fill="none" stroke={`${color}AA`} strokeWidth={2.2} strokeLinecap="round" />
          <path d={`M ${center + shoulderWidth / 2} 54 C 118 72 124 88 127 108`} fill="none" stroke={`${color}AA`} strokeWidth={2.2} strokeLinecap="round" />
          <path d={`M ${center - 9 * widthScale} 171 L ${center - 11 * widthScale} 196`} stroke={`${color}AA`} strokeWidth={2.2} strokeLinecap="round" />
          <path d={`M ${center + 9 * widthScale} 171 L ${center + 11 * widthScale} 196`} stroke={`${color}AA`} strokeWidth={2.2} strokeLinecap="round" />
        </svg>
      </div>
      <div style={{ textAlign: "center" }}>
        <div style={{ color: COLORS.textPrimary, fontWeight: 800, fontSize: 14 }}>{label}</div>
        <div style={{ color, fontSize: 12, fontWeight: 900, marginTop: 4 }}>BMI {safeBmi.toFixed(1)}</div>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  unit,
  percent,
  color = COLORS.accent,
}: {
  icon: ReactNode;
  label: string;
  value: string | number;
  unit?: string;
  percent?: number;
  color?: string;
}) {
  return (
    <div style={{ ...cardStyle, padding: 16, animation: "countUp 0.5s ease forwards" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ color, display: "grid", placeItems: "center" }}>{icon}</div>
        {typeof percent === "number" ? (
          <div
            style={{
              fontSize: 10,
              fontWeight: 800,
              color: percent >= 80 ? COLORS.accent : percent >= 55 ? COLORS.gold : COLORS.red,
              background: percent >= 80 ? COLORS.accentDim : percent >= 55 ? COLORS.goldDim : COLORS.redDim,
              padding: "2px 8px",
              borderRadius: 99,
            }}
          >
            {percent}%
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

function DailyRoutineCard({ time, activity, duration, impact, done, strictRule, disabled = false, onToggle }: RoutineItem & { disabled?: boolean; onToggle: () => void }) {
  const impactColor = impact === "High" ? COLORS.accent : impact === "Med" ? COLORS.gold : COLORS.textMuted;

  return (
    <button
      onClick={onToggle}
      disabled={disabled}
      style={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        gap: 16,
        background: done ? COLORS.accentDim : COLORS.card,
        border: `1px solid ${done ? COLORS.accentMid : COLORS.border}`,
        borderRadius: 16,
        padding: "14px 18px",
        cursor: disabled ? "not-allowed" : "pointer",
        textAlign: "left",
        opacity: disabled ? 0.68 : 1,
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
        {strictRule ? (
          <div style={{ color: COLORS.gold, fontSize: 11, marginTop: 5, lineHeight: 1.45 }}>
            Rule: {strictRule}
          </div>
        ) : null}
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
        TASK COMPLETION
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
        {doneCount} of {total} tasks done
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

function PrimaryButton({ children, onClick, disabled = false }: { children: ReactNode; onClick?: () => void; disabled?: boolean }) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      style={{
        background: disabled ? COLORS.border : `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
        border: "none",
        color: disabled ? COLORS.textMuted : COLORS.bg,
        borderRadius: 14,
        padding: "14px 28px",
        fontSize: 14,
        fontWeight: 900,
        cursor: disabled ? "not-allowed" : "pointer",
        boxShadow: disabled ? "none" : `0 8px 30px ${COLORS.accent}33`,
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        opacity: disabled ? 0.7 : 1,
      }}
    >
      {children}
    </button>
  );
}

function GhostButton({ children, onClick, disabled = false }: { children: ReactNode; onClick?: () => void; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: COLORS.card,
        border: `1px solid ${COLORS.border}`,
        color: COLORS.textSecondary,
        borderRadius: 12,
        padding: "12px 22px",
        fontSize: 14,
        fontWeight: 700,
        cursor: disabled ? "not-allowed" : "pointer",
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        opacity: disabled ? 0.65 : 1,
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
  routine,
  biomarkers,
  clampedScore,
  doneCount,
  routinePlan,
  adaptiveLoading,
  checkinSubmitting,
  adaptiveMessage,
  negativeChoices,
  dailyNotes,
  toggleRoutine,
  setNegativeChoices,
  setDailyNotes,
  onRefreshPlan,
  onSubmitCheckin,
}: {
  age: number;
  routine: RoutineItem[];
  biomarkers: Biomarkers;
  clampedScore: number;
  doneCount: number;
  routinePlan: RoutinePlanResponse | null;
  adaptiveLoading: boolean;
  checkinSubmitting: boolean;
  adaptiveMessage: string;
  negativeChoices: NegativeChoice[];
  dailyNotes: string;
  toggleRoutine: (index: number) => void;
  setNegativeChoices: (choices: NegativeChoice[]) => void;
  setDailyNotes: (value: string) => void;
  onRefreshPlan: () => void;
  onSubmitCheckin: () => void;
}) {
  const controlsLocked = adaptiveLoading || checkinSubmitting;
  const negativeOptions = routinePlan?.negative_options || (Object.keys(NEGATIVE_LABELS) as NegativeChoice[]);
  const taskCompletionScore = routine.length ? Math.round((doneCount / routine.length) * 100) : 0;
  const sleepPercent = higherIsBetterPercent(biomarkers.sleepHrs, 8);
  const stepsPercent = higherIsBetterPercent(biomarkers.steps, 10000);
  const heartRatePercent = lowerIsBetterPercent(biomarkers.heartRate, 70, 110);
  const stressPercent = lowerIsBetterPercent(biomarkers.stress, 35, 100);
  const toggleNegativeChoice = (choice: NegativeChoice) => {
    if (controlsLocked) return;
    setNegativeChoices(
      negativeChoices.includes(choice)
        ? negativeChoices.filter((item) => item !== choice)
        : [...negativeChoices, choice],
    );
  };

  return (
    <div className="lt-page">
      <div className="lt-grid-two">
        <div>
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
              <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: 0 }}>Today's Protocol</h2>
              <GhostButton onClick={onRefreshPlan} disabled={controlsLocked}>
                <RefreshCw size={15} /> {adaptiveLoading ? "Generating..." : "Refresh AI plan"}
              </GhostButton>
            </div>
            <p style={{ color: COLORS.textSecondary, marginTop: 6, fontSize: 14 }}>
              Tailored for Pruthvi, {age} · {formatPlanDate(routinePlan?.plan_date)}
            </p>
            {routinePlan ? (
              <div style={{ ...cardStyle, marginTop: 16, padding: 16, borderColor: COLORS.accentMid }}>
                <div style={{ color: COLORS.accent, fontWeight: 900, fontSize: 12, textTransform: "uppercase", letterSpacing: 1.5 }}>
                  {routinePlan.strictness} plan
                </div>
                <p style={{ color: COLORS.textSecondary, margin: "8px 0 0", fontSize: 13, lineHeight: 1.5 }}>{routinePlan.summary}</p>
                <p style={{ color: COLORS.gold, margin: "8px 0 0", fontSize: 12, lineHeight: 1.5 }}>
                  Timeline: {routinePlan.timeline.estimated_weeks} weeks | Confidence: {routinePlan.timeline.confidence}
                </p>
              </div>
            ) : null}
            {adaptiveMessage ? <p style={{ color: COLORS.textMuted, marginTop: 10, fontSize: 12 }}>{adaptiveMessage}</p> : null}
            {checkinSubmitting ? (
              <div style={{ ...cardStyle, marginTop: 14, padding: 16, borderColor: COLORS.accentMid, background: COLORS.accentDim }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <RefreshCw size={18} style={{ color: COLORS.accent, animation: "spin 1s linear infinite" }} />
                  <div>
                    <div style={{ color: COLORS.textPrimary, fontWeight: 900, fontSize: 14 }}>AI is recalculating tomorrow's plan</div>
                    <div style={{ color: COLORS.textSecondary, fontSize: 12, marginTop: 4 }}>
                      Routine updates first. Nutrition refreshes in parallel and will replace automatically.
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: 14, height: 6, overflow: "hidden", borderRadius: 999, background: "rgba(255,255,255,0.08)" }}>
                  <div style={{ height: "100%", width: "66%", borderRadius: 999, background: `linear-gradient(90deg, ${COLORS.accent}, ${COLORS.blue})`, animation: "loading-sweep 1.45s ease-in-out infinite" }} />
                </div>
              </div>
            ) : null}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {routine.map((item, index) => (
              <DailyRoutineCard key={`${item.time}-${item.activity}`} {...item} disabled={controlsLocked} onToggle={() => toggleRoutine(index)} />
            ))}
          </div>
          <div style={{ ...cardStyle, borderRadius: 18, padding: 20, marginTop: 18 }}>
            <SectionLabel color={COLORS.red}>Things that should not have happened</SectionLabel>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
              {negativeOptions.map((choice) => {
                const active = negativeChoices.includes(choice);
                return (
                  <button
                    key={choice}
                    disabled={controlsLocked}
                    onClick={() => toggleNegativeChoice(choice)}
                    style={{
                      border: `1px solid ${active ? COLORS.red : COLORS.border}`,
                      background: active ? COLORS.redDim : COLORS.surface,
                      color: active ? COLORS.textPrimary : COLORS.textSecondary,
                      borderRadius: 999,
                      padding: "8px 12px",
                      fontSize: 12,
                      fontWeight: 800,
                      cursor: controlsLocked ? "not-allowed" : "pointer",
                      opacity: controlsLocked ? 0.62 : 1,
                    }}
                  >
                    {NEGATIVE_LABELS[choice]}
                  </button>
                );
              })}
            </div>
            <textarea
              value={dailyNotes}
              onChange={(event) => setDailyNotes(event.target.value)}
              disabled={controlsLocked}
              placeholder="Add context: what made you skip, cravings, pain, travel, stress, meal notes..."
              style={{
                width: "100%",
                minHeight: 96,
                border: `1px solid ${COLORS.border}`,
                background: COLORS.surface,
                color: COLORS.textPrimary,
                borderRadius: 14,
                padding: 14,
                resize: "vertical",
                outline: "none",
                font: "inherit",
                fontSize: 13,
                boxSizing: "border-box",
                cursor: controlsLocked ? "not-allowed" : "text",
                opacity: controlsLocked ? 0.65 : 1,
              }}
            />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, flexWrap: "wrap", marginTop: 14 }}>
              <p style={{ color: COLORS.textMuted, margin: 0, fontSize: 12, maxWidth: 520 }}>
                {routinePlan?.checkin_prompt || "Submit your completed checklist and misses so tomorrow can be recalculated."}
              </p>
              <PrimaryButton onClick={onSubmitCheckin} disabled={controlsLocked}>
                {checkinSubmitting ? (
                  <>
                    <RefreshCw size={15} style={{ animation: "spin 1s linear infinite" }} /> Calculating...
                  </>
                ) : (
                  "Submit day"
                )}
              </PrimaryButton>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <ScoreRing score={taskCompletionScore} doneCount={doneCount} total={routine.length} />
          <div className="lt-grid-half">
            <MetricCard icon={<Moon size={21} />} label="Sleep" value={biomarkers.sleepHrs} unit="hrs" percent={sleepPercent} color={COLORS.purple} />
            <MetricCard icon={<Activity size={21} />} label="Steps" value={`${(biomarkers.steps / 1000).toFixed(1)}k`} percent={stepsPercent} color={COLORS.gold} />
            <MetricCard icon={<HeartPulse size={21} />} label="Heart rate" value={biomarkers.heartRate} unit="bpm" percent={heartRatePercent} color={COLORS.red} />
            <MetricCard icon={<Zap size={21} />} label="Stress" value={biomarkers.stress} percent={stressPercent} color={COLORS.accent} />
          </div>
        </div>
      </div>
    </div>
  );
}

function BiomarkersTab({
  biomarkers,
  intakeBiomarkers,
  updateBio,
  onAddDetails,
}: {
  biomarkers: Biomarkers;
  intakeBiomarkers: IntakeBiomarkers;
  updateBio: (key: BiomarkerKey, value: number) => void;
  onAddDetails: () => void;
}) {
  const [updateMessage, setUpdateMessage] = useState("");
  const [savedBiomarkers, setSavedBiomarkers] = useState<IntakeBiomarkers>(intakeBiomarkers);
  const [analysis, setAnalysis] = useState<BiomarkerAnalysisResponse | null>(() => loadCachedBiomarkerAnalysis());
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState("");
  const hasAnyDetails = [
    intakeBiomarkers.hba1c,
    intakeBiomarkers.systolic,
    intakeBiomarkers.diastolic,
    intakeBiomarkers.vitaminD,
    intakeBiomarkers.b12,
  ].some((value) => typeof value === "number");

  useEffect(() => {
    setSavedBiomarkers(intakeBiomarkers);
  }, [intakeBiomarkers]);

  useEffect(() => {
    const syncCachedAnalysis = () => {
      const cached = loadCachedBiomarkerAnalysis();
      const pending = localStorage.getItem(ADAPTIVE_PLAN_PENDING_STORAGE_KEY) === "true";
      if (cached) {
        setAnalysis(cached);
        setAnalysisLoading(false);
        setAnalysisMessage("");
        return;
      }
      setAnalysisLoading(pending);
      setAnalysisMessage(pending ? "" : "Submit details from the home page to generate biomarker analysis.");
    };

    syncCachedAnalysis();
    window.addEventListener(ADAPTIVE_PLAN_UPDATED_EVENT, syncCachedAnalysis);
    return () => window.removeEventListener(ADAPTIVE_PLAN_UPDATED_EVENT, syncCachedAnalysis);
  }, []);

  const hasBiomarkerChanges =
    (typeof savedBiomarkers.hba1c === "number" && biomarkers.hba1c !== savedBiomarkers.hba1c) ||
    (typeof savedBiomarkers.systolic === "number" && biomarkers.systolic !== savedBiomarkers.systolic) ||
    (typeof savedBiomarkers.diastolic === "number" && biomarkers.diastolic !== savedBiomarkers.diastolic) ||
    (typeof savedBiomarkers.vitaminD === "number" && biomarkers.vitaminD !== savedBiomarkers.vitaminD) ||
    (typeof savedBiomarkers.b12 === "number" && biomarkers.b12 !== savedBiomarkers.b12);

  const saveBiomarkerUpdates = async () => {
    try {
      const saved = localStorage.getItem(INTAKE_STORAGE_KEY);
      const parsed = saved ? (JSON.parse(saved) as IntakeDraft) : {};
      const userId = await getSingleUserId();
      if (!userId) {
        setUpdateMessage("Submit details on the home page first.");
        return;
      }
      const form = {
        ...(parsed.form || {}),
        hba1c: String(biomarkers.hba1c || ""),
        bpSystolic: String(biomarkers.systolic || ""),
        bpDiastolic: String(biomarkers.diastolic || ""),
        vitaminD: String(biomarkers.vitaminD || ""),
        vitaminB12: String(biomarkers.b12 || ""),
      };
      const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/biomarkers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hba1c: biomarkers.hba1c,
          bp_systolic: biomarkers.systolic,
          bp_diastolic: biomarkers.diastolic,
          vitamin_d: biomarkers.vitaminD,
          vitamin_b12: biomarkers.b12,
        }),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Could not update biomarker values.");
      }
      localStorage.setItem(INTAKE_STORAGE_KEY, JSON.stringify({ ...parsed, form }));
      setSavedBiomarkers({
        hba1c: biomarkers.hba1c,
        systolic: biomarkers.systolic,
        diastolic: biomarkers.diastolic,
        vitaminD: biomarkers.vitaminD,
        b12: biomarkers.b12,
      });
      setUpdateMessage("Biomarker values updated.");
    } catch {
      setUpdateMessage("Could not update biomarker values.");
    }
  };

  if (!hasAnyDetails) {
    return (
      <div className="lt-page" style={{ maxWidth: 760 }}>
        <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: "0 0 8px" }}>Your Biomarker Panel</h2>
        <p style={{ color: COLORS.textSecondary, marginBottom: 24, fontSize: 14 }}>
          Add HbA1c, BP, Vitamin D, and Vitamin B12 details to see how far each value is from the normal range.
        </p>
        <div style={{ ...cardStyle, padding: 28, borderRadius: 20, textAlign: "center" }}>
          <div style={{ color: COLORS.gold, marginBottom: 12 }}>
            <TestTube2 size={34} />
          </div>
          <h3 style={{ color: COLORS.textPrimary, fontSize: 20, fontWeight: 900, margin: "0 0 8px" }}>No biomarker details yet</h3>
          <p style={{ color: COLORS.textSecondary, fontSize: 14, lineHeight: 1.7, margin: "0 auto 20px", maxWidth: 480 }}>
            Enter the following details first: HbA1c, BP, Vitamin D, and Vitamin B12.
          </p>
          <PrimaryButton onClick={onAddDetails}>Add biomarker details</PrimaryButton>
        </div>
      </div>
    );
  }

  return (
    <div className="lt-page" style={{ maxWidth: 900 }}>
      <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: "0 0 8px" }}>Your Biomarker Panel</h2>
      <p style={{ color: COLORS.textSecondary, marginBottom: 32, fontSize: 14 }}>
        These values come from your intake. Each tile shows how far the value sits from the normal target.
      </p>

      <BiomarkerSection color={COLORS.accent} title="Biomarkers" icon={<TestTube2 size={14} />}>
        {typeof intakeBiomarkers.hba1c === "number" ? (
          <BiomarkerInput label="HbA1c" value={biomarkers.hba1c} onChange={(value) => { updateBio("hba1c", value); setUpdateMessage(""); }} unit="%" min={4} max={9} optimal={5.0} sublabel="Normal target around 5.0%" />
        ) : null}
        {typeof intakeBiomarkers.systolic === "number" && typeof intakeBiomarkers.diastolic === "number" ? (
          <BloodPressureInput
            systolic={biomarkers.systolic}
            diastolic={biomarkers.diastolic}
            onSystolicChange={(value) => { updateBio("systolic", value); setUpdateMessage(""); }}
            onDiastolicChange={(value) => { updateBio("diastolic", value); setUpdateMessage(""); }}
          />
        ) : null}
        {typeof intakeBiomarkers.vitaminD === "number" ? (
          <BiomarkerInput label="Vitamin D" value={biomarkers.vitaminD} onChange={(value) => { updateBio("vitaminD", value); setUpdateMessage(""); }} unit="ng/mL" min={5} max={100} optimal={60} sublabel="Normal target around 60" />
        ) : null}
        {typeof intakeBiomarkers.b12 === "number" ? (
          <BiomarkerInput label="Vitamin B12" value={biomarkers.b12} onChange={(value) => { updateBio("b12", value); setUpdateMessage(""); }} unit="pg/mL" min={100} max={1200} optimal={700} sublabel="Normal target around 700" />
        ) : null}
      </BiomarkerSection>

      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap", marginBottom: 24 }}>
        <PrimaryButton onClick={saveBiomarkerUpdates} disabled={!hasBiomarkerChanges}>Update values</PrimaryButton>
        {updateMessage ? <span style={{ color: COLORS.accent, fontSize: 13, fontWeight: 700 }}>{updateMessage}</span> : null}
      </div>

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
        {analysisLoading ? (
          <p style={{ color: COLORS.textSecondary, fontSize: 14, margin: 0, lineHeight: 1.7 }}>
            Generating current biomarker analysis...
          </p>
        ) : analysis ? (
          <div style={{ color: COLORS.textSecondary, fontSize: 14, lineHeight: 1.7 }}>
            <p style={{ margin: "0 0 10px" }}>{analysis.summary}</p>
            {analysis.key_findings.length ? (
              <div style={{ marginBottom: 10 }}>
                <strong style={{ color: COLORS.textPrimary }}>Key findings</strong>
                <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                  {analysis.key_findings.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ) : null}
            {analysis.watch_items.length ? (
              <div style={{ marginBottom: 10 }}>
                <strong style={{ color: COLORS.textPrimary }}>Watch items</strong>
                <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                  {analysis.watch_items.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ) : null}
            {analysis.next_actions.length ? (
              <div>
                <strong style={{ color: COLORS.textPrimary }}>Next actions</strong>
                <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                  {analysis.next_actions.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <p style={{ color: COLORS.textSecondary, fontSize: 14, margin: 0, lineHeight: 1.7 }}>
            {analysisMessage || "Add biomarker values to generate current-situation analysis."}
          </p>
        )}
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

function NutritionTab({
  age,
  supplements,
  nutrition,
  plan,
  loading,
}: {
  age: number;
  supplements: Array<{ name: string; dose: string; reason: string; priority: string }>;
  nutrition?: AdaptiveNutrition;
  plan?: NutritionPlanResponse | null;
  loading?: boolean;
}) {
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

  if (nutrition) {
    const macroTargets = [
      { label: "Protein", target: `${nutrition.macro_distribution.protein_percent}%`, current: nutrition.macro_distribution.protein_percent, color: COLORS.accent },
      { label: "Carbs", target: `${nutrition.macro_distribution.carbs_percent}%`, current: nutrition.macro_distribution.carbs_percent, color: COLORS.gold },
      { label: "Fats", target: `${nutrition.macro_distribution.fats_percent}%`, current: nutrition.macro_distribution.fats_percent, color: COLORS.purple },
      { label: "Fibre", target: `${nutrition.macro_distribution.fiber_grams}g`, current: Math.min(100, nutrition.macro_distribution.fiber_grams * 2), color: COLORS.blue },
      { label: "Water", target: `${nutrition.macro_distribution.water_liters}L`, current: Math.min(100, nutrition.macro_distribution.water_liters * 25), color: COLORS.accent },
    ];

    return (
      <div className="lt-page" style={{ maxWidth: 1040 }}>
        <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: "0 0 8px" }}>Personalised Nutrition Stack</h2>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, flexWrap: "wrap", marginBottom: 32 }}>
          <p style={{ color: COLORS.textSecondary, margin: 0, fontSize: 14 }}>
            Composition-led Indian meal choices for Pruthvi, {age}. {plan ? `Plan date: ${formatPlanDate(plan.plan_date)}.` : ""}
          </p>
          {loading ? (
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, color: COLORS.accent, fontSize: 12, fontWeight: 900 }}>
              <RefreshCw size={14} style={{ animation: "spin 1s linear infinite" }} /> Generating nutrition...
            </div>
          ) : null}
        </div>

        <div className="lt-nutrition" style={{ marginBottom: 32 }}>
          <div>
            <SectionLabel color={COLORS.gold}>Vitamin and Supplement Guidance</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {nutrition.supplement_guidance.map((item) => {
                const priorityColor = item.priority === "critical" ? COLORS.red : item.priority === "high" ? COLORS.gold : item.priority === "avoid" ? COLORS.red : COLORS.accent;
                const priorityBackground = item.priority === "critical" || item.priority === "avoid" ? COLORS.redDim : item.priority === "high" ? COLORS.goldDim : COLORS.accentDim;
                return (
                  <div key={`${item.name}-${item.priority}`} style={{ ...cardStyle, borderRadius: 14, padding: "14px 18px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 14, alignItems: "flex-start" }}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 14, color: COLORS.textPrimary }}>{item.name}</div>
                        <div style={{ color: COLORS.textSecondary, fontSize: 12, marginTop: 5, lineHeight: 1.55 }}>{item.why}</div>
                        <div style={{ color: COLORS.textMuted, fontSize: 11, marginTop: 5 }}>{item.safety_note}</div>
                      </div>
                      <div style={{ textAlign: "right", minWidth: 90 }}>
                        <div style={{ fontWeight: 900, color: COLORS.accent, fontSize: 12 }}>{item.suggested_timing}</div>
                        <div style={{ fontSize: 9, fontWeight: 800, padding: "2px 8px", borderRadius: 99, marginTop: 4, color: priorityColor, background: priorityBackground, letterSpacing: 0.5 }}>
                          {item.priority.toUpperCase()}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ ...cardStyle, borderRadius: 14, padding: 16, marginTop: 16 }}>
              <div style={{ color: COLORS.textMuted, fontSize: 11, fontWeight: 700, letterSpacing: 1, marginBottom: 12, textTransform: "uppercase" }}>
                Daily Composition Targets
              </div>
              {macroTargets.map((macro) => (
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

          <div>
            <SectionLabel color={COLORS.accent}>Today's Diet Choices</SectionLabel>
            {nutrition.meals.map((meal) => (
              <div key={meal.meal} style={{ ...cardStyle, borderRadius: 14, padding: "16px 18px", marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 10, flexWrap: "wrap" }}>
                  <div style={{ fontWeight: 800, fontSize: 14, color: COLORS.textPrimary, textTransform: "capitalize" }}>{meal.meal}</div>
                  <div style={{ fontSize: 10, color: COLORS.accent, background: COLORS.accentDim, padding: "3px 8px", borderRadius: 99, fontWeight: 800 }}>
                    {meal.composition}
                  </div>
                </div>
                {[
                  ["North veg", meal.north_indian_veg],
                  ["North non-veg", meal.north_indian_non_veg],
                  ["South veg", meal.south_indian_veg],
                  ["South non-veg", meal.south_indian_non_veg],
                ].map(([label, items]) => (
                  <div key={label as string} style={{ marginTop: 8 }}>
                    <div style={{ color: COLORS.textMuted, fontSize: 10, fontWeight: 900, textTransform: "uppercase", letterSpacing: 1 }}>{label as string}</div>
                    <div style={{ color: COLORS.textSecondary, fontSize: 12, lineHeight: 1.6 }}>{(items as string[]).join(" | ")}</div>
                  </div>
                ))}
                <p style={{ color: COLORS.gold, fontSize: 11, lineHeight: 1.5, margin: "10px 0 0" }}>{meal.note}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="lt-page" style={{ maxWidth: 760 }}>
        <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: "0 0 8px" }}>Personalised Nutrition Stack</h2>
        <div style={{ ...cardStyle, padding: 26, marginTop: 24, display: "flex", alignItems: "center", gap: 12 }}>
          <RefreshCw size={18} style={{ color: COLORS.accent, animation: "spin 1s linear infinite" }} />
          <div>
            <div style={{ color: COLORS.textPrimary, fontWeight: 900, fontSize: 15 }}>Generating nutrition...</div>
            <div style={{ color: COLORS.textMuted, fontSize: 12, marginTop: 4 }}>Routine can load first while this finishes.</div>
          </div>
        </div>
      </div>
    );
  }

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

function TwinTab({ clampedScore, routinePlan }: { clampedScore: number; routinePlan: RoutinePlanResponse | null }) {
  const timelineText = routinePlan
    ? `${routinePlan.timeline.estimated_weeks} weeks · ${routinePlan.timeline.confidence} confidence`
    : "Timeline appears after your routine plan is generated";
  const form = loadIntakeForm();
  const currentBmi = calculateBmi(numberFromDraft(form?.height), numberFromDraft(form?.weight));
  const idealBmi = 23;

  return (
    <div className="lt-page" style={{ maxWidth: 920 }}>
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <div style={{ fontSize: 11, letterSpacing: 3, color: COLORS.accent, textTransform: "uppercase", fontWeight: 900, marginBottom: 12 }}>
          Ideal Twin
        </div>
        <h1 style={{ fontSize: 44, fontWeight: 950, letterSpacing: -2, lineHeight: 1.1, margin: 0 }}>
          You today vs{" "}
          <span
            style={{
              background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            ideal you
          </span>
        </h1>
        <p style={{ color: COLORS.textSecondary, marginTop: 12, fontSize: 16 }}>
          A simple view of where your current plan stands against the ideal routine, nutrition, recovery, and consistency state.
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 60, marginBottom: 34, flexWrap: "wrap" }}>
        <div style={{ textAlign: "center" }}>
          <HumanBmiOutline label="You Today" bmi={currentBmi} color={COLORS.blue} />
        </div>
        <div style={{ textAlign: "center", width: 220 }}>
          <div style={{ fontSize: 42, fontWeight: 950, color: COLORS.accent }}>{clampedScore}%</div>
          <div style={{ color: COLORS.textMuted, fontSize: 12, marginTop: 4, marginBottom: 10 }}>Current progress to ideal</div>
          <ProgressBar value={clampedScore} color={COLORS.accent} height={4} />
          <div style={{ color: COLORS.gold, fontSize: 12, fontWeight: 800, marginTop: 12 }}>{timelineText}</div>
          {routinePlan?.timeline.summary ? (
            <div style={{ color: COLORS.textMuted, fontSize: 11, lineHeight: 1.5, marginTop: 8 }}>{routinePlan.timeline.summary}</div>
          ) : null}
        </div>
        <div style={{ textAlign: "center" }}>
          <HumanBmiOutline label="Ideal You" bmi={idealBmi} color={COLORS.accent} ideal />
        </div>
      </div>

      <div style={{ ...cardStyle, borderRadius: 20, padding: 24 }}>
        <SectionLabel color={COLORS.accent}>Focus Path</SectionLabel>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 14 }}>
          {[
            { label: "Routine", text: "Complete today's checklist consistently." },
            { label: "Nutrition", text: "Follow the composition plan without making meals rigid." },
            { label: "Recovery", text: "Protect sleep, stress control, and daily movement." },
          ].map((item) => (
            <div key={item.label} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 14, padding: 16 }}>
              <div style={{ color: COLORS.textPrimary, fontWeight: 900, fontSize: 14 }}>{item.label}</div>
              <div style={{ color: COLORS.textMuted, fontSize: 12, lineHeight: 1.6, marginTop: 6 }}>{item.text}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ color: COLORS.textSecondary, fontSize: 12, fontWeight: 800 }}>Overall progress</span>
            <span style={{ color: COLORS.accent, fontSize: 12, fontWeight: 900 }}>{clampedScore}%</span>
          </div>
          <ProgressBar value={clampedScore} color={COLORS.accent} height={6} />
        </div>
      </div>
    </div>
  );
}

function severityColor(severity: AlertItem["severity"]) {
  if (severity === "critical") return COLORS.red;
  if (severity === "warning") return COLORS.gold;
  return COLORS.accent;
}

function ChartPanel({
  title,
  data,
  dataKey,
  color,
  unit,
  chart = "line",
}: {
  title: string;
  data: Array<Record<string, string | number | null>>;
  dataKey: string;
  color: string;
  unit?: string;
  chart?: "line" | "area";
}) {
  return (
    <div style={{ ...cardStyle, padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <div style={{ color: COLORS.textPrimary, fontWeight: 900, fontSize: 14 }}>{title}</div>
        {unit ? <div style={{ color: COLORS.textMuted, fontSize: 11, fontWeight: 800 }}>{unit}</div> : null}
      </div>
      <div style={{ width: "100%", height: 170 }}>
        <ResponsiveContainer>
          {chart === "area" ? (
            <AreaChart data={data}>
              <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="time" stroke={COLORS.textMuted} fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke={COLORS.textMuted} fontSize={10} tickLine={false} axisLine={false} width={32} />
              <Tooltip
                labelFormatter={(_, payload) => payload?.[0]?.payload?.tooltipTime || ""}
                contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 10, color: COLORS.textPrimary }}
              />
              <Area type="monotone" dataKey={dataKey} stroke={color} fill={`${color}33`} strokeWidth={2.5} connectNulls />
            </AreaChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="time" stroke={COLORS.textMuted} fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke={COLORS.textMuted} fontSize={10} tickLine={false} axisLine={false} width={32} />
              <Tooltip
                labelFormatter={(_, payload) => payload?.[0]?.payload?.tooltipTime || ""}
                contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 10, color: COLORS.textPrimary }}
              />
              <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2.5} dot={false} connectNulls />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AlertCard({ alert }: { alert: AlertItem }) {
  const color = severityColor(alert.severity);
  return (
    <div style={{ ...cardStyle, padding: 16, borderColor: `${color}66`, background: `${color}12` }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ color, background: `${color}22`, borderRadius: 12, padding: 8 }}>
          {alert.severity === "info" ? <Bell size={18} /> : <AlertTriangle size={18} />}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div style={{ color: COLORS.textPrimary, fontWeight: 900, fontSize: 14 }}>{alert.title}</div>
            <div style={{ color, fontSize: 10, fontWeight: 900, letterSpacing: 1, textTransform: "uppercase" }}>{alert.severity}</div>
          </div>
          <p style={{ color: COLORS.textSecondary, fontSize: 12, lineHeight: 1.55, margin: "6px 0 0" }}>{alert.message}</p>
          <p style={{ color: COLORS.textPrimary, fontSize: 12, lineHeight: 1.55, margin: "8px 0 0", fontWeight: 800 }}>
            {alert.recommended_action}
          </p>
          <div style={{ color: COLORS.textMuted, fontSize: 10, marginTop: 8 }}>
            {alert.source}
            {alert.timestamp ? ` | ${readingTimeLabel(alert.timestamp)}` : ""}
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertsTab() {
  const [readings, setReadings] = useState<WearableReading[]>([]);
  const [backendAlerts, setBackendAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [demoExpanded, setDemoExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadAlerts = async () => {
      setLoading(true);
      setMessage("");
      try {
        const userId = await getSingleUserId();
        if (!userId) {
          setMessage("Submit intake details first to read wearable alerts.");
          return;
        }
        const [readingsResponse, alertsResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/users/${userId}/wearable-readings?limit=60`),
          fetch(`${API_BASE_URL}/api/v1/users/${userId}/alerts`),
        ]);
        if (!readingsResponse.ok) throw new Error(await readingsResponse.text());
        const wearablePayload = (await readingsResponse.json()) as WearableReading[];
        const alertPayload = alertsResponse.ok ? (await alertsResponse.json()) as Array<{
          id: string;
          severity: AlertItem["severity"];
          title: string;
          message: string;
          recommended_action: string;
          source?: string | null;
          created_at?: string;
        }> : [];
        if (cancelled) return;
        setReadings(wearablePayload);
        setBackendAlerts(
          alertPayload.map((item) => ({
            id: item.id,
            severity: item.severity,
            title: item.title,
            message: item.message,
            recommended_action: item.recommended_action,
            source: item.source || "alert engine",
            timestamp: item.created_at,
          })),
        );
      } catch {
        if (!cancelled) setMessage("Could not load wearable alerts right now.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadAlerts();
    return () => {
      cancelled = true;
    };
  }, []);

  const chartData = wearableChartData(readings);
  const derivedAlerts = deriveWearableAlerts(readings);
  const allAlerts = [...derivedAlerts, ...backendAlerts].slice(0, 8);
  const latest = readings.slice().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
  const demoData = wearableChartData(SYNTHETIC_WATCH_DEMO, false);
  const demoAlerts = deriveSyntheticAlerts(SYNTHETIC_WATCH_DEMO);

  return (
    <div className="lt-page" style={{ maxWidth: 1120 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap", marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, margin: 0 }}>Wearable Alerts</h2>
          <p style={{ color: COLORS.textSecondary, marginTop: 8, fontSize: 14 }}>
            Smartwatch readings mapped into break, breath, walk, recovery, and safety alerts.
          </p>
        </div>
        <GhostButton onClick={() => window.location.reload()}>
          <RefreshCw size={15} /> Refresh
        </GhostButton>
      </div>

      {loading ? (
        <div style={{ ...cardStyle, padding: 22, display: "flex", alignItems: "center", gap: 12 }}>
          <RefreshCw size={18} style={{ color: COLORS.accent, animation: "spin 1s linear infinite" }} />
          <div style={{ color: COLORS.textSecondary, fontSize: 14 }}>Reading wearable stream and generating alerts...</div>
        </div>
      ) : null}

      {!loading && message ? (
        <div style={{ ...cardStyle, padding: 18, color: COLORS.textSecondary, marginBottom: 18 }}>{message}</div>
      ) : null}

      {!loading ? (
        <>
          <div className="lt-grid-cards" style={{ marginBottom: 20 }}>
            <MetricCard icon={<HeartPulse size={21} />} label="Latest BPM" value={latest?.heart_rate ?? latest?.resting_heart_rate ?? "--"} percent={latest?.heart_rate ? lowerIsBetterPercent(latest.heart_rate, 70, 120) : undefined} color={COLORS.red} />
            <MetricCard icon={<Wind size={21} />} label="Stress" value={latest?.stress_score != null ? Math.round(latest.stress_score) : "--"} percent={latest?.stress_score != null ? lowerIsBetterPercent(latest.stress_score, 35, 100) : undefined} color={COLORS.gold} />
            <MetricCard icon={<Activity size={21} />} label="Steps" value={latest?.steps ?? "--"} percent={latest?.steps != null ? higherIsBetterPercent(latest.steps, 10000) : undefined} color={COLORS.accent} />
          </div>

          <div className="lt-grid-two" style={{ alignItems: "start", marginBottom: 22 }}>
            <div className="lt-grid-half">
              <ChartPanel title="BPM" data={chartData} dataKey="bpm" color={COLORS.red} unit="bpm" />
              <ChartPanel title="Stress" data={chartData} dataKey="stress" color={COLORS.gold} unit="score" />
              <ChartPanel title="Steps" data={chartData} dataKey="steps" color={COLORS.accent} unit="steps" chart="area" />
              <ChartPanel title="Sleep" data={chartData} dataKey="sleep" color={COLORS.purple} unit="hours" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <SectionLabel color={COLORS.red}>Live Alert Stack</SectionLabel>
              {allAlerts.length ? allAlerts.map((alert) => <AlertCard key={`${alert.source}-${alert.id}`} alert={alert} />) : (
                <div style={{ ...cardStyle, padding: 18, color: COLORS.textSecondary, fontSize: 13 }}>
                  No active wearable alerts from the available readings.
                </div>
              )}
            </div>
          </div>

          <div style={{ ...cardStyle, padding: 18, borderColor: COLORS.purple + "66" }}>
            <button
              onClick={() => setDemoExpanded((current) => !current)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 16,
                background: "transparent",
                border: "none",
                color: COLORS.textPrimary,
                cursor: "pointer",
                padding: 0,
                textAlign: "left",
              }}
            >
              <div>
                <div style={{ color: COLORS.purple, fontWeight: 900, fontSize: 12, letterSpacing: 1.5, textTransform: "uppercase" }}>Demo Smartwatch Stream</div>
                <div style={{ color: COLORS.textSecondary, fontSize: 13, marginTop: 4 }}>Synthetic stress, walk, and fall signals for presentation mode.</div>
              </div>
              {demoExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>

            {demoExpanded ? (
              <div style={{ marginTop: 18 }}>
                <div className="lt-grid-half" style={{ marginBottom: 16 }}>
                  <ChartPanel title="Demo BPM" data={demoData} dataKey="bpm" color={COLORS.red} unit="bpm" />
                  <ChartPanel title="Demo Stress" data={demoData} dataKey="stress" color={COLORS.gold} unit="score" />
                  <ChartPanel title="Demo Steps" data={demoData} dataKey="steps" color={COLORS.accent} unit="steps" chart="area" />
                  <ChartPanel title="Demo Sleep" data={demoData} dataKey="sleep" color={COLORS.purple} unit="hours" />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {demoAlerts.map((alert) => <AlertCard key={alert.id} alert={alert} />)}
                </div>
              </div>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
