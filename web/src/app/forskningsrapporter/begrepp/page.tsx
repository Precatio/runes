import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import ReportTermList, { termsJsonLd } from "@/components/ReportTermList";
import EnglishEdition from "@/components/EnglishEdition";
import { EN_TERMS_PATH, REPORTS_PATH, TERMS_PATH } from "@/lib/report";
import { SITE_URL } from "@/lib/site";

// The statistical terms of the research reports in plain words (lib/reportTerms.ts), linked from every report.
const TITLE = "Statistiska begrepp i forskningsrapporterna – förklarade i vanliga ord";
const DESCRIPTION = "Vad p-värde, oddskvot, 95 %-intervall, slumpeffekt, Holm-korrigering, halvorna, känslighetsanalyser, "
  + "förregistrering, korsvalidering och blindprov betyder i Vitkis forskningsrapporter om runstenarna, och hur siffrorna ska läsas.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: ["statistiska begrepp", "ordlista", "p-värde", "oddskvot", "konfidensintervall", "slumpeffekt", "förregistrering", "runologi", "runstenar"],
  alternates: { canonical: TERMS_PATH, languages: { sv: TERMS_PATH, en: EN_TERMS_PATH, "x-default": TERMS_PATH } },
  openGraph: { type: "website", url: TERMS_PATH, title: TITLE, description: DESCRIPTION, siteName: "Vitki", locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: "Statistiska begrepp" }] },
};

export default function TermsPage() {
  return (
    <BlogShell>
      <EnglishEdition href={EN_TERMS_PATH} />
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24">
        <div className="flex items-center justify-between gap-4 mb-3">
          <Link href={REPORTS_PATH} prefetch={false} className="tap text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] hover:underline">← Forskningsrapporter</Link>
          <Link href={EN_TERMS_PATH} hrefLang="en" className="tap text-sm text-[#b7410e] font-semibold hover:underline">In English →</Link>
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Statistiska begrepp i rapporterna</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Forskningsrapporterna använder ett fåtal statistiska begrepp gång på gång. Här förklaras de i vanliga ord: vad
          begreppet är och hur siffran ska läsas. Rapporterna säger dessutom sitt huvudresultat i klartext.
        </p>
        <ReportTermList lang="sv" />
      </section>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(termsJsonLd("sv", `${SITE_URL}${TERMS_PATH}`, TITLE)).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
