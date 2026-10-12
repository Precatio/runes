"use client";

import { usePathname } from "next/navigation";
import { useRef, type ReactNode } from "react";
import { download, fileName, sourcesFor, tableRows, toCSV, toXLSX, type ExportMeta } from "@/lib/exportTable";

/** The heading nearest above an element: the table's name in the file when it has none of its own. */
function nearestHeading(el: HTMLElement | null): string {
  for (let node: Element | null = el; node; node = node.parentElement) {
    for (let sib = node.previousElementSibling; sib; sib = sib.previousElementSibling) {
      const h = sib.matches("h1,h2,h3,h4") ? sib : sib.querySelector("h1,h2,h3,h4");
      if (h?.textContent?.trim()) return h.textContent.trim();
    }
  }
  return document.title.split("|")[0].trim() || "tabell";
}

/**
 * A table with buttons to download it as CSV or Excel. The file has the table as shown (in the language of the page)
 * and the source: the data's origin and licence (by page, or `sources`), the address it was exported from, the date and
 * the attribution of Vitki.
 */
export default function ExportTable({ children, name, sources, rows }: {
  children: ReactNode; name?: string; sources?: string[];
  // All rows, when the table shows only some of them (header row first)
  rows?: () => string[][];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const run = (kind: "csv" | "xlsx") => {
    const table = ref.current?.querySelector("table");
    const data = rows ? rows() : table ? tableRows(table) : [];
    if (!data.length) return;
    const date = new Date().toISOString().slice(0, 10);
    const title = name || nearestHeading(ref.current);
    const meta: ExportMeta = { title, sources: sources ?? sourcesFor(pathname), url: window.location.href, date };
    download(kind === "csv" ? toCSV(data, meta) : toXLSX(data, meta), `${fileName(title, date)}.${kind}`);
  };
  const btn = "rounded-md px-1.5 py-0.5 font-semibold text-slate-500 hover:bg-slate-900/5 hover:text-[#b7410e]";
  return (
    <div ref={ref} className="min-w-0">
      <div className="flex justify-end items-center gap-1 text-[11px] text-slate-400 mb-1 print:hidden" data-export-tools="">
        <span>Exportera:</span>
        <button type="button" onClick={() => run("csv")} className={btn} title="Ladda ner tabellen som CSV, med källan">CSV</button>
        <button type="button" onClick={() => run("xlsx")} className={btn} title="Ladda ner tabellen som Excel, med källan">Excel</button>
      </div>
      {children}
    </div>
  );
}
