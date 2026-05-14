import type { GenericRecord } from "../types/api";

export const toNumber = (value: unknown, fallback = 0): number => {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const toText = (value: unknown, fallback = "Not available"): string => {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number") return String(value);
  return fallback;
};

export const asRecord = (value: unknown): GenericRecord =>
  value && typeof value === "object" && !Array.isArray(value) ? (value as GenericRecord) : {};

export const asArray = <T = unknown>(value: unknown): T[] => (Array.isArray(value) ? (value as T[]) : []);

export const pct = (value: unknown, fallback = 0): number =>
  Math.max(0, Math.min(100, Math.round(toNumber(value, fallback))));

export const titleCase = (value: string): string =>
  value
    .replace(/[_-]/g, " ")
    .replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());

export const compactNumber = (value: unknown): string =>
  new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(toNumber(value));

export const safeJsonDownload = (filename: string, data: unknown) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};
