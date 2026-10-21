"use client";

// The articles page's search: finds articles by any word in title, summary or body (shared logic in
// lib/articleSearch.ts). A query can arrive from the landing page as ?q=.
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { BlogPost } from "@/components/BlogBody";
import BlogList from "@/components/BlogList";
import LabelFilter, { useLabelFromAddress, withLabel } from "@/components/LabelFilter";
import SortToggle, { useOrderFromAddress } from "@/components/SortToggle";
import { useLanguage } from "@/components/LanguageContext";
import { labelName } from "@/lib/labels";
import { loadIndex, matches, searchTerms, snippet, type IndexPost } from "@/lib/articleSearch";
import { trackSearch } from "@/lib/track";

export default function ArticleSearch({ posts, failed }: { posts: BlogPost[]; failed: boolean }) {
  // The landing page's search box links here with the query in the address; what the reader types then takes over
  const initialQ = useSyncExternalStore(() => () => {}, () => new URLSearchParams(window.location.search).get("q") ?? "", () => "");
  const [typed, setTyped] = useState<string | null>(null);
  const q = typed ?? initialQ;
  const setQ = setTyped;
  const [index, setIndex] = useState<IndexPost[] | null>(null);
  const [label, setLabel] = useLabelFromAddress();
  const [order, setOrder] = useOrderFromAddress();
  const { lang } = useLanguage();
  useEffect(() => {
    if (initialQ) loadIndex().then(setIndex);
  }, [initialQ]);

  const terms = useMemo(() => searchTerms(q), [q]);
  const by = useMemo(() => new Map((index ?? []).map(p => [p.slug, p])), [index]);
  const hits = useMemo(() => {
    if (!terms.length) return null;
    return posts.filter(p => {
      const ix = by.get(p.slug);
      if (ix) return matches(ix, terms);
      const hay = `${p.title} ${p.title_en ?? ""} ${p.summary ?? ""} ${p.summary_en ?? ""}`.toLowerCase();
      return terms.every(t => hay.includes(t));
    });
  }, [terms, posts, by]);

  // The words and the number of hits are counted once the typing has settled (lib/track.ts: anonymous, nothing else)
  useEffect(() => {
    if (!hits || !index) return; // before the full texts are fetched the hit count only covers titles and summaries
    const t = setTimeout(() => trackSearch(q, hits.length), 1500);
    return () => clearTimeout(t);
  }, [q, hits, index]);

  return (
    <>
      <div className="mt-8">
        <input value={q} onChange={e => setQ(e.target.value)} onFocus={() => loadIndex().then(setIndex)}
          placeholder="Sök i artiklarna – ett ord, ett signum, ett namn …"
          aria-label="Sök i artiklarna"
          className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-3.5 text-[16px] text-slate-900 placeholder:text-slate-400 shadow-sm outline-none focus:border-[#b7410e] focus:ring-2 focus:ring-[#b7410e]/20" />
        {hits && (
          <p className="mt-2 text-sm text-slate-500">
            {hits.length === 0 ? "Inga artiklar matchar sökningen." :
              hits.length === 1 ? "En artikel matchar." : `${hits.length} artiklar matchar.`}
            {!index && " Söker i titlar och sammanfattningar medan texterna hämtas …"}
          </p>
        )}
      </div>
      {hits && hits.length > 0 && terms.length > 0 && index && (
        <ul className="mt-4 space-y-1.5">
          {hits.flatMap(p => {
            const ix = by.get(p.slug);
            const s = ix ? snippet(ix, terms[0]) : null;
            return s ? [
              <li key={p.slug} className="text-sm text-slate-500 leading-relaxed">
                <span className="font-semibold text-slate-700">{p.title}:</span> ”{s}”
              </li>,
            ] : [];
          })}
        </ul>
      )}
      <div className="mt-8"><LabelFilter posts={posts} lang={lang} value={label} onChange={setLabel} /></div>
      <SortToggle posts={posts} lang={lang} value={order} onChange={setOrder} className="mt-5" />
      {label && withLabel(hits ?? posts, label).length === 0 && (
        <p className="mt-6 text-sm text-slate-500">
          {lang === "en" ? `No article carries the label “${labelName(label, lang)}”.` : `Ingen artikel har etiketten ”${label}”.`}
        </p>
      )}
      <div className="mt-10 space-y-10">
        <BlogList posts={withLabel(hits ?? posts, label)} failed={failed} order={order} />
      </div>
    </>
  );
}
