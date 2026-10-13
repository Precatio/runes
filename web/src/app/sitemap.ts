import type { MetadataRoute } from "next";
import { API_URL } from "@/lib/api";
import { PUBLIC_SITE, SITE_URL } from "@/lib/site";

// The public pages, and every published article (GET /api/blog/posts); refreshed every five minutes. The public website
// (NEXT_PUBLIC_SITE_MODE=public) has only the start page and the articles, so the app's pages are left out there
export const revalidate = 300;

const PAGES: [string, MetadataRoute.Sitemap[number]["changeFrequency"], number][] = [
  ["/", "weekly", 1], ["/artiklar", "weekly", 0.9], ["/karta", "monthly", 0.8], ["/inskrifter", "monthly", 0.8],
  ["/stilgrupper", "monthly", 0.6], ["/statistik", "monthly", 0.7], ["/luckor", "monthly", 0.7], ["/oversikt", "monthly", 0.6],
  ["/docs", "monthly", 0.5], ["/start", "monthly", 0.5],
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const pages = PAGES.filter(([path]) => !PUBLIC_SITE || path === "/" || path === "/artiklar").map(([path, changeFrequency, priority]) => ({ url: `${SITE_URL}${path}`, lastModified: now, changeFrequency, priority }));
  try {
    const r = await fetch(`${API_URL}/api/blog/posts`, { next: { revalidate: 300, tags: ["blog"] } });
    const posts: { slug: string; publishedAt?: string | null; updatedAt?: string | null }[] = r.ok ? (await r.json()).posts : [];
    return [...pages, ...posts.map(p => {
      const changed = p.updatedAt ?? p.publishedAt;
      return { url: `${SITE_URL}/artiklar/${encodeURIComponent(p.slug)}`, lastModified: changed ? new Date(changed) : now,
               changeFrequency: "monthly" as const, priority: 0.8,
               images: [`${SITE_URL}/artiklar/${encodeURIComponent(p.slug)}/opengraph-image`] };
    })];
  } catch {
    return pages;
  }
}
