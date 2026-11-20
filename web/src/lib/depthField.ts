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
}

export const DEFAULT_DEPTH: DepthSettings = { scheme: "fast", peel: -5, peelMode: "yta", plane: 0, strength: 0.85, contour: 0 };

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
