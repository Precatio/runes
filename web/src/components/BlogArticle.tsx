"use client";

import Link from "next/link";
import BlogBody, { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import LabelChips from "@/components/LabelChips";
import { useLanguage } from "@/components/LanguageContext";
import ShareArticle from "@/components/ShareArticle";
import { authorOf } from "@/lib/site";
import type { ImageSizes } from "@/lib/blogSeo";

// One post, rendered on the server in Swedish (what search engines read) and shown in English when the reader has
// chosen English and the post has an English version. The text is the author's, so the page translator leaves it alone.
export default function BlogArticle({ post, sizes }: { post: BlogPost; sizes?: ImageSizes }) {
  const { lang } = useLanguage();
  const v = inLanguage(post, lang);
  const author = authorOf(post.author);
  const name = post.author || author?.name;
  return (
    <article className="max-w-3xl mx-auto px-6 pt-16 pb-24">
      <nav aria-label="Brödsmulor" className="text-sm">
        <Link href="/artiklar" prefetch={false} className="font-bold text-[#b7410e] hover:underline">← Artiklar</Link>
      </nav>
      <div className="mt-8 text-sm text-slate-500">
        <time dateTime={post.publishedAt ?? post.month}>{postDate(post, lang)}</time>
      </div>
      <LabelChips labels={post.labels} lang={lang} linked className="mt-3" />
      <h1 className="mt-2 text-4xl md:text-5xl font-serif font-bold tracking-tight leading-tight" translate="no">{v.title}</h1>
      {v.summary && <p className="mt-5 text-xl text-slate-600 leading-relaxed" translate="no">{v.summary}</p>}
      {name && (
        <div className="mt-7 flex items-center gap-3 border-y border-slate-900/10 py-4" translate="no">
          <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#b7410e] text-sm font-bold text-white">
            {name.split(/\s+/).map(w => w[0]).slice(0, 2).join("")}
          </span>
          <div className="leading-tight">
            <div className="text-xs uppercase tracking-wider text-slate-500">{lang === "en" ? "By" : "Av"}</div>
            {author
              ? <Link href={author.page} rel="author" className="text-base font-bold text-slate-900 hover:text-[#b7410e]">{name}</Link>
              : <span className="text-base font-bold text-slate-900">{name}</span>}
            {author && <div className="text-sm text-slate-500">{lang === "en" ? author.role_en : author.role}</div>}
          </div>
          {author && (
            <a href={author.linkedin} target="_blank" rel="noopener noreferrer" className="ml-auto text-sm font-bold text-[#b7410e] hover:underline">
              LinkedIn ↗
            </a>
          )}
        </div>
      )}
      {lang === "en" && !v.en && <p className="mt-4 text-sm text-slate-500">Den här artikeln finns bara på svenska.</p>}
      <div className="mt-10" translate="no"><BlogBody text={v.body} sizes={sizes} /></div>
      <ShareArticle title={v.title} lang={lang === "en" ? "en" : "sv"} />
      {author && (
        <aside className="mt-16 rounded-2xl border border-slate-900/10 bg-white p-6" translate="no">
          <div className="text-xs font-bold uppercase tracking-wider text-[#b7410e]">{lang === "en" ? "The person behind Vitki" : "Personen bakom Vitki"}</div>
          <Link href={author.page} rel="author" className="mt-2 inline-block text-lg font-bold text-slate-900 hover:text-[#b7410e]">{author.name}</Link>
          <p className="mt-2 text-slate-600 leading-relaxed">{lang === "en" ? author.bio_en : author.bio}</p>
          <div className="mt-3 flex flex-wrap gap-4 text-sm font-bold text-[#b7410e]">
            <Link href={author.page} className="hover:underline">{lang === "en" ? "The person behind Vitki, and contact →" : "Personen bakom Vitki, och kontakt →"}</Link>
            <a href={author.linkedin} target="_blank" rel="noopener noreferrer" className="hover:underline">LinkedIn ↗</a>
          </div>
        </aside>
      )}
    </article>
  );
}
