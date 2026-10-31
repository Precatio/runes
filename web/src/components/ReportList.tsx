import Link from "next/link";
import { dateLabel, type BlogPost } from "@/components/BlogBody";
import { enReportPath, reportParts, reportPath } from "@/lib/report";
import { paperFace } from "@/lib/paperFont";

// The list of research reports, set like a journal's table of contents: date and report version, the title, the
// author and affiliation, the summary and the keywords, and the way to the other language. The posts carry their texts
// (the page fetches each report), so that the version and keywords can be read from the header line.
export default function ReportList({ posts, lang }: { posts: BlogPost[]; lang: "sv" | "en" }) {
  const en = lang === "en";
  if (!posts.length) {
    return <p className="mt-10 text-slate-600">{en ? "The first reports are being prepared." : "De första rapporterna förbereds."}</p>;
  }
  return (
    <ol className={`${paperFace.variable} mt-10 border-t border-slate-900/15`}>
      {posts.map(p => {
        const parts = reportParts((en ? p.body_en : p.body) ?? "");
        const h = parts.header;
        const title = (en && p.title_en) || p.title;
        const href = en ? enReportPath(p.slug) : reportPath(p.slug);
        const other = en ? reportPath(p.slug) : p.body_en ? enReportPath(p.slug) : null;
        return (
          <li key={p.slug} className="border-b border-slate-900/15 py-8">
            <p className="text-[12px] uppercase tracking-[0.15em] text-slate-500">
              {[dateLabel(p.publishedAt ?? h?.date, lang), h?.version && `${en ? "Report version" : "Rapportversion"} ${h.version}`].filter(Boolean).join("  ·  ")}
            </p>
            <h2 className="mt-2 text-[1.45rem] sm:text-[1.6rem] leading-snug font-semibold text-slate-900" style={{ fontFamily: "var(--font-paper), var(--font-serif)" }}>
              <Link href={href} prefetch={false} className="hover:text-[#9a350b]">{title}</Link>
            </h2>
            <p className="mt-2 text-sm text-slate-700">{h?.author ?? "Viktor Kvant"}{h?.affiliation ? <span className="italic text-slate-500"> · {h.affiliation[0].toUpperCase() + h.affiliation.slice(1)}</span> : null}</p>
            {((en ? p.summary_en : p.summary) ?? "") && (
              <p className="mt-3 text-[16px] leading-relaxed text-slate-700" style={{ fontFamily: "var(--font-paper), var(--font-serif)" }}>{en ? p.summary_en : p.summary}</p>
            )}
            {h && h.keywords.length > 0 && (
              <p className="mt-2 text-sm text-slate-500"><span className="font-semibold">{en ? "Keywords" : "Nyckelord"}:</span> <span className="italic">{h.keywords.join(", ")}</span></p>
            )}
            <p className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm font-semibold">
              <Link href={href} prefetch={false} className="tap text-[#b7410e] hover:underline">{en ? "Read the report →" : "Läs rapporten →"}</Link>
              {other && <a href={other} hrefLang={en ? "sv" : "en"} className="tap text-slate-600 hover:text-[#9a350b] hover:underline">{en ? "På svenska" : "In English"}</a>}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
