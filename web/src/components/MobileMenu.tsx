"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

// The public website's menu on phones and small tablets (below lg, where SiteHeader's row of links is hidden): a button
// with three bars that opens a panel under the header. The articles and the research reports first and large, then the
// news and the contact page, then the start page's sections, and last the download. Closed by a link, Escape, a tap
// outside the panel, or when the window grows past lg; the page behind it does not scroll while it is open, and the
// focus goes into the panel and back to the button.
export interface MenuLink { href: string; label: string; internal?: boolean }

export default function MobileMenu({ primary, sections, download, lang }: { primary: MenuLink[]; sections: MenuLink[]; download: MenuLink; lang: "sv" | "en" }) {
  const en = lang === "en";
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const close = useCallback((refocus = true) => {
    setOpen(false);
    if (refocus) button.current?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    panel.current?.querySelector<HTMLElement>("a")?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
    const wide = window.matchMedia("(min-width: 1024px)");
    const onWide = () => { if (wide.matches) close(false); };
    window.addEventListener("keydown", onKey);
    wide.addEventListener("change", onWide);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
      wide.removeEventListener("change", onWide);
    };
  }, [open, close]);

  const here = (href: string) => {
    const path = href.replace(/\/$/, "") || "/";
    const cur = (pathname || "/").replace(/\/$/, "") || "/";
    return path !== "/" && !href.includes("#") && (cur === path || cur.startsWith(`${path}/`));
  };
  const big = "flex items-center justify-between min-h-12 py-3 text-[17px] font-semibold text-slate-900";
  const small = "flex items-center min-h-11 py-2.5 text-[15px] text-slate-700";

  return (
    <div className="lg:hidden">
      <button ref={button} type="button" onClick={() => setOpen(v => !v)} aria-expanded={open} aria-controls="mobilmeny"
        aria-label={open ? (en ? "Close the menu" : "Stäng menyn") : (en ? "Open the menu" : "Öppna menyn")}
        className="-mr-2 inline-flex h-11 w-11 items-center justify-center rounded-full text-slate-800 hover:bg-slate-900/5">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
        </svg>
      </button>
      {/* In a portal on <body>: the header's backdrop blur makes it the containing block of fixed children, which would
          squeeze the panel and its backdrop into the header's own 64 px */}
      {open && createPortal(
        <>
          <div className="fixed inset-x-0 top-16 bottom-0 z-40 bg-slate-900/20" onClick={() => close(false)} aria-hidden="true" />
          <div ref={panel} id="mobilmeny" role="dialog" aria-modal="true" aria-label={en ? "Menu" : "Meny"}
            className="fixed inset-x-0 top-16 z-50 max-h-[calc(100dvh-4rem)] overflow-y-auto border-b border-slate-900/10 bg-[#f6f4f1] px-6 pb-8 pt-2 shadow-lg">
            <nav aria-label={en ? "Main" : "Huvudmeny"}>
              <ul className="divide-y divide-slate-900/10">
                {primary.map(l => (
                  <li key={l.href}>
                    <Link href={l.href} prefetch={false} onClick={() => setOpen(false)} aria-current={here(l.href) ? "page" : undefined}
                      className={`${big} ${here(l.href) ? "text-[#9a350b]" : ""}`}>
                      {l.label}<span aria-hidden="true" className="text-slate-400">→</span>
                    </Link>
                  </li>
                ))}
              </ul>
              <p className="mt-6 text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">{en ? "More about Vitki" : "Mer om Vitki"}</p>
              <ul className="mt-1 grid grid-cols-2 gap-x-4">
                {sections.map(l => (
                  <li key={l.href}><a href={l.href} onClick={() => setOpen(false)} className={small}>{l.label}</a></li>
                ))}
              </ul>
            </nav>
            <a href={download.href} target="_blank" rel="noopener noreferrer" onClick={() => setOpen(false)}
              className="mt-6 flex min-h-12 items-center justify-center rounded-full bg-slate-900 px-5 text-[16px] font-bold text-white hover:bg-black">
              {download.label}
            </a>
          </div>
        </>,
        document.body,
      )}
    </div>
  );
}
