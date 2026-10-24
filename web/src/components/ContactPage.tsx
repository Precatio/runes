import Link from "next/link";
import ContactForm from "@/components/ContactForm";
import { postDate } from "@/components/BlogBody";
import { listPosts } from "@/lib/articles";
import { enPostPath, EN_ARTICLES_PATH, ARTICLES_PATH, postPath } from "@/lib/blogSeo";
import { featuredFirst } from "@/lib/featured";
import { AUTHORS, BLUESKY_URL, CONTACT_PATH, EN_CONTACT_PATH, GITHUB_URL, SITE_URL } from "@/lib/site";

// The author's page and the contact page in one, in Swedish (/kontakt) and English (/en/kontakt): who writes the
// articles, what he has written, and a form that is emailed to him (ContactForm). Search engines get the same person as
// a schema.org entity (#founder, also on the start page).
export const AUTHOR = AUTHORS["Viktor Kvant"];
export const CONTACT_TITLE = { sv: "Viktor Kvant – personen bakom Vitki – kontakt", en: "Viktor Kvant – the person behind Vitki – contact" };
export const CONTACT_DESCRIPTION = {
  sv: "Viktor Kvant grundade Vitki och skriver artiklarna om runstenarna. Personen bakom Vitki, artiklarna och ett formulär för frågor, rättelser och samarbete.",
  en: "Viktor Kvant founded Vitki and writes the articles on the runestones. The person behind Vitki, the articles and a form for questions, corrections and collaboration.",
};
export const contactAlternates = { sv: CONTACT_PATH, en: EN_CONTACT_PATH, "x-default": CONTACT_PATH };

const link = "font-semibold text-[#b7410e] hover:underline";

export default async function ContactPage({ lang }: { lang: "sv" | "en" }) {
  const en = lang === "en";
  const { posts } = await listPosts();
  const own = featuredFirst(posts.filter(p => (!p.author || p.author === AUTHOR.name) && (!en || p.title_en)));
  const methods = <a href={`${GITHUB_URL}/blob/main/METHODS.md`} target="_blank" rel="noopener noreferrer" className={link}>
    {en ? "method documentation" : "metoddokumentationen"}</a>;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    url: `${SITE_URL}${en ? EN_CONTACT_PATH : CONTACT_PATH}`,
    name: CONTACT_TITLE[lang],
    inLanguage: en ? "en" : "sv",
    mainEntity: {
      "@type": "Person", "@id": `${SITE_URL}/#founder`, name: AUTHOR.name, url: AUTHOR.url, sameAs: [AUTHOR.linkedin, GITHUB_URL],
      jobTitle: en ? AUTHOR.role_en : AUTHOR.role, description: en ? AUTHOR.bio_en : AUTHOR.bio,
      worksFor: { "@id": `${SITE_URL}/#organization` },
      knowsAbout: en ? ["Runestones", "Runic inscriptions", "Data analysis", "Statistics", "3D scanning"]
                     : ["Runstenar", "Runinskrifter", "Dataanalys", "Statistik", "3D-skanning"],
    },
  };
  return (
    <section className="max-w-2xl mx-auto px-6 pt-20 pb-24" lang={lang}>
      <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">{en ? "The person behind Vitki" : "Personen bakom Vitki"}</div>
      <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight">{AUTHOR.name}</h1>
      <p className="mt-2 text-lg text-slate-500">{en ? AUTHOR.role_en : AUTHOR.role}</p>
      <p className="mt-5 text-lg text-slate-600 leading-relaxed">{en ? AUTHOR.bio_en : AUTHOR.bio}</p>
      {en ? (
        <>
          <p className="mt-4 text-slate-600 leading-relaxed">
            The articles on Vitki build on open data and open code: anyone who wants to can recompute every figure, and
            the methods are described in the {methods}.
          </p>
          <p className="mt-4 text-slate-600 leading-relaxed">
            The articles are at the same time only examples of what the tool can be used for and what kind of data it
            gives. The same data and tools can serve research with a deeper and narrower focus than a popular-science
            article can have – and questions nobody has asked yet.
          </p>
          <p className="mt-4 text-slate-600 leading-relaxed">
            Vitki does not replace the runologist&apos;s judgement. It provides measurable, reviewable evidence to test
            hypotheses against.
          </p>
        </>
      ) : (
        <>
          <p className="mt-4 text-slate-600 leading-relaxed">
            Artiklarna på Vitki bygger på öppna data och öppen kod: varje siffra kan räknas om av den som vill, och metoderna
            är beskrivna i {methods}.
          </p>
          <p className="mt-4 text-slate-600 leading-relaxed">
            Artiklarna är samtidigt bara exempel på vad verktyget kan användas till och vilken sorts data det ger. Samma
            data och verktyg går att använda i forskning med ett djupare och smalare fokus än en populärvetenskaplig artikel
            kan ha – och till frågor som ingen ännu har ställt.
          </p>
          <p className="mt-4 text-slate-600 leading-relaxed">
            Vitki ersätter inte runologens bedömning. Den ger mätbara, granskningsbara underlag att pröva hypoteser mot.
          </p>
        </>
      )}
      <div className="mt-5 flex flex-wrap gap-4 text-sm font-bold text-[#b7410e]">
        <a href={AUTHOR.linkedin} target="_blank" rel="noopener noreferrer me" className="hover:underline">LinkedIn ↗</a>
        <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="hover:underline">{en ? "Vitki on GitHub ↗" : "Vitki på GitHub ↗"}</a>
        <a href={BLUESKY_URL} target="_blank" rel="noopener noreferrer me" className="hover:underline">{en ? "Vitki on Bluesky ↗" : "Vitki på Bluesky ↗"}</a>
      </div>

      <div className="mt-14">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">{en ? "Contact" : "Kontakt"}</div>
        <h2 className="text-3xl font-serif font-bold tracking-tight">{en ? "Write to Vitki" : "Skriv till Vitki"}</h2>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          {en ? "Do you have a question about a runestone or an article, have you found an error, or would you like to "
                + "collaborate? Write a few lines and the message goes straight to Viktor."
              : "Har du en fråga om en runsten eller en artikel, har du hittat ett fel, eller vill du samarbeta? Skriv några "
                + "rader så kommer meddelandet direkt till Viktor."}
        </p>
        <div className="mt-8"><ContactForm /></div>
      </div>
      {own.length > 0 && (
        <div className="mt-16 border-t border-slate-900/10 pt-8">
          <h2 className="text-xl font-serif font-bold text-slate-900">{en ? `Articles by ${AUTHOR.name}` : `Artiklar av ${AUTHOR.name}`}</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {own.slice(0, 6).map(p => (
              <li key={p.id} className="leading-snug">
                <Link href={en ? enPostPath(p.slug) : postPath(p.slug)} prefetch={false} className="font-semibold text-slate-800 hover:text-[#b7410e]">
                  {en ? p.title_en : p.title}</Link>
                <span className="ml-2 text-slate-500">{postDate(p, lang)}</span>
              </li>
            ))}
          </ul>
          <Link href={en ? EN_ARTICLES_PATH : ARTICLES_PATH} className="mt-3 inline-block text-sm font-bold text-[#b7410e] hover:underline">
            {en ? `All ${own.length} articles →` : `Alla ${own.length} artiklar →`}</Link>
        </div>
      )}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
    </section>
  );
}
