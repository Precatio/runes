import type { Metadata } from "next";
import Link from "next/link";
import { notFound, permanentRedirect } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import { SwedishEditionLink } from "@/components/LanguageToggle";
import BlogBody, { postDate, type BlogPost } from "@/components/BlogBody";
import LabelChips from "@/components/LabelChips";
import { AuthorByline, AuthorCard } from "@/components/ArticleAuthor";
import ShareArticle from "@/components/ShareArticle";
import { getPost, listPosts, postSlugs } from "@/lib/articles";
import { isReport, enReportPath } from "@/lib/report";
import { featuredFirst } from "@/lib/featured";
import { authorOf } from "@/lib/site";
import { articleJsonLd, commonsSizes, enPostPath, EN_ARTICLES_PATH, postPath, keywords, languageAlternates, metaDescription, pictures, SHARE_SIZE, sharePath } from "@/lib/blogSeo";

// The English edition of a published article, rendered on the server so that search engines see English text and
// the hreflang pair ties it to the Swedish original. The content is the article's own English version from the
// build; the Swedish page remains the canonical original (x-default). The frame is the Swedish article's
// (components/BlogArticle.tsx) in English: the way back to the articles, the labels, the author and the card about the
// person behind Vitki.
export const revalidate = 60;
export const generateStaticParams = postSlugs;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post?.body_en) return { title: "Article not found", robots: { index: false, follow: true } };
  const description = metaDescription(post.summary_en || post.body_en);
  const path = enPostPath(post.slug);
  return {
    title: post.title_en || post.title,
    description,
    keywords: keywords(post),
    authors: [{ name: post.author || "Viktor Kvant" }],
    alternates: { canonical: path, languages: languageAlternates(post.slug) },
    openGraph: {
      type: "article", url: path, title: post.title_en || post.title, description, siteName: "Vitki", locale: "en_GB",
      publishedTime: post.publishedAt ?? undefined, modifiedTime: post.updatedAt ?? post.publishedAt ?? undefined,
      authors: [post.author || "Viktor Kvant"], section: "Articles", tags: keywords(post),
      images: [{ url: sharePath(post.slug), ...SHARE_SIZE, alt: post.title_en || post.title }],
    },
    twitter: { card: "summary_large_image", title: post.title_en || post.title, description, images: [sharePath(post.slug)] },
    robots: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
  };
}

function MoreInEnglish({ posts }: { posts: BlogPost[] }) {
  if (!posts.length) return null;
  return (
    <section className="max-w-3xl mx-auto px-6 pb-20" lang="en" aria-labelledby="more-articles">
      <div className="border-t border-slate-900/10 pt-10 flex items-baseline justify-between gap-4">
        <h2 id="more-articles" className="text-2xl font-serif font-bold text-slate-900">More articles</h2>
        <Link href={EN_ARTICLES_PATH} className="text-sm font-bold text-[#b7410e] hover:underline">All articles →</Link>
      </div>
      <ul className="mt-5 space-y-4">
        {posts.map(p => (
          <li key={p.slug}>
            <Link href={enPostPath(p.slug)} prefetch={false} className="font-bold text-[#b7410e] hover:underline">{p.title_en || p.title}</Link>
            {p.summary_en && <p className="text-sm text-slate-600 mt-0.5">{metaDescription(p.summary_en, 140)}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default async function EnglishPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post?.body_en) notFound();
  if (isReport(post)) permanentRedirect(enReportPath(post.slug));
  const more = featuredFirst((await listPosts()).posts.filter(p => p.slug !== post.slug && p.title_en)).slice(0, 3);
  const sizes = await commonsSizes(pictures(post.body_en).map(p => p.src));
  const author = authorOf(post.author);
  const name = post.author || author?.name;
  const title = post.title_en || post.title;
  return (
    <BlogShell lang="en">
      <article className="max-w-3xl mx-auto px-6 pt-16 pb-14" lang="en">
        <nav aria-label="Breadcrumb" className="flex items-center justify-between gap-4 text-sm">
          <Link href={EN_ARTICLES_PATH} prefetch={false} className="tap font-bold text-[#b7410e] hover:underline">← Articles</Link>
          <SwedishEditionLink href={postPath(post.slug)} className="tap text-[#b7410e] font-semibold hover:underline">
            Läs på svenska →
          </SwedishEditionLink>
        </nav>
        <div className="mt-8 text-sm text-slate-500">
          <time dateTime={post.publishedAt ?? post.month}>{postDate(post, "en")}</time>
        </div>
        <LabelChips labels={post.labels} lang="en" linked className="mt-3" />
        <h1 className="mt-2 text-4xl md:text-5xl font-serif font-bold tracking-tight leading-tight text-slate-900">{title}</h1>
        {post.summary_en && <p className="mt-5 text-xl text-slate-600 leading-relaxed">{post.summary_en}</p>}
        {name && <AuthorByline name={name} author={author} lang="en" />}
        <div className="mt-10">
          <BlogBody text={post.body_en} sizes={sizes} lang="en" />
        </div>
        <ShareArticle title={title} lang="en" />
        {author && <AuthorCard author={author} lang="en" />}
      </article>
      <MoreInEnglish posts={more} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{
        __html: JSON.stringify(articleJsonLd(post, "en")).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
