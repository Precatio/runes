import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

// Search engines may read the public pages; personal and administrative pages are left out
export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/admin", "/account", "/api/"] },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
