import type { Metadata } from "next";
import { notFound } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import BlogArticle from "@/components/BlogArticle";
import { getPost, postSlugs } from "@/lib/articles";
import { articleJsonLd, keywords, metaDescription, pictures, postPath, SHARE_SIZE, sharePath } from "@/lib/blogSeo";

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
    alternates: { canonical: path, types: { "application/rss+xml": "/artiklar/rss.xml" } },
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
  return (
    <BlogShell>
      <BlogArticle post={post} />
      { }
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd(post)).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
