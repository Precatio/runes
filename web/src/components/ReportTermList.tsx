import { REPORT_TERMS } from "@/lib/reportTerms";
import { paperFace } from "@/lib/paperFont";

// The glossary of the research reports' statistical terms: each term with an anchor (#oddskvot), what it is and how to
// read the number, in plain words (lib/reportTerms.ts).
export default function ReportTermList({ lang }: { lang: "sv" | "en" }) {
  const en = lang === "en";
  return (
    <dl className={`${paperFace.variable} mt-10 border-t border-slate-900/15`} style={{ fontFamily: "var(--font-paper), var(--font-serif)" }}>
      {REPORT_TERMS.map(t => {
        const x = en ? t.en : t.sv;
        return (
          <div key={t.id} id={t.id} className="scroll-mt-24 border-b border-slate-900/15 py-6">
            <dt className="text-[1.25rem] font-semibold text-slate-900">
              <a href={`#${t.id}`} className="hover:text-[#9a350b]">{x.term}</a>
            </dt>
            <dd className="mt-2 text-[17px] leading-relaxed text-slate-800">{x.what}</dd>
            <dd className="mt-2 text-[17px] leading-relaxed text-slate-700"><span className="font-semibold">{en ? "How to read it: " : "Så läser man det: "}</span>{x.read}</dd>
          </div>
        );
      })}
    </dl>
  );
}

/** The glossary as schema.org DefinedTermSet, so that search engines can show the definitions. */
export function termsJsonLd(lang: "sv" | "en", url: string, name: string) {
  const en = lang === "en";
  return {
    "@context": "https://schema.org",
    "@type": "DefinedTermSet",
    name, url, inLanguage: en ? "en" : "sv-SE",
    hasDefinedTerm: REPORT_TERMS.map(t => {
      const x = en ? t.en : t.sv;
      return { "@type": "DefinedTerm", name: x.term, description: `${x.what} ${x.read}`, url: `${url}#${t.id}` };
    }),
  };
}
