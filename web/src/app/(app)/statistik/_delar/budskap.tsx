import { Details } from "@/components/Explain";
import ExportTable from "@/components/ExportTable";
import type { Corpus, MessageElement, MessageRuleCheck, OddsRow } from "./typer";
import { Fig, Method, SectionIntro, Th, d2, pText, pc } from "./gemensamt";
import { sectionOf } from "./oversikt";

/** The region of Götaland and Svealand where a separated message never occurs. */
const missingIn = (e: MessageElement) => ((e.by_region.find(x => x.region === "Götaland")?.k ?? 0) === 0 ? "Götaland" : "Svealand");
const odds = (o?: OddsRow | null) => (o ? `${d2(o.or, 2)} (${d2(o.lo, 2)}–${o.hi == null ? "∞" : d2(o.hi, o.hi >= 10 ? 0 : 2)})` : "–");
const UNCHECKED: Record<string, string> = { gald: "gäld", arv: "arv", gard: "gård", egen: "egen sten", berom: "beröm" };
const pair = (x?: [number, number]) => (x ? `${x[0]} av ${x[1]}` : "–");
const andList = (xs: string[]) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} och ${xs[xs.length - 1]}`);

/** How the message rules agree with the hand codings, from data/messages_check.json (scripts/check_messages.py). */
function ruleCheckText(rc?: MessageRuleCheck | null): string {
  if (!rc) return "Hur väl reglerna stämmer med handkodningarna redovisar scripts/check_messages.py (METHODS.md 1o).";
  const all = rc.east.samples["alla"], rnd = rc.east.samples["slump"];
  const un = rc.unchecked.map(k => UNCHECKED[k] ?? k);
  return `Reglerna stämmer med handkodningen av ${rc.west.n} västerinskrifter (${rc.west.file}) för död borta i ${pair(rc.west.dod_borta)}; `
    + `mot ${all?.n ?? "–"} handkodade stenar om österfärder och angränsande fall (${rc.east.file}) stämmer resa i ${pair(all?.resa)}, `
    + `död borta i ${pair(all?.dod_borta)}, dödsuppgift i ${pair(all?.dod_uppgift)} och riktningen i ${pair(all?.riktning)}.`
    + (rnd?.n ? ` Österurvalet kodades medan reglerna rättades; i dess slumpvisa del (${rnd.n} stenar) stämmer resa i ${pair(rnd.resa)} och död borta i ${pair(rnd.dod_borta)}.` : "")
    + (un.length ? ` ${andList(un).replace(/^./, c => c.toUpperCase())} är bara stickprovskontrollerade.` : "")
    + (rc.stale ? " Kontrollen gjordes med en tidigare version av reglerna." : "");
}

/** The messages of the runestones (r/messages.R): what they tell about the dead, by region, and the journeys. */
export function Messages({ data }: { data: Corpus }) {
  const m = data.messages, f = data.figure_urls.messages || {};
  if (!m) return <p className="text-sm text-slate-600">Budskapsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const cell = (region: string, direction: string) => m.travel.cells.find(c => c.region === region && c.direction === direction);
  const share = (c?: { k: number; n: number }) => (c && c.n ? `${pc(c.k / c.n)} (${c.k} av ${c.n})` : "–");
  const t = m.travel, dir = (d: string) => t.by_direction.find(x => x.direction === d);
  const gw = cell("Götaland", "väst")?.n ?? 0, ge = cell("Götaland", "öst")?.n ?? 0;
  const lg = m.legibility, lgr = (r: string) => lg?.by_region.find(x => x.region === r);
  const fragShare = (r: string) => { const x = lgr(r); return x && x.legible ? pc((x.legible - x.strict) / x.legible) : "–"; };
  const strictWords = lg?.strict_words ?? m.elements.find(e => e.strict)?.strict?.words;
  const single = (t.all_journeys ?? []).reduce((a, x) => a + x.single, 0);
  const notSingle = (t.all_journeys ?? []).reduce((a, x) => a + x.n - x.single, 0);
  /** One direction: Fisher's exact test (its own odds ratio and p) and the model with time layers (its own odds ratio and p). */
  const dirRow = (d: string) => {
    const x = dir(d);
    if (!x) return "–";
    const model = `med tidsskikt ${odds(x)}, p ${pText(x.p)}`;
    return x.fisher ? `Fishers exakta test ${odds(x.fisher)}, p ${pText(x.fisher.p)}; ${model}` : `${model}; Fishers exakta test utan justering p ${pText(x.fisher_p)}`;
  };
  // Old results (before the outcome was died abroad) counted every statement of how or where the man died
  const abroad = t.outcome === "dod_borta";
  return (
    <>
      <SectionIntro section={sectionOf(data, "messages")} patterns={data.patterns} />
      <p className="text-sm text-slate-600 max-w-3xl">
        {m.n_legible.toLocaleString("sv-SE")} av {m.n_stones.toLocaleString("sv-SE")} runstenar räknas som läsbara
        {lg ? <>: minst {lg.min_words} ord av översättningen går att läsa</> : <> (tillräckligt många ord av översättningen går att läsa)</>}.
        Det visar inte att minnesformeln eller budskapen är bevarade, så ett fragment räknas som en sten utan budskapen.
        {lg && <> Färre än {lg.strict_words} läsbara ord har {fragShare("Götaland")} av de läsbara stenarna i Götaland och {fragShare("Svealand")} i
          Svealand; därför görs testen också bara på stenar med minst {lg.strict_words} ord.</>}
        {" "}Varje budskap räknas en gång per sten, med en regel i Rundatas engelska översättning, och prövas mot landsdel
        och tid med ristaren som slumpeffekt.
      </p>
      <Fig src={f.regions} alt="Budskapen i Götaland och Svealand" />
      <Details title={abroad ? "Resorna: säger stenen att mannen dog utanför Norden?" : "Resorna: säger stenen hur eller var mannen dog?"} open>
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
          <li>Götaland mot Svealand inom varje riktning: oddskvot {odds(t.mh)}, p {pText(t.mh.p)} (exakt Mantel–Haenszel med riktningen som skikt).</li>
          {t.mh_time && <li>Inom riktning och tidsskikt samtidigt: oddskvot {odds(t.mh_time)}, p {pText(t.mh_time.p)} (exakt Mantel–Haenszel med riktning × tidsskikt som skikt{t.mh_time.n != null && <>; {t.mh_time.n} av {t.n} resestenar ligger i skikt med båda landsdelarna och båda utfallen, de andra skikten bär ingen information</>}).</li>}
          {t.mh_strict && <li>Bara stenar med minst {t.mh_strict.words} läsbara ord: oddskvot {odds(t.mh_strict)}, p {pText(t.mh_strict.p)} (exakt Mantel–Haenszel med riktningen som skikt, {t.mh_strict.n} resestenar).</li>}
          <li>Riktning för riktning: västerut {dirRow("väst")}; österut {dirRow("öst")}.</li>
          <li>Skiljer sig skillnaden mellan väst och öst? Interaktion p {pText(t.p_interaction)}
            {t.interaction && <>, kvoten mellan oddskvoterna öst/väst {odds(t.interaction)}</>}.
            {t.p_interaction != null && t.p_interaction >= 0.05
              ? <> Ett högt värde betyder bara att ingen skillnad mellan riktningarna kan visas, inte att skillnaden är densamma: testet är svagt med {gw} götländska resestenar västerut och {ge} österut.</>
              : <> Skillnaden mellan landsdelarna är inte densamma åt båda håll.</>}</li>
          <li>Med tidsskikt (logistisk regression): oddskvot {odds(t.common_glm)}, p {pText(t.common_glm?.p)}. Med ristaren eller socknen som slumpeffekt: {odds(t.common)}, p {pText(t.common?.p)}{t.common && t.common.p >= 0.05 ? " – inte signifikant, eftersom de götländska resestenarna är få och spridda över många socknar" : ""}.</li>
          {notSingle > 0 && <li>Tabellen och testen gäller de {single} resestenar som har en enda riktning; {notSingle} med båda riktningarna eller ingen räknas inte.</li>}
        </ul>
      </Details>
      <Details title="Alla budskap per landsdel" open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Budskap</Th><Th>Götaland</Th><Th>Svealand</Th><Th>Gotland</Th><Th>Norrland</Th>
              <Th tip="Götaland mot Svealand, justerat för tidsskikt och ristare. Över 1: vanligare i Götaland.">Oddskvot (95 % KI)</Th><Th>p</Th>
              {strictWords != null && <Th tip="Samma test bara på stenar med så många läsbara ord: håller skillnaden när fragmenten räknas bort?">Minst {strictWords} ord: oddskvot, p</Th>}</tr></thead>
            <tbody>{m.elements.map(e => {
              const br = (r: string) => e.by_region.find(x => x.region === r);
              const row = e.model ?? null;
              return (
                <tr key={e.key} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold">{e.label}</td>
                  {["Götaland", "Svealand", "Gotland", "Norrland"].map(r => <td key={r} className="p-2">{share(br(r))}</td>)}
                  <td className="p-2">{e.separation ? `finns inte i ${missingIn(e)}` : row ? odds(row) : <>{odds(e.fisher)}<span className="text-slate-500"> (Fisher)</span></>}</td>
                  <td className="p-2">{pText(row ? row.p : e.fisher.p)}{!row && <span className="text-slate-500"> (Fisher)</span>}</td>
                  {strictWords != null && <td className="p-2">{e.separation || !e.strict ? "–"
                    : row ? (e.strict.model ? `${odds(e.strict.model)}, p ${pText(e.strict.model.p)}` : "–")
                    : <>{odds(e.strict.fisher)}, p {pText(e.strict.fisher.p)}<span className="text-slate-500"> (Fisher)</span></>}</td>}
                </tr>);
            })}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Andelarna är råa (stenar med budskapet av läsbara stenar). Oddskvoten kommer ur modellen med tidsskikt och ristare.
          Finns budskapet inte alls i den ena landsdelen går ingen kvot att skatta, och då står Fishers exakta test; är
          budskapet för sällsynt för modellen
          {m.min_events != null && <> (färre än {m.min_events} stenar med budskapet, eller utan det, i Götaland och Svealand tillsammans)</>}
          {" "}står Fishers oddskvot och p, utan justering för tid och ristare.
          {strictWords != null && <> Sista kolumnen är samma test bara på stenar med minst {strictWords} läsbara ord.</>}
        </p>
      </Details>
      <Details title="Hemma: säger stenar utan resa hur den döde dog?">
        <p className="text-sm text-slate-700">
          {m.home.cells.map(c => `${c.region} ${pc(c.k / Math.max(1, c.n))} (${c.k} av ${c.n})`).join(", ")}.
          {m.home.model && <> Oddskvot Götaland mot Svealand {odds(m.home.model)}, p {pText(m.home.model.p)}.</>}
          {m.home.model && (m.home.model.p < 0.05
            ? <> Även utan resa skiljer sig landsdelarna: stenarna i Götaland säger {m.home.model.or < 1 ? "mer sällan" : "oftare"} hur den döde dog.</>
            : <> Utan resa går ingen skillnad mellan landsdelarna att visa.</>)}
        </p>
      </Details>
      <Method text={m.method} caveat={`${ruleCheckText(m.rule_check)} Stenarna visar vad de efterlevande valde att berätta, inte vad som hände.`} />
    </>
  );
}
