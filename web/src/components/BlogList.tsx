"use client";

import Link from "next/link";
import { inLanguage, monthLabel, type BlogPost } from "@/components/BlogBody";
import { useLanguage } from "@/components/LanguageContext";
import { postPath } from "@/lib/blogSeo";

// The published posts, newest first; rendered on the server in Swedish and shown in English when chosen
export default function BlogList({ posts, failed }: { posts: BlogPost[]; failed: boolean }) {
  const { lang } = useLanguage();
  if (!posts.length) {
    return <p className="text-slate-500">{failed ? "Bloggen kunde inte hämtas just nu." : "Inga inlägg ännu. Det första kommer snart."}</p>;
  }
  return (
    <>
      {posts.map(p => {
        const v = inLanguage(p, lang);
        return (
          <article key={p.id} className="border-t-2 border-[#b7410e] pt-5">
            <div className="text-sm text-slate-500">
              <time dateTime={p.publishedAt ?? p.month}>{monthLabel(p.month, lang)}</time>{p.author ? ` · ${p.author}` : ""}
            </div>
            <h2 className="mt-1 text-2xl font-serif font-bold" translate="no">
              <Link href={postPath(p.slug)} className="hover:text-[#b7410e]">{v.title}</Link>
            </h2>
            <p className="mt-2 text-slate-600 leading-relaxed" translate="no">{v.summary}</p>
            <Link href={postPath(p.slug)} className="mt-3 inline-block text-sm font-bold text-[#b7410e] hover:underline">
              Läs inlägget →
            </Link>
          </article>
        );
      })}
    </>
  );
}
