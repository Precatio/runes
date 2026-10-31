import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import BlogArticle from "@/components/BlogArticle";
import MoreArticles from "@/components/MoreArticles";
import type { BlogPost } from "@/components/BlogBody";
import { getPost, listPosts, postSlugs } from "@/lib/articles";
import { isReport, reportPath } from "@/lib/report";
import { featuredFirst } from "@/lib/featured";
import { articleJsonLd, commonsSizes, keywords, metaDescription, pictures, postPath, SHARE_SIZE, sharePath, withImageSizes } from "@/lib/blogSeo";
import { enPostPath, languageAlternates } from "@/lib/blogSeo";

// A published post, rendered on the server with its metadata and structured data (lib/blogSeo.ts), so that every new
// post is described for search engines and social media as soon as it is published. Fetched again at most every five
// minutes, so that an edit shows without a new build.
export const revalidate = 60;

// Every published article is built ahead; on the public website there are no others
export const generateStaticParams = postSlugs;

// The English fields stay out of what the Swedish page sends to the browser: a reader who chooses English is taken to
// the English edition (/en/artiklar/…, components/LanguageContext.tsx) instead of having the text swapped in place
const swedishOnly = ({ title_en: _t, summary_en: _s, body_en: _b, ...p }: BlogPost): BlogPost => p; // eslint-disable-line @typescript-eslint/no-unused-vars
// A card under "Fler artiklar" keeps its English title: a reader who has chosen English on an article that is only in
// Swedish (the frame translated in place) sees the cards in English, and each links to its English edition when the
// article has one (readerPath, by title_en), as in the list. No texts and no English summary: the cards show neither
const moreCard = ({ body: _b, body_en: _e, summary_en: _s, ...p }: BlogPost): BlogPost => p; // eslint-disable-line @typescript-eslint/no-unused-vars

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
    alternates: { canonical: path, languages: post.body_en ? languageAlternates(post.slug) : undefined, types: { "application/rss+xml": "/artiklar/rss.xml" } },
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
  // A research report has its own section and paper layout (app/rapporter); an old address under /artiklar leads there
  if (isReport(post)) permanentRedirect(reportPath(post.slug));
  // three other articles: the article of the week first, then the newest
  const more = (await withImageSizes(featuredFirst((await listPosts()).posts.filter(p => p.slug !== post.slug)).slice(0, 3))).map(moreCard);
  // The sizes of its Commons photos
  const sizes = await commonsSizes(pictures(post.body ?? "").map(p => p.src));
  const english = post.body_en ? enPostPath(post.slug) : null;
  return (
    <BlogShell>
      {english && (
        <div className="max-w-3xl mx-auto px-6 pt-8 -mb-10 text-right">
          <a href={english} hrefLang="en" className="tap text-sm text-[#b7410e] font-semibold hover:underline">In English →</a>
        </div>
      )}
      <BlogArticle post={swedishOnly(post)} sizes={sizes} english={english} />
      <MoreArticles posts={more} />
      { }
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd(post)).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
