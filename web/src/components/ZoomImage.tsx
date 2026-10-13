"use client";
/* eslint-disable @next/next/no-img-element -- Commons photos and R figures of varying size, credited beside them */

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageContext";

// A picture in an article that opens large on a click: over the page, as large as the screen allows, closed with a
// click or Escape, with a link to the file itself
export default function ZoomImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const [open, setOpen] = useState(false);
  const en = useLanguage().lang === "en";
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = overflow; };
  }, [open]);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="group relative block w-full cursor-zoom-in" aria-label={`${en ? "Show larger" : "Visa större"}: ${alt}`}>
        <img src={src} alt={alt} loading="lazy" className={className} />
        <span className="pointer-events-none absolute right-3 top-3 rounded-full bg-slate-900/70 px-2.5 py-1 text-xs font-bold text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
          {en ? "Enlarge" : "Förstora"} ⤢
        </span>
      </button>
      {open && (
        <div role="dialog" aria-modal="true" aria-label={alt} onClick={() => setOpen(false)}
          className="fixed inset-0 z-[100] flex cursor-zoom-out flex-col items-center justify-center gap-3 bg-slate-950/90 p-4">
          <img src={src} alt={alt} className="max-h-[88vh] max-w-[96vw] rounded-lg bg-white object-contain" />
          <div className="flex gap-4 text-sm text-slate-200">
            <a href={src} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="underline hover:text-white">{en ? "Open the file" : "Öppna filen"}</a>
            <button type="button" onClick={() => setOpen(false)} className="underline hover:text-white">{en ? "Close (Esc)" : "Stäng (Esc)"}</button>
          </div>
        </div>
      )}
    </>
  );
}
