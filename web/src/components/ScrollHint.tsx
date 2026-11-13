"use client";

import { useEffect, useState } from "react";

/** A small floating "more below" cue at the foot of the screen (Viktor 2026-11-13: not everyone sees that the start page
 *  goes on). The hero is taller than most screens, so a cue inside it would sit below the fold; this one is fixed to
 *  the viewport, shows while the reader is at the top and fades away as soon as they scroll. The arrow stands still for
 *  readers who have asked for less motion. */
export default function ScrollHint({ target, label }: { target: string; label: string }) {
  const [show, setShow] = useState(true);
  useEffect(() => {
    const update = () => {
      const more = document.documentElement.scrollHeight > window.innerHeight + 200;
      setShow(more && window.scrollY < 120);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);
  return (
    <a href={target} aria-label="Scrolla ner till mer innehåll" aria-hidden={!show} tabIndex={show ? 0 : -1}
       className={`fixed bottom-16 sm:bottom-5 left-1/2 -translate-x-1/2 z-30 transition-opacity duration-500 ${show ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
      <span className="inline-flex items-center gap-2 rounded-full border border-slate-900/10 bg-white/90 px-4 py-2 text-sm font-semibold text-slate-700 shadow-lg shadow-slate-900/10 backdrop-blur hover:text-[#b7410e]">
        {label}
        <svg aria-hidden viewBox="0 0 24 24" className="w-5 h-5 motion-safe:animate-bounce" fill="none" stroke="currentColor"
             strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </span>
    </a>
  );
}
