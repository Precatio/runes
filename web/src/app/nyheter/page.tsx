import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import NewsList from "@/components/NewsList";
import { NEWS } from "@/lib/news";
import { NEWS_PATH } from "@/lib/site";

// All news notices about Vitki: new features in the app and what is under way (web/content/news.json)
const TITLE = "Nyheter – Vitki";
const DESCRIPTION = "Nytt i Vitki: korta notiser om nya funktioner i forskningsplattformen för runinskrifter och om det som är på gång.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: NEWS_PATH },
  openGraph: { type: "website", url: NEWS_PATH, title: TITLE, description: DESCRIPTION, siteName: "Vitki", locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: "Vitki" }] },
};

export default function NewsPage() {
  return (
    <BlogShell>
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-24">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Nyheter</div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Nytt i Vitki</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Korta notiser om nya funktioner i appen och om det som är på gång. Hur varje funktion räknar står i
          metoddokumentationen, och ändringarna i sin helhet i ändringsloggen på GitHub.
        </p>
        <div className="mt-10"><NewsList items={NEWS} /></div>
      </section>
    </BlogShell>
  );
}
