import type { Metadata } from "next";
import { notFound } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import ReportPaper from "@/components/ReportPaper";
import { getPost, reportSlugs } from "@/lib/articles";
import { commonsSizes, keywords, metaDescription, pictures, SHARE_SIZE } from "@/lib/blogSeo";
import { enReportPath, isReport, reportAlternates, reportJsonLd, reportParts, reportPath, reportSharePath, scholarMeta } from "@/lib/report";

// The English version of a research report as a paper; the canonical version for citation
export const revalidate = 60;
export const generateStaticParams = reportSlugs;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post?.body_en || !isReport(post)) return { title: "Report not found", robots: { index: false, follow: true } };
  const parts = reportParts(post.body_en);
  const title = post.title_en || post.title;
  const description = metaDescription(post.summary_en || parts.abstract || "");
  const path = enReportPath(post.slug);
  return {
    title: `${title} – research report`,
    description,
    keywords: [...(parts.header?.keywords ?? []), "research report", "research findings", ...keywords(post)],
    authors: [{ name: post.author || "Viktor Kvant" }],
    alternates: { canonical: path, languages: reportAlternates(post.slug) },
    openGraph: {
      type: "article", url: path, title, description, siteName: "Vitki", locale: "en_GB",
      publishedTime: post.publishedAt ?? undefined, modifiedTime: post.updatedAt ?? post.publishedAt ?? undefined,
      authors: [post.author || "Viktor Kvant"], section: "Research reports", tags: parts.header?.keywords,
      images: [{ url: reportSharePath(post.slug), ...SHARE_SIZE, alt: title }],
    },
    twitter: { card: "summary_large_image", title, description, images: [reportSharePath(post.slug)] },
    robots: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
    other: scholarMeta(post, "en"),
  };
}

export default async function EnglishReportPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post?.body_en || !isReport(post)) notFound();
  const sizes = await commonsSizes(pictures(post.body_en).map(p => p.src));
  return (
    <BlogShell lang="en">
      <ReportPaper post={post} lang="en" sizes={sizes} otherHref={reportPath(post.slug)} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(reportJsonLd(post, "en")).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
