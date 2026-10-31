import Link from "next/link";
import BlogBody, { dateLabel, type BlogPost } from "@/components/BlogBody";
import ReportCite from "@/components/ReportCite";
import EnglishEdition from "@/components/EnglishEdition";
import type { ImageSizes } from "@/lib/blogSeo";
import { bibtex, EN_REPORTS_PATH, REPORT_FORMS, REPORTS_PATH, reportParts } from "@/lib/report";
import { CONTACT_PATH, EN_CONTACT_PATH } from "@/lib/site";
import { paperFace } from "@/lib/paperFont";

// A research report laid out as an academic paper (not as an article): a title block with author, affiliation, report
// version, Vitki version and licence; a boxed abstract with the keywords and the highlights; a numbered table of contents
// beside numbered sections; figures with captions; references with hanging indents; and a citation box. Set in Source
// Serif 4, a book face made for long reading, on a white sheet; it prints as a paper (app/globals.css, .report-print).

const T = {
  sv: { kind: "Forskningsrapport", back: "← Forskningsrapporter", other: "Read in English →", version: "Rapportversion", published: "Publicerad",
        analysis: "Analys i Vitki", licence: "Licens", keywords: "Nyckelord", highlights: "Huvudpunkter", contents: "Innehåll",
        competing: "Konkurrerande intressen", funding: "Finansiering", cite: "Citera som", abstract: "Sammanfattning",
        updated: "Senast ändrad", series: "Vitki – forskningsrapporter" },
  en: { kind: "Research report", back: "← Research reports", other: "Läs på svenska →", version: "Report version", published: "Published",
        analysis: "Analysis in Vitki", licence: "Licence", keywords: "Keywords", highlights: "Highlights", contents: "Contents",
        competing: "Competing interests", funding: "Funding", cite: "Cite as", abstract: "Abstract",
        updated: "Last changed", series: "Vitki – research reports" },
};

export default function ReportPaper({ post, lang, sizes, otherHref }: { post: BlogPost; lang: "sv" | "en"; sizes?: ImageSizes; otherHref?: string | null }) {
  const en = lang === "en";
  const t = T[lang];
  const title = (en && post.title_en) || post.title;
  const parts = reportParts((en ? post.body_en : post.body) ?? "");
  const h = parts.header;
  const form = h?.form ?? REPORT_FORMS[0];
  const published = post.publishedAt ?? h?.date ?? null;
  const changed = post.updatedAt && published && post.updatedAt.slice(0, 10) !== published.slice(0, 10) ? post.updatedAt : null;
  const citation = h?.citation ?? `Kvant, V. ${title}.`;
  const meta = [
    h?.version && `${t.version} ${h.version}`,
    published && `${t.published} ${dateLabel(published, lang)}`,
    h?.appVersion && `${t.analysis} ${h.appVersion}`,
    h?.licence && `${t.licence} ${h.licence}`,
  ].filter(Boolean) as string[];
  return (
    <div className={`${paperFace.variable} report-print`}>
      {!en && <EnglishEdition href={otherHref ?? null} />}
      <nav aria-label={en ? "Breadcrumb" : "Brödsmulor"} className="no-print max-w-5xl mx-auto px-4 sm:px-6 pt-8 flex items-center justify-between gap-4 text-sm">
        <Link href={en ? EN_REPORTS_PATH : REPORTS_PATH} prefetch={false} className="tap font-bold text-[#b7410e] hover:underline">{t.back}</Link>
        {otherHref && <a href={otherHref} hrefLang={en ? "sv" : "en"} className="tap font-semibold text-[#b7410e] hover:underline">{t.other}</a>}
      </nav>
      <article lang={en ? "en" : "sv"} className="report-sheet max-w-5xl mx-auto mt-6 mb-16 bg-white border border-slate-900/10 shadow-sm px-5 sm:px-10 lg:px-16 py-10 sm:py-14" translate="no">
        <header className="text-center max-w-3xl mx-auto">
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#9a350b]">{t.kind} · Vitki</p>
          {/* the form and level (utdata/rapporter/MALL.md, version 2): how thoroughly the finding or method was tested */}
          <p className="mt-3"><span className={`inline-block rounded-full border px-3 py-0.5 text-[12px] font-semibold ${form.key === "full" || form.key === "method-full" ? "border-[#9a350b] text-[#9a350b]" : "border-slate-400 text-slate-600"}`}>{en ? form.en : form.sv}</span></p>
          <h1 className="report-title mt-5 text-[1.9rem] sm:text-[2.35rem] leading-[1.18] font-semibold text-slate-900">{title}</h1>
          <p className="mt-6 text-[1.05rem] text-slate-900">
            <Link href={en ? EN_CONTACT_PATH : CONTACT_PATH} prefetch={false} className="font-semibold hover:underline">{h?.author ?? post.author ?? "Viktor Kvant"}</Link>
          </p>
          {h?.affiliation && <p className="mt-1 text-sm italic text-slate-600">{h.affiliation[0].toUpperCase() + h.affiliation.slice(1)} · Vitki</p>}
          {meta.length > 0 && <p className="mt-4 text-[13px] text-slate-500">{meta.join("  ·  ")}</p>}
          {changed && <p className="mt-1 text-[13px] text-slate-500">{t.updated} {dateLabel(changed, lang)}</p>}
          <div className="mt-6"><ReportCite citation={citation} bibtex={bibtex(post, h)} lang={lang} /></div>
        </header>

        {parts.headerRaw && <p className="mt-8 text-sm italic text-slate-600 text-center">{parts.headerRaw.replace(/^\*|\*$/g, "")}</p>}

        {parts.abstract && (
          <section aria-labelledby="abstract" className="report-abstract mt-10 max-w-3xl mx-auto border-y border-slate-300 py-6">
            <h2 id="abstract" className="text-center text-[13px] font-semibold uppercase tracking-[0.2em] text-slate-900">{en ? t.abstract : parts.abstractTitle}</h2>
            <div className="report-body report-abstract-body mt-4"><BlogBody text={parts.abstract} lang={lang} /></div>
            {h && h.keywords.length > 0 && (
              <p className="mt-4 text-[15px] text-slate-700"><span className="font-semibold">{t.keywords}:</span> <span className="italic">{h.keywords.join(", ")}</span></p>
            )}
          </section>
        )}

        {parts.highlights && (
          <section aria-labelledby="highlights" className="mt-8 max-w-3xl mx-auto">
            <h2 id="highlights" className="text-[13px] font-semibold uppercase tracking-[0.2em] text-[#9a350b]">{t.highlights}</h2>
            <div className="report-body report-highlights mt-2"><BlogBody text={parts.highlights.md} lang={lang} /></div>
          </section>
        )}

        <div className="mt-12 lg:grid lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-12">
          <aside className="no-print hidden lg:block">
            <nav aria-label={t.contents} className="sticky top-6 text-sm">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{t.contents}</p>
              <ol className="mt-3 space-y-1.5 border-l border-slate-200 pl-3">
                {parts.sections.map(s => (
                  <li key={s.id}><a href={`#${s.id}`} className="block leading-snug text-slate-600 hover:text-[#9a350b]">{s.title}</a></li>
                ))}
              </ol>
            </nav>
          </aside>
          <div className="min-w-0">
            {parts.sections.map(s => {
              const refs = /^(Referenser|References)$/.test(s.title);
              const data = /^(Data och kod|Data and code)$/.test(s.title);
              return (
                <section key={s.id} id={s.id} aria-labelledby={`${s.id}-h`} className="scroll-mt-6 mb-10">
                  <h2 id={`${s.id}-h`} className="report-h2 text-[1.35rem] font-semibold text-slate-900 border-b border-slate-200 pb-1.5 mb-5">{s.title}</h2>
                  <div className={`report-body${refs ? " report-refs" : ""}${data ? " report-data" : ""}`}><BlogBody text={s.md} sizes={sizes} lang={lang} /></div>
                </section>
              );
            })}
            {h && (h.competing || h.funding) && (
              <section className="mb-10 text-sm text-slate-600">
                {h.competing && <p><span className="font-semibold text-slate-800">{t.competing}:</span> {h.competing}.</p>}
                {h.funding && <p className="mt-1"><span className="font-semibold text-slate-800">{t.funding}:</span> {h.funding}.</p>}
              </section>
            )}
            <section className="border-t border-slate-300 pt-5 text-sm text-slate-600">
              <p className="font-semibold text-slate-800">{t.cite}</p>
              <p className="mt-1 leading-relaxed">{citation}</p>
            </section>
          </div>
        </div>
      </article>
    </div>
  );
}
