import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ActivitySquare,
  BrainCircuit,
  HeartPulse,
  RefreshCw,
  Sparkles,
  Watch,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

const STORAGE_KEY = "lifetwin_intake_draft_v1";
const USER_STORAGE_KEY = "lifetwin_intake_user_id_v1";
const ADAPTIVE_ROUTINE_STORAGE_KEY = "lifetwin_adaptive_routine_v1";
const ADAPTIVE_NUTRITION_STORAGE_KEY = "lifetwin_adaptive_nutrition_v1";
const BIOMARKER_ANALYSIS_STORAGE_KEY = "lifetwin_biomarker_analysis_v1";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function optionalNumber(value: string) {
  return value.trim() ? Number(value) : null;
}

function optionalInteger(value: string) {
  return value.trim() ? Math.round(Number(value)) : null;
}

function adaptiveMetricsFromForm(form: IntakeForm) {
  return {
    age: optionalInteger(form.currentAge),
    weight_kg: optionalNumber(form.weight),
    height_cm: optionalNumber(form.height),
    stress_score: optionalNumber(form.stress),
    heart_rate_bpm: optionalInteger(form.pulseRate),
    sleep_hours: optionalNumber(form.sleepHours),
    steps: optionalInteger(form.dailySteps),
    workout_info: form.exercise.trim() ? `Workout/exercise minutes or note: ${form.exercise.trim()}` : null,
    biomarkers: {
      hba1c: optionalNumber(form.hba1c),
      bp_systolic: optionalInteger(form.bpSystolic),
      bp_diastolic: optionalInteger(form.bpDiastolic),
      vitamin_d: optionalNumber(form.vitaminD),
      vitamin_b12: optionalNumber(form.vitaminB12),
    },
  };
}

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

type ApiUser = {
  id: string;
  full_name: string;
  age: number;
  height_cm: number;
  weight_kg: number;
  target_age?: number | null;
};

type ApiLabReport = {
  hba1c?: number | null;
  bp_systolic?: number | null;
  bp_diastolic?: number | null;
  vitamin_d?: number | null;
  vitamin_b12?: number | null;
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
] as const;

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

function numberText(value: number | null | undefined, digits = 0) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return digits > 0 ? value.toFixed(digits) : String(value);
}

export function LandingPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<IntakeForm>(defaultForm);
  const [wearableMessage, setWearableMessage] = useState("");
  const [wearableLoading, setWearableLoading] = useState(false);
  const [reportMessage, setReportMessage] = useState("");
  const [reportName, setReportName] = useState("");
  const [bloodDetailsMessage, setBloodDetailsMessage] = useState("");
  const [aiPreloading, setAiPreloading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [extractedFields, setExtractedFields] = useState<ExtractedField[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved) as { form?: IntakeForm; reportName?: string };
      if (parsed.form) setForm({ ...defaultForm, ...parsed.form });
      if (parsed.reportName) setReportName(parsed.reportName);
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ form, reportName }));
  }, [form, reportName]);

  useEffect(() => {
    let cancelled = false;

    const hydrateFromBackend = async () => {
      try {
        const existingUserId = localStorage.getItem(USER_STORAGE_KEY);
        let user: ApiUser | undefined;
        if (existingUserId) {
          const response = await fetch(`${API_BASE_URL}/api/v1/users/${existingUserId}`);
          if (response.ok) {
            user = (await response.json()) as ApiUser;
          } else {
            localStorage.removeItem(USER_STORAGE_KEY);
          }
        }
        if (!user) {
          const response = await fetch(`${API_BASE_URL}/api/v1/users?limit=1`);
          if (response.ok) {
            const users = (await response.json()) as ApiUser[];
            user = users[0];
            if (user) localStorage.setItem(USER_STORAGE_KEY, user.id);
          }
        }
        if (!user || cancelled) return;

        let latestLab: ApiLabReport | undefined;
        const labResponse = await fetch(`${API_BASE_URL}/api/v1/users/${user.id}/lab-reports/latest`);
        if (labResponse.ok) {
          latestLab = (await labResponse.json()) as ApiLabReport;
        }

        if (cancelled) return;
        setForm((current) => ({
          ...current,
          fullName: current.fullName || user.full_name,
          currentAge: numberText(user.age),
          height: numberText(user.height_cm, 1),
          weight: numberText(user.weight_kg, 1),
          targetTwinAge: numberText(user.target_age),
          hba1c: numberText(latestLab?.hba1c, 1),
          bpSystolic: numberText(latestLab?.bp_systolic),
          bpDiastolic: numberText(latestLab?.bp_diastolic),
          vitaminD: numberText(latestLab?.vitamin_d, 1),
          vitaminB12: numberText(latestLab?.vitamin_b12),
        }));
      } catch {
        // Keep locally cached values if the backend is not available yet.
      }
    };

    hydrateFromBackend();
    return () => {
      cancelled = true;
    };
  }, []);

  const filledManualFields = manualFieldCount.filter((key) => String(form[key]).trim().length > 0).length;
  const completion = Math.round((filledManualFields / manualFieldCount.length) * 100);
  const hasRequiredBmiMetrics = [form.currentAge, form.height, form.weight].every((value) => value.trim().length > 0);
  const hasPartialBp = [form.bpSystolic, form.bpDiastolic].filter((value) => value.trim().length > 0).length === 1;
  const canSubmitDetails = hasRequiredBmiMetrics && !hasPartialBp;

  const updateField = <K extends keyof IntakeForm>(key: K, value: IntakeForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const updateBloodDetail = <K extends keyof IntakeForm>(key: K, value: IntakeForm[K]) => {
    updateField(key, value);
    setBloodDetailsMessage("");
  };

  const getOrCreateIntakeUser = async (current: IntakeForm) => {
    const existingUserId = localStorage.getItem(USER_STORAGE_KEY);
    if (existingUserId) return existingUserId;

    const usersResponse = await fetch(`${API_BASE_URL}/api/v1/users?limit=1`);
    if (usersResponse.ok) {
      const users = (await usersResponse.json()) as ApiUser[];
      if (users[0]) {
        localStorage.setItem(USER_STORAGE_KEY, users[0].id);
        return users[0].id;
      }
    }

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

  const updateUserMetrics = async (userId: string, current: IntakeForm) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: current.fullName.trim() || "Samsung Health User",
        age: Number(current.currentAge) || 34,
        height_cm: Number(current.height) || 170,
        weight_kg: Number(current.weight) || 70,
        target_age: Number(current.targetTwinAge) || 75,
      }),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Could not update BMI metrics.");
    }
  };

  const resetSingleUserFlow = async () => {
    setResetLoading(true);
    setWearableMessage("");
    setBloodDetailsMessage("");
    try {
      const userId = localStorage.getItem(USER_STORAGE_KEY);
      if (userId) {
        const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, { method: "DELETE" });
        if (!response.ok && response.status !== 404) {
          const errorText = await response.text();
          throw new Error(errorText || "Could not clear user data.");
        }
      }
      localStorage.removeItem(USER_STORAGE_KEY);
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(ADAPTIVE_ROUTINE_STORAGE_KEY);
      localStorage.removeItem(ADAPTIVE_NUTRITION_STORAGE_KEY);
      localStorage.removeItem(BIOMARKER_ANALYSIS_STORAGE_KEY);
      setForm(defaultForm);
      setReportName("");
      setExtractedFields([]);
      setBloodDetailsMessage("User data cleared. You can start fresh.");
    } catch (error) {
      setBloodDetailsMessage(error instanceof Error ? error.message : "Could not clear user data.");
    } finally {
      setResetLoading(false);
    }
  };

  const connectWearable = async () => {
    setWearableLoading(true);
    setWearableMessage("Reading C:\\Users\\dhanu\\Downloads\\Data.zip through the backend and syncing Samsung Health data...");
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
      const mergedForm = { ...form };
      (Object.entries(nextFields) as Array<[keyof IntakeForm, string]>).forEach(([key, value]) => {
        if (value) mergedForm[key] = value as never;
      });
      setForm(mergedForm);
      await updateUserMetrics(userId, mergedForm);

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
  };

  const submitBloodDetails = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmitDetails) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ form, reportName }));
    setBloodDetailsMessage("Saving details...");
    setAiPreloading(true);
    try {
      const userId = await getOrCreateIntakeUser(form);
      await updateUserMetrics(userId, form);
      const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/biomarkers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hba1c: optionalNumber(form.hba1c),
          bp_systolic: optionalInteger(form.bpSystolic),
          bp_diastolic: optionalInteger(form.bpDiastolic),
          vitamin_d: optionalNumber(form.vitaminD),
          vitamin_b12: optionalNumber(form.vitaminB12),
        }),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Could not save biomarker details.");
      }
      setBloodDetailsMessage("AI is generating your routine, nutrition, and biomarker analysis...");
      const body = JSON.stringify({ metrics: adaptiveMetricsFromForm(form) });
      const routineRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/routine`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
      }).then(async (routineResponse) => {
        if (!routineResponse.ok) throw new Error(await routineResponse.text());
        const routinePlan = await routineResponse.json();
        localStorage.setItem(ADAPTIVE_ROUTINE_STORAGE_KEY, JSON.stringify(routinePlan));
        return routinePlan;
      });
      const nutritionRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/nutrition`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
      }).then(async (nutritionResponse) => {
        if (nutritionResponse.ok) {
          localStorage.setItem(ADAPTIVE_NUTRITION_STORAGE_KEY, JSON.stringify(await nutritionResponse.json()));
        }
      });
      const biomarkerRequest = fetch(`${API_BASE_URL}/api/v1/users/${userId}/adaptive-plan/biomarker-analysis`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
      }).then(async (analysisResponse) => {
        if (analysisResponse.ok) {
          localStorage.setItem(BIOMARKER_ANALYSIS_STORAGE_KEY, JSON.stringify(await analysisResponse.json()));
        }
      });
      await routineRequest;
      navigate("/twin");
      await Promise.allSettled([nutritionRequest, biomarkerRequest]);
    } catch (error) {
      setBloodDetailsMessage(error instanceof Error ? error.message : "Could not save biomarker details.");
      setAiPreloading(false);
    }
  };

  return (
    <main className="min-h-screen bg-life-grid bg-[size:44px_44px]">
      <section className="page-wrap py-6 sm:py-8">
        <div className="mb-4 flex justify-end">
          <Button variant="secondary" onClick={resetSingleUserFlow} disabled={resetLoading} title="Clear user data and start fresh">
            <RefreshCw size={17} className={resetLoading ? "animate-spin" : ""} />
            {resetLoading ? "Clearing..." : "Start fresh"}
          </Button>
        </div>
        <div className="grid items-stretch gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(280px,0.75fr)]">
          <Card className="!p-0 h-full overflow-hidden">
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
                        Add current health, labs, wearable trends, and reports so LifeTwin can model a sharper future version of you.
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

          <Card className="!p-5 h-full">
            <div className="flex h-full items-center justify-between gap-5">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Profile completeness</p>
                <h2 className="mt-2 text-xl font-semibold text-white">Intake progress</h2>
                <p className="mt-3 text-4xl font-extrabold leading-none text-white">{completion}%</p>
                <p className="mt-4 max-w-xs text-sm leading-6 text-slate-300">
                  Start with what you know. Import wearable or report data whenever it is ready.
                </p>
              </div>
              <HumanProgress value={completion} />
            </div>
          </Card>
        </div>

        <div className="mt-6 grid items-stretch gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <Card title="Auto-fill from Wearables" className="h-full">
            <p className="text-sm leading-7 text-slate-300">
              Use this option to fetch details from your smart watch<br />
              Highly Recommended!
            </p>
            <Button className="mt-5" onClick={connectWearable} disabled={wearableLoading}>
              {wearableLoading ? "Fetching Samsung Health..." : "Fetch from wearables"} <Watch size={18} />
            </Button>
            {wearableMessage ? <StatusNote tone={wearableLoading ? "info" : "success"}>{wearableMessage}</StatusNote> : null}
          </Card>

          <Card title="Add BMI metrics" className="h-full">
            <form className="mt-4" onSubmit={submitBloodDetails}>
              <div className="grid gap-4 sm:grid-cols-3">
                <BloodReportField label="Age" unit="years" value={form.currentAge} onChange={(value) => updateBloodDetail("currentAge", value)} required />
                <BloodReportField label="Weight" unit="kg" value={form.weight} onChange={(value) => updateBloodDetail("weight", value)} required />
                <BloodReportField label="Height" unit="cm" value={form.height} onChange={(value) => updateBloodDetail("height", value)} required />
              </div>

              <p className="mt-6 text-sm leading-6 text-slate-300">
                Add key blood report values to improve your twin profile.
              </p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <BloodReportField label="HbA1c" unit="%" value={form.hba1c} onChange={(value) => updateBloodDetail("hba1c", value)} />
                <BloodReportField label="Vitamin D" unit="ng/ml" value={form.vitaminD} onChange={(value) => updateBloodDetail("vitaminD", value)} />
                <BloodReportField label="Vitamin B12" unit="pg/ml" value={form.vitaminB12} onChange={(value) => updateBloodDetail("vitaminB12", value)} />
                <BloodPressureField
                  systolic={form.bpSystolic}
                  diastolic={form.bpDiastolic}
                  onSystolicChange={(value) => updateBloodDetail("bpSystolic", value)}
                  onDiastolicChange={(value) => updateBloodDetail("bpDiastolic", value)}
                  invalid={hasPartialBp}
                />
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <Button type="submit" disabled={!canSubmitDetails || aiPreloading}>
                  {aiPreloading ? "Generating AI plan..." : "Submit details"}
                </Button>
                {hasPartialBp ? <span className="text-sm font-medium text-amber-100">Enter both BP values or leave both empty.</span> : null}
                {bloodDetailsMessage ? <span className="text-sm font-medium text-emerald-100">{bloodDetailsMessage}</span> : null}
              </div>
              {aiPreloading ? (
                <div className="mt-5 rounded-2xl border border-emerald-300/25 bg-emerald-300/10 p-4">
                  <div className="flex items-center gap-3">
                    <RefreshCw size={18} className="animate-spin text-emerald-100" />
                    <div>
                      <p className="text-sm font-semibold text-white">AI is generating your plan</p>
                      <p className="mt-1 text-xs leading-5 text-slate-300">
                        Routine loads first. Nutrition and biomarker analysis continue in parallel.
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-emerald-300 to-blue-400" />
                  </div>
                </div>
              ) : null}
            </form>
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

function HumanProgress({ value }: { value: number }) {
  const boundedValue = Math.max(0, Math.min(100, value));
  const fill = `${boundedValue}%`;
  const fillY = 116 - boundedValue * 1.08;

  return (
    <div
      className="relative h-32 w-24 shrink-0 rounded-3xl border border-cyan-300/15 bg-black/20 p-2 shadow-inner shadow-black/30"
      aria-label={`Profile completeness ${value}%`}
    >
      <svg className="h-full w-full overflow-visible" viewBox="0 0 96 128" role="img" aria-hidden="true">
        <defs>
          <linearGradient id="humanProgressFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#a5f3fc" />
            <stop offset="50%" stopColor="#5eead4" />
            <stop offset="100%" stopColor="#60a5fa" />
          </linearGradient>
          <clipPath id="humanProgressShape">
            <circle cx="48" cy="19" r="12" />
            <path d="M31 44c2-10 10-16 17-16s15 6 17 16l-4 31c-1 7-6 12-13 12s-12-5-13-12l-4-31Z" />
            <path d="M19 45c0-6 4-10 9-10 4 0 7 3 8 7l4 31c1 5-2 9-7 10-4 1-8-2-9-7l-5-31Z" />
            <path d="M77 45c0-6-4-10-9-10-4 0-7 3-8 7l-4 31c-1 5 2 9 7 10 4 1 8-2 9-7l5-31Z" />
            <path d="M36 82h11v34c0 5-3 8-8 8s-8-3-8-8l5-34Z" />
            <path d="M49 82h11l5 34c0 5-3 8-8 8s-8-3-8-8V82Z" />
          </clipPath>
        </defs>
        <rect x="10" y="6" width="76" height="112" rx="28" fill="none" stroke="rgba(148, 163, 184, 0.12)" />
        <g clipPath="url(#humanProgressShape)">
          <rect x="12" y="4" width="72" height="120" fill="rgba(255,255,255,0.12)" />
          <rect x="12" y={fillY} width="72" height={116 - fillY} fill="url(#humanProgressFill)" />
        </g>
        <g fill="none" stroke="rgba(226, 232, 240, 0.18)" strokeWidth="1.5">
          <circle cx="48" cy="19" r="12" />
          <path d="M31 44c2-10 10-16 17-16s15 6 17 16l-4 31c-1 7-6 12-13 12s-12-5-13-12l-4-31Z" />
          <path d="M19 45c0-6 4-10 9-10 4 0 7 3 8 7l4 31c1 5-2 9-7 10-4 1-8-2-9-7l-5-31Z" />
          <path d="M77 45c0-6-4-10-9-10-4 0-7 3-8 7l-4 31c-1 5 2 9 7 10 4 1 8-2 9-7l5-31Z" />
          <path d="M36 82h11v34c0 5-3 8-8 8s-8-3-8-8l5-34Z" />
          <path d="M49 82h11l5 34c0 5-3 8-8 8s-8-3-8-8V82Z" />
        </g>
        <path d="M19 118h58" stroke="rgba(148, 163, 184, 0.28)" strokeWidth="4" strokeLinecap="round" />
      </svg>
      <div className="absolute bottom-2 left-3 right-3 h-1 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gradient-to-r from-emerald-300 to-blue-400" style={{ width: fill }} />
      </div>
    </div>
  );
}

function BloodReportField({
  label,
  inputLabel,
  unit,
  value,
  onChange,
  required = false,
}: {
  label: string;
  inputLabel?: string;
  unit: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-slate-300">
        {label}
        {required ? <span className="ml-1 text-cyan-200">*</span> : null}
      </span>
      <div className="relative">
        <input
          className="field pr-16"
          type="number"
          aria-label={inputLabel || label}
          required={required}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
        <span className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-xs font-semibold text-slate-500">
          {unit}
        </span>
      </div>
    </label>
  );
}

function BloodPressureField({
  systolic,
  diastolic,
  onSystolicChange,
  onDiastolicChange,
  invalid,
}: {
  systolic: string;
  diastolic: string;
  onSystolicChange: (value: string) => void;
  onDiastolicChange: (value: string) => void;
  invalid: boolean;
}) {
  const inputClasses = "h-full min-w-0 flex-1 rounded-lg border border-transparent bg-transparent px-2 text-center text-sm text-white outline-none";

  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-slate-300">BP</span>
      <div className={`flex min-h-[46px] items-center gap-2 rounded-xl border bg-white/[0.07] px-4 py-0 transition ${invalid ? "border-amber-300/70" : "border-white/10"}`}>
        <input
          className={inputClasses}
          type="number"
          aria-label="BP systolic"
          required={diastolic.trim().length > 0}
          value={systolic}
          onChange={(event) => onSystolicChange(event.target.value)}
        />
        <span className="text-lg font-bold text-slate-500">/</span>
        <input
          className={inputClasses}
          type="number"
          aria-label="BP diastolic"
          required={systolic.trim().length > 0}
          value={diastolic}
          onChange={(event) => onDiastolicChange(event.target.value)}
        />
        <span className="shrink-0 text-xs font-semibold text-slate-500">mmHg</span>
      </div>
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
