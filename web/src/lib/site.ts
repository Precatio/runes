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
// Vitki on Bluesky: the share button on the articles names the account, and the footer and contact page link to it
export const BLUESKY_HANDLE = "vitkirunor.bsky.social";
export const BLUESKY_URL = `https://bsky.app/profile/${BLUESKY_HANDLE}`;
export const DOWNLOAD_URL = `${GITHUB_URL}#systemkrav--installation`;
export const METHODS_URL = `${GITHUB_URL}/blob/main/METHODS.md`;
export const DOCS_URL = `${GITHUB_URL}#readme`;
// While the app runs locally (next dev or a production next start), its own pages are a click away; never on the
// public website, which is always built with NEXT_PUBLIC_SITE_MODE=public (site.yml), so that flag alone separates them
export const SHOW_LOCAL_APP = !PUBLIC_SITE;

/** The paths that exist on the public website: the start page, the articles and their figures, the research reports, the news and the contact page. */
export const isPublicPath = (href: string) => /^\/(?:$|[#?]|artiklar(?:[/?#]|$)|forskningsrapporter(?:[/?#]|$)|en\/(?:forskningsrapporter|artiklar)(?:[/?#]|$)|nyheter(?:[/?#]|$)|kontakt(?:[/?#]|$)|api\/blog\/figures\/)/.test(href);
export const CONTACT_PATH = PUBLIC_SITE ? "/kontakt/" : "/kontakt";
export const EN_CONTACT_PATH = PUBLIC_SITE ? "/en/kontakt/" : "/en/kontakt";
export const NEWS_PATH = PUBLIC_SITE ? "/nyheter/" : "/nyheter";

// The contact form's receiver. The website is static, so FormSubmit (no account) emails the message on. The form is
// activated, and FormSubmit's random alias stands in for the founder's email address, so the address is not in the page.
export const CONTACT_ENDPOINT = process.env.NEXT_PUBLIC_CONTACT_ENDPOINT || "https://formsubmit.co/ajax/dd84130aea1d4ba97d568c540422d13e";
export const CONTACT_SERVICE_URL = "https://formsubmit.co/";

// The articles' authors: the byline links to the author's page, and search engines get the same link (schema.org)
export interface Author { name: string; url: string; page: string; linkedin: string; role: string; role_en: string; bio: string; bio_en: string }
export const AUTHORS: Record<string, Author> = {
  "Viktor Kvant": {
    name: "Viktor Kvant",
    // The author's page on the site (the contact page, which also presents the author) and the LinkedIn profile
    url: `${SITE_URL}/kontakt/`,
    page: "/kontakt",
    linkedin: "https://www.linkedin.com/in/viktor-kvant-555180108/",
    role: "Digital analytiker och grundare av Vitki",
    role_en: "Digital analyst and founder of Vitki",
    bio: "Viktor Kvant arbetar till vardags som digital analytiker och ser dataanalys som ett övergripande yrkesfält, där samma analytiska metoder kan driva gränserna framåt även inom humaniora och arkeologi. Han grundade Vitki.",
    bio_en: "Viktor Kvant works as a digital analyst and sees data analysis as an overarching field, where the same analytical methods can push the boundaries forward in the humanities and archaeology as well. He founded Vitki.",
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

/**
 * The public website's Content-Security-Policy, set as a <meta http-equiv> in app/layout.tsx (GitHub Pages cannot send
 * headers), and only on the website: what its pages load and send, nothing more.
 * - script-src 'unsafe-inline': the static export's inline bootstrap scripts (self.__next_f.push(…) with the page's
 *   data, and the loader of public/lang-init.js) differ on every page and in every build, so hashes would have to be
 *   computed after the build for each page; nothing on the site puts visitors' text into a script.
 * - style-src 'unsafe-inline': React's style attributes (the charts' bars, the picture sizes).
 * - img-src: the site's own pictures and Wikimedia Commons, where the articles' photos come from (articles.json).
 * - connect-src: the article search's index (the site itself), the vote and visitor counts (Firestore's REST
 *   interface, lib/track.ts and components/SiteVote.tsx) and the contact form (FormSubmit, components/ContactForm.tsx).
 * frame-ancestors cannot be set by a meta element (browsers ignore it there and warn), so it is left out.
 * Empty in the app, which sets no policy; the condition is written out (not PUBLIC_SITE), so that the app's build drops
 * the policy's text altogether.
 */
export const SITE_CSP = process.env.NEXT_PUBLIC_SITE_MODE !== "public" ? "" : [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https://upload.wikimedia.org https://thumb.wikimedia.org https://commons.wikimedia.org",
  "font-src 'self'",
  `connect-src 'self' https://firestore.googleapis.com ${new URL(CONTACT_ENDPOINT).origin}`,
  `form-action 'self' ${new URL(CONTACT_SERVICE_URL).origin}`,
  "object-src 'none'",
  "base-uri 'self'",
].join("; ");
