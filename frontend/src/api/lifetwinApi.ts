import { apiRequest } from "./client";
import type {
  DailyCheckinPayload,
  DashboardResponse,
  DemoRunResponse,
  HealthResponse,
  ScenarioReplayPayload,
  WearableReadingPayload,
} from "../types/api";

export const lifetwinApi = {
  health: () => apiRequest<HealthResponse>("/health"),
  runFullDemo: () => apiRequest<DemoRunResponse>("/api/v1/demo/run-full-demo", { method: "POST" }),
  getDashboard: (userId: string) => apiRequest<DashboardResponse>(`/api/v1/users/${userId}/dashboard`),
  replayScenario: (userId: string, scenario: string, points = 30) =>
    apiRequest<DashboardResponse>(`/api/v1/users/${userId}/simulation/replay`, {
      method: "POST",
      body: { scenario, points } satisfies ScenarioReplayPayload,
    }),
  submitDailyCheckin: (userId: string, payload: DailyCheckinPayload) =>
    apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/daily-checkin`, { method: "POST", body: payload }),
  getDoctorReport: (userId: string) => apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/doctor-report`),
  getCurrentTwin: (userId: string) => apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/twin/current`),
  getIdealTwin: (userId: string) => apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/twin/ideal`),
  getDailyRoutine: (userId: string) => apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/daily-routine`),
  getAlerts: (userId: string) => apiRequest<unknown[]>(`/api/v1/users/${userId}/alerts`),
  createWearableReading: (userId: string, payload: WearableReadingPayload) =>
    apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/wearable-readings`, { method: "POST", body: payload }),
  calculateRisk: (userId: string) =>
    apiRequest<Record<string, unknown>>(`/api/v1/users/${userId}/risk/calculate`, { method: "POST" }),
};
