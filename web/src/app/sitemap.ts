import type { MetadataRoute } from "next";
import { listPosts, listReports } from "@/lib/articles";
import { ARTICLES_PATH, EN_ARTICLES_PATH, enPostUrl, postUrl, sharePath } from "@/lib/blogSeo";
import { CONTACT_PATH, EN_CONTACT_PATH, NEWS_PATH, PUBLIC_SITE, SITE_URL } from "@/lib/site";
import { EN_REPORTS_PATH, EN_TERMS_PATH, enReportUrl, REPORTS_PATH, reportSharePath, reportUrl, TERMS_PATH } from "@/lib/report";

// The public pages, every published article and research report in Swedish and English (with hreflang pairs); refreshed every
// five minutes. The public website (NEXT_PUBLIC_SITE_MODE=public) has only the start page, the articles and the
// contact page, so the app's pages are left out there. The fixed pages carry no change date – only the articles
// know honestly when they changed.
export const revalidate = 300;

const PAGES: [string, MetadataRoute.Sitemap[number]["changeFrequency"], number][] = [
  ["/", "weekly", 1], [ARTICLES_PATH, "weekly", 0.9], [EN_ARTICLES_PATH, "weekly", 0.7],
  [REPORTS_PATH, "weekly", 0.9], [EN_REPORTS_PATH, "weekly", 0.8], [TERMS_PATH, "monthly", 0.6], [EN_TERMS_PATH, "monthly", 0.5],
  ["/karta", "monthly", 0.8], ["/inskrifter", "monthly", 0.8],
  ["/statistik", "monthly", 0.7], ["/luckor", "monthly", 0.7], ["/oversikt", "monthly", 0.6],
  ["/docs", "monthly", 0.5], ["/start", "monthly", 0.5], [NEWS_PATH, "weekly", 0.5], [CONTACT_PATH, "monthly", 0.6], [EN_CONTACT_PATH, "monthly", 0.4],
];
const PUBLIC_PAGES = new Set(["/", ARTICLES_PATH, EN_ARTICLES_PATH, REPORTS_PATH, EN_REPORTS_PATH, TERMS_PATH, EN_TERMS_PATH, NEWS_PATH, CONTACT_PATH, EN_CONTACT_PATH]);

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages = PAGES.filter(([path]) => !PUBLIC_SITE || PUBLIC_PAGES.has(path))
    .map(([path, changeFrequency, priority]) => ({ url: `${SITE_URL}${path}`, changeFrequency, priority }));
  try {
    const { posts } = await listPosts();
    const entries = posts.flatMap(p => {
      const changed = p.updatedAt ?? p.publishedAt;
      const lastModified = changed ? new Date(changed) : undefined;
      const languages = p.title_en ? { sv: postUrl(p.slug), en: enPostUrl(p.slug) } : undefined;
      const common = { lastModified, changeFrequency: "monthly" as const,
                       ...(languages ? { alternates: { languages } } : {}) };
      return [
        { url: postUrl(p.slug), priority: 0.8, images: [`${SITE_URL}${sharePath(p.slug)}`], ...common },
        ...(p.title_en ? [{ url: enPostUrl(p.slug), priority: 0.6, ...common }] : []),
      ];
    });
    // The research reports, with the highest priority after the start page: the English version is the one cited
    const { posts: reports } = await listReports();
    const reportEntries = reports.flatMap(p => {
      const changed = p.updatedAt ?? p.publishedAt;
      const lastModified = changed ? new Date(changed) : undefined;
      const languages = p.title_en ? { sv: reportUrl(p.slug), en: enReportUrl(p.slug) } : undefined;
      const common = { lastModified, changeFrequency: "monthly" as const, ...(languages ? { alternates: { languages } } : {}) };
      return [
        { url: reportUrl(p.slug), priority: 0.9, images: [`${SITE_URL}${reportSharePath(p.slug)}`], ...common },
        ...(p.title_en ? [{ url: enReportUrl(p.slug), priority: 0.9, ...common }] : []),
      ];
    });
    return [...pages, ...reportEntries, ...entries];
  } catch {
    return pages;
  }
}
