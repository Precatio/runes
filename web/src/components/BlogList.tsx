"use client";
/* eslint-disable @next/next/no-img-element -- the public site is a static export without image optimisation */

import Link from "next/link";
import { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import { featuredFirst } from "@/lib/featured";
import { useLanguage } from "@/components/LanguageContext";
import { postPath, thumbnail } from "@/lib/blogSeo";
import LabelChips from "@/components/LabelChips";

// The article's first photo, or a rune on the page colour when it has none
function Picture({ post, width, className }: { post: BlogPost; width: number; className: string }) {
  if (!post.image) {
    return (
      <div className={`${className} flex items-center justify-center bg-[#f3ede4]`} aria-hidden="true">
        <span className="text-6xl text-[#b7410e]/30 select-none">ᚱ</span>
      </div>
    );
  }
  return (
    <div className={`${className} overflow-hidden bg-slate-200`}>
      <img src={thumbnail(post.image, width)} alt={post.image_alt || post.title} loading="lazy" decoding="async"
        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
    </div>
  );
}

// The published posts: the article of the month first and large, then the others newest first, each a card that is
// a link as a whole; rendered on the server in Swedish and shown in English when chosen
export default function BlogList({ posts, failed }: { posts: BlogPost[]; failed: boolean }) {
  const { lang } = useLanguage();
  if (!posts.length) {
    return <p className="text-slate-500">{failed ? "Artiklarna kunde inte hämtas just nu." : "Inga artiklar ännu. Den första kommer snart."}</p>;
  }
  const read = lang === "en" ? "Read the article →" : "Läs artikeln →";
  return (
    <>
      {featuredFirst(posts).map((p, i) => {
        const v = inLanguage(p, lang);
        const big = i === 0 && p.featured;
        const meta = (
          <div className="text-sm text-slate-500">
            {p.featured && (
              <span className="mr-2 text-xs font-bold uppercase tracking-wider text-[#b7410e]">
                {lang === "en" ? "Article of the month" : "Månadens artikel"}
              </span>
            )}
            <time dateTime={p.publishedAt ?? p.month}>{postDate(p, lang)}</time>{p.author ? ` · ${p.author}` : ""}
          </div>
        );
        const chips = (
          <div className="mt-3">
            <LabelChips labels={p.labels} lang={lang} />
          </div>
        );
        return (
          <article key={p.id}>
            <Link href={postPath(p.slug)}
              className={`group block rounded-2xl border border-slate-200 bg-white/70 overflow-hidden transition hover:-translate-y-0.5 hover:border-[#b7410e]/50 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#b7410e] ${big ? "" : "sm:flex"}`}>
              <Picture post={p} width={big ? 960 : 500}
                className={big ? "aspect-[16/9] w-full" : "aspect-[16/9] w-full sm:aspect-auto sm:w-56 sm:min-h-[11rem] shrink-0"} />
              <div className="p-5 sm:p-6 flex flex-col">
                {meta}
                <h2 className={`mt-1 font-serif font-bold leading-snug group-hover:text-[#b7410e] ${big ? "text-3xl" : "text-2xl"}`} translate="no">
                  {v.title}
                </h2>
                <p className="mt-2 text-slate-600 leading-relaxed line-clamp-4" translate="no">{v.summary}</p>
                {chips}
                <span className="mt-3 text-sm font-bold text-[#b7410e] group-hover:underline">{read}</span>
              </div>
            </Link>
          </article>
        );
      })}
    </>
  );
}
