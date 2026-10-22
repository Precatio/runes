"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { translations, Language, Translations } from "@/lib/translations";

interface LanguageContextType {
  // The language the page is shown in: English on the English editions (/en/…), otherwise the reader's choice
  lang: Language;
  setLang: (lang: Language) => void;
  t: Translations;
  // The English edition of the page shown, registered by the page (useEnglishEdition): a reader who has chosen
  // English is taken there instead of having the Swedish page translated
  setEdition: (href: string | null) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);
const KEY = "vitki_lang";

function stored(): Language {
  try { return localStorage.getItem(KEY) === "en" ? "en" : "sv"; } catch { return "sv"; }
}

function reveal() {
  document.documentElement.classList.remove("i18n-pending");
}

// The English edition of an article (/en/artiklar/…) is English whatever the reader has chosen: it is rendered in
// English on the server, so it needs neither the catalog nor the translator
export const englishPage = (path: string | null) => !!path && /^\/en(?:\/|$)/.test(path);

/** The catalog, names and terms: on the public website only the entries its pages can show (src/i18n/public-catalog.mjs),
 *  in the app the whole catalog. The condition is written out (not PUBLIC_SITE from lib/site), so that the build leaves
 *  the whole catalog out of the website. */
function catalogFiles() {
  return process.env.NEXT_PUBLIC_SITE_MODE === "public"
    ? Promise.all([import("@/i18n/en.public.json"), import("@/i18n/names.public.json"), import("@/i18n/terms.public.json")])
    : Promise.all([import("@/i18n/en.json"), import("@/i18n/names.json"), import("@/i18n/terms.json")]);
}

/** After the whole document has arrived and React has finished hydrating the parts that stream in later (Suspense),
 *  so that the translator never changes server-rendered markup that React is still comparing. DOMContentLoaded comes
 *  when the last streamed part of the HTML has been parsed (it carries the page's data with it), and React hydrates
 *  those parts in tasks of its own, so the first idle moment after it comes after them. It does not wait for the
 *  pictures ("load"): a reader who has chosen English would otherwise look at a hidden page until the photos in view
 *  had arrived (about 0.4 s on the article list, more on a slow line). */
function settled(): Promise<void> {
  return new Promise(res => {
    const go = () => ("requestIdleCallback" in window ? window.requestIdleCallback(() => res(), { timeout: 800 })
                                                    : setTimeout(res, 300));
    if (document.readyState !== "loading") go();
    else document.addEventListener("DOMContentLoaded", go, { once: true });
  });
}

// Whether the translator has been loaded: switching back to Swedish needs it only to restore what it changed
let translatorLoaded = false;

export function LanguageProvider({ children }: { children: ReactNode }) {
  // The page is rendered in Swedish (the original) and translated in place after hydration (src/i18n/dom.ts); the
  // stored choice is read after the first render (null until then), so that server and client render the same thing
  const [chosen, setChosen] = useState<Language | null>(null);
  const [edition, setEdition] = useState<string | null>(null);
  const pathname = usePathname();
  const router = useRouter();
  const english = englishPage(pathname);
  const lang: Language = english ? "en" : chosen ?? "sv";
  // English chosen on a Swedish page that has an English edition: that edition is shown instead of a translation
  const toEdition = chosen === "en" && !english && edition ? edition : null;
  const translating = chosen === "en" && !english && !edition;

  useEffect(() => {
    const saved = stored();
    queueMicrotask(() => setChosen(saved));
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  // Replaced, not pushed: going back leaves the article instead of landing on the Swedish page that forwards again.
  // The page stays hidden until the edition is shown, if public/lang-init.js hid it. The query (a campaign parameter
  // that SiteTracker records) and the #anchor of a shared link go along; an anchor the edition lacks just does nothing.
  useEffect(() => {
    if (toEdition) router.replace(toEdition + window.location.search + window.location.hash);
  }, [toEdition, router]);

  useEffect(() => {
    if (chosen === null || toEdition) return;
    let cancelled = false;
    (async () => {
      if (translating) {
        const [dom, core, [catalog, names, terms]] = await Promise.all([import("@/i18n/dom"), import("@/i18n/core"), catalogFiles(), settled()]);
        if (cancelled) return;
        translatorLoaded = true;
        core.setNames(names.default as string[]);
        core.setTerms(terms.default as string[]);
        dom.start(catalog.default as Record<string, string>);
      } else if (translatorLoaded) {
        const dom = await import("@/i18n/dom");
        if (cancelled) return;
        dom.stop();
      }
      reveal();
    })().catch(reveal);
    return () => { cancelled = true; };
  }, [chosen, translating, toEdition]);

  const setLang = useCallback((l: Language) => {
    setChosen(l);
    try { localStorage.setItem(KEY, l); } catch { /* private mode: the choice lasts for this visit */ }
  }, []);

  // The interface texts are written in Swedish and translated with the rest of the page
  const value = useMemo(() => ({ lang, setLang, t: translations.sv, setEdition }), [lang, setLang]);
  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

/** Registers the English edition of the page being shown (its address), for as long as the page is shown. */
export function useEnglishEdition(href: string | null) {
  const { setEdition } = useLanguage();
  useEffect(() => {
    setEdition(href);
    return () => setEdition(null);
  }, [href, setEdition]);
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
