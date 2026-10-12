import type { MetadataRoute } from "next";
import { API_URL } from "@/lib/api";
import { SITE_URL } from "@/lib/site";

// The public pages, and every published blog post (GET /api/blog/posts); refreshed once an hour
export const revalidate = 3600;

const PAGES: [string, MetadataRoute.Sitemap[number]["changeFrequency"], number][] = [
  ["/", "weekly", 1], ["/blogg", "weekly", 0.9], ["/karta", "monthly", 0.8], ["/inskrifter", "monthly", 0.8],
  ["/stilgrupper", "monthly", 0.6], ["/statistik", "monthly", 0.7], ["/luckor", "monthly", 0.7], ["/oversikt", "monthly", 0.6],
  ["/docs", "monthly", 0.5], ["/start", "monthly", 0.5],
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const pages = PAGES.map(([path, changeFrequency, priority]) => ({ url: `${SITE_URL}${path}`, lastModified: now, changeFrequency, priority }));
  try {
    const r = await fetch(`${API_URL}/api/blog/posts`, { next: { revalidate: 3600 } });
    const posts: { slug: string; publishedAt?: string | null; updatedAt?: string | null }[] = r.ok ? (await r.json()).posts : [];
    return [...pages, ...posts.map(p => {
      const changed = p.updatedAt ?? p.publishedAt;
      return { url: `${SITE_URL}/blogg/${encodeURIComponent(p.slug)}`, lastModified: changed ? new Date(changed) : now,
               changeFrequency: "monthly" as const, priority: 0.8,
               images: [`${SITE_URL}/blogg/${encodeURIComponent(p.slug)}/opengraph-image`] };
    })];
  } catch {
    return pages;
  }
}
