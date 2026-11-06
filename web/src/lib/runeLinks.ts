// Runa för runa: each click in the review image of the automatic groove analysis tied to a rune of the stone's
// transliteration in Rundata (src/rune_links.py). The transliteration comes as tokens from GET /api/rundata/tokens;
// the clicks and skips are kept as steps in the order they were made, so that every action can be undone. A step
// without tokens is a plain mark (Markera runorna, stones without a transliteration). The links go into the facit
// (version 2, scripts/evaluate_rune_detection.py) and the TEI/EpiDoc export (src/tei_export.py).
import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

export type TokenKind = "rune" | "uncertain" | "lost" | "divider" | "gap" | "other";

export interface TranslitToken {
  i: number; // the token's index in the whole transliteration (its xml:id in the TEI file is t + i)
  char: string;
  orig: string;
  kind: TokenKind;
  word: number | null;
  section: string;
  pos: number | null; // place in the text model's text (src/textmodel.text_groups)
  reason?: "lost" | "illegible";
  bind_next?: boolean; // Rundata writes a bind rune with the next rune (^)
  older?: boolean; // within [ ]: known from older documentation
  uninterpreted?: boolean;
  line_break?: boolean;
}

export interface Transliteration {
  signum: string;
  transliteration: string;
  part: string | null; // a part stone's section (Sö 137A)
  sections: string[];
  tokens: TranslitToken[];
  source: { database: string; version: string; licence: string; signum: string; publisher: string };
}

export type MarkStep =
  | { kind: "mark"; xy: [number, number]; tokens: number[] } // one click; tokens empty for a plain mark
  | { kind: "skip"; token: number }; // a rune that cannot be seen

// The 3D anchor of a mark (POST /api/3d/rune_anchors)
export interface RuneAnchor {
  image_xy: [number, number];
  plane_mm: [number, number];
  point_mm: [number, number, number] | null;
  height_from: "modellen" | "snitten" | null;
  normal_or_view: {
    normal: [number, number, number];
    view: { position: [number, number, number]; target: [number, number, number]; up: [number, number, number] } | null;
    source: string;
  };
}

// The links as the export sends them (result.rune_edition): the engine adds the 3D anchors
export interface RuneEdition {
  signum: string;
  labeller: string;
  created: string;
  transliteration: { text: string; source: Transliteration["source"]; part: string | null };
  tokens: TranslitToken[];
  rune_links: { mark: number; token_index: number; tokens: number[]; char: string; image_xy: [number, number] }[];
  skipped_tokens: number[];
  image_width: number;
  image_height: number;
}

export const LINKABLE: ReadonlySet<TokenKind> = new Set<TokenKind>(["rune", "uncertain", "lost"]);

export function marksOf(steps: MarkStep[]): [number, number][] {
  return steps.flatMap(s => (s.kind === "mark" ? [s.xy] : []));
}

/** The links in mark order: mark k is the k-th click. */
export function linksOf(steps: MarkStep[]): { mark: number; xy: [number, number]; tokens: number[] }[] {
  let k = -1;
  return steps.flatMap(s => {
    if (s.kind !== "mark") return [];
    k += 1;
    return s.tokens.length ? [{ mark: k, xy: s.xy, tokens: s.tokens }] : [];
  });
}

export function skippedOf(steps: MarkStep[]): number[] {
  return steps.flatMap(s => (s.kind === "skip" ? [s.token] : []));
}

/** Which mark (click number from 0) each linked token belongs to. */
export function markOfToken(steps: MarkStep[]): Map<number, number> {
  const out = new Map<number, number>();
  for (const l of linksOf(steps)) for (const t of l.tokens) out.set(t, l.mark);
  return out;
}

/** The next rune to link: the first linkable token after the last one handled (linked or skipped), within the
 *  chosen section. null when every rune is handled. */
export function nextToken(tokens: TranslitToken[], steps: MarkStep[], section: string | null = null): number | null {
  let last = -1;
  for (const s of steps) {
    const ts = s.kind === "mark" ? s.tokens : [s.token];
    for (const t of ts) last = Math.max(last, t);
  }
  const hit = tokens.find(t => t.i > last && LINKABLE.has(t.kind) && (section === null || t.section === section));
  return hit ? hit.i : null;
}

/** The linkable token after token i (for a bind rune), or null. */
export function followingToken(tokens: TranslitToken[], i: number, section: string | null = null): number | null {
  const hit = tokens.find(t => t.i > i && LINKABLE.has(t.kind) && (section === null || t.section === section));
  return hit ? hit.i : null;
}

export function buildEdition(tr: Transliteration | null, steps: MarkStep[], labeller: string, signum: string,
  size: { width: number; height: number }): RuneEdition | null {
  const links = linksOf(steps);
  if (!tr || !links.length) return null;
  const byI = new Map(tr.tokens.map(t => [t.i, t]));
  return {
    signum: signum || tr.signum,
    labeller,
    created: new Date().toISOString(),
    transliteration: { text: tr.transliteration, source: tr.source, part: tr.part },
    tokens: tr.tokens,
    rune_links: links.map(l => ({
      mark: l.mark, token_index: l.tokens[0], tokens: l.tokens,
      char: l.tokens.map(t => byI.get(t)?.char ?? "").join(""), image_xy: l.xy,
    })),
    skipped_tokens: skippedOf(steps),
    image_width: size.width,
    image_height: size.height,
  };
}

// One request per signum and page load; a failure is not kept, so that a later attempt tries again
const cache = new Map<string, Promise<Transliteration | null>>();
function loadTransliteration(signum: string): Promise<Transliteration | null> {
  let hit = cache.get(signum);
  if (!hit) {
    hit = fetch(`${API_URL}/api/rundata/tokens?signum=${encodeURIComponent(signum)}`).then(async res => {
      if (res.status === 404) return null;
      if (!res.ok) throw new Error(`Fel ${res.status}`);
      return (await res.json()) as Transliteration;
    });
    hit.catch(() => cache.delete(signum));
    cache.set(signum, hit);
  }
  return hit;
}

export type TransliterationState =
  | { status: "none" } // no signum, or Rundata has no transliteration
  | { status: "loading" }
  | { status: "error" }
  | { status: "ok"; data: Transliteration };

/** The stone's transliteration as tokens, fetched when the signum has rested for a moment. */
export function useTransliteration(signum: string): TransliterationState {
  const key = signum.trim();
  const [got, setGot] = useState<{ key: string; state: TransliterationState } | null>(null);
  useEffect(() => {
    if (!key) return;
    let live = true;
    const timer = setTimeout(() => {
      loadTransliteration(key)
        .then(data => { if (live) setGot({ key, state: data ? { status: "ok", data } : { status: "none" } }); })
        .catch(() => { if (live) setGot({ key, state: { status: "error" } }); });
    }, 400);
    return () => { live = false; clearTimeout(timer); };
  }, [key]);
  if (!key) return { status: "none" };
  return got?.key === key ? got.state : { status: "loading" };
}
