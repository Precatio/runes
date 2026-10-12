"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import BlogShell from "@/components/BlogShell";
import { inLanguage, monthLabel, type BlogPost } from "@/components/BlogBody";
import { useLanguage } from "@/components/LanguageContext";
import { API_URL } from "@/lib/api";

// The blog: one post a month about the most interesting patterns and findings (written in Admin)
export default function BlogPage() {
  const { lang } = useLanguage();
  const [posts, setPosts] = useState<BlogPost[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/blog/posts`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(d => setPosts(d.posts))
      .catch(() => { setError(true); setPosts([]); });
  }, []);

  return (
    <BlogShell>
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Månadens fynd</div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Mönster i runstenarna</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          En gång i månaden skriver vi om de mest intressanta mönstren och fynden i Vitki – vad vi ser, vad det kan
          betyda och hur det kan prövas. Siffrorna kommer från appens analyser och kan granskas där.
        </p>

        <div className="mt-14 space-y-10">
          {posts === null && <p className="text-slate-500">Hämtar inläggen …</p>}
          {posts && posts.length === 0 && (
            <p className="text-slate-500">{error ? "Bloggen kunde inte hämtas just nu." : "Inga inlägg ännu. Det första kommer snart."}</p>
          )}
          {posts?.map(p => {
            const v = inLanguage(p, lang);
            return (
              <article key={p.id} className="border-t-2 border-[#b7410e] pt-5">
                <div className="text-sm text-slate-500">{monthLabel(p.month, lang)}{p.author ? ` · ${p.author}` : ""}</div>
                <h2 className="mt-1 text-2xl font-serif font-bold" translate="no">
                  <Link href={`/blogg/${encodeURIComponent(p.slug)}`} className="hover:text-[#b7410e]">{v.title}</Link>
                </h2>
                <p className="mt-2 text-slate-600 leading-relaxed" translate="no">{v.summary}</p>
                <Link href={`/blogg/${encodeURIComponent(p.slug)}`} className="mt-3 inline-block text-sm font-bold text-[#b7410e] hover:underline">
                  Läs inlägget →
                </Link>
              </article>
            );
          })}
        </div>
      </section>
    </BlogShell>
  );
}
