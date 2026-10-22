"use client";
/* eslint-disable @next/next/no-img-element -- Commons photos and R figures of varying size, credited beside them */

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageContext";

// A picture that opens large on a click, in the same window: over the page, as large as the screen allows, closed with
// a click or Escape. frameClassName styles the clickable frame around the small picture (border, rounding); srcSet and
// sizes let the browser pick a smaller copy for the small picture, and zoomSrc is the large one (the original).
// zoomSrcSet offers the large copies (up to the original) for the enlarged view, which the browser chooses from by how
// large the picture is drawn there: at most 96 % of the window's width and 88 % of its height (measured when it opens)
export default function ZoomImage({ src, alt, className, frameClassName = "", width, height, srcSet, sizes, zoomSrc, zoomSrcSet }:
  { src: string; alt: string; className?: string; frameClassName?: string; width?: number; height?: number;
    srcSet?: string; sizes?: string; zoomSrc?: string; zoomSrcSet?: string }) {
  const [open, setOpen] = useState(false);
  // How wide the enlarged picture is drawn, in CSS pixels: the window's share, narrowed by the height for a tall picture,
  // and never wider than the original. sizes also sets the drawn size (a srcset copy is shown at the sizes width), so
  // without the last cap an 800 px original would be stretched to fill a large window and look blurred
  const zoomSizes = () => {
    const w = window.innerWidth * 0.96, h = window.innerHeight * 0.88;
    return `${Math.ceil(width && height ? Math.min(w, (h * width) / height, width) : w)}px`;
  };
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
      <button type="button" onClick={() => setOpen(true)} className={`group relative block w-full cursor-zoom-in ${frameClassName}`} aria-label={`${en ? "Show larger" : "Visa större"}: ${alt}`}>
        <img src={src} srcSet={srcSet} sizes={srcSet ? sizes : undefined} alt={alt} loading="lazy" decoding="async"
          width={width} height={height} className={className} />
        <span className="pointer-events-none absolute right-3 top-3 rounded-full bg-slate-900/70 px-2.5 py-1 text-xs font-bold text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
          {en ? "Enlarge" : "Förstora"} ⤢
        </span>
      </button>
      {open && (
        <div role="dialog" aria-modal="true" aria-label={alt} onClick={() => setOpen(false)}
          className="fixed inset-0 z-[100] flex cursor-zoom-out flex-col items-center justify-center gap-3 bg-slate-950/90 p-4">
          <img src={zoomSrc ?? src} srcSet={zoomSrcSet} sizes={zoomSrcSet ? zoomSizes() : undefined} alt={alt} className="max-h-[88vh] max-w-[96vw] rounded-lg bg-white object-contain" />
          <div className="flex gap-4 text-sm text-slate-200">
            <button type="button" onClick={() => setOpen(false)} className="underline hover:text-white">{en ? "Close (Esc)" : "Stäng (Esc)"}</button>
          </div>
        </div>
      )}
    </>
  );
}
