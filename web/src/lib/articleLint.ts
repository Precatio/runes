// The review before approval (/redaktion): the same checks as src/article_lint.py, apart from the journal page check,
// which needs the local journal database (sok.sqlite) and runs in the local Admin and at its approval. Both are tried
// against the same cases (tests/fixtures/article_lint_cases.json) in tests/test_article_lint.py and
// web/scripts/article_lint.test.mjs, so a change to a rule is made in both files.
// No imports, so that the tests can run it with plain Node.

export type Level = "FEL" | "VARNING";
export interface Finding { niva: Level; kod: string; sprak: "sv" | "en"; text: string; utdrag: string }

/** The fields of an article the review reads (as in Firestore: title, summary, body, *_en, seo_title*, labels). */
export interface LintPost {
  slug?: string; title?: string; summary?: string; body?: string;
  title_en?: string; summary_en?: string; body_en?: string;
  seo_title?: string; seo_title_en?: string; labels?: string[];
  published?: boolean; publishedAt?: Date | string | null;
}
/** Another article, for the link check. */
export interface LinkTarget { slug: string; published: boolean; publishedAt: Date | string | null; hasEnglish?: boolean }

export const SEO_MAX = 52;
export const KORTHET_MIN_CHARS = 3000;
const BOX = { sv: "Det viktigaste i korthet", en: "The essentials in brief" } as const;
const SITE_ROUTES: Record<string, Set<string>> = { artiklar: new Set(["rss.xml"]), forskningsrapporter: new Set(["begrepp"]) };

// Python's \b and \w are Unicode-aware; JavaScript's are not, so word edges are written out
const W = "[\\p{L}\\p{N}_]";
const B = `(?<!${W})`;
const E = `(?!${W})`;

const finding = (niva: Level, kod: string, sprak: "sv" | "en", text: string, utdrag = ""): Finding =>
  ({ niva, kod, sprak, text, utdrag: utdrag.slice(0, 240) });

// ---- text helpers --------------------------------------------------------------------------------------------------

const LINK_TARGET = /\]\(([^)\s]*)\)/g;
const IMAGE = /!\[[^\]]*\]\([^)]*\)/g;
const SOURCES = /^##\s+(Källor|Källor och data|Sources|References|Litteratur|Literature)\b.*$/m;

export const visible = (text: string) => (text ?? "").replace(IMAGE, "").replace(LINK_TARGET, "]");

export function prose(text: string): string {
  const m = SOURCES.exec(text ?? "");
  return visible(m ? text.slice(0, m.index) : text ?? "");
}

const SENTENCE = /(?<=[.!?])\s+(?=["”“(«*]*[A-ZÅÄÖÆØÉÜ0-9])|\n+/u;
export const sentences = (text: string) => text.split(SENTENCE).map(s => s.trim()).filter(Boolean);

function excerpt(s: string, at = 0, width = 110): string {
  const a = Math.max(0, at - Math.floor(width / 2));
  return (a ? "…" : "") + s.slice(a, a + width).trim() + (a + width < s.length ? "…" : "");
}

// ---- checks --------------------------------------------------------------------------------------------------------

const PLACEHOLDER = /\{[^{}\n]{1,60}\}/g;
const AI_WORD = /(?<![\p{L}\p{N}_ÅÄÖåäö])AI(?![a-zåäöA-ZÅÄÖ])/gu;

function checkPlaceholders(fields: Record<string, string>, sprak: "sv" | "en"): Finding[] {
  const out: Finding[] = [];
  for (const [name, text] of Object.entries(fields)) {
    for (const m of (text ?? "").matchAll(PLACEHOLDER)) {
      out.push(finding("FEL", "platshallare", sprak, `Platshållaren ${m[0]} står kvar (${name}).`, excerpt(text, m.index)));
    }
  }
  return out;
}

function checkAi(fields: Record<string, string>, sprak: "sv" | "en"): Finding[] {
  const out: Finding[] = [];
  for (const [name, text] of Object.entries(fields)) {
    const t = visible(text ?? "");
    for (const m of t.matchAll(AI_WORD)) {
      out.push(finding("FEL", "ai", sprak, `Ordet ”AI” (${name}); namnge modellen i stället (Anthropics språkmodell Claude).`,
        excerpt(t, m.index)));
    }
  }
  return out;
}

const CARVER = {
  sv: new RegExp(`${B}${W}*(?:ristare|ristaren|ristarens|ristares)${E}`, "giu"),
  en: new RegExp(`${B}${W}*(?:carver|carver's|carver’s)${E}`, "giu"),
};
const PRONOUN = { sv: new RegExp(`${B}(han|hans|honom)${E}`, "u"), en: new RegExp(`${B}(he|his|him|himself)${E}`, "u") };
const LEAD_PRONOUN = { sv: new RegExp(`^["”“(«*]*(Han|Hans|Honom)${E}`, "u"), en: new RegExp(`^["”“(«*]*(He|His|Him)${E}`, "u") };
const PRONOUN_WINDOW = 12;
// "hans eller hennes", "his or her": both genders named, nothing assumed
const INCLUSIVE = new RegExp(`${B}(han eller hon|hon eller han|hans eller hennes|hennes eller hans|honom eller henne|he or she|she or he|his or her|her or his|him or her)${E}`, "giu");
const NAMED_CARVER = {
  sv: new RegExp(`^["”“(«*]*[A-ZÅÄÖ][\\p{L}\\p{N}_]+(?: [A-ZÅÄÖ][\\p{L}\\p{N}_]+)?\\s+(?:var|är|kallas)\\s+(?:en|den)${E}`, "u"),
  en: new RegExp(`^["”“(«*]*[A-Z][\\p{L}\\p{N}_]+(?: [A-Z][\\p{L}\\p{N}_]+)?\\s+(?:was|is)\\s+(?:a|an|the)${E}`, "u"),
};

/** A gendered pronoun after a carver word: in the same sentence (within 12 words) an error, as the first word of the
 *  next sentence a warning. "Balle var en flitig ristare … han" (a named carver) is a warning. */
export function checkPronouns(text: string, sprak: "sv" | "en"): Finding[] {
  const out: Finding[] = [];
  const ss = sentences(prose(text));
  ss.forEach((s, i) => {
    const hits = [...s.matchAll(CARVER[sprak])];
    if (!hits.length) return;
    const named = NAMED_CARVER[sprak].test(s);
    let flagged = false;
    for (const h of hits) {
      const window = s.slice(h.index! + h[0].length).split(/\s+/).filter(Boolean).slice(0, PRONOUN_WINDOW).join(" ").replace(INCLUSIVE, "");
      const m = PRONOUN[sprak].exec(window);
      if (m) {
        out.push(finding(named ? "VARNING" : "FEL", "pronomen", sprak,
          `”${m[1]}” om en ristare; skriv ristaren/ristarens (the carver/the carver's)${named ? " – gäller en namngiven ristare" : ""}.`,
          excerpt(s, h.index)));
        flagged = true;
        break;
      }
    }
    const lead = i + 1 < ss.length ? LEAD_PRONOUN[sprak].exec(ss[i + 1]) : null;
    if (!flagged && lead) {
      out.push(finding("VARNING", "pronomen", sprak, `Nästa mening börjar med ”${lead[1]}” efter en ristare; gäller det ristaren?`,
        excerpt(ss[i + 1], 0)));
    }
  });
  return out;
}

const CAUSAL = {
  sv: new RegExp(`${B}(visar|visade|visat|bevisar|bevisade|bevisat|beror på|berodde på|berott på|orsakade|orsakar|orsakat)${E}`, "giu"),
  en: new RegExp(`${B}(shows?|showed|shown|proves?|proved|proven|(?:is|was|are|were) due to|caused|causes)${E}`, "giu"),
};
const FIGURE_SUBJECT = {
  sv: new RegExp(`${B}(kartan|kartorna|bilden|bilderna|figuren|diagrammet|grafen|stapeln|staplarna|tabellen|fotot|ritningen|exemplet|sidan|appen|Vitki|skärmbilden|rutan)\\s+\\S*\\s*$`, "iu"),
  en: new RegExp(`${B}(the map|maps|the picture|the figure|the chart|the graph|the bars?|the table|the photo|the drawing|the example|the page|the app|Vitki|the screenshot|the box)\\s+\\S*\\s*$`, "iu"),
};
const NOT_A_CLAIM = {
  sv: new RegExp(`(${B}(inte|ej|aldrig|kan|kunde|skulle)${E}\\s+(\\S+\\s+){0,4}|${B}det\\s+)$`, "iu"),
  en: new RegExp(`(${B}(not|no|never|cannot|can|could|would)${E}\\s+(\\S+\\s+){0,4}|n't\\s+(\\S+\\s+){0,4}|${B}to\\s+|${B}what\\s+(is|was)\\s+)$`, "iu"),
};
const STATS = {
  sv: new RegExp(`%|${B}procent|${B}p\\s*[=<≤]|${B}p-värde|signifikan|${B}samband|korrelation|${B}oddskvot|${B}odds${E}|slumpen|konfidensintervall|osäkerhetsintervall|${B}regression|gånger så|${B}medelvärde|${B}median`, "iu"),
  en: new RegExp(`%|${B}per ?cent|${B}p\\s*[=<≤]|${B}p-value|significan|${B}association|${B}correlat|${B}odds${E}|by chance|confidence interval|uncertainty interval|${B}regression|times as|${B}mean${E}|${B}median`, "iu"),
};

/** A causal or proof word in a sentence with a statistical result: tested is only an association. */
export function checkCausal(text: string, sprak: "sv" | "en"): Finding[] {
  const out: Finding[] = [];
  for (const s of sentences(prose(text))) {
    if (!STATS[sprak].test(s)) continue;
    for (const m of s.matchAll(CAUSAL[sprak])) {
      const before = s.slice(0, m.index);
      if (FIGURE_SUBJECT[sprak].test(before) || NOT_A_CLAIM[sprak].test(before)) continue;
      out.push(finding("VARNING", "orsak", sprak, `”${m[1]}” i en mening med statistik: prövat är ett samband, inte en orsak eller ett bevis.`,
        excerpt(s, m.index)));
      break;
    }
  }
  return out;
}

const NUMBER = new RegExp(`(?<![\\p{L}\\p{N}_,.])\\d+(?:[ \\u00a0\\u202f]\\d{3})*(?:[,.]\\d+)?(?!${W})`, "gu");

function normaliseNumber(raw: string, sprak: "sv" | "en"): string {
  let s = raw.replace(/[   ]/g, "");
  s = sprak === "sv" ? s.replace(/,/g, ".") : s.replace(/,(?=\d{3}(?!\d))/g, "");
  return s.replace(/\.+$/, "");
}

export function numbers(text: string, sprak: "sv" | "en"): Set<string> {
  const t = sprak === "en" ? text.replace(/(?<=\d),(?=\d{3}(?!\d))/g, "") : text;
  return new Set([...t.matchAll(NUMBER)].map(m => normaliseNumber(m[0], sprak)));
}

/** A round number in the box ("över 1 300") that rounds one in the text (1 352): within a tenth of it. */
function rounded(n: string, body: Set<string>): boolean {
  const v = Number(n);
  if (!Number.isFinite(v) || v < 100 || v % 10) return false;
  for (const b of body) {
    const w = Number(b);
    if (Number.isFinite(w) && w && Math.abs(w - v) / w <= 0.1) return true;
  }
  return false;
}

const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function boxOf(text: string, sprak: "sv" | "en"): [string, string] | null {
  const m = new RegExp(`^:::box\\s+${escape(BOX[sprak])}\\s*$`, "mi").exec(text ?? "");
  if (!m) return null;
  const startBody = m.index + m[0].length;
  const end = /^:::\s*$/m.exec(text.slice(startBody));
  const stop = startBody + (end ? end.index : text.length - startBody);
  return [text.slice(startBody, stop), text.slice(0, m.index) + text.slice(stop)];
}

export function needsBox(post: LintPost, body: string): boolean {
  const labels = post.labels ?? [];
  if (labels.includes("Personligt") || labels.includes("Rapport") || (post.title ?? "").startsWith("De gamla landen")) return false;
  return [...(body ?? "")].length >= KORTHET_MIN_CHARS;
}

function checkBox(post: LintPost, body: string, sprak: "sv" | "en"): Finding[] {
  const got = boxOf(body, sprak);
  if (!got) return needsBox(post, body) ? [finding("FEL", "korthet_saknas", sprak, `Rutan ”:::box ${BOX[sprak]}” saknas.`)] : [];
  const [box, rest] = got;
  const bodyNumbers = numbers(visible(rest), sprak);
  const missing = [...numbers(box, sprak)].filter(n => !bodyNumbers.has(n) && !rounded(n, bodyNumbers))
    .sort((a, b) => a.length - b.length || (a < b ? -1 : a > b ? 1 : 0));
  return missing.length
    ? [finding("FEL", "korthet_tal", sprak, `Rutan ”Det viktigaste i korthet” har tal som inte står i brödtexten: ${missing.join(", ")}.`, box.trim())]
    : [];
}

function checkSeo(post: LintPost): Finding[] {
  const out: Finding[] = [];
  for (const [key, titleKey, sprak] of [["seo_title", "title", "sv"], ["seo_title_en", "title_en", "en"]] as const) {
    const seo = (post[key] ?? "").trim();
    const title = (post[titleKey] ?? "").trim();
    const n = [...seo].length, nt = [...title].length;
    if (seo && n > SEO_MAX) out.push(finding("FEL", "seo_titel", sprak, `${key} har ${n} tecken; högst ${SEO_MAX}.`, seo));
    else if (!seo && title && nt > SEO_MAX) {
      out.push(finding("VARNING", "seo_titel", sprak, `Ingen ${key}, och rubriken har ${nt} tecken (över ${SEO_MAX}); sökmotorerna kortar den.`, title));
    }
  }
  return out;
}

// ---- links ---------------------------------------------------------------------------------------------------------

const INTERNAL = /^(?:https?:\/\/(?:www\.)?vitkirunor\.se)?\/(en\/)?(artiklar|forskningsrapporter)\/([A-Za-z0-9_.-]+)\/?(?:[#?].*)?$/;

const when = (v: Date | string | null | undefined): Date | null => {
  if (!v) return null;
  const d = v instanceof Date ? v : new Date(v);
  return Number.isNaN(d.getTime()) ? null : d;
};
const stockholmDay = (d: Date) => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Stockholm", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);

export function checkLinks(body: string, sprak: "sv" | "en", posts: LinkTarget[], publishAt: Date | null, now: Date, selfSlug = ""): Finding[] {
  const bySlug = new Map(posts.filter(p => p.slug).map(p => [p.slug, p]));
  const out: Finding[] = [];
  const seen = new Set<string>();
  for (const m of (body ?? "").matchAll(LINK_TARGET)) {
    const target = m[1];
    const lm = INTERNAL.exec(target);
    if (!lm) continue;
    const [, en, section, slug] = lm;
    const k = `${slug}|${en ?? ""}`;
    if (SITE_ROUTES[section].has(slug) || slug === selfSlug || seen.has(k)) continue;
    seen.add(k);
    const p = bySlug.get(slug);
    if (!p) { out.push(finding("FEL", "lank_okand", sprak, `Länken går till en artikel som inte finns: ${target}`, target)); continue; }
    const live = when(p.publishedAt);
    if (!p.published) out.push(finding("FEL", "lank_opublicerad", sprak, `Länken går till ett opublicerat utkast: ${target}`, target));
    else if (live && live > now && (!publishAt || live > publishAt)) {
      out.push(finding("FEL", "lank_opublicerad", sprak, `Länken går till en artikel som publiceras först ${stockholmDay(live)}, efter den här: ${target}`, target));
    }
    if (en && p.hasEnglish === false) out.push(finding("VARNING", "lank_okand", sprak, `Länken går till den engelska utgåvan, som saknas: ${target}`, target));
  }
  return out;
}

// ---- the whole article ---------------------------------------------------------------------------------------------

/** All findings for one article, apart from the journal page check. posts: every article, for the link check (without
 *  it links are not checked); publishAt: when this article goes out. */
export function lintArticle(post: LintPost, posts: LinkTarget[] | null, publishAt: Date | null, now: Date): Finding[] {
  const out: Finding[] = [];
  const at = publishAt ?? (post.published ? when(post.publishedAt) : null);
  for (const [sprak, sfx] of [["sv", ""], ["en", "_en"]] as const) {
    const body = (sfx ? post.body_en : post.body) ?? "";
    if (sprak === "en" && !body.trim()) continue;
    const fields = {
      rubrik: (sfx ? post.title_en : post.title) ?? "", ingress: (sfx ? post.summary_en : post.summary) ?? "",
      "söktitel": (sfx ? post.seo_title_en : post.seo_title) ?? "", text: body,
    };
    out.push(...checkPlaceholders(fields, sprak), ...checkAi(fields, sprak), ...checkPronouns(body, sprak),
      ...checkCausal(body, sprak), ...checkBox(post, body, sprak));
    if (posts) out.push(...checkLinks(body, sprak, posts, at, now, post.slug ?? ""));
  }
  out.push(...checkSeo(post));
  return out;
}

export function lintSummary(findings: Finding[]): { fel: number; varningar: number } {
  const fel = findings.filter(f => f.niva === "FEL").length;
  return { fel, varningar: findings.length - fel };
}
