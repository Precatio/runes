// Tests for the web admin's helper (src/lib/redaktion.ts) and its security policy (scripts/redaktion_csp.mjs), with
// Node's own test runner and type stripping (Node 22.18+):  node --test scripts/redaktion.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  BLUESKY_LIMIT, blueskyRequest, composedLength, explainError, fromStockholm, inWeek, isoWeek, latestPublished, matches,
  monthOf, ordered, planTime, publicationTime, publishNow, schedule, status, todayStockholm, toStockholmInput, unpublish,
  upcoming, weekOf, weekRefusal, weekState,
} from "../src/lib/redaktion.ts";
import { checkLabels } from "../src/lib/labels.ts";
import { policyOf, rewrite, widen } from "./redaktion_csp.mjs";

const NOW = new Date("2026-11-11T12:00:00Z");
const day = n => new Date(NOW.getTime() + n * 86_400_000);
const post = (over = {}) => ({ id: "x", slug: "x", title: "X", published: false, publishedAt: null, updatedAt: null, ...over });

test("status: draft, scheduled, published", () => {
  assert.equal(status(post(), NOW), "utkast");
  assert.equal(status(post({ published: false, publishedAt: day(-3) }), NOW), "utkast");
  assert.equal(status(post({ published: true, publishedAt: day(2) }), NOW), "schemalagd");
  assert.equal(status(post({ published: true, publishedAt: day(-2) }), NOW), "publicerad");
  assert.equal(status(post({ published: true, publishedAt: null }), NOW), "publicerad");  // as is_live: no date = live
});

test("publicationTime mirrors api/routers/blog.py publication_time", () => {
  const chosen = day(5), before = day(-10), future = day(3);
  assert.equal(publicationTime(chosen, before, NOW), chosen);
  assert.equal(publicationTime(null, before, NOW), before);   // live before: keeps its date
  assert.equal(publicationTime(null, future, NOW), NOW);      // scheduled, published at once: now
  assert.equal(publicationTime(null, null, NOW), NOW);
});

test("month is the UTC month of publishedAt, as the server's strftime", () => {
  assert.equal(monthOf(new Date("2026-12-31T23:30:00Z")), "2026-12");  // already January in Sweden
  assert.equal(monthOf(new Date("2027-01-01T00:00:00Z")), "2027-01");
});

test("the fields each action writes", () => {
  assert.deepEqual(publishNow(post(), NOW, "u"), { published: true, publishedAt: NOW, month: "2026-11", by: "u" });
  const old = day(-40);
  assert.deepEqual(publishNow(post({ publishedAt: old }), NOW, "u"), { published: true, publishedAt: old, month: monthOf(old), by: "u" });
  assert.deepEqual(publishNow(post({ publishedAt: day(4) }), NOW, "u").publishedAt, NOW);
  const at = new Date("2026-12-01T07:00:00Z");
  assert.deepEqual(schedule(at, NOW, "u"), { published: true, publishedAt: at, month: "2026-12", by: "u" });
  assert.throws(() => schedule(day(-1), NOW, "u"), /framtiden/);
  assert.throws(() => schedule(new Date(NaN), NOW, "u"), /kunde inte läsas/);
  assert.deepEqual(unpublish("u"), { published: false, by: "u" });  // date and month stay
});

test("Swedish wall-clock time, winter and summer", () => {
  assert.equal(fromStockholm("2026-11-20T08:00").toISOString(), "2026-11-20T07:00:00.000Z");  // CET, UTC+1
  assert.equal(fromStockholm("2026-07-01T18:00").toISOString(), "2026-07-01T16:00:00.000Z");  // CEST, UTC+2
  assert.equal(toStockholmInput(new Date("2026-11-20T07:00:00Z")), "2026-11-20T08:00");
  assert.equal(toStockholmInput(new Date("2026-07-01T16:00:00Z")), "2026-07-01T18:00");
  // the hour skipped in March moves forward; the hour repeated in October is the first one
  assert.equal(fromStockholm("2026-03-29T02:30").toISOString(), "2026-03-29T01:30:00.000Z");
  assert.equal(fromStockholm("2026-10-25T02:30").toISOString(), "2026-10-25T00:30:00.000Z");
  assert.ok(Number.isNaN(fromStockholm("i morgon").getTime()));
  for (const s of ["2026-01-05T00:00", "2026-03-28T23:59", "2026-10-26T12:15"]) assert.equal(toStockholmInput(fromStockholm(s)), s);
});

test("search, filters and the overview's lists", () => {
  const posts = [
    post({ id: "a", title: "Runor i Skåne", published: true, publishedAt: day(-1), labels: ["Artikel"] }),
    post({ id: "b", title: "Malt", published: true, publishedAt: day(3) }),
    post({ id: "c", title: "Rapport om Tor", labels: ["Rapport"], updatedAt: day(-2) }),
    post({ id: "d", title: "Senare", published: true, publishedAt: day(40) }),
    post({ id: "e", title: "Äldre", published: true, publishedAt: day(-9) }),
  ];
  assert.deepEqual(posts.filter(p => matches(p, "", "schemalagd", NOW)).map(p => p.id), ["b", "d"]);
  assert.deepEqual(posts.filter(p => matches(p, "", "rapporter", NOW)).map(p => p.id), ["c"]);
  assert.deepEqual(posts.filter(p => matches(p, "skåne", "alla", NOW)).map(p => p.id), ["a"]);
  assert.deepEqual(posts.filter(p => matches(p, "artikel", "publicerad", NOW)).map(p => p.id), ["a"]);
  assert.deepEqual(upcoming(posts, NOW).map(p => p.id), ["b"]);  // d is beyond four weeks
  assert.deepEqual(latestPublished(posts, NOW).map(p => p.id), ["a", "e"]);
  assert.deepEqual(ordered(posts, NOW).map(p => p.id), ["b", "d", "c", "a", "e"]);
});

test("errors in words; permission-denied means not activated", () => {
  assert.equal(explainError("permission-denied").notActive, true);
  assert.equal(explainError("auth/unauthorized-domain").notActive, true);
  assert.equal(explainError("auth/popup-closed-by-user").notActive, false);
  assert.equal(explainError("unavailable"), null);
});

test("the security policy is widened only by what sign-in and Firestore need", () => {
  const sitePolicy = "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self' https://firestore.googleapis.com; object-src 'none'";
  const w = widen(sitePolicy);
  assert.match(w, /script-src 'self' 'unsafe-inline' https:\/\/apis\.google\.com/);
  assert.match(w, /connect-src 'self' https:\/\/firestore\.googleapis\.com https:\/\/identitytoolkit\.googleapis\.com/);
  assert.match(w, /frame-src https:\/\/runes-1656b\.firebaseapp\.com/);
  assert.match(w, /object-src 'none'/);
  assert.equal(widen(w), w);  // idempotent
  const html = `<head><meta charSet="utf-8"/><meta http-equiv="Content-Security-Policy" content="default-src &#x27;self&#x27;; script-src &#x27;self&#x27;"/></head>`
    + `<script>self.__next_f.push([1,"[\\"$\\",\\"meta\\",null,{\\"content\\":\\"default-src 'self'; script-src 'self'\\"}]"])</script>`;
  const site = policyOf(html);
  assert.equal(site, "default-src 'self'; script-src 'self'");
  const { text, replaced } = rewrite(html, site);
  assert.equal(replaced, 2);  // the <meta> and the React data
  assert.match(text, /content="default-src &#x27;self&#x27;; script-src &#x27;self&#x27; https:\/\/apis\.google\.com; frame-src /);
  assert.match(text, /\\"default-src 'self'; script-src 'self' https:\/\/apis\.google\.com; frame-src [^\\]*\\"/);
  assert.equal(rewrite(text, site).replaced, 0);  // a second run changes nothing
  assert.equal(policyOf("<head></head>"), null);
});

// ---- Veckans publiceringar: the same answers as api/routers/blog_week.py (tests/test_blog_week.py) -----------------

test("the plan is read as Swedish time in winter and summer", () => {
  assert.equal(planTime({ datum: "2026-11-17", tid: "07:00" }).toISOString(), "2026-11-17T06:00:00.000Z");
  assert.equal(planTime({ datum: "2027-06-01", tid: "07:00" }).toISOString(), "2027-06-01T05:00:00.000Z");
  assert.equal(planTime({ datum: "2026-10-25", tid: "07:00" }).toISOString(), "2026-10-25T06:00:00.000Z");
  assert.equal(planTime({ datum: "2027-03-28", tid: "07:00" }).toISOString(), "2027-03-28T05:00:00.000Z");
  assert.equal(planTime({ datum: "2026-11-17", tid: "" }).toISOString(), "2026-11-17T06:00:00.000Z");  // 07:00 by default
  for (const bad of [{ datum: "2026-11-17", tid: "7" }, { datum: "17 nov", tid: "07:00" }, { datum: "2026-02-30", tid: "07:00" },
    { datum: "2026-11-17", tid: "25:00" }]) assert.ok(Number.isNaN(planTime(bad).getTime()), JSON.stringify(bad));
});

test("the week is the coming Monday to Sunday", () => {
  assert.deepEqual(weekOf(null, "2026-11-11"), { from: "2026-11-16", to: "2026-11-22" });  // a Wednesday
  assert.deepEqual(weekOf(null, "2026-11-16"), { from: "2026-11-16", to: "2026-11-22" });  // on the Monday itself
  assert.deepEqual(weekOf(null, "2026-11-17"), { from: "2026-11-23", to: "2026-11-29" });
  assert.deepEqual(weekOf(null, "2026-11-22"), { from: "2026-11-23", to: "2026-11-29" });  // a Sunday
  assert.deepEqual(weekOf("2026-11-19", "2026-11-11"), { from: "2026-11-16", to: "2026-11-22" });
  assert.deepEqual(weekOf("2026-12-28", "2026-11-11"), { from: "2026-12-28", to: "2027-01-03" });
  assert.equal(isoWeek("2026-11-16"), 47);
  assert.equal(isoWeek("2026-12-28"), 53);   // 2026 has 53 ISO weeks
  assert.equal(isoWeek("2027-01-04"), 1);
  assert.equal(isoWeek("2027-01-01"), 53);
  assert.equal(todayStockholm(new Date("2026-11-15T23:30:00Z")), "2026-11-16");  // already Monday in Sweden
  const rows = [{ datum: "2026-11-20", tid: "07:00", id: "b" }, { datum: "2026-11-17", tid: "12:00", id: "a2" },
    { datum: "2026-11-17", tid: "07:00", id: "a" }, { datum: "2026-11-24", id: "c" }, { datum: "2026-11-15", id: "z" }];
  assert.deepEqual(inWeek(rows, "2026-11-16", "2026-11-22").map(r => r.id), ["a", "a2", "b"]);
});

test("refusals, in the same order and words as blog_week.refusal", () => {
  const MON = new Date("2026-11-16T08:00:00Z");
  const row = { datum: "2026-11-17", tid: "07:00", id: "a", titel: "A", spar: "P", bluesky: { text: "Hello.", tags: ["runology"] } };
  const draft = { published: false, publishedAt: null };
  assert.equal(weekRefusal(row, draft, MON, null), null);
  assert.match(weekRefusal(row, null, MON, null), /finns inte/);
  assert.match(weekRefusal(row, { published: true, publishedAt: new Date("2026-11-01T06:00:00Z") }, MON, null), /^Redan publicerad/);
  assert.match(weekRefusal(row, { published: true, publishedAt: new Date("2026-11-20T06:00:00Z") }, MON, null), /^Redan schemalagd/);
  assert.match(weekRefusal(row, draft, new Date("2026-11-17T06:00:00Z"), null), /passerat/);  // 07:00 Swedish time
  assert.equal(weekRefusal(row, draft, new Date("2026-11-17T05:59:00Z"), null), null);
  assert.match(weekRefusal(row, draft, MON, "Okänd etikett: Påhittad"), /^Etiketterna: Okänd etikett/);
  assert.match(weekRefusal({ ...row, bluesky: { text: "x".repeat(300), tags: ["a"] } }, draft, MON, null), /Bluesky-texten har 304 tecken; högst 300/);
  assert.match(weekRefusal({ ...row, tid: "7" }, draft, MON, null), /kan inte läsas/);
  assert.equal(weekState(null, MON), "saknas");
  assert.equal(weekState({ published: true, publishedAt: new Date("2026-11-20T06:00:00Z") }, MON), "schemalagd");
  assert.equal(composedLength(row.bluesky), "Hello.\n\n#runology".length);
  assert.equal(composedLength({ text: " Hi ", tags: [] }), 2);
  assert.equal(composedLength(null), null);
  assert.equal(BLUESKY_LIMIT, 300);
});

test("the labels are checked as src/blog_labels.check", () => {
  assert.equal(checkLabels(["Forskning", "Geografi"]), null);
  assert.equal(checkLabels([]), null);
  assert.match(checkLabels(["Påhittad"]), /^Okänd etikett: Påhittad/);
  assert.match(checkLabels(["Forskning", "Metod"]), /^Bara en typ/);
  assert.match(checkLabels(["Forskning", "Ristare", "Norden", "Eddan", "Geografi", "Tolkning"]), /Högst 5/);
  assert.match(checkLabels(["Ristare", "Ristare"]), /två gånger/);
});

test("the Bluesky request has exactly the fields the rules allow", () => {
  const row = { datum: "2026-11-17", tid: "07:00", id: "a", titel: "A", spar: "P", bluesky: { text: "Hello.", tags: ["runology"] } };
  const r = blueskyRequest(row, "artikel-a", "u");
  assert.deepEqual(r, { slug: "artikel-a", datum: "2026-11-17", text: "Hello.", tags: ["runology"], en: true, by: "u" });
  r.tags.push("x");
  assert.deepEqual(row.bluesky.tags, ["runology"]);  // a copy
  assert.throws(() => blueskyRequest({ ...row, bluesky: null }, "a", "u"));
});
