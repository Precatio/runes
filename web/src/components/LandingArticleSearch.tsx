"use client";

// The landing page's compact article search: inline hits with a snippet, each leading to its article;
// the full archive search lives on /artiklar and gets the query passed along.
import { useMemo, useState } from "react";
import Link from "next/link";
import { loadIndex, matches, searchTerms, snippet, type IndexPost } from "@/lib/articleSearch";

export default function LandingArticleSearch() {
  const [q, setQ] = useState("");
  const [index, setIndex] = useState<IndexPost[] | null>(null);
  const [tried, setTried] = useState(false);

  const fetchIndex = () => loadIndex().then(ix => { setIndex(ix); setTried(true); });
  const terms = useMemo(() => searchTerms(q), [q]);
  const hits = useMemo(() => (terms.length && index ? index.filter(p => matches(p, terms)) : null),
    [terms, index]);

  return (
    <div className="mt-8 mb-10 max-w-2xl">
      <input value={q} onChange={e => { setQ(e.target.value); if (!index) fetchIndex(); }} onFocus={fetchIndex}
        placeholder="Sök i artiklarna – ett ord, ett signum, ett namn …"
        aria-label="Sök i artiklarna"
        className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-3.5 text-[16px] text-slate-900 placeholder:text-slate-400 shadow-sm outline-none focus:border-[#b7410e] focus:ring-2 focus:ring-[#b7410e]/20" />
      {terms.length > 0 && !index && (
        <p className="mt-2 text-sm text-slate-500">
          {tried ? <>Sökningen kunde inte hämta artiklarna just nu – prova i <Link href={`/artiklar?q=${encodeURIComponent(q)}`} className="underline text-[#b7410e]">artikelarkivet</Link>.</> : "Hämtar artiklarna …"}
        </p>
      )}
      {hits && (
        <div className="mt-3 rounded-2xl border border-slate-200 bg-white shadow-sm divide-y divide-slate-100">
          {hits.length === 0 && <p className="px-5 py-4 text-sm text-slate-500">Inga artiklar matchar sökningen.</p>}
          {hits.slice(0, 6).map(p => {
            const s = snippet(p, terms[0]);
            return (
              <Link key={p.slug} href={`/artiklar/${p.slug}`} className="block px-5 py-3.5 hover:bg-[#b7410e]/5">
                <span className="font-bold text-slate-900">{p.title}</span>
                {s && <span className="block text-sm text-slate-500 mt-0.5">”{s}”</span>}
              </Link>
            );
          })}
          {hits.length > 0 && (
            <Link href={`/artiklar?q=${encodeURIComponent(q)}`} className="block px-5 py-3 text-sm font-bold text-[#b7410e] hover:bg-[#b7410e]/5">
              {hits.length === 1 ? "Öppna i artikelarkivet" : `Visa alla ${hits.length} i artikelarkivet`} →
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
