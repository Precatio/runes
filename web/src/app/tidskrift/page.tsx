import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import EnglishEdition from "@/components/EnglishEdition";
import KorpusPage from "@/components/KorpusPage";
import { EN_KORPUS_PATH, KORPUS_DESCRIPTION, KORPUS_ISSUES, KORPUS_PATH, KORPUS_TITLE, korpusAlternates } from "@/lib/korpus";
import { SITE_NAME } from "@/lib/site";

// Vitki's journal Korpus in Swedish; a reader who has chosen English is shown /en/korpus instead
const cover = KORPUS_ISSUES[0]?.cover_sv;

export const metadata: Metadata = {
  title: KORPUS_TITLE.sv,
  description: KORPUS_DESCRIPTION.sv,
  alternates: { canonical: KORPUS_PATH, languages: korpusAlternates },
  openGraph: { type: "website", url: KORPUS_PATH, title: KORPUS_TITLE.sv, description: KORPUS_DESCRIPTION.sv, siteName: SITE_NAME, locale: "sv_SE",
               images: cover ? [{ url: cover, width: 909, height: 1287, alt: "Korpus" }] : [{ url: "/delningsbild.png", width: 1200, height: 630, alt: SITE_NAME }] },
};

export default function SwedishKorpusPage() {
  return (
    <BlogShell>
      <EnglishEdition href={EN_KORPUS_PATH} />
      <KorpusPage lang="sv" />
    </BlogShell>
  );
}
