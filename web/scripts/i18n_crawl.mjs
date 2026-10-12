// Visits the app in English and collects every sentence the translator could not find in the catalog.
//
//   node scripts/i18n_crawl.mjs OUT.json [BASE_URL] [ROUTE ...]
//
// Needs the dev servers (web on :3000, API on :8000) and Google Chrome. Opens <details>, question menus and the first
// rows of tables, but never presses buttons that start analyses, write data or call AI. Also reports JavaScript
// errors, so that a page the translator breaks is noticed.
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [out = "i18n_misses.json", base = "http://localhost:3000", ...only] = process.argv.slice(2);
const ROUTES = only.length ? only : [
  "/", "/start", "/stenanalys", "/3d", "/2d", "/rti", "/synthesis", "/phonetics", "/inskrifter",
  "/inskrifter?signum=U%20735", "/karta", "/karta?signum=U%20735", "/stilgrupper", "/korpus", "/jamfor", "/luckor",
  "/oversikt", "/oversikt?signum=U%20735", "/oversikt?signum=U%20344", "/oversikt?signum=Sö%20131", "/statistik",
  "/rapporter", "/knowledge", "/docs", "/account", "/admin",
];
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9300 + Math.floor(Math.random() * 400);
const sleep = ms => new Promise(r => setTimeout(r, ms));

const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "i18n-"))}`, "about:blank"], { stdio: "ignore" });
let ws, id = 0;
const pending = new Map(), errors = [];
const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;

// Clicks that only reveal text: details, question menus, "show all", tabs and the first rows of clickable tables
const REVEAL = `(() => {
  const unsafe = /kör|starta|stäm av|radera|ta bort|logga|spara|skicka|ladda|skapa|generera|exportera|analysera|mät|beräkna|hämta|avstäm|banna|kopiera|byt|switch|run|start|check|delete|remove|sign|save|send|upload|download|create|generate|export|analy|measure|compute|fetch|ban|copy/i;
  const clicked = [];
  document.querySelectorAll("details:not([open])").forEach(d => { d.open = true; clicked.push("details"); });
  const buttons = [...document.querySelectorAll("nav[aria-label] button, [role=tab], button")]
    .filter(b => !b.disabled && b.offsetParent && !b.closest("aside, header, [translate=no]") && !unsafe.test(b.innerText || b.getAttribute("aria-label") || ""))
    .filter(b => b.closest("nav[aria-label]") || b.getAttribute("role") === "tab" || /^(visa|show|alla|all|fler|more|mer)/i.test((b.innerText || "").trim()));
  return buttons.map(b => (b.innerText || "").trim().slice(0, 40));
})()`;
const CLICK = i => `(() => {
  const unsafe = /kör|starta|stäm av|radera|ta bort|logga|spara|skicka|ladda|skapa|generera|exportera|analysera|mät|beräkna|hämta|avstäm|banna|kopiera|byt|switch|run|start|check|delete|remove|sign|save|send|upload|download|create|generate|export|analy|measure|compute|fetch|ban|copy/i;
  const buttons = [...document.querySelectorAll("nav[aria-label] button, [role=tab], button")]
    .filter(b => !b.disabled && b.offsetParent && !b.closest("aside, header, [translate=no]") && !unsafe.test(b.innerText || b.getAttribute("aria-label") || ""))
    .filter(b => b.closest("nav[aria-label]") || b.getAttribute("role") === "tab" || /^(visa|show|alla|all|fler|more|mer)/i.test((b.innerText || "").trim()));
  buttons[${i}]?.click();
})()`;
const ROWS = `(() => { const rows = [...document.querySelectorAll("tr.cursor-pointer")].slice(0, 4); rows.forEach(r => r.click()); return rows.length; })()`;
const MISSES = `JSON.stringify(window.__vitkiI18n || { misses: {}, pages: {} })`;

async function quiet() {
  let last = -1;
  for (let i = 0; i < 40; i++) {
    await sleep(1000);
    const n = await ev(`document.body ? document.body.innerText.length : 0`);
    const busy = await ev(`/Läser|Laddar|Hämtar|Beräknar|Loading|Fetching|Calculating|Reading/.test(document.body?.innerText || "")`);
    if (n === last && !busy) return;
    last = n;
  }
}

const all = existsSync(out) ? JSON.parse(readFileSync(out, "utf8")) : { misses: {}, pages: {}, errors: [] };
try {
  for (let i = 0; i < 50; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const p = l.find(t => t.type === "page");
      if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); break; }
    } catch { /* Chrome is starting */ }
    await sleep(200);
  }
  await new Promise(r => ws.addEventListener("open", r));
  ws.addEventListener("message", e => {
    const m = JSON.parse(e.data);
    if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description?.split("\n")[0] || m.params.exceptionDetails.text);
    if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") errors.push("console: " + m.params.args.map(a => a.value ?? a.description).join(" ").slice(0, 300));
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  await send("Page.enable"); await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: base + "/" });
  await sleep(2500);
  await ev(`localStorage.setItem("vitki_lang", "en")`);
  for (const route of ROUTES) {
    const before = errors.length;
    await send("Page.navigate", { url: base + route });
    await quiet();
    for (let y = 0; y < 30; y++) {  // scroll so that lazily rendered parts appear
      const done = await ev(`(() => { window.scrollBy(0, 900); return window.innerHeight + window.scrollY >= document.body.scrollHeight - 5; })()`);
      await sleep(150);
      if (done) break;
    }
    const labels = (await ev(REVEAL)) || [];
    for (let k = 0; k < Math.min(labels.length, 25); k++) { await ev(CLICK(k)); await sleep(900); }
    await ev(ROWS); await sleep(1200);
    await ev(`document.querySelectorAll("details:not([open])").forEach(d => d.open = true)`); await sleep(400);
    const got = JSON.parse(await ev(MISSES));
    let fresh = 0;
    for (const [t, ex] of Object.entries(got.misses)) {
      if (!(t in all.misses)) { all.misses[t] = ex; all.pages[t] = got.pages[t]; fresh++; }
    }
    const errs = errors.slice(before).filter(e => !/favicon|Failed to load resource|401|403|404/.test(e));
    if (errs.length) all.errors.push({ route, errors: errs.slice(0, 5) });
    console.log(`${route}: ${fresh} nya saknade, ${labels.length} klick${errs.length ? `, FEL: ${errs[0].slice(0, 160)}` : ""}`);
    writeFileSync(out, JSON.stringify(all, null, 1));
  }
  console.log(`totalt ${Object.keys(all.misses).length} saknade mallar → ${out}`);
} finally {
  try { ws?.close(); } catch { /* closed */ }
  chrome.kill("SIGKILL");
}
