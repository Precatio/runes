/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import type { ReactNode } from "react";
import LanguageToggle from "@/components/LanguageToggle";
import LocalAppLink from "@/components/LocalAppLink";
import StatsNote from "@/components/StatsNote";
import { CONTACT_PATH, DOCS_URL, EN_CONTACT_PATH, DOWNLOAD_URL, GITHUB_URL, NEWS_PATH } from "@/lib/site";
import { ARTICLES_PATH, EN_ARTICLES_PATH } from "@/lib/blogSeo";

// The articles' frame: the landing page's header and footer. The public website has no app, so the frame links to the
// articles and to GitHub, where the app is downloaded. Its links are not prefetched: every page has them, and the start
// page and the article list are larger than most pages themselves (they load when clicked). lang="en": the frame of the
// English editions (/en/…), rendered in English (the same words the translator gives the Swedish frame), so that those
// pages need neither the catalog nor the translator; its Articles link leads to the English list
export default function BlogShell({ children, lang = "sv" }: { children: ReactNode; lang?: "sv" | "en" }) {
  const en = lang === "en";
  return (
    <div className="min-h-screen bg-[#f6f4f1] text-slate-900 overflow-x-hidden flex flex-col">
      <header className="sticky top-0 z-50 bg-[#f6f4f1]/85 backdrop-blur-md border-b border-slate-900/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" prefetch={false} className="flex items-center gap-2.5">
            <img src="/vitki_logo.png" alt="" className="w-9 h-9" />
            <span className="text-xl font-bold tracking-tight">Vitki</span>
          </Link>
          <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
            <Link href="/" prefetch={false} className="hover:text-slate-900">{en ? "Home" : "Start"}</Link>
            <Link href={en ? EN_ARTICLES_PATH : ARTICLES_PATH} prefetch={false} className="hover:text-slate-900">{en ? "Articles" : "Artiklar"}</Link>
            <Link href={NEWS_PATH} prefetch={false} className="hover:text-slate-900">{en ? "News" : "Nyheter"}</Link>
            <Link href={en ? EN_CONTACT_PATH : CONTACT_PATH} prefetch={false} className="hover:text-slate-900">{en ? "Contact" : "Kontakt"}</Link>
          </nav>
          <div className="flex items-center gap-3">
            <LanguageToggle className="px-2.5 py-1 rounded-full border border-slate-300 text-[11px] font-bold tracking-wider text-slate-600 hover:border-slate-900 hover:text-slate-900" />
            <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="px-4 py-2 rounded-full bg-slate-900 text-white text-sm font-bold hover:bg-black">{en ? "Download Vitki" : "Ladda ner Vitki"}</a>
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-slate-900/10">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row gap-4 justify-between text-sm text-slate-500">
          <div>{en ? "Vitki · open research platform for runic inscriptions" : "Vitki · öppen forskningsplattform för runinskrifter"}</div>
          <div className="flex flex-wrap items-center gap-5">
            <Link href={NEWS_PATH} prefetch={false} className="hover:text-slate-900">{en ? "News" : "Nyheter"}</Link>
            <Link href={en ? EN_CONTACT_PATH : CONTACT_PATH} prefetch={false} className="hover:text-slate-900">{en ? "Contact" : "Kontakt"}</Link>
            <a href={DOCS_URL} target="_blank" rel="noopener noreferrer" className="hover:text-slate-900">{en ? "Documentation" : "Dokumentation"}</a>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="hover:text-slate-900">GitHub</a>
            <span>GPL-3.0</span>
            <StatsNote />
          </div>
        </div>
      </footer>
      <LocalAppLink className="fixed bottom-4 right-4 z-50 inline shadow-lg bg-white" />
    </div>
  );
}
