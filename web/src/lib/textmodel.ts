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
  words: { word: string; p: number }[];
  traces: (string | null)[] | null;
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
  dating?: { epochs: { epoch: string; label: string; p: number }[]; calibrated: boolean; rundata: string };
  translation?: { sv: string; en: string };
  validation: {
    inside_word: number; whole_word: number; sure_right: number; rundata_sure: number;
    with_traces: number; dating_epoch: number; dating_near: number;
  };
}

// The runes a trace can be ticked as: the younger futhark and the dotted runes, as the model writes them
export const TRACE_RUNES: [string, string][] = [
  ["ᚠ", "f"], ["ᚢ", "u"], ["ᚦ", "þ"], ["ᚬ", "o"], ["ᚱ", "r"], ["ᚴ", "k"], ["ᚼ", "h"], ["ᚾ", "n"],
  ["ᛁ", "i"], ["ᛅ", "a"], ["ᛋ", "s"], ["ᛏ", "t"], ["ᛒ", "b"], ["ᛘ", "m"], ["ᛚ", "l"], ["ᛦ", "R"],
  ["ᛂ", "e"], ["ᚤ", "y"], ["ᚵ", "g"], ["ᛑ", "d"], ["ᛔ", "p"],
];

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
  // allowed: gap number → for each lost rune the runes its remains allow ("" = nothing visible)
  withTraces: async (signum: string, allowed: Record<number, string[]>) =>
    json<TextModelReading>(await fetch(`${API_URL}/api/textmodel/traces/${enc(signum)}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ allowed: Object.fromEntries(Object.entries(allowed).map(([k, v]) => [k, v.map(s => s || null)])) }),
    })),
};
