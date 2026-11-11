// web/firestore.rules in the Firestore emulator: the web admin's access to the articles (/redaktion), and that the
// rules the app and the public website already rely on still hold. Run with `npm test` in this folder (the emulator
// needs Java 11+); nothing is deployed. The editor's uid is read from the rules file itself, so it is not repeated here.
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
