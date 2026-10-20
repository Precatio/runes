"use client";

import { useLanguage } from "@/components/LanguageContext";
import { PUBLIC_SITE, SITE_PROJECT } from "@/lib/site";

// What the website counts (components/SiteTracker.tsx), in the footer
export default function StatsNote() {
  const en = useLanguage().lang === "en";
  if (!PUBLIC_SITE || !SITE_PROJECT) return null;
  return (
    <span translate="no" title={en ? "Pages viewed, the referring site, the page before within the visit, the share channel of a shared link, words searched in the article search, clicks on share buttons and outbound links, time zone, language and kind of device – no cookies, no IP address, nothing stored on your device"
                                   : "Vilka sidor som visas, varifrån besökaren kom, sidan före inom besöket, delningskanalen i en delad länk, sökord i artikelsökningen, klick på delningsknappar och utgående länkar, tidszon, språk och typ av enhet – inga kakor, ingen IP-adress, inget sparat på din enhet"}>
      {en ? "Anonymous visitor counts, no cookies" : "Anonym besöksstatistik utan kakor"}
    </span>
  );
}
