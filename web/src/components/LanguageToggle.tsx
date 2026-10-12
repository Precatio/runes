"use client";

import { useLanguage } from "./LanguageContext";

/** Svenska/English. Not translated itself: it always names the other language in that language. */
export default function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, setLang } = useLanguage();
  const label = lang === "sv" ? "Switch to English" : "Byt till svenska";
  return (
    <button type="button" translate="no" onClick={() => setLang(lang === "sv" ? "en" : "sv")} aria-label={label}
            title={label} className={className}>
      {lang === "sv" ? "EN" : "SV"}
    </button>
  );
}
