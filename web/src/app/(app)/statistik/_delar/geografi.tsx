import { Details } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import { API_URL } from "@/lib/api";
import ExportTable from "@/components/ExportTable";
import type { AgeTerm, ChurchAge, Corpus, CultResult, VikingShore } from "./typer";
import { Fig, Method, SectionIntro, Th, d2, pText, pc } from "./gemensamt";
import { sectionOf } from "./oversikt";

export function Geography({ data }: { data: Corpus }) {
  const g = data.geography, f = data.figure_urls.geography || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "geography")} patterns={data.patterns} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.map} alt="Ristarnas områden" /><Fig src={f.water} alt="Avstånd till vatten" /></div>
      {data.html_map_url && (
        <a href={`${API_URL}${data.html_map_url}`} target="_blank" rel="noreferrer" className="inline-block text-sm font-semibold text-[#b7410e] hover:underline">
          Öppna den interaktiva kartan över ristarnas stenar
        </a>
      )}
      <VikingShoreTable v={g.water?.viking_shore} today={g.water?.provinces} />
      <Remains data={data} />
      <Details title="Ristarna en och en">
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ristare</Th><Th>Säkra stenar</Th><Th>Median till tyngdpunkt</Th>
              <Th>Slumpvisa urval</Th><Th>Kvot</Th><Th>q</Th><Th>Höljets yta</Th><Th>Landskap</Th></tr></thead>
            <tbody>{g.carvers.map(r => (
              <tr key={r.carver} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td><td className="p-2">{d2(r.median_km, 1)} km</td>
                <td className="p-2">{d2(r.random_median_km, 1)} km</td><td className="p-2">{d2(r.compact_ratio)}</td><td className="p-2">{d2(r.compact_q, 3)}</td>
                <td className="p-2">{r.hull_area_km2} km²</td><td className="p-2 text-xs">{r.provinces}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={g.method} />
    </>
  );
}

// Distance to the modelled shoreline of c. AD 1000 per province, beside today's water (r/geography.R)
function VikingShoreTable({ v, today }: { v?: VikingShore; today?: { province: string; median_stones_km: number; median_random_km: number }[] }) {
  if (!v || v.error || !v.provinces?.length) return null;
  const now = new Map((today ?? []).map(r => [r.province, r]));
  return (
    <Details title="Dåtidens strand: avstånd till en modellerad strandlinje omkring år 1000">
      <p className="text-sm text-slate-600 mb-2">
        Havet omkring år 1000 är modellerat som land under landskapets landhöjning sedan dess (dagens höjd, omkring 300 m
        upplösning), tillsammans med dagens sjöar och vattendrag. Kvoten är stenarnas medianavstånd delat med
        slumppunkternas: ju lägre, desto närmare vatten står stenarna. Alla landskap: {d2(v.median_stones_km, 1)} mot{" "}
        {d2(v.median_random_km, 1)} km (p {pText(v.p)}).
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr><Th>Landskap</Th><Th>Landhöjning</Th><Th>Stenar</Th><Th>Stenar, median</Th><Th>Slumppunkter, median</Th>
            <Th>Kvot omkring år 1000</Th><Th>Kvot med dagens vatten</Th><Th>p</Th></tr></thead>
          <tbody>{v.provinces.map(r => {
            const t = now.get(r.province);
            return (
              <tr key={r.province} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold">{r.province}</td><td className="p-2">{d2(r.uplift_m, 1)} m</td><td className="p-2">{r.n}</td>
                <td className="p-2">{d2(r.median_stones_km, 1)} km</td><td className="p-2">{d2(r.median_random_km, 1)} km</td>
                <td className="p-2 font-semibold">{d2(r.median_stones_km / r.median_random_km)}</td>
                <td className="p-2">{t ? d2(t.median_stones_km / t.median_random_km) : "–"}</td><td className="p-2">{pText(r.p)}</td>
              </tr>
            );
          })}</tbody>
        </table></ExportTable>
      </div>
    </Details>
  );
}

// The stones among the registered remains: grave fields, mounds, roads, bridges, hillforts and harbours (r/remains.R)
function Remains({ data }: { data: Corpus }) {
  const r = data.remains, f = data.figure_urls.remains || {};
  if (!r?.available || !r.distances?.length) return null;
  const m = Math.round((r.near_km ?? 0.5) * 1000);
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-slate-900">Lämningar runt stenarna</h3>
      <p className="text-sm text-slate-600 max-w-4xl">
        Hur nära står runstenarna gravfält, högar, färdvägar, broar, fornborgar och hamnar i Kulturmiljöregistret, jämfört
        med slumpvisa punkter på land i samma trakter? {r.n_stones} stenar som inte är flyttade.
      </p>
      <Fig src={f.near} alt="Lämningar runt stenarna" narrow />
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr><Th>Lämning</Th><Th>I registret</Th><Th>Stenar, median</Th><Th>Slumppunkter, median</Th>
            <Th tip={`Andel inom ${m} m`}>{`Stenar inom ${m} m`}</Th><Th tip={`Andel inom ${m} m`}>{`Slumppunkter inom ${m} m`}</Th><Th>q</Th></tr></thead>
          <tbody>{r.distances.map(x => (
            <tr key={x.key} className="border-t border-slate-900/5">
              <td className="p-2 font-semibold">{x.label}</td><td className="p-2">{x.n_remains.toLocaleString("sv-SE")}</td>
              <td className="p-2">{d2(x.median_stones_km, 1)} km</td><td className="p-2">{d2(x.median_random_km, 1)} km</td>
              <td className="p-2 font-semibold">{pc(x.near_stones)}</td><td className="p-2">{pc(x.near_random)}</td><td className="p-2">{pText(x.q_bh)}</td>
            </tr>))}</tbody>
        </table></ExportTable>
      </div>
      {r.tests && Object.keys(r.tests).length > 0 && (
        <Details title="Samband: tid, kristna markörer och brostenar">
          <div className="overflow-x-auto">
            <ExportTable><table className="w-full text-sm">
              <thead><tr><Th>Samband</Th><Th>Stenar</Th><Th tip="Oddskvot: över 1 betyder oftare nära, under 1 mer sällan">Oddskvot</Th><Th>95 % intervall</Th><Th>q</Th><Th tip={GLOSSARY["Båda halvorna"]}>Båda halvorna</Th></tr></thead>
              <tbody>{Object.entries(r.tests).map(([k, t]) => (
                <tr key={k} className="border-t border-slate-900/5">
                  <td className="p-2">{t.label}{t.periods && <span className="block text-xs text-slate-500">före ca 1050 {pc(t.periods.early)}, efter {pc(t.periods.late)}</span>}</td>
                  <td className="p-2">{t.n}</td><td className="p-2 font-semibold">{d2(t.or)}</td><td className="p-2">{d2(t.lo)}–{d2(t.hi)}</td>
                  <td className="p-2">{pText(t.q_bh)}</td><td className="p-2">{t.halves?.replicated ? "✓ ja" : "nej"}</td>
                </tr>))}</tbody>
            </table></ExportTable>
          </div>
        </Details>
      )}
      <Method text={r.method} caveat={r.note} />
      <CultNames c={r.cult} />
    </div>
  );
}

// The age of the churches: does a pattern follow the early churches or the later ones (r/remains.R)
function ChurchAgeTable({ a }: { a: ChurchAge }) {
  const or = (t: AgeTerm) => (t ? <>{d2(t.or)} <span className="text-xs text-slate-500">({d2(t.lo)}–{d2(t.hi)})</span></> : "–");
  return (
    <div className="space-y-2">
      <h4 className="font-semibold text-slate-900">Tidiga och sena kyrkor</h4>
      <p className="text-sm text-slate-600 max-w-4xl">
        Följer mönstret de tidiga kyrkorna (uppförda {a.early_year} eller tidigare, {a.n_early} kyrkor) eller de senare
        ({a.n_late} kyrkor)? Båda avstånden ingår i samma modell, med landskapet konstant, så att varje oddskvot gäller när
        avståndet till den andra sortens kyrka hålls konstant. Oddskvoten gäller när avståndet halveras.
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr><Th>Mönster</Th><Th>Tidiga kyrkor</Th><Th>Sena kyrkor</Th><Th>Skillnad, p</Th><Th>Med tiden konstant (tidiga)</Th><Th tip={GLOSSARY["Båda halvorna"]}>Båda halvorna (tidiga)</Th><Th>Andel inom {a.near_km} km: tidig / bara sen / ingen</Th></tr></thead>
          <tbody>{a.tests.map(t => (
            <tr key={t.feature} className="border-t border-slate-900/5">
              <td className="p-2">{t.label} <span className="text-xs text-slate-500">({t.n} stenar)</span></td>
              <td className="p-2 font-semibold">{or(t.early)}<span className="block text-xs font-normal text-slate-500">p {t.early ? pText(t.early.p) : "–"}</span></td>
              <td className="p-2">{or(t.late)}<span className="block text-xs text-slate-500">p {t.late ? pText(t.late.p) : "–"}</span></td>
              <td className="p-2">{pText(t.p_diff)}</td>
              <td className="p-2">{t.early_time ? `${d2(t.early_time.or)} (p ${pText(t.early_time.p)})` : "–"}</td>
              <td className="p-2">{t.early?.halves?.replicated ? "✓ ja" : "nej"}</td>
              <td className="p-2 tabular-nums">{pc(t.share_early)} / {pc(t.share_late)} / {pc(t.share_none)}
                <span className="block text-xs text-slate-500">{t.n_early} / {t.n_late} / {t.n_none} stenar</span></td>
            </tr>))}</tbody>
        </table></ExportTable>
      </div>
      <p className="text-xs text-slate-500">
        Uppförandeåren kommer ur Wikidata och gäller oftast den kyrka som står i dag, inte den första på platsen; många är
        avrundade till sekelskiften.
      </p>
    </div>
  );
}

// Christian messages near place names that suggest pre-Christian cult, and churches near the same names (r/remains.R)
function CultNames({ c }: { c?: CultResult }) {
  if (!c?.available || !c.tests) return null;
  const order = ["prayer_a", "christian_a", "cross_a", "prayer_a_time", "prayer_a_central", "prayer_central", "christian_b"];
  const rows = order.filter(k => c.tests![k]).map(k => [k, c.tests![k]] as const);
  return (
    <div className="space-y-3 pt-4">
      <h3 className="text-lg font-bold text-slate-900">Förkristna kultnamn och stenarnas budskap</h3>
      <p className="text-sm text-slate-600 max-w-4xl">
        Är kristna budskap vanligare på stenar nära ortnamn som tyder på förkristen kult? Teofora namn är ett gudanamn med
        en sakral efterled (Torsvi, Odensala, Ullevi, Frösö; {c.n_a} namn), sakrala namn utan gudanamn är Vi, Viby, Harg
        och Hov ({c.n_b} namn) och centralortsnamn utan kult (Husby, -tuna; {c.n_c ?? "–"} namn) är en jämförelse. Nära
        betyder inom {c.near_km} km; {c.stones_near_a} stenar står nära ett teoforiskt namn.
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr><Th>Samband</Th><Th>Nära</Th><Th>Andel nära</Th><Th>Andel övriga</Th><Th>Oddskvot</Th><Th>95 % intervall</Th><Th>q</Th><Th tip={GLOSSARY["Båda halvorna"]}>Båda halvorna</Th></tr></thead>
          <tbody>{rows.map(([k, t]) => (
            <tr key={k} className="border-t border-slate-900/5">
              <td className="p-2">{t.label}{t.loo && <span className="block text-xs text-slate-500">utan ett namn i taget: {d2(t.loo.min_or)}–{d2(t.loo.max_or)}</span>}</td>
              <td className="p-2">{t.n_near}</td><td className="p-2 font-semibold">{pc(t.share_near)}</td><td className="p-2">{pc(t.share_far)}</td>
              <td className="p-2 font-semibold">{d2(t.or)}</td><td className="p-2">{d2(t.lo)}–{d2(t.hi)}</td>
              <td className="p-2">{pText(t.q_bh)}</td><td className="p-2">{t.halves?.replicated ? "✓ ja" : "nej"}</td>
            </tr>))}</tbody>
        </table></ExportTable>
      </div>
      {c.radius && c.radius.length > 0 && (
        <p className="text-xs text-slate-500">
          Kristen bön med annan radie: {c.radius.map(r => `${r.km} km: oddskvot ${d2(r.or)} (p ${pText(r.p)}, ${r.n_near} stenar nära)`).join("; ")}.
        </p>
      )}
      {c.churches && c.churches.rows.length > 0 && (
        <p className="text-sm text-slate-600 max-w-4xl">
          Medeltida kyrkor (Wikidata, {c.churches.n_churches} kyrkor före 1350): inom {c.churches.near_km} km från en kyrka
          ligger {c.churches.rows.map(r => `${pc(r.near_church)} av de ${r.tier === "A" ? "teofora" : "sakrala"} namnen (oddskvot ${d2(r.or)}, p ${pText(r.p)})`).join(" och ")},
          mot {d2(c.churches.near_church_other * 100, 1)} % av {c.churches.n_other.toLocaleString("sv-SE")} andra ortnamn i samma trakter.
        </p>
      )}
      {c.churches?.age && c.churches.age.tests.length > 0 && <ChurchAgeTable a={c.churches.age} />}
      {c.pagan && c.pagan.length > 0 && (
        <p className="text-xs text-slate-500">
          Stenar med uttryckligt hedniska markörer och avståndet till närmaste teoforiska namn:{" "}
          <span translate="no">{c.pagan.map(x => `${x.signum} ${d2(x.km_a, 1)} km`).join(", ")}</span>.
        </p>
      )}
    </div>
  );
}
