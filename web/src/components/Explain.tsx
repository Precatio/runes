"use client";

// Shared building blocks for pages with much text and data: explanations on hover, collapsible details, labels for
// how certain a result is and whether it is statistically significant, and figures that can be enlarged.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

// A term with an explanation on hover, focus or tap. The box is placed on the page itself (portal), so that tables
// with their own scrolling do not cut it off.
export function Tip({ text, children }: { text?: string; children: ReactNode }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [pos, setPos] = useState<{ x: number; y: number; above: boolean } | null>(null);
  if (!text) return <>{children}</>;
  const show = () => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const above = r.bottom + 170 > window.innerHeight;
    setPos({ x: Math.max(8, Math.min(r.left, window.innerWidth - 296)), y: above ? r.top - 6 : r.bottom + 6, above });
  };
  return (
    <span ref={ref} tabIndex={0} role="button" aria-label={text}
      onMouseEnter={show} onMouseLeave={() => setPos(null)} onFocus={show} onBlur={() => setPos(null)}
      onClick={e => { e.stopPropagation(); if (pos) setPos(null); else show(); }}
      className="cursor-help underline decoration-dotted decoration-slate-400 underline-offset-2 outline-none focus-visible:ring-2 focus-visible:ring-[#b7410e]/40 rounded">
      {children}
      {pos && createPortal(
        <span role="tooltip" style={{ left: pos.x, top: pos.y, transform: pos.above ? "translateY(-100%)" : undefined }}
          className="fixed z-[100] w-72 rounded-xl bg-slate-900 px-3 py-2 text-[12px] font-normal normal-case tracking-normal leading-snug text-white shadow-xl pointer-events-none">
          {text}
        </span>, document.body)}
    </span>
  );
}

export function Lightbox({ src, alt, help, onClose }: { src: string; alt: string; help?: string; onClose: () => void }) {
  const [full, setFull] = useState(false);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return createPortal(
    <div role="dialog" aria-modal="true" aria-label={alt} onClick={onClose}
      className="fixed inset-0 z-[90] bg-slate-900/80 backdrop-blur-sm flex flex-col items-center p-3 md:p-8">
      <div className="w-full max-w-6xl flex flex-wrap items-center justify-between gap-2 text-white mb-3" onClick={e => e.stopPropagation()}>
        <div className="font-bold">{alt}</div>
        <div className="flex gap-2 text-xs font-bold">
          <button type="button" onClick={() => setFull(f => !f)} className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25">
            {full ? "Anpassa till fönstret" : "Full storlek"}
          </button>
          <a href={src} target="_blank" rel="noreferrer" className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25">Öppna i ny flik</a>
          <button type="button" onClick={onClose} className="px-3 py-1.5 rounded-lg bg-white text-slate-900">Stäng</button>
        </div>
      </div>
      <div className="w-full max-w-6xl flex-1 min-h-0 overflow-auto rounded-2xl bg-white p-2" onClick={e => e.stopPropagation()}>
        {/* eslint-disable-next-line @next/next/no-img-element -- figures are rendered by R on the backend */}
        <img src={src} alt={alt} onClick={() => setFull(f => !f)}
          className={full ? "max-w-none cursor-zoom-out" : "w-full h-auto cursor-zoom-in"} />
      </div>
      {help && <p className="w-full max-w-6xl mt-3 text-sm text-white/90 leading-relaxed" onClick={e => e.stopPropagation()}>{help}</p>}
    </div>, document.body);
}

// R writes a one-element vector as a plain value
export const asList = (v: string[] | string | null | undefined): string[] => v == null ? [] : Array.isArray(v) ? v : [v];

// A collapsible block for the detailed numbers, so that the page starts with the answer
export function Details({ title, children, open }: { title: string; children: ReactNode; open?: boolean }) {
  return (
    <details open={open} className="group/det rounded-2xl border border-slate-200 bg-white/70">
      <summary className="cursor-pointer select-none list-none px-4 py-3 font-semibold text-slate-800 flex items-center justify-between gap-3">
        <span>{title}</span>
        <span className="text-xs font-bold text-[#b7410e] group-open/det:hidden">Visa</span>
        <span className="text-xs font-bold text-[#b7410e] hidden group-open/det:inline">Dölj</span>
      </summary>
      <div className="px-4 pb-4 space-y-3">{children}</div>
    </details>
  );
}

// **bold** in the explanations from the server
export function Md({ text }: { text: string }) {
  return <>{text.split("**").map((part, i) => i % 2 ? <strong key={i} className="text-slate-900">{part}</strong> : <span key={i}>{part}</span>)}</>;
}

export type Level = "säkert" | "troligt" | "osäkert";
export const LEVEL_STYLE: Record<Level, string> = {
  "säkert": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "troligt": "bg-amber-50 text-amber-900 border-amber-200",
  "osäkert": "bg-slate-100 text-slate-700 border-slate-300",
};
export const LEVEL_HELP: Record<Level, string> = {
  "säkert": "Resultatet är prövat (t.ex. med korsvalidering eller slumptest) och stämmer med vad forskningen redan utgår från.",
  "troligt": "Resultatet håller statistiskt, men det finns viktiga reservationer – läs vad resultatet inte säger.",
  "osäkert": "Ett mönster att pröva: strukturen är svag, eller resultatet är hypoteser som behöver granskas av en runolog.",
};

export function Confidence({ level, text }: { level: Level; text: string }) {
  return (
    <span className={`inline-flex shrink-0 items-center rounded-full border px-3 py-1 text-xs font-bold ${LEVEL_STYLE[level]}`}>
      <Tip text={LEVEL_HELP[level]}>{text}</Tip>
    </span>
  );
}

export interface Significance {
  significant: boolean | null; label?: string; test?: string; kind?: string; value?: number;
}

// Whether a result is statistically significant – the same mark everywhere
export function SigBadge({ sig, compact }: { sig?: Significance | null; compact?: boolean }) {
  if (!sig) return null;
  if (sig.significant) {
    return (
      <span className="inline-flex w-fit self-start shrink-0 items-center rounded-full bg-emerald-700 px-2.5 py-0.5 text-[11px] font-bold text-white">
        <Tip text={`Statistiskt säkerställt: ${sig.label}${sig.test ? ` (${sig.test})` : ""}. Under 0,05 betyder att resultatet sannolikt inte är slump, även när man räknar med att många saker prövats.`}>
          ✓ Säkerställt{compact ? "" : ` · ${sig.label}`}
        </Tip>
      </span>
    );
  }
  if (sig.significant === false) {
    return (
      <span className="inline-flex w-fit self-start shrink-0 items-center rounded-full border border-slate-300 bg-white px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
        <Tip text={`Inte statistiskt säkerställt (${sig.label}${sig.test ? `, ${sig.test}` : ""}). Resultatet kan vara slump.`}>
          Inte säkerställt{compact ? "" : ` · ${sig.label}`}
        </Tip>
      </span>
    );
  }
  return (
    <span className="inline-flex w-fit self-start shrink-0 items-center rounded-full border border-dashed border-slate-300 px-2.5 py-0.5 text-[11px] text-slate-500">
      <Tip text={`Inget signifikanstest${sig.test ? `: ${sig.test}` : ""}.`}>Inget signifikanstest</Tip>
    </span>
  );
}

// A figure: click to enlarge; "Så läser du figuren" explains it on hover
export function Figure({ src, alt, help, narrow }: { src?: string; alt: string; help?: string; narrow?: boolean }) {
  const [open, setOpen] = useState(false);
  if (!src) return null;
  const url = src;
  return (
    <figure className={`group/fig rounded-2xl bg-white border border-slate-200 p-2 ${narrow ? "max-w-3xl w-full mx-auto" : ""}`}>
      <button type="button" onClick={() => setOpen(true)} className="relative block w-full cursor-zoom-in" aria-label={`Förstora: ${alt}`}>
        {/* eslint-disable-next-line @next/next/no-img-element -- figures are rendered by R on the backend */}
        <img src={url} alt={alt} className="w-full h-auto rounded-xl" loading="lazy" />
        <span className="absolute top-2 right-2 rounded-lg bg-slate-900/75 text-white text-[11px] font-bold px-2 py-1 opacity-0 group-hover/fig:opacity-100 transition-opacity">
          Förstora
        </span>
      </button>
      {help && (
        <figcaption className="px-2 pt-2 pb-1 text-[11px] text-slate-600">
          <Tip text={help}><span className="font-semibold">Så läser du figuren</span></Tip>
          <span className="text-slate-400"> · klicka på figuren för att förstora</span>
        </figcaption>
      )}
      {open && <Lightbox src={url} alt={alt} help={help} onClose={() => setOpen(false)} />}
    </figure>
  );
}

// The method in short; caveats and how to read the results are in the documentation (METHODS.md 17)
