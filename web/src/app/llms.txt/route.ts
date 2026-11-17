import { listPosts, listReports } from "@/lib/articles";
import { enPostUrl, postUrl } from "@/lib/blogSeo";
import { enReportUrl, reportUrl } from "@/lib/report";
import { KORPUS_PATH } from "@/lib/korpus";
import { GITHUB_URL, METHODS_URL, SITE_DESCRIPTION, SITE_URL } from "@/lib/site";

// /llms.txt (llmstxt.org): a plain-text map of the site for language-model tools (ChatGPT, Gemini, Perplexity, Claude)
// that read it. Google says its own search needs no such file; the sitemap and the pages themselves are what count, so
// this only lists what is already public: every published article and research report with its summary.
export const dynamic = "force-static";

const line = (title: string, url: string, summary?: string | null) =>
  `- [${title}](${url})${summary ? `: ${summary.replace(/\s+/g, " ").trim()}` : ""}`;

export async function GET() {
  const [{ posts }, { posts: reports }] = await Promise.all([listPosts(), listReports()]);
  const text = [
    "# Vitki – runstenar och runinskrifter",
    "",
    `> ${SITE_DESCRIPTION} Vitki mäter Sveriges runinskrifter statistiskt (Samnordisk runtextdatabas, Riksantikvarieämbetets Runor, ` +
      "Sveriges runinskrifter) och i 3D-skanningar av huggspåren. Varje studie följer en analysplan som låses innan något räknas.",
    "",
    "Vitki is an open research platform for the runestones and runic inscriptions of Sweden and the Viking Age. Articles are " +
      "written in Swedish with English versions; research reports are citable with a DOI.",
    "",
    "## Forskningsrapporter / Research reports",
    "",
    ...reports.flatMap(p => [
      line(p.title, reportUrl(p.slug), p.summary),
      ...(p.title_en ? [line(p.title_en, enReportUrl(p.slug), p.summary_en)] : []),
    ]),
    "",
    "## Artiklar (svenska)",
    "",
    ...posts.map(p => line(p.title, postUrl(p.slug), p.summary)),
    "",
    "## Articles (English)",
    "",
    ...posts.filter(p => p.title_en).map(p => line(p.title_en as string, enPostUrl(p.slug), p.summary_en)),
    "",
    "## Optional",
    "",
    line("Korpus – Vitkis tidskrift", `${SITE_URL}${KORPUS_PATH}`),
    line("Metoder (METHODS.md)", METHODS_URL),
    line("Källkod och data (GitHub)", GITHUB_URL),
    "",
  ].join("\n");
  return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
}
