import Link from "next/link";
import { enPostPath, postPath } from "@/lib/blogSeo";
import { KORPUS_ISSUES, korpusJsonLd, type KorpusIssue } from "@/lib/korpus";
import { CONTACT_PATH, EN_CONTACT_PATH } from "@/lib/site";

// The journal's page (/tidskrift, /en/tidskrift): the latest issue with cover, contents and both PDFs, how to read the
// journal, what it is, and every issue. Rendered in the reader's language; the two routes are each other's editions.
const T = {
  sv: {
    kicker: "Tidskrift", sub: "Ristat & räknat – digital runforskning från Vitki",
    intro: "Korpus mäter hela runstenskorpusen på en gång – mot jordarter, strandlinjer, ortnamn, gravfält och vägar – och prövar varje mönster mot slumpen innan vi kallar det ett fynd. Tidskriften är skriven för den som är nyfiken men har ont om tid, och den är fri: läs den som PDF på svenska eller engelska.",
    latest: "Senaste numret", contents: "I numret", read: "Läs", pdfSv: "Läs nr {n} som PDF", pdfEn: "Read No. {n} in English (PDF)", pages: "sidor",
    online: "Läs artikeln på webbplatsen", how: "Så läser du Korpus",
    depths: [["30 sekunder", "Rubriken, Siffran och rutan På 30 sekunder ger dig fyndet och hur säkert det är."],
             ["5 minuter", "Artikeln berättar hur vi kom fram till det, med diagram i procent och stenarna som exempel."],
             ["På djupet", "Rutan Så säkra är vi, källorna och de öppna data på vitkirunor.se låter dig pröva allt själv."]],
    about: "Om Korpus",
    aboutText: ["Korpus är Vitkis tidskrift för digital och kvantitativ runforskning. Varje nummer samlar artiklar, en rapport från verkstaden och en metodnotis i en form som går att läsa på en kaffepaus.",
                "Analyserna förregistreras: planen låses innan vi räknar, och när ett resultat inte håller säger vi det. Texterna får spridas fritt under CC BY 4.0; bilderna har egna licenser, angivna vid varje bild."],
    editor: "Redaktör: Viktor Kvant.", contact: "Hör av dig", all: "Alla nummer",
  },
  en: {
    kicker: "Journal", sub: "Carved & counted – digital runic research from Vitki",
    intro: "Korpus measures the whole runestone corpus at once – against soils, shorelines, place names, grave fields and roads – and tests every pattern against chance before we call it a finding. The journal is written for the curious reader with little time, and it is free: read it as a PDF in English or Swedish.",
    latest: "Latest issue", contents: "In this issue", read: "Read", pdfSv: "Läs nr {n} på svenska (PDF)", pdfEn: "Read No. {n} as a PDF", pages: "pages",
    online: "Read the article on the website", how: "How to read Korpus",
    depths: [["30 seconds", "The headline, The number and In 30 seconds give you the finding and how certain it is."],
             ["5 minutes", "The article tells how we got there, with charts in percent and the stones as examples."],
             ["In depth", "How sure we are, the sources and the open data at vitkirunor.se let you test everything yourself."]],
    about: "About Korpus",
    aboutText: ["Korpus is Vitki's journal of digital and quantitative runic research. Each issue gathers articles, a report from the workshop and a method note in a form that can be read over a coffee break.",
                "Analyses are pre-registered: the plan is locked before we count, and when a result does not hold, we say so. The texts may be shared freely under CC BY 4.0; the images carry their own licences, given with each image."],
    editor: "Editor: Viktor Kvant.", contact: "Get in touch", all: "All issues",
  },
};

const rust = "text-[#b7410e]";

function PdfButtons({ i, lang }: { i: KorpusIssue; lang: "sv" | "en" }) {
  const t = T[lang];
  const own = lang === "en" ? { href: i.pdf_en, label: t.pdfEn, size: i.size_en } : { href: i.pdf_sv, label: t.pdfSv, size: i.size_sv };
  const other = lang === "en" ? { href: i.pdf_sv, label: t.pdfSv, size: i.size_sv } : { href: i.pdf_en, label: t.pdfEn, size: i.size_en };
  return (
    <div className="flex flex-wrap gap-3">
      <a href={own.href} className="tap inline-flex items-center h-11 px-5 rounded-full bg-[#b7410e] text-white text-sm font-bold hover:bg-[#9a370c]">
        {own.label.replace("{n}", String(i.nr))} <span className="ml-2 font-normal opacity-80">{own.size}</span>
      </a>
      <a href={other.href} className="tap inline-flex items-center h-11 px-5 rounded-full border border-slate-900/20 text-sm font-semibold hover:border-slate-900/50">
        {other.label.replace("{n}", String(i.nr))} <span className="ml-2 font-normal text-slate-500">{other.size}</span>
      </a>
    </div>
  );
}

export default function KorpusPage({ lang }: { lang: "sv" | "en" }) {
  const t = T[lang];
  const en = lang === "en";
  const [latest, ...older] = KORPUS_ISSUES;
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(korpusJsonLd(lang)).replace(/</g, "\\u003c") }} />
      <section className="max-w-6xl mx-auto px-6 pt-16 md:pt-20">
        <div className={`text-xs font-bold uppercase tracking-[0.2em] ${rust} mb-3`}>{t.kicker}</div>
        <h1 className="text-6xl md:text-8xl font-serif font-black tracking-tight leading-none">Korpus</h1>
        <p className="mt-4 text-lg md:text-xl font-semibold text-slate-700 border-t-2 border-[#b7410e] inline-block pt-2">{t.sub}</p>
        <p className="mt-6 max-w-3xl text-lg text-slate-600 leading-relaxed">{t.intro}</p>
      </section>

      {latest && (
        <section className="max-w-6xl mx-auto px-6 pt-14">
          <div className="grid md:grid-cols-[minmax(0,22rem)_1fr] gap-10 items-start">
            <figure>
              <a href={en ? latest.pdf_en : latest.pdf_sv} className="block shadow-xl ring-1 ring-slate-900/10 hover:shadow-2xl transition-shadow">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={en ? latest.cover_en : latest.cover_sv} alt={en ? latest.cover_alt_en : latest.cover_alt_sv} width={909} height={1287} className="w-full h-auto block" />
              </a>
              <figcaption className="mt-2 text-xs text-slate-500">{en ? latest.cover_credit_en : latest.cover_credit_sv}</figcaption>
            </figure>
            <div>
              <div className={`text-xs font-bold uppercase tracking-[0.2em] ${rust}`}>{t.latest}</div>
              <h2 className="mt-2 text-3xl md:text-4xl font-serif font-bold">{en ? latest.label_en : latest.label_sv}</h2>
              <p className="mt-3 text-lg text-slate-600 leading-relaxed">{en ? latest.lead_en : latest.lead_sv}</p>
              <div className="mt-6"><PdfButtons i={latest} lang={lang} /></div>
              <p className="mt-2 text-sm text-slate-500">{latest.pages} {t.pages} · PDF</p>
              <div className={`mt-10 text-xs font-bold uppercase tracking-[0.2em] ${rust}`}>{t.contents}</div>
              <ol className="mt-3 divide-y divide-slate-900/10 border-y border-slate-900/10">
                {latest.contents.map((c, n) => (
                  <li key={n} className="py-4 grid grid-cols-[2.5rem_1fr] gap-3">
                    <span className={`font-serif font-black text-xl ${rust}`}>{String(n + 1).padStart(2, "0")}</span>
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-500">{en ? c.theme_en : c.theme_sv}</div>
                      <div className="font-serif font-bold text-lg leading-snug">{en ? c.title_en : c.title_sv}</div>
                      {c.slug && (
                        <Link href={en ? enPostPath(c.slug) : postPath(c.slug)} prefetch={false} className={`tap text-sm font-semibold ${rust} hover:underline`}>
                          {t.online} →
                        </Link>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>
      )}

      <section className="max-w-6xl mx-auto px-6 pt-16">
        <h2 className="text-2xl font-serif font-bold">{t.how}</h2>
        <div className="mt-5 grid md:grid-cols-3 gap-4">
          {t.depths.map(([h, d]) => (
            <div key={h} className="bg-[#f8ece4] p-6">
              <div className={`font-serif font-black text-2xl ${rust}`}>{h}</div>
              <p className="mt-2 text-sm text-slate-700 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pt-16 pb-24 grid md:grid-cols-2 gap-12">
        <div>
          <h2 className="text-2xl font-serif font-bold">{t.about}</h2>
          {t.aboutText.map((p, n) => <p key={n} className="mt-3 text-slate-700 leading-relaxed">{p}</p>)}
          <p className="mt-3 text-slate-700">
            {t.editor} <Link href={en ? EN_CONTACT_PATH : CONTACT_PATH} prefetch={false} className={`font-semibold ${rust} hover:underline`}>{t.contact}</Link>
          </p>
        </div>
        <div>
          <h2 className="text-2xl font-serif font-bold">{t.all}</h2>
          <ul className="mt-3 divide-y divide-slate-900/10 border-y border-slate-900/10">
            {[latest, ...older].filter(Boolean).map((i) => (
              <li key={i.nr} className="py-3 flex flex-wrap items-baseline justify-between gap-3">
                <span className="font-serif font-bold">{en ? i.label_en : i.label_sv}</span>
                <span className="text-sm space-x-4">
                  <a href={i.pdf_sv} className={`font-semibold ${rust} hover:underline`}>{en ? "Swedish" : "Svenska"} (PDF)</a>
                  <a href={i.pdf_en} className={`font-semibold ${rust} hover:underline`}>{en ? "English" : "Engelska"} (PDF)</a>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
