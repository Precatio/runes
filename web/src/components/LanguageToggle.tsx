"use client";

import Link from "next/link";
import type { MouseEvent, ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { englishPage, useLanguage } from "./LanguageContext";

// The Swedish page of an English edition: /en/artiklar/x/ → /artiklar/x/
const swedishOf = (path: string) => path.replace(/^\/en(?=\/|$)/, "") || "/";

/** Svenska/English. Not translated itself: it always names the other language in that language. On an English edition
 *  (/en/…) it leads to the Swedish page; on a Swedish article it leads to the English edition (LanguageContext); on the
 *  other pages it translates the page in place. */
export default function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, setLang } = useLanguage();
  const pathname = usePathname();
  const router = useRouter();
  const label = lang === "sv" ? "Switch to English" : "Byt till svenska";
  const toggle = () => {
    if (lang === "en" && englishPage(pathname)) {
      setLang("sv");
      router.push(swedishOf(pathname) + window.location.search);
      return;
    }
    setLang(lang === "sv" ? "en" : "sv");
  };
  return (
    <button type="button" translate="no" onClick={toggle} aria-label={label} title={label} className={className}>
      {lang === "sv" ? "EN" : "SV"}
    </button>
  );
}

/** "Läs på svenska →" on an English edition: also makes Swedish the reader's choice, so that the Swedish page is not
 *  forwarded back to the English edition for a reader who had chosen English. A plain click sets the choice here; the
 *  address carries ?sv for a link opened in a new tab or window (middle click, the context menu), where public/
 *  lang-init.js makes the same choice before the page can forward, and takes ?sv off the address again. */
export function SwedishEditionLink({ href, className, children }: { href: string; className?: string; children: ReactNode }) {
  const { setLang } = useLanguage();
  const router = useRouter();
  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    setLang("sv");
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // a new tab or window: ?sv
    e.preventDefault();
    router.push(href);
  };
  return (
    <Link href={`${href}${href.includes("?") ? "&" : "?"}sv`} hrefLang="sv" className={className} onClick={onClick}>
      {children}
    </Link>
  );
}
