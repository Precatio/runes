"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ExportTable from "@/components/ExportTable";
import { API_URL } from "@/lib/api";

// GET /api/r/scan: every pattern of the map against the distance to every kind of place (r/remains.R)
export interface ScanCell {
  feature: string; kind: string; radius_km: number; n_near: number; share_near: number; share_far: number;
  n: number; or: number; lo: number; hi: number; p: number; q_bh: number;
  halves?: { replicated: boolean }; time?: { n: number; or: number; p: number } | null;
}
export interface Scan {
  available: boolean; reason?: string; computed_at?: string; n_tests: number; n_sig: number; n_replicated: number;
  kinds: string[]; kind_labels: Record<string, string>; features: { key: string; label: string; group: string }[]; cells: ScanCell[];
}

// Diverging: warm when the pattern is more common nearer the places, cool when it is rarer; grey when not significant
const WARM = ["#fbe3d6", "#f0a37f", "#b7410e"];
const COOL = ["#dbe8f7", "#86b6ef", "#1c5cab"];
const NONE = "#f1f0ee";
function cellStyle(c: ScanCell) {
  if (c.q_bh >= 0.05) return { background: NONE, color: "#94a3b8" };
  const m = Math.abs(Math.log2(c.or));
  const step = m < 0.2 ? 0 : m < 0.35 ? 1 : 2;
  const bg = (c.or > 1 ? WARM : COOL)[step];
  return { background: bg, color: step === 2 ? "#ffffff" : "#0f172a" };
}
const n2 = (x: number) => x.toFixed(2).replace(".", ",");
const qText = (q: number) => (q < 0.001 ? "< 0,001" : q.toFixed(3).replace(".", ","));

/** The hidden patterns in the landscape: a grid of patterns against kinds of place, computed in R. */
export default function LandscapeScan({ onPick, current, scan: given }: {
  onPick: (feature: string, kind: string, km: number) => void; current?: { feature: string; kind: string }; scan?: Scan | null;
}) {
  const [fetched, setFetched] = useState<Scan | null>(null);
  const [onlyRep, setOnlyRep] = useState(false);
  useEffect(() => {
    if (given !== undefined) return;
    fetch(`${API_URL}/api/r/scan`).then(r => (r.ok ? r.json() : null)).then(setFetched).catch(() => setFetched(null));
  }, [given]);
  const scan = given !== undefined ? given : fetched;
  if (!scan) return null;
  if (!scan.available) {
    return <p className="text-xs text-slate-500">Dolda mönster i landskapet: {scan.reason}</p>;
  }
  const byKey = new Map(scan.cells.map(c => [`${c.feature}|${c.kind}`, c]));
  const rows = scan.features.filter(f => scan.kinds.some(k => byKey.has(`${f.key}|${k}`)));
  // Every cell with all its numbers, for the export
  const allRows = () => [
    ["Mönster", "Plats", "Oddskvot när avståndet halveras", "95 % nedre", "95 % övre", "p", "q (Benjamini–Hochberg)",
     "Båda halvorna", "Oddskvot med tiden konstant", "Radie (km)", "Stenar inom radien", "Andel inom radien", "Andel övriga", "Stenar"],
    ...scan.cells.map(c => [
      scan.features.find(f => f.key === c.feature)?.label ?? c.feature, scan.kind_labels[c.kind] ?? c.kind,
      n2(c.or), n2(c.lo), n2(c.hi), String(c.p).replace(".", ","), String(c.q_bh).replace(".", ","),
      c.halves?.replicated ? "ja" : "nej", c.time ? n2(c.time.or) : "", String(c.radius_km).replace(".", ","),
      String(c.n_near), `${Math.round(c.share_near * 100)} %`, `${Math.round(c.share_far * 100)} %`, String(c.n),
    ]),
  ];
  return (
    <div>
      <p className="mt-2 text-xs text-slate-600 max-w-4xl">
        Varje ruta prövar om ett mönster blir vanligare (varmt) eller ovanligare (kallt) ju närmare stenen står en sorts plats –
        utan vald radie, med landskapet konstant och alla {scan.n_tests} rutor justerade tillsammans (Benjamini–Hochberg). Talet
        är oddskvoten när avståndet halveras; ✓ betyder att sambandet håller i båda halvorna av korpusen. Grått klarar inte
        justeringen. Flyttade stenar räknas inte. Klicka på en ruta för att se den på kartan.
      </p>
      <label className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-slate-700">
        <input type="checkbox" checked={onlyRep} onChange={e => setOnlyRep(e.target.checked)} />
        Visa bara de som håller i båda halvorna
      </label>
      <div className="mt-2 overflow-x-auto">
        <ExportTable name="Dolda mönster i landskapet" rows={allRows}>
        <table className="text-xs border-separate" style={{ borderSpacing: 2 }}>
          <thead>
            <tr>
              <th />
              {scan.kinds.map(k => (
                <th key={k} className="px-1 pb-1 font-semibold text-slate-600 align-bottom text-left" style={{ minWidth: 64 }}>
                  {scan.kind_labels[k] ?? k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(f => (
              <tr key={f.key}>
                <th className="pr-2 text-left font-semibold text-slate-700 whitespace-nowrap">{f.label}</th>
                {scan.kinds.map(k => {
                  const c = byKey.get(`${f.key}|${k}`);
                  if (!c) return <td key={k} className="text-center text-slate-300">–</td>;
                  const rep = !!c.halves?.replicated && c.q_bh < 0.05;
                  const dim = onlyRep && !rep;
                  const sel = current?.feature === f.key && current?.kind === k;
                  const st = dim ? { background: NONE, color: "#cbd5e1" } : cellStyle(c);
                  const tip = `${f.label} – ${scan.kind_labels[k] ?? k}: oddskvot ${n2(c.or)} (${n2(c.lo)}–${n2(c.hi)}) när avståndet halveras, `
                    + `q ${qText(c.q_bh)}${rep ? ", håller i båda halvorna" : c.q_bh < 0.05 ? ", bara i en halva" : ""}. Inom ${String(c.radius_km).replace(".", ",")} km: `
                    + `${Math.round(c.share_near * 100)} % av ${c.n_near} stenar, mot ${Math.round(c.share_far * 100)} % av övriga.`
                    + (c.time ? ` Med tiden konstant: oddskvot ${n2(c.time.or)}.` : "");
                  return (
                    <td key={k} className="p-0">
                      <button type="button" onClick={() => onPick(f.key, k, c.radius_km)} title={tip} aria-label={tip}
                        className={`w-full h-8 rounded-md font-semibold tabular-nums ${sel ? "ring-2 ring-slate-900" : ""}`} style={st}>
                        {n2(c.or)}{rep ? " ✓" : ""}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        </ExportTable>
      </div>
      <p className="mt-2 text-[11px] text-slate-500">
        Mönster som håller i båda halvorna finns också i <Link href="/luckor" className="underline">Forskningsluckor</Link> med hypotes och
        prov. Beräknat i korpusanalysen{scan.computed_at ? ` (${new Date(scan.computed_at).toLocaleDateString("sv-SE")})` : ""}; METHODS.md 17.
      </p>
    </div>
  );
}
