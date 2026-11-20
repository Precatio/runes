// Djupfärger i 3D-vyn (POST /api/3d/depth_field, METHODS.md 2d4): the depth below the reference surface (mm, positive
// downwards) as a grid in the model's own coordinates. The viewer looks it up per pixel on the GPU, so the colour
// bands, the peel slider and the contours change in real time.
import type { MeshSession } from "@/lib/mesh";

export interface DepthField {
  width: number;
  height: number;
  res_mm: number;
  origin: [number, number];            // the grid's corner in (u, v), mm
  u: [number, number, number];
  v: [number, number, number];
  n: [number, number, number];         // the view the depth is measured along (out of the carved face)
  level_mm: number;                    // the common level of Runor och ornamentik (70th percentile)
  percentiles: Record<string, number>; // "50", "70", "90", "99"
  depth: Float32Array;                 // row by row (row = v, column = u); NaN = no depth
}

export type DepthScheme = "fast" | "sten";
export type PeelMode = "yta" | "plan";

export interface DepthSettings {
  scheme: DepthScheme;  // fixed millimetre bands, or bands from this stone's own depths
  peel: number;         // mm: what lies shallower is peeled off (shown pale) – "längs ytan"
  peelMode: PeelMode;   // "yta": along the stone's surface; "plan": a flat cut from the top, as a 3D-print slicer
  plane: number;        // 0–1: how far down the flat cut has come
  strength: number;     // 0–1: how strongly the colour covers the shaded stone
  contour: number;      // mm between depth contours, 0 = none
  only: number | null;  // one colour band only (0–3, the deepest = "3 mm och djupare"); the rest pale; null = all
}

export const DEFAULT_DEPTH: DepthSettings = { scheme: "fast", peel: -5, peelMode: "yta", plane: 0, strength: 0.85, contour: 0, only: null };

// Sand, orange, rust, dark rust: the deeper, the darker (no violet, house colours)
export const DEPTH_COLORS = ["#e9c46a", "#f4a261", "#b7410e", "#5c1f05"] as const;
export const FIXED_EDGES: [number, number, number, number] = [0.5, 1, 2, 3];

/** The band edges (mm) the colours start at: fixed, or from the stone's own depth (its common level, the 90th and the
 *  99th percentile and a step between them), so that a shallow stone also gets all four colours. */
export function bandEdges(field: DepthField | null, scheme: DepthScheme): [number, number, number, number] {
  if (scheme === "fast" || !field) return FIXED_EDGES;
  const p = field.percentiles;
  const e0 = Math.max(0.1, field.level_mm), e1 = Math.max(e0 + 0.1, p["90"] ?? e0 + 0.5);
  const e3 = Math.max(e1 + 0.2, p["99"] ?? e1 + 1);
  return [e0, e1, (e1 + e3) / 2, e3];
}

export async function fetchDepthField(session: MeshSession, view: { toward: number[]; up: number[] } | null): Promise<DepthField> {
  const fields: Record<string, number> = view ? {
    normal_x: view.toward[0], normal_y: view.toward[1], normal_z: view.toward[2],
    up_x: view.up[0], up_y: view.up[1], up_z: view.up[2],
  } : {};
  const res = await session.post("/api/3d/depth_field", fields);
  const head = res.headers.get("X-Depth-Field");
  if (!head) throw new Error("Djupet kom utan sin beskrivning (X-Depth-Field).");
  const meta = JSON.parse(head);
  const q = new Uint16Array(await res.arrayBuffer());
  const depth = new Float32Array(q.length);
  const scale = meta.depth_span / 65534;
  for (let i = 0; i < q.length; i++) depth[i] = q[i] === 0 ? NaN : meta.depth_min + (q[i] - 1) * scale;
  return { ...meta, depth };
}

/** The depth under a point in the model's coordinates (mm), or null outside the grid. */
export function depthAt(field: DepthField, p: [number, number, number]): number | null {
  const a = p[0] * field.u[0] + p[1] * field.u[1] + p[2] * field.u[2] - field.origin[0];
  const b = p[0] * field.v[0] + p[1] * field.v[1] + p[2] * field.v[2] - field.origin[1];
  const col = Math.floor(a / field.res_mm), row = Math.floor(b / field.res_mm);
  if (col < 0 || row < 0 || col >= field.width || row >= field.height) return null;
  const d = field.depth[row * field.width + col];
  return Number.isFinite(d) ? d : null;
}

const hex = (c: string): [number, number, number] => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)) as [number, number, number];

/** The depth map straight from above (north up, u to the right) at the grid's full resolution, `scale` times enlarged,
 *  coloured as in the 3D view (bands, peel along the surface, one band only, contours) over a hillshade of the depth
 *  itself, with a scale bar. A PNG blob, for printing and articles. */
export async function depthMapPng(field: DepthField, s: DepthSettings, scale = 2): Promise<Blob> {
  const { width: W, height: H, depth, res_mm } = field;
  const e = bandEdges(field, s.scheme);
  const cols = DEPTH_COLORS.map(hex);
  const img = new ImageData(W, H);
  const at = (r: number, c: number) => depth[Math.min(H - 1, Math.max(0, r)) * W + Math.min(W - 1, Math.max(0, c))];
  for (let r = 0; r < H; r++) {
    for (let c = 0; c < W; c++) {
      const d = depth[r * W + c];
      const o = ((H - 1 - r) * W + c) * 4;  // north up: the grid's first row (smallest v) at the bottom
      if (!Number.isFinite(d)) { img.data[o + 3] = 0; continue; }
      // hillshade from the depth's slope (light from the upper left), so the carving reads as relief
      const dx = ((at(r, c + 1) || d) - (at(r, c - 1) || d)) / (2 * res_mm);
      const dy = ((at(r + 1, c) || d) - (at(r - 1, c) || d)) / (2 * res_mm);
      const shade = Math.max(0.35, Math.min(1, 0.8 + 0.35 * (dx - dy) / Math.sqrt(1 + dx * dx + dy * dy)));
      let rgb: [number, number, number] = [160 * shade, 165 * shade, 170 * shade];
      const band = d >= e[3] ? 3 : d >= e[2] ? 2 : d >= e[1] ? 1 : d >= e[0] ? 0 : -1;
      const pale = (s.peelMode === "yta" && d < s.peel) || (s.only != null && band !== s.only);
      if (pale) rgb = [240 * (0.85 + 0.15 * shade), 237 * (0.85 + 0.15 * shade), 232 * (0.85 + 0.15 * shade)];
      else if (band >= 0) rgb = rgb.map((v, i) => v * (1 - s.strength) + cols[band][i] * shade * s.strength) as [number, number, number];
      if (s.contour > 0) {
        const x = d / s.contour, f = Math.abs(x - Math.round(x));
        if (f < 0.06) rgb = rgb.map(v => v * 0.35) as [number, number, number];
      }
      img.data[o] = rgb[0]; img.data[o + 1] = rgb[1]; img.data[o + 2] = rgb[2]; img.data[o + 3] = 255;
    }
  }
  const base = document.createElement("canvas");
  base.width = W; base.height = H;
  base.getContext("2d")!.putImageData(img, 0, 0);
  const out = document.createElement("canvas");
  out.width = W * scale; out.height = H * scale;
  const g = out.getContext("2d")!;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, out.width, out.height);
  g.imageSmoothingEnabled = true;
  g.drawImage(base, 0, 0, out.width, out.height);
  // scale bar: 50 mm (10 mm on a small piece), lower left
  const pxPerMm = scale / res_mm;
  const len = W * res_mm > 300 ? 50 : 10;
  const x0 = 24 * scale, y0 = out.height - 24 * scale, bar = len * pxPerMm;
  g.fillStyle = "#111827";
  g.fillRect(x0, y0 - 4 * scale, bar, 4 * scale);
  g.font = `${11 * scale}px system-ui, sans-serif`;
  g.fillText(`${len} mm`, x0, y0 - 8 * scale);
  return new Promise((ok, fail) => out.toBlob(b => (b ? ok(b) : fail(new Error("Bilden kunde inte skapas."))), "image/png"));
}
