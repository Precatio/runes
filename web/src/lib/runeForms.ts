// Rune crops (runutsnitt) beyond the image they were cut from: turning a crop so the rune stands upright, a new form
// description after the turn (src/graphemes.py via /api/2d/extract_features), the form likeness between crops, and the
// crops grouped by stone and by carver. Used by "Bilder och runformer" on the 3D page and by "Jämför två stenar".
import { API_URL } from "@/lib/api";
import { db, type PaleographicCrop } from "@/lib/db";
import type { Carver } from "@/lib/rundata";

export interface CropWithStone {
  crop: PaleographicCrop;
  projectId: string;
  signum: string;
}

/** Cosine likeness of two form vectors (1 = the same form). */
export function cosine(a: number[], b: number[]) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return na && nb ? dot / Math.sqrt(na * nb) : 0;
}

/** Two crops can be compared when both have a form vector of the same description version. */
export const comparable = (a: PaleographicCrop, b: PaleographicCrop) =>
  !!a.featureVector && !!b.featureVector && !!a.featureVersion && a.featureVersion === b.featureVersion;

/** Every saved crop in the user's projects, with the stone it belongs to. */
export async function loadAllCrops(): Promise<CropWithStone[]> {
  const projects = await db.getProjects();
  return projects.flatMap(p => (p.paleographicCrops ?? []).map(crop => ({ crop, projectId: p.id, signum: p.metaText || p.name })));
}

// The colour of the crop's border (median brightness), so the corners a turn opens up look like the stone around the rune
function borderGrey(src: HTMLCanvasElement): string {
  const ctx = src.getContext("2d")!;
  const { width: w, height: h } = src;
  const d = ctx.getImageData(0, 0, w, h).data;
  const vals: number[] = [];
  const take = (x: number, y: number) => { const i = (y * w + x) * 4; vals.push((d[i] + d[i + 1] + d[i + 2]) / 3); };
  for (let x = 0; x < w; x++) { take(x, 0); take(x, h - 1); }
  for (let y = 0; y < h; y++) { take(0, y); take(w - 1, y); }
  vals.sort((a, b) => a - b);
  const g = Math.round(vals[Math.floor(vals.length / 2)] ?? 255);
  return `rgb(${g},${g},${g})`;
}

/** The crop turned clockwise by deg degrees, on a canvas large enough for the whole turned crop. */
export function rotateCanvas(src: HTMLCanvasElement, deg: number): HTMLCanvasElement {
  const r = (deg * Math.PI) / 180;
  const c = Math.abs(Math.cos(r)), s = Math.abs(Math.sin(r));
  const w = src.width, h = src.height;
  const out = document.createElement("canvas");
  out.width = Math.max(1, Math.round(w * c + h * s));
  out.height = Math.max(1, Math.round(w * s + h * c));
  const ctx = out.getContext("2d")!;
  ctx.fillStyle = borderGrey(src);
  ctx.fillRect(0, 0, out.width, out.height);
  ctx.translate(out.width / 2, out.height / 2);
  ctx.rotate(r);
  ctx.drawImage(src, -w / 2, -h / 2);
  return out;
}

/** A canvas scaled down so its longer side is at most maxSide. */
export function scaledCanvas(src: HTMLCanvasElement, maxSide: number): HTMLCanvasElement {
  const k = Math.min(1, maxSide / Math.max(src.width, src.height));
  if (k >= 1) return src;
  const out = document.createElement("canvas");
  out.width = Math.max(1, Math.round(src.width * k));
  out.height = Math.max(1, Math.round(src.height * k));
  out.getContext("2d")!.drawImage(src, 0, 0, out.width, out.height);
  return out;
}

export async function canvasFromDataUrl(url: string): Promise<HTMLCanvasElement> {
  const img = new Image();
  img.src = url;
  await img.decode();
  const c = document.createElement("canvas");
  c.width = img.naturalWidth;
  c.height = img.naturalHeight;
  c.getContext("2d")!.drawImage(img, 0, 0);
  return c;
}

/** The form description of a crop image (src/graphemes.py). */
export async function describeForm(canvas: HTMLCanvasElement): Promise<{ vector: number[]; version: string; formPng: string }> {
  const res = await fetch(`${API_URL}/api/2d/extract_features`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_base64: canvas.toDataURL("image/png") }),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Kunde inte beskriva runformen.");
  const f = await res.json();
  return { vector: f.feature_vector, version: f.feature_version, formPng: f.form_png };
}

/** A saved crop turned by deg more degrees: a new thumbnail and form description from the turned thumbnail. The
 * thumbnail is all that is kept of the crop, so each turn resamples it; a turn of 90° steps loses nothing. */
export async function turnCrop(crop: PaleographicCrop, deg: number): Promise<PaleographicCrop> {
  const src = await canvasFromDataUrl(crop.imageBase64);
  const turned = rotateCanvas(src, deg);
  const side = Math.max(src.width, src.height);
  const thumb = scaledCanvas(turned, side);
  const png = crop.imageBase64.startsWith("data:image/png");
  const form = await describeForm(turned);
  const auto = !!crop.auto;
  return {
    ...crop,
    imageBase64: thumb.toDataURL(png ? "image/png" : "image/jpeg", auto ? 0.7 : 0.8),
    featureVector: auto ? form.vector.map(v => Math.round(v * 1000) / 1000) : form.vector,
    featureVersion: form.version,
    formPng: form.formPng,
    rotationDeg: (((crop.rotationDeg ?? 0) + deg) % 360 + 540) % 360 - 180,
  };
}

/** Replaces one crop in its project (after a turn or a new rune tag), or removes it when updated is null. */
export async function saveCrop(projectId: string, cropId: string, updated: PaleographicCrop | null) {
  const p = await db.getProject(projectId);
  if (!p) throw new Error("Projektet finns inte längre.");
  const crops = (p.paleographicCrops ?? []).flatMap(c => (c.id !== cropId ? [c] : updated ? [updated] : []));
  await db.saveProject({ id: projectId, paleographicCrops: crops });
}

/** Carvers Rundata names for certain (signed or attributed, not marked uncertain), and the uncertain ones. */
export function carversOf(carvers: Carver[] | undefined): { certain: string[]; uncertain: string[] } {
  const named = (carvers ?? []).filter(c => c.kind === "S" || c.kind === "A");
  return { certain: named.filter(c => !c.uncertain).map(c => c.name), uncertain: named.filter(c => c.uncertain).map(c => c.name) };
}

export interface LikenessSummary { mean: number; n: number }
/** Mean likeness over all pairs between two groups of crops (or within one group, when b is omitted). */
export function meanLikeness(a: PaleographicCrop[], b?: PaleographicCrop[]): LikenessSummary {
  let sum = 0, n = 0;
  if (!b) {
    for (let i = 0; i < a.length; i++) for (let j = i + 1; j < a.length; j++) {
      if (comparable(a[i], a[j])) { sum += cosine(a[i].featureVector!, a[j].featureVector!); n++; }
    }
  } else {
    for (const x of a) for (const y of b) if (comparable(x, y)) { sum += cosine(x.featureVector!, y.featureVector!); n++; }
  }
  return { mean: n ? sum / n : NaN, n };
}
