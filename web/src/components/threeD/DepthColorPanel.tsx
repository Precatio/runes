"use client";
// Djupfärger (POST /api/3d/depth_field, METHODS.md 2d4): the panel under the 3D view. The depth is the same as the
// groove measurement's and Runor och ornamentik's – below a reference surface that follows the stone (closing 20 mm) –
// so the colours mean the same millimetres on every scan. Everything but loading moves uniforms only: real time.
import React, { useEffect, useState } from "react";
import { bandEdges, DEPTH_COLORS, type DepthField, type DepthSettings } from "@/lib/depthField";

const mm = (x: number) => `${x.toLocaleString("sv-SE", { maximumFractionDigits: 2 })} mm`;

export type ProbeChannel = React.RefObject<(mm: number | null) => void>;

/** Points the viewer's channel at this panel's state; the cleanup points it at nothing. */
function connectProbe(ch: ProbeChannel, fn: (mm: number | null) => void) {
  ch.current = fn;
  return () => { ch.current = () => {}; };
}

export default function DepthColorPanel({ field, settings, onChange, busy, error, probeChannel, onToggle, on, onFromView }: {
  field: DepthField | null;
  settings: DepthSettings;
  onChange: (s: DepthSettings) => void;
  busy: boolean;
  error: string | null;
  // the viewer reports the depth under the pointer here, so that only this panel re-renders on every move
  probeChannel: ProbeChannel;
  on: boolean;
  onToggle: () => void;
  onFromView: () => void;
}) {
  const [probe, setProbe] = useState<number | null>(null);
  useEffect(() => {
    return connectProbe(probeChannel, setProbe);
  }, [probeChannel]);
  const set = (patch: Partial<DepthSettings>) => onChange({ ...settings, ...patch });
  const edges = bandEdges(field, settings.scheme);
  const maxPeel = Math.max(3, Math.ceil((field?.percentiles["99"] ?? 3) + 1));
  return (
    <div className="liquid-glass-island rounded-3xl p-4 space-y-3 border border-white/50">
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" onClick={onToggle} disabled={busy}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${on ? "bg-[#b7410e] text-white" : "bg-white border border-[#b7410e] text-[#b7410e] hover:bg-[#b7410e] hover:text-white"} disabled:opacity-50`}>
          {busy ? "Räknar fram djupet …" : on ? "Djupfärger på" : "Djupfärger"}
        </button>
        {on && field && (
          <button type="button" onClick={onFromView} disabled={busy} className="text-xs font-semibold text-[#b7410e] hover:underline disabled:opacity-50">
            Mät djupet från vyn i fönstret
          </button>
        )}
        {on && field && (
          <span className="text-xs text-slate-600 tabular-nums" aria-live="polite">
            Under pekaren: {probe == null ? "–" : mm(probe)}
          </span>
        )}
      </div>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {on && field && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs text-slate-600">
                <span className="font-semibold">Skala av</span>
                <span className="tabular-nums">
                  {settings.peelMode === "yta" ? (settings.peel <= -5 ? "inget" : `grundare än ${mm(settings.peel)}`) : `${Math.round(settings.plane * 100)} % ned`}
                </span>
              </div>
              <div className="mt-1 flex gap-1 text-[11px]">
                {(["yta", "plan"] as const).map(m => (
                  <button key={m} type="button" onClick={() => set({ peelMode: m })}
                    className={`px-2 py-0.5 rounded ${settings.peelMode === m ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}>
                    {m === "yta" ? "Längs stenytan" : "Plant snitt (som en slicer)"}
                  </button>
                ))}
              </div>
              {settings.peelMode === "yta" ? (
                <input type="range" min={-5} max={maxPeel} step={0.05} value={settings.peel} aria-label="Skala av längs stenytan"
                  onChange={e => set({ peel: +e.target.value })} className="w-full accent-[#b7410e]" />
              ) : (
                <input type="range" min={0} max={1} step={0.002} value={settings.plane} aria-label="Plant snitt uppifrån"
                  onChange={e => set({ plane: +e.target.value })} className="w-full accent-[#b7410e]" />
              )}
              <p className="text-[11px] text-slate-500">
                {settings.peelMode === "yta"
                  ? "Allt som ligger grundare än gränsen under stenytan blir blekt, så att bara de djupare spåren står kvar. Ytan följer stenens form, också på en välvd sten."
                  : "Ett plant snitt rakt in mot den ristade sidan skär bort allt ovanför, lager för lager som i ett program för 3D-utskrift. Insidan syns mörkgrå."}
              </p>
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-600">
                <span className="font-semibold">Färgens styrka</span><span className="tabular-nums">{Math.round(settings.strength * 100)} %</span>
              </div>
              <input type="range" min={0} max={1} step={0.05} value={settings.strength} aria-label="Färgens styrka"
                onChange={e => set({ strength: +e.target.value })} className="w-full accent-[#b7410e]" />
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <div className="text-xs font-semibold text-slate-600">Färgband</div>
              <div className="mt-1 flex gap-1 text-[11px]">
                {(["fast", "sten"] as const).map(s => (
                  <button key={s} type="button" onClick={() => set({ scheme: s })}
                    className={`px-2 py-0.5 rounded ${settings.scheme === s ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}>
                    {s === "fast" ? "Fasta millimeter" : "Efter stenens djup"}
                  </button>
                ))}
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-700">
                {DEPTH_COLORS.map((c, i) => (
                  <span key={c} className="inline-flex items-center gap-1">
                    <span className="inline-block h-3 w-5 rounded-sm border border-black/10" style={{ background: c }} />
                    {i < 3 ? `${mm(edges[i])}–${mm(edges[i + 1])}` : `${mm(edges[3])} och djupare`}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-600">Djupkurvor</div>
              <div className="mt-1 flex gap-1 text-[11px]">
                {[0, 0.25, 0.5, 1].map(c => (
                  <button key={c} type="button" onClick={() => set({ contour: c })}
                    className={`px-2 py-0.5 rounded ${settings.contour === c ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}>
                    {c === 0 ? "Av" : `var ${mm(c)}`}
                  </button>
                ))}
              </div>
            </div>
            <p className="text-[11px] text-slate-500">
              Djupet under en referensyta som följer stenens form, samma som huggspårsmätningen. Stenens gemensamma nivå (där
              ungefär 30 % av ytan ligger djupare): {mm(field.level_mm)}. Rutnät {mm(field.res_mm)}. De yttersta 10 mm av
              skanningen får ingen färg, eftersom referensytan är osäker där.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
