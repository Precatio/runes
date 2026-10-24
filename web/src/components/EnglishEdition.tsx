"use client";

import { useEnglishEdition } from "@/components/LanguageContext";

// A Swedish page with an English edition (as the articles have): a reader who has chosen English is shown the edition
export default function EnglishEdition({ href }: { href: string }) {
  useEnglishEdition(href);
  return null;
}
