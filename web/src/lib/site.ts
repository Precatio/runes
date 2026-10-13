// The site's public address and name, for metadata, the sitemap and structured data (override with NEXT_PUBLIC_SITE_URL)
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://vitkirunor.se").replace(/\/$/, "");
export const SITE_NAME = "Vitki";
export const SITE_DESCRIPTION =
  "Utforska Sveriges runstenar: mönsterkarta, ristare, stilgrupper, Samnordisk runtextdatabas, 3D-analys av huggspår " +
  "och statistik i R. En öppen och fri forskningsplattform för runologi och runinskrifter.";
export const KEYWORDS = [
  "runstenar", "runsten", "runinskrifter", "runor", "runologi", "runforskning", "vikingatid", "Rundata",
  "Samnordisk runtextdatabas", "runristare", "Öpir", "stilgrupper", "Gräslund", "runstenskarta", "kristnandet",
  "fornlämningar", "3D-skanning", "huggspår", "runestones", "runic inscriptions", "Viking Age", "runology",
];

// The public website has only the start page and the articles; the app runs on the researcher's own computer and is
// downloaded from GitHub. NEXT_PUBLIC_SITE_MODE=public builds that website: the app's pages lead to the start page
// (next.config.ts) and are left out of the sitemap.
export const PUBLIC_SITE = process.env.NEXT_PUBLIC_SITE_MODE === "public";
export const GITHUB_URL = "https://github.com/Precatio/runes";
export const DOWNLOAD_URL = `${GITHUB_URL}#systemkrav--installation`;
export const METHODS_URL = `${GITHUB_URL}/blob/main/METHODS.md`;
export const DOCS_URL = `${GITHUB_URL}#readme`;
// While the app runs locally (next dev), its own pages are a click away; never on the public website
export const SHOW_LOCAL_APP = process.env.NODE_ENV === "development" && !PUBLIC_SITE;

/** The paths that exist on the public website: the start page, the articles and their figures. */
export const isPublicPath = (href: string) => /^\/(?:$|[#?]|artiklar(?:[/?#]|$)|api\/blog\/figures\/)/.test(href);
