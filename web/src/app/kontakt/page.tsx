import type { Metadata } from "next";
import Link from "next/link";
import BlogShell from "@/components/BlogShell";
import ContactForm from "@/components/ContactForm";
import { postDate } from "@/components/BlogBody";
import { listPosts } from "@/lib/articles";
import { postPath } from "@/lib/blogSeo";
import { featuredFirst } from "@/lib/featured";
import { AUTHORS, CONTACT_PATH, GITHUB_URL, SITE_NAME, SITE_URL } from "@/lib/site";

// The author's page and the contact page in one: who writes the articles, what he has written, and a form that is
// emailed to him (ContactForm). Search engines get the same person as a schema.org entity (#founder, also on the start page).
const AUTHOR = AUTHORS["Viktor Kvant"];
const TITLE = "Viktor Kvant – om författaren och kontakt – Vitki";
const DESCRIPTION = "Viktor Kvant grundade Vitki och skriver artiklarna om runstenarna. Om författaren, hans artiklar och ett formulär för frågor, rättelser och samarbete.";
export const revalidate = 60;

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: CONTACT_PATH },
  openGraph: { type: "profile", url: CONTACT_PATH, title: TITLE, description: DESCRIPTION, siteName: SITE_NAME, locale: "sv_SE",
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: SITE_NAME }] },
};

export default async function ContactPage() {
  const { posts } = await listPosts();
  const own = featuredFirst(posts.filter(p => !p.author || p.author === AUTHOR.name));
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    url: `${SITE_URL}${CONTACT_PATH}`,
    name: TITLE,
    mainEntity: {
      "@type": "Person", "@id": `${SITE_URL}/#founder`, name: AUTHOR.name, url: AUTHOR.url, sameAs: [AUTHOR.linkedin, GITHUB_URL],
      jobTitle: AUTHOR.role, description: AUTHOR.bio, worksFor: { "@id": `${SITE_URL}/#organization` },
      knowsAbout: ["Runstenar", "Runinskrifter", "Dataanalys", "Statistik", "3D-skanning"],
    },
  };
  return (
    <BlogShell>
      <section className="max-w-2xl mx-auto px-6 pt-20 pb-24">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Om författaren</div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">{AUTHOR.name}</h1>
        <p className="mt-2 text-lg text-slate-500">{AUTHOR.role}</p>
        <p className="mt-5 text-lg text-slate-600 leading-relaxed">{AUTHOR.bio}</p>
        <p className="mt-4 text-slate-600 leading-relaxed">
          Artiklarna på Vitki bygger på öppna data och öppen kod: varje siffra kan räknas om av den som vill, och metoderna
          är beskrivna i <a href={`${GITHUB_URL}/blob/main/METHODS.md`} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#b7410e] hover:underline">metoddokumentationen</a>.
        </p>
        <div className="mt-5 flex flex-wrap gap-4 text-sm font-bold text-[#b7410e]">
          <a href={AUTHOR.linkedin} target="_blank" rel="noopener noreferrer me" className="hover:underline">LinkedIn ↗</a>
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="hover:underline">Vitki på GitHub ↗</a>
        </div>

        {own.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-serif font-bold text-slate-900">Artiklar av {AUTHOR.name}</h2>
            <ul className="mt-4 space-y-2.5">
              {own.map(p => (
                <li key={p.id} className="leading-snug">
                  <Link href={postPath(p.slug)} className="font-semibold text-slate-900 hover:text-[#b7410e]">{p.title}</Link>
                  <span className="ml-2 text-sm text-slate-500">{postDate(p, "sv")}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-14">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Kontakt</div>
          <h2 className="text-3xl font-serif font-bold tracking-tight">Skriv till Vitki</h2>
          <p className="mt-4 text-lg text-slate-600 leading-relaxed">
            Har du en fråga om en runsten eller en artikel, har du hittat ett fel, eller vill du samarbeta? Skriv några rader
            så kommer meddelandet direkt till Viktor.
          </p>
          <div className="mt-8"><ContactForm /></div>
        </div>
      </section>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
    </BlogShell>
  );
}
