// web/firestore.rules in the Firestore emulator: the web admin's access to the articles, the weekly plan and the Bluesky
// requests (/redaktion), and that the rules the app and the public website already rely on still hold. Run with
// `npm test` in this folder (the emulator needs Java 11+); nothing is deployed. The editor's uid is read from the rules file itself, so it is not repeated here.
import { readFileSync } from "node:fs";
import { after, before, beforeEach, describe, test } from "node:test";
import { assertFails, assertSucceeds, initializeTestEnvironment } from "@firebase/rules-unit-testing";
import {
  addDoc, collection, deleteDoc, doc, getDoc, getDocs, serverTimestamp, setDoc, Timestamp, updateDoc,
} from "firebase/firestore";

const RULES = readFileSync(new URL("../../web/firestore.rules", import.meta.url), "utf8");
const EDITOR = /request\.auth\.uid in \['([^']+)'/.exec(RULES)?.[1];
if (!EDITOR) throw new Error("No editor uid found in web/firestore.rules");
const OTHER = "someone-else";

let env;
const db = (uid) => (uid ? env.authenticatedContext(uid) : env.unauthenticatedContext()).firestore();
const post = (uid, id = "p1") => doc(db(uid), "posts", id);
const month = (d) => `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;

before(async () => {
  const [host, port] = (process.env.FIRESTORE_EMULATOR_HOST || "127.0.0.1:8095").split(":");
  env = await initializeTestEnvironment({ projectId: "demo-vitki", firestore: { rules: RULES, host, port: Number(port) } });
});
after(async () => env?.cleanup());

beforeEach(async () => {
  await env.clearFirestore();
  await env.withSecurityRulesDisabled(async (ctx) => {
    const fs = ctx.firestore();
    await setDoc(doc(fs, "posts", "p1"), {
      slug: "ett-utkast", title: "Ett utkast", body: "Text", published: false, month: "2026-11",
      updatedAt: Timestamp.fromDate(new Date("2026-11-01T10:00:00Z")), labels: ["Artikel"],
    });
    await setDoc(doc(fs, "posts", "p2"), {
      slug: "publicerad", title: "Publicerad", body: "Text", published: true, month: "2026-10",
      publishedAt: Timestamp.fromDate(new Date("2026-10-20T08:00:00Z")),
      updatedAt: Timestamp.fromDate(new Date("2026-10-20T08:00:00Z")), labels: ["Artikel"],
    });
    await setDoc(doc(fs, "publiceringsschema", "2026-11-17_p1"), {
      datum: "2026-11-17", tid: "07:00", id: "p1", titel: "Ett utkast", spar: "P", godkand: null,
      bluesky: { text: "Hello.", tags: ["runestones", "VikingAge"] },
    });
    await setDoc(doc(fs, "bluesky_forfragningar", "redan-dar"), {
      slug: "redan-dar", datum: "2026-11-20", text: "Hello.", tags: [], en: true,
      created: Timestamp.fromDate(new Date("2026-11-16T07:00:00Z")), by: EDITOR,
    });
    await setDoc(doc(fs, "messages", "m1"), { to: "all", text: "Hej" });
    await setDoc(doc(fs, "banned", "x"), { at: 1 });
  });
});

describe("posts: reading", () => {
  test("nobody signed out may read an article", () => assertFails(getDoc(post(null))));
  test("another account may not read", () => assertFails(getDoc(post(OTHER))));
  test("another account may not list", () => assertFails(getDocs(collection(db(OTHER), "posts"))));
  test("the editor may read a draft", () => assertSucceeds(getDoc(post(EDITOR))));
  test("the editor may list all articles", () => assertSucceeds(getDocs(collection(db(EDITOR), "posts"))));
});

describe("posts: publishing from /redaktion", () => {
  const at = new Date("2026-12-01T07:00:00Z");
  const publish = (over = {}) => ({
    published: true, publishedAt: Timestamp.fromDate(at), month: month(at), updatedAt: serverTimestamp(), by: EDITOR, ...over,
  });

  test("the editor may publish or schedule", () => assertSucceeds(updateDoc(post(EDITOR), publish())));
  test("the month must follow publishedAt (UTC)", () =>
    assertFails(updateDoc(post(EDITOR), publish({ month: "2026-11" }))));
  test("the month at a year's turn, in UTC", () => {
    const newYear = new Date("2026-12-31T23:30:00Z");  // already 1 January in Sweden, still December in UTC
    return assertSucceeds(updateDoc(post(EDITOR), publish({ publishedAt: Timestamp.fromDate(newYear), month: "2026-12" })));
  });
  test("updatedAt must be the server's time", () =>
    assertFails(updateDoc(post(EDITOR), publish({ updatedAt: Timestamp.fromDate(new Date()) }))));
  test("by must be the editor's own uid", () => assertFails(updateDoc(post(EDITOR), publish({ by: OTHER }))));
  test("a published article needs a publishedAt time", () =>
    assertFails(updateDoc(post(EDITOR), publish({ publishedAt: "2026-12-01" }))));
  test("the text cannot be changed", () => assertFails(updateDoc(post(EDITOR), publish({ title: "Ny titel" }))));
  test("veckans artikel cannot be changed", () => assertFails(updateDoc(post(EDITOR), publish({ featured: true }))));
  test("another account may not publish", () => assertFails(updateDoc(post(OTHER), publish({ by: OTHER }))));
  test("signed out may not publish", () => assertFails(updateDoc(post(null), publish())));

  test("the editor may unpublish, keeping date and month", () =>
    assertSucceeds(updateDoc(post(EDITOR, "p2"), { published: false, updatedAt: serverTimestamp(), by: EDITOR })));
  test("unpublishing may not move the date", () =>
    assertFails(updateDoc(post(EDITOR, "p2"), {
      published: false, publishedAt: Timestamp.fromDate(at), updatedAt: serverTimestamp(), by: EDITOR,
    })));
  test("the editor may not create an article", () =>
    assertFails(addDoc(collection(db(EDITOR), "posts"), { title: "Ny", published: false })));
  test("the editor may not delete an article", () => assertFails(deleteDoc(post(EDITOR))));
});

describe("publiceringsschema: the weekly plan", () => {
  const row = (uid) => doc(db(uid), "publiceringsschema", "2026-11-17_p1");
  test("the editor may read the plan", () => assertSucceeds(getDocs(collection(db(EDITOR), "publiceringsschema"))));
  test("another account may not read it", () => assertFails(getDoc(row(OTHER))));
  test("signed out may not read it", () => assertFails(getDocs(collection(db(null), "publiceringsschema"))));
  test("the editor may not change a row", () => assertFails(updateDoc(row(EDITOR), { tid: "08:00" })));
  test("the editor may not add a row", () =>
    assertFails(setDoc(doc(db(EDITOR), "publiceringsschema", "2026-11-18_x"), { datum: "2026-11-18", id: "x" })));
  test("the editor may not delete a row", () => assertFails(deleteDoc(row(EDITOR))));
});

describe("bluesky_forfragningar: Bluesky requests from /redaktion", () => {
  const request = (over = {}) => ({
    slug: "ny-artikel", datum: "2026-11-17", text: "No one on Sweden's runestones was called Freja.",
    tags: ["OldNorse", "Skystorians", "runestones", "VikingAge", "Vikings"], en: true, created: serverTimestamp(),
    by: EDITOR, ...over,
  });
  const req = (uid, id = "ny-artikel") => doc(db(uid), "bluesky_forfragningar", id);

  test("the editor may create a request", () => assertSucceeds(setDoc(req(EDITOR), request())));
  test("a request without tags", () => assertSucceeds(setDoc(req(EDITOR), request({ tags: [] }))));
  test("the editor may read requests", () => assertSucceeds(getDocs(collection(db(EDITOR), "bluesky_forfragningar"))));
  test("another account may not read requests", () => assertFails(getDoc(req(OTHER, "redan-dar"))));
  test("another account may not create one", () => assertFails(setDoc(req(OTHER), request({ by: OTHER }))));
  test("signed out may not create one", () => assertFails(setDoc(req(null), request())));
  test("the document id must be the slug", () => assertFails(setDoc(req(EDITOR, "annan"), request())));
  test("the slug must be an article address", () =>
    assertFails(setDoc(req(EDITOR, "Inte OK"), request({ slug: "Inte OK" }))));
  test("text of 400 characters is allowed", () => assertSucceeds(setDoc(req(EDITOR), request({ text: "x".repeat(400) }))));
  test("text of 401 characters is refused", () => assertFails(setDoc(req(EDITOR), request({ text: "x".repeat(401) }))));
  test("empty text is refused", () => assertFails(setDoc(req(EDITOR), request({ text: "" }))));
  test("at most 8 tags", () =>
    assertFails(setDoc(req(EDITOR), request({ tags: ["a", "b", "c", "d", "e", "f", "g", "h", "i"] }))));
  test("8 tags are allowed", () =>
    assertSucceeds(setDoc(req(EDITOR), request({ tags: ["a", "b", "c", "d", "e", "f", "g", "h"] }))));
  test("tags must be strings", () => assertFails(setDoc(req(EDITOR), request({ tags: ["a", 5] }))));
  test("tags must be a list", () => assertFails(setDoc(req(EDITOR), request({ tags: "VikingAge" }))));
  test("datum must be a date string", () => assertFails(setDoc(req(EDITOR), request({ datum: "17 nov" }))));
  test("datum may not be a timestamp", () =>
    assertFails(setDoc(req(EDITOR), request({ datum: Timestamp.fromDate(new Date("2026-11-17T06:00:00Z")) }))));
  test("en must be true", () => assertFails(setDoc(req(EDITOR), request({ en: false }))));
  test("created must be the server's time", () =>
    assertFails(setDoc(req(EDITOR), request({ created: Timestamp.fromDate(new Date()) }))));
  test("by must be the editor's own uid", () => assertFails(setDoc(req(EDITOR), request({ by: OTHER }))));
  test("no other fields", () => assertFails(setDoc(req(EDITOR), request({ posted: "https://bsky.app/x" }))));
  test("no missing fields", () => {
    const { tags, ...rest } = request();  // eslint-disable-line no-unused-vars
    return assertFails(setDoc(req(EDITOR), rest));
  });
  test("an existing request cannot be overwritten", () =>
    assertFails(setDoc(req(EDITOR, "redan-dar"), request({ slug: "redan-dar" }))));
  test("an existing request cannot be changed", () =>
    assertFails(updateDoc(req(EDITOR, "redan-dar"), { text: "Changed" })));
  test("a request cannot be deleted", () => assertFails(deleteDoc(req(EDITOR, "redan-dar"))));
});

describe("the rules the app and the website already use", () => {
  test("a user's own settings", () =>
    assertSucceeds(setDoc(doc(db("u1"), "users/u1/settings/profile"), { userInstitution: "X" }, { merge: true })));
  test("not another user's settings", () => assertFails(getDoc(doc(db("u2"), "users/u1/settings/profile"))));
  test("the corpus is read by signed-in users", () => assertSucceeds(getDocs(collection(db("u1"), "corpus"))));
  test("the corpus is not read signed out", () => assertFails(getDocs(collection(db(null), "corpus"))));
  test("a message to everyone is read signed out", () => assertSucceeds(getDoc(doc(db(null), "messages/m1"))));
  test("suspended accounts are closed", () => assertFails(getDoc(doc(db(EDITOR), "banned/x"))));
  test("a vote from the website", () =>
    assertSucceeds(addDoc(collection(db(null), "site_votes"), { question: "webbapp", choice: "ja", lang: "sv" })));
  test("a page view from the website", () => {
    const day = new Date().toISOString().slice(0, 10);
    return assertSucceeds(addDoc(collection(db(null), "site_views"), { kind: "view", path: "/artiklar/", day, lang: "sv" }));
  });
  test("page views cannot be read", () => assertFails(getDocs(collection(db(EDITOR), "site_views"))));
  test("anything else is closed", () => assertFails(getDoc(doc(db(EDITOR), "other/x"))));
});
