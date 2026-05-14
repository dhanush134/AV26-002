import type { RiskLevel } from "../types/api";

export const normalizeRisk = (risk: unknown): RiskLevel => {
  const value = String(risk ?? "").toLowerCase();
  if (value.includes("critical")) return "critical";
  if (value.includes("high")) return "high";
  if (value.includes("medium") || value.includes("moderate") || value.includes("warning")) return "moderate";
  if (value.includes("low") || value.includes("healthy") || value.includes("normal")) return "low";
  return "unknown";
};

export const riskCopy: Record<RiskLevel, string> = {
  low: "Low",
  moderate: "Moderate",
  high: "High",
  critical: "Critical",
  unknown: "Unknown",
};

export const riskStyles: Record<RiskLevel, string> = {
  low: "border-emerald-400/35 bg-emerald-400/12 text-emerald-200",
  moderate: "border-amber-300/35 bg-amber-300/12 text-amber-100",
  high: "border-orange-400/35 bg-orange-400/12 text-orange-100",
  critical: "border-rose-400/40 bg-rose-500/15 text-rose-100",
  unknown: "border-white/15 bg-white/8 text-slate-200",
};

export const riskAccent: Record<RiskLevel, string> = {
  low: "#34d399",
  moderate: "#fbbf24",
  high: "#fb923c",
  critical: "#fb7185",
  unknown: "#94a3b8",
};
