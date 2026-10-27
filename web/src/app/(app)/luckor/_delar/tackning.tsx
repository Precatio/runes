import { Fragment, useEffect, useState } from "react";
import Link from "next/link";
import { Answer } from "@/components/Explain";
import { API_URL } from "@/lib/api";
import { fmtP } from "@/lib/significance";
import { DocsNote } from "@/components/KnownLimitations";
import ExportTable from "@/components/ExportTable";
import type { CategoryStats, ProvinceRow, SizeStats, SortValue } from "./typer";
import { BarLink, CELL_LINK, TH_ROW, fmt, gapHref, signaHref, useSorted } from "./gemensamt";

export function SizePanel() {
  const [data, setData] = useState<SizeStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/research/stone_size`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(setData).catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta storleksanalysen."));
  }, []);
  if (error) return <p className="text-red-700 font-semibold">{error}</p>;
  if (!data) return <p className="text-slate-500">Räknar (permutationstest inom landskap) …</p>;
  if (data.error) return <p className="text-slate-600">{data.error}</p>;
  const ratio = (r: number | null) => (r == null ? "–" : `${r >= 1 ? "+" : "−"}${Math.abs(Math.round((r - 1) * 100))} %`);
  const sig = (q: number | null) => (q != null && q < 0.05 ? "font-semibold text-slate-900" : "text-slate-600");
  const sigTests = data.tests.filter(t => t.q != null && t.q < 0.05);
  return (
    <div className="space-y-5 text-sm">
      <Answer topic="Storlek" question="Restes större stenar för större syften?"
        why="Storleken kan säga något om beställarens resurser och om vad stenen skulle uttrycka."
        headline={{ value: `${sigTests.length} av ${data.tests.length}`, label: "jämförelser där stenarnas höjd skiljer sig signifikant (inom landskap)" }}
        answer={sigTests.length
          ? <>Med hänsyn till landskapet skiljer sig höjden signifikant för {sigTests.map(t => `${t.variable.replace(/^Syfte: /, "").toLowerCase()} (${ratio(t.ratio)} mot övriga stenar)`).join(" och ")}. Höjden är känd för {data.n} av {data.meta.n_runestones} runstenar.</>
          : <>Ingen av jämförelserna visar en signifikant skillnad i höjd när landskapet hålls konstant. Höjden är känd för {data.n} av {data.meta.n_runestones} runstenar.</>}
        interpretation={["En högre sten för vissa syften kan spegla beställarnas resurser eller budskapets vikt – men också vilken sten som fanns att tillgå."]}
        notSaying={["Måtten är ofullständiga och ojämna: höjd över mark för resta stenar, fragment uteslutna.",
          "En stor sten har plats för en längre text, så text och storlek hänger ihop av praktiska skäl."]} />
      <p className="text-slate-600 max-w-4xl">
        Restes större stenar för större syften och av mäktigare personer? Höjden för {data.n} av {data.meta.n_runestones}{" "}
        vikingatida runstenar kunde läsas ur Kulturmiljöregistret (median {fmt(data.median_height_m)} m, kvartiler{" "}
        {fmt(data.quartiles_m[0])}–{fmt(data.quartiles_m[1])} m; fragment uteslutna). Alla jämförelser görs <em>inom landskap</em>{" "}
        (bergart och lokal sed påverkar storleken): skillnaden anges som hur mycket högre eller lägre stenarna är, med
        permutationstest inom landskap och q-värden korrigerade för antalet test.
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full">
          <thead><tr><th className="p-2 text-left text-[11px] uppercase text-slate-500">Variabel</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Stenar</th>
            <th className="p-2 text-left text-[11px] uppercase text-slate-500">Höjd mot övriga (inom landskap)</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Median med / utan</th>
            <th className="p-2 text-left text-[11px] uppercase text-slate-500">p</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">q</th></tr></thead>
          <tbody>{data.tests.map(t => (
            <tr key={t.variable} className={`border-t border-slate-900/5 ${sig(t.q)}`}>
              <td className="p-2">{t.variable}</td><td className="p-2">{t.n}</td><td className="p-2">{ratio(t.ratio)}</td>
              <td className="p-2">{fmt(t.median_with_m)} / {fmt(t.median_without_m)} m</td><td className="p-2">{fmtP(t.p)}</td><td className="p-2">{fmtP(t.q)}</td>
            </tr>
          ))}</tbody>
        </table></ExportTable>
      </div>
      <div>
        <p className="font-bold text-slate-900 mb-1">Samband med texten (rangkorrelation inom landskap)</p>
        <ul className="list-disc pl-5 text-slate-700">
          {data.correlations.map(c => <li key={c.variable}>{c.variable}: rho {fmt(c.rho)} (p {fmtP(c.p)}, {c.n} stenar)</li>)}
        </ul>
        <p className="text-xs text-slate-500 mt-1">En större sten har plats för en längre text; därför visas också antalet personer med hänsyn till textens längd.</p>
      </div>
      {data.carvers.length > 0 && (
        <div className="overflow-x-auto">
          <p className="font-bold text-slate-900 mb-1">Ristare med minst tio stenar med kända mått</p>
          <ExportTable><table className="w-full">
            <thead><tr><th className="p-2 text-left text-[11px] uppercase text-slate-500">Ristare</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Stenar</th>
              <th className="p-2 text-left text-[11px] uppercase text-slate-500">Median</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Höjd mot andra i landskapet</th>
              <th className="p-2 text-left text-[11px] uppercase text-slate-500">p</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">q</th></tr></thead>
            <tbody>{data.carvers.map(c => (
              <tr key={c.carver} className={`border-t border-slate-900/5 ${sig(c.q)}`}>
                <td className="p-2"><Link href={`/inskrifter?carver=${encodeURIComponent(c.carver)}`} className="text-[#b7410e] hover:underline">{c.carver}</Link></td>
                <td className="p-2">{c.n}</td><td className="p-2">{fmt(c.median_m)} m</td><td className="p-2">{ratio(c.ratio)}</td><td className="p-2">{fmtP(c.p)}</td><td className="p-2">{fmtP(c.q)}</td>
              </tr>
            ))}</tbody>
          </table></ExportTable>
        </div>
      )}
      <DocsNote anchor="10b-stenens-storlek-och-syfte">Hur måtten läses ut, hur de ska tolkas och vilka reservationer som gäller står i avsnitt 10b.</DocsNote>
    </div>
  );
}

export function CategoryPanel() {
  const [data, setData] = useState<CategoryStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/research/categories`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(setData).catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta kategorierna."));
  }, []);
  const rows = data?.carvers ?? [];
  const get: Record<string, (r: CategoryStats["carvers"][number]) => SortValue> = { carver: r => r.carver, n: r => r.n };
  for (const c of data?.categories ?? []) get[c.key] = r => r.counts[c.key]?.share;
  const { sorted, header } = useSorted(rows, get, { key: "n", desc: true });
  if (error) return <p className="text-red-700 font-semibold">{error}</p>;
  if (!data) return <p className="text-slate-500">Räknar …</p>;
  const pctTxt = (v: number) => `${(v * 100).toFixed(v < 0.01 ? 1 : 0).replace(".", ",")} %`;
  const label = Object.fromEntries(data.categories.map(c => [c.key, c.label.toLowerCase()]));
  const deviations = data.carvers.flatMap(r => Object.entries(r.counts).filter(([, v]) => v.direction !== "som genomsnittet")
    .map(([k, v]) => ({ carver: r.carver, cat: label[k] ?? k, dir: v.direction, share: v.share, q: v.q })));
  const carversWith = new Set(deviations.map(d => d.carver)).size;
  const examples = deviations.filter(d => d.dir === "över").sort((a, b) => a.q - b.q).slice(0, 3);
  return (
    <>
      <Answer topic="Syfte" question="Skiljer sig ristarna i vad inskrifterna handlar om?"
        why="Om en ristare oftare än andra ristar minnesstenar, brostenar eller böner kan det säga något om ristarens repertoar eller beställarkrets."
        headline={{ value: String(deviations.length), label: `signifikanta avvikelser från genomsnittet, hos ${carversWith} av ${data.carvers.length} ristare` }}
        answer={<>{carversWith} av {data.carvers.length} ristare med minst fem säkra inskrifter skriver signifikant oftare eller mer sällan än
          genomsnittet om något (q under 0,05){examples.length > 0 && <>, t.ex. {examples.map(e => `${e.carver} om ${e.cat} (${pctTxt(e.share)})`).join(", ")}</>}.</>}
        interpretation={["Skillnaderna kan spegla ristarens repertoar och skrivvanor, men också vilka beställare ristaren arbetade för och när.",
          "Kristna böner och brobyggen följer också tiden, så en ristare som var verksam sent har fler av dem."]}
        notSaying={["Kategorierna sätts med regler på Rundatas text och översättning; de kan överlappa och ibland missa.",
          "Att en ristare saknar en sällsynt kategori (t.ex. magiska inskrifter) är oftast väntat av en slump."]} />
      <p className="text-sm text-slate-600 mb-3 max-w-4xl">
        Vad inskrifterna handlar om, katalogiserat med regler på Rundatas normalisering och översättning ({data.n_inscriptions}{" "}
        vikingatida runstenar med text). Kategorierna kan överlappa. För varje ristare med minst fem säkra inskrifter jämförs
        andelen med genomsnittet. <span className="text-emerald-700 font-semibold">Grönt</span> = fler och{" "}
        <span className="text-amber-700 font-semibold">orange</span> = färre än väntat (q &lt; 0,05). Vid 0 visas sannolikheten att
        få 0 av en slump om ristaren följde genomsnittet – för sällsynta typer som magiska inskrifter är 0 därför oftast väntat.
        Klicka på en siffra för att se inskrifterna.
      </p>
      <div className="flex flex-wrap gap-2 mb-4 text-xs">
        {data.categories.map(c => (
          <span key={c.key} title={c.definition} className="px-2 py-1 rounded-lg bg-white border border-slate-200">
            <strong>{c.label}</strong> {c.count} ({pctTxt(c.base_rate)})
          </span>
        ))}
      </div>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead>
            <tr className={TH_ROW}>
              {header("carver", "Ristare")}{header("n", "Inskrifter")}
              {data.categories.map(c => <Fragment key={c.key}>{header(c.key, c.label, `${c.definition} Genomsnitt ${pctTxt(c.base_rate)}.`)}</Fragment>)}
            </tr>
          </thead>
          <tbody>
            {sorted.map(r => (
              <tr key={r.carver} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold"><Link href={`/inskrifter?carver=${encodeURIComponent(r.carver)}`} className={CELL_LINK}>{r.carver}</Link></td>
                <td className="p-2">{r.n}</td>
                {data.categories.map(c => {
                  const v = r.counts[c.key];
                  const color = v.direction === "över" ? "text-emerald-700 font-bold" : v.direction === "under" ? "text-amber-700 font-bold" : "text-slate-700";
                  const tip = `${v.k} av ${r.n} (${pctTxt(v.share)}); väntat ${v.expected.toFixed(1).replace(".", ",")}; p ${fmtP(v.p)}, q ${fmtP(v.q)}` +
                    (v.p_zero != null ? `; sannolikhet för 0 av en slump ${Math.round(v.p_zero * 100)} %` : "");
                  return (
                    <td key={c.key} className="p-2 text-xs" title={tip}>
                      {v.k > 0
                        ? <Link href={`/inskrifter?carver=${encodeURIComponent(r.carver)}&category=${c.key}&certain=1`} className={`${color} ${CELL_LINK}`}>{v.k}</Link>
                        : <span className={color}>0{v.p_zero != null && <span className="text-slate-400 font-normal"> ({Math.round(v.p_zero * 100)} %)</span>}</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
      <p className="text-[11px] text-slate-500 mt-3">{data.method}</p>
    </>
  );
}

export function ProvinceTable({ rows, measuredSigna }: { rows: ProvinceRow[]; measuredSigna: string[] }) {
  const { sorted, header } = useSorted(rows, {
    name: r => r.name, total: r => r.total, carver: r => r.carver / r.total, style: r => r.style / r.total,
    uncertain: r => r.uncertain_interpretation, lost: r => r.lost, measured: r => r.measured,
  }, { key: "total", desc: true });
  return (
    <div className="liquid-glass-island rounded-[32px] p-4 overflow-x-auto">
      <ExportTable><table className="w-full text-sm">
        <thead>
          <tr className={TH_ROW}>
            {header("name", "Landskap")}{header("total", "Runstenar")}{header("carver", "Med ristare")}
            {header("style", "Säker stilgrupp")}{header("uncertain", "Osäkert tolkade")}{header("lost", "Försvunna")}{header("measured", "Uppmätta")}
          </tr>
        </thead>
        <tbody>
          {sorted.map(r => (
            <tr key={r.code} className="border-t border-slate-900/5">
              <td className="p-2 font-semibold">
                <Link href={`/inskrifter?province=${encodeURIComponent(r.code)}`} className="hover:text-[#b7410e]">{r.name}</Link>
                {r.axelson && <span className="ml-2 text-[10px] font-bold text-slate-400" title="Ristaruppgifter främst ur Axelson 1993">AXELSON</span>}
              </td>
              <td className="p-2"><Link href={gapHref("runestone", r.code)} className={CELL_LINK}>{r.total}</Link></td>
              <td className="p-2"><BarLink value={r.carver} total={r.total} color="#b7410e" has={gapHref("carver", r.code)} missing={gapHref("no_carver", r.code)} /></td>
              <td className="p-2"><BarLink value={r.style} total={r.total} color="#0369a1" has={gapHref("style", r.code)} missing={gapHref("no_style", r.code)} /></td>
              <td className="p-2"><Link href={gapHref("uncertain_interpretation", r.code)} className={CELL_LINK}>{r.uncertain_interpretation}</Link></td>
              <td className="p-2"><Link href={gapHref("lost", r.code)} className={CELL_LINK}>{r.lost}</Link></td>
              <td className="p-2">
                {(() => {
                  const here = measuredSigna.filter(sg => sg.split(" ")[0] === r.code);
                  return here.length ? <Link href={signaHref(here)} className={CELL_LINK}>{r.measured}</Link> : r.measured;
                })()}
              </td>
            </tr>
          ))}
        </tbody>
      </table></ExportTable>
    </div>
  );
}
