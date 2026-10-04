"use client";

import { useEffect, useRef, useState } from "react";
import { parsePTM, relight, type PTM } from "@/lib/ptm";

const MAX_BYTES = 400 * 1024 * 1024;

export default function RTIPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<ImageData | null>(null);
  const [ptm, setPtm] = useState<PTM | null>(null);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [light, setLight] = useState({ lu: -0.6, lv: 0.4 });
  const [gain, setGain] = useState(1);
  const [grayscale, setGrayscale] = useState(false);
  const [dragging, setDragging] = useState(false);

  const load = async (file: File | undefined) => {
    if (!file) return;
    setError(null);
    if (file.size > MAX_BYTES) {
      setError("Filen är för stor för webbläsaren (max 400 MB).");
      return;
    }
    try {
      const parsed = parsePTM(await file.arrayBuffer());
      imageRef.current = new ImageData(parsed.width, parsed.height);
      setPtm(parsed);
      setFileName(file.name);
    } catch (e) {
      setPtm(null);
      setError(e instanceof Error ? e.message : "Kunde inte läsa filen.");
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!ptm || !canvas || !img) return;
    const frame = requestAnimationFrame(() => {
      relight(ptm, img, { lu: light.lu, lv: light.lv, diffuseGain: gain, grayscale });
      canvas.width = ptm.width;
      canvas.height = ptm.height;
      canvas.getContext("2d")?.putImageData(img, 0, 0);
    });
    return () => cancelAnimationFrame(frame);
  }, [ptm, light, gain, grayscale]);

  const setFromPointer = (e: React.PointerEvent<HTMLElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    let lu = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    let lv = 1 - ((e.clientY - rect.top) / rect.height) * 2;
    const len = Math.hypot(lu, lv);
    if (len > 0.999) { lu /= len / 0.999; lv /= len / 0.999; }
    setLight({ lu, lv });
  };

  const azimuth = ((Math.atan2(light.lv, light.lu) * 180) / Math.PI + 360) % 360;
  const elevation = (Math.acos(Math.min(1, Math.hypot(light.lu, light.lv))) * 180) / Math.PI;

  const savePNG = () => {
    const url = canvasRef.current?.toDataURL("image/png");
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `${fileName.replace(/\.[^.]+$/, "")}_ljus${azimuth.toFixed(0)}-${elevation.toFixed(0)}.png`;
    a.click();
  };

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">RTI-visare</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Öppna en PTM-fil (Polynomial Texture Map) och flytta ljuset fritt för att läsa svaga ristningar i strykljus.
          Filen bearbetas lokalt i webbläsaren och laddas inte upp.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
        <div className="liquid-glass-island rounded-[32px] p-6 space-y-5 h-fit">
          <div>
            <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">PTM-fil</label>
            <input type="file" accept=".ptm" onChange={e => load(e.target.files?.[0])}
              className="w-full text-xs file:mr-3 file:py-2 file:px-4 file:rounded-full file:border-0 file:font-semibold file:bg-slate-900 file:text-white" />
            <p className="text-[11px] text-slate-500 mt-2">
              Stöder PTM_FORMAT_LRGB och PTM_FORMAT_RGB. HSH-filer (.rti) kan exporteras som PTM i RTIBuilder.
            </p>
          </div>

          <div>
            <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Ljusriktning</label>
            <div
              className="relative w-full aspect-square rounded-full bg-gradient-to-br from-slate-100 to-slate-300 border border-slate-300 cursor-crosshair touch-none"
              onPointerDown={e => { setDragging(true); e.currentTarget.setPointerCapture(e.pointerId); setFromPointer(e); }}
              onPointerMove={e => dragging && setFromPointer(e)}
              onPointerUp={() => setDragging(false)}
            >
              <div className="absolute w-4 h-4 -ml-2 -mt-2 rounded-full bg-amber-400 border-2 border-slate-900 shadow"
                style={{ left: `${(light.lu + 1) * 50}%`, top: `${(1 - light.lv) * 50}%` }} />
            </div>
            <div className="flex justify-between text-xs text-slate-600 font-semibold mt-2">
              <span>Riktning {azimuth.toFixed(0)}°</span><span>Höjd {elevation.toFixed(0)}°</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Dra mot kanten för lägre ljus (strykljus).</p>
          </div>

          <div>
            <label className="flex justify-between text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
              <span>Diffuse gain</span><span>{gain.toFixed(1)}</span>
            </label>
            <input type="range" min="1" max="10" step="0.5" value={gain} onChange={e => setGain(+e.target.value)} className="w-full accent-slate-900" />
            <p className="text-[11px] text-slate-500 mt-1">Förstärker ytrelief (Malzbender m.fl. 2001). 1 = av.</p>
          </div>

          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <input type="checkbox" checked={grayscale} onChange={e => setGrayscale(e.target.checked)} /> Gråskala
          </label>

          <button onClick={savePNG} disabled={!ptm}
            className="w-full py-2.5 bg-slate-900 text-white text-sm font-bold rounded-xl disabled:opacity-40">
            Spara vy som PNG
          </button>
        </div>

        <div className="liquid-glass-island rounded-[32px] p-4 min-h-[500px] flex items-center justify-center overflow-auto">
          {error && <p className="text-red-700 font-semibold">{error}</p>}
          {!ptm && !error && <p className="text-slate-500">Ingen fil öppnad.</p>}
          <canvas ref={canvasRef} className={`max-w-full h-auto rounded-xl ${ptm ? "" : "hidden"}`} />
        </div>
      </div>
      {ptm && <p className="text-[11px] text-slate-500">{fileName}: {ptm.width}×{ptm.height} px, {ptm.format}.</p>}
    </div>
  );
}
