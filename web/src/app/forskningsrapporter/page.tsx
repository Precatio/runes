import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import ReportList from "@/components/ReportList";
import EnglishEdition from "@/components/EnglishEdition";
import { getPost, listReports } from "@/lib/articles";
import type { BlogPost } from "@/components/BlogBody";
import { ARTICLES_PATH } from "@/lib/blogSeo";
import { EN_REPORTS_PATH, REPORTS_DESCRIPTION, REPORTS_PATH, REPORTS_TITLE, reportAlternates, reportsJsonLd } from "@/lib/report";

// The research reports: confirmed findings in the locked scholarly form (utdata/rapporter/MALL.md), each laid out as a
// paper (components/ReportPaper.tsx). Rendered on the server, like the articles.
export const revalidate = 60;

const TITLE = "Forskningsrapporter om runstenar – forskningsresultat ur Vitki";

export const metadata: Metadata = {
  title: TITLE,
  description: REPORTS_DESCRIPTION,
  keywords: ["forskningsrapporter", "forskningsresultat", "runstenar", "runinskrifter", "runologi", "vikingatiden", "förregistrering", "statistik", "Rundata"],
  alternates: { canonical: REPORTS_PATH, languages: reportAlternates() },
  openGraph: { type: "website", url: REPORTS_PATH, title: TITLE, description: REPORTS_DESCRIPTION, siteName: "Vitki", locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: REPORTS_TITLE }] },
  twitter: { card: "summary_large_image", title: TITLE, description: REPORTS_DESCRIPTION, images: ["/delningsbild.png"] },
};

export default async function ReportsPage() {
  const list = await listReports();
  // with their texts, for the version and the keywords in the header line (a handful of reports)
  const posts = (await Promise.all(list.posts.map(p => getPost(p.slug)))).filter(Boolean) as BlogPost[];
  return (
    <BlogShell>
      <EnglishEdition href={EN_REPORTS_PATH} />
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-24">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">{REPORTS_TITLE}</div>
          <Link href={EN_REPORTS_PATH} hrefLang="en" className="tap text-sm text-[#b7410e] font-semibold hover:underline">In English →</Link>
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Forskningsresultat ur runstenarna</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Här står de fynd ur Vitkis analyser som har klarat alla kontroller: de håller i båda halvorna av materialet, i en
          fast serie känslighetsanalyser och i en justering för alla samband vi prövar. Varje rapport följer samma
          vetenskapliga form – förregistrering, material, metod, resultat, diskussion och referenser – och anger sin version
          och hur den citeras.
        </p>
        <p className="mt-3 text-sm text-slate-500">
          Populärvetenskapliga texter om samma mönster finns under <Link href={ARTICLES_PATH} prefetch={false} className="font-semibold text-[#b7410e] hover:underline">Artiklar</Link>.
        </p>
        <ReportList posts={posts} lang="sv" />
      </section>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(reportsJsonLd(posts, "sv")).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
