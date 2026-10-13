import { readdirSync } from "node:fs";
import { join } from "node:path";
import type { NextConfig } from "next";

// The public website (NEXT_PUBLIC_SITE_MODE=public) has only the start page and the articles: the app runs on the
// researcher's own computer and is downloaded from GitHub. There, every page of the app – the folders of src/app/(app) –
// leads to the start page.
const PUBLIC_SITE = process.env.NEXT_PUBLIC_SITE_MODE === "public";
const APP_PAGES = readdirSync(join(process.cwd(), "src", "app", "(app)"), { withFileTypes: true })
  .filter(d => d.isDirectory()).map(d => d.name);

const nextConfig: NextConfig = {
  async redirects() {
    return [
      // The articles were called a blog at /blogg before 2026-10-13; old links lead to the same article
      { source: "/blogg", destination: "/artiklar", permanent: true },
      { source: "/blogg/:path*", destination: "/artiklar/:path*", permanent: true },
      ...(PUBLIC_SITE ? APP_PAGES.flatMap(p => [
        { source: `/${p}`, destination: "/", permanent: false },
        { source: `/${p}/:path*`, destination: "/", permanent: false },
      ]) : []),
    ];
  },
};

export default nextConfig;
