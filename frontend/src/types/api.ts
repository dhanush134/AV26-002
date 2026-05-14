export type RiskLevel = "low" | "moderate" | "high" | "critical" | "unknown";

export type GenericRecord = Record<string, unknown>;

export interface DemoRunResponse extends GenericRecord {
  user_id?: string | number;
  id?: string | number;
}

export interface HealthResponse extends GenericRecord {
  status?: string;
}

export interface DashboardResponse extends GenericRecord {
  user?: GenericRecord;
  user_id?: string | number;
  name?: string;
  twin_alignment_score?: number;
  alignment_score?: number;
  overall_risk_level?: string;
  risk_level?: string;
  summary?: string;
  healthspan_target_age?: number;
  vitals?: GenericRecord;
  latest_vitals?: GenericRecord;
  labs?: GenericRecord;
  risk_breakdown?: GenericRecord;
  trends?: GenericRecord;
  top_risk_factors?: unknown[];
  recommended_actions?: unknown[];
  today_actions?: unknown[];
  alerts?: unknown[];
}

export interface ScenarioReplayPayload {
  scenario: string;
  points: number;
}

export interface DailyCheckinPayload {
  sleep_quality: string;
  exercise_done: string;
  food_quality: string;
  alcohol_used: boolean;
  smoking_done: boolean;
  stress_level: string;
  steps_completed: number;
  sleep_hours: number;
  notes: string;
}

export interface WearableReadingPayload {
  heart_rate: number;
  spo2: number;
  steps: number;
  active_minutes: number;
  sleep_hours: number;
  captured_at?: string;
}
