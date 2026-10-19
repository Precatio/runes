// The site's public address and name, for metadata, the sitemap and structured data (override with NEXT_PUBLIC_SITE_URL).
// The description is what a search result shows, so it is kept within about 155 characters.
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://vitkirunor.se").replace(/\/$/, "");
export const SITE_NAME = "Vitki";
export const SITE_DESCRIPTION =
  "Utforska Sveriges runstenar: runinskrifter, ristare, mönsterkarta, 3D-mätning av huggspår och statistik i R. " +
  "Vitki är en öppen och fri forskningsplattform.";
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

/** The paths that exist on the public website: the start page, the articles and their figures, and the contact page. */
export const isPublicPath = (href: string) => /^\/(?:$|[#?]|artiklar(?:[/?#]|$)|kontakt(?:[/?#]|$)|api\/blog\/figures\/)/.test(href);
export const CONTACT_PATH = PUBLIC_SITE ? "/kontakt/" : "/kontakt";

// The contact form's receiver. The website is static, so FormSubmit (no account) emails the message on. The form is
// activated, and FormSubmit's random alias stands in for the founder's email address, so the address is not in the page.
export const CONTACT_ENDPOINT = process.env.NEXT_PUBLIC_CONTACT_ENDPOINT || "https://formsubmit.co/ajax/dd84130aea1d4ba97d568c540422d13e";
export const CONTACT_SERVICE_URL = "https://formsubmit.co/";

// The articles' authors: the byline links to the author's page, and search engines get the same link (schema.org)
export interface Author { name: string; url: string; role: string; role_en: string; bio: string; bio_en: string }
export const AUTHORS: Record<string, Author> = {
  "Viktor Kvant": {
    name: "Viktor Kvant",
    url: "https://www.linkedin.com/in/viktor-kvant-555180108/",
    role: "Digital analytiker och grundare av Vitki",
    role_en: "Digital analyst and founder of Vitki",
    bio: "Viktor Kvant arbetar till vardags som digital analytiker. Han grundade Vitki för att pröva samma analytiska metoder på runstenarna.",
    bio_en: "Viktor Kvant works as a digital analyst. He founded Vitki to try the same analytical methods on the runestones.",
  },
};
export const authorOf = (name?: string | null): Author | null => (name ? AUTHORS[name] ?? null : AUTHORS["Viktor Kvant"]);

// The Firebase project that the public website's vote and visitor counts are written to, through Firestore's REST
// interface (no SDK, no key: the rules decide what may be written). Set when the site is built; without it neither is used.
export const SITE_PROJECT = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "";
export const siteCollection = (name: string) =>
  `https://firestore.googleapis.com/v1/projects/${SITE_PROJECT}/databases/vitki/documents/${name}`;

// Opening the website once with ?inte-rakna leaves that browser out of the visitor statistics (the founder's own visits)
export const STATS_OFF_KEY = "vitki-stats-off";
export const STATS_OFF_URL = `${SITE_URL}/?inte-rakna`;
