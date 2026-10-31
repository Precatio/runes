import Link from "next/link";
import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import { SwedishEditionLink } from "@/components/LanguageToggle";
import EnglishArticleList from "@/components/EnglishArticleList";
import ContentVote from "@/components/ContentVote";
import { listPosts } from "@/lib/articles";
import { EN_REPORTS_PATH } from "@/lib/report";
import { featuredFirst } from "@/lib/featured";
import { ARTICLES_PATH, BLOG_DESCRIPTION_EN, BLOG_TITLE_EN, EN_ARTICLES_PATH, languageAlternates } from "@/lib/blogSeo";

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
    <BlogShell lang="en">
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24" lang="en">
        <div className="flex items-center justify-between gap-4">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Articles</div>
          <SwedishEditionLink href={ARTICLES_PATH} className="tap text-sm text-[#b7410e] font-semibold hover:underline">Läs på svenska →</SwedishEditionLink>
        </div>
        <h1 className="mt-3 text-4xl md:text-5xl font-serif font-bold tracking-tight">Hidden patterns of the runestones</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          What we see when all of Sweden&apos;s Viking-age runestones are read at once – what it may mean, and how it
          can be tested. The figures come from Vitki&apos;s open analyses and are explained in the text.
        </p>
        <p className="mt-3 text-sm text-slate-500">
          The findings that have passed every check are also written up in scholarly form, with version and citation, under{" "}
          <Link href={EN_REPORTS_PATH} prefetch={false} className="font-semibold text-[#b7410e] hover:underline">Research reports</Link>.
        </p>
        <EnglishArticleList posts={withEn} />
        <ContentVote />
      </section>
    </BlogShell>
  );
}
