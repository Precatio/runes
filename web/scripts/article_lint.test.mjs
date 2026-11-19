// The web's review (src/lib/articleLint.ts) against the cases shared with src/article_lint.py
// (tests/fixtures/article_lint_cases.json), and how long the queue lasts (src/lib/redaktion.ts queueEnd), with
// Node's own test runner and type stripping:  node --test scripts/article_lint.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { lintArticle, lintSummary, numbers } from "../src/lib/articleLint.ts";
import { queueEnd } from "../src/lib/redaktion.ts";

const cases = JSON.parse(readFileSync(new URL("../../tests/fixtures/article_lint_cases.json", import.meta.url), "utf8")).fall;

for (const c of cases) {
  test(`samma fynd som Python: ${c.name}`, () => {
    const now = new Date(c.now ?? "2026-11-19T00:00:00Z");
    const got = lintArticle(c.post, c.posts ?? null, c.publish_at ? new Date(c.publish_at) : null, now);
    const key = got.map(f => [f.niva, f.kod, f.sprak]).sort((a, b) => (a.join() < b.join() ? -1 : a.join() > b.join() ? 1 : 0));
    const want = [...c.expect].sort((a, b) => (a.join() < b.join() ? -1 : a.join() > b.join() ? 1 : 0));
    assert.deepEqual(key, want, JSON.stringify(got, null, 1));
  });
}

test("tal läses som i Python", () => {
  assert.deepEqual(numbers("1 352 borgar, 31,5 procent och år 1050", "sv"), new Set(["1352", "31.5", "1050"]));
  assert.deepEqual(numbers("1,352 forts, 31.5 per cent and the year 1050", "en"), new Set(["1352", "31.5", "1050"]));
  assert.deepEqual(lintSummary([{ niva: "FEL" }, { niva: "VARNING" }, { niva: "VARNING" }]), { fel: 1, varningar: 2 });
});

test("kön: sista dagen och larmet under tre veckor", () => {
  const post = (id, over = {}) => ({ id, slug: id, title: id, published: false, publishedAt: null, updatedAt: null, labels: ["Forskning"], ...over });
  const posts = [
    post("a", { published: true, publishedAt: new Date("2027-02-07T06:00:00Z") }),
    post("r", { published: true, publishedAt: new Date("2027-03-01T06:00:00Z"), labels: ["Rapport"] }),
    post("d"),
  ];
  const plan = [
    { datum: "2027-02-10", tid: "07:00", id: "d", titel: "D", spar: "P", bluesky: null },
    { datum: "2027-02-12", tid: "07:00", id: "saknas", titel: "X", spar: "P", bluesky: null },
    { datum: "2027-03-05", tid: "07:00", id: "r", titel: "R", spar: "F", bluesky: null },
  ];
  assert.deepEqual(queueEnd(plan, posts, new Date("2026-11-19T12:00:00Z")), { until: "2027-02-10", daysLeft: 83, alarm: false });
  assert.deepEqual(queueEnd(plan, posts, new Date("2027-01-25T12:00:00Z")), { until: "2027-02-10", daysLeft: 16, alarm: true });
  assert.deepEqual(queueEnd([], [], new Date("2026-11-19T12:00:00Z")), { until: null, daysLeft: 0, alarm: true });
});
