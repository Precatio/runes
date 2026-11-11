// The web admin (/redaktion): which state an article is in, and exactly which fields a publication change writes to
// Firestore. It writes the same fields, with the same meaning, as the local app's save (api/routers/blog.py save_post
// and publication_time): published, publishedAt, month (from publishedAt, in UTC, as the server's strftime), by and
// updatedAt (the server's time, which the Firestore rules require). Text, labels and "veckans artikel" are not touched.
// No imports, so that the tests can run it with plain Node (web/scripts/redaktion.test.mjs).

export type Status = "utkast" | "schemalagd" | "publicerad";
export type Filter = "alla" | Status | "rapporter";

export interface AdminPost {
  id: string;
  slug: string;
  title: string;
  summary?: string;
  body?: string;
  published: boolean;
  publishedAt: Date | null;
  updatedAt: Date | null;
  month?: string;
  labels?: string[];
  featured?: boolean;
}

/** The fields one publication change writes, apart from updatedAt (serverTimestamp() in the page). */
export interface PublicationFields {
  published: boolean;
  publishedAt?: Date;
  month?: string;
  by: string;
}

export const REPORT_LABEL = "Rapport";
export const TIME_ZONE = "Europe/Stockholm";

export function status(p: Pick<AdminPost, "published" | "publishedAt">, now: Date): Status {
  if (!p.published) return "utkast";
  return p.publishedAt && p.publishedAt.getTime() > now.getTime() ? "schemalagd" : "publicerad";
}

export const isReport = (p: Pick<AdminPost, "labels">) => (p.labels ?? []).includes(REPORT_LABEL);

/** "YYYY-MM" of a time in UTC – what the server writes as month (data["publishedAt"].strftime("%Y-%m")). */
export function monthOf(d: Date): string {
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

/** As api/routers/blog.py publication_time: the chosen time, else the date it already had if that has passed, else now. */
export function publicationTime(publishAt: Date | null, before: Date | null, now: Date): Date {
  if (publishAt) return publishAt;
  if (before && before.getTime() <= now.getTime()) return before;
  return now;
}

/** "Publicera nu": live at once. An article that was live before keeps its date; a draft or a scheduled one gets now. */
export function publishNow(p: Pick<AdminPost, "publishedAt">, now: Date, uid: string): PublicationFields {
  const at = publicationTime(null, p.publishedAt, now);
  return { published: true, publishedAt: at, month: monthOf(at), by: uid };
}

/** "Schemalägg": live at the given time, which must lie in the future. */
export function schedule(at: Date, now: Date, uid: string): PublicationFields {
  if (Number.isNaN(at.getTime())) throw new Error("Tiden kunde inte läsas.");
  if (at.getTime() <= now.getTime()) throw new Error("Välj en tid i framtiden (eller Publicera nu).");
  return { published: true, publishedAt: at, month: monthOf(at), by: uid };
}

/** "Avpublicera": back to a draft. Its date and month stay, as when the local app saves a draft. */
export function unpublish(uid: string): PublicationFields {
  return { published: false, by: uid };
}

// ---- Swedish time --------------------------------------------------------------------------------------------------

function zoneParts(d: Date): Record<string, number> {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: TIME_ZONE, hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit",
    minute: "2-digit", second: "2-digit",
  }).formatToParts(d);
  const out: Record<string, number> = {};
  for (const x of parts) if (x.type !== "literal") out[x.type] = Number(x.value);
  return out;
}

/** How far Swedish time is ahead of UTC at that moment, in milliseconds (1 h in winter, 2 h in summer). */
function offsetAt(d: Date): number {
  const p = zoneParts(d);
  return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - Math.floor(d.getTime() / 1000) * 1000;
}

/** A wall-clock time in Sweden ("2026-11-20T08:00", as from <input type="datetime-local">) as an exact moment. A time
 *  that does not exist (the hour skipped in March) moves forward an hour; an ambiguous one (October) is the first. */
export function fromStockholm(local: string): Date {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(local.trim());
  if (!m) return new Date(NaN);
  const wall = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  // The offsets in force a day before and a day after: a change of clocks lies between them at most
  const offsets = [...new Set([offsetAt(new Date(wall - 86_400_000)), offsetAt(new Date(wall + 86_400_000))])];
  const exact = offsets.map(o => wall - o).filter(t => toStockholmInput(new Date(t)) === local.trim());
  if (exact.length) return new Date(Math.min(...exact));
  return new Date(wall - Math.min(...offsets));
}

/** The moment as Swedish wall-clock time for <input type="datetime-local"> ("2026-11-20T08:00"). */
export function toStockholmInput(d: Date): string {
  const p = zoneParts(d);
  const two = (n: number) => String(n).padStart(2, "0");
  return `${p.year}-${two(p.month)}-${two(p.day)}T${two(p.hour)}:${two(p.minute)}`;
}

/** "ons 20 nov. 2026 08:00" in Swedish time. */
export function formatStockholm(d: Date | null): string {
  if (!d) return "–";
  return new Intl.DateTimeFormat("sv-SE", {
    timeZone: TIME_ZONE, weekday: "short", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(d);
}

// ---- lists ---------------------------------------------------------------------------------------------------------

export function matches(p: AdminPost, query: string, filter: Filter, now: Date): boolean {
  if (filter === "rapporter" ? !isReport(p) : filter !== "alla" && status(p, now) !== filter) return false;
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return [p.title, p.slug, p.summary ?? "", ...(p.labels ?? [])].some(s => s.toLowerCase().includes(q));
}

/** Scheduled articles that go live within the coming days, soonest first. */
export function upcoming(posts: AdminPost[], now: Date, days = 28): AdminPost[] {
  const end = now.getTime() + days * 86_400_000;
  return posts.filter(p => status(p, now) === "schemalagd" && p.publishedAt!.getTime() <= end)
    .sort((a, b) => a.publishedAt!.getTime() - b.publishedAt!.getTime());
}

/** Live articles, newest first. */
export function latestPublished(posts: AdminPost[], now: Date, n = 5): AdminPost[] {
  return posts.filter(p => status(p, now) === "publicerad")
    .sort((a, b) => (b.publishedAt?.getTime() ?? 0) - (a.publishedAt?.getTime() ?? 0)).slice(0, n);
}

/** The list's order: scheduled soonest first, then drafts and published by their latest change or date. */
export function ordered(posts: AdminPost[], now: Date): AdminPost[] {
  const rank: Record<Status, number> = { schemalagd: 0, utkast: 1, publicerad: 2 };
  const key = (p: AdminPost) => (p.publishedAt ?? p.updatedAt)?.getTime() ?? 0;
  return [...posts].sort((a, b) => {
    const ra = rank[status(a, now)], rb = rank[status(b, now)];
    if (ra !== rb) return ra - rb;
    return ra === 0 ? key(a) - key(b) : (b.updatedAt?.getTime() ?? key(b)) - (a.updatedAt?.getTime() ?? key(a));
  });
}

/** Why Firestore or sign-in refused, in words for the editor; null when the error is not one of the known kinds. */
export function explainError(code: string | undefined): { notActive: boolean; text: string } | null {
  switch (code) {
    case "permission-denied":
    case "firestore/permission-denied":
      return { notActive: true, text: "Firestore nekade åtkomst: säkerhetsreglerna för redaktionen är inte driftsatta än, "
        + "eller så är det här kontot inte redaktör (ADMIN_UIDS)." };
    case "auth/unauthorized-domain":
      return { notActive: true, text: "Den här domänen är inte godkänd för inloggning i Firebase Auth (Authorized domains)." };
    case "auth/api-key-not-valid.-please-pass-a-valid-api-key.":
    case "auth/invalid-api-key":
      return { notActive: true, text: "Firebase-nyckeln i webbplatsens bygge saknas eller är fel (FIREBASE_WEB_API_KEY)." };
    case "auth/popup-blocked":
      return { notActive: false, text: "Webbläsaren stoppade inloggningsfönstret. Tillåt popup-fönster för sidan och försök igen." };
    case "auth/popup-closed-by-user":
    case "auth/cancelled-popup-request":
      return { notActive: false, text: "Inloggningen avbröts." };
    default:
      return null;
  }
}
