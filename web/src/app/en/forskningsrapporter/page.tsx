import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import ReportList from "@/components/ReportList";
import { getPost, listReports } from "@/lib/articles";
import type { BlogPost } from "@/components/BlogBody";
import { EN_ARTICLES_PATH } from "@/lib/blogSeo";
import { EN_REPORTS_PATH, REPORTS_DESCRIPTION_EN, REPORTS_PATH, REPORTS_TITLE_EN, reportAlternates, reportsJsonLd } from "@/lib/report";

// The English list of the research reports (the reports' own English versions)
export const revalidate = 60;

const TITLE = "Research reports on runestones – research findings from Vitki";

export const metadata: Metadata = {
  title: TITLE,
  description: REPORTS_DESCRIPTION_EN,
  keywords: ["research reports", "research findings", "runestones", "runic inscriptions", "runology", "Viking Age", "pre-registration", "statistics", "Rundata"],
  alternates: { canonical: EN_REPORTS_PATH, languages: reportAlternates() },
  openGraph: { type: "website", url: EN_REPORTS_PATH, title: TITLE, description: REPORTS_DESCRIPTION_EN, siteName: "Vitki", locale: "en_GB",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: REPORTS_TITLE_EN }] },
  twitter: { card: "summary_large_image", title: TITLE, description: REPORTS_DESCRIPTION_EN, images: ["/delningsbild.png"] },
};

export default async function EnglishReportsPage() {
  const list = await listReports();
  const posts = (await Promise.all(list.posts.filter(p => p.title_en).map(p => getPost(p.slug)))).filter(Boolean) as BlogPost[];
  return (
    <BlogShell lang="en">
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-24" lang="en">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">{REPORTS_TITLE_EN}</div>
          <Link href={REPORTS_PATH} hrefLang="sv" className="tap text-sm text-[#b7410e] font-semibold hover:underline">På svenska →</Link>
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Research findings from the runestones</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          These are the findings and methods from Vitki&apos;s analyses that have been tested by fixed rules, marked by how
          thoroughly. A fully tested finding holds in both halves of the material, in a fixed series of sensitivity analyses
          and in an adjustment for all the associations we test. A partially tested finding holds in both halves and after
          the adjustment, but not in every sensitivity analysis; what is missing is stated first in the abstract. A methods
          report tests a method in a blind test locked in advance. Each report follows the same scholarly form –
          pre-registration, material, method, results, discussion and references – and states its version and how to cite it.
        </p>
        <p className="mt-3 text-sm text-slate-500">
          Popular-science texts on the same patterns are under <Link href={EN_ARTICLES_PATH} prefetch={false} className="font-semibold text-[#b7410e] hover:underline">Articles</Link>.
        </p>
        <ReportList posts={posts} lang="en" />
      </section>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(reportsJsonLd(posts, "en")).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
