import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import ArticleSearch from "@/components/ArticleSearch";
import ContentVote from "@/components/ContentVote";
import { listPosts } from "@/lib/articles";
import { REPORTS_PATH } from "@/lib/report";
import { ARTICLES_PATH, BLOG_DESCRIPTION, BLOG_TITLE, blogJsonLd, languageAlternates, withImageSizes } from "@/lib/blogSeo";

// The articles about the most interesting patterns (written in Admin), rendered on the server
export const revalidate = 60;

export const metadata: Metadata = {
  title: BLOG_TITLE,
  description: BLOG_DESCRIPTION,
  alternates: { canonical: ARTICLES_PATH, languages: languageAlternates(), types: { "application/rss+xml": "/artiklar/rss.xml" } },
  openGraph: { type: "website", url: ARTICLES_PATH, title: BLOG_TITLE, description: BLOG_DESCRIPTION, siteName: "Vitki", locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: BLOG_TITLE }] },
  twitter: { card: "summary_large_image", title: BLOG_TITLE, description: BLOG_DESCRIPTION, images: ["/delningsbild.png"] },
};

export default async function BlogPage() {
  const list = await listPosts();
  // With the photos' sizes, so that a card never asks Commons for a thumbnail wider than the original
  const posts = await withImageSizes(list.posts), failed = list.failed;
  return (
    <BlogShell>
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24">
        <div className="flex items-center justify-between gap-4 mb-3"><div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Artiklar</div><Link href="/en/artiklar/" hrefLang="en" className="tap text-sm text-[#b7410e] font-semibold hover:underline">In English →</Link></div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Mönster i runstenarna</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Här skriver vi om de mest intressanta mönstren i de svenska runstenarna – vad vi ser, vad det kan betyda och
          hur det kan prövas. Siffrorna kommer från Vitkis analyser och förklaras i texten.
        </p>
        <p className="mt-3 text-sm text-slate-500">
          De prövade fynden finns också i vetenskaplig form, märkta efter hur hårt de prövats, med version och citering, under{" "}
          <Link href={REPORTS_PATH} prefetch={false} className="font-semibold text-[#b7410e] hover:underline">Forskningsrapporter</Link>.
        </p>
        <div className="mt-10"><ArticleSearch posts={posts} failed={failed} /></div>
        <ContentVote />
      </section>
      {posts.length > 0 && (
         
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(blogJsonLd(posts)).replace(/</g, "\\u003c") }} />
      )}
    </BlogShell>
  );
}
