import type { BlogPost } from "@/components/BlogBody";

export type Order = "senaste" | "mest-lasta";

/** The article of the month ("Månadens artikel") first, then the others in the order they came (newest first). */
export function featuredFirst<T extends Pick<BlogPost, "featured">>(posts: T[]): T[] {
  const top = posts.find(p => p.featured);
  return top ? [top, ...posts.filter(p => p !== top)] : posts;
}

/** Most read first (page views exported with the articles), equal counts newest first; the article of the month gets no
 * special place here. */
export function byViews<T extends Pick<BlogPost, "views" | "publishedAt" | "month">>(posts: T[]): T[] {
  return [...posts].sort((a, b) => (b.views ?? 0) - (a.views ?? 0) ||
    Date.parse(b.publishedAt ?? b.month ?? "") - Date.parse(a.publishedAt ?? a.month ?? ""));
}

/** The sort can be offered once the website has counted something. */
export const hasViews = (posts: Pick<BlogPost, "views">[]) => posts.some(p => (p.views ?? 0) > 0);

/** The posts in the chosen order. */
export function inOrder<T extends Pick<BlogPost, "views" | "publishedAt" | "month" | "featured">>(posts: T[], order: Order): T[] {
  return order === "mest-lasta" ? byViews(posts) : featuredFirst(posts);
}
