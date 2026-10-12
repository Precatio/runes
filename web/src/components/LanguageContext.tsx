"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { translations, Language, Translations } from "@/lib/translations";

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);
const KEY = "vitki_lang";

function stored(): Language {
  try { return localStorage.getItem(KEY) === "en" ? "en" : "sv"; } catch { return "sv"; }
}

function reveal() {
  document.documentElement.classList.remove("i18n-pending");
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  // The page is rendered in Swedish (the original) and translated in place after hydration (src/i18n/dom.ts); the
  // stored choice is read after the first render so that server and client render the same thing
  const [lang, setLangState] = useState<Language>("sv");

  useEffect(() => {
    const saved = stored();
    if (saved !== "sv") queueMicrotask(() => setLangState(saved));
    else reveal();
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    let cancelled = false;
    (async () => {
      const dom = await import("@/i18n/dom");
      if (lang === "en") {
        const [core, catalog, names, terms] = await Promise.all([import("@/i18n/core"), import("@/i18n/en.json"),
                                                                 import("@/i18n/names.json"), import("@/i18n/terms.json")]);
        if (cancelled) return;
        core.setNames(names.default as string[]);
        core.setTerms(terms.default as string[]);
        dom.start(catalog.default as Record<string, string>);
      } else {
        dom.stop();
      }
      reveal();
    })().catch(reveal);
    return () => { cancelled = true; };
  }, [lang]);

  const setLang = (l: Language) => {
    setLangState(l);
    try { localStorage.setItem(KEY, l); } catch { /* private mode: the choice lasts for this visit */ }
  };

  // The interface texts are written in Swedish and translated with the rest of the page
  return (
    <LanguageContext.Provider value={{ lang, setLang, t: translations.sv }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
