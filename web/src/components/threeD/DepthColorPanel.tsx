"use client";
// Djupfärger (POST /api/3d/depth_field, METHODS.md 2d4): the panel inside the 3D view, opened from the toolbar's
// "Djupfärger" button. The depth is the same as the groove measurement's and Runor och ornamentik's – below a reference
// surface that follows the stone (closing 20 mm) – so the colours mean the same millimetres on every scan. Everything
// but loading moves uniforms only: real time.
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

export default function DepthColorPanel({ field, settings, onChange, busy, error, probeChannel, onClose, onFromView,
  onSnapshot, onExportMap }: {
  field: DepthField | null;
  settings: DepthSettings;
  onChange: (s: DepthSettings) => void;
  busy: boolean;
  error: string | null;
  // the viewer reports the depth under the pointer here, so that only this panel re-renders on every move
  probeChannel: ProbeChannel;
  onClose: () => void;
  onFromView: () => void;
  onSnapshot: () => void;   // the 3D view as a high-resolution picture
  onExportMap: () => void;  // the depth map straight from above at full resolution
}) {
  const [probe, setProbe] = useState<number | null>(null);
  const [open, setOpen] = useState(false);  // folded at first: the colour bands only, so the stone stays in view
  useEffect(() => connectProbe(probeChannel, setProbe), [probeChannel]);
  const set = (patch: Partial<DepthSettings>) => onChange({ ...settings, ...patch });
  const edges = bandEdges(field, settings.scheme);
  const maxPeel = Math.max(3, Math.ceil((field?.percentiles["99"] ?? 3) + 1));
  const bandLabel = (i: number) => (i < 3 ? `${mm(edges[i])}–${mm(edges[i + 1])}` : `${mm(edges[3])} och djupare`);
  return (
    <div className="bg-white/95 backdrop-blur-md p-3 space-y-2.5 border border-white/60 rounded-2xl text-slate-800">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="text-xs font-bold uppercase tracking-wider text-[#b7410e]">Djupfärger</span>
        {busy && <span className="text-xs text-slate-500">Räknar fram djupet …</span>}
        {field && (
          <span className="text-xs text-slate-600 tabular-nums" aria-live="polite">Under pekaren: {probe == null ? "–" : mm(probe)}</span>
        )}
        <span className="ml-auto flex gap-2">
          <button type="button" onClick={() => setOpen(o => !o)} className="text-xs font-semibold text-slate-600 hover:text-[#b7410e]" aria-expanded={open}>
            {open ? "Fäll ihop" : "Visa reglagen"}
          </button>
          <button type="button" onClick={onClose} className="text-xs font-semibold text-slate-600 hover:text-[#b7410e]" title="Stäng av djupfärgerna">
            Stäng
          </button>
        </span>
      </div>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {field && (
        <div>
          <div className="text-[11px] text-slate-500 mb-1">
            Klicka på ett djup för att se bara det{settings.only != null && <> – nu visas bara <strong>{bandLabel(settings.only)}</strong></>}:
          </div>
          <div className="flex flex-wrap gap-1.5 text-[11px]">
            {DEPTH_COLORS.map((c, i) => (
              <button key={c} type="button" aria-pressed={settings.only === i}
                onClick={() => set({ only: settings.only === i ? null : i })}
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-1 ${settings.only === i ? "border-slate-900 bg-slate-900 text-white" : settings.only != null ? "border-slate-200 bg-white text-slate-400" : "border-slate-200 bg-white text-slate-700 hover:border-slate-400"}`}>
                <span className="inline-block h-3 w-4 rounded-sm border border-black/10" style={{ background: c }} />
                {bandLabel(i)}
              </button>
            ))}
            {settings.only != null && (
              <button type="button" onClick={() => set({ only: null })} className="rounded-lg px-2 py-1 font-semibold text-[#b7410e] hover:underline">
                Visa alla djup
              </button>
            )}
          </div>
        </div>
      )}
      {field && open && (
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2.5">
            <div>
              <div className="flex justify-between text-xs text-slate-600">
                <span className="font-semibold">Skala av</span>
                <span className="tabular-nums">
                  {settings.peelMode === "yta" ? (settings.peel <= -5 ? "inget" : `grundare än ${mm(settings.peel)}`) : `${Math.round(settings.plane * 100)} % ned`}
                </span>
              </div>
              <div className="mt-1 flex gap-1 text-[11px]">
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
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-600">
                <span className="font-semibold">Färgens styrka</span><span className="tabular-nums">{Math.round(settings.strength * 100)} %</span>
              </div>
              <input type="range" min={0} max={1} step={0.05} value={settings.strength} aria-label="Färgens styrka"
                onChange={e => set({ strength: +e.target.value })} className="w-full accent-[#b7410e]" />
            </div>
          </div>
          <div className="space-y-2.5">
            <div>
              <div className="text-xs font-semibold text-slate-600">Färgband</div>
              <div className="mt-1 flex gap-1 text-[11px]">
                <button type="button" onClick={() => set({ scheme: "fast" })} className={chip(settings.scheme === "fast")}>Fasta millimeter</button>
                <button type="button" onClick={() => set({ scheme: "sten" })} className={chip(settings.scheme === "sten")}>Efter stenens djup</button>
              </div>
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
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] font-semibold">
              <button type="button" onClick={onSnapshot} className="text-[#b7410e] hover:underline">Spara bild av 3D-vyn</button>
              <button type="button" onClick={onExportMap} className="text-[#b7410e] hover:underline">Spara djupkartan rakt uppifrån</button>
              <button type="button" onClick={onFromView} disabled={busy} className="text-slate-600 hover:underline disabled:opacity-50">Mät djupet från vyn i fönstret</button>
            </div>
          </div>
          <p className="sm:col-span-2 text-[11px] text-slate-500">
            {settings.peelMode === "yta"
              ? "Skala av: allt som ligger grundare än gränsen under stenytan blir blekt, så att bara de djupare spåren står kvar; ytan följer stenens form, också på en välvd sten."
              : "Plant snitt: ett plan rakt in mot den ristade sidan skär bort allt ovanför, lager för lager som i ett program för 3D-utskrift; insidan syns mörkgrå."}
            {" "}Djupet är detsamma som huggspårsmätningens, under en referensyta som följer stenen. Stenens gemensamma nivå
            (där ungefär 30 % av ytan ligger djupare): {mm(field.level_mm)}; rutnät {mm(field.res_mm)}. De yttersta 10 mm
            av skanningen får ingen färg. Färgen visar djup, inte vad som är runor: vittrade runor kan vara lika grunda som gropar.
          </p>
        </div>
      )}
    </div>
  );
}
