import { type Significance } from "@/components/Explain";
import { type Pattern } from "@/components/PatternCard";

export interface ProvinceRow {
  code: string; name: string; axelson: boolean; total: number; carver: number; style: number; dated: number;
  uncertain_interpretation: number; lost: number; measured: number;
}
export interface Hypothesis extends StoneExtras {
  signum: string; place: string; province: string; style: string | null; carver: string; similarity: number;
  p_value: number | null; p_adjusted: number | null;
  margin: number; runner_up: string; n_words: number; in_carver_area: boolean; carver_area: string[];
  carver_precision: number | null; short_text: boolean; attributed_to?: string[];
}

// Rock type and language traits of the stone, compared with the suggested carver
export interface StoneExtras {
  material: string | null; material_fit: boolean | null; material_text?: string;
  language: { agree: number; comparable: number; text: string; fits: boolean | null } | null;
}
export interface Priority {
  carver: string; inscriptions: number; signed: number; measured: number; measured_signa: string[];
  missing_to_target: number; suggestions: { signum: string; place: string; signed: boolean }[];
}
export interface Brief { signum: string; place: string; province: string; style: string | null; dating: string; carvers: string[] }
export interface Gaps {
  coverage: { scope: string; totals: Record<string, number>; per_province: ProvinceRow[] };
  hypotheses: { new: Hypothesis[]; reconsider: Hypothesis[]; evaluation: { top1_accuracy: number; signed_only: { top1_accuracy: number | null }; n_carvers: number; chance_top1: number } };
  open_questions: { uninterpreted: { count: number; items: Brief[] }; uncertain_style: { count: number; items: Brief[] } };
  measurement_priorities: Priority[];
  source_note: string;
  attribution: string;
}

export type Verdict = "stämmer" | "nytt" | "motsäger";
export interface Finding extends StoneExtras {
  stats?: Record<string, number | string | boolean | null>;
  signum: string; place: string; province: string; method: string; verdict: Verdict; ours: string; existing: string;
  evidence: number; novelty: number; relevance: number; score: number; assessment: string; suggested?: string;
  reasons: { belägg: string[]; nyhet: string[]; relevans: string[] };
  crosscheck?: CrossCheck;
  significance?: Significance;
  // The reasoned conclusion (same rules as the interpretation shown when the row is opened; METHODS.md 14d)
  interpretation?: { level: string; support: number; against: number };
}
// The suggestion checked against newer sources (Runor 2020, Wikidata)
export interface CrossCheck {
  status: "finns redan" | "nämns" | "annan ristare" | "samma som" | "saknas" | "ej kontrollerad";
  runor?: { status: string; text: string; references: string[]; url?: string | null };
  wikidata?: { text: string };
}
export type RPattern = Pattern;
export interface Findings {
  r_patterns?: RPattern[];
  r_ready?: boolean;
  findings: Finding[];
  summary: { counts: Record<Verdict, number>; by_method: Record<string, Partial<Record<Verdict, number>>>; likely_new: number };
  technique_note: string | null;
  method_note: string;
}

export type Tab = "findings" | "coverage" | "categories" | "size" | "hypotheses" | "reconsider" | "priorities" | "uninterpreted" | "style" | "textgaps";

// The probability model's open gaps (GET /api/research/gaps/textmodel, scripts/textmodel_candidates.py)
// p is the calibrated probability (since 2026-10-23); p_model the model's raw figure; alts [word, calibrated, raw]
interface TextGapCandidate {
  signum: string; province: string; object?: string | null; runestone?: boolean; carved: string; gap: number;
  fill: string | null; word: string | null; p: number; p_model?: number;
  alts: [string, number, number?][]; reading: string | null; p_reading: number | null; translation_sv?: string | null;
}
interface TextGapCounts { gaps_inventoried: number; open: number; candidates: number; stones: number; sure?: number }
export interface TextGaps {
  available: boolean; note?: string; model_version?: string; computed_at?: string; rundata_version?: string; min_p?: number;
  sure_p?: number; counts?: TextGapCounts & { runsten?: TextGapCounts; annat?: TextGapCounts };
  candidates?: TextGapCandidate[];
}

export interface CategoryStats {
  categories: { key: string; label: string; definition: string; base_rate: number; count: number }[];
  n_inscriptions: number;
  carvers: { carver: string; n: number; counts: Record<string, { k: number; share: number; expected: number; p: number; q: number; p_zero: number | null; direction: "över" | "under" | "som genomsnittet" }> }[];
  method: string;
}

// ---- sorting -------------------------------------------------------------------------------
export type SortValue = string | number | boolean | null | undefined;
export type SortState = { key: string; desc: boolean };

interface SizeTest { variable: string; n: number; ratio: number | null; p: number | null; q: number | null; median_with_m: number; median_without_m: number }
export interface SizeStats {
  n: number; median_height_m: number; quartiles_m: [number, number]; error?: string;
  meta: { n_runestones: number; status: Record<string, number> }; source: string;
  tests: SizeTest[];
  correlations: { variable: string; rho: number; p: number; n: number; partial?: boolean }[];
  carvers: { carver: string; n: number; ratio: number | null; p: number | null; q: number | null; median_m: number }[];
  largest: { signum: string; height_m: number; categories: string[]; status: string[] }[];
}

export interface Interpretation { paragraphs: { title: string; text: string }[]; level: string; support: number; against: number }
