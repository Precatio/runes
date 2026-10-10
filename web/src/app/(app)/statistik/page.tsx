"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/api";

interface Status {
  r: { available: boolean; version: string | null; missing: string[]; note: string | null };
  corpus?: {
    fingerprint: string; n_stones: number; ready: boolean; computed_at: string | null; running: boolean;
    module: string | null; done_modules: string[]; error: string | null; errors: Record<string, string> | null;
    modules: { key: string; label: string }[];
  };
}

type Dict = Record<string, unknown>;
interface Pattern { topic: string; status: string; text: string; note?: string | null }
interface Finding {
  signum: string; place: string; method: string; verdict: string; ours: string; existing: string; score: number;
  assessment: string; suggested?: string; crosscheck?: { status: string; runor?: { text: string; url?: string | null } };
}
interface Corpus {
  computed_at: string; r_version: string; errors: Record<string, string>;
  figure_urls: Record<string, Record<string, string>>;
  patterns: Pattern[]; findings: Finding[];
  findings_summary: { n: number; new: number; contradicts: number; crosschecked: number; already_known: number; still_new: number };
  html_map_url: string | null;
  geography: Dict & { carvers: { carver: string; n: number; median_km: number; random_median_km: number; compact_ratio: number; compact_q: number; provinces: string; hull_area_km2: number }[]; method: string; water: Dict & { note?: string } };
  clusters: Dict & { k: number; best_silhouette: number; structure: string; n_stones: number; method: string; carvers: { ari: number };
    clusters: { cluster: number; n: number; stability: number; silhouette: number; features: { level: string; share_in_cluster: number; share_overall: number }[]; styles: { style: string; n: number }[]; provinces: { province: string; n: number }[] }[] };
  text: Dict & { method: string; lemmas: { lemma: string; n: number; cramers_v: number; q: number }[];
    formulas: { tests: { label: string; cramers_v: number; q: number }[] } };
  attribution: Dict & { method: string; caveat: string; n_train: number; carvers: string[]; majority_baseline: number;
    ablation: { features: string; accuracy: number; top3: number; log_loss: number }[];
    grouped_cv?: Record<string, { level: string; n_groups: number; ablation: { features: string; accuracy: number | null; top3: number | null }[] }>;
    calibration: { ece: number; reliability: { threshold: number; n: number; accuracy: number }[] };
    per_carver: { carver: string; n: number; recall: number; precision: number | null }[] };
  chronology: Dict & { method: string; region: string; validation: { rho: number; partial_rho: number; usable: boolean; mae_loo_years: number; mae_naive_years: number };
    corpus_dimensions: { dim: number; inertia_pct: number; rho_time: number; rho_lat: number; eta2_province: number; eta2_carver: number; positive: string[]; negative: string[]; unexplained: boolean; explained_by: string[] }[] };
  dialect: Dict & { method: string; caveat: string; mantel: { r: number; p: number }; n_districts: number;
    groups: { group: number; n: number; provinces: string }[]; group_forms: { group: number; forms: { lemma: string; form: string; share_in_group: number; share_all: number }[] }[] };
  network: Dict & { method: string; modularity: number; communities: { community: number; size: number; words: { word: string }[] }[];
    kinship: { relation: string; n: number; early: number; late: number; q_period: number; share_christian: number; share_other: number; q_christian: number }[] };
}

type Tab = "overview" | "geography" | "clusters" | "text" | "attribution" | "chronology" | "network";
const TABS: [Tab, string][] = [
  ["overview", "Översikt"], ["geography", "Geografi"], ["clusters", "Grupper"], ["text", "Språk och dialekter"],
  ["attribution", "Attribueringsmodell"], ["chronology", "Seriation"], ["network", "Formelnätverk"],
];

const d2 = (v: number | null | undefined, k = 2) => v == null ? "–" : v.toFixed(k).replace(".", ",");
const pc = (v: number | null | undefined) => v == null ? "–" : `${Math.round(v * 100)} %`;
const TH = "text-left text-[11px] uppercase tracking-wider text-slate-500 p-2";

function Fig({ src, alt }: { src?: string; alt: string }) {
  if (!src) return null;
  return (
    <figure className="rounded-2xl bg-white border border-slate-200 p-2">
      {/* eslint-disable-next-line @next/next/no-img-element -- figures are rendered by R on the backend */}
      <img src={`${API_URL}${src}`} alt={alt} className="w-full h-auto rounded-xl" loading="lazy" />
    </figure>
  );
}

function Method({ text, caveat }: { text?: string; caveat?: string }) {
  if (!text) return null;
  return (
    <details className="text-xs text-slate-600 rounded-xl bg-slate-50 border border-slate-200 p-3">
      <summary className="cursor-pointer font-semibold">Metod{caveat ? " och reservationer" : ""}</summary>
      <p className="mt-2">{text}</p>
      {caveat && <p className="mt-2 text-amber-900">{caveat}</p>}
    </details>
  );
}

export default function StatistikPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [data, setData] = useState<Corpus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  const [tick, setTick] = useState(0);

  // Loads the status and, when the corpus analyses are ready, their results; tick reloads
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/r/status`).then(r => r.json()).then(async (st: Status) => {
      if (cancelled) return;
      setStatus(st);
      if (st.corpus?.ready) {
        const res = await fetch(`${API_URL}/api/r/corpus`);
        if (res.ok && !cancelled) setData(await res.json());
      }
    }).catch(() => { if (!cancelled) setError("Kunde inte nå analysmotorn."); });
    return () => { cancelled = true; };
  }, [tick]);

  // Poll while the corpus analyses run
  useEffect(() => {
    if (!status?.corpus?.running) return;
    const t = setInterval(() => setTick(x => x + 1), 4000);
    return () => clearInterval(t);
  }, [status?.corpus?.running]);

  const start = async () => {
    setError(null);
    const res = await fetch(`${API_URL}/api/r/corpus/run`, { method: "POST" });
    if (!res.ok) { setError((await res.json().catch(() => null))?.detail || `Fel ${res.status}`); return; }
    setTick(x => x + 1);
  };

  const c = status?.corpus;
  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Statistik (R)</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Hela korpusen av svenska vikingatida runstenar analyserad i R: ristarnas områden, grupper av stil och språk,
          stavning och dialekter, en korsvaliderad attribueringsmodell, seriation mot Gräslunds kronologi och formelnätverk.
          Samma analyser används för den enskilda stenen i <Link href="/stenanalys" className="text-[#b7410e] hover:underline">Fullständig stenanalys</Link> och
          stenrapporten, och resultaten ställs mot forskningen i <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>.
        </p>
      </div>

      {error && <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-3 text-sm text-red-800">{error}</div>}

      <div className="liquid-glass-island rounded-[24px] p-5 flex flex-wrap items-center gap-4">
        {!status ? <span className="text-slate-500">Hämtar läget …</span> : !status.r.available ? (
          <div className="text-sm text-amber-900">
            <strong>R är inte tillgängligt på servern.</strong> {status.r.note}
            {status.r.missing.length > 0 && <div className="text-xs mt-1">Saknas: {status.r.missing.join(", ")}</div>}
          </div>
        ) : (
          <>
            <div className="text-sm">
              <div className="font-bold text-slate-900">{status.r.version}</div>
              <div className="text-slate-500 text-xs">
                Korpus: {c?.n_stones} runstenar · version {c?.fingerprint}
                {c?.computed_at && ` · beräknad ${new Date(c.computed_at).toLocaleString("sv-SE")}`}
              </div>
            </div>
            {c && !c.ready && !c.running && (
              <button onClick={start} className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-bold">
                Beräkna korpusanalyserna (några minuter)
              </button>
            )}
            {c?.running && (
              <div className="flex flex-wrap gap-2 text-xs">
                {c.modules.map(m => (
                  <span key={m.key} className={`px-2 py-1 rounded-lg border ${c.done_modules.includes(m.key) ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                    : c.module === m.key ? "bg-amber-50 border-amber-300 text-amber-900 animate-pulse" : "bg-white border-slate-200 text-slate-500"}`}>
                    {c.done_modules.includes(m.key) ? "✓ " : ""}{m.label}
                  </span>
                ))}
              </div>
            )}
            {c?.error && !c.running && <span className="text-xs text-red-700">{c.error}</span>}
            {data && (
              <a href={`${API_URL}/api/r/package`} className="ml-auto px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold hover:bg-slate-50">
                Ladda ner reproducerbarhetspaket (R-skript, data, resultat)
              </a>
            )}
          </>
        )}
      </div>

      {data && (
        <>
          <div className="flex flex-wrap gap-2">
            {TABS.map(([key, label]) => (
              <button key={key} onClick={() => setTab(key)}
                className={`px-4 py-2 rounded-xl text-sm font-bold border ${tab === key ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
                {label}
              </button>
            ))}
          </div>
          <div className="liquid-glass-island rounded-[32px] p-5 space-y-5">
            {tab === "overview" && <Overview data={data} />}
            {tab === "geography" && <Geography data={data} />}
            {tab === "clusters" && <Clusters data={data} />}
            {tab === "text" && <TextTab data={data} />}
            {tab === "attribution" && <Attribution data={data} />}
            {tab === "chronology" && <Chronology data={data} />}
            {tab === "network" && <Network data={data} />}
          </div>
        </>
      )}
    </div>
  );
}

const STATUS_STYLE: Record<string, string> = {
  "bekräftar": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "mönster att pröva": "bg-amber-50 text-amber-900 border-amber-200",
  "begränsning": "bg-slate-100 text-slate-700 border-slate-300", "svagt": "bg-slate-100 text-slate-700 border-slate-300",
};

function Overview({ data }: { data: Corpus }) {
  const s = data.findings_summary;
  const top = data.findings.filter(f => f.verdict !== "stämmer").slice(0, 25);
  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[["Fynd per sten", s.n], ["Nya mot Rundata", s.new], ["Motsäger Rundata", s.contradicts],
          ["Finns redan i nyare källa", s.already_known], ["Nya även mot Runor 2020", s.still_new]].map(([l, v]) => (
          <div key={l as string} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{l}</div>
            <div className="text-2xl font-bold text-slate-900">{v}</div>
          </div>
        ))}
      </div>
      <div>
        <h3 className="font-bold text-slate-900 mb-2">Mönster i korpusen</h3>
        <ul className="space-y-2 text-sm">
          {data.patterns.map((pt, i) => (
            <li key={i} className="flex gap-3">
              <span className={`shrink-0 h-fit px-2 py-0.5 rounded-lg border text-[11px] font-bold ${STATUS_STYLE[pt.status] ?? ""}`}>{pt.status}</span>
              <div><span className="text-[11px] uppercase tracking-wider text-slate-500 mr-2">{pt.topic}</span>{pt.text}
                {pt.note && <div className="text-xs text-slate-500 mt-0.5">{pt.note}</div>}</div>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-slate-900 mb-1">Starkaste fynden per sten</h3>
        <p className="text-xs text-slate-500 mb-2">
          Nya och motsägande resultat från attribueringsmodellen och seriationen. &quot;Nyare källor&quot; visar avstämningen mot
          Runor 2020 och Wikidata (görs i <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>).
          Ett förslag är en hypotes för en runolog att pröva, inte en attribuering.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr><th className={TH}>Sten</th><th className={TH}>Metod</th><th className={TH}>Mot Rundata</th><th className={TH}>Resultat</th>
              <th className={TH}>Rundata</th><th className={TH}>Nyare källor</th><th className={TH}>Bedömning</th></tr></thead>
            <tbody>
              {top.map(f => (
                <tr key={`${f.signum}|${f.method}`} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold"><Link href={`/inskrifter/${encodeURIComponent(f.signum)}`} className="hover:underline">{f.signum}</Link>
                    <div className="text-[11px] text-slate-500 font-normal">{f.place}</div></td>
                  <td className="p-2 text-xs">{f.method}</td>
                  <td className="p-2 text-xs font-bold">{f.verdict}</td>
                  <td className="p-2 text-xs max-w-[280px]">{f.ours}</td>
                  <td className="p-2 text-xs">{f.existing}</td>
                  <td className="p-2 text-xs" title={f.crosscheck?.runor?.text}>{f.crosscheck?.status ?? "–"}</td>
                  <td className="p-2 text-xs font-semibold">{f.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function Geography({ data }: { data: Corpus }) {
  const g = data.geography, f = data.figure_urls.geography || {};
  return (
    <>
      <p className="text-sm text-slate-700">
        {String(g.n_compact)} av {g.carvers.length} ristare med minst fem säkra stenar arbetade inom ett mindre område än slumpvisa
        stenar ur samma landskap.{" "}
        {data.html_map_url && <a href={`${API_URL}${data.html_map_url}`} target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Öppna den interaktiva kartan (leaflet)</a>}
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.map} alt="Ristarnas områden" /><Fig src={f.water} alt="Avstånd till vatten" /></div>
      {g.water?.note && <p className="text-xs text-amber-900">{g.water.note}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><th className={TH}>Ristare</th><th className={TH}>Säkra stenar</th><th className={TH}>Median till tyngdpunkt</th>
            <th className={TH}>Slumpvisa urval</th><th className={TH}>Kvot</th><th className={TH}>q</th><th className={TH}>Höljets yta</th><th className={TH}>Landskap</th></tr></thead>
          <tbody>{g.carvers.map(r => (
            <tr key={r.carver} className="border-t border-slate-900/5">
              <td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td><td className="p-2">{d2(r.median_km, 1)} km</td>
              <td className="p-2">{d2(r.random_median_km, 1)} km</td><td className="p-2">{d2(r.compact_ratio)}</td><td className="p-2">{d2(r.compact_q, 3)}</td>
              <td className="p-2">{r.hull_area_km2} km²</td><td className="p-2 text-xs">{r.provinces}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={g.method} />
    </>
  );
}

function Clusters({ data }: { data: Corpus }) {
  const c = data.clusters, f = data.figure_urls.clusters || {};
  return (
    <>
      <p className="text-sm text-slate-700">
        {c.n_stones} stenar i {c.k} grupper; strukturen är {c.structure} (silhuettbredd {d2(c.best_silhouette)}). Grupperna
        sammanfaller inte med ristarna (justerat Rand-index {d2(c.carvers.ari)}).
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.mca} alt="MCA" /><Fig src={f.variables} alt="Kategorier i MCA" />
        <Fig src={f.silhouette} alt="Silhuettbredd" /><Fig src={f.carvers} alt="Ristare per grupp" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><th className={TH}>Grupp</th><th className={TH}>Stenar</th><th className={TH}>Stabilitet</th><th className={TH}>Utmärks av</th><th className={TH}>Stilgrupper</th><th className={TH}>Landskap</th></tr></thead>
          <tbody>{c.clusters.map(k => (
            <tr key={k.cluster} className="border-t border-slate-900/5 align-top">
              <td className="p-2 font-semibold">{k.cluster}</td><td className="p-2">{k.n}</td><td className="p-2">{d2(k.stability)}</td>
              <td className="p-2 text-xs">{k.features.slice(0, 4).map(x => `${x.level} (${pc(x.share_in_cluster)} mot ${pc(x.share_overall)})`).join("; ")}</td>
              <td className="p-2 text-xs">{k.styles.map(x => `${x.style} ${x.n}`).join(", ")}</td>
              <td className="p-2 text-xs">{k.provinces.map(x => `${x.province} ${x.n}`).join(", ")}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={c.method} />
    </>
  );
}

function TextTab({ data }: { data: Corpus }) {
  const t = data.text, dl = data.dialect, ft = data.figure_urls.text || {}, fd = data.figure_urls.dialect || {};
  return (
    <>
      <h3 className="font-bold text-slate-900">Ristarnas stavning och formler</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={ft.formulas} alt="Formler per ristare" /><Fig src={ft.lemmas} alt="Stavning per ord" /></div>
      <p className="text-sm text-slate-700">
        Formler som skiljer ristarna åt: {t.formulas.tests.map(x => `${x.label} (Cramérs V ${d2(x.cramers_v)})`).join(", ")}.
      </p>
      <Method text={t.method} />
      <h3 className="font-bold text-slate-900 pt-3">Stavning och dialekter</h3>
      <p className="text-sm text-slate-700">
        Ortografiskt avstånd mot geografiskt avstånd mellan {dl.n_districts} härader: Mantel r {d2(dl.mantel.r)}, p {d2(dl.mantel.p, 3)}.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={fd.distance} alt="Stavning mot avstånd" /><Fig src={fd.groups} alt="Härader med likartad stavning" />
        <Fig src={fd.efter} alt="Stavning av efter" /><Fig src={fd.sten} alt="Diftongen i sten" />
      </div>
      <ul className="text-sm space-y-1">
        {dl.group_forms.map(g => (
          <li key={g.group}><strong>Grupp {g.group}</strong> ({dl.groups.find(x => x.group === g.group)?.provinces}):{" "}
            {g.forms.map(x => `${x.lemma} = ${x.form} (${pc(x.share_in_group)} mot ${pc(x.share_all)})`).join("; ")}</li>
        ))}
      </ul>
      <Method text={dl.method} caveat={dl.caveat} />
    </>
  );
}

function Attribution({ data }: { data: Corpus }) {
  const a = data.attribution, f = data.figure_urls.attribution || {};
  return (
    <>
      <p className="text-sm text-slate-700">
        {a.n_train} säkra stenar av {a.carvers.length} ristare. Modellen hittar rätt ristare i{" "}
        {pc(a.ablation.find(x => x.features === "Alla")?.accuracy)} av fallen vid korsvalidering, mot {pc(a.majority_baseline)} om man alltid
        gissar på den vanligaste ristaren. Sannolikheterna är försiktiga:{" "}
        {a.calibration.reliability.map(r => `vid minst ${d2(r.threshold, 1)} är förstavalet rätt i ${pc(r.accuracy)} (${r.n} stenar)`).join("; ")}.
      </p>
      {a.grouped_cv && (
        <div className="overflow-x-auto">
          <p className="text-sm text-slate-700 mb-2">
            <strong>Fungerar modellen på en ny plats?</strong> Vid slumpvis korsvalidering kan stenar från samma plats finnas
            både i tränings- och testdata. Här hålls hela socknar respektive härader utanför träningen; en ristare som bara
            finns i det utelämnade området kan då inte föreslås och räknas som fel.
          </p>
          <table className="w-full text-sm">
            <thead><tr><th className={TH}>Belägg</th><th className={TH}>Slumpvis</th>
              {Object.entries(a.grouped_cv).map(([k, g]) => <th key={k} className={TH}>Ny {k.toLowerCase()} ({g.n_groups} grupper)</th>)}</tr></thead>
            <tbody>{a.ablation.map(x => (
              <tr key={x.features} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{x.features}</td><td className="p-2">{pc(x.accuracy)}</td>
                {Object.entries(a.grouped_cv!).map(([k, g]) => <td key={k} className="p-2">{pc(g.ablation.find(y => y.features === x.features)?.accuracy ?? undefined)}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.ablation} alt="Delmodeller" /><Fig src={f.calibration} alt="Kalibrering" />
        <Fig src={f.importance} alt="Variabler" /><Fig src={f.confusion} alt="Förväxlingar" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><th className={TH}>Ristare</th><th className={TH}>Säkra stenar</th><th className={TH}>Hittas (recall)</th><th className={TH}>Rätt när föreslagen (precision)</th></tr></thead>
          <tbody>{a.per_carver.map(r => (
            <tr key={r.carver} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td>
              <td className="p-2">{pc(r.recall)}</td><td className="p-2">{pc(r.precision)}</td></tr>))}</tbody>
        </table>
      </div>
      <Method text={a.method} caveat={a.caveat} />
    </>
  );
}

function Chronology({ data }: { data: Corpus }) {
  const ch = data.chronology, f = data.figure_urls.chronology || {}, v = ch.validation;
  return (
    <>
      <p className="text-sm text-slate-700">
        I {ch.region === "U" ? "Uppland" : ch.region} ordnar seriationen av språk och innehåll stenarna i samma följd som Gräslunds stilkronologi
        (rho {d2(v.rho)}, {d2(v.partial_rho)} med latituden konstant), utan att ornamentiken ingick. Årtalen är osäkra:
        medelfel {v.mae_loo_years} år mot {v.mae_naive_years} år utan modell.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.validation} alt="Seriation mot Gräslund" /><Fig src={f.diagram} alt="Seriationsdiagram" /><Fig src={f.estimates} alt="Skattad tid" />
      </div>
      <h3 className="font-bold text-slate-900">Vad korpusens dimensioner följer</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><th className={TH}>Dimension</th><th className={TH}>Inerti</th><th className={TH}>Tid (rho)</th><th className={TH}>Latitud (rho)</th>
            <th className={TH}>Landskap (eta²)</th><th className={TH}>Ristare (eta²)</th><th className={TH}>Förklaras av</th><th className={TH}>Skiljer</th></tr></thead>
          <tbody>{ch.corpus_dimensions.map(x => (
            <tr key={x.dim} className={`border-t border-slate-900/5 align-top ${x.unexplained ? "bg-amber-50" : ""}`}>
              <td className="p-2 font-semibold">{x.dim}</td><td className="p-2">{d2(x.inertia_pct, 1)} %</td><td className="p-2">{d2(x.rho_time)}</td>
              <td className="p-2">{d2(x.rho_lat)}</td><td className="p-2">{d2(x.eta2_province)}</td><td className="p-2">{d2(x.eta2_carver)}</td>
              <td className="p-2 text-xs font-semibold">{x.unexplained ? "oförklarat mönster" : x.explained_by.join(", ")}</td>
              <td className="p-2 text-xs">{x.positive.slice(0, 3).join(", ")} ↔ {x.negative.slice(0, 3).join(", ")}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={ch.method} />
    </>
  );
}

function Network({ data }: { data: Corpus }) {
  const n = data.network, f = data.figure_urls.network || {};
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.network} alt="Formelnätverk" /><Fig src={f.kinship} alt="Släktrelationer" /></div>
      <ul className="text-sm space-y-1">
        {n.communities.map(c => <li key={c.community}><strong>Grupp {c.community}</strong> ({c.size} ord): {c.words.map(w => w.word).join(", ")}</li>)}
      </ul>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><th className={TH}>Relation</th><th className={TH}>Inskrifter</th><th className={TH}>Före ca 1050</th><th className={TH}>Efter ca 1050</th>
            <th className={TH}>q (tid)</th><th className={TH}>Kristna</th><th className={TH}>Övriga</th><th className={TH}>q (kristen)</th></tr></thead>
          <tbody>{n.kinship.map(k => (
            <tr key={k.relation} className={`border-t border-slate-900/5 ${k.q_period < 0.05 ? "bg-amber-50" : ""}`}>
              <td className="p-2 font-semibold">{k.relation}</td><td className="p-2">{k.n}</td><td className="p-2">{pc(k.early)}</td><td className="p-2">{pc(k.late)}</td>
              <td className="p-2">{d2(k.q_period, 3)}</td><td className="p-2">{pc(k.share_christian)}</td><td className="p-2">{pc(k.share_other)}</td><td className="p-2">{d2(k.q_christian, 3)}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={n.method} />
    </>
  );
}
