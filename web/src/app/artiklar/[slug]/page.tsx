import type { Metadata } from "next";
import { notFound } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import BlogArticle from "@/components/BlogArticle";
import MoreArticles from "@/components/MoreArticles";
import { getPost, listPosts, postSlugs } from "@/lib/articles";
import { featuredFirst } from "@/lib/featured";
import { articleJsonLd, commonsSizes, keywords, metaDescription, pictures, postPath, SHARE_SIZE, sharePath, withImageSizes } from "@/lib/blogSeo";
import { enPostPath, languageAlternates } from "@/lib/blogSeo";

// A published post, rendered on the server with its metadata and structured data (lib/blogSeo.ts), so that every new
// post is described for search engines and social media as soon as it is published. Fetched again at most every five
// minutes, so that an edit shows without a new build.
export const revalidate = 60;

// Every published article is built ahead; on the public website there are no others
export const generateStaticParams = postSlugs;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post) return { title: "Artikeln finns inte", robots: { index: false, follow: true } };
  const description = metaDescription(post.summary || post.body || "");
  const path = postPath(post.slug);
  const photo = pictures(post.body ?? "")[0];
  return {
    title: post.title,
    description,
    keywords: keywords(post),
    authors: [{ name: post.author || "Viktor Kvant" }],
    alternates: { canonical: path, languages: languageAlternates(post.slug), types: { "application/rss+xml": "/artiklar/rss.xml" } },
    openGraph: {
      type: "article", url: path, title: post.title, description, siteName: "Vitki", locale: "sv_SE",
      publishedTime: post.publishedAt ?? undefined, modifiedTime: post.updatedAt ?? post.publishedAt ?? undefined,
      authors: [post.author || "Viktor Kvant"], section: "Artiklar", tags: keywords(post),
      images: [{ url: sharePath(post.slug), ...SHARE_SIZE, alt: post.title }],
    },
    twitter: { card: "summary_large_image", title: post.title, description, images: [sharePath(post.slug)] },
    robots: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
    other: photo ? { "article:image": photo.src } : undefined,
  };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post) notFound();
  // three other articles: the article of the week first, then the newest
  const more = await withImageSizes(featuredFirst((await listPosts()).posts.filter(p => p.slug !== post.slug)).slice(0, 3));
  // The sizes of its Commons photos, in both languages (the reader can switch)
  const sizes = await commonsSizes(pictures(`${post.body ?? ""}\n${post.body_en ?? ""}`).map(p => p.src));
  return (
    <BlogShell>
      <div className="max-w-3xl mx-auto px-6 pt-8 -mb-10 text-right">
        <a href={enPostPath(post.slug)} hrefLang="en" className="text-sm text-[#b7410e] font-semibold hover:underline">In English →</a>
      </div>
      <BlogArticle post={post} sizes={sizes} />
      <MoreArticles posts={more} />
      { }
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd(post)).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
