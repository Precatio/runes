"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { inLanguage, monthLabel, type BlogPost } from "@/components/BlogBody";
import { useLanguage } from "@/components/LanguageContext";
import { postPath } from "@/lib/blogSeo";

// The newest articles on the start page: the latest large, with its first photo, and up to three more beside it. Rendered
// on the server in Swedish and shown in English when the reader has chosen English.
export default function ArticleTeasers({ posts, photo }: { posts: BlogPost[]; photo?: { src: string; alt: string; credit: string | null } | null }) {
  const { lang } = useLanguage();
  if (!posts.length) return <p className="text-slate-500">Den första artikeln kommer snart.</p>;
  const [first, ...rest] = posts;
  const v = inLanguage(first, lang);
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8">
      <article className="rounded-3xl bg-white border border-slate-200 overflow-hidden flex flex-col md:flex-row lg:flex-col xl:flex-row">
        {photo && (
          <Link href={postPath(first.slug)} className="relative md:w-2/5 lg:w-full xl:w-2/5 shrink-0 bg-slate-100">
            <img src={photo.src} alt={photo.alt} className="h-64 md:h-full lg:h-64 xl:h-full w-full object-cover" />
            {photo.credit && (
              <span className="absolute bottom-0 right-0 bg-slate-900/60 text-white text-[10px] px-2 py-0.5">Foto: {photo.credit}</span>
            )}
          </Link>
        )}
        <div className="p-7 flex flex-col">
          <div className="text-xs font-bold uppercase tracking-wider text-[#b7410e]">Senaste artikeln · {monthLabel(first.month, lang)}</div>
          <h3 className="mt-2 text-2xl md:text-3xl font-serif font-bold leading-tight" translate="no">
            <Link href={postPath(first.slug)} className="hover:text-[#b7410e]">{v.title}</Link>
          </h3>
          <p className="mt-3 text-slate-600 leading-relaxed" translate="no">{v.summary}</p>
          <Link href={postPath(first.slug)} className="mt-5 inline-block self-start px-5 py-2.5 rounded-full bg-[#b7410e] text-white text-sm font-bold hover:bg-[#9a350b]">
            Läs artikeln
          </Link>
        </div>
      </article>
      <div className="flex flex-col gap-6">
        {rest.slice(0, 3).map(p => {
          const w = inLanguage(p, lang);
          return (
            <article key={p.id} className="border-t-2 border-[#b7410e] pt-4">
              <div className="text-xs text-slate-500">{monthLabel(p.month, lang)}</div>
              <h3 className="mt-1 text-lg font-serif font-bold leading-snug" translate="no">
                <Link href={postPath(p.slug)} className="hover:text-[#b7410e]">{w.title}</Link>
              </h3>
              <p className="mt-1 text-sm text-slate-600 leading-relaxed line-clamp-3" translate="no">{w.summary}</p>
            </article>
          );
        })}
        <div className="mt-auto rounded-2xl border border-[#b7410e]/30 bg-[#fbf3ee] p-5">
          <p className="text-sm text-slate-700 leading-relaxed">
            Artiklarna berättar om de mönster som Vitkis analyser hittar i runstenarna – för alla som är intresserade av
            runor och vikingatid, med statistiken förklarad och prövad.
          </p>
          <Link href="/artiklar" className="mt-3 inline-block text-sm font-bold text-[#b7410e] hover:underline">Alla artiklar →</Link>
        </div>
      </div>
    </div>
  );
}
