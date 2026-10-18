import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import { postDate } from "@/components/BlogBody";
import { listPosts } from "@/lib/articles";
import { featuredFirst } from "@/lib/featured";
import { BLOG_DESCRIPTION_EN, BLOG_TITLE_EN, EN_ARTICLES_PATH, enPostPath, languageAlternates, metaDescription } from "@/lib/blogSeo";

// The English index of the articles, rendered on the server; every article links its Swedish original via hreflang
export const revalidate = 60;

export const metadata: Metadata = {
  title: BLOG_TITLE_EN,
  description: BLOG_DESCRIPTION_EN,
  alternates: { canonical: EN_ARTICLES_PATH, languages: languageAlternates() },
  openGraph: { type: "website", url: EN_ARTICLES_PATH, title: BLOG_TITLE_EN, description: BLOG_DESCRIPTION_EN,
               siteName: "Vitki", locale: "en_GB",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: BLOG_TITLE_EN }] },
  twitter: { card: "summary_large_image", title: BLOG_TITLE_EN, description: BLOG_DESCRIPTION_EN, images: ["/delningsbild.png"] },
};

export default async function EnglishBlogPage() {
  const { posts } = await listPosts();
  const withEn = featuredFirst(posts.filter(p => p.title_en));
  return (
    <BlogShell>
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24" lang="en">
        <div className="flex items-center justify-between gap-4">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Articles</div>
          <Link href="/artiklar/" className="text-sm text-[#b7410e] font-semibold hover:underline" hrefLang="sv">Läs på svenska →</Link>
        </div>
        <h1 className="mt-3 text-4xl md:text-5xl font-serif font-bold tracking-tight">Hidden patterns of the runestones</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          What we see when all of Sweden&apos;s Viking-age runestones are read at once – what it may mean, and how it
          can be tested. The figures come from Vitki&apos;s open analyses and are explained in the text.
        </p>
        <ul className="mt-14 space-y-10">
          {withEn.map(p => (
            <li key={p.slug} className="border-t border-slate-200 pt-8">
              <p className="text-sm text-slate-500">{postDate(p, "en")}{p.author && <> · {p.author}</>}</p>
              <h2 className="mt-1.5 text-2xl font-serif font-bold text-slate-900">
                <Link href={enPostPath(p.slug)} className="hover:text-[#b7410e]">{p.title_en}</Link>
              </h2>
              {p.summary_en && <p className="mt-2 text-slate-600 leading-relaxed">{metaDescription(p.summary_en, 220)}</p>}
              <Link href={enPostPath(p.slug)} className="inline-block mt-3 text-sm font-bold text-[#b7410e] hover:underline">
                Read the article →
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </BlogShell>
  );
}
