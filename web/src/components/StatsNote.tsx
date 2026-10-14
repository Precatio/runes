"use client";

import { useLanguage } from "@/components/LanguageContext";
import { PUBLIC_SITE, SITE_PROJECT } from "@/lib/site";

// What the website counts (components/SiteTracker.tsx), in the footer
export default function StatsNote() {
  const en = useLanguage().lang === "en";
  if (!PUBLIC_SITE || !SITE_PROJECT) return null;
  return (
    <span translate="no" title={en ? "Pages viewed, the referring site, time zone, language and kind of device – no cookies, no IP address"
                                   : "Vilka sidor som visas, varifrån besökaren kom, tidszon, språk och typ av enhet – inga kakor, ingen IP-adress"}>
      {en ? "Anonymous visitor counts, no cookies" : "Anonym besöksstatistik utan kakor"}
    </span>
  );
}
