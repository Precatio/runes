// The research reports (label "Rapport"): confirmed findings in the fixed, locked form of utdata/rapporter/MALL.md,
// shown in their own section (/forskningsrapporter) and laid out as an academic paper rather than as an article. The text is the
// same markdown as an article's; this module reads the paper's parts out of it: the header line (author, report
// version, Vitki version, licence, citation, keywords), the abstract, the highlights box and the numbered sections.
import type { BlogPost } from "@/components/BlogBody";
import { plainText } from "@/lib/blogSeo";
import { PUBLIC_SITE, SITE_NAME, SITE_URL } from "@/lib/site";

export const REPORT_LABEL = "Rapport";
/** Whether a post is a research report. */
export const isReport = (p: Pick<BlogPost, "labels">) => (p.labels ?? []).includes(REPORT_LABEL);

const SLASH = PUBLIC_SITE ? "/" : "";
export const REPORTS_PATH = `/forskningsrapporter${SLASH}`;
export const EN_REPORTS_PATH = `/en/forskningsrapporter${SLASH}`;
export const reportPath = (slug: string) => `/forskningsrapporter/${encodeURIComponent(slug)}${SLASH}`;
export const enReportPath = (slug: string) => `/en/forskningsrapporter/${encodeURIComponent(slug)}${SLASH}`;
export const reportUrl = (slug: string) => `${SITE_URL}${reportPath(slug)}`;
export const enReportUrl = (slug: string) => `${SITE_URL}${enReportPath(slug)}`;
export const reportSharePath = (slug: string) => `/forskningsrapporter/${encodeURIComponent(slug)}/delningsbild.png`;
export const reportAlternates = (slug?: string) => ({
  sv: slug ? reportPath(slug) : REPORTS_PATH,
  en: slug ? enReportPath(slug) : EN_REPORTS_PATH,
  "x-default": slug ? reportPath(slug) : REPORTS_PATH,
});

export const REPORTS_TITLE = "Forskningsrapporter";
export const REPORTS_TITLE_EN = "Research reports";
export const REPORTS_DESCRIPTION = "Prövade fynd och metoder ur Vitkis analyser av Sveriges runstenar, i vetenskaplig form: förregistrering, "
  + "material, metod, resultat, diskussion och referenser – märkta efter hur hårt de prövats, med version och citering.";
export const REPORTS_DESCRIPTION_EN = "Tested findings and methods from Vitki's analyses of Sweden's runestones, in scholarly form: "
  + "pre-registration, material, method, results, discussion and references – marked by how thoroughly they were tested, with version and citation.";

/** The report's form and level (utdata/rapporter/MALL.md, version 2), written right after the author sentence in the
 *  header line. A report without it was built on version 1 of the template and is a fully tested finding. */
export interface ReportForm { key: "full" | "partial" | "method-full" | "method-partial" | "data"; sv: string; en: string; rank: number;
  group: { sv: string; en: string } }
const GROUPS = {
  full: { sv: "Fullt prövade fynd", en: "Fully tested findings" },
  partial: { sv: "Delvis prövade fynd", en: "Partially tested findings" },
  method: { sv: "Metodrapporter", en: "Methods reports" },
  data: { sv: "Datanotiser", en: "Data notes" },
};
export const REPORT_FORMS: ReportForm[] = [
  { key: "full", sv: "Fullt prövat fynd", en: "Fully tested finding", rank: 0, group: GROUPS.full },
  { key: "partial", sv: "Delvis prövat fynd", en: "Partially tested finding", rank: 1, group: GROUPS.partial },
  { key: "method-full", sv: "Metodrapport, fullt prövad", en: "Methods report, fully tested", rank: 2, group: GROUPS.method },
  { key: "method-partial", sv: "Metodrapport, delvis prövad", en: "Methods report, partially tested", rank: 2, group: GROUPS.method },
  { key: "data", sv: "Datanotis", en: "Data note", rank: 3, group: GROUPS.data },
];
const FORM_RE = new RegExp(`(?:^|\\.\\s)(${REPORT_FORMS.flatMap(f => [f.sv, f.en]).map(x => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\.`);
/** The form named in a header line (the first sentence after the author), or a fully tested finding. */
export function parseForm(line: string): ReportForm {
  const m = FORM_RE.exec(line.replace(/^\*|\*$/g, ""));
  return REPORT_FORMS.find(f => m && (f.sv === m[1] || f.en === m[1])) ?? REPORT_FORMS[0];
}

export interface ReportHeader {
  author: string;
  affiliation: string;
  form: ReportForm;
  version: string | null;
  date: string | null;
  appVersion: string | null;
  licence: string | null;
  citation: string | null;
  keywords: string[];
  competing: string | null;
  funding: string | null;
}

export interface ReportSection { id: string; title: string; md: string; numbered: boolean }

export interface ReportParts {
  header: ReportHeader | null;
  /** The header line as written, when it could not be read (shown as it stands). */
  headerRaw: string | null;
  abstract: string | null;
  abstractTitle: string;
  highlights: { title: string; md: string } | null;
  sections: ReportSection[];
}

const pick = (re: RegExp, s: string) => re.exec(s)?.[1]?.trim() ?? null;

/** The header line: "*Viktor Kvant, oberoende forskare. Rapportversion 1, 2026-10-31. Analysen är gjord i Vitki 3.0.0.
 *  Licens CC BY 4.0. … citering: <citation>. Nyckelord: a, b. Konkurrerande intressen: inga. Finansiering: ingen.*" */
export function parseHeader(line: string): ReportHeader | null {
  const s = line.replace(/^\*|\*$/g, "").trim();
  const who = /^([^,]+),\s*([^.]+)\./.exec(s);
  if (!who) return null;
  const v = /(?:Rapportversion|Report version)\s+(\d+),\s*(\d{4}-\d{2}-\d{2})/.exec(s);
  const kw = pick(/(?:Nyckelord|Keywords):\s*(.+?)\.\s*(?:Konkurrerande intressen|Competing interests|$)/, s);
  return {
    author: who[1].trim(),
    affiliation: who[2].trim(),
    form: parseForm(s),
    version: v?.[1] ?? null,
    date: v?.[2] ?? null,
    appVersion: pick(/Vitki\s+(\d+\.\d+\.\d+)/, s),
    licence: pick(/(?:Licens|Licence)\s+(CC[ A-Z-]*\d\.\d)/, s),
    citation: pick(/(?:för citering|for citation):\s*(.+?)\.\s*(?:Nyckelord|Keywords):/, s),
    keywords: kw ? kw.split(/,\s*/).filter(Boolean) : [],
    competing: pick(/(?:Konkurrerande intressen|Competing interests):\s*([^.]+)\./, s),
    funding: pick(/(?:Finansiering|Funding):\s*([^.]+)\./, s),
  };
}

/** A heading's anchor: "1. Inledning" → "inledning", "5.1 …" kept unique by the caller. */
const anchor = (t: string) => t.toLowerCase().replace(/^\d+(\.\d+)*\.?\s*/, "").normalize("NFKD").replace(/[̀-ͯ]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "avsnitt";

const ABSTRACT = /^(Sammanfattning|Abstract)$/;
const HIGHLIGHTS = /^:::box (Det viktigaste i korthet|The essentials(?: in brief)?)\s*$/m;

/** The paper's parts, read out of the report's markdown. */
export function reportParts(md: string): ReportParts {
  let text = md.replace(/\r\n/g, "\n").trim();
  // The highlights box ("Det viktigaste i korthet") is lifted out and shown after the abstract, as papers do
  let highlights: ReportParts["highlights"] = null;
  const hb = HIGHLIGHTS.exec(text);
  if (hb) {
    const start = hb.index, inner = start + hb[0].length + 1;
    const end = text.indexOf("\n:::", inner - 1);
    if (end >= 0) {
      highlights = { title: hb[1], md: text.slice(inner, end).trim() };
      text = (text.slice(0, start) + text.slice(end + 4)).trim();
    }
  }
  // The header line: the first paragraph, in italics, before the first heading
  let header: ReportHeader | null = null, headerRaw: string | null = null;
  const first = text.split(/\n\s*\n/)[0] ?? "";
  if (/^\*[^*][\s\S]*\*$/.test(first.trim()) && !first.startsWith("## ")) {
    header = parseHeader(first.trim());
    if (!header) headerRaw = first.trim();
    text = text.slice(first.length).trim();
  }
  // The sections, split at "## " outside the :::box/:::chart blocks
  const lines = text.split("\n");
  const sections: { title: string; body: string[] }[] = [];
  let inBlock = false;
  let cur: { title: string; body: string[] } = { title: "", body: [] };
  for (const l of lines) {
    if (/^:::(box|chart)\b/.test(l.trim())) inBlock = true;
    else if (l.trim() === ":::") inBlock = false;
    if (!inBlock && l.startsWith("## ")) {
      if (cur.title || cur.body.join("").trim()) sections.push(cur);
      cur = { title: l.slice(3).trim(), body: [] };
    } else cur.body.push(l);
  }
  if (cur.title || cur.body.join("").trim()) sections.push(cur);
  let abstract: string | null = null, abstractTitle = "Sammanfattning";
  const seen = new Set<string>();
  const out: ReportSection[] = [];
  for (const s of sections) {
    const md2 = s.body.join("\n").trim();
    if (ABSTRACT.test(s.title) && abstract === null) { abstract = md2; abstractTitle = s.title; continue; }
    let id = anchor(s.title);
    while (seen.has(id)) id += "-2";
    seen.add(id);
    out.push({ id, title: s.title, md: md2, numbered: /^\d/.test(s.title) });
  }
  return { header, headerRaw, abstract, abstractTitle, highlights, sections: out };
}

/** "2026-10-31" → "2026/10/31", the date form the Highwire Press tags (Google Scholar) ask for. */
const scholarDate = (iso: string | null | undefined) => (iso ? iso.slice(0, 10).replace(/-/g, "/") : undefined);

/** The <meta name="citation_…"> tags that Google Scholar reads (Highwire Press), for generateMetadata's `other`. */
export function scholarMeta(post: BlogPost, lang: "sv" | "en"): Record<string, string | string[]> {
  const en = lang === "en";
  const parts = reportParts((en ? post.body_en : post.body) ?? "");
  const h = parts.header;
  const published = post.publishedAt ?? h?.date ?? undefined;
  const meta: Record<string, string | string[]> = {
    citation_title: (en && post.title_en) || post.title,
    citation_author: "Kvant, Viktor",
    citation_language: en ? "en" : "sv",
    citation_publisher: SITE_NAME,
    citation_technical_report_institution: SITE_NAME,
    citation_fulltext_html_url: en ? enReportUrl(post.slug) : reportUrl(post.slug),
    citation_abstract_html_url: en ? enReportUrl(post.slug) : reportUrl(post.slug),
  };
  const d = scholarDate(published);
  if (d) { meta.citation_publication_date = d; meta.citation_online_date = d; }
  if (h?.keywords.length) meta.citation_keywords = h.keywords.join("; ");
  if (h?.version) meta.citation_technical_report_number = `${en ? "Report version" : "Rapportversion"} ${h.version}`;
  const refs = references(parts);
  if (refs.length) meta.citation_reference = refs;
  return meta;
}

/** The reference list, one plain-text entry per "- " line of the references section. */
export function references(parts: ReportParts): string[] {
  const s = parts.sections.find(x => /^(Referenser|References)$/.test(x.title));
  return s ? s.md.split("\n").filter(l => l.startsWith("- ")).map(l => plainText(l.slice(2))) : [];
}

/** The citation in BibTeX, for the "Cite" box. */
export function bibtex(post: BlogPost, h: ReportHeader | null): string {
  const year = (h?.date ?? post.publishedAt ?? "").slice(0, 4) || new Date().getFullYear().toString();
  const key = `kvant${year}${post.slug.split("-").slice(0, 3).join("")}`.replace(/[^a-z0-9]/gi, "");
  const title = post.title_en || post.title;
  return [
    `@techreport{${key},`,
    `  author      = {Kvant, Viktor},`,
    `  title       = {${title}},`,
    `  institution = {Vitki},`,
    `  type        = {Research report},`,
    `  number      = {Report version ${h?.version ?? "1"}},`,
    `  year        = {${year}},`,
    `  url         = {${enReportUrl(post.slug)}},`,
    `  note        = {Analysis in Vitki ${h?.appVersion ?? ""}. Swedish edition: ${reportUrl(post.slug)}}`,
    `}`,
  ].join("\n");
}

/** schema.org ScholarlyArticle + Report and the breadcrumb, for the report page (JSON-LD). */
export function reportJsonLd(post: BlogPost, lang: "sv" | "en" = "sv") {
  const en = lang === "en";
  const url = en ? enReportUrl(post.slug) : reportUrl(post.slug);
  const parts = reportParts((en ? post.body_en : post.body) ?? "");
  const h = parts.header;
  const published = post.publishedAt ?? h?.date ?? undefined;
  const title = (en && post.title_en) || post.title;
  return [
    {
      "@context": "https://schema.org",
      "@type": ["ScholarlyArticle", "Report"],
      headline: title.slice(0, 110),
      name: title,
      ...(post.title_en && !en ? { alternativeHeadline: post.title_en } : {}),
      abstract: parts.abstract ? plainText(parts.abstract) : plainText((en ? post.summary_en : post.summary) ?? ""),
      description: plainText((en ? post.summary_en : post.summary) ?? ""),
      author: { "@type": "Person", "@id": `${SITE_URL}/#founder`, name: h?.author ?? "Viktor Kvant",
                ...(h?.affiliation ? { affiliation: h.affiliation } : {}) },
      publisher: { "@type": "Organization", "@id": `${SITE_URL}/#organization`, name: SITE_NAME, url: SITE_URL },
      datePublished: published,
      dateModified: post.updatedAt ?? published,
      ...(h?.version ? { version: h.version, reportNumber: `${en ? "Report version" : "Rapportversion"} ${h.version}` } : {}),
      ...(h?.keywords.length ? { keywords: h.keywords.join(", ") } : {}),
      license: "https://creativecommons.org/licenses/by/4.0/",
      isAccessibleForFree: true,
      inLanguage: en ? "en" : "sv-SE",
      genre: (h?.form ?? REPORT_FORMS[0]).en,
      isPartOf: { "@type": "CreativeWorkSeries", name: en ? `${SITE_NAME} – ${REPORTS_TITLE_EN}` : `${SITE_NAME} – ${REPORTS_TITLE}`,
                  url: `${SITE_URL}${en ? EN_REPORTS_PATH : REPORTS_PATH}` },
      url,
      mainEntityOfPage: { "@type": "WebPage", "@id": url },
      citation: references(parts),
      about: [{ "@type": "Thing", name: "Runstenar" }, { "@type": "Thing", name: "Runinskrifter" }],
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: SITE_NAME, item: SITE_URL },
        { "@type": "ListItem", position: 2, name: en ? REPORTS_TITLE_EN : REPORTS_TITLE, item: `${SITE_URL}${en ? EN_REPORTS_PATH : REPORTS_PATH}` },
        { "@type": "ListItem", position: 3, name: title, item: url },
      ],
    },
  ];
}

/** schema.org CollectionPage with the reports as an ItemList, for the list page (JSON-LD). */
export function reportsJsonLd(posts: BlogPost[], lang: "sv" | "en" = "sv") {
  const en = lang === "en";
  const url = `${SITE_URL}${en ? EN_REPORTS_PATH : REPORTS_PATH}`;
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: en ? `${REPORTS_TITLE_EN} – ${SITE_NAME}` : `${REPORTS_TITLE} – ${SITE_NAME}`,
    description: en ? REPORTS_DESCRIPTION_EN : REPORTS_DESCRIPTION,
    url,
    inLanguage: en ? "en" : "sv-SE",
    isPartOf: { "@type": "WebSite", "@id": `${SITE_URL}/#website`, name: SITE_NAME, url: SITE_URL },
    publisher: { "@type": "Organization", "@id": `${SITE_URL}/#organization`, name: SITE_NAME, url: SITE_URL },
    about: [{ "@type": "Thing", name: "Runstenar" }, { "@type": "Thing", name: "Runinskrifter" }, { "@type": "Thing", name: "Runologi" }],
    mainEntity: {
      "@type": "ItemList",
      itemListElement: posts.map((p, i) => ({
        "@type": "ListItem", position: i + 1,
        item: { "@type": ["ScholarlyArticle", "Report"], name: (en && p.title_en) || p.title,
                url: en ? enReportUrl(p.slug) : reportUrl(p.slug), datePublished: p.publishedAt ?? undefined,
                author: { "@type": "Person", "@id": `${SITE_URL}/#founder`, name: "Viktor Kvant" },
                description: plainText((en ? p.summary_en : p.summary) ?? "") },
      })),
    },
  };
}
