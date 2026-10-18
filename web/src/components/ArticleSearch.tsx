"use client";

// Sökrutan på artikelsidan: hittar artiklar på vilket ord som helst i titel, sammanfattning eller brödtext.
// Indexet (ren text per artikel, src/blog_search.py) hämtas först när rutan används: lokalt från analysmotorn,
// på den statiska webbplatsen från /artiklar-sok.json som exporten skriver.
import { useMemo, useRef, useState } from "react";
import type { BlogPost } from "@/components/BlogBody";
import BlogList from "@/components/BlogList";
import { API_URL } from "@/lib/api";
import { PUBLIC_SITE } from "@/lib/site";

interface IndexPost {
  slug: string; title: string; title_en: string;
  text: string; text_en: string; summary: string; summary_en: string;
}

const haystack = (p: IndexPost) => `${p.title.toLowerCase()} ${p.title_en.toLowerCase()} ${p.summary} ${p.summary_en} ${p.text} ${p.text_en}`;

// Ett kort utdrag runt första träffen i brödtexten, för att visa var ordet står
function snippet(p: IndexPost, term: string): string | null {
  for (const text of [p.text, p.text_en]) {
    const i = text.indexOf(term);
    if (i >= 0) {
      const from = Math.max(0, i - 60);
      const to = Math.min(text.length, i + term.length + 90);
      return `${from > 0 ? "…" : ""}${text.slice(from, to).trim()}${to < text.length ? "…" : ""}`;
    }
  }
  return null;
}

export default function ArticleSearch({ posts, failed }: { posts: BlogPost[]; failed: boolean }) {
  const [q, setQ] = useState("");
  const [index, setIndex] = useState<IndexPost[] | null>(null);
  const loading = useRef(false);

  const loadIndex = async () => {
    if (index || loading.current) return;
    loading.current = true;
    try {
      const url = PUBLIC_SITE ? "/artiklar-sok.json" : `${API_URL}/api/blog/search_index`;
      const r = await fetch(url);
      if (r.ok) setIndex(((await r.json()) as { posts: IndexPost[] }).posts);
    } catch {
      // utan index söker vi i titel och sammanfattning från kortlistan
    } finally {
      loading.current = false;
    }
  };

  const terms = useMemo(() => q.toLowerCase().split(/\s+/).filter(t => t.length >= 2), [q]);
  const hits = useMemo(() => {
    if (!terms.length) return null;
    const by = new Map((index ?? []).map(p => [p.slug, p]));
    return posts.filter(p => {
      const ix = by.get(p.slug);
      const hay = ix ? haystack(ix) : `${p.title} ${p.title_en ?? ""} ${p.summary ?? ""} ${p.summary_en ?? ""}`.toLowerCase();
      return terms.every(t => hay.includes(t));
    });
  }, [terms, posts, index]);

  const by = new Map((index ?? []).map(p => [p.slug, p]));

  return (
    <>
      <div className="mt-8">
        <input value={q} onChange={e => setQ(e.target.value)} onFocus={loadIndex}
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
      <div className="mt-10 space-y-10">
        <BlogList posts={hits ?? posts} failed={failed} />
      </div>
    </>
  );
}
