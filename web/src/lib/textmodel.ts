import { API_URL } from "@/lib/api";

// The probability model's reading of an inscription (api/routers/textmodel.py, src/textmodel.py)
export interface TextModelWord {
  runes: string;
  word: string;
  name: boolean;
  unknown: boolean;
  p: number | null;  // null for an unknown word (no claim about a word)
  filled: boolean;
  break_after: boolean;
}

export interface TextModelGap {
  number: number;
  group: number;
  start: number;
  end: number;
  carved: string;
  n: number;
  best: string | null;
  fills: { fill: string; p: number; word: string | null }[];
  words: { word: string; p: number | null; p_model?: number }[];
  traces: (string | null)[] | null;
}

// A gap whose best word changes with the editors' word boundaries (src/textmodel.py _boundaries): in a text without
// dividers the model chooses where the words begin, and may borrow runes from a word it does not know
export interface TextModelBoundary {
  gap: number;
  variant: "main" | "alt";
  model_runes: string;
  model_fill: string | null;
  editor_runes: string;
  best: string | null;
  words: { word: string; p: number }[];
}

export interface TextModelReading {
  signum: string;
  version: string;
  available: boolean;
  reason?: string;
  computed_at?: string;
  groups?: string[];
  reading?: TextModelWord[];
  gaps?: TextModelGap[];
  open_gaps?: { group: number; start: number; end: number; n: number }[];
  boundaries?: TextModelBoundary[];
  dating?: { epochs: { epoch: string; label: string; p: number }[]; calibrated: boolean; rundata: string };
  calibrated?: boolean;
  gap_calibrated?: boolean;
  translation?: { sv: string; en: string };
  validation: {
    inside_word: number; whole_word: number; sure_right: number; rundata_sure: number;
    with_traces: number; with_misread_traces?: number; dating_epoch: number; dating_near: number;
    documented_right?: number; documented_sure?: number;
  };
}

// The runes a trace can be ticked as: the younger futhark and the dotted runes, as the model writes them
export const TRACE_RUNES: [string, string][] = [
  ["ᚠ", "f"], ["ᚢ", "u"], ["ᚦ", "þ"], ["ᚬ", "o"], ["ᚱ", "r"], ["ᚴ", "k"], ["ᚼ", "h"], ["ᚾ", "n"],
  ["ᛁ", "i"], ["ᛅ", "a"], ["ᛋ", "s"], ["ᛏ", "t"], ["ᛒ", "b"], ["ᛘ", "m"], ["ᛚ", "l"], ["ᛦ", "R"],
  ["ᛂ", "e"], ["ᚤ", "y"], ["ᚵ", "g"], ["ᛑ", "d"], ["ᛔ", "p"],
];

// What the scan's trace reader sees at a gap (api GET /textmodel/scantraces): proposals only – they count
// first when the user confirms them, and a possible bind rune proposes nothing
export interface ScanTraceEntry {
  pos: number;
  set: string;
  informative?: boolean; // false: the set excludes nothing – shown, but never prefilled
  top: [string, number][];
  blobs: { cross: boolean; zone: string; long: boolean; length: number; ratio: number; w: number }[];
  bind: boolean;
}

export interface ScanTraces {
  available: boolean;
  reason?: string;
  gaps?: Record<string, ScanTraceEntry[]>;
  quality?: { detected: number; text_runes: number; paired: number; lost_total: number; lost_with_proposal: number };
}

// Every candidate the model tries in one gap (api GET /textmodel/candidates, src/textmodel_overview.py): the
// probability p is calibrated as the app's suggestions, for the kmax most probable words only; p_model is the model's
// own share among the candidates tried, before calibration
export type CandidateOrigin = "vocabulary" | "names" | "nearby" | "carver" | "stone" | "variant" | "runes";

export interface GapCandidate {
  fill: string;
  p_model: number;
  word: string | null;
  unknown: boolean;
  composed: boolean;
  name: boolean;
  p_word: number | null;
  origins: CandidateOrigin[];
  left: string;
  right: string;
}

export interface GapWord {
  word: string | null;
  unknown: boolean;
  composed: boolean;
  name: boolean;
  class: string | null;
  p: number | null;
  p_model: number;
  fills: { fill: string; p_model: number; left: string; right: string }[];
  n_fills: number;
  origins: CandidateOrigin[];
  corpus: { count: number; stones: number; examples: string[]; other_count: number; other_stones: number } | null;
}

export interface GapOverview {
  signum: string;
  version: string;
  available: boolean;
  reason?: string;
  cached?: boolean;
  seconds?: number;
  gap?: {
    number: number; kind: "gap" | "open"; group: number; start: number; end: number; carved: string;
    rundata_n: number; n: number; adjustable: boolean; tested: boolean; min_n: number; max_n: number;
  };
  context?: { number: number; fill: string }[];
  calibrated?: boolean;
  kmax?: number;
  candidates?: GapCandidate[];
  words?: GapWord[];
  n_tried?: number;
  n_words?: number;
  n_unknown_fills?: number;
  unassigned?: number | null;
  top_unsure?: boolean;
  whole_word?: boolean;
  limit?: number;
  truncated?: boolean;
  validation: TextModelReading["validation"];
}

// Vitki's own fillings of lost runes (api /textmodel/fills, src/vitki_fills.py): a layer on top of Rundata, which is
// never changed; the model is never trained or tested on them
export type FillStatus = "förslag" | "bekräftad" | "avvisad";
export type FillMethod = "sannolikhetsmodellen" | "spår ur skanningen" | "utgivarens läsning";
export type EvidenceKind = "sri" | "skanning" | "runor2020" | "annat";

export interface VitkiFill {
  id: string;
  signum: string;
  gap: { kind: "gap" | "open"; number: number; group: number; start: number; end: number; carved: string;
         rundata_n: number; n: number; width: number; key: string };
  fill: string;
  word: string | null;
  name: boolean;
  method: FillMethod;
  model_version: string | null;
  p: number | null;
  p_model: number | null;
  evidence: { kind: EvidenceKind; ref: string }[];
  status: FillStatus;
  comment: string;
  by: string;
  date: string;
  history: { status: FillStatus; by: string; date: string; comment: string }[];
  label: string;
}

export const EVIDENCE_LABEL: Record<EvidenceKind, string> = {
  sri: "SRI-sida", skanning: "Skanning", runor2020: "Runor 2020", annat: "Annat",
};

const enc = encodeURIComponent;

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Fel ${res.status}`);
  }
  return res.json();
}

type Headers = Record<string, string>;

export const textmodel = {
  // n: another number of lost runes than Rundata's; kind "open": one of the longer gaps the reading leaves open
  candidates: async (signum: string, gap: number, n?: number, kind: "gap" | "open" = "gap") =>
    json<GapOverview>(await fetch(`${API_URL}/api/textmodel/candidates/${enc(signum)}?gap=${gap}&kind=${kind}${n ? `&n=${n}` : ""}`)),
  fills: async (signum?: string) =>
    json<{ license: string; fills: VitkiFill[] }>(await fetch(`${API_URL}/api/textmodel/fills${signum ? `?signum=${enc(signum)}` : ""}`)),
  saveFill: async (headers: Headers, body: {
    signum: string; gap: number; kind: "gap" | "open"; n?: number; fill: string; method: FillMethod;
    status: "förslag" | "bekräftad"; comment: string; evidence: { kind: EvidenceKind; ref: string }[];
  }) => json<VitkiFill>(await fetch(`${API_URL}/api/textmodel/fills`, {
    method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body),
  })),
  setFillStatus: async (headers: Headers, id: string, status: FillStatus, comment: string,
                        evidence: { kind: EvidenceKind; ref: string }[] = []) =>
    json<VitkiFill>(await fetch(`${API_URL}/api/textmodel/fills/${enc(id)}/status`, {
      method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify({ status, comment, evidence }),
    })),
  read: async (signum: string) => json<TextModelReading>(await fetch(`${API_URL}/api/textmodel/${enc(signum)}`)),
  scanTraces: async (signum: string) =>
    json<ScanTraces>(await fetch(`${API_URL}/api/textmodel/scantraces/${enc(signum)}`)),
  // allowed: gap number → for each lost rune the runes its remains allow ("" = nothing visible)
  withTraces: async (signum: string, allowed: Record<number, string[]>) =>
    json<TextModelReading>(await fetch(`${API_URL}/api/textmodel/traces/${enc(signum)}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ allowed: Object.fromEntries(Object.entries(allowed).map(([k, v]) => [k, v.map(s => s || null)])) }),
    })),
};
