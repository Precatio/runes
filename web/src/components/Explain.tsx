"use client";

// Shared building blocks for pages with much text and data: explanations on hover, collapsible details, labels for
// how certain a result is and whether it is statistically significant, and figures that can be enlarged.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { GLOSSARY } from "@/lib/glossary";
import { TONE } from "@/lib/tone";

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
  "säkert": TONE.tint,
  "troligt": TONE.outline,
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
  qualified?: string; // significant, but the result is only an indication or a weak effect
}

// Whether a result is statistically significant – the same mark everywhere
export function SigBadge({ sig, compact }: { sig?: Significance | null; compact?: boolean }) {
  if (!sig) return null;
  if (sig.significant && sig.qualified) {
    return (
      <span className={`inline-flex w-fit self-start shrink-0 items-center rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${TONE.caution}`}>
        <Tip text={`Signifikant men osäkert: ${sig.label ?? ""}${sig.test ? ` (${sig.test})` : ""} – ${sig.qualified}.`}>
          Signifikant men osäkert{compact ? "" : ` · ${sig.label}`}
        </Tip>
      </span>
    );
  }
  if (sig.significant) {
    return (
      <span className={`inline-flex w-fit self-start shrink-0 items-center rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${TONE.fill}`}>
        <Tip text={`Statistiskt signifikant: ${sig.label}${sig.test ? ` (${sig.test})` : ""}. Under 0,05 betyder att ett så tydligt resultat vore ovanligt (färre än 5 av 100 fall) om det inte fanns något verkligt samband, även när man räknar med att många saker prövats. Det är inte sannolikheten att resultatet är sant.`}>
          ✓ Signifikant{compact ? "" : ` · ${sig.label}`}
        </Tip>
      </span>
    );
  }
  if (sig.significant === false) {
    return (
      <span className="inline-flex w-fit self-start shrink-0 items-center rounded-full border border-slate-300 bg-white px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
        <Tip text={`Inte statistiskt signifikant (${sig.label}${sig.test ? `, ${sig.test}` : ""}). Resultatet är inte tydligare än vad slumpen ofta ger; det visar inte att sambandet saknas.`}>
          Inte signifikant{compact ? "" : ` · ${sig.label}`}
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

// The method in short; caveats and how to read the results are in the documentation (METHODS.md 1)

// The glossary of all explained terms, searchable
export function Glossary({ onClose }: { onClose: () => void }) {
  const [q, setQ] = useState("");
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const terms = Object.entries(GLOSSARY).sort(([a], [b]) => a.localeCompare(b, "sv"))
    .filter(([k, v]) => !q || (k + " " + v).toLowerCase().includes(q.toLowerCase()));
  return createPortal(
    <div role="dialog" aria-modal="true" aria-label="Ordlista" onClick={onClose}
      className="fixed inset-0 z-[90] bg-slate-900/60 backdrop-blur-sm flex justify-center p-3 md:p-8">
      <div onClick={e => e.stopPropagation()} className="w-full max-w-2xl bg-white rounded-3xl shadow-2xl flex flex-col max-h-full">
        <div className="p-5 border-b border-slate-100 flex items-center gap-3">
          <h3 className="text-lg font-bold text-slate-900">Ordlista</h3>
          <input autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Sök ett ord …"
            className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-[#b7410e]/50" />
          <button type="button" onClick={onClose} className="px-3 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold">Stäng</button>
        </div>
        <dl className="overflow-y-auto p-5 space-y-3">
          {terms.map(([k, v]) => (
            <div key={k}><dt className="font-semibold text-slate-900">{k}</dt><dd className="text-sm text-slate-600">{v}</dd></div>
          ))}
          {terms.length === 0 && <p className="text-sm text-slate-500">Inga träffar.</p>}
        </dl>
      </div>
    </div>, document.body);
}


// The top of a page with much data: what the page is for, in plain words, how to read it, and the glossary
export function PageIntro({ title, lead, howTo }: { title: string; lead: ReactNode; howTo?: ReactNode[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="space-y-3">
      <h2 className="text-3xl font-bold tracking-tight text-slate-900">{title}</h2>
      <div className="text-slate-700 text-[16px] leading-relaxed max-w-3xl">{lead}</div>
      <div className="flex flex-wrap items-center gap-3">
        {howTo && howTo.length > 0 && (
          <details className="rounded-2xl border border-slate-200 bg-white/70 text-sm max-w-3xl">
            <summary className="cursor-pointer list-none px-4 py-2 font-semibold text-slate-800">Så läser du sidan</summary>
            <ul className="px-6 pb-4 space-y-1.5 list-disc text-slate-700">{howTo.map((h, i) => <li key={i}>{h}</li>)}</ul>
          </details>
        )}
        <button type="button" onClick={() => setOpen(true)}
          className="px-4 py-2 rounded-2xl border border-slate-200 bg-white/70 text-sm font-semibold text-slate-800 hover:border-[#b7410e]/40">
          Ordlista
        </button>
        {open && <Glossary onClose={() => setOpen(false)} />}
      </div>
    </div>
  );
}

export interface QuestionCard { key: string; topic: string; question: string; note?: string }

// The sections of a page as questions instead of method names
export function QuestionCards({ items, active, onSelect, label = "Frågor" }: {
  items: QuestionCard[]; active: string; onSelect: (key: string) => void; label?: string;
}) {
  return (
    <nav aria-label={label} className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
      {items.map(card => (
        <button key={card.key} type="button" onClick={() => onSelect(card.key)} aria-pressed={active === card.key}
          className={`text-left rounded-2xl border p-3 transition-colors ${active === card.key
            ? "bg-slate-900 border-slate-900 text-white shadow-lg" : "bg-white/80 border-slate-200 text-slate-800 hover:border-[#b7410e]/40"}`}>
          <div className={`text-[10px] font-bold uppercase tracking-wider ${active === card.key ? "text-[#f0a37f]" : "text-[#b7410e]"}`}>{card.topic}</div>
          <div className="text-sm font-semibold leading-snug mt-0.5">{card.question}</div>
          {card.note && <div className={`text-[10px] mt-1.5 ${active === card.key ? "text-white/70" : "text-slate-500"}`}>{card.note}</div>}
        </button>
      ))}
    </nav>
  );
}

export interface AnswerProps {
  topic?: string; question: string; why?: ReactNode; headline?: { value: string; label: string };
  answer: ReactNode; confidence?: { level: Level; text: string }; interpretation?: ReactNode[]; notSaying?: ReactNode[];
  children?: ReactNode;
}

// The answer first: the question, why it matters, a key number, the answer, a suggested interpretation and its limits
export function Answer({ topic, question, why, headline, answer, confidence, interpretation = [], notSaying = [], children }: AnswerProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          {topic && <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">{topic}</div>}
          <h3 className="text-2xl font-bold tracking-tight text-slate-900">{question}</h3>
          {why && <p className="text-slate-600 mt-1">{why}</p>}
        </div>
        {confidence && <Confidence level={confidence.level} text={confidence.text} />}
      </div>
      <div className={`grid grid-cols-1 ${headline ? "md:grid-cols-[240px_1fr]" : ""} gap-4`}>
        {headline && (
          <div className="rounded-2xl bg-slate-900 text-white p-5 flex flex-col justify-center">
            <div className="text-4xl font-bold tracking-tight">{headline.value}</div>
            <div className="text-sm text-white/80 mt-1 leading-snug">{headline.label}</div>
          </div>
        )}
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Svaret i korthet</div>
          <div className="text-slate-800 leading-relaxed">{answer}</div>
        </div>
      </div>
      {(interpretation.length > 0 || notSaying.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {interpretation.length > 0 && (
            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <h4 className="font-bold text-slate-900 mb-2">Förslag till tolkning</h4>
              <ul className="space-y-2 text-sm text-slate-700 list-disc pl-5">{interpretation.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          {notSaying.length > 0 && (
            <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
              <h4 className="font-bold text-slate-900 mb-2">Det här säger resultatet inte</h4>
              <ul className="space-y-2 text-sm text-slate-600 list-disc pl-5">{notSaying.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

// A small "?" with an explanation, for places where the label itself is a button (e.g. a sortable column)
export function InfoTip({ text }: { text?: string }) {
  if (!text) return null;
  return <Tip text={text}><span className="ml-1 text-slate-400 font-normal normal-case">ⓘ</span></Tip>;
}
