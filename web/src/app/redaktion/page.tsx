import type { Metadata } from "next";
import Redaktion from "@/components/Redaktion";

// The web admin on the public website (ADMIN_PA_WEBBEN.md): the founder signs in with Google and schedules, publishes
// or unpublishes articles straight in Firestore, guarded by web/firestore.rules. Texts are still written in the local
// app. Never indexed, not in the sitemap (app/sitemap.ts lists only its own pages), disallowed in robots.txt, and with
// a security policy of its own (scripts/redaktion_csp.mjs).
export const metadata: Metadata = {
  title: "Redaktion",
  description: "Vitkis redaktion: publicering och schemaläggning av artiklar.",
  robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
  alternates: { canonical: null },
  openGraph: null,
};

export default function RedaktionPage() {
  return <Redaktion />;
}
