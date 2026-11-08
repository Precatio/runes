"use client";

// Runor och ornamentik (POST /api/3d/band_image, src/band_image.py, METHODS.md 2d3): today's depth image cut at one
// common level for the whole stone, coloured by the text bands the groove analysis uses – rust inside the bands, grey
// outside (ornament, cracks, pits), the bands' edge black. The bands are Viktor's checked drawing for the open scans,
// otherwise the band model's proposal, so the picture shows what the analysis counts as text.
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import type { MeshSession } from "@/lib/mesh";

interface BandResult {
  image: string; width: number; height: number; resolution_mm: number; offset_mm: number;
  offset_range: [number, number]; level_mm: number; source: "ritade" | "modellen" | null;
  shown_share: number; band_share: number | null; in_bands: number | null;
}
interface View { toward: number[]; up: number[] }

const fmt = (v: number, d = 1) => v.toFixed(d).replace(".", ",");
const pct = (v: number) => `${Math.round(100 * v)} %`;
const errorText = (err: unknown, fallback: string) => (err instanceof Error ? err.message : fallback);

export default function BandImageDialog({ session, filename, view, onClose }: {
  session: MeshSession; filename: string; view: View | null; onClose: () => void;
}) {
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState<BandResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // A new picture when the slider stops moving
  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(async () => {
      setBusy(true);
      setError(null);
      try {
        const fields: Record<string, string | number> = { offset_mm: offset };
        if (view) {
          Object.assign(fields, { normal_x: view.toward[0], normal_y: view.toward[1], normal_z: view.toward[2],
            up_x: view.up[0], up_y: view.up[1], up_z: view.up[2] });
        }
        const data = await session.postJSON<BandResult>("/api/3d/band_image", fields);
        if (!cancelled) setResult(data);
      } catch (e) {
        if (!cancelled) setError(errorText(e, "Bilden kunde inte räknas fram."));
      } finally {
        if (!cancelled) setBusy(false);
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(t); };
  }, [offset, session, view]);

  const download = () => {
    if (!result) return;
    const a = document.createElement("a");
    a.href = result.image;
    a.download = `${filename.replace(/\.[^.]+$/, "")}_runor_ornamentik_${fmt(offset)}mm.png`;
    a.click();
  };

  const [lo, hi] = result?.offset_range ?? [-1, 3];

  // In document.body: the page's main column is its own stacking context, under the sidebar
  return createPortal(
    <div className="fixed inset-0 z-[600] bg-slate-900/50 flex items-center justify-center p-3" role="dialog" aria-modal="true" aria-label="Runor och ornamentik">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-6xl max-h-[94vh] overflow-auto p-5 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Runor och ornamentik</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Bilden visar det som ligger djupare än en gemensam nivå för hela stenen, färgat efter textslingorna:
              rostrött inne i slingorna, grått utanför – ornamentik, sprickor och gropar. Den svarta linjen är
              slingornas kant. Det är samma slingor som huggspårsanalysen använder för att avgöra vad som är runor, så
              bilden visar vad analysen räknar som text.
            </p>
          </div>
          <button type="button" onClick={onClose} className="shrink-0 px-3 py-1.5 text-sm font-semibold rounded-lg border border-slate-300 hover:bg-slate-50">Stäng</button>
        </div>

        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] items-end">
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Visa mer eller mindre</span>
            <input type="range" min={lo} max={hi} step={0.1} value={offset} onChange={e => setOffset(Number(e.target.value))}
              className="w-full accent-[#b7410e]" aria-valuetext={`${fmt(offset)} mm`} />
            <span className="text-xs text-slate-600">
              <span className="font-semibold">{offset > 0 ? "+" : ""}{fmt(offset)} mm</span>{" "}
              <span>utöver stenens gemensamma nivå</span>
              {result && <> ({fmt(result.level_mm)} mm <span>under ytan</span>)</>}
            </span>
          </label>
          <button type="button" onClick={download} disabled={!result} className="px-3 py-1.5 text-sm font-semibold rounded-lg border border-[#b7410e] text-[#b7410e] disabled:opacity-40 hover:bg-[#b7410e] hover:text-white">Ladda ned bilden</button>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
          <span><span className="inline-block w-3 h-3 rounded-sm align-middle mr-1" style={{ background: "#b7410e" }} /><span>i textslingorna</span></span>
          <span><span className="inline-block w-3 h-3 rounded-sm align-middle mr-1" style={{ background: "#9aa6b8" }} /><span>utanför slingorna</span></span>
          <span><span className="inline-block w-3 h-0.5 align-middle mr-1" style={{ background: "#141414" }} /><span>slingornas kant</span></span>
          {result && result.in_bands !== null && result.band_share !== null && (
            <span className="text-slate-800">
              <span className="font-semibold">{pct(result.in_bands)}</span> <span>av det visade ligger i slingorna, som täcker</span>{" "}
              <span className="font-semibold">{pct(result.band_share)}</span> <span>av ytan</span>
            </span>
          )}
          {busy && <span className="text-slate-500">Räknar …</span>}
        </div>

        {result && (
          <p className="text-xs text-slate-600 max-w-3xl">
            {result.source === "ritade" && <span>Slingorna är ritade och granskade för den här skanningen.</span>}
            {result.source === "modellen" && (
              <span>
                Slingorna är slingmodellens förslag. Den träffar inte alltid hela slingan, så se efter om något av texten
                hamnat utanför.
              </span>
            )}
            {result.source === null && (
              <span>Inga textslingor kunde tas fram för den här skanningen; bilden visar bara det som ligger djupast.</span>
            )}
          </p>
        )}

        {error && <p className="text-sm text-red-700">{error}</p>}
        <div className="relative border border-slate-200 rounded-xl overflow-hidden bg-white">
          {!result && !error && <p className="p-8 text-center text-sm text-slate-500">Räknar fram ytan och slingorna ur skanningen – första gången tar det några sekunder …</p>}
          {result && (
            // eslint-disable-next-line @next/next/no-img-element -- a data URI computed by the API
            <img src={result.image} width={result.width} height={result.height} alt="Runor och ornamentik" className="w-full h-auto" />
          )}
        </div>

        <p className="text-xs text-slate-500 max-w-3xl">
          Bilden är en hjälp att se vad analysen räknar som text, inte en läsning. Ange reglagets värde om du använder den.
        </p>
      </div>
    </div>,
    document.body,
  );
}
