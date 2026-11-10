import data from "../../content/korpus.json";
import { PUBLIC_SITE, SITE_URL } from "@/lib/site";

// Vitki's journal Korpus – Ristat & räknat (web/content/korpus.json): one entry per issue, the PDFs and covers in
// web/public/korpus/ (built by utdata/tidskrift/bygg_tidskrift.py). Shown at /tidskrift and /en/tidskrift (the app
// already has /korpus, the shared measurement corpus).
export interface KorpusItem { theme_sv: string; theme_en: string; title_sv: string; title_en: string; slug?: string }
export interface KorpusIssue {
  nr: number; date: string; label_sv: string; label_en: string; pages: number;
  pdf_sv: string; pdf_en: string; size_sv: string; size_en: string;
  cover_sv: string; cover_en: string; cover_alt_sv: string; cover_alt_en: string; cover_credit_sv: string; cover_credit_en: string;
  lead_sv: string; lead_en: string; contents: KorpusItem[];
}

export const KORPUS_ISSUES: KorpusIssue[] = [...(data.issues as KorpusIssue[])].sort((a, b) => b.date.localeCompare(a.date));

const SLASH = PUBLIC_SITE ? "/" : "";
export const KORPUS_PATH = `/tidskrift${SLASH}`;
export const EN_KORPUS_PATH = `/en/tidskrift${SLASH}`;
export const korpusAlternates = { sv: KORPUS_PATH, en: EN_KORPUS_PATH, "x-default": KORPUS_PATH };

export const KORPUS_TITLE = { sv: "Korpus – Ristat & räknat · Vitkis tidskrift", en: "Korpus – Carved & counted · Vitki's journal" };
export const KORPUS_DESCRIPTION = {
  sv: "Korpus är Vitkis tidskrift för digital runforskning: hela runstenskorpusen mätt mot jord, vatten, ortnamn och slumpen. Fri som PDF på svenska och engelska.",
  en: "Korpus is Vitki's journal of digital runic research: the whole runestone corpus measured against soil, water, place names and chance. Free as a PDF in Swedish and English.",
};

/** schema.org: the journal as a Periodical, each issue a PublicationIssue with its PDF in both languages. */
export function korpusJsonLd(lang: "sv" | "en") {
  const url = `${SITE_URL}${lang === "en" ? EN_KORPUS_PATH : KORPUS_PATH}`;
  return {
    "@context": "https://schema.org",
    "@type": "Periodical",
    "@id": `${SITE_URL}/tidskrift/#korpus`,
    name: "Korpus",
    alternateName: lang === "en" ? "Korpus – Carved & counted" : "Korpus – Ristat & räknat",
    description: KORPUS_DESCRIPTION[lang],
    url,
    inLanguage: ["sv", "en"],
    publisher: { "@type": "Organization", name: "Vitki", url: SITE_URL },
    editor: { "@type": "Person", name: "Viktor Kvant", "@id": `${SITE_URL}/#founder` },
    license: "https://creativecommons.org/licenses/by/4.0/",
    hasPart: KORPUS_ISSUES.map((i) => ({
      "@type": "PublicationIssue",
      issueNumber: String(i.nr),
      datePublished: i.date,
      name: lang === "en" ? i.label_en : i.label_sv,
      image: `${SITE_URL}${lang === "en" ? i.cover_en : i.cover_sv}`,
      encoding: [
        { "@type": "MediaObject", encodingFormat: "application/pdf", inLanguage: "sv", contentUrl: `${SITE_URL}${i.pdf_sv}` },
        { "@type": "MediaObject", encodingFormat: "application/pdf", inLanguage: "en", contentUrl: `${SITE_URL}${i.pdf_en}` },
      ],
    })),
  };
}
