import type { BlogPost } from "@/components/BlogBody";
import { API_URL } from "@/lib/api";
import { BLOG_DESCRIPTION, BLOG_TITLE, metaDescription, postUrl } from "@/lib/blogSeo";
import { SITE_URL } from "@/lib/site";

// RSS for the blog: feed readers and search engines learn about a new post when it is published
export const revalidate = 3600;

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export async function GET() {
  let posts: BlogPost[] = [];
  try {
    const r = await fetch(`${API_URL}/api/blog/posts`, { next: { revalidate: 3600, tags: ["blog"] } });
    if (r.ok) posts = (await r.json()).posts;
  } catch { /* an empty feed */ }
  const items = posts.map(p => `
    <item>
      <title>${esc(p.title)}</title>
      <link>${postUrl(p.slug)}</link>
      <guid isPermaLink="true">${postUrl(p.slug)}</guid>
      ${p.publishedAt ? `<pubDate>${new Date(p.publishedAt).toUTCString()}</pubDate>` : ""}
      <description>${esc(metaDescription(p.summary || "", 400))}</description>
      ${p.author ? `<dc:creator>${esc(p.author)}</dc:creator>` : ""}
    </item>`).join("");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>${esc(BLOG_TITLE)}</title>
    <link>${SITE_URL}/blogg</link>
    <description>${esc(BLOG_DESCRIPTION)}</description>
    <language>sv-SE</language>
    <atom:link href="${SITE_URL}/blogg/rss.xml" rel="self" type="application/rss+xml" />${items}
  </channel>
</rss>
`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, max-age=3600" } });
}
