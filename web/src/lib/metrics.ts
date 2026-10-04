// Groove metrics, in the same order as src/stats.py METRICS on the backend
export const METRICS = [
  "apex_vinkel_deg",
  "asymmetri_deg",
  "spårdjup_mm",
  "spårbredd_mm",
  "djup_bredd_kvot",
  "bottenradie_mm",
  "ytråhet_mm",
] as const;

export type Metric = (typeof METRICS)[number];

export const METRIC_LABELS: Record<Metric, string> = {
  apex_vinkel_deg: "V-vinkel (°)",
  asymmetri_deg: "Asymmetri (°)",
  spårdjup_mm: "Spårdjup (mm)",
  spårbredd_mm: "Spårbredd (mm)",
  djup_bredd_kvot: "Djup/bredd",
  bottenradie_mm: "Bottenradie (mm)",
  ytråhet_mm: "Ytråhet (mm)",
};

export const METRIC_DIGITS: Record<Metric, number> = {
  apex_vinkel_deg: 1,
  asymmetri_deg: 1,
  spårdjup_mm: 2,
  spårbredd_mm: 2,
  djup_bredd_kvot: 2,
  bottenradie_mm: 2,
  ytråhet_mm: 3,
};

export interface Summary {
  n: number;
  mean: number | null;
  sd: number | null;
  ci95: [number, number] | null;
  min: number | null;
  max: number | null;
}

export type SliceMetrics = Record<Metric, number> & { position_mm: number };

export const FEATURE_TYPES = {
  rune: "Runa",
  ornament: "Ornamentik",
  unknown: "Okänt",
} as const;

export type FeatureType = keyof typeof FEATURE_TYPES;

export function formatSummary(s: Summary | undefined, digits = 2): string {
  if (!s || s.n === 0 || s.mean === null) return "–";
  if (s.n < 2 || s.sd === null) return s.mean.toFixed(digits);
  return `${s.mean.toFixed(digits)} ± ${s.sd.toFixed(digits)}`;
}
