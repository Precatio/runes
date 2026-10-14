import type { BlogPost } from "@/components/BlogBody";

/** The article of the month ("Månadens artikel") first, then the others in the order they came (newest first). */
export function featuredFirst<T extends Pick<BlogPost, "featured">>(posts: T[]): T[] {
  const top = posts.find(p => p.featured);
  return top ? [top, ...posts.filter(p => p !== top)] : posts;
}
