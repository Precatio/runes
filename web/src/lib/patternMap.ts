// The pattern map's data and colours, without Leaflet, so that pages can use them in the server render
// (the maps themselves are in src/components/PatternMap.tsx, loaded only in the browser)

// A stone in the pattern map (GET /api/research/pattern-map): place, mid-year of the style group and, per pattern,
// 1 (has it), 0 (lacks it) or null (cannot be decided, e.g. illegible text)
export interface PatternStone { s: string; lat: number; lon: number; p: string; y: number | null; v: Record<string, 0 | 1 | null> }

// Sequential blue, light → dark (dataviz reference ramp, steps 150–700): the share of stones with the pattern
export const SHARE_CLASSES: { max: number; color: string; label: string }[] = [
  { max: 0.2, color: "#b7d3f6", label: "0–20 %" },
  { max: 0.4, color: "#86b6ef", label: "20–40 %" },
  { max: 0.6, color: "#3987e5", label: "40–60 %" },
  { max: 0.8, color: "#1c5cab", label: "60–80 %" },
  { max: 1.01, color: "#0d366b", label: "80–100 %" },
];
export const TOO_FEW = "#e7e5e0";
export const colorOf = (share: number) => SHARE_CLASSES.find(c => share < c.max)?.color ?? SHARE_CLASSES[4].color;

/** The share per province, as a table beside the map (the same numbers without the map). */
export function provinceTable(stones: PatternStone[], key: string) {
  const by = new Map<string, { n: number; k: number }>();
  for (const st of stones) {
    const val = st.v[key];
    if (val === null || val === undefined) continue;
    const c = by.get(st.p) ?? { n: 0, k: 0 };
    c.n += 1; c.k += val;
    by.set(st.p, c);
  }
  return [...by.entries()].map(([p, c]) => ({ p, ...c, share: c.k / c.n })).sort((a, b) => b.n - a.n);
}

/** The share in the whole corpus and before and after about 1050 (the stones with a dated style group). */
export function periodShares(stones: PatternStone[], key: string) {
  const out = { all: { n: 0, k: 0 }, early: { n: 0, k: 0 }, late: { n: 0, k: 0 } };
  for (const st of stones) {
    const val = st.v[key];
    if (val === null || val === undefined) continue;
    out.all.n += 1; out.all.k += val;
    if (st.y === null) continue;
    const c = st.y < 1050 ? out.early : out.late;
    c.n += 1; c.k += val;
  }
  return out;
}
