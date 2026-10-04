import { API_URL } from "@/lib/api";

export interface Carver {
  name: string;
  kind: "S" | "A" | "P" | "L";
  uncertain: boolean;
}

export interface Inscription {
  signum: string;
  flags: { lost: boolean; new_reading: boolean; medieval: boolean; proto_norse: boolean; post_medieval: boolean };
  place: string;
  parish: string;
  district: string;
  municipality: string;
  placement: string;
  lat: number | null;
  lon: number | null;
  rune_types: string;
  cross_form: string;
  dating: string;
  period: "U" | "V" | "M" | null;
  style: string | null;
  style_uncertain: boolean;
  carver_raw: string;
  carvers: Carver[];
  material_type: string;
  material: string;
  object: string;
  other: string;
  alt_signum: string;
  references: string;
  image_link: string;
  transliteration: string;
  normalization: string;
  normalization_ows: string;
  translation_en: string;
}

export interface RundataMeta {
  source: string;
  source_url: string;
  attribution: string;
  license: string;
  built: string;
  count: number;
  note: string;
}

export interface StyleGroup {
  code: string;
  from: number | null;
  to: number | null;
  name: string;
  features: string;
}

export interface StyleDistribution {
  style: string;
  count: number;
  uncertain: number;
  provinces: Record<string, number>;
  carvers: Record<string, number>;
  examples: { signum: string; place: string; image_link: string }[];
}

export interface OrthographyEvaluation {
  n_inscriptions: number;
  n_carvers: number;
  top1_accuracy: number;
  top3_accuracy: number;
  chance_top1: number;
  signed_only: { n: number; top1_accuracy: number | null };
  min_inscriptions_per_carver: number;
  method: string;
}

export interface CarverRanking {
  ranking: { carver: string; similarity: number; n_inscriptions: number; significance?: { p_value: number; p_adjusted: number; n_null: number; own_percentile: number | null; n_carvers: number } | null }[];
  n_words: number;
  known_attribution: Carver[];
  evaluation: OrthographyEvaluation;
}

export interface SimilarInscription {
  signum: string;
  place: string;
  similarity: number;
  carvers: Carver[];
  style: string | null;
  shared_spellings: Record<string, string>;
}

export interface OrthographyProfile {
  n_words: number;
  separators: Record<string, number>;
  separator_density: number;
  bindrune_rate: number;
  spellings: Record<string, string>;
}

export const CARVER_KIND: Record<Carver["kind"], string> = {
  S: "signerad",
  A: "attribuerad",
  P: "parsten",
  L: "liknar",
};

export const PERIOD_LABEL: Record<string, string> = { U: "Urnordisk", V: "Vikingatid", M: "Medeltid" };

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Fel ${res.status}`);
  }
  return res.json();
}

const enc = encodeURIComponent;

export const rundata = {
  meta: () => getJSON<RundataMeta>("/api/rundata/meta"),
  inscription: (signum: string) => getJSON<Inscription>(`/api/rundata/inscription/${enc(signum)}`),
  search: (params: Record<string, string | number | boolean | undefined>) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "" && v !== false) qs.set(k, String(v));
    }
    return getJSON<{ total: number; results: Inscription[] }>(`/api/rundata/search?${qs}`);
  },
  find: (text: string) => getJSON<{ signum: string; place: string }[]>(`/api/rundata/find?text=${enc(text)}`),
  carvers: () =>
    getJSON<{ name: string; signed: number; attributed: number; pair: number; similar: number; total: number }[]>(
      "/api/rundata/carvers",
    ),
  styles: () =>
    getJSON<{ groups: StyleGroup[]; source: string; distribution: StyleDistribution[] }>("/api/rundata/styles"),
  geo: () =>
    getJSON<{ fields: string[]; rows: [string, number, number, string | null, string | null, string, number][] }>(
      "/api/rundata/geo",
    ),
  orthographyProfile: (signum: string) => getJSON<OrthographyProfile>(`/api/orthography/profile/${enc(signum)}`),
  similar: (signum: string, limit = 10) =>
    getJSON<SimilarInscription[]>(`/api/orthography/similar/${enc(signum)}?limit=${limit}`),
  carverRanking: (signum: string, limit = 8) =>
    getJSON<CarverRanking>(`/api/orthography/carvers/${enc(signum)}?limit=${limit}`),
  orthographyEvaluation: () => getJSON<OrthographyEvaluation>("/api/orthography/evaluation"),
};

export function carverText(carvers: Carver[]): string {
  return carvers.map(c => `${c.name} (${CARVER_KIND[c.kind]}${c.uncertain ? ", osäker" : ""})`).join(", ");
}
