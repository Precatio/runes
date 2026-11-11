// Tests for the web admin's helper (src/lib/redaktion.ts) and its security policy (scripts/redaktion_csp.mjs), with
// Node's own test runner and type stripping (Node 22.18+):  node --test scripts/redaktion.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  explainError, fromStockholm, latestPublished, matches, monthOf, ordered, publicationTime, publishNow, schedule, status,
  toStockholmInput, unpublish, upcoming,
} from "../src/lib/redaktion.ts";
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
