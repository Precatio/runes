import Link from "next/link";
import type { ReactNode } from "react";
import SiteHeader from "@/components/SiteHeader";
import LocalAppLink from "@/components/LocalAppLink";
import StatsNote from "@/components/StatsNote";
import { BLUESKY_URL, CONTACT_PATH, DOCS_URL, EN_CONTACT_PATH, GITHUB_URL, NEWS_PATH } from "@/lib/site";
import { ARTICLES_PATH, EN_ARTICLES_PATH } from "@/lib/blogSeo";
import { EN_REPORTS_PATH, REPORTS_PATH } from "@/lib/report";

// The articles' frame: the landing page's header and footer. The public website has no app, so the frame links to the
// articles and to GitHub, where the app is downloaded. Its links are not prefetched: every page has them, and the start
// page and the article list are larger than most pages themselves (they load when clicked). lang="en": the frame of the
// English editions (/en/…), rendered in English (the same words the translator gives the Swedish frame), so that those
// pages need neither the catalog nor the translator; its Articles link leads to the English list
export default function BlogShell({ children, lang = "sv" }: { children: ReactNode; lang?: "sv" | "en" }) {
  const en = lang === "en";
  return (
    <div className="min-h-screen bg-[#f6f4f1] text-slate-900 overflow-x-hidden flex flex-col">
      <SiteHeader lang={lang} />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-slate-900/10">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row gap-4 justify-between text-sm text-slate-500">
          <div>{en ? "Vitki · open research platform for runic inscriptions" : "Vitki · öppen forskningsplattform för runinskrifter"}</div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
            <Link href={en ? EN_ARTICLES_PATH : ARTICLES_PATH} prefetch={false} className="tap hover:text-slate-900">{en ? "Articles" : "Artiklar"}</Link>
            <Link href={en ? EN_REPORTS_PATH : REPORTS_PATH} prefetch={false} className="tap hover:text-slate-900">{en ? "Research reports" : "Forskningsrapporter"}</Link>
            <Link href={NEWS_PATH} prefetch={false} className="tap hover:text-slate-900">{en ? "News" : "Nyheter"}</Link>
            <Link href={en ? EN_CONTACT_PATH : CONTACT_PATH} prefetch={false} className="tap hover:text-slate-900">{en ? "Contact" : "Kontakt"}</Link>
            <a href={DOCS_URL} target="_blank" rel="noopener noreferrer" className="tap hover:text-slate-900">{en ? "Documentation" : "Dokumentation"}</a>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="tap hover:text-slate-900">GitHub</a>
            <a href={BLUESKY_URL} target="_blank" rel="noopener noreferrer me" className="tap hover:text-slate-900">Bluesky</a>
            <span>GPL-3.0</span>
            <StatsNote />
          </div>
        </div>
      </footer>
      <LocalAppLink className="fixed bottom-4 right-4 z-50 inline shadow-lg bg-white" />
    </div>
  );
}
