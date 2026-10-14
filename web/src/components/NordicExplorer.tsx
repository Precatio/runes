"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import { Tip } from "@/components/Explain";
import ExportTable from "@/components/ExportTable";
import RealmPanel from "@/components/RealmPanel";
import { REALMS } from "@/lib/realms";
import { SHARE_CLASSES, TOO_FEW, type PatternStone } from "@/lib/patternMap";

const PatternMaps = dynamic(() => import("@/components/PatternMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-slate-500">Laddar karta...</div>,
});

// Danish, Norwegian and Swedish runestones compared (GET /api/research/nordic, src/nordic.py): a pattern's share per
// country or per realm about 1025, with and without time held constant, and what crosses the borders – Rundata's
// remarks, texts naming another land and the Danish likeness of Swedish stones and carvers
interface NordicPattern { key: string; label: string; group: string; help: string }
interface Group {
  key: string; label: string; realm: string; n: number; k: number; share: number | null; lo: number; hi: number;
  bins: Record<string, { n: number; k: number }>; dated: number;
}
interface Pair { a: string; b: string; or: number; p: number; or_mh: number | null; p_mh: number | null; strata: number; n_dated: number }
interface Comparison { groups: Group[]; test: { chi2: number; df: number; p: number; groups: string[]; small: boolean } | null; pairs: Pair[] }
interface Brief {
  signum: string; realm: string; province: string; year: number | null; score: number; style: string; carvers: string[];
  place: string; features: string[];
}
interface Summary { key: string; label?: string; years?: string; n: number; mean: number | null; danish: number }
interface Likeness {
  available: boolean; reason?: string; auc: number | null; n_train_dk: number; n_train_se: number; years: number[];
  features: { key: string; label: string; or: number; dk: number; se: number }[]; min_features: number; n_told: number;
  check: { n: number; mean: number; mean_others: number; p: number; of: number; stones: { signum: string; score: number; rank: number }[] } | null;
  by_realm: Summary[]; by_style: Summary[]; by_danish_realm: Summary[]; n_carvers: number;
  carvers: { carver: string; n: number; mean: number | null; danish: number; first_year: number | null; provinces: string[]; top: string[] }[];
  most_danish: Brief[]; earliest_danish: Brief[]; most_swedish_dk: Brief[];
}
interface Nordic {
  patterns: NordicPattern[]; not_comparable: { label: string; why: string }[];
  groupings: Record<string, { key: string; label: string; realm: string }[]>; bins: { key: string; label: string }[];
  counts: Record<string, number>; with_place: Record<string, number>; dated: Record<string, number>;
  stones: { s: string; lat: number | null; lon: number | null; l: string; r: string | null; y: number | null; v: (0 | 1 | null)[] }[];
  compare: Record<string, Record<string, Comparison>>;
  crossborder: {
    remarks: { signum: string; land: string; year: number | null; text: string }[];
    mentions: { signum: string; land: string; names: string; year: number | null; text: string }[];
    likeness: Likeness;
  };
}

const LAND_NAME: Record<string, string> = { danmark: "Danmark", sverige: "Sverige", norge: "Norge" };
const LAND_ADJ: Record<string, string> = { danmark: "danska", sverige: "svenska", norge: "norska" };
const HEX_SIZES = [20, 40, 80];
const MIN_STONES = 5;
// Small shares with a decimal, so that 6 of 2321 stones is not shown as 0 %
const pct = (x: number | null | undefined) => (x == null ? "–" : x > 0 && x < 0.1
  ? `${(Math.round(x * 1000) / 10).toString().replace(".", ",")} %` : `${Math.round(x * 100)} %`);
const n2 = (x: number | null | undefined) => (x == null ? "–" : x.toFixed(2).replace(".", ","));
const pText = (p: number | null | undefined) => (p == null ? "–" : p < 0.001 ? "< 0,001" : p.toFixed(3).replace(".", ","));
const ODDS = "Oddskvoten jämför oddsen för mönstret i två grupper. 1 betyder ingen skillnad, 2 att oddsen är dubbelt så stora, 0,5 att de är hälften så stora.";
const P = "Sannolikheten att få en minst lika stor skillnad om det inte fanns någon. Under 0,05 brukar räknas som säkert.";
const TIME = "Stenarna jämförs inom tre perioder (före 1000, 1000–1050, 1050 och senare) och resultaten vägs samman (Mantel–Haenszel), så att en skillnad i ålder inte ser ut som en skillnad mellan länderna. Bara daterade stenar räknas.";
const STONE = (s: string) => <Link href={`/inskrifter?signum=${encodeURIComponent(s)}`} className="font-semibold text-[#b7410e] hover:underline" translate="no">{s}</Link>;

export default function NordicExplorer({ f, set, onError }: {
  f: Record<string, string>; set: (k: string, v: string) => void; onError: (e: string) => void;
}) {
  const [data, setData] = useState<Nordic | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/research/nordic`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(setData)
      .catch(e => onError(e instanceof Error ? e.message : "Jämförelsen kunde inte hämtas."));
  }, [onError]);

  const patternKey = data?.patterns.some(x => x.key === f.npattern) ? f.npattern : data?.patterns[0]?.key ?? "";
  const pattern = data?.patterns.find(x => x.key === patternKey);
  const grouping = f.grouping === "rike" ? "rike" : "land";
  const hexKm = Number(f.hex) || 40;
  const comparison = data && patternKey ? data.compare[grouping][patternKey] : null;

  // The stones in the pattern map's form, so that the same hexagon map can be used
  const stones = useMemo<PatternStone[]>(() => {
    if (!data) return [];
    const keys = data.patterns.map(x => x.key);
    return data.stones.filter(s => s.lat != null && s.lon != null).map(s => ({
      s: s.s, lat: s.lat as number, lon: s.lon as number, p: s.l, y: s.y,
      v: Object.fromEntries(keys.map((k, i) => [k, s.v[i]])) as Record<string, 0 | 1 | null>,
    }));
  }, [data]);

  const box = "liquid-glass-island rounded-[24px] p-4";
  const step = "text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2";
  const seg = (on: boolean) => `px-3 py-1.5 rounded-lg text-xs font-bold border ${on ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"}`;

  if (!data) return <div className={`${box} text-slate-500`}>Hämtar de danska, norska och svenska stenarna …</div>;
  const missing = ["danmark", "norge"].map(l => `${data.with_place[l]} av ${data.counts[l]} ${LAND_ADJ[l]}`).join(" och ");
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 items-start">
        <aside className="space-y-4">
          <div className={box}>
            <p className={step}>1. Mönster</p>
            <div className="space-y-2">
              {[...new Set(data.patterns.map(x => x.group))].map(g => (
                <div key={g}>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{g}</p>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {data.patterns.filter(x => x.group === g).map(x => (
                      <button key={x.key} onClick={() => set("npattern", x.key)} title={x.help} aria-pressed={patternKey === x.key}
                        className={`px-2 py-1 rounded-lg text-xs font-semibold border ${patternKey === x.key ? "bg-[#1c5cab] text-white border-[#1c5cab]" : "bg-white text-slate-700 border-slate-200 hover:border-slate-400"}`}>
                        {x.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            {pattern && <p className="text-xs text-slate-600 mt-2">{pattern.help}</p>}
            <details className="mt-2 text-xs text-slate-600">
              <summary className="cursor-pointer font-semibold text-slate-700">Varför kors och språkdrag saknas</summary>
              <ul className="mt-1 space-y-1">
                {data.not_comparable.map(x => <li key={x.label}><span className="font-semibold">{x.label}:</span> {x.why}</li>)}
              </ul>
            </details>
          </div>

          <div className={box}>
            <p className={step}>2. Indelning</p>
            <div className="grid grid-cols-1 gap-1.5" role="tablist" aria-label="Indelning">
              {([["land", "Länder", "Rundatas serier: danska (med Skåne, Blekinge och Bornholm), svenska och norska"],
                 ["rike", "Riken och trakter omkring 1025", "Svitjod, götarna, Gotland, de danska landsdelarna och Norge"]] as const).map(([k, l, help]) => (
                <button key={k} role="tab" aria-selected={grouping === k} onClick={() => set("grouping", k === "land" ? "" : k)}
                  className={`${seg(grouping === k)} text-left`}>
                  <span className="block">{l}</span>
                  <span className={`block text-[10px] font-normal ${grouping === k ? "text-slate-300" : "text-slate-500"}`}>{help}</span>
                </button>
              ))}
            </div>
          </div>

          <div className={box}>
            <RealmPanel value={f.borders} onChange={v => set("borders", v)} />
          </div>

          <details className={box}>
            <summary className="cursor-pointer text-xs font-bold text-slate-700">Fler inställningar</summary>
            <div className="mt-3">
              <p className="text-[11px] font-bold text-slate-500 mb-1">Områdets storlek</p>
              <div className="flex gap-1">
                {HEX_SIZES.map(km => <button key={km} onClick={() => set("hex", km === 40 ? "" : String(km))} className={seg(hexKm === km)}>{km} km</button>)}
              </div>
            </div>
          </details>
        </aside>

        <div className="space-y-2 lg:sticky lg:top-4">
          <div className="rounded-2xl border border-slate-200 bg-white/90 px-4 py-3">
            <p className={step}>3. Vad jämförelsen visar{pattern ? <> – <span>{pattern.label}</span></> : null}</p>
            {comparison && <Result c={comparison} grouping={grouping} />}
          </div>
          <div className="liquid-glass-island rounded-[24px] p-1.5 h-[64dvh] min-h-[460px] relative">
            {pattern && (
              <PatternMaps stones={stones} patternKey={patternKey} label={pattern.label} widthKm={hexKm} minStones={MIN_STONES}
                split={false} realm={f.borders || undefined} />
            )}
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-2 text-[11px] text-slate-600">
            <span className="font-bold">Andel med mönstret</span>
            {SHARE_CLASSES.map(c => (
              <span key={c.label} className="flex items-center gap-1"><span className="w-3.5 h-2.5 inline-block rounded-sm" style={{ background: c.color }} />{c.label}</span>
            ))}
            <span className="flex items-center gap-1"><span className="w-3.5 h-2.5 inline-block rounded-sm border border-dashed border-slate-400" style={{ background: TOO_FEW }} />Färre än {MIN_STONES} stenar</span>
          </div>
          <p className="px-2 text-[11px] text-slate-500">
            Kartan visar bara stenar med koordinater i Rundata: {missing} stenar har det, och nästan alla svenska.
            Tabellen och proven räknar alla.
          </p>
        </div>
      </div>

      {comparison && <GroupTable c={comparison} bins={data.bins} />}
      <CrossBorder cb={data.crossborder} />
    </div>
  );
}

/** The comparison in words: the shares, whether the difference is larger than chance, and with time held constant. */
function Result({ c, grouping }: { c: Comparison; grouping: string }) {
  const groups = c.groups.filter(g => g.n > 0);
  const t = c.test;
  return (
    <div className="text-sm text-slate-700 space-y-1.5">
      {grouping === "land" ? (
        <p>{groups.map(g => `${g.k} av ${g.n} ${LAND_ADJ[g.key]} stenar (${pct(g.share)})`).join(", ")} har mönstret.</p>
      ) : (
        // Each group in an element of its own, so that the translation has one template per name
        <p>Vanligast i{" "}{[...groups].filter(g => g.n >= 10).sort((a, b) => (b.share ?? 0) - (a.share ?? 0)).slice(0, 3)
          .map((g, i) => <span key={g.key}>{i ? ", " : ""}<span>{g.label}</span> ({pct(g.share)} av {g.n})</span>)}.</p>
      )}
      {t && (
        <p>
          {t.p < 0.05 ? "Skillnaden mellan grupperna är större än slumpen brukar ge" : "Skillnaden mellan grupperna kan vara en slump"}
          {" "}(<Tip text={P}>p</Tip> {pText(t.p)}{t.small ? "; få stenar i någon grupp, så provet är osäkert" : ""}).
        </p>
      )}
      {c.pairs.map(p => {
        const crudeSure = p.p < 0.05, timeSure = p.p_mh != null && p.p_mh < 0.05;
        const more = p.or > 1 ? `vanligare på ${LAND_ADJ[p.a]} stenar` : `ovanligare på ${LAND_ADJ[p.a]} stenar`;
        return (
          <p key={`${p.a}-${p.b}`}>
            <span className="font-semibold">{LAND_NAME[p.a]} mot {LAND_NAME[p.b]}:</span>{" "}
            {crudeSure ? `mönstret är ${more} än på ${LAND_ADJ[p.b]}` : "ingen säker skillnad"}{" "}
            (<Tip text={ODDS}>oddskvot</Tip> {n2(p.or)}, p {pText(p.p)}).{" "}
            {p.or_mh != null && (
              <>
                <Tip text={TIME}>Med tiden konstant</Tip>: oddskvot {n2(p.or_mh)}, p {pText(p.p_mh)}
                {crudeSure && timeSure ? " – skillnaden finns kvar bland stenar från samma tid." :
                  crudeSure && !timeSure ? " – skillnaden kan bero på att stenarna är från olika tid." :
                  !crudeSure && timeSure ? " – bland stenar från samma tid syns en skillnad." : "."}
              </>
            )}
          </p>
        );
      })}
      <p className="text-xs text-slate-500">
        Ett utforskande prov: mönstren läser Rundatas engelska översättning och translitterationen, som är gjorda på samma
        sätt i alla tre serierna. Dateringarna bygger på olika system (svenska stilgrupper, den danska Jellingindelningen)
        och de flesta norska stenar är bara daterade till vikingatid.
      </p>
    </div>
  );
}

function GroupTable({ c, bins }: { c: Comparison; bins: { key: string; label: string }[] }) {
  return (
    <details className="liquid-glass-island rounded-[24px] p-4" open>
      <summary className="cursor-pointer text-sm font-bold text-slate-800">Andel per grupp och period (samma siffror som tabell)</summary>
      <div className="overflow-x-auto mt-2">
        <ExportTable><table className="text-sm min-w-[640px]">
          <thead><tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
            <th className="p-2">Grupp</th><th className="p-2">Stenar</th><th className="p-2">Med mönstret</th>
            <th className="p-2"><Tip text="Andelen och ett 95 % intervall: med fler stenar blir intervallet smalare. Två grupper vars intervall inte överlappar skiljer sig säkert.">Andel (95 % intervall)</Tip></th>
            {bins.map(b => <th key={b.key} className="p-2">{b.label}</th>)}
          </tr></thead>
          <tbody>
            {c.groups.filter(g => g.n > 0).map(g => (
              <tr key={g.key} className="border-t border-slate-900/5">
                <td className="p-2"><span className="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style={{ background: REALMS[g.realm]?.color }} />{g.label}</td>
                <td className="p-2">{g.n}</td><td className="p-2">{g.k}</td>
                <td className="p-2 font-semibold">{pct(g.share)} <span className="font-normal text-slate-500">({pct(g.lo)}–{pct(g.hi)})</span></td>
                {bins.map(b => {
                  const x = g.bins[b.key];
                  return <td key={b.key} className="p-2">{x?.n ? `${pct(x.k / x.n)} (${x.n})` : "–"}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
    </details>
  );
}

function Bar({ value }: { value: number | null }) {
  return (
    <span className="inline-block w-24 h-2 rounded-full bg-slate-200 align-middle mr-2 overflow-hidden">
      <span className="block h-full rounded-full" style={{ width: `${Math.round((value ?? 0) * 100)}%`, background: "#c2410c" }} />
    </span>
  );
}

/** What crosses the borders: Rundata's remarks, texts that name another land and the Danish likeness. */
function CrossBorder({ cb }: { cb: Nordic["crossborder"] }) {
  const L = cb.likeness;
  const feat = (keys: string[]) => keys.map((k, i) => <span key={k}>{i ? ", " : ""}<span>{L.features?.find(x => x.key === k)?.label ?? k}</span></span>);
  const th = "p-2 text-left text-[11px] uppercase tracking-wider text-slate-500";
  return (
    <details className="liquid-glass-island rounded-[24px] p-4" open>
      <summary className="cursor-pointer text-sm font-bold text-slate-800">Över gränserna: dansk prägel på svensk mark och svensk på dansk</summary>
      <div className="mt-3 space-y-5 text-sm text-slate-700">
        {!L.available ? <p className="text-slate-500">{L.reason}</p> : (
          <>
            <div className="space-y-1.5">
              <p>
                En modell har lärt sig skilja danska från svenska runstenar på ordval och stavning, bara bland stenar från
                samma tid ({L.years[0]}–{L.years[1]}: {L.n_train_dk} danska och {L.n_train_se} svenska), så att den lär sig
                skillnaden mellan danskt och svenskt bruk och inte skillnaden mellan tidiga och sena stenar. Den skiljer en
                dansk från en svensk sten rätt i {Math.round((L.auc ?? 0) * 100)} av 100 par. Varje sten får sedan en dansk
                prägel mellan 0 och 1; över 0,5 är den formulerad och stavad mer som en dansk än som en svensk sten. Det
                betyder inte att ristaren var dansk – men en ristare som lärt sig hantverket i Danmark borde ge stenar med hög prägel.
              </p>
              {L.check && (
                <p>
                  <span className="font-semibold">Kontroll:</span> modellen har aldrig sett Rundatas anmärkningar, men de {L.check.n} danska
                  stenar som Rundata kallar svenskgjorda eller svenskpåverkade liknar ändå svenska stenar mer än de andra danska gör:
                  dansk prägel {n2(L.check.mean)} i genomsnitt, mot {n2(L.check.mean_others)} (<Tip text={P}>p</Tip> {pText(L.check.p)}).
                  Plats 1 är den mest svenska av de {L.check.of} danska stenarna:{" "}
                  {L.check.stones.map((s, i) => <span key={s.signum}>{i ? ", " : ""}{STONE(s.signum)} (plats {s.rank})</span>)}.
                </p>
              )}
              <p className="text-xs text-slate-500">
                Bara stenar med minst {L.min_features} av dragen räknas ({L.n_told} danska och svenska stenar); en kort eller skadad text
                säger för lite. Stenar äldre än {L.years[0]} ligger utanför modellens tid: där kan likheten spegla ett äldre
                språk som danskan och de tidiga svenska stenarna delar, inte påverkan.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Var: genomsnittlig dansk prägel</p>
                <table className="text-sm w-full"><tbody>
                  {[...L.by_danish_realm, ...L.by_realm].filter(x => x.n >= 5).map(x => (
                    <tr key={x.key} className="border-t border-slate-900/5">
                      <td className="py-1 pr-2">{x.label}</td><td className="py-1 pr-2 whitespace-nowrap"><Bar value={x.mean} />{n2(x.mean)}</td>
                      <td className="py-1 text-xs text-slate-500 whitespace-nowrap">{x.danish} av {x.n} över 0,5</td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">När: svear och götar per stilgrupp</p>
                <table className="text-sm w-full"><tbody>
                  {L.by_style.filter(x => x.n >= 5).map(x => (
                    <tr key={x.key} className="border-t border-slate-900/5">
                      <td className="py-1 pr-2" translate="no">{x.key}{x.years ? <span className="text-xs text-slate-500"> {x.years}</span> : null}</td>
                      <td className="py-1 pr-2 whitespace-nowrap"><Bar value={x.mean} />{n2(x.mean)}</td>
                      <td className="py-1 text-xs text-slate-500 whitespace-nowrap">{x.danish} av {x.n} över 0,5</td>
                    </tr>
                  ))}
                </tbody></table>
                <p className="text-xs text-slate-500 mt-1">Stilgrupperna i tidsordning (Gräslund); KB är en sidogren utan egen datering.</p>
              </div>
            </div>

            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">De tidigaste stenarna med dansk prägel hos svear och götar</p>
              <p className="text-xs text-slate-500 mb-1">Var den danska seden kan ha slagit rot först: stenar över 0,5, äldst först (Gotland, Jämtland och de omstridda landskapen räknas inte).</p>
              <div className="overflow-x-auto"><ExportTable><table className="text-sm min-w-[640px]">
                <thead><tr><th className={th}>Sten</th><th className={th}>År ca</th><th className={th}>Prägel</th><th className={th}>Ristare</th><th className={th}>Danska drag</th></tr></thead>
                <tbody>
                  {L.earliest_danish.map(b => (
                    <tr key={b.signum} className="border-t border-slate-900/5">
                      <td className="p-2">{STONE(b.signum)} <span className="text-xs text-slate-500" translate="no">{b.place}</span></td>
                      <td className="p-2">{b.year ?? "–"}{b.year != null && b.year < L.years[0] ? <span className="text-xs text-slate-500"> (före modellens tid)</span> : null}</td>
                      <td className="p-2">{n2(b.score)}</td><td className="p-2" translate="no">{b.carvers.join(", ") || "–"}</td>
                      <td className="p-2 text-xs">{feat(b.features)}</td>
                    </tr>
                  ))}
                </tbody>
              </table></ExportTable></div>
            </div>

            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Ristare hos svear och götar med starkast dansk prägel</p>
              <p className="text-xs text-slate-500 mb-1">Rundatas signerade och attribuerade ristare med minst tre stenar som räknas ({L.n_carvers} ristare). Få stenar ger ett osäkert genomsnitt.</p>
              <div className="overflow-x-auto"><ExportTable><table className="text-sm min-w-[640px]">
                <thead><tr><th className={th}>Ristare</th><th className={th}>Stenar</th><th className={th}>Prägel</th><th className={th}>Tidigast ca</th><th className={th}>Landskap</th><th className={th}>Mest danska</th></tr></thead>
                <tbody>
                  {L.carvers.map(c => (
                    <tr key={c.carver} className="border-t border-slate-900/5">
                      <td className="p-2 font-semibold" translate="no">{c.carver}</td><td className="p-2">{c.n}</td>
                      <td className="p-2 whitespace-nowrap"><Bar value={c.mean} />{n2(c.mean)}</td><td className="p-2">{c.first_year ?? "–"}</td>
                      <td className="p-2" translate="no">{c.provinces.join(", ")}</td>
                      <td className="p-2">{c.top.map((s, i) => <span key={s}>{i ? ", " : ""}{STONE(s)}</span>)}</td>
                    </tr>
                  ))}
                </tbody>
              </table></ExportTable></div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Svenska stenar som liknar danska mest</p>
                <ul className="space-y-1">
                  {L.most_danish.slice(0, 12).map(b => (
                    <li key={b.signum}>{STONE(b.signum)} {n2(b.score)} <span className="text-xs text-slate-500"><span translate="no">{b.place}</span>{b.year ? `, ca ${b.year}` : ""}{b.carvers.length ? <span translate="no">, {b.carvers.join(", ")}</span> : null}</span></li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Danska stenar som liknar svenska mest</p>
                <ul className="space-y-1">
                  {L.most_swedish_dk.map(b => (
                    <li key={b.signum}>{STONE(b.signum)} {n2(b.score)} <span className="text-xs text-slate-500"><span translate="no">{b.place}</span>{b.year ? `, ca ${b.year}` : ""}</span></li>
                  ))}
                </ul>
              </div>
            </div>

            <details>
              <summary className="cursor-pointer text-xs font-bold text-slate-700">Dragen modellen väger</summary>
              <div className="overflow-x-auto mt-2"><ExportTable><table className="text-sm min-w-[520px]">
                <thead><tr><th className={th}>Drag</th><th className={th}>Danska stenar</th><th className={th}>Svenska stenar</th>
                  <th className={th}><Tip text={`${ODDS} Här med de andra dragen konstanta; över 1 drar draget mot dansk.`}>Oddskvot</Tip></th></tr></thead>
                <tbody>
                  {[...L.features].sort((a, b) => b.or - a.or).map(x => (
                    <tr key={x.key} className="border-t border-slate-900/5">
                      <td className="p-2">{x.label}</td><td className="p-2">{pct(x.dk)}</td><td className="p-2">{pct(x.se)}</td><td className="p-2 font-semibold">{n2(x.or)}</td>
                    </tr>
                  ))}
                </tbody>
              </table></ExportTable></div>
              <p className="text-xs text-slate-500 mt-1">Andelarna gäller de samtida stenar som modellen tränades på.</p>
            </details>
          </>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Rundatas anmärkningar om ett annat lands ristare eller språk</p>
            <ul className="space-y-1.5">
              {cb.remarks.map(r => <li key={r.signum}>{STONE(r.signum)} <span className="text-xs text-slate-500">{r.year ? `ca ${r.year}` : ""}</span> – {r.text}</li>)}
            </ul>
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Texter som nämner ett annat nordiskt land</p>
            <ul className="space-y-1.5">
              {cb.mentions.map(r => (
                <li key={`${r.signum}-${r.names}`}>{STONE(r.signum)} <span className="text-xs text-slate-500">({LAND_ADJ[r.land]}, nämner {LAND_NAME[r.names]}{r.year ? `, ca ${r.year}` : ""})</span> – <span translate="no">”{r.text}”</span></li>
              ))}
            </ul>
            <p className="text-xs text-slate-500 mt-1">Ur Rundatas engelska översättning.</p>
          </div>
        </div>
      </div>
    </details>
  );
}
