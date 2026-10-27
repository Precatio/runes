import { Details } from "@/components/Explain";
import ExportTable from "@/components/ExportTable";
import type { Corpus, OddsRow } from "./typer";
import { Fig, Method, SectionIntro, Th, d2, pText, pc } from "./gemensamt";
import { sectionOf } from "./oversikt";

const odds = (o?: OddsRow | null) => (o ? `${d2(o.or, 2)} (${d2(o.lo, 2)}–${o.hi == null ? "∞" : d2(o.hi, o.hi >= 10 ? 0 : 2)})` : "–");

/** The messages of the runestones (r/messages.R): what they tell about the dead, by region, and the journeys. */
export function Messages({ data }: { data: Corpus }) {
  const m = data.messages, f = data.figure_urls.messages || {};
  if (!m) return <p className="text-sm text-slate-600">Budskapsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const cell = (region: string, direction: string) => m.travel.cells.find(c => c.region === region && c.direction === direction);
  const share = (c?: { k: number; n: number }) => (c && c.n ? `${pc(c.k / c.n)} (${c.k} av ${c.n})` : "–");
  return (
    <>
      <SectionIntro section={sectionOf(data, "messages")} patterns={data.patterns} />
      <p className="text-sm text-slate-600 max-w-3xl">
        {m.n_legible.toLocaleString("sv-SE")} av {m.n_stones.toLocaleString("sv-SE")} runstenar går att läsa så pass att det
        syns vad de berättar. Varje budskap räknas en gång per sten, med en regel i Rundatas engelska översättning, och
        prövas mot landsdel och tid med ristaren som slumpeffekt.
      </p>
      <Fig src={f.regions} alt="Budskapen i Götaland och Svealand" />
      <Details title="Resorna: säger stenen att mannen dog borta?" open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Landsdel</Th><Th>Västerut</Th><Th>Österut</Th></tr></thead>
            <tbody>{["Götaland", "Svealand"].map(r => (
              <tr key={r} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold">{r}</td>
                <td className="p-2">{share(cell(r, "väst"))}</td>
                <td className="p-2">{share(cell(r, "öst"))}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <ul className="text-xs text-slate-600 mt-2 space-y-1 list-disc pl-5">
          <li>Över båda riktningarna, inom varje riktning: oddskvot {odds(m.travel.mh)}, p {pText(m.travel.mh.p)} (exakt Mantel–Haenszel).</li>
          <li>Är skillnaden densamma åt båda håll? Interaktion p {pText(m.travel.p_interaction)} – ett högt värde betyder att Götaland skiljer sig lika mycket i väst som i öst.</li>
          <li>Med tidsskikt: oddskvot {odds(m.travel.common_glm)}, p {pText(m.travel.common_glm?.p)}. Med ristaren eller socknen som slumpeffekt: {odds(m.travel.common)}, p {pText(m.travel.common?.p)} – osäkrare, eftersom de götländska resestenarna är få och spridda.</li>
        </ul>
      </Details>
      <Details title="Alla budskap per landsdel" open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Budskap</Th><Th>Götaland</Th><Th>Svealand</Th><Th>Gotland</Th><Th>Norrland</Th>
              <Th tip="Götaland mot Svealand, justerat för tidsskikt och ristare. Över 1: vanligare i Götaland.">Oddskvot (95 % KI)</Th><Th>p</Th></tr></thead>
            <tbody>{m.elements.map(e => {
              const br = (r: string) => e.by_region.find(x => x.region === r);
              const row = e.model ?? null;
              return (
                <tr key={e.key} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold">{e.label}</td>
                  {["Götaland", "Svealand", "Gotland", "Norrland"].map(r => <td key={r} className="p-2">{share(br(r))}</td>)}
                  <td className="p-2">{e.separation ? "finns inte i Götaland" : odds(row)}</td>
                  <td className="p-2">{pText(row ? row.p : e.fisher.p)}{!row && <span className="text-slate-500"> (Fisher)</span>}</td>
                </tr>);
            })}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Andelarna är råa (stenar med budskapet av läsbara stenar). Oddskvoten kommer ur modellen med tidsskikt och ristare;
          finns budskapet inte alls i den ena landsdelen går ingen kvot att skatta, och då står Fishers exakta test.
        </p>
      </Details>
      <Details title="Hemma: säger stenar utan resa hur den döde dog?">
        <p className="text-sm text-slate-700">
          {m.home.cells.map(c => `${c.region} ${pc(c.k / Math.max(1, c.n))} (${c.k} av ${c.n})`).join(", ")}.
          {m.home.model && <> Oddskvot Götaland mot Svealand {odds(m.home.model)}, p {pText(m.home.model.p)}.</>}
          {" "}Stenarna nämner sällan hur någon dog hemma, i båda landsdelarna; skillnaden gäller resorna.
        </p>
      </Details>
      <Method text={m.method} caveat="Reglerna för budskapen stämmer med handkodningen i 50 av 51 västerinskrifter (utdata/brittiska/hemma_kodning.csv); övriga budskap är inte handkontrollerade. Stenarna visar vad de efterlevande valde att berätta, inte vad som hände." />
    </>
  );
}
