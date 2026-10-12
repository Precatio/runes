// The IndexNow key (INDEXNOW_KEY on the server), which proves to the search engines that the pings about new blog posts
// come from the site itself (api/routers/blog.py). Without a key there is nothing here and no pings are sent.
export function GET() {
  const key = process.env.INDEXNOW_KEY;
  return key ? new Response(key, { headers: { "Content-Type": "text/plain; charset=utf-8" } }) : new Response("Not found", { status: 404 });
}
