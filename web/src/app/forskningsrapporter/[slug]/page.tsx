import type { Metadata } from "next";
import { notFound } from "next/navigation";
import BlogShell from "@/components/BlogShell";
import ReportPaper from "@/components/ReportPaper";
import { getPost, reportSlugs } from "@/lib/articles";
import { commonsSizes, keywords, metaDescription, pictures, SHARE_SIZE } from "@/lib/blogSeo";
import { enReportPath, isReport, reportAlternates, reportJsonLd, reportParts, reportPath, reportSharePath, scholarMeta } from "@/lib/report";

// A research report as a paper (components/ReportPaper.tsx), rendered on the server with the metadata search engines
// read for scholarly work: the citation_… tags (Google Scholar), schema.org ScholarlyArticle/Report and hreflang to the
// English version, which is the canonical one for citation (the Swedish page stays the default for the site).
export const revalidate = 60;
export const generateStaticParams = reportSlugs;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post || !isReport(post)) return { title: "Rapporten finns inte", robots: { index: false, follow: true } };
  const parts = reportParts(post.body ?? "");
  const description = metaDescription(post.summary || parts.abstract || "");
  const path = reportPath(post.slug);
  return {
    title: `${post.title} – forskningsrapport`,
    description,
    keywords: [...(parts.header?.keywords ?? []), "forskningsrapport", "forskningsresultat", ...keywords(post)],
    authors: [{ name: post.author || "Viktor Kvant" }],
    alternates: { canonical: path, languages: post.body_en ? reportAlternates(post.slug) : undefined },
    openGraph: {
      type: "article", url: path, title: post.title, description, siteName: "Vitki", locale: "sv_SE",
      publishedTime: post.publishedAt ?? undefined, modifiedTime: post.updatedAt ?? post.publishedAt ?? undefined,
      authors: [post.author || "Viktor Kvant"], section: "Forskningsrapporter", tags: parts.header?.keywords,
      images: [{ url: reportSharePath(post.slug), ...SHARE_SIZE, alt: post.title }],
    },
    twitter: { card: "summary_large_image", title: post.title, description, images: [reportSharePath(post.slug)] },
    robots: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
    other: scholarMeta(post, "sv"),
  };
}

export default async function ReportPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  if (!post || !isReport(post)) notFound();
  const sizes = await commonsSizes(pictures(post.body ?? "").map(p => p.src));
  return (
    <BlogShell>
      <ReportPaper post={post} lang="sv" sizes={sizes} otherHref={post.body_en ? enReportPath(post.slug) : null} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(reportJsonLd(post, "sv")).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
