// The public website's visitor counting, shared by components/SiteTracker.tsx (page views, sections, the way
// between pages and the outbound and language clicks) and the search boxes and share buttons (searches and shares).
// Every count is one anonymous row written straight to Firestore (the rules in firestore.rules allow exactly these
// fields and nothing else), with no cookie, nothing stored on the device and no identifier: not even the visit
// is given an id – the page a visitor came from inside the site is passed on from memory and lost on reload.
// A browser that has opened the site once with ?inte-rakna is left out from then on; ?rakna counts it again.
import { PUBLIC_SITE, SITE_PROJECT, STATS_OFF_KEY, siteCollection } from "@/lib/site";

const URL_ = siteCollection("site_views");

export const str = (v: string, max: number) => ({ stringValue: v.slice(0, max) });
const int = (n: number) => ({ integerValue: String(Math.max(0, Math.round(n))) });

// The channels a share link can name in ?via= (components/ShareArticle.tsx); anything else in the address is ignored
export const SHARE_CHANNELS = ["lank", "enhet", "x", "facebook", "linkedin", "epost"] as const;
export type ShareChannel = (typeof SHARE_CHANNELS)[number];

// The share channel named in the address the visit started from, read once when the page is first loaded
export const entryVia: string | null = (() => {
  if (typeof window === "undefined") return null;
  const v = new URLSearchParams(window.location.search).get("via");
  return v && (SHARE_CHANNELS as readonly string[]).includes(v) ? v : null;
})();

const counted = () => {
  try { return localStorage.getItem(STATS_OFF_KEY) !== "1"; } catch { return true; }
};

// Counting happens only on the public website, never on a developer's machine, in automated browsers or in a
// browser the founder has switched off
export const counting = () => {
  if (!PUBLIC_SITE || !SITE_PROJECT || typeof window === "undefined") return false;
  const host = window.location.hostname;
  return host !== "localhost" && host !== "127.0.0.1" && !navigator.webdriver && counted();
};

// Pages as the visitor sees them, without the trailing slash of the static export (/artiklar/x/ and /artiklar/x are one)
export const normal = (path: string) => (path.length > 1 ? path.replace(/\/+$/, "") : path) || "/";

export type Kind = "view" | "section" | "search" | "click";

export function send(kind: Kind, path: string, extra: Record<string, unknown> = {}) {
  const w = window.innerWidth;
  const fields = {
    kind: str(kind, 10),
    path: str(path, 200),
    day: str(new Date().toISOString().slice(0, 10), 10),
    tz: str(Intl.DateTimeFormat().resolvedOptions().timeZone || "", 60),
    lang: str(navigator.language || "", 12),
    device: str(w < 640 ? "mobil" : w < 1024 ? "surfplatta" : "dator", 12),
    ...extra,
  };
  fetch(URL_, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ fields }), keepalive: true })
    .catch(() => { /* a lost count is not worth an error */ });
}

// A click on a share button (dela:kanal), an outbound link (ut:webbplats) or a language link (sprak:en / sprak:sv)
export function trackClick(label: string) {
  if (!counting()) return;
  send("click", normal(window.location.pathname), { label: str(label, 80) });
}

let lastSearch = "";

// A settled search in one of the article search boxes: the words and how many articles they found. Words that look like
// an e-mail address, a link or a long number are never stored, and the same words twice in a row count once.
export function trackSearch(query: string, hits: number) {
  if (!counting()) return;
  const words = query.toLowerCase().replace(/\s+/g, " ").trim();
  if (words.length < 3 || words.length > 60) return;
  if (/@|https?:|www\./.test(words) || /\d{6,}/.test(words.replace(/[\s-]/g, ""))) return;
  if (words === lastSearch) return;
  lastSearch = words;
  send("search", normal(window.location.pathname), { label: str(words, 80), hits: int(hits) });
}
