// The web admin's own security policy on the public website. Every page carries SITE_CSP (lib/site.ts) as a <meta> in
// its <head>; a second policy could only narrow it, never widen it, so after the build this script rewrites the policy
// in the files under /redaktion only (.github/workflows/site.yml): in the <meta> itself and in the page's React data
// (the inline RSC payload and the .txt files). Without the second, React adds the site's own <meta> again when the page
// hydrates, and the browser then enforces both policies – the narrower one wins (seen in a test 2026-11-11).
//   node web/scripts/redaktion_csp.mjs web/out
// What /redaktion needs beyond the site's policy, and why:
// - script-src https://apis.google.com: Firebase Auth's Google sign-in (signInWithPopup) loads Google's iframe helper.
// - frame-src <authDomain>: the hidden iframe that carries the sign-in back from the popup.
// - connect-src Identity Toolkit and Secure Token (sign-in and token refresh) and api.github.com (the build status);
//   Firestore (firestore.googleapis.com) is already allowed for the votes and counts.
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const AUTH_DOMAIN = "https://runes-1656b.firebaseapp.com";
export const EXTRA = {
  "script-src": ["https://apis.google.com"],
  "frame-src": [AUTH_DOMAIN, "https://apis.google.com"],
  "connect-src": ["https://identitytoolkit.googleapis.com", "https://securetoken.googleapis.com", "https://api.github.com"],
};

/** The site's policy with the sources /redaktion needs added (a directive that is missing is created). */
export function widen(policy, extra = EXTRA) {
  const parts = policy.split(";").map(s => s.trim()).filter(Boolean);
  const seen = new Set();
  const out = parts.map(p => {
    const [name, ...sources] = p.split(/\s+/);
    seen.add(name);
    const add = (extra[name] ?? []).filter(s => !sources.includes(s));
    return [name, ...sources, ...add].join(" ");
  });
  for (const [name, sources] of Object.entries(extra)) if (!seen.has(name)) out.push([name, ...sources].join(" "));
  return out.join("; ");
}

const META = /(<meta http-equiv="Content-Security-Policy" content=")([^"]*)(")/i;
const decode = s => s.replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&");
const encode = s => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;");

/** The site's policy as the page's <meta> gives it; null when the page has none (the app's build). */
export function policyOf(html) {
  const m = META.exec(html);
  return m ? decode(m[2]) : null;
}

/** A page's HTML or React data with every copy of the site's policy replaced by the widened one: the <meta> attribute
 *  (HTML-escaped) and the RSC payload, where the policy stands as a plain JSON string (the added sources hold no
 *  quotes or backslashes, so the JSON stays valid). Returns the text and how many copies were replaced. */
export function rewrite(text, site) {
  const wide = widen(site);
  // The site's policy can be the start of the widened one (a directive added at the end), so copies that are already
  // widened are set aside first: a second run changes nothing
  const KEEP = "\u0000redaktion-csp\u0000";
  const count = (s, part) => s.split(part).length - 1;
  let t = text.split(encode(wide)).join(KEEP + "e").split(wide).join(KEEP + "r");
  const replaced = count(t, encode(site)) + count(t, site);
  t = t.split(encode(site)).join(encode(wide)).split(site).join(wide);
  return { text: t.split(KEEP + "e").join(encode(wide)).split(KEEP + "r").join(wide), replaced };
}

function files(dir) {
  return readdirSync(dir).flatMap(name => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? files(p) : /\.(html|txt)$/.test(name) ? [p] : [];
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const out = process.argv[2] || "out";
  const dir = join(out, "redaktion");
  const site = policyOf(readFileSync(join(dir, "index.html"), "utf8"));
  if (!site) throw new Error(`${dir}/index.html: no Content-Security-Policy to widen`);
  let pages = 0, copies = 0;
  for (const f of files(dir)) {
    const { text, replaced } = rewrite(readFileSync(f, "utf8"), site);
    if (f.endsWith(".html") && !replaced) throw new Error(`${f}: the site's policy was not found`);
    if (replaced) writeFileSync(f, text);
    pages += f.endsWith(".html") ? 1 : 0;
    copies += replaced;
  }
  console.log(`Redaktionens säkerhetspolicy: ${pages} sida/sidor, ${copies} förekomster`);
}
