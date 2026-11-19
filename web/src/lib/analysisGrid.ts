// The analysis grid of a groove measurement (parameters.resolution_mm, fixed_resolution, harmonize_mm) and whether
// several measurements share it. A coarser grid moves the levels: in the locked test of 2026-11-19
// (utdata/sakra_runor/resultat.md) the grid 1.2 mm instead of 0.6 mm gave, on the same scans, a V-angle about 1.9°
// larger (2.9° on Zedig's scans) and a groove width about 0.95 mm larger. So stones are compared only on a common grid.
// Kept free of imports, so that tests/test_analysis_grid.py can run it with node; src/analysis_grid.py is the same rule.

export const PROTOCOL_GRID_MM = 0.6; // src/protocol.PARAMETERS.resolution_mm
export const GRID_TOLERANCE_MM = 0.01; // grids closer than this count as the same

export interface GridInfo {
  resolution_mm: number | null;
  fixed: boolean | null;
  harmonize_mm: number | null;
}

type Params = Record<string, unknown> | null | undefined;

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

/** The grid of a measurement, from its parameters (or provenance.parameters). */
export function gridOf(params: Params): GridInfo {
  const p = params ?? {};
  return {
    resolution_mm: num(p.resolution_mm),
    fixed: typeof p.fixed_resolution === "boolean" ? p.fixed_resolution : null,
    harmonize_mm: num(p.harmonize_mm) || null, // 0 and null both mean no harmonisation
  };
}

export function sameGrid(a: GridInfo, b: GridInfo): boolean | null {
  if (a.resolution_mm === null || b.resolution_mm === null) return null;
  return Math.abs(a.resolution_mm - b.resolution_mm) < GRID_TOLERANCE_MM
    && Math.abs((a.harmonize_mm ?? 0) - (b.harmonize_mm ?? 0)) < GRID_TOLERANCE_MM;
}

const mm = (v: number) => `${v.toFixed(2).replace(".", ",")} mm`;

/** A short label, e.g. "0,60 mm" or "0,85 mm (följer skanningen), harmonisering 1,00 mm". */
export function gridLabel(g: GridInfo): string {
  if (g.resolution_mm === null) return "okänt rutnät";
  return mm(g.resolution_mm) + (g.fixed === false ? " (följer skanningen)" : "")
    + (g.harmonize_mm ? `, harmonisering ${mm(g.harmonize_mm)}` : "");
}

export const GRID_EFFECT_TEXT =
  "Ett grövre analysrutnät flyttar måtten: i provet 2026-11-19 gav rutnätet 1,2 mm i stället för 0,6 mm, på samma " +
  "skanningar, omkring 2° större V-vinkel (1,9° på skanningarna från Södermanland, 2,9° på dem från Medelpad och " +
  "Hälsingland) och omkring 1 mm " +
  "större spårbredd. Skillnader mellan mätningar med olika rutnät kan alltså komma av rutnätet och inte av stenarna.";

export const GRID_REMEDY_TEXT =
  "Mät om med samma rutnät: analysera skanningen i 3D-vyn med Vitki-protokollet (fast rutnät 0,6 mm).";

export interface GridMix {
  groups: { label: string; resolution_mm: number | null; n: number }[];
  mixed: boolean; // more than one known grid
  unknown: number; // measurements without a recorded grid
}

/** The grids among several measurements, most common first. */
export function gridMix(grids: GridInfo[]): GridMix {
  const groups: GridMix["groups"] = [];
  const reps: GridInfo[] = [];
  let unknown = 0;
  for (const g of grids) {
    if (g.resolution_mm === null) { unknown += 1; continue; }
    const k = reps.findIndex(r => sameGrid(r, g));
    if (k >= 0) groups[k].n += 1;
    else { reps.push(g); groups.push({ label: gridLabel(g), resolution_mm: g.resolution_mm, n: 1 }); }
  }
  groups.sort((a, b) => b.n - a.n);
  return { groups, mixed: groups.length > 1, unknown };
}

/** The warning for several measurements, or null when they share one grid. */
export function gridMixWarning(mix: GridMix): string | null {
  if (!mix.mixed) return null;
  const parts = mix.groups.map(g => `${g.label}: ${g.n}`).join(", ");
  return `Mätningarna är gjorda med ${mix.groups.length} olika analysrutnät (${parts}${mix.unknown ? `; ${mix.unknown} utan uppgift` : ""}). `
    + GRID_EFFECT_TEXT;
}
