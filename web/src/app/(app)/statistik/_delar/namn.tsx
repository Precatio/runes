import { Details } from "@/components/Explain";
import ExportTable from "@/components/ExportTable";
import type { Corpus, NamesTest } from "./typer";
import { PROVINCE_NAMES, SectionIntro, Th, d2, pText, pc } from "./gemensamt";
import { sectionOf } from "./oversikt";

const region = (c: string) => PROVINCE_NAMES[c] ?? c;
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const test = (t?: NamesTest) => (!t || t.share == null ? "–"
  : `${pc(t.share)} mot ${pc(t.expected)} väntat (${d2(t.ratio, 1)} gånger, p ${pText(t.p)}, ${t.pairs} par)`);

/** Namn och släkt (r/names.R): namnled i arv, grannar som delar namn, namnens geografi och namnskicket per gammal region. */
export function Names({ data }: { data: Corpus }) {
  const m = data.names;
  if (!m || !m.available) return <p className="text-sm text-slate-600">Analysen av namn och släkt saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const f = m.family;
  return (
    <>
      <SectionIntro section={sectionOf(data, "names")} patterns={data.patterns} />
      <p className="text-sm text-slate-600 max-w-3xl">
        Namnen och släktbanden läses ur Rundatas översättning för {m.n_stones.toLocaleString("sv-SE")} svenska runstenar
        ({m.n_pairs.toLocaleString("sv-SE")} förälder–barn- och syskonpar). Regionen är den vikingatida: Upplands folkland,
        Smålands små land, Gotlands tredingar och övriga landskap som egna land. Proven låstes innan de kördes ({m.plan}).
      </p>
      <Details title="Barnen ärvde namnled" open>
        <ul className="text-sm text-slate-700 space-y-1.5 list-disc pl-5">
          <li><span className="font-semibold">Förälder och barn</span> delar ett namnled (som Holmger och Holmfast):{" "}
            {test(m.inheritance.pc)}. Halvorna: {test(m.inheritance.pc.halves.A)}; {test(m.inheritance.pc.halves.B)}.
            {m.inheritance.pc.holds ? " Håller i båda halvorna." : " Håller inte i båda halvorna."}</li>
          <li><span className="font-semibold">Syskon</span>: {test(m.inheritance.sib)}. Halvorna: {test(m.inheritance.sib.halves.A)};{" "}
            {test(m.inheritance.sib.halves.B)}.{m.inheritance.sib.holds ? " Håller i båda halvorna." : " Håller inte i båda halvorna."}</li>
        </ul>
        <p className="text-xs text-slate-500 mt-1">Väntat: om barnen hade fått sina namn slumpvis bland namnen i samma region (9 999 omblandningar).</p>
      </Details>
      <Details title="Namnskicket per region">
        <div className="overflow-x-auto"><ExportTable><table className="text-sm min-w-[360px]">
          <thead><tr><Th>Region</Th><Th>Par</Th><Th>Delar namnled</Th><Th tip="Andel som delar namnled minus vad slumpen ger i regionen.">Överskott</Th></tr></thead>
          <tbody>{m.custom.regions.map(r => (
            <tr key={r.region} className="border-t border-slate-900/5"><td className="p-2">{region(r.region)}</td><td className="p-2">{r.pairs}</td>
              <td className="p-2">{pc(r.share)}</td><td className="p-2">{d2(r.excess * 100, 1)} procentenheter</td></tr>))}</tbody>
        </table></ExportTable></div>
        <p className="text-xs text-slate-500 mt-1">Skiljer sig seden mellan regionerna? Omblandning av regionerna: p {pText(m.custom.p)}.</p>
      </Details>
      <Details title="Grannar delar namn" open>
        <p className="text-sm text-slate-700">Stenar i samma region som står mindre än en kilometer från varandra nämner samma ovanliga namn i{" "}
          {test(m.neighbours)}.{m.neighbours.holds ? " Det håller i båda halvorna." : " Det håller inte i båda halvorna."}</p>
        <div className="overflow-x-auto"><ExportTable><table className="text-sm min-w-[360px] mt-2">
          <thead><tr><Th>Avstånd</Th><Th>Stenpar</Th><Th>Delar ett ovanligt namn</Th><Th tip="Jämfört med stenpar 20–50 km isär.">Gånger vanligare</Th></tr></thead>
          <tbody>{m.neighbours.bands.map(b => (
            <tr key={b.band} className="border-t border-slate-900/5"><td className="p-2">{b.band} km</td><td className="p-2">{b.pairs.toLocaleString("sv-SE")}</td>
              <td className="p-2">{pc(b.share)}</td><td className="p-2">{d2(b.ratio, 1)}</td></tr>))}</tbody>
        </table></ExportTable></div>
        <p className="text-xs text-slate-500 mt-1">De 60 vanligaste namnen räknas inte: att två stenar nämner Sven eller Björn säger lite om släkt.</p>
      </Details>
      <Details title="Namnens geografi efter de gamla gränserna" open>
        <p className="text-sm text-slate-700">{m.geography.n_names} namn prövades i {m.geography.regions.length} regioner ({m.geography.n_tests} prov).{" "}
          {m.geography.n_sig} namn är vanligare i en region än i resten efter justering, och {m.geography.n_holds} av dem håller i båda halvorna.</p>
        {m.geography.rows.length > 0 && (
          <div className="overflow-x-auto"><ExportTable><table className="text-sm min-w-[360px] mt-2">
            <thead><tr><Th>Namn</Th><Th>Region</Th><Th>I regionen</Th><Th>Utanför</Th><Th>Oddskvot</Th><Th>q</Th><Th>Båda halvorna</Th></tr></thead>
            <tbody>{m.geography.rows.map(r => (
              <tr key={r.name + r.region} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold">{cap(r.name)}</td><td className="p-2">{region(r.region)}</td>
                <td className="p-2">{r.k_in} av {r.n_in}</td><td className="p-2">{r.k_out} av {r.n_out}</td>
                <td className="p-2">{d2(r.or, 1)}</td><td className="p-2">{pText(r.q)}</td><td className="p-2">{r.holds ? "ja" : "nej"}</td></tr>))}</tbody>
          </table></ExportTable></div>)}
      </Details>
      {f && f.n_links > 0 && (
        <Details title="Släkterna över flera stenar">
          <p className="text-sm text-slate-700">{f.n_links} säkra länkar binder ihop svenska runstenar som nämner samma personer
            (länkmodellen, METHODS 1r). {f.same_parish} av dem går mellan stenar i samma socken och {f.same_region} inom samma
            gamla region; medianavståndet är {d2(f.km_median, 1)} km (kvartiler {d2(f.km_q1, 1)}–{d2(f.km_q3, 1)} km).</p>
          {Object.keys(f.families_by_region).length > 0 && (
            <p className="text-sm text-slate-700 mt-1">De {f.n_families} släkterna efter region:{" "}
              {Object.entries(f.families_by_region).map(([k, v]) => `${region(k)} ${v}`).join(", ")}.</p>)}
        </Details>)}
    </>
  );
}
