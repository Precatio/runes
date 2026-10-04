// Client-side file export helpers (CSV / JSON)

export function downloadFile(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function csvCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const s = typeof value === "number" ? String(value) : typeof value === "string" ? value : JSON.stringify(value);
  return /[",;\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCSV(rows: Record<string, unknown>[], columns?: string[]): string {
  const cols = columns ?? Array.from(new Set(rows.flatMap(r => Object.keys(r))));
  const lines = [cols.join(","), ...rows.map(r => cols.map(c => csvCell(r[c])).join(","))];
  // BOM so that Excel opens åäö correctly
  return "﻿" + lines.join("\n");
}

export function safeFilename(s: string): string {
  return s.replace(/[^\p{L}\p{N}_-]+/gu, "_").replace(/^_+|_+$/g, "") || "export";
}
