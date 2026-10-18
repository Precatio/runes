import { API_URL } from "@/lib/api";

// The probability model's reading of an inscription (api/routers/textmodel.py, src/textmodel.py)
export interface TextModelWord {
  runes: string;
  word: string;
  name: boolean;
  unknown: boolean;
  p: number;
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
  words: { word: string; p: number; p_model?: number }[];
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

const enc = encodeURIComponent;

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Fel ${res.status}`);
  }
  return res.json();
}

export const textmodel = {
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
