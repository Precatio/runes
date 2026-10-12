// Export of tables as CSV and Excel (.xlsx), always with the source: where the data come from, under which licence, the
// page it was exported from and the attribution of Vitki (NOTICE). Written without libraries: the .xlsx file is a zip of
// a few XML files, stored without compression.

export type Cell = string | number | null;
export interface ExportMeta { title: string; sources: string[]; url: string; date: string }

const VITKI = "Bygger på Vitki, ursprungligen utvecklad av Viktor Kvant (https://github.com/Precatio/runes).";
const CITE = "Citera Vitki enligt CITATION.cff (https://github.com/Precatio/runes/blob/main/CITATION.cff).";

// Sources by page, for tables that do not name their own
const RUNDATA = "Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License (ODbL 1.0); data som härleds ur Rundata omfattas av samma licens.";
const R = "Vitkis korpusanalyser i R; metoden beskrivs i METHODS.md (https://vitkirunor.se/docs/metod).";
const LANDSCAPE = "Fornlämningar: Kulturmiljöregistret, Riksantikvarieämbetet (via K-samsök). Ortnamn: © OpenStreetMap-bidragsgivare (ODbL). Medeltida kyrkor: Wikidata (CC0).";
const MEASURED = "Vitkis mätkorpus: bidragen publiceras under CC BY 4.0 med bidragsgivaren angiven.";
const ANALYSIS = "Vitkis analyser (mätningar, ortografi, syntes); metoden beskrivs i METHODS.md.";
export const SOURCES = { RUNDATA, R, LANDSCAPE, MEASURED, ANALYSIS };

export function sourcesFor(pathname: string): string[] {
  if (pathname.startsWith("/statistik") || pathname.startsWith("/karta")) return [R, RUNDATA, LANDSCAPE];
  if (pathname.startsWith("/korpus") || pathname.startsWith("/jamfor")) return [MEASURED, RUNDATA];
  if (pathname.startsWith("/inskrifter") || pathname.startsWith("/stilgrupper")) return [RUNDATA];
  return [ANALYSIS, RUNDATA];
}

export function metaLines(m: ExportMeta): [string, string][] {
  return [
    ["Tabell", m.title],
    ...m.sources.map((s, i) => [i === 0 ? "Källa" : "", s] as [string, string]),
    ["Exporterad från", m.url],
    ["Datum", m.date],
    ["Programvara", VITKI],
    ["Citering", CITE],
    ["Not", "Andelar i procent är exporterade som decimaltal (0,25 = 25 %). Celler som \"< 0,001\" är text."],
  ];
}

// Numbers as the pages show them, in Swedish: "1 563", "1,26", "−0,4", "25 %"
const NUM = /^[−-]?\d{1,3}(?:[\s  ]\d{3})*(?:,\d+)?$|^[−-]?\d+(?:,\d+)?$/;
export function parseCell(text: string): { v: Cell; pct?: boolean } {
  const t = text.replace(/\s+/g, " ").trim();
  if (!t || t === "–" || t === "—") return { v: t ? null : "" };
  const pct = /^(.*\S)\s?%$/.exec(t);
  const body = pct ? pct[1] : t;
  if (NUM.test(body) || /^[−-]?\d+(?:[.,]\d+)?e[−-]?\d+$/i.test(body)) {
    const n = Number(body.replace(/[\s  ]/g, "").replace(/−/g, "-").replace(",", "."));
    if (Number.isFinite(n)) return pct ? { v: n / 100, pct: true } : { v: n };
  }
  return { v: t };
}

/** The table as rows of text, header rows first; a cell spanning columns is followed by empty cells. */
export function tableRows(table: HTMLTableElement): string[][] {
  const out: string[][] = [];
  for (const tr of Array.from(table.rows)) {
    const row: string[] = [];
    for (const cell of Array.from(tr.cells)) {
      const el = cell as HTMLElement;
      const txt = (el.innerText || el.textContent || "").replace(/\s*\n\s*/g, " ").trim();
      row.push(txt);
      for (let i = 1; i < (cell as HTMLTableCellElement).colSpan; i++) row.push("");
    }
    if (row.some(c => c !== "")) out.push(row);
  }
  return out;
}

function csvField(v: Cell) {
  if (v == null) return "";
  const s = typeof v === "number" ? String(v) : v;
  return /[",\n\r#]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** CSV with comma and decimal point; the source first, on lines starting with # (read.csv(comment.char = "#") and
 *  pandas.read_csv(comment = "#") skip them). With a byte order mark, so that Excel reads the letters right. */
export function toCSV(rows: string[][], meta: ExportMeta): Blob {
  const head = metaLines(meta).map(([k, v]) => `# ${k ? `${k}: ` : "  "}${v}`);
  const body = rows.map((r, i) => r.map(c => csvField(i === 0 ? c : parseCell(c).v)).join(","));
  return new Blob(["﻿" + [...head, ...body].join("\r\n") + "\r\n"], { type: "text/csv;charset=utf-8" });
}

// ---- xlsx ------------------------------------------------------------------------------------------------------------
const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")
  .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "");
const colName = (i: number) => { let s = ""; for (i++; i > 0; i = Math.floor((i - 1) / 26)) s = String.fromCharCode(65 + ((i - 1) % 26)) + s; return s; };

function sheetXml(rows: { v: Cell; pct?: boolean; bold?: boolean }[][], freeze: boolean, widths: number[]) {
  const cols = widths.map((w, i) => `<col min="${i + 1}" max="${i + 1}" width="${Math.min(60, Math.max(8, w + 2))}" customWidth="1"/>`).join("");
  const data = rows.map((r, ri) => `<row r="${ri + 1}">${r.map((c, ci) => {
    const ref = `${colName(ci)}${ri + 1}`;
    const s = c.bold ? ' s="1"' : c.pct ? ' s="2"' : "";
    if (c.v == null || c.v === "") return `<c r="${ref}"${s}/>`;
    if (typeof c.v === "number") return `<c r="${ref}"${s}><v>${c.v}</v></c>`;
    return `<c r="${ref}" t="inlineStr"${s}><is><t xml:space="preserve">${esc(c.v)}</t></is></c>`;
  }).join("")}</row>`).join("");
  const pane = freeze ? '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>' : "";
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">${pane}${cols ? `<cols>${cols}</cols>` : ""}<sheetData>${data}</sheetData></worksheet>`;
}

const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(b: Uint8Array) { let c = 0xffffffff; for (let i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }

/** A zip archive with the files stored as they are. */
function zip(files: [string, string][]): Blob {
  const enc = new TextEncoder();
  const parts: Uint8Array[] = [], central: Uint8Array[] = [];
  let offset = 0;
  for (const [name, text] of files) {
    const data = enc.encode(text), nm = enc.encode(name), crc = crc32(data);
    const local = new DataView(new ArrayBuffer(30));
    [[0, 0x04034b50, 4], [4, 20, 2], [6, 0x0800, 2], [8, 0, 2], [10, 0, 2], [12, 0x21, 2], [14, crc, 4], [18, data.length, 4], [22, data.length, 4], [26, nm.length, 2], [28, 0, 2]]
      .forEach(([o, v, n]) => (n === 4 ? local.setUint32(o, v, true) : local.setUint16(o, v, true)));
    parts.push(new Uint8Array(local.buffer), nm, data);
    const cd = new DataView(new ArrayBuffer(46));
    [[0, 0x02014b50, 4], [4, 20, 2], [6, 20, 2], [8, 0x0800, 2], [10, 0, 2], [12, 0, 2], [14, 0x21, 2], [16, crc, 4], [20, data.length, 4], [24, data.length, 4], [28, nm.length, 2], [30, 0, 2], [32, 0, 2], [34, 0, 2], [36, 0, 2], [38, 0, 4], [42, offset, 4]]
      .forEach(([o, v, n]) => (n === 4 ? cd.setUint32(o, v, true) : cd.setUint16(o, v, true)));
    central.push(new Uint8Array(cd.buffer), nm);
    offset += 30 + nm.length + data.length;
  }
  const size = central.reduce((s, b) => s + b.length, 0);
  const end = new DataView(new ArrayBuffer(22));
  [[0, 0x06054b50, 4], [4, 0, 2], [6, 0, 2], [8, files.length, 2], [10, files.length, 2], [12, size, 4], [16, offset, 4], [20, 0, 2]]
    .forEach(([o, v, n]) => (n === 4 ? end.setUint32(o, v, true) : end.setUint16(o, v, true)));
  return new Blob([...parts, ...central, new Uint8Array(end.buffer)] as BlobPart[],
    { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
}

/** An Excel workbook: the table on the sheet "Data" (header row frozen) and the source on "Källa och licens". */
export function toXLSX(rows: string[][], meta: ExportMeta): Blob {
  const data = rows.map((r, i) => r.map(c => (i === 0 ? { v: c, bold: true } : parseCell(c))));
  const n = Math.max(...rows.map(r => r.length), 1);
  const widths = Array.from({ length: n }, (_, i) => Math.max(...rows.map(r => (r[i] ?? "").length)));
  const metaRows = metaLines(meta).map(([k, v]) => [{ v: k, bold: true }, { v }]);
  const ct = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>`;
  const rels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`;
  const wb = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/><sheet name="Källa och licens" sheetId="2" r:id="rId2"/></sheets></workbook>`;
  const wbRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`;
  const styles = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/><xf numFmtId="9" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs></styleSheet>`;
  return zip([
    ["[Content_Types].xml", ct], ["_rels/.rels", rels], ["xl/workbook.xml", wb], ["xl/_rels/workbook.xml.rels", wbRels],
    ["xl/styles.xml", styles], ["xl/worksheets/sheet1.xml", sheetXml(data, true, widths)],
    ["xl/worksheets/sheet2.xml", sheetXml(metaRows, false, [18, 100])],
  ]);
}

export function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/** "Kristen bön nära kyrkor" → "vitki-kristen-bon-nara-kyrkor-2026-10-12". */
export function fileName(title: string, date: string) {
  const slug = title.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "").slice(0, 60);
  return `vitki-${slug || "tabell"}-${date}`;
}
