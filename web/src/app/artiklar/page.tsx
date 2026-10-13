import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import BlogList from "@/components/BlogList";
import type { BlogPost } from "@/components/BlogBody";
import { API_URL } from "@/lib/api";
import { BLOG_DESCRIPTION, BLOG_TITLE, blogJsonLd } from "@/lib/blogSeo";

// The articles about the most interesting patterns (written in Admin), rendered on the server
export const revalidate = 60;

export const metadata: Metadata = {
  title: BLOG_TITLE,
  description: BLOG_DESCRIPTION,
  alternates: { canonical: "/artiklar", types: { "application/rss+xml": "/artiklar/rss.xml" } },
  openGraph: { type: "website", url: "/artiklar", title: BLOG_TITLE, description: BLOG_DESCRIPTION, siteName: "Vitki", locale: "sv_SE" },
  twitter: { card: "summary_large_image", title: BLOG_TITLE, description: BLOG_DESCRIPTION },
};

export default async function BlogPage() {
  let posts: BlogPost[] = [], failed = false;
  try {
    const r = await fetch(`${API_URL}/api/blog/posts`, { next: { revalidate: 60, tags: ["blog"] } });
    if (r.ok) posts = (await r.json()).posts; else failed = true;
  } catch {
    failed = true;
  }
  return (
    <BlogShell>
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Artiklar</div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Mönster i runstenarna</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Här skriver vi om de mest intressanta mönstren i de svenska runstenarna – vad vi ser, vad det kan betyda och
          hur det kan prövas. Siffrorna kommer från Vitkis analyser och förklaras i texten.
        </p>
        <div className="mt-14 space-y-10"><BlogList posts={posts} failed={failed} /></div>
      </section>
      {posts.length > 0 && (
         
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(blogJsonLd(posts)).replace(/</g, "\\u003c") }} />
      )}
    </BlogShell>
  );
}
