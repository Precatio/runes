"use client";

import Link from "next/link";
import BlogBody, { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import LabelChips from "@/components/LabelChips";
import { AuthorByline, AuthorCard } from "@/components/ArticleAuthor";
import { useEnglishEdition, useLanguage } from "@/components/LanguageContext";
import ShareArticle from "@/components/ShareArticle";
import { authorOf } from "@/lib/site";
import type { ImageSizes } from "@/lib/blogSeo";

// One post, rendered on the server in Swedish (what search engines read). english: the address of its English edition,
// where a reader who has chosen English is taken (LanguageContext), so the page itself stays Swedish and carries no
// English text; without one, the frame is translated and a note says that the article is only in Swedish. The text is
// the author's, so the page translator leaves it alone.
export default function BlogArticle({ post, sizes, english = null }: { post: BlogPost; sizes?: ImageSizes; english?: string | null }) {
  useEnglishEdition(english);
  const chosen = useLanguage().lang;
  const lang = english ? "sv" : chosen;
  const v = inLanguage(post, lang);
  const author = authorOf(post.author);
  const name = post.author || author?.name;
  return (
    <article className="max-w-3xl mx-auto px-6 pt-16 pb-24">
      <nav aria-label="Brödsmulor" className="text-sm">
        <Link href="/artiklar" prefetch={false} className="tap font-bold text-[#b7410e] hover:underline">← Artiklar</Link>
      </nav>
      <div className="mt-8 text-sm text-slate-500">
        <time dateTime={post.publishedAt ?? post.month}>{postDate(post, lang)}</time>
      </div>
      <LabelChips labels={post.labels} lang={lang} linked className="mt-3" />
      <h1 className="mt-2 text-4xl md:text-5xl font-serif font-bold tracking-tight leading-tight" translate="no">{v.title}</h1>
      {v.summary && <p className="mt-5 text-xl text-slate-600 leading-relaxed" translate="no">{v.summary}</p>}
      {name && <AuthorByline name={name} author={author} lang={lang} />}
      {lang === "en" && !v.en && <p className="mt-4 text-sm text-slate-500">Den här artikeln finns bara på svenska.</p>}
      <div className="mt-10" translate="no"><BlogBody text={v.body} sizes={sizes} /></div>
      <ShareArticle title={v.title} lang={lang === "en" ? "en" : "sv"} />
      {author && <AuthorCard author={author} lang={lang} />}
    </article>
  );
}
