import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The articles were called a blog at /blogg before 2026-10-13; old links lead to the same article
  async redirects() {
    return [
      { source: "/blogg", destination: "/artiklar", permanent: true },
      { source: "/blogg/:path*", destination: "/artiklar/:path*", permanent: true },
    ];
  },
};

export default nextConfig;
