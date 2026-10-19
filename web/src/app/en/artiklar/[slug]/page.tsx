import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import BlogBody, { postDate, type BlogPost } from "@/components/BlogBody";
import ShareArticle from "@/components/ShareArticle";
import { getPost, listPosts, postSlugs } from "@/lib/articles";
import { featuredFirst } from "@/lib/featured";
import { articleJsonLd, enPostPath, keywords, languageAlternates, metaDescription, SHARE_SIZE, sharePath } from "@/lib/blogSeo";

// The English edition of a published article, rendered on the server so that search engines see English text and
// the hreflang pair ties it to the Swedish original. The content is the article's own English version from the
// build; the Swedish page remains the canonical original (x-default).
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
    <section className="max-w-3xl mx-auto px-6 pb-20" lang="en">
      <h2 className="text-2xl font-serif font-bold text-slate-900">More articles</h2>
      <ul className="mt-5 space-y-4">
        {posts.map(p => (
          <li key={p.slug}>
            <Link href={enPostPath(p.slug)} className="font-bold text-[#b7410e] hover:underline">{p.title_en || p.title}</Link>
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
  const more = featuredFirst((await listPosts()).posts.filter(p => p.slug !== post.slug && p.title_en)).slice(0, 3);
  return (
    <BlogShell>
      <article className="max-w-3xl mx-auto px-6 pt-16 pb-14" lang="en">
        <div className="flex items-center justify-between gap-4 text-sm">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Articles</div>
          <Link href={`/artiklar/${encodeURIComponent(post.slug)}/`} className="text-[#b7410e] font-semibold hover:underline" hrefLang="sv">
            Läs på svenska →
          </Link>
        </div>
        <h1 className="mt-3 text-4xl md:text-5xl font-serif font-bold tracking-tight text-slate-900">{post.title_en || post.title}</h1>
        <p className="mt-4 text-slate-500 text-sm">
          <time dateTime={post.publishedAt ?? post.month}>{postDate(post, "en")}</time>
          {post.author && <> · {post.author}</>}
        </p>
        {post.summary_en && <p className="mt-6 text-lg text-slate-600 leading-relaxed">{post.summary_en}</p>}
        <div className="mt-10">
          <BlogBody text={post.body_en} />
        </div>
        <ShareArticle title={post.title_en || post.title} lang="en" />
      </article>
      <MoreInEnglish posts={more} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{
        __html: JSON.stringify(articleJsonLd(post, "en")).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
