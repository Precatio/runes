import { API_URL } from "@/lib/api";
import type { Metric, SliceMetrics, Summary } from "@/lib/metrics";

export interface StoneInput {
  label: string;
  signum?: string;
  feature_type?: string;
  slices?: SliceMetrics[];
  means?: Record<Metric, number>;
}

export interface ComparisonResult {
  a: string;
  b: string;
  per_metric: {
    metric: Metric;
    label: string;
    a: Summary;
    b: Summary;
    p_value: number | null;
    p_adjusted: number | null;
    diff: number | null;
    effect_size_d?: number | null;
  }[];
  overall: { p_value: number | null; distance?: number; metrics_used: string[] };
  interpretation: string;
  warnings: string[];
}

export interface GrooveAttribution {
  ranking: { group: string; n: number; distance: number }[];
  evaluation: {
    n_stones: number;
    n_groups: number;
    top1_accuracy: number;
    top3_accuracy: number;
    chance_top1: number;
    method: string;
  } | null;
  note?: string;
  reference_size: number;
  skipped_unlabelled: number;
  labels_from: string;
}

export interface ClusterResult {
  order: string[];
  icoord: number[][];
  dcoord: number[][];
  method: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Fel ${res.status}`);
  }
  return res.json();
}

export const stats = {
  compare: (a: StoneInput, b: StoneInput) => post<ComparisonResult>("/api/stats/compare", { a, b }),
  cluster: (stones: StoneInput[]) => post<ClusterResult>("/api/stats/cluster", { stones }),
  attribute: (query: StoneInput, reference: StoneInput[]) =>
    post<GrooveAttribution>("/api/stats/attribute", { query, reference }),
};

export function formatP(p: number | null | undefined): string {
  if (p === null || p === undefined) return "–";
  if (p < 0.001) return "< 0,001";
  return p.toFixed(3).replace(".", ",");
}
