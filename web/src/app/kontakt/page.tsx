import type { Metadata } from "next";
import BlogShell from "@/components/BlogShell";
import ContactForm from "@/components/ContactForm";
import { CONTACT_PATH } from "@/lib/site";

// The contact page: a form that is emailed to the founder (ContactForm)
const TITLE = "Kontakt – Vitki";
const DESCRIPTION = "Kontakta Viktor Kvant, som grundade Vitki: frågor om runstenarna och artiklarna, rättelser, idéer eller samarbete.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: CONTACT_PATH },
  openGraph: { type: "website", url: CONTACT_PATH, title: TITLE, description: DESCRIPTION, siteName: "Vitki", locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: "Vitki" }] },
};

export default function ContactPage() {
  return (
    <BlogShell>
      <section className="max-w-2xl mx-auto px-6 pt-20 pb-24">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Kontakt</div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">Skriv till Vitki</h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Har du en fråga om en runsten eller en artikel, har du hittat ett fel, eller vill du samarbeta? Skriv några rader
          så kommer meddelandet direkt till Viktor Kvant, som grundade Vitki.
        </p>
        <div className="mt-10"><ContactForm /></div>
      </section>
    </BlogShell>
  );
}
