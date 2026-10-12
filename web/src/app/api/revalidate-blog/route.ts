import { revalidateTag } from "next/cache";
import { API_URL } from "@/lib/api";

// Refreshes the public blog at once after the founder saves, publishes, unpublishes or deletes a post (BlogAdmin): the
// list, the posts, the share images, the sitemap and the RSS feed are cached with the tag "blog". Only for an admin –
// the analysis engine checks the Firebase token (GET /api/me).
export async function POST(req: Request) {
  const auth = req.headers.get("authorization");
  if (!auth) return Response.json({ detail: "Logga in." }, { status: 401 });
  try {
    const me = await fetch(`${API_URL}/api/me`, { headers: { Authorization: auth }, cache: "no-store" });
    if (!me.ok || !(await me.json()).admin) return Response.json({ detail: "Bara för grundaren." }, { status: 403 });
  } catch {
    return Response.json({ detail: "Analysmotorn svarar inte." }, { status: 503 });
  }
  // Expired at once: the next visitor gets the new list, not the old one while it is refreshed in the background
  revalidateTag("blog", { expire: 0 });
  return Response.json({ revalidated: true });
}
