import { useEffect, useMemo, useState } from "react";
import { Answer } from "@/components/Explain";
import { API_URL } from "@/lib/api";
import { toggle } from "@/lib/tone";
import ExportTable from "@/components/ExportTable";
import type { SriKind, SriRundata } from "./typer";
import { StoneLinks, TH_ROW } from "./gemensamt";

// Rundata och SRI säger olika (src/sri_rundata.py): stones where the find history in Sveriges runinskrifter does not
// agree with Rundata or the app's move rule. A list to check, not a test; the move rule is not changed by it.

const KINDS: SriKind[] = ["sri_flyttad", "rundata_flyttad", "sri_forsvunnen", "rundata_forsvunnen"];

export function SriRundataPanel() {
  const [data, setData] = useState<SriRundata | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [kind, setKind] = useState<SriKind | "">("");
  const [prov, setProv] = useState("");
  useEffect(() => {
    fetch(`${API_URL}/api/research/sri-rundata`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(setData).catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta jämförelsen."));
  }, []);
  const rows = useMemo(() => (data?.rows ?? []).filter(r => (!kind || r.kind === kind) && (!prov || r.province === prov)), [data, kind, prov]);
  if (error) return <p className="text-red-700 font-semibold">{error}</p>;
  if (!data) return <p className="text-slate-500">Jämför SRI med Rundata …</p>;
  if (!data.available) return <p className="text-slate-600">{data.note}</p>;
  const kinds = data.kinds as Record<SriKind, { label: string; help: string }>;
  const n = data.n_compared ?? 0;
  const total = KINDS.reduce((a, k) => a + (data.counts[k] ?? 0), 0);
  const moved = data.counts.sri_flyttad ?? 0;
  const provinces = Object.keys(data.per_province ?? {}).sort();
  return (
    <div className="space-y-4">
      <Answer topic="SRI mot Rundata" question="Var säger SRI och Rundata olika om var stenen står och om den finns kvar?"
        why="Platsstudierna bygger på att stenen står där den restes, och räkningarna av försvunna stenar på Rundatas uppgift. Sveriges runinskrifter beskriver varje stens fyndhistoria, ofta med årtal och vem som flyttade den."
        headline={{ value: String(moved), label: `runstenar som SRI säger var flyttade men som appens flyttregel räknar som stående på sin plats` }}
        answer={<>Av {n} runstenar med en granskad fyndhistorik i SRI säger SRI och Rundata olika om {total}:
          {" "}{moved} är flyttade enligt SRI men räknas som stående på plats, {data.counts.rundata_flyttad ?? 0} står på sin
          ursprungliga plats enligt SRI men räknas som flyttade, {data.counts.sri_forsvunnen ?? 0} var försvunna när bandet
          skrevs men står som bevarade i Rundata, och {data.counts.rundata_forsvunnen ?? 0} beskrivs som bevarade i SRI men
          står som försvunna i Rundata.</>}
        interpretation={[
          "Den största gruppen är stenar som SRI säger flyttades men där Rundatas placering inte nämner det. Appens flyttregel läser Rundatas placering, så de räknas som stående på sin plats i platsstudierna (lerkanten, vägen, gravfälten).",
          "Banden skrevs 1900–1981 och Rundata är från 2018; en del av oenigheten är verkliga händelser efter bandet – en sten som flyttats, hittats igen eller försvunnit sedan.",
        ]}
        notSaying={[
          "Listan är ett förslag att granska, inte ett prov. Flyttregeln ändras inte av den (analysplan A1, tillägg 1).",
          "SRI:s uppgifter är utplockade av Anthropics språkmodell Claude och granskade i stickprov; läget och försvunnen/återfunnen höll 95–100 % rätt. Flyttningarnas detaljer höll inte och används inte.",
        ]} />
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <button onClick={() => setKind("")} className={toggle(!kind)}>Alla {total}</button>
        {KINDS.map(k => (
          <button key={k} onClick={() => setKind(kind === k ? "" : k)} className={toggle(kind === k)} title={kinds[k].help}>
            {kinds[k].label} {data.counts[k] ?? 0}
          </button>
        ))}
        <select value={prov} onChange={e => setProv(e.target.value)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-xs font-semibold outline-none">
          <option value="">Alla landskap</option>
          {provinces.map(p => <option key={p} value={p}>{data.per_province![p].name ?? p} ({data.per_province![p].compared} jämförda)</option>)}
        </select>
        <span className="text-slate-500">{rows.length} rader</span>
      </div>
      {kind && <p className="text-sm text-slate-600 max-w-4xl">{kinds[kind].help}</p>}
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr className={TH_ROW}>
            <th className="p-2 text-left">Sten</th><th className="p-2 text-left">Oenighet</th><th className="p-2 text-left">SRI säger</th>
            <th className="p-2 text-left">Rundata säger</th><th className="p-2 text-left">Runor 2020</th>
          </tr></thead>
          <tbody>
            {rows.slice(0, 400).map(r => (
              <tr key={`${r.signum}-${r.kind}`} className="border-t border-slate-900/5 align-top">
                <td className="p-2"><StoneLinks signum={r.signum} stacked /><div className="text-[11px] text-slate-500" translate="no">{r.place}</div></td>
                <td className="p-2 text-xs font-semibold">{r.label}</td>
                <td className="p-2 text-xs max-w-md">
                  <span className="font-semibold">{r.sri.value}</span>
                  {r.sri.quote && <div className="text-slate-600" translate="no">»{r.sri.quote}»</div>}
                  <div className="text-[11px] text-slate-500" translate="no">
                    {r.sri.volume} {r.sri.year}{r.sri.page ? `, s. ${r.sri.page}` : r.sri.article_pages.length ? `, artikeln s. ${r.sri.article_pages.join(", ")}` : ""}
                  </div>
                </td>
                <td className="p-2 text-xs">
                  <span translate="no">{r.rundata.text}</span>
                  <div className="text-[11px] text-slate-500">
                    {r.rundata.moved_rule ? "flyttregeln: flyttad" : "flyttregeln: på plats"} · {r.rundata.lost ? "försvunnen" : "bevarad"}
                  </div>
                </td>
                <td className="p-2 text-xs">{r.runor_original == null ? "–" : r.runor_original ? "ursprunglig plats" : "inte ursprunglig plats"}</td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
      {rows.length > 400 && <p className="text-xs text-slate-500">Visar de 400 första – filtrera för att se fler.</p>}
      <p className="text-[11px] text-slate-500 max-w-4xl">{data.method} Citaten är korta utdrag med sida (citaträtten); utgåvorna ligger utanför kodförrådet.</p>
    </div>
  );
}
