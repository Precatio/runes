import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import ContactPage, { CONTACT_DESCRIPTION, CONTACT_TITLE, contactAlternates } from "@/components/ContactPage";
import EnglishEdition from "@/components/EnglishEdition";
import { CONTACT_PATH, EN_CONTACT_PATH, SITE_NAME } from "@/lib/site";

// The author's page and the contact page in Swedish; a reader who has chosen English is shown /en/kontakt instead
export const revalidate = 60;

export const metadata: Metadata = {
  title: CONTACT_TITLE.sv,
  description: CONTACT_DESCRIPTION.sv,
  alternates: { canonical: CONTACT_PATH, languages: contactAlternates },
  openGraph: { type: "profile", url: CONTACT_PATH, title: CONTACT_TITLE.sv, description: CONTACT_DESCRIPTION.sv, siteName: SITE_NAME,
               locale: "sv_SE", images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: SITE_NAME }] },
};

export default function SwedishContactPage() {
  return (
    <BlogShell>
      <EnglishEdition href={EN_CONTACT_PATH} />
      <ContactPage lang="sv" />
    </BlogShell>
  );
}
