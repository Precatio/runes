// The pattern map's data and colours, without Leaflet, so that pages can use them in the server render
// (the maps themselves are in src/components/PatternMap.tsx, loaded only in the browser)

// A stone in the pattern map (GET /api/research/pattern-map): place, mid-year of the style group and, per pattern,
// 1 (has it), 0 (lacks it) or null (cannot be decided, e.g. illegible text)
export interface PatternStone {
  s: string; lat: number; lon: number; p: string; y: number | null; v: Record<string, 0 | 1 | null>;
  // Moved according to Rundata's placement (at a church, in a wall, a museum), and the distance (km) to the nearest
  // place of each kind (src/places.py)
  m?: number; d?: Record<string, number | null>;
}

// Places around the stones (GET /api/research/places): place names that suggest pre-Christian cult, medieval churches
// and registered ancient monuments
export interface PlaceKind { key: string; label: string; group: string; help: string }
export interface PlaceLayer { kind: string; label: string; points: [number, number, string, string][] }

// Colours that stand out against the blue hexagons; the ancient monuments are small and quiet
export const PLACE_STYLE: Record<string, { color: string; radius: number }> = {
  cult_a: { color: "#b7410e", radius: 6 }, cult_b: { color: "#e5883a", radius: 5 }, central: { color: "#7c3aed", radius: 5 },
  church: { color: "#111827", radius: 3 }, gravfalt: { color: "#7c6f64", radius: 2 }, hog: { color: "#a8a29e", radius: 2 },
  vag: { color: "#a16207", radius: 2 }, bro: { color: "#0f766e", radius: 3 }, fornborg: { color: "#be185d", radius: 4 },
};

// Clusters (circles) and hot or cold stones (markers) from the R analysis of hot spots (r/hotspots.R)
export interface MapCircle { lat: number; lon: number; radiusKm: number; color: string; label: string; dashed?: boolean }
export interface MapMarker { lat: number; lon: number; color: string; label: string }

/** The stones near a kind of place (within km), leaving out moved stones. */
export const nearPlace = (stones: PatternStone[], kind: string, km: number) =>
  stones.filter(st => !st.m && st.d?.[kind] != null && (st.d[kind] as number) < km);

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
