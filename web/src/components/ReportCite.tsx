"use client";

import { useState } from "react";

// The report's "Cite" and "Print / PDF" buttons: the citation as text and as BibTeX, each copied with one click, and the
// browser's print dialog (the page has a print layout, app/globals.css .report-print), which also saves a PDF.
export default function ReportCite({ citation, bibtex, lang }: { citation: string; bibtex: string; lang: "sv" | "en" }) {
  const en = lang === "en";
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const copy = async (what: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(what);
      setTimeout(() => setCopied(null), 1800);
    } catch { /* the text stays selectable */ }
  };
  const btn = "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 hover:border-[#b7410e] hover:text-[#9a350b]";
  return (
    <div className="no-print">
      <div className="flex flex-wrap justify-center gap-2">
        <button type="button" className={btn} aria-expanded={open} onClick={() => setOpen(v => !v)}>{en ? "Cite" : "Citera"}</button>
        <button type="button" className={btn} onClick={() => window.print()}>{en ? "Print / save as PDF" : "Skriv ut / spara som PDF"}</button>
      </div>
      {open && (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4 text-left text-sm">
          <p className="font-semibold text-slate-900">{en ? "Cite as" : "Citera som"}</p>
          <p className="mt-1 leading-relaxed text-slate-700 select-all">{citation}</p>
          <button type="button" className="mt-2 text-xs font-semibold text-[#9a350b] hover:underline" onClick={() => copy("cite", citation)}>
            {copied === "cite" ? (en ? "Copied" : "Kopierad") : (en ? "Copy the citation" : "Kopiera citeringen")}
          </button>
          <p className="mt-4 font-semibold text-slate-900">BibTeX</p>
          <pre className="mt-1 overflow-x-auto whitespace-pre rounded border border-slate-200 bg-white p-3 text-xs leading-relaxed text-slate-700">{bibtex}</pre>
          <button type="button" className="mt-2 text-xs font-semibold text-[#9a350b] hover:underline" onClick={() => copy("bib", bibtex)}>
            {copied === "bib" ? (en ? "Copied" : "Kopierad") : (en ? "Copy BibTeX" : "Kopiera BibTeX")}
          </button>
        </div>
      )}
    </div>
  );
}
