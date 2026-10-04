"use client";

import DOMPurify from "dompurify";
import { downloadFile } from "@/lib/export";

export interface ReportResult {
  html: string;
  markdown: string;
  latex: string;
  figures: { name: string; png: string }[];
  ai_used: boolean;
  ai_text: Record<string, string> | null;
}

// Downloads and an HTML preview of a generated report (sanitised – the AI sections are model output)
export default function ReportPreview({ report, base, busy, onDocx }: {
  report: ReportResult;
  base: string;
  busy: boolean;
  onDocx: () => void;
}) {
  const downloadFigure = (f: { name: string; png: string }) => {
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${f.png}`; a.download = f.name; a.click();
  };
  const downloadAllFigures = () => report.figures.forEach((f, i) => setTimeout(() => downloadFigure(f), i * 250));
  return (
    <>
      <div className="flex flex-wrap gap-2 items-center">
        <button onClick={onDocx} disabled={busy} className="px-4 py-2 bg-slate-900 text-white text-xs font-bold rounded-xl disabled:opacity-40">
          {busy ? "Skapar Word-fil …" : "Ladda ner Word (.docx)"}
        </button>
        <button onClick={() => downloadFile(`${base}.tex`, report.latex, "application/x-tex")} className="px-4 py-2 bg-white border border-slate-300 text-xs font-bold rounded-xl">LaTeX (.tex)</button>
        <button onClick={() => downloadFile(`${base}.md`, report.markdown, "text/markdown")} className="px-4 py-2 bg-white border border-slate-300 text-xs font-bold rounded-xl">Markdown (.md)</button>
        {report.figures.length > 0 && (
          <button onClick={downloadAllFigures} className="px-4 py-2 bg-white border border-slate-300 text-xs font-bold rounded-xl">
            Alla figurer ({report.figures.length} PNG)
          </button>
        )}
        <span className="text-xs text-slate-500">
          {report.ai_used ? "Innehåller AI-formulerade avsnitt (markerade) – granska innan användning." : "Ingen AI-text – inledning och diskussion skriver du själv."}
          {" "}LaTeX- och Markdown-filerna hänvisar till figurfilerna med samma namn.
        </span>
      </div>
      <article
        className="liquid-glass-island rounded-[32px] p-6 md:p-10 bg-white prose prose-slate max-w-none prose-table:text-sm prose-img:rounded-xl prose-img:mx-auto [&_figure]:my-8 [&_figcaption]:text-xs [&_figcaption]:text-slate-600 [&_.ai-badge]:ml-1 [&_.ai-badge]:text-[10px] [&_.ai-badge]:font-bold [&_.ai-badge]:uppercase [&_.ai-badge]:text-amber-700 [&_.caption]:text-xs [&_.caption]:italic [&_table]:w-full [&_table]:block [&_table]:overflow-x-auto [&_td]:border-t [&_td]:border-slate-200 [&_td]:px-2 [&_td]:py-1 [&_th]:px-2 [&_th]:text-left [&_.inscription]:not-italic [&_.inscription]:border-[#b7410e]"
        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(report.html) }}
      />
    </>
  );
}

export async function downloadBlob(res: Response, filename: string) {
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}
