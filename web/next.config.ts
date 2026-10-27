import type { NextConfig } from "next";

// The public website (NEXT_PUBLIC_SITE_MODE=public) has only the start page and the articles: the app runs on the
// researcher's own computer and is downloaded from GitHub. It is built as static files for GitHub Pages
// (.github/workflows/site.yml), which leaves out the app's pages; every address ends with a slash (/artiklar/…/), so that
// a page and the folder of its sub-pages never collide.
const PUBLIC_SITE = process.env.NEXT_PUBLIC_SITE_MODE === "public";

// NEXT_DIST_DIR builds beside the running app (e.g. a test build without the analysis engine) instead of over it
const distDir = process.env.NEXT_DIST_DIR || undefined;

const nextConfig: NextConfig = PUBLIC_SITE
  ? { output: "export", trailingSlash: true, images: { unoptimized: true } }
  : {
      ...(distDir ? { distDir } : {}),
      async redirects() {
        return [
          // The articles were called a blog at /blogg before 2026-10-13; old links lead to the same article
          { source: "/blogg", destination: "/artiklar", permanent: true },
          { source: "/blogg/:path*", destination: "/artiklar/:path*", permanent: true },
        ];
      },
    };

export default nextConfig;
