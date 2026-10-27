"use client";

import Link from "next/link";
import { useEffect, useState, type CSSProperties } from "react";
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

// Diverging: warm when the pattern is more common nearer the places, cool when it is rarer. Full colour when the cell
// passes the adjustment for many tests, a pale tint when it only has p < 0.05 (a hint), grey otherwise.
const WARM = ["#fbe3d6", "#f0a37f", "#b7410e"];
const COOL = ["#dbe8f7", "#86b6ef", "#1c5cab"];
const HINT_WARM = "#fdf3ee", HINT_COOL = "#eef4fb";
const NONE = "#f1f0ee";
const MIRROR = "neutral"; // pm_neutral: no religious markers, the complement of pm_kristen
const sure = (c: ScanCell) => c.q_bh < 0.05;
const hint = (c: ScanCell) => !sure(c) && c.p < 0.05;
const holds = (c: ScanCell) => sure(c) && !!c.halves?.replicated;
function cellStyle(c: ScanCell) {
  if (hint(c)) return { background: c.or > 1 ? HINT_WARM : HINT_COOL, color: "#475569", outline: "1px dashed #94a3b8", outlineOffset: -2 };
  if (!sure(c)) return { background: NONE, color: "#94a3b8" };
  const m = Math.abs(Math.log2(c.or));
  const step = m < 0.2 ? 0 : m < 0.35 ? 1 : 2;
  const bg = (c.or > 1 ? WARM : COOL)[step];
  return { background: bg, color: step === 2 ? "#ffffff" : "#0f172a" };
}
const n2 = (x: number) => x.toFixed(2).replace(".", ",");
const pText = (q: number) => (q < 0.001 ? "< 0,001" : q.toFixed(3).replace(".", ","));
const pct = (x: number) => `${Math.round(x * 100)} %`;
const km = (x: number) => `${String(x).replace(".", ",")} km`;

/** One association in words: the direction, the shares within the radius, the odds ratio with and without time held
 * constant, and how sure it is. The labels stand in their own elements so the sentences around them translate. */
function Association({ c, scan }: { c: ScanCell; scan: Scan }) {
  const feature = scan.features.find(f => f.key === c.feature)?.label ?? c.feature;
  const kind = scan.kind_labels[c.kind] ?? c.kind;
  return (
    <li className="text-sm text-slate-700 leading-relaxed">
      <strong>{feature}:</strong>{" "}{c.or > 1 ? "vanligare närmare" : "ovanligare närmare"}{" "}<strong>{kind}</strong>.{" "}
      <span>{`${pct(c.share_near)} av ${c.n_near} stenar inom ${km(c.radius_km)} har mönstret, mot ${pct(c.share_far)} av övriga.`}</span>{" "}
      <span>{`Oddskvoten när avståndet halveras är ${n2(c.or)} (95 % ${n2(c.lo)}–${n2(c.hi)}).`}</span>{" "}
      {c.time && (
        <span>{c.time.p < 0.05
          ? `Sambandet står sig med tiden konstant (oddskvot ${n2(c.time.or)}).`
          : `Med tiden konstant försvagas det (oddskvot ${n2(c.time.or)}, p ${pText(c.time.p)}), så en del kan bero på att stenarna är från olika tid.`}</span>
      )}{" "}
      <span className="text-xs text-slate-500">{holds(c)
        ? `Klarar justeringen (q ${pText(c.q_bh)}) och håller i båda halvorna av korpusen.`
        : sure(c)
          ? `Klarar justeringen (q ${pText(c.q_bh)}) men håller bara i den ena halvan av korpusen.`
          : `Klarar inte justeringen för de många proven (p ${pText(c.p)}, q ${pText(c.q_bh)}).`}</span>
    </li>
  );
}

/** What the scan shows, in words: how many associations hold, and the strongest ones by tier. */
function Summary({ scan }: { scan: Scan }) {
  const n = scan.cells.length;
  // The lists leave out the pattern without religious markers: it is the mirror image of the Christian markers
  const cells = scan.cells.filter(c => c.feature !== MIRROR);
  const rep = cells.filter(holds).sort((a, b) => a.q_bh - b.q_bh);
  const half = cells.filter(c => sure(c) && !holds(c)).sort((a, b) => a.q_bh - b.q_bh);
  const hints = cells.filter(hint).sort((a, b) => a.p - b.p);
  const expected = Math.round(0.05 * n);
  const below = scan.cells.filter(c => c.p < 0.05).length;
  const more = below > 1.5 * expected;
  return (
    <div className="space-y-3">
      <div className="text-sm text-slate-800 space-y-1.5">
        <p>{`Genomsökningen prövar ${n} samband: varje mönster mot avståndet till varje sorts plats.`}</p>
        <p className="font-semibold">{rep.length + half.length === 0
          ? "Inget av dem klarar justeringen för att så många prov görs samtidigt."
          : `${rep.length + half.length} klarar justeringen för de många proven, och ${rep.length} av dem håller också i båda halvorna av korpusen.`}</p>
        <p>{more
          ? `${below} har p under 0,05, där slumpen ensam väntas ge omkring ${expected}. Det kan betyda att det finns svaga samband i landskapet. Men flera av proven mäter nästan samma sak (kristna markörer, kors och stenar utan religiösa markörer), så överskottet är osäkrare än det ser ut.`
          : `${below} har p under 0,05, ungefär så många som slumpen ensam väntas ge (omkring ${expected}).`}</p>
      </div>
      {rep.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Håller</h4>
          <ul className="space-y-2 list-disc pl-5">{rep.map(c => <Association key={c.feature + c.kind} c={c} scan={scan} />)}</ul>
        </div>
      )}
      {half.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Indikationer: bara i den ena halvan</h4>
          <ul className="space-y-2 list-disc pl-5">{half.slice(0, 5).map(c => <Association key={c.feature + c.kind} c={c} scan={scan} />)}</ul>
        </div>
      )}
      {hints.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Starkast, men inte säkra</h4>
          <ul className="space-y-2 list-disc pl-5">{hints.slice(0, 5).map(c => <Association key={c.feature + c.kind} c={c} scan={scan} />)}</ul>
          <p className="mt-1 text-xs text-slate-500">
            Dessa är ledtrådar att pröva med en egen analysplan, inte fynd. Mönstret utan religiösa markörer står inte i
            listorna, eftersom det är spegelbilden av de kristna markörerna och säger samma sak. Det finns i rutnätet.
          </p>
        </div>
      )}
    </div>
  );
}

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
     "Båda halvorna", "Oddskvot med tiden konstant", "p med tiden konstant", "Radie (km)", "Stenar inom radien",
     "Andel inom radien", "Andel övriga", "Stenar"],
    ...scan.cells.map(c => [
      scan.features.find(f => f.key === c.feature)?.label ?? c.feature, scan.kind_labels[c.kind] ?? c.kind,
      n2(c.or), n2(c.lo), n2(c.hi), String(c.p).replace(".", ","), String(c.q_bh).replace(".", ","),
      c.halves?.replicated ? "ja" : "nej", c.time ? n2(c.time.or) : "", c.time ? String(c.time.p).replace(".", ",") : "",
      String(c.radius_km).replace(".", ","), String(c.n_near), `${Math.round(c.share_near * 100)} %`,
      `${Math.round(c.share_far * 100)} %`, String(c.n),
    ]),
  ];
  const swatch = (style: CSSProperties) => <span className="inline-block w-4 h-3 rounded-sm align-middle mr-1" style={style} />;
  return (
    <div>
      <Summary scan={scan} />
      <details className="mt-3 text-xs text-slate-600 max-w-4xl">
        <summary className="cursor-pointer font-bold text-slate-700">Så räknas och läses sambanden</summary>
        <div className="mt-1.5 space-y-1.5 leading-relaxed">
          <p>
            Varje samband är en logistisk regression på avståndet från stenen till närmaste plats av sorten, utan vald
            radie och med landskapet konstant. Flyttade stenar räknas inte, eftersom deras avstånd säger inget om var de
            restes.
          </p>
          <p>
            Oddskvoten 1,20 betyder att oddsen för att en sten har mönstret är 20 % högre för varje gång avståndet till
            platsen halveras, till exempel från 4 km till 2 km. 1 betyder inget samband, och under 1 blir mönstret
            ovanligare närmare platsen. Andelarna inom radien är bara en läshjälp.
          </p>
          <p>
            När många samband prövas samtidigt ger slumpen några låga p-värden. Därför justeras alla tillsammans
            (Benjamini–Hochberg, q). Ett samband håller om q är under 0,05 och det dessutom syns i båda halvorna av
            korpusen, där stenarna delas socken för socken. Med tiden konstant visar om sambandet kan bero på att stenarna
            nära platserna är från en annan tid.
          </p>
        </div>
      </details>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-600">
        <span>{swatch({ background: WARM[2] })}Vanligare närmare, säkert</span>
        <span>{swatch({ background: COOL[2] })}Ovanligare närmare, säkert</span>
        <span>{swatch({ background: HINT_WARM, outline: "1px dashed #94a3b8", outlineOffset: -1 })}Antydan (p under 0,05, klarar inte justeringen)</span>
        <span>{swatch({ background: NONE })}Inget samband</span>
        <span>✓ Håller i båda halvorna</span>
      </div>
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
                  const rep = holds(c);
                  const dim = onlyRep && !rep;
                  const sel = current?.feature === f.key && current?.kind === k;
                  const st = dim ? { background: NONE, color: "#cbd5e1" } : cellStyle(c);
                  const tip = `${f.label} – ${scan.kind_labels[k] ?? k}: oddskvot ${n2(c.or)} (${n2(c.lo)}–${n2(c.hi)}) när avståndet halveras, `
                    + `p ${pText(c.p)}, q ${pText(c.q_bh)}${rep ? ", håller i båda halvorna" : sure(c) ? ", bara i en halva" : hint(c) ? ", antydan" : ""}. `
                    + `Inom ${km(c.radius_km)}: ${pct(c.share_near)} av ${c.n_near} stenar, mot ${pct(c.share_far)} av övriga.`
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
        Klicka på en ruta för att se sambandet på kartan. Samband som håller blir mönster att pröva i{" "}
        <Link href="/luckor" className="underline">Forskningsluckor</Link>. Beräknat i korpusanalysen
        {scan.computed_at ? ` (${new Date(scan.computed_at).toLocaleDateString("sv-SE")})` : ""}; METHODS.md 1e.
      </p>
    </div>
  );
}
