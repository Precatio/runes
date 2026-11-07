"use client";

// Skala av vittringen (POST /api/3d/peel, src/peel.py, METHODS.md 2h): the carved surface with only what lies deeper
// than the weathering around it, the long narrow grooves in rust and the short pits in grey. A click removes a speck
// (it is not a rune) or brings it back; the removed specks are kept as points on the model in this browser, per scan,
// so that they follow when the slider moves. The label map (an RGB PNG, id = r + 256 g + 65536 b) lies exactly under
// the picture and tells which speck the pointer is on.
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { MeshSession } from "@/lib/mesh";

type Kind = "spar" | "grop";
type Point = [number, number, number];
interface PeelComp {
  id: number; kind: Kind; area_mm2: number; length_mm: number; width_mm: number; depth_mm: number;
  point: Point; removed: boolean; removed_by: number[];
}
interface PeelResult {
  background: string; labels: string; width: number; height: number; resolution_mm: number; offset_mm: number;
  offset_range: [number, number]; level_mm: { min: number; median: number; max: number }; components: PeelComp[];
}
interface View { toward: number[]; up: number[] }

const RUST: [number, number, number] = [0xb7, 0x41, 0x0e];
const SLATE: [number, number, number] = [0x94, 0xa3, 0xb8];
const INK: [number, number, number] = [0x0f, 0x17, 0x2a];
const fmt = (v: number, d = 1) => v.toFixed(d).replace(".", ",");
const storeKey = (sha: string) => `vitki-skala-av:${sha}`;
const errorText = (err: unknown, fallback: string) => (err instanceof Error ? err.message : fallback);

function readStored(sha: string): Point[] {
  try {
    const v = JSON.parse(localStorage.getItem(storeKey(sha)) || "[]");
    return Array.isArray(v) ? v.filter((p: unknown) => Array.isArray(p) && p.length === 3) : [];
  } catch {
    return [];
  }
}

function writeStored(sha: string, pts: Point[]) {
  try {
    localStorage.setItem(storeKey(sha), JSON.stringify(pts));
  } catch {
    /* private window or full storage: the clicks then last only while the dialog is open */
  }
}

async function bitmap(dataUrl: string): Promise<ImageBitmap> {
  const blob = await (await fetch(dataUrl)).blob();
  return createImageBitmap(blob, { colorSpaceConversion: "none", premultiplyAlpha: "none" });
}

async function decodeLabels(dataUrl: string, w: number, h: number): Promise<Uint32Array> {
  const bm = await bitmap(dataUrl);
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d", { willReadFrequently: true })!;
  ctx.drawImage(bm, 0, 0);
  const px = ctx.getImageData(0, 0, w, h).data;
  const ids = new Uint32Array(w * h);
  for (let i = 0; i < ids.length; i++) ids[i] = px[4 * i] + 256 * px[4 * i + 1] + 65536 * px[4 * i + 2];
  return ids;
}

export default function PeelDialog({ session, sha256, filename, view, onClose }: {
  session: MeshSession; sha256: string; filename: string; view: View | null; onClose: () => void;
}) {
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState<PeelResult | null>(null);
  const [comps, setComps] = useState<PeelComp[]>([]);
  const [points, setPoints] = useState<Point[]>(() => readStored(sha256));
  const [history, setHistory] = useState<Point[][]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPits, setShowPits] = useState(true);
  const [hover, setHover] = useState(0);
  const [refresh, setRefresh] = useState(0); // fetch again with the same setting (after undo or bringing back)
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const idsRef = useRef<Uint32Array | null>(null);
  const bgRef = useRef<ImageBitmap | null>(null);
  const pointsRef = useRef(points);
  useEffect(() => { pointsRef.current = points; }, [points]);

  // A new layer when the slider stops moving; the clicked-away points go along so that the server marks them
  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(async () => {
      setBusy(true);
      setError(null);
      try {
        const fields: Record<string, string | number> = { offset_mm: offset, removed_json: JSON.stringify(pointsRef.current) };
        if (view) {
          Object.assign(fields, { normal_x: view.toward[0], normal_y: view.toward[1], normal_z: view.toward[2],
            up_x: view.up[0], up_y: view.up[1], up_z: view.up[2] });
        }
        const data = await session.postJSON<PeelResult>("/api/3d/peel", fields);
        const [ids, bg] = await Promise.all([decodeLabels(data.labels, data.width, data.height), bitmap(data.background)]);
        if (cancelled) return;
        idsRef.current = ids;
        bgRef.current = bg;
        setResult(data);
        setComps(data.components);
      } catch (e) {
        if (!cancelled) setError(errorText(e, "Ytan kunde inte skalas av."));
      } finally {
        if (!cancelled) setBusy(false);
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(t); };
  }, [offset, refresh, session, view]);

  // Draw the picture and the coloured specks
  useEffect(() => {
    const canvas = canvasRef.current, ids = idsRef.current, bg = bgRef.current;
    if (!canvas || !ids || !bg || !result) return;
    const { width: w, height: h } = result;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d")!;
    ctx.drawImage(bg, 0, 0);
    const over = new ImageData(w, h);
    const byId = new Map(comps.map(c => [c.id, c]));
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      if (!id) continue;
      const c = byId.get(id);
      if (!c || c.removed) continue;
      if (c.kind === "grop" && !showPits && id !== hover) continue;
      const col = id === hover ? INK : c.kind === "spar" ? RUST : SLATE;
      over.data.set([col[0], col[1], col[2], c.kind === "spar" || id === hover ? 215 : 150], 4 * i);
    }
    const layer = document.createElement("canvas");
    layer.width = w;
    layer.height = h;
    layer.getContext("2d")!.putImageData(over, 0, 0);
    ctx.drawImage(layer, 0, 0);
  }, [result, comps, showPits, hover]);

  const idAt = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current, ids = idsRef.current;
    if (!canvas || !ids || !result) return 0;
    const r = canvas.getBoundingClientRect();
    const x = Math.floor(((e.clientX - r.left) / r.width) * result.width);
    const y = Math.floor(((e.clientY - r.top) / r.height) * result.height);
    if (x < 0 || y < 0 || x >= result.width || y >= result.height) return 0;
    return ids[y * result.width + x];
  }, [result]);

  const save = (next: Point[], nextComps: PeelComp[]) => {
    setHistory(h => [...h.slice(-49), points]);
    setPoints(next);
    setComps(nextComps);
    writeStored(sha256, next);
  };

  // Click: remove a speck (store its point) or bring it back (drop the points that hit it, and renumber the rest)
  const toggle = (id: number) => {
    const c = comps.find(x => x.id === id);
    if (!c) return;
    if (!c.removed) {
      const next: Point[] = [...points, c.point];
      save(next, comps.map(x => (x.id === id ? { ...x, removed: true, removed_by: [next.length - 1] } : x)));
      return;
    }
    const drop = new Set(c.removed_by);
    const newIndex = new Map<number, number>();
    const next: Point[] = [];
    points.forEach((p, i) => { if (!drop.has(i)) { newIndex.set(i, next.length); next.push(p); } });
    save(next, comps.map(x => x.id === id ? { ...x, removed: false, removed_by: [] }
      : { ...x, removed_by: x.removed_by.flatMap(i => (newIndex.has(i) ? [newIndex.get(i)!] : [])) }));
  };

  // Undo and "bring everything back" change the stored points; the next layer marks the specks anew
  const resetTo = (pts: Point[]) => {
    setPoints(pts);
    writeStored(sha256, pts);
    setRefresh(n => n + 1);
  };
  const undo = () => {
    const prev = history[history.length - 1];
    if (!prev) return;
    setHistory(h => h.slice(0, -1));
    resetTo(prev);
  };

  const download = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const a = document.createElement("a");
    a.href = canvas.toDataURL("image/png");
    a.download = `${filename.replace(/\.[^.]+$/, "")}_skalad_${fmt(offset)}mm.png`;
    a.click();
  };

  const nSpar = comps.filter(c => c.kind === "spar" && !c.removed).length;
  const nGrop = comps.filter(c => c.kind === "grop" && !c.removed).length;
  const nRemoved = comps.filter(c => c.removed).length;
  const hovered = comps.find(c => c.id === hover);
  const [lo, hi] = result?.offset_range ?? [-1, 3];

  // In document.body: the page's main column is its own stacking context, under the sidebar
  return createPortal(
    <div className="fixed inset-0 z-[600] bg-slate-900/50 flex items-center justify-center p-3" role="dialog" aria-modal="true" aria-label="Skala av vittringen">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-6xl max-h-[94vh] overflow-auto p-5 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Skala av vittringen</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Bilden visar bara det som ligger djupare än vittringen runt omkring. Ytan följer stenens välvning, och
              djupet mäts vinkelrätt mot ytan. Långa, smala spår är röda – de kan vara runor, ornament eller sprickor.
              Korta fläckar och gropar är grå. Klicka på det som inte är runor för att ta bort det, och klicka igen för
              att ta tillbaka det.
            </p>
          </div>
          <button type="button" onClick={onClose} className="shrink-0 px-3 py-1.5 text-sm font-semibold rounded-lg border border-slate-300 hover:bg-slate-50">Stäng</button>
        </div>

        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] items-end">
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Skala av mer eller mindre</span>
            <input type="range" min={lo} max={hi} step={0.1} value={offset} onChange={e => setOffset(Number(e.target.value))}
              className="w-full accent-[#b7410e]" aria-valuetext={`${fmt(offset)} mm`} />
            <span className="text-xs text-slate-600">
              <span className="font-semibold">{offset > 0 ? "+" : ""}{fmt(offset)} mm</span>{" "}
              <span>utöver vittringens nivå där den står</span>
              {result && <> (<span>på den här stenen</span> {fmt(result.level_mm.min)}–{fmt(result.level_mm.max)} mm, <span>median</span> {fmt(result.level_mm.median)})</>}
            </span>
          </label>
          <div className="flex flex-wrap gap-2">
            <label className="flex items-center gap-1.5 text-sm text-slate-700">
              <input type="checkbox" checked={showPits} onChange={e => setShowPits(e.target.checked)} className="accent-[#b7410e]" />
              <span>Visa gropar</span>
            </label>
            <button type="button" onClick={undo} disabled={!history.length} className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 disabled:opacity-40 hover:bg-slate-50">Ångra</button>
            <button type="button" onClick={() => { setHistory(h => [...h, points]); resetTo([]); }} disabled={!points.length} className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 disabled:opacity-40 hover:bg-slate-50">Ta tillbaka allt</button>
            <button type="button" onClick={download} disabled={!result} className="px-3 py-1.5 text-sm font-semibold rounded-lg border border-[#b7410e] text-[#b7410e] disabled:opacity-40 hover:bg-[#b7410e] hover:text-white">Ladda ned bilden</button>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
          <span><span className="inline-block w-3 h-3 rounded-sm align-middle mr-1" style={{ background: "#b7410e" }} /><span className="font-semibold">{nSpar}</span> <span>spår</span></span>
          <span><span className="inline-block w-3 h-3 rounded-sm align-middle mr-1" style={{ background: "#94a3b8" }} /><span className="font-semibold">{nGrop}</span> <span>gropar</span></span>
          <span><span className="font-semibold">{nRemoved}</span> <span>bortklickade</span></span>
          {busy && <span className="text-slate-500">Räknar …</span>}
          {hovered && (
            <span className="text-slate-800">
              <span>{hovered.kind === "spar" ? "Spår" : "Grop"}</span>: {fmt(hovered.length_mm, 0)} mm <span>långt</span>,{" "}
              {fmt(hovered.width_mm)} mm <span>brett</span>, {fmt(hovered.depth_mm)} mm <span>djupt</span>
              {hovered.removed ? <> – <span>bortklickad</span></> : null}
            </span>
          )}
        </div>

        {error && <p className="text-sm text-red-700">{error}</p>}
        <div className="relative border border-slate-200 rounded-xl overflow-hidden bg-white">
          {!result && !error && <p className="p-8 text-center text-sm text-slate-500">Räknar fram ytan ur skanningen – första gången tar det några sekunder …</p>}
          <canvas ref={canvasRef} className={`w-full h-auto ${result ? "cursor-pointer" : "hidden"}`}
            onMouseMove={e => setHover(idAt(e))} onMouseLeave={() => setHover(0)}
            onClick={e => { const id = idAt(e); if (id) toggle(id); }} />
        </div>

        <p className="text-xs text-slate-500 max-w-3xl">
          Det du klickar bort sparas i den här webbläsaren för den här skanningen och följer med när du flyttar reglaget.
          Bilden är en hjälp att se, inte en läsning: ange reglagets värde och vad du klickat bort om du använder den.
        </p>
      </div>
    </div>,
    document.body,
  );
}
