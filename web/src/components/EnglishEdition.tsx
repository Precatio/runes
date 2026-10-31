"use client";

import { useEnglishEdition } from "@/components/LanguageContext";

// Tells the language switch that this Swedish page has an English edition: a reader who has chosen English is taken
// there instead of having the page translated in place (as the articles do, components/BlogArticle.tsx)
export default function EnglishEdition({ href }: { href: string | null }) {
  useEnglishEdition(href);
  return null;
}
