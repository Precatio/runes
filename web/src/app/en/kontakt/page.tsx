import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import ContactPage, { CONTACT_DESCRIPTION, CONTACT_TITLE, contactAlternates } from "@/components/ContactPage";
import { SwedishEditionLink } from "@/components/LanguageToggle";
import { CONTACT_PATH, EN_CONTACT_PATH, SITE_NAME } from "@/lib/site";

// The English edition of the author's and contact page, rendered in English for every reader (as /en/artiklar)
export const revalidate = 60;

export const metadata: Metadata = {
  title: CONTACT_TITLE.en,
  description: CONTACT_DESCRIPTION.en,
  alternates: { canonical: EN_CONTACT_PATH, languages: contactAlternates },
  openGraph: { type: "profile", url: EN_CONTACT_PATH, title: CONTACT_TITLE.en, description: CONTACT_DESCRIPTION.en, siteName: SITE_NAME,
               locale: "en_GB", images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: SITE_NAME }] },
};

export default function EnglishContactPage() {
  return (
    <BlogShell lang="en">
      <div className="max-w-2xl mx-auto px-6 pt-8 -mb-12 text-right">
        <SwedishEditionLink href={CONTACT_PATH} className="tap text-sm text-[#b7410e] font-semibold hover:underline">Läs på svenska →</SwedishEditionLink>
      </div>
      <ContactPage lang="en" />
    </BlogShell>
  );
}
