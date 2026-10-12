"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import BlogShell from "@/components/BlogShell";
import BlogBody, { inLanguage, monthLabel, type BlogPost } from "@/components/BlogBody";
import { useLanguage } from "@/components/LanguageContext";
import { API_URL } from "@/lib/api";

// One blog post. The text is the author's: it is shown as written (in English when there is an English version)
export default function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>();
  const { lang } = useLanguage();
  const [post, setPost] = useState<BlogPost | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/blog/posts/${encodeURIComponent(decodeURIComponent(slug))}`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(d => setPost(d.post))
      .catch(() => setMissing(true));
  }, [slug]);

  const v = post ? inLanguage(post, lang) : null;
  return (
    <BlogShell>
      <article className="max-w-3xl mx-auto px-6 pt-16 pb-24">
        <Link href="/blogg" className="text-sm font-bold text-[#b7410e] hover:underline">← Månadens fynd</Link>
        {missing && <p className="mt-10 text-slate-600">Inlägget finns inte eller är inte publicerat.</p>}
        {!post && !missing && <p className="mt-10 text-slate-500">Hämtar inlägget …</p>}
        {post && v && (
          <>
            <div className="mt-8 text-sm text-slate-500">{monthLabel(post.month, lang)}{post.author ? ` · ${post.author}` : ""}</div>
            <h1 className="mt-2 text-4xl md:text-5xl font-serif font-bold tracking-tight leading-tight" translate="no">{v.title}</h1>
            {v.summary && <p className="mt-5 text-xl text-slate-600 leading-relaxed" translate="no">{v.summary}</p>}
            {lang === "en" && !v.en && <p className="mt-4 text-sm text-slate-500">Det här inlägget finns bara på svenska.</p>}
            <div className="mt-10" translate="no"><BlogBody text={v.body} /></div>
          </>
        )}
      </article>
    </BlogShell>
  );
}
