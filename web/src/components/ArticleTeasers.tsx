"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import { featuredFirst } from "@/lib/featured";
import { useLanguage } from "@/components/LanguageContext";
import { commonsAt, commonsSrcSet, postPath } from "@/lib/blogSeo";

// The articles on the start page: the article of the week large (or the latest, when none is chosen), with its first
// photo, and up to three more beside it. Rendered on the server in Swedish and shown in English when the reader has
// chosen English. The photo is a Commons thumbnail no wider than its original (lib/blogSeo.ts commonsAt), when the page
// knows the original's size; the links beside it are not prefetched (they load when clicked).
type Photo = { src: string; alt: string; credit: string | null; width?: number; height?: number };
// How wide the photo is drawn. The box is 40 % of the article beside the text from md and xl up (about 250 px wide and
// as tall as the text, up to about 620 px at xl and 440 px at md), the whole article 256 px tall at lg, the page below md.
// The photo covers the box (object-cover), so a landscape photo is drawn as wide as the box's height times its aspect
// ratio, not only as wide as the box: the larger of the two, as the share picture does (app/delningsbild.png).
function photoSizes(width: number, height?: number): string {
  const ratio = height ? width / height : 1;
  const cover = (tall: number) => Math.ceil(tall * ratio);
  // A box as wide as part of the window (from `from` px up) and `tall` px tall: the window's share where that is wider
  // than the covered height, and the covered width on the narrower windows where it is not
  const share = (vw: string, part: number, minus: number, from: number, tall: number) => {
    const px = cover(tall), at = Math.ceil((px + minus) / part), when = (w: number) => (w ? `(min-width: ${w}px) ` : "");
    return at <= from ? [`${when(from)}${vw}`] : [`${when(at)}${vw}`, `${when(from)}${px}px`];
  };
  return [`(min-width: 1280px) ${Math.max(250, cover(620))}px`, ...share("58vw", 0.58, 0, 1024, 256),
          `(min-width: 768px) ${Math.max(410, cover(440))}px`, ...share("calc(100vw - 48px)", 1, 48, 0, 256)].join(", ");
}

export default function ArticleTeasers({ posts, photo }: { posts: BlogPost[]; photo?: Photo | null }) {
  const { lang } = useLanguage();
  if (!posts.length) return <p className="text-slate-500">Den första artikeln kommer snart.</p>;
  const [first, ...rest] = featuredFirst(posts);
  const v = inLanguage(first, lang);
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8">
      <article className="rounded-3xl bg-white border border-slate-200 overflow-hidden flex flex-col">
        {/* The article of the week is marked with a band of Vitki's rust red along the top of the box */}
        {first.featured && <div className="h-1.5 shrink-0 bg-[#b7410e]" aria-hidden />}
        <div className="flex flex-1 flex-col md:flex-row lg:flex-col xl:flex-row">
        {photo && (
          <Link href={postPath(first.slug)} className="relative md:w-2/5 lg:w-full xl:w-2/5 shrink-0 bg-slate-100">
            <img src={commonsAt(photo.src, 960, photo.width)} srcSet={commonsSrcSet(photo.src, photo.width, [500, 960])}
              sizes={photo.width ? photoSizes(photo.width, photo.height) : undefined} alt={photo.alt} loading="lazy" decoding="async"
              className="h-64 md:h-full lg:h-64 xl:h-full w-full object-cover" />
            {photo.credit && (
              <span className="absolute bottom-0 right-0 bg-slate-900/60 text-white text-[10px] px-2 py-0.5">Foto: {photo.credit}</span>
            )}
          </Link>
        )}
        <div className="p-7 flex flex-col">
          <div className="text-xs font-bold uppercase tracking-wider text-[#b7410e]">{first.featured ? "Veckans artikel" : "Senaste artikeln"} · {postDate(first, lang)}</div>
          <h3 className="mt-2 text-2xl md:text-3xl font-serif font-bold leading-tight" translate="no">
            <Link href={postPath(first.slug)} className="hover:text-[#b7410e]">{v.title}</Link>
          </h3>
          <p className="mt-3 text-slate-600 leading-relaxed" translate="no">{v.summary}</p>
          <Link href={postPath(first.slug)} className="mt-5 inline-block self-start px-5 py-2.5 rounded-full bg-[#b7410e] text-white text-sm font-bold hover:bg-[#9a350b]">
            Läs artikeln
          </Link>
        </div>
        </div>
      </article>
      <div className="flex flex-col gap-6">
        {rest.slice(0, 3).map(p => {
          const w = inLanguage(p, lang);
          return (
            <article key={p.id} className="border-t-2 border-[#b7410e] pt-4">
              <div className="text-xs text-slate-500">{postDate(p, lang)}</div>
              <h3 className="mt-1 text-lg font-serif font-bold leading-snug" translate="no">
                <Link href={postPath(p.slug)} prefetch={false} className="hover:text-[#b7410e]">{w.title}</Link>
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
