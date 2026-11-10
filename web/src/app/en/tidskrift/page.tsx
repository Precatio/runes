import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import KorpusPage from "@/components/KorpusPage";
import { SwedishEditionLink } from "@/components/LanguageToggle";
import { EN_KORPUS_PATH, KORPUS_DESCRIPTION, KORPUS_ISSUES, KORPUS_PATH, KORPUS_TITLE, korpusAlternates } from "@/lib/korpus";
import { SITE_NAME } from "@/lib/site";

// The English edition of the journal's page (/en/tidskrift), rendered in English for every reader (as /en/kontakt)
const cover = KORPUS_ISSUES[0]?.cover_en;

export const metadata: Metadata = {
  title: KORPUS_TITLE.en,
  description: KORPUS_DESCRIPTION.en,
  alternates: { canonical: EN_KORPUS_PATH, languages: korpusAlternates },
  openGraph: { type: "website", url: EN_KORPUS_PATH, title: KORPUS_TITLE.en, description: KORPUS_DESCRIPTION.en, siteName: SITE_NAME, locale: "en_GB",
               images: cover ? [{ url: cover, width: 909, height: 1287, alt: "Korpus" }] : [{ url: "/delningsbild.png", width: 1200, height: 630, alt: SITE_NAME }] },
};

export default function EnglishKorpusPage() {
  return (
    <BlogShell lang="en">
      <div className="max-w-6xl mx-auto px-6 pt-8 -mb-10 text-right">
        <SwedishEditionLink href={KORPUS_PATH} className="tap text-sm text-[#b7410e] font-semibold hover:underline">Läs på svenska →</SwedishEditionLink>
      </div>
      <KorpusPage lang="en" />
    </BlogShell>
  );
}
