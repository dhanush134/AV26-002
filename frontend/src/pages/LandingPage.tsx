import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ActivitySquare,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  CloudUpload,
  Dna,
  FileSearch,
  HeartPulse,
  Sparkles,
  Target,
  Watch,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

const STORAGE_KEY = "lifetwin_intake_draft_v1";
const USER_STORAGE_KEY = "lifetwin_intake_user_id_v1";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type GeneticTrack = "nutrigenomics" | "fitnessGenetics" | "sleepRecoveryGenetics" | "stimulantProcessingGenetics";

type IntakeForm = {
  fullName: string;
  currentAge: string;
  height: string;
  weight: string;
  bodyComposition: string;
  pulseRate: string;
  stress: string;
  activity: string;
  exercise: string;
  bpSystolic: string;
  bpDiastolic: string;
  hba1c: string;
  dailySteps: string;
  fastingBloodSugar: string;
  lft: string;
  rft: string;
  lipidProfile: string;
  vitaminD: string;
  vitaminB12: string;
  ironFerritin: string;
  magnesium: string;
  sleepHours: string;
  tsh: string;
  cortisol: string;
  testosterone: string;
  targetTwinAge: string;
  nutrigenomics: boolean;
  fitnessGenetics: boolean;
  sleepRecoveryGenetics: boolean;
  stimulantProcessingGenetics: boolean;
  geneticsNotes: string;
};

type ExtractedField = {
  key: keyof IntakeForm;
  label: string;
  value: string;
  confidence: "High" | "Medium";
};

type SamsungDailyHealth = {
  steps?: number | null;
  active_time_seconds?: number | null;
  exercise_time_seconds?: number | null;
  avg_heart_rate?: number | null;
  stress_avg_score?: number | null;
  sleep_minutes?: number | null;
};

type SamsungBodyMeasurement = {
  type?: string;
  start_time?: string | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  body_fat_percent?: number | null;
  skeletal_muscle_mass?: number | null;
  muscle_mass?: number | null;
  vfa_level?: number | null;
};

type SamsungUploadResponse = {
  ai_twin_readiness?: {
    score?: number;
    level?: string;
  };
  storage?: {
    status?: string;
    already_imported?: boolean;
    saved_counts?: Record<string, number>;
    daily_summaries_updated?: number;
  };
  heart_rate?: {
    summary?: {
      avg_bpm?: number | null;
    };
  };
  steps?: {
    summary?: {
      total_steps_detected?: number | null;
    };
  };
  stress?: {
    summary?: {
      avg_score?: number | null;
    };
  };
  activity?: {
    day_summaries?: Array<{
      score?: number | null;
      active_time?: number | null;
      exercise_time?: number | null;
    }>;
  };
  sleep?: {
    detected?: boolean;
  };
  body_profile?: {
    measurements?: SamsungBodyMeasurement[];
  };
  daily_health?: SamsungDailyHealth[];
};

const defaultForm: IntakeForm = {
  fullName: "",
  currentAge: "",
  height: "",
  weight: "",
  bodyComposition: "",
  pulseRate: "",
  stress: "",
  activity: "",
  exercise: "",
  bpSystolic: "",
  bpDiastolic: "",
  hba1c: "",
  dailySteps: "",
  fastingBloodSugar: "",
  lft: "",
  rft: "",
  lipidProfile: "",
  vitaminD: "",
  vitaminB12: "",
  ironFerritin: "",
  magnesium: "",
  sleepHours: "",
  tsh: "",
  cortisol: "",
  testosterone: "",
  targetTwinAge: "",
  nutrigenomics: false,
  fitnessGenetics: false,
  sleepRecoveryGenetics: false,
  stimulantProcessingGenetics: false,
  geneticsNotes: "",
};

const manualFieldCount = [
  "fullName",
  "currentAge",
  "height",
  "weight",
  "bodyComposition",
  "pulseRate",
  "stress",
  "activity",
  "exercise",
  "bpSystolic",
  "bpDiastolic",
  "hba1c",
  "dailySteps",
  "fastingBloodSugar",
  "lft",
  "rft",
  "lipidProfile",
  "vitaminD",
  "vitaminB12",
  "ironFerritin",
  "magnesium",
  "sleepHours",
  "tsh",
  "cortisol",
  "testosterone",
  "targetTwinAge",
] as const;

const geneticCards: Array<{ key: GeneticTrack; title: string; copy: string }> = [
  {
    key: "nutrigenomics",
    title: "Nutrigenomics",
    copy: "Macro tolerance, methylation support, and micronutrient response.",
  },
  {
    key: "fitnessGenetics",
    title: "Fitness Genetics",
    copy: "VO2 response, recovery style, strength bias, and training adaptation.",
  },
  {
    key: "sleepRecoveryGenetics",
    title: "Sleep and Recovery Genetics",
    copy: "Chronotype, sleep pressure, inflammation, and overnight recovery tendencies.",
  },
  {
    key: "stimulantProcessingGenetics",
    title: "Alcohol and Caffeine Processing Genetics",
    copy: "Caffeine clearance, stimulant sensitivity, and alcohol metabolism clues.",
  },
];

function decodeFileToText(file: File) {
  return file.arrayBuffer().then((buffer) => new TextDecoder("utf-8", { fatal: false }).decode(buffer).replace(/\0/g, " "));
}

function capturePanel(text: string, markers: string[]) {
  const parts = markers.flatMap((marker) => {
    const match = text.match(new RegExp(`${marker}[^\\d]{0,24}(\\d+(?:\\.\\d+)?)`, "i"));
    return match ? [`${marker.toUpperCase()} ${match[1]}`] : [];
  });
  return parts.join(" | ");
}

function pushUnique(results: ExtractedField[], field: ExtractedField) {
  if (!results.some((item) => item.key === field.key)) {
    results.push(field);
  }
}

function extractFieldsFromText(text: string) {
  const results: ExtractedField[] = [];
  const normalized = text.replace(/\s+/g, " ");

  const directPatterns: Array<[keyof IntakeForm, string, RegExp]> = [
    ["height", "Height", /(?:height|ht)[^\d]{0,12}(\d+(?:\.\d+)?)/i],
    ["weight", "Weight", /(?:weight|wt)[^\d]{0,12}(\d+(?:\.\d+)?)/i],
    ["stress", "Stress", /(?:stress(?: score| level)?)[^\d]{0,16}(\d+(?:\.\d+)?)/i],
    ["activity", "Activity", /(?:activity(?: score| level)?)[^\d]{0,16}(\d+(?:\.\d+)?)/i],
    ["exercise", "Exercise", /(?:exercise(?: minutes| duration)?|workout(?: minutes)?)[^\d]{0,16}(\d+(?:\.\d+)?)/i],
    ["pulseRate", "Pulse rate", /(?:pulse rate|resting heart rate|heart rate)[^\d]{0,12}(\d+(?:\.\d+)?)/i],
    ["hba1c", "HbA1c", /(?:hba1c|hb1ac|glycated hemoglobin)[^\d]{0,12}(\d+(?:\.\d+)?)/i],
    ["dailySteps", "Daily steps", /(?:steps(?: per day| daily)?)[^\d]{0,12}(\d+(?:\.\d+)?)/i],
    ["fastingBloodSugar", "Fasting blood sugar", /(?:fasting blood sugar|fasting glucose|fbs)[^\d]{0,12}(\d+(?:\.\d+)?)/i],
    ["vitaminD", "Vitamin D", /(?:vitamin d|25-oh vitamin d)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["vitaminB12", "Vitamin B12", /(?:vitamin b12|b12)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["ironFerritin", "Iron/Ferritin", /(?:ferritin|serum iron|iron)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["magnesium", "Magnesium", /(?:magnesium)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["sleepHours", "Sleep hours", /(?:sleep(?: hours| duration)?)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["tsh", "TSH", /(?:tsh|thyroid stimulating hormone)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["cortisol", "Cortisol", /(?:cortisol)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
    ["testosterone", "Testosterone", /(?:testosterone)[^\d]{0,18}(\d+(?:\.\d+)?)/i],
  ];

  directPatterns.forEach(([key, label, pattern]) => {
    const match = normalized.match(pattern);
    if (match?.[1]) {
      pushUnique(results, { key, label, value: match[1], confidence: "High" });
    }
  });

  const bpMatch = normalized.match(/(?:bp|blood pressure)[^\d]{0,12}(\d{2,3})\s*[\/-]\s*(\d{2,3})/i);
  if (bpMatch) {
    pushUnique(results, { key: "bpSystolic", label: "Systolic BP", value: bpMatch[1], confidence: "High" });
    pushUnique(results, { key: "bpDiastolic", label: "Diastolic BP", value: bpMatch[2], confidence: "High" });
  }

  const lipidProfile = capturePanel(normalized, ["ldl", "hdl", "triglycerides", "total cholesterol"]);
  if (lipidProfile) {
    pushUnique(results, { key: "lipidProfile", label: "Lipid profile", value: lipidProfile, confidence: "Medium" });
  }

  const lft = capturePanel(normalized, ["alt", "ast", "alp", "bilirubin"]);
  if (lft) {
    pushUnique(results, { key: "lft", label: "LFT", value: lft, confidence: "Medium" });
  }

  const rft = capturePanel(normalized, ["creatinine", "urea", "egfr", "bun"]);
  if (rft) {
    pushUnique(results, { key: "rft", label: "RFT", value: rft, confidence: "Medium" });
  }

  const bodyComposition = capturePanel(normalized, ["body fat", "muscle mass", "bmi", "visceral fat"]);
  if (bodyComposition) {
    pushUnique(results, { key: "bodyComposition", label: "Body composition", value: bodyComposition, confidence: "Medium" });
  }

  return results;
}

function applyExtractedFields(current: IntakeForm, fields: ExtractedField[]) {
  const next = { ...current };
  fields.forEach((field) => {
    next[field.key] = field.value as never;
  });
  return next;
}

function formatNumber(value: number | null | undefined, digits = 0) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return digits > 0 ? value.toFixed(digits) : String(Math.round(value));
}

function latestDailyHealth(days: SamsungDailyHealth[] | undefined) {
  return days?.length ? days[days.length - 1] : undefined;
}

function latestMeasurement(measurements: SamsungBodyMeasurement[] | undefined, predicate: (item: SamsungBodyMeasurement) => boolean) {
  return measurements?.filter(predicate).sort((a, b) => String(b.start_time || "").localeCompare(String(a.start_time || "")))[0];
}

function bodyCompositionText(measurement: SamsungBodyMeasurement | undefined) {
  if (!measurement) return "";
  const parts = [
    typeof measurement.body_fat_percent === "number" ? `Body fat ${formatNumber(measurement.body_fat_percent, 1)}%` : "",
    typeof measurement.skeletal_muscle_mass === "number" ? `Skeletal muscle ${formatNumber(measurement.skeletal_muscle_mass, 1)} kg` : "",
    typeof measurement.muscle_mass === "number" ? `Muscle mass ${formatNumber(measurement.muscle_mass, 1)} kg` : "",
    typeof measurement.vfa_level === "number" ? `VFA ${formatNumber(measurement.vfa_level)}` : "",
  ].filter(Boolean);
  return parts.join(" | ");
}

export function LandingPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<IntakeForm>(defaultForm);
  const [wearableMessage, setWearableMessage] = useState("");
  const [wearableLoading, setWearableLoading] = useState(false);
  const [reportMessage, setReportMessage] = useState("");
  const [saveMessage, setSaveMessage] = useState("");
  const [reportName, setReportName] = useState("");
  const [geneticUploads, setGeneticUploads] = useState<Record<GeneticTrack, string>>({
    nutrigenomics: "",
    fitnessGenetics: "",
    sleepRecoveryGenetics: "",
    stimulantProcessingGenetics: "",
  });
  const [extractedFields, setExtractedFields] = useState<ExtractedField[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved) as { form?: IntakeForm; reportName?: string; geneticUploads?: Record<GeneticTrack, string> };
      if (parsed.form) setForm({ ...defaultForm, ...parsed.form });
      if (parsed.reportName) setReportName(parsed.reportName);
      if (parsed.geneticUploads) setGeneticUploads((current) => ({ ...current, ...parsed.geneticUploads }));
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ form, reportName, geneticUploads }));
  }, [form, reportName, geneticUploads]);

  const filledManualFields = manualFieldCount.filter((key) => String(form[key]).trim().length > 0).length;
  const completion = Math.round((filledManualFields / manualFieldCount.length) * 100);

  const updateField = <K extends keyof IntakeForm>(key: K, value: IntakeForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
    setSaveMessage("");
  };

  const getOrCreateIntakeUser = async (current: IntakeForm) => {
    const existingUserId = localStorage.getItem(USER_STORAGE_KEY);
    if (existingUserId) return existingUserId;

    const response = await fetch(`${API_BASE_URL}/api/v1/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: current.fullName.trim() || "Samsung Health User",
        age: Number(current.currentAge) || 34,
        gender: null,
        height_cm: Number(current.height) || 170,
        weight_kg: Number(current.weight) || 70,
        target_age: Number(current.targetTwinAge) || 75,
      }),
    });
    if (!response.ok) {
      throw new Error("Could not create a user for the wearable import.");
    }
    const user = (await response.json()) as { id: string };
    localStorage.setItem(USER_STORAGE_KEY, user.id);
    return user.id;
  };

  const connectWearable = async () => {
    setWearableLoading(true);
    setWearableMessage("Reading C:\\Users\\dhanu\\Downloads\\Data.zip through the backend and syncing Samsung Health data...");
    setSaveMessage("");
    try {
      const userId = await getOrCreateIntakeUser(form);
      const params = new URLSearchParams({
        user_id: userId,
        include_raw_records: "true",
        include_samples: "false",
        sample_limit: "1000",
      });
      const response = await fetch(`${API_BASE_URL}/api/health-imports/samsung/upload?${params.toString()}`, {
        method: "POST",
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Samsung Health import failed.");
      }
      const payload = (await response.json()) as SamsungUploadResponse;
      const latestDay = latestDailyHealth(payload.daily_health);
      const heightMeasurement = latestMeasurement(payload.body_profile?.measurements, (item) => typeof item.height_cm === "number");
      const weightMeasurement = latestMeasurement(payload.body_profile?.measurements, (item) => typeof item.weight_kg === "number");
      const compositionMeasurement = latestMeasurement(
        payload.body_profile?.measurements,
        (item) =>
          typeof item.body_fat_percent === "number" ||
          typeof item.skeletal_muscle_mass === "number" ||
          typeof item.muscle_mass === "number" ||
          typeof item.vfa_level === "number",
      );
      const activitySummary = payload.activity?.day_summaries?.[payload.activity.day_summaries.length - 1];
      const nextFields: Partial<IntakeForm> = {
        height: formatNumber(heightMeasurement?.height_cm ?? weightMeasurement?.height_cm, 1),
        weight: formatNumber(weightMeasurement?.weight_kg, 1),
        bodyComposition: bodyCompositionText(compositionMeasurement || weightMeasurement),
        pulseRate: formatNumber(latestDay?.avg_heart_rate ?? payload.heart_rate?.summary?.avg_bpm),
        stress: formatNumber(latestDay?.stress_avg_score ?? payload.stress?.summary?.avg_score),
        activity: formatNumber(activitySummary?.score),
        exercise: formatNumber(((latestDay?.exercise_time_seconds ?? activitySummary?.exercise_time ?? 0) || 0) / 60),
        dailySteps: formatNumber(latestDay?.steps ?? payload.steps?.summary?.total_steps_detected),
        sleepHours: formatNumber(typeof latestDay?.sleep_minutes === "number" ? latestDay.sleep_minutes / 60 : null, 1),
      };
      setForm((current) => {
        const next = { ...current };
        (Object.entries(nextFields) as Array<[keyof IntakeForm, string]>).forEach(([key, value]) => {
          if (value) next[key] = value as never;
        });
        return next;
      });

      const savedCounts = payload.storage?.saved_counts || {};
      const savedTotal = Object.values(savedCounts).reduce((sum, count) => sum + count, 0);
      const storageText = payload.storage?.already_imported
        ? "This ZIP was already imported, so existing stored records were reused."
        : `Stored ${savedTotal} normalized records and updated ${payload.storage?.daily_summaries_updated || 0} daily summaries.`;
      setWearableMessage(
        `${storageText} Manual intake was filled from Samsung Health fields: pulse, stress, activity, exercise, steps, sleep if available, height, weight, and body composition.`,
      );
    } catch (error) {
      setWearableMessage(error instanceof Error ? error.message : "Samsung Health wearable sync failed.");
    } finally {
      setWearableLoading(false);
    }
  };

  const handleReportUpload = async (file: File | undefined) => {
    if (!file) return;
    setReportName(file.name);
    setReportMessage("Scanning uploaded report...");
    try {
      const text = await decodeFileToText(file);
      const fields = extractFieldsFromText(text);
      setExtractedFields(fields);
      if (fields.length) {
        setForm((current) => applyExtractedFields(current, fields));
        setReportMessage(`Confirmed ${fields.length} usable data points from ${file.name} and filled the matching fields below.`);
      } else {
        setReportMessage(`The file was uploaded, but no clear lab values were confirmed in-browser. The intake is ready for a deeper AI document parser connection.`);
      }
    } catch {
      setExtractedFields([]);
      setReportMessage("The file was uploaded, but it could not be decoded in-browser. A backend document parser will make this more robust.");
    }
    setSaveMessage("");
  };

  const handleGeneticUpload = (track: GeneticTrack, file: File | undefined) => {
    if (!file) return;
    setGeneticUploads((current) => ({ ...current, [track]: file.name }));
    updateField(track, true as IntakeForm[typeof track]);
  };

  const saveDraft = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ form, reportName, geneticUploads }));
    setSaveMessage("Your intake draft has been saved in this browser. The twin will become more accurate as you keep adding more verified data.");
  };

  return (
    <main className="min-h-screen bg-life-grid bg-[size:44px_44px]">
      <section className="page-wrap py-6 sm:py-8">
        <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(280px,0.75fr)]">
          <Card className="!p-0 overflow-hidden">
            <div className="relative p-5 sm:p-6">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.16),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(96,165,250,0.13),transparent_30%)]" />
              <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="max-w-3xl">
                  <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100">
                    <Sparkles size={14} />
                    Ideal Twin Intake
                  </div>
                  <div className="mt-4 flex items-start gap-3 sm:gap-4">
                    <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-emerald-300 to-blue-400 text-slate-950 shadow-glow sm:h-12 sm:w-12">
                      <ActivitySquare size={24} />
                    </div>
                    <div>
                      <h1 className="max-w-3xl text-2xl font-extrabold leading-tight text-white sm:text-4xl">
                        Build your ideal future twin.
                      </h1>
                      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">
                        Add current health, labs, wearable trends, and genetics so LifeTwin can model a sharper future version of you.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="hidden gap-2 sm:grid sm:grid-cols-3 lg:min-w-72 lg:grid-cols-1">
                  <SummaryChip icon={<HeartPulse size={17} className="text-rose-200" />} label="Biomarkers" value="20+" />
                  <SummaryChip icon={<Watch size={17} className="text-cyan-200" />} label="Wearables" value="Auto-fill" />
                  <SummaryChip icon={<BrainCircuit size={17} className="text-emerald-200" />} label="Reports" value="AI assisted" />
                </div>
              </div>
            </div>
          </Card>

          <Card className="!p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Profile completeness</p>
                <h2 className="mt-2 text-xl font-semibold text-white">Intake progress</h2>
              </div>
              <p className="text-4xl font-extrabold leading-none text-white">{completion}%</p>
            </div>
            <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-300 via-cyan-300 to-blue-400 transition-[width] duration-500"
                style={{ width: `${completion}%` }}
              />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                <p className="text-slate-500">Filled</p>
                <p className="mt-1 font-semibold text-white">
                  {filledManualFields}/{manualFieldCount.length} fields
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                <p className="text-slate-500">Next</p>
                <p className="mt-1 font-semibold text-white">Wearables or labs</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              Start with what you know. Import wearable or report data whenever it is ready.
            </p>
          </Card>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <Card title="1. Manual Health Intake">
            <p className="mb-5 text-sm leading-7 text-slate-300">
              Start with manual entry. You do not need every field to continue, but each confirmed value sharpens the model.
            </p>

            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Full name" value={form.fullName} onChange={(value) => updateField("fullName", value)} placeholder="Aarav Mehta" />
              <FormField label="Current age" type="number" value={form.currentAge} onChange={(value) => updateField("currentAge", value)} placeholder="34" />
              <FormField label="Height (cm)" type="number" value={form.height} onChange={(value) => updateField("height", value)} placeholder="172" />
              <FormField label="Weight (kg)" type="number" value={form.weight} onChange={(value) => updateField("weight", value)} placeholder="74" />
              <FormField label="Body composition" value={form.bodyComposition} onChange={(value) => updateField("bodyComposition", value)} placeholder="Body fat 18% | Muscle mass 31 kg | BMI 25.0" />
              <FormField label="Pulse rate (bpm)" type="number" value={form.pulseRate} onChange={(value) => updateField("pulseRate", value)} placeholder="64" />
              <FormField label="Stress score" type="number" value={form.stress} onChange={(value) => updateField("stress", value)} placeholder="28" />
              <FormField label="Activity score" type="number" value={form.activity} onChange={(value) => updateField("activity", value)} placeholder="82" />
              <FormField label="Exercise minutes" type="number" value={form.exercise} onChange={(value) => updateField("exercise", value)} placeholder="46" />
              <div className="grid grid-cols-2 gap-3">
                <FormField label="BP systolic" type="number" value={form.bpSystolic} onChange={(value) => updateField("bpSystolic", value)} placeholder="118" />
                <FormField label="BP diastolic" type="number" value={form.bpDiastolic} onChange={(value) => updateField("bpDiastolic", value)} placeholder="76" />
              </div>
              <FormField label="HbA1c (%)" type="number" value={form.hba1c} onChange={(value) => updateField("hba1c", value)} placeholder="5.3" />
              <FormField label="Daily steps" type="number" value={form.dailySteps} onChange={(value) => updateField("dailySteps", value)} placeholder="9200" />
              <FormField label="Fasting blood sugar (mg/dL)" type="number" value={form.fastingBloodSugar} onChange={(value) => updateField("fastingBloodSugar", value)} placeholder="92" />
              <FormField label="Vitamin D (ng/mL)" type="number" value={form.vitaminD} onChange={(value) => updateField("vitaminD", value)} placeholder="34" />
              <FormField label="Vitamin B12 (pg/mL)" type="number" value={form.vitaminB12} onChange={(value) => updateField("vitaminB12", value)} placeholder="540" />
              <FormField label="Iron / Ferritin" value={form.ironFerritin} onChange={(value) => updateField("ironFerritin", value)} placeholder="Ferritin 72 ng/mL" />
              <FormField label="Magnesium" value={form.magnesium} onChange={(value) => updateField("magnesium", value)} placeholder="2.0 mg/dL" />
              <FormField label="Sleep hours" type="number" value={form.sleepHours} onChange={(value) => updateField("sleepHours", value)} placeholder="7.4" />
              <FormField label="TSH" value={form.tsh} onChange={(value) => updateField("tsh", value)} placeholder="2.1" />
              <FormField label="Cortisol" value={form.cortisol} onChange={(value) => updateField("cortisol", value)} placeholder="13.2" />
              <FormField label="Testosterone" value={form.testosterone} onChange={(value) => updateField("testosterone", value)} placeholder="560" />
            </div>

            <div className="mt-4 grid gap-4">
              <TextAreaField label="LFT" value={form.lft} onChange={(value) => updateField("lft", value)} placeholder="ALT 24 | AST 22 | Bilirubin 0.8" />
              <TextAreaField label="RFT" value={form.rft} onChange={(value) => updateField("rft", value)} placeholder="Creatinine 0.9 | Urea 26 | eGFR 104" />
              <TextAreaField label="Lipid profile" value={form.lipidProfile} onChange={(value) => updateField("lipidProfile", value)} placeholder="LDL 96 | HDL 58 | Triglycerides 110 | Total cholesterol 176" />
            </div>
          </Card>

          <div className="space-y-6">
            <Card title="2. Auto-fill from Wearables">
              <p className="text-sm leading-7 text-slate-300">
                Use this when a watch or wearable is connected. For now, only fields that are realistically wearable-driven
                are auto-filled here: stress, activity, exercise, pulse rate, daily steps, sleep hours, and body profile
                metrics such as height, weight, and body composition.
              </p>
              <Button className="mt-5" onClick={connectWearable} disabled={wearableLoading}>
                {wearableLoading ? "Fetching Samsung Health..." : "Fetch from wearables"} <Watch size={18} />
              </Button>
              {wearableMessage ? <StatusNote tone={wearableLoading ? "info" : "success"}>{wearableMessage}</StatusNote> : null}
            </Card>

            <Card title="3. Upload Blood Reports and Health Files">
              <p className="text-sm leading-7 text-slate-300">
                Upload PDF, PPT, CSV, DOC, or text-based health reports. The intake assistant tries to confirm recognizable
                data points and fills the matching boxes automatically.
              </p>
              <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-cyan-300/25 bg-cyan-300/5 px-5 py-8 text-center transition hover:bg-cyan-300/10">
                <CloudUpload className="h-8 w-8 text-cyan-200" />
                <span className="mt-3 text-base font-semibold text-white">Upload lab report or blood test file</span>
                <span className="mt-2 text-sm text-slate-400">PDF, PPT, CSV, TXT, or any other exported report format</span>
                <input
                  className="hidden"
                  type="file"
                  accept=".pdf,.ppt,.pptx,.doc,.docx,.csv,.txt,.json,.xlsx,.xls,image/*"
                  onChange={(event) => handleReportUpload(event.target.files?.[0])}
                />
              </label>
              {reportName ? <p className="mt-4 text-sm text-slate-400">Latest file: {reportName}</p> : null}
              {reportMessage ? <StatusNote tone="info">{reportMessage}</StatusNote> : null}
              {extractedFields.length ? (
                <div className="mt-5 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <FileSearch size={16} className="text-emerald-200" />
                    Confirmed values
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {extractedFields.map((field) => (
                      <div key={field.key} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-white">{field.label}</p>
                            <p className="mt-1 text-sm text-slate-300">{field.value}</p>
                          </div>
                          <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-100">
                            {field.confidence}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </Card>
          </div>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <Card title="4. Genetics Uploads">
            <p className="mb-5 text-sm leading-7 text-slate-300">
              Switch on the genetics layers you have. You can add uploads now and refine with notes whenever needed.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              {geneticCards.map((card) => (
                <div key={card.key} className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={form[card.key]}
                      onChange={(event) => updateField(card.key, event.target.checked as IntakeForm[typeof card.key])}
                      className="mt-1 h-4 w-4 rounded border-white/15 bg-transparent text-cyan-300"
                    />
                    <div>
                      <p className="font-semibold text-white">{card.title}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">{card.copy}</p>
                    </div>
                  </label>
                  <label className="mt-4 flex cursor-pointer items-center justify-between rounded-2xl border border-dashed border-white/10 bg-black/10 px-4 py-3 text-sm text-slate-300 transition hover:border-cyan-300/25 hover:bg-cyan-300/5">
                    <span>{geneticUploads[card.key] || "Upload supporting file"}</span>
                    <Dna size={16} className="text-cyan-200" />
                    <input
                      className="hidden"
                      type="file"
                      accept=".pdf,.ppt,.pptx,.doc,.docx,.csv,.txt,.json,image/*"
                      onChange={(event) => handleGeneticUpload(card.key, event.target.files?.[0])}
                    />
                  </label>
                </div>
              ))}
            </div>
            <TextAreaField
              label="Genetics notes"
              value={form.geneticsNotes}
              onChange={(value) => updateField("geneticsNotes", value)}
              placeholder="Anything you already know about caffeine sensitivity, training response, food intolerances, recovery, or nutrient handling."
              className="mt-5"
            />
          </Card>

          <Card title="5. Ideal Twin Target">
            <div className="rounded-3xl border border-emerald-300/20 bg-emerald-300/10 p-5">
              <div className="flex items-center gap-3">
                <Target className="h-6 w-6 text-emerald-200" />
                <p className="font-semibold text-emerald-100">Set the age of your idealistic twin</p>
              </div>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                This tells the twin what future state it should optimize toward. It is the age at which you want your ideal
                healthy version to exist and stay functional.
              </p>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_auto]">
              <FormField
                label="Target age for your ideal twin"
                type="number"
                value={form.targetTwinAge}
                onChange={(value) => updateField("targetTwinAge", value)}
                placeholder="75"
              />
              <div className="flex items-end">
                <Button className="w-full sm:w-auto" onClick={saveDraft}>
                  Save intake <CheckCircle2 size={18} />
                </Button>
              </div>
            </div>

            {saveMessage ? <StatusNote tone="success">{saveMessage}</StatusNote> : null}

            <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-sm font-semibold text-white">What happens next</p>
              <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
                <p>1. Fill as much as you know manually.</p>
                <p>2. Pull wearable-friendly metrics with one click.</p>
                <p>3. Upload lab files so the intake assistant can confirm extra markers.</p>
                <p>4. Add genetics inputs to personalize nutrition, recovery, and stimulant handling.</p>
                <p>5. Save the intake, then continue to the rest of the twin workflow.</p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button onClick={() => navigate("/twin")}>
                Continue to your twin <ArrowRight size={18} />
              </Button>
            </div>
          </Card>
        </div>
      </section>
    </main>
  );
}

function SummaryChip({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-3 py-2.5">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/10">{icon}</span>
      <div className="min-w-0">
        <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
        <p className="truncate text-sm font-semibold text-white">{value}</p>
      </div>
    </div>
  );
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "number";
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-slate-300">{label}</span>
      <input className="field" type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </label>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  className = "",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <label className={className}>
      <span className="mb-2 block text-sm font-medium text-slate-300">{label}</span>
      <textarea
        className="field min-h-24 resize-y"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function StatusNote({ children, tone }: { children: React.ReactNode; tone: "success" | "info" }) {
  const classes =
    tone === "success"
      ? "mt-4 rounded-2xl border border-emerald-300/25 bg-emerald-300/10 p-4 text-sm text-emerald-100"
      : "mt-4 rounded-2xl border border-cyan-300/25 bg-cyan-300/10 p-4 text-sm text-cyan-100";
  return <p className={classes}>{children}</p>;
}
