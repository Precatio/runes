import { Details } from "@/components/Explain";
import ExportTable from "@/components/ExportTable";
import type { Corpus, PeopleFit, PeopleTest } from "./typer";
import { Method, SectionIntro, Th, d2, pText, pc } from "./gemensamt";
import { sectionOf } from "./oversikt";

const odds = (f?: PeopleFit | null) => (f && !f.too_few && f.or != null
  ? `${d2(f.or, 2)} (${d2(f.lo, 2)}–${f.hi == null || f.hi > 1e3 ? "∞" : d2(f.hi, f.hi >= 10 ? 0 : 2)})` : "–");
const fitText = (f?: PeopleFit | null) => (!f ? "–" : f.too_few ? `för få (${f.k} av ${f.n})` : `${odds(f)}, p ${pText(f.p)}`);
/** The model's shares in plain words: x = 1 against x = 0, or Svealand against Götaland. */
function shares(t: PeopleTest): string {
  const m = t.main;
  if (m.shares_region) return `Svealand ${pc(m.shares_region.Svealand)}, Götaland ${pc(m.shares_region.Götaland)}`;
  if (!m.shares) return "–";
  const [one, zero] = t.key.endsWith("_ung") ? ["söner och bröder", "fäder och makar"] : ["med en kvinna", "utan kvinna"];
  return `${one} ${pc(m.shares["1"])}, ${zero} ${pc(m.shares["0"])}`;
}
const ROBUST: Record<string, string> = {
  ord10: "minst tio läsbara ord", kon_bestamt: "alla resares kön bestämt", utan_ristare: "utan ristarens slumpeffekt",
  uppland: "bara Uppland", son_far: "bara söner mot bara fäder",
};

/** The people on the runestones (r/people.R): who raised the stones, for whom, and what the stones say about them. */
export function People({ data }: { data: Corpus }) {
  const m = data.people;
  if (!m) return <p className="text-sm text-slate-600">Analysen av människorna saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  return (
    <>
      <SectionIntro section={sectionOf(data, "people")} patterns={data.patterns} />
      <p className="text-sm text-slate-600 max-w-3xl">
        Resarnas och de dödas kön och relation läses ur Rundatas engelska översättning för {m.n_stones.toLocaleString("sv-SE")} läsbara
        svenska runstenar. Sex frågor prövas med landsdel, tid och ristare konstanta, enligt en plan som låstes innan
        något test kördes ({m.plan}).
      </p>
      <Details title="De sex testen" open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Fråga</Th><Th tip="Antal stenar med utfallet av antal prövade stenar.">Stenar</Th>
              <Th tip="Andelen enligt modellen, med landsdel, tid och ristare konstanta.">Andel enligt modellen</Th>
              <Th tip="Över 1: vanligare för den första gruppen; för tiden: förändringen per 50 år.">Oddskvot (95 % KI)</Th>
              <Th tip="Holm-korrigerat över de sex testen.">p (Holm)</Th><Th>Båda halvorna</Th><Th>Utslag</Th></tr></thead>
            <tbody>{m.tests.map(t => (
              <tr key={t.key} className="border-t border-slate-900/5 align-top">
                <td className="p-2 font-semibold">{t.label}</td>
                <td className="p-2">{t.main.k} av {t.main.n}</td>
                <td className="p-2">{shares(t)}</td>
                <td className="p-2">{odds(t.main)}</td>
                <td className="p-2">{pText(t.main.p_holm)}</td>
                <td className="p-2">{t.replicated ? "ja" : "nej"}</td>
                <td className="p-2">{t.status}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Bekräftar: Holm-p under 0,05 och samma riktning med p under 0,05 i båda halvorna (socken för socken). Mönster att
          pröva: Holm-p under 0,05 men inte i båda halvorna. Indikation: bara okorrigerat p under 0,05. Ett test körs när
          utfallet finns på minst {m.min_events} stenar.
        </p>
      </Details>
      <Details title="Halvorna och robusthetsproven">
        <ul className="text-sm text-slate-700 space-y-2 list-disc pl-5">
          {m.tests.map(t => (
            <li key={t.key}><span className="font-semibold">{t.label}.</span> Halvorna: {fitText(t.halves.A)}; {fitText(t.halves.B)}.
              {" "}{Object.entries(t.robustness).filter(([, f]) => f).map(([k, f]) => `${ROBUST[k] ?? k}: ${fitText(f)}`).join("; ")}.</li>))}
        </ul>
      </Details>
      <Method text={m.method} caveat="Reglerna stämmer med handkodningen av 40 nya stenar i 39 fall för kvinnor bland resarna och i 38 för relationen (data/people_check.json); felen gäller stenar med luckor. drengr och þegn kan säga något om ställning och följe, inte bara om ålder. Stenarna visar vem som reste dem och vad de valde att säga, inte hur familjerna faktiskt såg ut." />
    </>
  );
}
