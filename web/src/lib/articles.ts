import type { BlogPost } from "@/components/BlogBody";
import { API_URL } from "@/lib/api";
import { PUBLIC_SITE } from "@/lib/site";
import { pictures } from "@/lib/blogSeo";
import { isReport } from "@/lib/report";
import snapshot from "../../content/articles.json";

// The articles for the pages that show them. In the local app they come from the analysis engine (the articles in
// Firestore, fetched again every minute). The public website has no analysis engine: it is built from
// content/articles.json – the articles that have gone live, exported with their figures by the local app
// (src/site_export.py) – by GitHub (.github/workflows/site.yml). When the analysis engine cannot be reached (it is down,
// or the app is built without it, as in the browser tests in CI), the local app falls back on the same export.
interface Snapshot { exported_at: string | null; posts: BlogPost[] }

const isLive = (p: BlogPost, now = Date.now()) => !p.publishedAt || Date.parse(p.publishedAt) <= now;
const exported = () => (snapshot as Snapshot).posts.filter(p => isLive(p));
// The list carries no article texts, as from the analysis engine, but the first photo for the thumbnail
const listed = ({ body, body_en: _e, ...p }: BlogPost) => { // eslint-disable-line @typescript-eslint/no-unused-vars
  const photo = pictures(body ?? "").find(x => /wikimedia\.org/.test(x.src));
  return { ...p, image: photo?.src ?? null, image_alt: photo?.alt || null } as BlogPost;
};

/** Everything published (articles and research reports), newest first; failed when neither the analysis engine nor
 *  the export has any. */
async function listAll(): Promise<{ posts: BlogPost[]; failed: boolean }> {
  const fromExport = () => { const posts = exported().map(listed); return { posts, failed: posts.length === 0 }; };
  if (PUBLIC_SITE) return { posts: exported().map(listed), failed: false };
  try {
    const r = await fetch(`${API_URL}/api/blog/posts`, { next: { revalidate: 60, tags: ["blog"] } });
    return r.ok ? { posts: (await r.json()).posts, failed: false } : fromExport();
  } catch {
    return fromExport();
  }
}

/** The published articles, newest first – without the research reports, which have their own section (/forskningsrapporter). */
export async function listPosts(): Promise<{ posts: BlogPost[]; failed: boolean }> {
  const all = await listAll();
  return { posts: all.posts.filter(p => !isReport(p)), failed: all.failed };
}

/** The published research reports (label "Rapport", lib/report.ts), newest first. */
export async function listReports(): Promise<{ posts: BlogPost[]; failed: boolean }> {
  const all = await listAll();
  return { posts: all.posts.filter(isReport), failed: all.failed };
}

/** One published article or report with its text, or null. */
export async function getPost(slug: string): Promise<BlogPost | null> {
  if (PUBLIC_SITE) return exported().find(p => p.slug === slug) ?? null;
  const fromExport = () => exported().find(p => p.slug === slug) ?? null;
  try {
    const r = await fetch(`${API_URL}/api/blog/posts/${encodeURIComponent(slug)}`, { next: { revalidate: 60, tags: ["blog"] } });
    if (r.ok) return (await r.json()).post;
    return r.status === 404 ? null : fromExport(); // not found is an answer; an engine error falls back on the export
  } catch {
    return fromExport();
  }
}

/** The articles' addresses, for the pages built ahead (the public website is built in full beforehand). */
export async function postSlugs(): Promise<{ slug: string }[]> {
  return (await listPosts()).posts.map(p => ({ slug: p.slug }));
}

/** The research reports' addresses, likewise. The static website (output: export) must build at least one path for
 *  each dynamic route; before the first report is published it gets a placeholder, which renders the not-found page. */
export async function reportSlugs(): Promise<{ slug: string }[]> {
  const slugs = (await listReports()).posts.map(p => ({ slug: p.slug }));
  return slugs.length || !PUBLIC_SITE ? slugs : [{ slug: "_" }];
}
