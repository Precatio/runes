"use client";
/* eslint-disable @next/next/no-img-element -- the public site is a static export without image optimisation */

import Link from "next/link";
import { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import { useLanguage } from "@/components/LanguageContext";
import { ARTICLES_PATH, postPath, thumbnail } from "@/lib/blogSeo";

// "More articles" under an article: links to the others, so that a reader – and a search engine – finds them
export default function MoreArticles({ posts }: { posts: BlogPost[] }) {
  const { lang } = useLanguage();
  const en = lang === "en";
  if (!posts.length) return null;
  return (
    <section className="max-w-3xl mx-auto px-6 pb-24" aria-labelledby="fler-artiklar">
      <div className="border-t border-slate-900/10 pt-10 flex items-baseline justify-between gap-4">
        <h2 id="fler-artiklar" className="text-2xl font-serif font-bold">{en ? "More articles" : "Fler artiklar"}</h2>
        <Link href={ARTICLES_PATH} className="text-sm font-bold text-[#b7410e] hover:underline">
          {en ? "All articles →" : "Alla artiklar →"}
        </Link>
      </div>
      <div className="mt-6 grid gap-5 sm:grid-cols-3">
        {posts.map(p => {
          const v = inLanguage(p, lang);
          return (
            <Link key={p.id} href={postPath(p.slug)}
              className="group block rounded-2xl border border-slate-200 bg-white/70 overflow-hidden transition hover:-translate-y-0.5 hover:border-[#b7410e]/50 hover:shadow-lg">
              {p.image ? (
                <div className="aspect-[16/10] overflow-hidden bg-slate-200">
                  <img src={thumbnail(p.image, 330)} alt={p.image_alt || v.title} loading="lazy" decoding="async"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                </div>
              ) : (
                <div className="aspect-[16/10] flex items-center justify-center bg-[#f3ede4]" aria-hidden="true">
                  <span className="text-5xl text-[#b7410e]/30 select-none">ᚱ</span>
                </div>
              )}
              <div className="p-4">
                <time className="text-xs text-slate-500" dateTime={p.publishedAt ?? p.month}>{postDate(p, lang)}</time>
                <h3 className="mt-1 font-serif font-bold leading-snug group-hover:text-[#b7410e]" translate="no">{v.title}</h3>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
