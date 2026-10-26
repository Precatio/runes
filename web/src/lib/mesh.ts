// A 3D scan is uploaded to the analysis engine once and then referred to by its id (SHA-256).
import { API_URL } from "@/lib/api";
import type { Metric, SliceMetrics } from "@/lib/metrics";

export interface MeshInfo {
  mesh_id: string;
  filename: string;
  sha256: string;
  md5?: string; // what Zenodo publishes for its files (src/scan_sources.identify)
  bytes?: number;
  vertices: number;
  faces: number;
  extent_mm: number[];
  centered_by: number[];
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function errorFrom(res: Response): Promise<ApiError> {
  const body = await res.json().catch(() => null);
  return new ApiError(res.status, body?.detail || `Fel ${res.status}`);
}

function uploadWithProgress(file: File, onProgress?: (fraction: number) => void): Promise<MeshInfo> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/api/3d/upload`);
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) onProgress?.(e.loaded / e.total);
    };
    xhr.onload = () => {
      let body: { detail?: string } & Partial<MeshInfo> = {};
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // keep empty body
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as MeshInfo);
      else reject(new ApiError(xhr.status, body.detail || `Uppladdningen misslyckades (${xhr.status})`));
    };
    xhr.onerror = () => reject(new ApiError(0, "Analysmotorn svarar inte. Är backend startad?"));
    const fd = new FormData();
    fd.append("file", file);
    xhr.send(fd);
  });
}

export class MeshSession {
  info: MeshInfo | null = null;
  private pending: Promise<MeshInfo> | null = null;

  constructor(public file: File, private onProgress?: (fraction: number) => void) {}

  ensure(): Promise<MeshInfo> {
    if (this.info) return Promise.resolve(this.info);
    if (!this.pending) {
      this.pending = uploadWithProgress(this.file, this.onProgress)
        .then(info => {
          this.info = info;
          return info;
        })
        .finally(() => {
          this.pending = null;
        });
    }
    return this.pending;
  }

  // POST form fields with mesh_id; if the engine has forgotten the model (404), upload again once. The signal aborts
  // the request (not an upload already under way)
  async post(path: string, fields: Record<string, string | number | boolean>, signal?: AbortSignal): Promise<Response> {
    for (let attempt = 0; attempt < 2; attempt++) {
      const info = await this.ensure();
      signal?.throwIfAborted();
      const fd = new FormData();
      fd.append("mesh_id", info.mesh_id);
      for (const [k, v] of Object.entries(fields)) fd.append(k, String(v));
      const res = await fetch(`${API_URL}${path}`, { method: "POST", body: fd, signal });
      if (res.status === 404 && attempt === 0) {
        this.info = null;
        continue;
      }
      if (!res.ok) throw await errorFrom(res);
      return res;
    }
    throw new ApiError(404, "3D-modellen kunde inte laddas upp igen.");
  }

  async postJSON<T>(path: string, fields: Record<string, string | number | boolean>): Promise<T> {
    return (await this.post(path, fields)).json();
  }
}

// ---- Automatic groove analysis ---------------------------------------------------------

export type AutoLabel = "rune" | "ornament" | "unknown" | "excluded";

export type StrokeKind = "rune" | "ornament" | "irregular" | "isolated";
// With runic bands (src/rune_bands.py) a groove may also be a band edge or lie just outside a band
export type GrooveKind = StrokeKind | "band" | "border";

export interface AutoSlice extends Partial<SliceMetrics> {
  accepted: boolean;
  reason: string | null;
  feature?: GrooveKind; // what the groove at this point was recognised as
  band?: "runa" | "slingkant" | "gräns" | "utanför"; // its place relative to the runic bands, when they decided
  rune_id?: number;
  stroke_id?: number;
  halfwidth_mm: number;
  position_mm: number;
  fit_r2?: number;
  img_x: number;
  img_y: number;
  point?: [number, number, number];
  direction?: [number, number, number];
  up?: [number, number, number];
  profile?: { x: number[]; z: number[] };
}

export interface AutoAnalysisResult {
  slices: AutoSlice[];
  image_base64: string;
  groove_map_base64: string;
  image_width: number;
  image_height: number;
  angle_color_range: [number, number];
  counts: {
    candidates: number;
    accepted: number;
    rejected: number;
    rejection_reasons: Record<string, number>;
    groove_area_mm2: number;
    wide_area_mm2: number;
    strokes?: Partial<Record<StrokeKind, number>>;
    runes_identified?: number;
    runes_measured?: number;
  };
  parameters: Record<string, number | number[] | boolean | string | null>;
  // Where the runic bands came from ("ritade": drawn and checked by hand; "modellen": the band model's proposal) and how
  // much of the scan they cover; source null when the old stroke classification decided
  bands?: { source: "ritade" | "modellen" | null; coverage?: number; note?: string };
  summary?: Record<Metric, import("@/lib/metrics").Summary>;
  // Stone means with the rune as unit (n = runes), present when only runes were measured
  rune_summary?: { n_runes: number; metrics: Record<Metric, import("@/lib/metrics").Summary & { n_slices: number; icc: number | null }> };
  // n_strokes and height_mm are null for runes marked by hand (withMarkedRunes)
  runes?: { id: number; n_strokes: number | null; height_mm: number | null; n_slices: number; box?: number[] }[];
  provenance: import("@/lib/db").AnalysisProvenance;
}

// Guideline numbers of measured runes (METHODS.md, 3; same as src/limitations.py): 10 to describe a stone,
// 20 to compare stones. Guidelines, not a standard – see the known limitations.
export const MIN_RUNES_DESCRIBE = 10;
export const MIN_RUNES_COMPARE = 20;

export function runeSampleNote(n: number): { ok: boolean; text: string } {
  if (n >= MIN_RUNES_COMPARE) return { ok: true, text: `${n} runor mätta – över riktvärdet ${MIN_RUNES_COMPARE} för jämförelser med andra stenar (en tumregel, inte en garanti).` };
  if (n >= MIN_RUNES_DESCRIBE) return { ok: true, text: `${n} runor mätta – över riktvärdet ${MIN_RUNES_DESCRIBE} för att beskriva stenen; för jämförelser med andra stenar är riktvärdet ${MIN_RUNES_COMPARE}.` };
  return { ok: false, text: `Bara ${n} runor mätta – under riktvärdet ${MIN_RUNES_DESCRIBE} för att beskriva stenen (${MIN_RUNES_COMPARE} för jämförelser); medelvärdena är mycket osäkra. Prova högre känslighet, en bättre vinkel eller mät fler runor för hand.` };
}

// Runes marked by hand in the review image: one click per rune, in reading order. Every cross-section labelled as a
// rune goes to the nearest mark, so the rune (not the slice) becomes the unit without anyone knowing which rune it
// is. A slice further than MARK_REACH times the median distance between neighbouring marks belongs to none (the
// gap between two bands, a rune left unmarked). The marks replace the automatic rune grouping everywhere downstream
// (results, comparisons, exports); the slices keep their measurements.
export const MARK_REACH = 1.5;

export function withMarkedRunes(result: AutoAnalysisResult, labels: AutoLabel[], marks: [number, number][]): AutoAnalysisResult {
  if (!marks.length) return result;
  const gaps = marks.slice(1).map((m, i) => Math.hypot(m[0] - marks[i][0], m[1] - marks[i][1])).sort((a, b) => a - b);
  const reach = gaps.length ? MARK_REACH * gaps[Math.floor(gaps.length / 2)] : Infinity;
  const slices = result.slices.map((s, i) => {
    let best = -1, bestD = reach;
    if (s.accepted && labels[i] === "rune") {
      marks.forEach((m, k) => { const d = Math.hypot(s.img_x - m[0], s.img_y - m[1]); if (d <= bestD) { bestD = d; best = k; } });
    }
    return { ...s, rune_id: best >= 0 ? best + 1 : undefined };
  });
  const W = result.image_width, H = result.image_height;
  const runes = marks.flatMap((_, k) => {
    const own = slices.filter(s => s.rune_id === k + 1);
    if (!own.length) return [];
    const xs = own.map(s => s.img_x), ys = own.map(s => s.img_y);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const pad = 6 + 0.1 * Math.max(x1 - x0, y1 - y0); // the slice centres, widened for the grooves and stroke ends
    return [{ id: k + 1, n_strokes: null, height_mm: null, n_slices: own.length,
              box: [Math.max(0, (x0 - pad) / W), Math.max(0, (y0 - pad) / H), Math.min(1, (x1 + pad) / W),
                    Math.min(1, (y1 + pad) / H)].map(v => Math.round(v * 1e4) / 1e4) }];
  });
  const marked = { n_marks: marks.length, reach_px: Number.isFinite(reach) ? Math.round(reach) : null, by: "hand" };
  return {
    ...result, slices, runes,
    counts: { ...result.counts, runes_identified: marks.length, runes_measured: runes.length },
    parameters: { ...result.parameters, runes_marked_by_hand: marks.length },
    provenance: { ...result.provenance, parameters: { ...result.provenance.parameters, rune_marks: marked } },
  };
}

// Same colour scale as the backend's review image (viridis over the angle range)
const VIRIDIS = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"];
export function angleColor(angle: number, [lo, hi]: [number, number]): string {
  const t = Math.min(1, Math.max(0, (angle - lo) / (hi - lo)));
  return VIRIDIS[Math.min(VIRIDIS.length - 1, Math.floor(t * VIRIDIS.length))];
}
