// A 3D scan is uploaded to the analysis engine once and then referred to by its id (SHA-256).
import { API_URL } from "@/lib/api";
import type { Metric, SliceMetrics } from "@/lib/metrics";

export interface MeshInfo {
  mesh_id: string;
  filename: string;
  sha256: string;
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

  // POST form fields with mesh_id; if the engine has forgotten the model (404), upload again once
  async post(path: string, fields: Record<string, string | number | boolean>): Promise<Response> {
    for (let attempt = 0; attempt < 2; attempt++) {
      const info = await this.ensure();
      const fd = new FormData();
      fd.append("mesh_id", info.mesh_id);
      for (const [k, v] of Object.entries(fields)) fd.append(k, String(v));
      const res = await fetch(`${API_URL}${path}`, { method: "POST", body: fd });
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

export interface AutoSlice extends Partial<SliceMetrics> {
  accepted: boolean;
  reason: string | null;
  feature?: StrokeKind; // what the groove at this point was recognised as
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
  parameters: Record<string, number | number[] | boolean>;
  summary?: Record<Metric, import("@/lib/metrics").Summary>;
  // Stone means with the rune as unit (n = runes), present when only runes were measured
  rune_summary?: { n_runes: number; metrics: Record<Metric, import("@/lib/metrics").Summary & { n_slices: number; icc: number | null }> };
  runes?: { id: number; n_strokes: number; height_mm: number; n_slices: number }[];
  provenance: import("@/lib/db").AnalysisProvenance;
}

// Guideline numbers of measured runes (METHODS.md, 2; same as src/limitations.py): 10 to describe a stone,
// 20 to compare stones. Guidelines, not a standard – see the known limitations.
export const MIN_RUNES_DESCRIBE = 10;
export const MIN_RUNES_COMPARE = 20;

export function runeSampleNote(n: number): { ok: boolean; text: string } {
  if (n >= MIN_RUNES_COMPARE) return { ok: true, text: `${n} runor mätta – över riktvärdet ${MIN_RUNES_COMPARE} för jämförelser med andra stenar (en tumregel, inte en garanti).` };
  if (n >= MIN_RUNES_DESCRIBE) return { ok: true, text: `${n} runor mätta – över riktvärdet ${MIN_RUNES_DESCRIBE} för att beskriva stenen; för jämförelser med andra stenar är riktvärdet ${MIN_RUNES_COMPARE}.` };
  return { ok: false, text: `Bara ${n} runor mätta – under riktvärdet ${MIN_RUNES_DESCRIBE} för att beskriva stenen (${MIN_RUNES_COMPARE} för jämförelser); medelvärdena är mycket osäkra. Prova högre känslighet, en bättre vinkel eller mät fler runor för hand.` };
}

// Same colour scale as the backend's review image (viridis over the angle range)
const VIRIDIS = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"];
export function angleColor(angle: number, [lo, hi]: [number, number]): string {
  const t = Math.min(1, Math.max(0, (angle - lo) / (hi - lo)));
  return VIRIDIS[Math.min(VIRIDIS.length - 1, Math.floor(t * VIRIDIS.length))];
}
