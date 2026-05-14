import { Activity, BedDouble, Flame, HeartPulse, Wind } from "lucide-react";

export const scenarios = [
  {
    id: "normal",
    label: "Normal Baseline",
    description: "Stable vitals with normal recovery and activity.",
    notice: "Judges see the twin stay steady when signals match baseline.",
    icon: Activity,
  },
  {
    id: "fatigue",
    label: "Fatigue",
    description: "Elevated resting HR, lower activity, and reduced sleep recovery.",
    notice: "Risk rises through lifestyle and recovery signals.",
    icon: BedDouble,
  },
  {
    id: "respiratory_risk",
    label: "Respiratory Risk",
    description: "SpO2 drift plus heart-rate deviation creates a preventive respiratory alert.",
    notice: "The app detects early signal clusters, not a single metric.",
    icon: Wind,
  },
  {
    id: "cardiac_strain",
    label: "Cardiac Strain",
    description: "Sustained heart-rate elevation and anomaly score trigger a high-priority plan update.",
    notice: "This is the strongest hackathon demo scenario.",
    icon: HeartPulse,
  },
  {
    id: "poor_sleep_metabolic_risk",
    label: "Sleep + Metabolic Risk",
    description: "Poor sleep, low steps, and metabolic risk signals reduce twin alignment.",
    notice: "Daily behavior changes the future twin gap.",
    icon: Flame,
  },
];
