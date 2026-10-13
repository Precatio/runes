"use client";

import Link from "next/link";
import BlogBody, { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import { useLanguage } from "@/components/LanguageContext";

// One post, rendered on the server in Swedish (what search engines read) and shown in English when the reader has
// chosen English and the post has an English version. The text is the author's, so the page translator leaves it alone.
export default function BlogArticle({ post }: { post: BlogPost }) {
  const { lang } = useLanguage();
  const v = inLanguage(post, lang);
  return (
    <article className="max-w-3xl mx-auto px-6 pt-16 pb-24">
      <nav aria-label="Brödsmulor" className="text-sm">
        <Link href="/artiklar" className="font-bold text-[#b7410e] hover:underline">← Artiklar</Link>
      </nav>
      <div className="mt-8 text-sm text-slate-500">
        <time dateTime={post.publishedAt ?? post.month}>{postDate(post, lang)}</time>{post.author ? ` · ${post.author}` : ""}
      </div>
      <h1 className="mt-2 text-4xl md:text-5xl font-serif font-bold tracking-tight leading-tight" translate="no">{v.title}</h1>
      {v.summary && <p className="mt-5 text-xl text-slate-600 leading-relaxed" translate="no">{v.summary}</p>}
      {lang === "en" && !v.en && <p className="mt-4 text-sm text-slate-500">Den här artikeln finns bara på svenska.</p>}
      <div className="mt-10" translate="no"><BlogBody text={v.body} /></div>
    </article>
  );
}
