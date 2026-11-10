"use client";

import { useEffect, useMemo, useState } from "react";
import { NEWS_CATEGORIES, newsDate, type NewsItem } from "@/lib/news";

// The news as a card index (/nyheter): one drawer per month, one index card per notice. The two newest drawers stand
// open; older ones open with a click. A search or a subject filter opens every drawer with a match. A link to a notice
// (/nyheter#id, as from the start page) opens its drawer and its card.
const MONTHS = ["Januari", "Februari", "Mars", "April", "Maj", "Juni", "Juli", "Augusti", "September", "Oktober", "November", "December"];
const OPEN_DRAWERS = 2;
const LONG = 170; // characters before a card's text is shortened to a preview

const norm = (s: string) => s.toLocaleLowerCase("sv-SE").normalize("NFD").replace(/[̀-ͯ]/g, "");
const monthOf = (d: string) => d.slice(0, 7);
const catLabel = (k?: string) => NEWS_CATEGORIES.find((c) => c.key === k)?.label ?? "Publicerat";
// faint ruled lines, as on a library catalogue card
const RULED = { backgroundImage: "repeating-linear-gradient(to bottom, transparent 0, transparent 23px, rgba(15,23,42,0.045) 23px, rgba(15,23,42,0.045) 24px)" };

function MonthName({ ym }: { ym: string }) {
  const [y, m] = ym.split("-");
  return <><span>{MONTHS[Number(m) - 1]}</span> <span>{y}</span></>;
}

export default function NewsCatalog({ items }: { items: NewsItem[] }) {
  const months = useMemo(() => [...new Set(items.map((i) => monthOf(i.date)))].sort().reverse(), [items]);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<string | null>(null);
  const [openDrawers, setOpenDrawers] = useState<Set<string>>(() => new Set(months.slice(0, OPEN_DRAWERS)));
  const [openCards, setOpenCards] = useState<Set<string>>(new Set());

  // A link straight to a notice opens its drawer and card and scrolls to it
  useEffect(() => {
    const openHash = () => {
      const id = decodeURIComponent(window.location.hash.slice(1));
      const hit = id && items.find((i) => i.id === id);
      if (!hit) return;
      setOpenDrawers((s) => new Set(s).add(monthOf(hit.date)));
      setOpenCards((s) => new Set(s).add(hit.id));
      setTimeout(() => document.getElementById(hit.id)?.scrollIntoView({ block: "start" }), 60);
    };
    const t = setTimeout(openHash, 0);
    window.addEventListener("hashchange", openHash);
    return () => { clearTimeout(t); window.removeEventListener("hashchange", openHash); };
  }, [items]);

  const filtering = q.trim() !== "" || cat !== null;
  const shown = useMemo(() => {
    const words = norm(q).split(/\s+/).filter(Boolean);
    return items.filter((i) => (!cat || (i.kategori ?? "publicerat") === cat)
      && words.every((w) => norm(`${i.title} ${i.text}`).includes(w)));
  }, [items, q, cat]);
  const byMonth = useMemo(() => {
    const m = new Map<string, NewsItem[]>();
    for (const i of shown) m.set(monthOf(i.date), [...(m.get(monthOf(i.date)) ?? []), i]);
    return m;
  }, [shown]);
  const counts = useMemo(() => {
    const c = new Map<string, number>();
    for (const i of items) c.set(i.kategori ?? "publicerat", (c.get(i.kategori ?? "publicerat") ?? 0) + 1);
    return c;
  }, [items]);

  const toggle = (set: Set<string>, key: string) => { const s = new Set(set); if (s.has(key)) s.delete(key); else s.add(key); return s; };
  const chip = (active: boolean) =>
    `tap px-3 h-9 inline-flex items-center rounded-full border text-sm font-semibold transition-colors ${active
      ? "bg-[#b7410e] border-[#b7410e] text-white" : "bg-white border-slate-900/15 text-slate-700 hover:border-slate-900/40"}`;

  return (
    <div>
      {/* Search and subjects */}
      <div className="flex flex-col gap-4">
        <label className="relative block max-w-xl">
          <span className="sr-only">Sök bland nyheterna</span>
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Sök bland nyheterna"
            className="w-full h-11 rounded-full border border-slate-900/15 bg-white px-5 text-base outline-none focus:border-[#b7410e]" />
        </label>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setCat(null)} className={chip(cat === null)}>
            <span>Alla</span><span className="ml-1.5 opacity-70">{items.length}</span>
          </button>
          {NEWS_CATEGORIES.filter((c) => counts.get(c.key)).map((c) => (
            <button key={c.key} type="button" onClick={() => setCat(cat === c.key ? null : c.key)} className={chip(cat === c.key)}>
              <span>{c.label}</span><span className="ml-1.5 opacity-70">{counts.get(c.key)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* The drawers' labels: an index of the months */}
      <nav aria-label="Månader" className="mt-8 flex flex-wrap gap-2 border-b border-slate-900/10 pb-4">
        {months.map((ym) => {
          const n = byMonth.get(ym)?.length ?? 0;
          return (
            <a key={ym} href={`#lada-${ym}`} onClick={() => setOpenDrawers((s) => new Set(s).add(ym))}
              className={`tap px-3 py-1.5 border text-xs font-bold uppercase tracking-[0.12em] bg-[#efe9df] border-slate-900/15 hover:border-[#b7410e] ${n ? "text-slate-700" : "text-slate-400"}`}>
              <MonthName ym={ym} /><span className="ml-1.5 font-mono font-normal normal-case tracking-normal">{n}</span>
            </a>
          );
        })}
      </nav>

      {shown.length === 0 && <p className="mt-10 text-slate-600">Inga notiser matchar sökningen.</p>}

      {/* One drawer per month */}
      <div className="mt-8 space-y-6">
        {months.filter((ym) => byMonth.has(ym)).map((ym) => {
          const cards = byMonth.get(ym)!;
          const open = filtering || openDrawers.has(ym);
          return (
            <section key={ym} id={`lada-${ym}`} className="scroll-mt-20 rounded-xl border border-slate-900/10 bg-[#efe9df]/70">
              <button type="button" onClick={() => setOpenDrawers((s) => toggle(s, ym))} aria-expanded={open}
                className="tap w-full flex items-center justify-between gap-4 px-5 py-4 text-left">
                <span className="inline-flex items-center gap-3">
                  <span className="border-2 border-slate-900/25 bg-[#fbf8f2] px-3 py-1 font-serif font-bold text-lg"><MonthName ym={ym} /></span>
                  <span className="text-sm text-slate-600"><span className="font-mono">{cards.length}</span> <span>kort</span></span>
                </span>
                <span className="ml-auto pl-4 text-sm font-semibold text-[#b7410e] whitespace-nowrap">{open ? "Stäng lådan" : "Öppna lådan"}</span>
              </button>
              {open && (
                <ul className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 px-5 pb-5">
                  {cards.map((n) => {
                    const long = n.text.length > LONG;
                    const expanded = openCards.has(n.id);
                    return (
                      <li key={n.id} id={n.id} className="scroll-mt-24">
                        <article className="h-full flex flex-col rounded-md border border-slate-900/10 border-t-2 border-t-[#b7410e] bg-[#fffdf8] shadow-sm px-4 pt-3 pb-3" style={RULED}>
                          <div className="flex items-center justify-between gap-2 text-[11px]">
                            <time dateTime={n.date} className="font-mono text-slate-500">{newsDate(n.date)}</time>
                            <span className="font-bold uppercase tracking-[0.12em] text-[#b7410e] text-right">{catLabel(n.kategori)}</span>
                          </div>
                          <h3 className="mt-2 font-serif font-bold text-[17px] leading-snug text-slate-900">{n.title}</h3>
                          <p className={`mt-1.5 text-sm text-slate-600 leading-6 ${long && !expanded ? "line-clamp-3" : ""}`}>{n.text}</p>
                          <div className="mt-auto pt-2 flex items-center justify-between text-xs">
                            {long ? (
                              <button type="button" onClick={() => setOpenCards((s) => toggle(s, n.id))} className="tap font-semibold text-[#b7410e] hover:underline">
                                {expanded ? "Visa mindre" : "Läs mer"}
                              </button>
                            ) : <span />}
                            <a href={`#${n.id}`} className="tap text-slate-400 hover:text-slate-700" aria-label="Länk till notisen">#</a>
                          </div>
                        </article>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
