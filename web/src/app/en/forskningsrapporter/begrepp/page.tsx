import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import ReportTermList, { termsJsonLd } from "@/components/ReportTermList";
import { EN_REPORTS_PATH, EN_TERMS_PATH, TERMS_PATH } from "@/lib/report";
import { SITE_URL } from "@/lib/site";

// The English glossary of the research reports' statistical terms (lib/reportTerms.ts).
const TITLE = "Statistical terms in the research reports – explained in plain words";
const DESCRIPTION = "What p-value, odds ratio, 95 % interval, random effect, Holm correction, the halves, sensitivity analyses, "
  + "pre-registration, cross-validation and blind test mean in Vitki's research reports on the runestones, and how to read the numbers.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: ["statistical terms", "glossary", "p-value", "odds ratio", "confidence interval", "random effect", "pre-registration", "runology", "runestones"],
  alternates: { canonical: EN_TERMS_PATH, languages: { sv: TERMS_PATH, en: EN_TERMS_PATH, "x-default": TERMS_PATH } },
  openGraph: { type: "website", url: EN_TERMS_PATH, title: TITLE, description: DESCRIPTION, siteName: "Vitki", locale: "en_GB",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: "Statistical terms" }] },
};

export default function EnglishTermsPage() {
  return (
    <BlogShell lang="en">
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24" lang="en">
        <div className="flex items-center justify-between gap-4 mb-3">
          <Link href={EN_REPORTS_PATH} prefetch={false} className="tap text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] hover:underline">← Research reports</Link>
          <Link href={TERMS_PATH} hrefLang="sv" className="tap text-sm text-[#b7410e] font-semibold hover:underline">På svenska →</Link>
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Statistical terms in the reports</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          The research reports use a small number of statistical terms again and again. Here they are explained in plain
          words: what the term is and how to read the number. Each report also states its main result in plain words.
        </p>
        <ReportTermList lang="en" />
      </section>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(termsJsonLd("en", `${SITE_URL}${EN_TERMS_PATH}`, TITLE)).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
