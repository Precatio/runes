/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import LanguageToggle from "@/components/LanguageToggle";
import { ARTICLES_PATH, EN_ARTICLES_PATH } from "@/lib/blogSeo";
import { CONTACT_PATH, DOWNLOAD_URL, EN_CONTACT_PATH, NEWS_PATH } from "@/lib/site";

// The one header of the public website: the start page, the articles, the news and the contact page all show it. The
// start page's sections are reached as /#… from every page. lang="en": the English editions (/en/…) get it in
// English; the Swedish pages are translated in place like the rest of the page. Links are not prefetched (BlogShell).
const SECTIONS: [string, string, string][] = [
  ["/#forskning", "För forskningen", "For research"],
  ["/#appen", "Appen", "The app"],
  ["/#nytt", "Vad Vitki tillför", "What Vitki adds"],
  ["/#landskap", "Nya källor", "New sources"],
  ["/#kallor", "Källor", "Sources"],
  ["/#oppen", "Öppen källkod", "Open source"],
];

export default function SiteHeader({ lang = "sv" }: { lang?: "sv" | "en" }) {
  const en = lang === "en";
  return (
    <header className="sticky top-0 z-50 bg-[#f6f4f1]/85 backdrop-blur-md border-b border-slate-900/5">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" prefetch={false} className="flex items-center gap-2.5">
          <img src="/vitki_logo.png" alt="" className="w-9 h-9" />
          <span className="text-xl font-bold tracking-tight">Vitki</span>
        </Link>
        <nav className="hidden lg:flex items-center gap-5 text-sm font-semibold text-slate-600">
          <Link href={en ? EN_ARTICLES_PATH : ARTICLES_PATH} prefetch={false} className="hover:text-slate-900">{en ? "Articles" : "Artiklar"}</Link>
          {SECTIONS.map(([href, sv, e]) => <a key={href} href={href} className="hover:text-slate-900">{en ? e : sv}</a>)}
          <Link href={NEWS_PATH} prefetch={false} className="hover:text-slate-900">{en ? "News" : "Nyheter"}</Link>
          <Link href={en ? EN_CONTACT_PATH : CONTACT_PATH} prefetch={false} className="hover:text-slate-900">{en ? "Contact" : "Kontakt"}</Link>
        </nav>
        <div className="flex items-center gap-3">
          <LanguageToggle className="px-2.5 py-1 rounded-full border border-slate-300 text-[11px] font-bold tracking-wider text-slate-600 hover:border-slate-900 hover:text-slate-900" />
          <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="px-4 py-2 rounded-full bg-slate-900 text-white text-sm font-bold hover:bg-black">{en ? "Download Vitki" : "Ladda ner Vitki"}</a>
        </div>
      </div>
    </header>
  );
}
