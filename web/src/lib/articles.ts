import type { BlogPost } from "@/components/BlogBody";
import { API_URL } from "@/lib/api";
import { PUBLIC_SITE } from "@/lib/site";
import { pictures } from "@/lib/blogSeo";
import snapshot from "../../content/articles.json";

// The articles for the pages that show them. In the local app they come from the analysis engine (the articles in
// Firestore, fetched again every minute). The public website has no analysis engine: it is built from
// content/articles.json – the articles that have gone live, exported with their figures by the local app
// (src/site_export.py) – by GitHub (.github/workflows/site.yml).
interface Snapshot { exported_at: string | null; posts: BlogPost[] }

const isLive = (p: BlogPost, now = Date.now()) => !p.publishedAt || Date.parse(p.publishedAt) <= now;
const exported = () => (snapshot as Snapshot).posts.filter(p => isLive(p));
// The list carries no article texts, as from the analysis engine, but the first photo for the thumbnail
const listed = ({ body, body_en: _e, ...p }: BlogPost) => // eslint-disable-line @typescript-eslint/no-unused-vars
  ({ ...p, image: pictures(body ?? "").find(x => /wikimedia\.org/.test(x.src))?.src ?? null }) as BlogPost;

/** The published articles, newest first; failed when the analysis engine could not be reached. */
export async function listPosts(): Promise<{ posts: BlogPost[]; failed: boolean }> {
  if (PUBLIC_SITE) return { posts: exported().map(listed), failed: false };
  try {
    const r = await fetch(`${API_URL}/api/blog/posts`, { next: { revalidate: 60, tags: ["blog"] } });
    return r.ok ? { posts: (await r.json()).posts, failed: false } : { posts: [], failed: true };
  } catch {
    return { posts: [], failed: true };
  }
}

/** One published article with its text, or null. */
export async function getPost(slug: string): Promise<BlogPost | null> {
  if (PUBLIC_SITE) return exported().find(p => p.slug === slug) ?? null;
  try {
    const r = await fetch(`${API_URL}/api/blog/posts/${encodeURIComponent(slug)}`, { next: { revalidate: 60, tags: ["blog"] } });
    return r.ok ? (await r.json()).post : null;
  } catch {
    return null;
  }
}

/** The articles' addresses, for the pages built ahead (the public website is built in full beforehand). */
export async function postSlugs(): Promise<{ slug: string }[]> {
  return (await listPosts()).posts.map(p => ({ slug: p.slug }));
}
