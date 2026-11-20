"use client";
// Djupfärger (POST /api/3d/depth_field, METHODS.md 2d4): a column beside the stone in the 3D view, always in view once
// a scan is loaded (the toolbar's "Djupfärger" button switches the colours too). The depth is the same as the groove
// measurement's and Runor och ornamentik's – below a reference surface that follows the stone (closing 20 mm) – so the
// colours mean the same millimetres on every scan. Everything but loading moves uniforms only: real time.
import React, { useEffect, useState } from "react";
import { bandEdges, DEPTH_COLORS, type DepthField, type DepthSettings } from "@/lib/depthField";

const mm = (x: number) => `${x.toLocaleString("sv-SE", { maximumFractionDigits: 2 })} mm`;

export type ProbeChannel = React.RefObject<(mm: number | null) => void>;

/** Points the viewer's channel at this panel's state; the cleanup points it at nothing. */
function connectProbe(ch: ProbeChannel, fn: (mm: number | null) => void) {
  ch.current = fn;
  return () => { ch.current = () => {}; };
}

const chip = (active: boolean) =>
  `px-2 py-0.5 rounded ${active ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`;

export default function DepthColorPanel({ field, settings, onChange, busy, error, probeChannel, on, onToggle, onFromView,
  onSnapshot, onExportMap }: {
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
  onSnapshot: () => void;   // the 3D view as a high-resolution picture
  onExportMap: () => void;  // the depth map straight from above at full resolution
}) {
  const [probe, setProbe] = useState<number | null>(null);
  useEffect(() => connectProbe(probeChannel, setProbe), [probeChannel]);
  const set = (patch: Partial<DepthSettings>) => onChange({ ...settings, ...patch });
  const edges = bandEdges(field, settings.scheme);
  const maxPeel = Math.max(3, Math.ceil((field?.percentiles["99"] ?? 3) + 1));
  const bandLabel = (i: number) => (i < 3 ? `${mm(edges[i])}–${mm(edges[i + 1])}` : `${mm(edges[3])} och djupare`);
  const live = on && field;
  return (
    <div className="liquid-glass-island h-full p-4 space-y-4 border border-white/50 rounded-[24px] text-slate-800">
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Djupfärger</span>
          <button type="button" role="switch" aria-checked={on} onClick={onToggle} disabled={busy}
            className={`relative h-6 w-11 rounded-full transition-colors disabled:opacity-50 ${on ? "bg-[#b7410e]" : "bg-slate-300"}`}
            title={on ? "Stäng av djupfärgerna" : "Slå på djupfärgerna"}>
            <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${on ? "left-[22px]" : "left-0.5"}`} />
          </button>
        </div>
        {busy && <p className="text-xs text-slate-500">Räknar fram djupet …</p>}
        {error && <p className="text-xs text-red-700">{error}</p>}
        {!on && !busy && (
          <p className="text-[11px] text-slate-500">
            Färga stenen efter hur djupt varje punkt ligger under stenytan, visa ett djup i taget, skala av lager och spara
            bilder i hög upplösning.
          </p>
        )}
        {live && (
          <p className="text-xs text-slate-600 tabular-nums" aria-live="polite">Under pekaren: {probe == null ? "–" : mm(probe)}</p>
        )}
      </div>

      {live && (
        <>
          <div>
            <div className="text-xs font-semibold text-slate-600">Djup</div>
            <div className="text-[11px] text-slate-500 mb-1.5">Klicka på ett djup för att se bara det.</div>
            <div className="flex flex-col gap-1 text-[11px]">
              {DEPTH_COLORS.map((c, i) => (
                <button key={c} type="button" aria-pressed={settings.only === i}
                  onClick={() => set({ only: settings.only === i ? null : i })}
                  className={`flex items-center gap-2 rounded-lg border px-2 py-1 text-left ${settings.only === i ? "border-slate-900 bg-slate-900 text-white" : settings.only != null ? "border-slate-200 bg-white text-slate-400" : "border-slate-200 bg-white text-slate-700 hover:border-slate-400"}`}>
                  <span className="inline-block h-3 w-5 flex-shrink-0 rounded-sm border border-black/10" style={{ background: c }} />
                  {bandLabel(i)}
                </button>
              ))}
              {settings.only != null && (
                <button type="button" onClick={() => set({ only: null })} className="self-start px-1 font-semibold text-[#b7410e] hover:underline">
                  Visa alla djup
                </button>
              )}
            </div>
            <div className="mt-1.5 flex gap-1 text-[11px]">
              <button type="button" onClick={() => set({ scheme: "fast" })} className={chip(settings.scheme === "fast")}>Fasta millimeter</button>
              <button type="button" onClick={() => set({ scheme: "sten" })} className={chip(settings.scheme === "sten")}>Efter stenens djup</button>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-600">
              <span className="font-semibold">Skala av</span>
              <span className="tabular-nums">
                {settings.peelMode === "yta" ? (settings.peel <= -5 ? "inget" : `grundare än ${mm(settings.peel)}`) : `${Math.round(settings.plane * 100)} % ned`}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-1 text-[11px]">
              <button type="button" onClick={() => set({ peelMode: "yta" })} className={chip(settings.peelMode === "yta")}>Längs stenytan</button>
              <button type="button" onClick={() => set({ peelMode: "plan" })} className={chip(settings.peelMode === "plan")}>Plant snitt (som en slicer)</button>
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
                ? "Det som ligger grundare än gränsen under stenytan blir blekt. Ytan följer stenens form, också på en välvd sten."
                : "Ett plan rakt in mot den ristade sidan skär bort allt ovanför, lager för lager som i ett program för 3D-utskrift."}
            </p>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-600">
              <span className="font-semibold">Färgens styrka</span><span className="tabular-nums">{Math.round(settings.strength * 100)} %</span>
            </div>
            <input type="range" min={0} max={1} step={0.05} value={settings.strength} aria-label="Färgens styrka"
              onChange={e => set({ strength: +e.target.value })} className="w-full accent-[#b7410e]" />
          </div>

          <div>
            <div className="text-xs font-semibold text-slate-600">Djupkurvor</div>
            <div className="mt-1 flex flex-wrap gap-1 text-[11px]">
              {[0, 0.25, 0.5, 1].map(c => (
                <button key={c} type="button" onClick={() => set({ contour: c })} className={chip(settings.contour === c)}>
                  {c === 0 ? "Av" : `var ${mm(c)}`}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-600">Spara</div>
            <button type="button" onClick={onSnapshot}
              className="w-full py-2 bg-white border border-[#b7410e] text-[#b7410e] hover:bg-[#b7410e] hover:text-white font-semibold text-xs rounded-xl transition-all">
              Bild av 3D-vyn (hög upplösning)
            </button>
            <button type="button" onClick={onExportMap}
              className="w-full py-2 bg-white border border-[#b7410e] text-[#b7410e] hover:bg-[#b7410e] hover:text-white font-semibold text-xs rounded-xl transition-all">
              Djupkartan rakt uppifrån
            </button>
            <button type="button" onClick={onFromView} disabled={busy} className="text-[11px] font-semibold text-slate-600 hover:underline disabled:opacity-50">
              Mät djupet från vyn i fönstret
            </button>
          </div>

          <p className="text-[11px] text-slate-500">
            Djupet är detsamma som huggspårsmätningens, under en referensyta som följer stenen. Stenens gemensamma nivå (där
            ungefär 30 % av ytan ligger djupare): {mm(field.level_mm)}; rutnät {mm(field.res_mm)}. De yttersta 10 mm av
            skanningen får ingen färg. Färgen visar djup, inte vad som är runor: vittrade runor kan vara lika grunda som gropar.
          </p>
        </>
      )}
    </div>
  );
}
