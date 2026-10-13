import { listPosts } from "@/lib/articles";
import { ARTICLES_PATH, BLOG_DESCRIPTION, BLOG_TITLE, metaDescription, postUrl } from "@/lib/blogSeo";
import { SITE_URL } from "@/lib/site";

// RSS for the articles: feed readers and search engines learn about a new article when it is published
export const revalidate = 300;

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export async function GET() {
  const { posts } = await listPosts();
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
    <link>${SITE_URL}${ARTICLES_PATH}</link>
    <description>${esc(BLOG_DESCRIPTION)}</description>
    <language>sv-SE</language>
    <atom:link href="${SITE_URL}/artiklar/rss.xml" rel="self" type="application/rss+xml" />${items}
  </channel>
</rss>
`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, max-age=3600" } });
}
