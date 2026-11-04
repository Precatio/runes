import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import Ristare from "@/components/Ristare";
import { CARVERS_PATH, DOWNLOAD_URL, METHODS_URL } from "@/lib/site";
import "./ristare.css";

// Ristarna på webbplatsen: samma sida som Korpus → Ristarna i appen (components/Ristare.tsx), med datan som webbplatsens
// export kopierar från den senaste korpuskörningen (src/site_export.py → web/public/ristarna/ristare.json).
const TITLE = "Ristarna, en i taget – runristarnas fingeravtryck";
const DESCRIPTION = "Varje känd runristares fingeravtryck ur de signerade stenarna, de attribuerade stenarna från kärna till " +
  "ytterkant, och de runstenar utan ristare som Vitkis attribueringsmodell tror att ristaren gjorde.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: ["runristare", "runristare attribuering", "Balle", "Öpir", "Åsmund", "runstenar", "Rundata", "signerade runstenar"],
  alternates: { canonical: CARVERS_PATH },
  openGraph: { type: "website", url: CARVERS_PATH, title: TITLE, description: DESCRIPTION, siteName: "Vitki", locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: "Vitki" }] },
  twitter: { card: "summary_large_image", title: TITLE, description: DESCRIPTION, images: ["/delningsbild.png"] },
};

export default function RistarnaPage() {
  return (
    <BlogShell>
      <section className="max-w-6xl mx-auto px-4 md:px-6 pt-14">
        <p className="max-w-[72ch] text-base text-slate-600 leading-relaxed">
          Tre av fyra svenska runstenar saknar en säker ristare. Den här sidan går igenom de kända ristarna en i taget: vilka
          drag som skiljer var och en från samtida grannstenar, vilka av deras stenar som ligger mitt i stilen och vilka i
          ytterkanten, och vilka stenar utan ristare som kan vara deras. Fingeravtrycken bygger på de stenar ristarna själva
          signerade; förslagen kommer från Vitkis attribueringsmodell och är förslag, inte attribueringar. Sidan räknas om när
          korpusen ändras. Metoden står i <a href={METHODS_URL} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#b7410e] hover:underline">METHODS.md</a>,
          och hela verktyget finns i <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#b7410e] hover:underline">Vitki</a>.
        </p>
      </section>
      <Ristare src="/ristarna/ristare.json" />
    </BlogShell>
  );
}
