/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import type { ReactNode } from "react";
import LanguageToggle from "@/components/LanguageToggle";

// The public blog's frame: the landing page's header and footer
export default function BlogShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#f6f4f1] text-slate-900 overflow-x-hidden flex flex-col">
      <header className="sticky top-0 z-50 bg-[#f6f4f1]/85 backdrop-blur-md border-b border-slate-900/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/vitki_logo.png" alt="" className="w-9 h-9" />
            <span className="text-xl font-bold tracking-tight">Vitki</span>
          </Link>
          <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
            <Link href="/" className="hover:text-slate-900">Start</Link>
            <Link href="/artiklar" className="hover:text-slate-900">Artiklar</Link>
            <Link href="/karta" className="hover:text-slate-900">Mönsterkartan</Link>
          </nav>
          <div className="flex items-center gap-3">
            <LanguageToggle className="px-2.5 py-1 rounded-full border border-slate-300 text-[11px] font-bold tracking-wider text-slate-600 hover:border-slate-900 hover:text-slate-900" />
            <Link href="/start" className="px-4 py-2 rounded-full bg-slate-900 text-white text-sm font-bold hover:bg-black">Öppna appen</Link>
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-slate-900/10">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row gap-4 justify-between text-sm text-slate-500">
          <div>Vitki · öppen forskningsplattform för runinskrifter</div>
          <div className="flex gap-5">
            <Link href="/docs" className="hover:text-slate-900">Dokumentation</Link>
            <a href="https://github.com/Precatio/runes" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900">GitHub</a>
            <span>GPL-3.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
