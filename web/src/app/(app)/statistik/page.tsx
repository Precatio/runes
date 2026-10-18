"use client";

import { useEffect, useState, type ReactNode } from "react";
import { DocsNote } from "@/components/KnownLimitations";
import { Confidence, Details, Figure, Glossary, LEVEL_STYLE, Md, SigBadge, Tip, asList, type Level } from "@/components/Explain";
import { PatternBadges, PatternBody, type Pattern } from "@/components/PatternCard";
import { GLOSSARY } from "@/lib/glossary";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import ExportTable from "@/components/ExportTable";
import PlotlyGraph from "@/components/PlotlyGraph";

interface Status {
  r: { available: boolean; version: string | null; missing: string[]; note: string | null };
  corpus?: {
    fingerprint: string; n_stones: number; ready: boolean; computed_at: string | null; running: boolean;
    module: string | null; done_modules: string[]; error: string | null; errors: Record<string, string> | null;
    modules: { key: string; label: string }[];
  };
}

type Dict = Record<string, unknown>;
interface ChangeFeature {
  key: string; label: string; group: string; n: number; share: number;
  time: {
    tested: boolean; n: number; n_yes: number; p?: number; q?: number | null; shape?: string; peak_year?: number | null;
    year_first?: number; year_last?: number; first?: number; last?: number; change_lo?: number; change_hi?: number;
    draws?: { n: number; share_sig: number | null; share_same_shape: number | null };
    curve?: { year: number; share: number }[];
  };
  provinces: { p_differ: number; q_differ?: number; p_differ_nocarver?: number; rows: { province: string; n: number; share1050: number; lo1050: number; hi1050: number; cross_year: number | null; cross_lo: number | null; cross_hi: number | null }[] } | null;
  space: { n: number; p: number; high: string[] | string; low: string[] | string } | null;
}
interface AnonGroup {
  id: number; name?: string | null; status: "candidate" | "known"; type_stone: string; n: number; spread_km: number;
  stones: string[]; parishes: string[] | string; styles: { style: string; n: number }[] | null; stability: number;
  marks: { feature: string; share_group: number; share_area: number }[] | null;
  nearest_carver: { carver: string; n: number; dist: number; km: number; as_close_as_same_carver: boolean } | null;
  model: { n: number; carver: string; share: number; mean_p: number } | null;
}
interface ChangeAssoc {
  key: string; label: string; n: number; n_x: number; share_x: number; share_other: number;
  all: { or: number; lo: number; hi: number; p: number; q: number | null } | null;
  dated: { n: number; or?: number; lo?: number; hi?: number; p?: number } | null;
}

interface RemainsTest {
  label: string; n: number; or: number; lo: number; hi: number; p: number; q_bh: number;
  halves?: { replicated: boolean }; periods?: { early: number; late: number; n_early: number; n_late: number };
}
interface CultTest extends RemainsTest { share_near: number; share_far: number; n_near: number; n_places?: number; loo?: { min_or: number; max_or: number } }
interface CultResult {
  available: boolean; near_km: number; n_a: number; n_b: number; n_c?: number; stones_near_a: number; stones_near_b: number;
  near_a_stones: number; near_a_random: number; tests?: Record<string, CultTest>;
  radius?: { km: number; n_near: number; or: number; p: number }[];
  pagan?: { signum: string; km_a: number; km_b: number }[];
  churches?: { n_churches: number; n_other: number; near_church_other: number; near_km: number;
    rows: { tier: string; n: number; near_church: number; or: number; p: number }[]; age?: ChurchAge } | null;
}
type AgeTerm = { or: number; lo: number; hi: number; p: number; halves?: { replicated: boolean } } | null;
interface ChurchAge {
  early_year: number; n_early: number; n_late: number; near_km: number;
  tests: { feature: string; label: string; n: number; early: AgeTerm; late: AgeTerm; early_time: AgeTerm; late_time: AgeTerm;
    ratio: number; p_diff: number; share_early: number; n_early: number; share_late: number; n_late: number; share_none: number; n_none: number }[];
}
interface VikingShore {
  n_stones: number; median_stones_km: number; median_random_km: number; p: number; error?: string;
  provinces?: { province: string; uplift_m: number; n: number; median_stones_km: number; median_random_km: number; p: number }[];
}

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
  geography: Dict & { carvers: { carver: string; n: number; median_km: number; random_median_km: number; compact_ratio: number; compact_q: number; provinces: string; hull_area_km2: number }[]; method: string;
    water: Dict & { note?: string; viking_shore?: VikingShore; provinces?: { province: string; median_stones_km: number; median_random_km: number }[] } };
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
    corpus_dimensions: { dim: number; inertia_pct: number; rho_time: number; rho_lat: number; eta2_province: number; eta2_carver: number; positive: string[] | string; negative: string[] | string; unexplained: boolean; explained_by: string[] | string }[] };
  dialect: Dict & { method: string; caveat: string; mantel: { r: number; p: number }; n_districts: number;
    groups: { group: number; n: number; provinces: string }[]; group_forms: { group: number; forms: { lemma: string; form: string; share_in_group: number; share_all: number }[] }[] };
  network: Dict & { method: string; modularity: number; communities: { community: number; size: number; words: { word: string }[] }[];
    kinship: { relation: string; n: number; early: number; late: number; q_period: number; share_christian: number; share_other: number; q_christian: number }[] };
  change?: Dict & { method: string; n_dated: number; draws: number; features: ChangeFeature[]; assoc: ChangeAssoc[] };
  remains?: Dict & { available: boolean; note?: string; method?: string; near_km?: number; n_stones?: number;
    distances?: { key: string; label: string; n_remains: number; median_stones_km: number; median_random_km: number; near_stones: number; near_random: number; q_bh: number }[];
    tests?: Record<string, RemainsTest>;
    gravfalt_provinces?: { province: string; n: number; near_stones: number; near_random: number; p: number }[];
    cult?: CultResult };
  anonymous?: Dict & { method: string; n_unattributed: number; n_candidates: number;
    calibration: { link_km: number; lr_min: number; tpr: number; fpr: number; precision: number; max_spread_km: number };
    validation: { n_groups: number; n_stones: number; purity: number; purity_geography: number; share_pure: number };
    groups: AnonGroup[] };
  words?: Dict & { method: string; n_stones: number; n_dated: number; n_words_tested: number;
    provinces_tested: string[] | string; n_region_tests: number; n_time_tests: number;
    region: { word: string; province: string; logodds: number; q: number; k_in: number; n_in: number;
      k_out: number; n_out: number; rate_in: number; rate_out: number; holds: boolean }[];
    time: { word: string; slope: number; q: number; shares: { epoch: string; k: number; n: number }[] }[];
    ca: { inertia: number[]; provinces: { code: string; x: number; y: number; n: number }[];
      words: { w: string; x: number; y: number; n: number }[] };
    neighbors: { a: string; b: string; dist: number }[] };
  sections?: Section[];
  overview?: { paragraphs: string[]; next_steps: string[] };
}

type Tab = "overview" | "geography" | "clusters" | "text" | "attribution" | "anonymous" | "chronology" | "change" | "network" | "words";

const d2 = (v: number | null | undefined, k = 2) => v == null ? "–" : v.toFixed(k).replace(".", ",");
const pc = (v: number | null | undefined) => v == null ? "–" : `${Math.round(v * 100)} %`;
const TH = "text-left text-[11px] uppercase tracking-wider text-slate-500 p-2";

// How to read each figure (keyed by its alt text)
const FIG_HELP: Record<string, string> = {
  "Ristarnas områden": "Varje panel är en ristare. Blå punkter är ristarens säkra stenar, linjen är det konvexa höljet runt dem och + tyngdpunkten; grått är alla runstenar. Ett litet, samlat hölje betyder att ristaren arbetade lokalt.",
  "Lämningar runt stenarna": "Andelen runstenar (blått) och slumpvisa punkter på land i stenarnas närhet (grått) som ligger inom 500 m från en registrerad lämning av varje slag i Kulturmiljöregistret. En högre blå stapel betyder att stenarna står närmare den sortens lämningar än slumpen ger.",
  "Avstånd till vatten": "Fördelningen av avstånd till närmaste strand, sjö eller vattendrag för runstenarna och för slumpvisa punkter på land (rotskala). Ligger runstenarnas fördelning till vänster står de närmare vatten än slumpen ger.",
  "MCA": "Stenarna i det rum som korrespondensanalysen ger (de två första dimensionerna). Varje panel visar en grupp i blått mot alla stenar i grått; en grupp som ligger samlat skiljer sig tydligt från de andra.",
  "Kategorier i MCA": "De drag som bidrar mest till de två första dimensionerna. Drag som ligger nära varandra förekommer ofta på samma stenar; ju längre från mitten, desto mer skiljer draget stenarna åt.",
  "Silhuettbredd": "Hur tydliga grupperna blir för olika antal grupper (k). Antalet med högst värde väljs; under 0,25 betyder svag struktur.",
  "Ristare per grupp": "Hur varje ristares säkra stenar fördelar sig på grupperna (talen är antal stenar, färgen andel). Om grupperna motsvarade ristare skulle varje rad ha all färg i en enda ruta.",
  "Formler per ristare": "Vilka resarformler (t.ex. lét resa, reste) och ristarsignaturer varje ristare använder, som andel av ristarens säkra inskrifter.",
  "Stavning per ord": "Ord vars stavning bäst skiljer ristarna åt, mätt med Cramérs V. Längre stapel betyder att stavningen av ordet säger mer om vem som ristade.",
  "Stavning mot avstånd": "Varje punkt är ett par härader: hur långt ifrån varandra de ligger mot hur olika de stavar. En stigande linje betyder att stavningen skiljer sig mer ju längre ifrån varandra häraderna ligger.",
  "Härader med likartad stavning": "Härader som stavar likartat har samma färg. Grupperna bildades bara ur stavningen; att de ändå hänger ihop på kartan tyder på regionala skrivtraditioner (eller ristarverkstäder).",
  "Stavning av efter": "Hur æftiR (efter) stavas på stenarna i olika delar av landet.",
  "Diftongen i sten": "Om sten skrivs med diftong (stain) eller monoftong (stin) på olika platser.",
  "Delmodeller": "Hur ofta modellen hittar rätt ristare med bara geografi, bara stil, bara språk och innehåll, eller allt – slumpvis och med hela socknar utelämnade. Den streckade linjen är att alltid gissa på den vanligaste ristaren.",
  "Kalibrering": "Stämmer modellens sannolikheter? Punkterna visar hur ofta förstavalet var rätt vid olika sannolikheter (större punkt = fler stenar). På den streckade diagonalen är sannolikheterna exakta; ovanför är modellen försiktig och har rätt oftare än den säger.",
  "Variabler": "Vilka variabler modellen förlitar sig mest på: hur mycket träffsäkerheten sjunker när variabeln blandas om slumpvis.",
  "Förväxlingar": "Rad = rätt ristare, kolumn = modellens förstaval. En mörk diagonal betyder rätt; mörka rutor utanför diagonalen visar vilka ristare som förväxlas.",
  "Seriation mot Gräslund": "Stenarnas läge i seriationen (som bara bygger på språk och innehåll) för varje stilgrupp. Stiger lådorna från RAK till Pr5 följer seriationen Gräslunds kronologi, utan att ornamentiken ingått.",
  "Seriationsdiagram": "Stenarna ordnade efter seriationen i tio lika stora grupper, från tidigt till sent. Stapelns höjd är hur vanligt draget är i gruppen; drag överst hör till de tidiga stenarna, drag nederst till de sena.",
  "Skattad tid": "Skattat årtal för stenar utan stilgrupp, ur seriationen. Osäkerheten är stor – ordningen är säkrare än årtalet.",
  "Formelnätverk": "Ord som ofta står i samma inskrifter är förbundna (tätare linje = starkare samband, större punkt = fler inskrifter). Ord med samma färg bildar en grupp som hör ihop, t.ex. en formel.",
  "Släktrelationer": "Hur stor andel av runstenarna i varje landskap som nämner en viss släktrelation.",
  "Dragen över tid": "Punkterna är andelen stenar med draget i varje stilgrupp, med 95 % intervall (större punkt = fler stenar). Den blå linjen är den justerade andelen med plats och ristare konstanta: förändringen över tid när man rensat för att olika perioder har stenar från olika trakter och ristare. Rubriken anger förloppet och q-värdet.",
  "Var dragen är vanligast": "Modellens skattade andel stenar med draget för en typisk ristare; mörkare blå = vanligare. Kartan visas bara nära stenar där draget kan bestämmas, och bara för drag där platsen spelar roll.",
  "Landskapen omkring 1050": "Skattad andel stenar med draget omkring år 1050 i varje landskap, med 95 % intervall. Intervall som inte överlappar tyder på en verklig skillnad mellan landskapen.",
  "Grupper av stenar utan ristare": "Röda punkter är grupper som kan vara en okänd ristare eller verkstad, blå är grupper som liknar en känd ristare. Numren hänvisar till tabellerna nedan; grått är övriga stenar med läsbar text.",
};

// A column heading; the explanation is looked up from the heading text unless given
function Th({ children, tip }: { children: ReactNode; tip?: string }) {
  return <th className={TH}><Tip text={tip ?? (typeof children === "string" ? GLOSSARY[children] : undefined)}>{children}</Tip></th>;
}

// An R figure from the backend, with its reading guide
function Fig({ src, alt, narrow }: { src?: string; alt: string; narrow?: boolean }) {
  return <Figure src={src ? `${API_URL}${src}` : undefined} alt={alt} help={FIG_HELP[alt]} narrow={narrow} />;
}

function Method({ text, caveat }: { text?: string; caveat?: string }) {
  if (!text) return null;
  return (
    <details className="text-xs text-slate-600 rounded-xl bg-slate-50 border border-slate-200 p-3">
      <summary className="cursor-pointer font-semibold">Metod och reservationer (för den som vill veta mer)</summary>
      <p className="mt-2">{text}</p>
      {caveat && <p className="mt-2">{caveat}</p>}
    </details>
  );
}

interface Section {
  key: Tab; question: string; why: string; headline: { value: string; label: string }; answer: string; short: string;
  confidence: Level; confidence_text: string; interpretation: string[]; not_saying: string[];
}

const PATTERN_TOPICS: Record<string, string[]> = {
  geography: ["Geografi"], attribution: ["Attribuering"], text: ["Språk"], clusters: ["Stil och innehåll"],
  chronology: ["Datering"], network: ["Släkt och formler"], anonymous: ["Okända ristare"], change: ["Förändring", "Regional skillnad", "Samband"],
};
const patternsFor = (patterns: Pattern[], key: string) => patterns.filter(p => (PATTERN_TOPICS[key] ?? []).includes(p.topic));

const TOPIC: Record<string, string> = {
  attribution: "Vem ristade?", anonymous: "Okända ristare", change: "Förändring", chronology: "Datering",
  geography: "Geografi", text: "Stavning och dialekt", clusters: "Grupper av stenar", network: "Formler och släkt",
  words: "Ordförrådet",
};

// The answer first: question, why it matters, the key number, the answer, a suggested interpretation and its limits
function SectionIntro({ section, patterns = [] }: { section?: Section; patterns?: Pattern[] }) {
  if (!section) return null;
  const tests = patternsFor(patterns, section.key);
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">{TOPIC[section.key]}</div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-900">{section.question}</h3>
          <p className="text-slate-600 mt-1">{section.why}</p>
        </div>
        <Confidence level={section.confidence} text={section.confidence_text} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-4">
        <div className="rounded-2xl bg-slate-900 text-white p-5 flex flex-col justify-center">
          <div className="text-4xl font-bold tracking-tight">{section.headline.value}</div>
          <div className="text-sm text-white/80 mt-1 leading-snug">{section.headline.label}</div>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Svaret i korthet</div>
          <p className="text-slate-800 leading-relaxed">{section.answer}</p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-2">Förslag till tolkning</h4>
          <ul className="space-y-2 text-sm text-slate-700 list-disc pl-5">{section.interpretation.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
        <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-2">Det här säger resultatet inte</h4>
          <ul className="space-y-2 text-sm text-slate-600 list-disc pl-5">{section.not_saying.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
      </div>
      {tests.length > 0 && (
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-1">Statistiska test i den här delen</h4>
          <p className="text-xs text-slate-500 mb-3">
            {tests.filter(t => t.significance?.significant).length} av {tests.length} resultat är statistiskt signifikanta
            (<Tip text={GLOSSARY["Statistiskt signifikant"]}>vad betyder det?</Tip>).
          </p>
          <ul className="space-y-2 text-sm">
            {tests.map((t, i) => (
              <li key={i} className="flex flex-col sm:flex-row sm:items-start gap-2">
                <div className="flex flex-wrap gap-1.5 shrink-0"><SigBadge sig={t.significance} /><PatternBadges pt={t} /></div>
                <div className="min-w-0"><PatternBody pt={t} /></div>
              </li>
            ))}
          </ul>
        </div>
      )}
      <h4 className="font-bold text-slate-900 pt-2">Figurer och siffror</h4>
    </div>
  );
}

// The adjusted share over time as a small line (0–100 %, the same scale in every row)
function Spark({ curve }: { curve?: { year: number; share: number }[] }) {
  if (!curve || curve.length < 2) return null;
  const W = 96, H = 30, x0 = curve[0].year, x1 = curve[curve.length - 1].year;
  const pts = curve.map(p => [((p.year - x0) / (x1 - x0 || 1)) * (W - 6) + 3, H - 3 - p.share * (H - 6)]);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const last = pts[pts.length - 1];
  const label = `Justerad andel från ${pc(curve[0].share)} (${x0}) till ${pc(curve[curve.length - 1].share)} (${x1})`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} className="shrink-0">
      <title>{label}</title>
      <line x1="3" x2={W - 3} y1={H - 3} y2={H - 3} stroke="#e2e8f0" strokeWidth="1" />
      <line x1="3" x2={W - 3} y1="3" y2="3" stroke="#f1f5f9" strokeWidth="1" />
      <path d={d} fill="none" stroke="#2a78d6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={pts[0][0]} cy={pts[0][1]} r="2.5" fill="#2a78d6" />
      <circle cx={last[0]} cy={last[1]} r="2.5" fill="#2a78d6" />
    </svg>
  );
}

// Kept for the rest of the visit, so that returning to the page is instant; the results are refetched only when the
// corpus version (fingerprint) changes
const memo: { status?: Status; data?: Corpus; fingerprint?: string } = {};

export default function StatistikPage() {
  const [status, setStatus] = useState<Status | null>(memo.status ?? null);
  const [data, setData] = useState<Corpus | null>(memo.data ?? null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [glossaryOpen, setGlossaryOpen] = useState(false);

  const [tick, setTick] = useState(0);

  // Loads the status and, when the corpus analyses are ready, their results; tick reloads
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/r/status`).then(r => r.json()).then(async (st: Status) => {
      if (cancelled) return;
      setStatus(st);
      memo.status = st;
      if (st.corpus?.ready && !(memo.data && memo.fingerprint === st.corpus.fingerprint)) {
        const res = await fetch(`${API_URL}/api/r/corpus`);
        if (res.ok && !cancelled) {
          const d = await res.json();
          memo.data = d;
          memo.fingerprint = st.corpus.fingerprint;
          setData(d);
        }
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
      <div className="space-y-3">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">Statistik (R)</h2>
        <p className="text-slate-700 text-[16px] leading-relaxed max-w-3xl">
          Här har alla {c?.n_stones ? c.n_stones.toLocaleString("sv-SE") : "svenska"} vikingatida runstenar i Rundata analyserats
          statistiskt för att hitta mönster som är svåra att se sten för sten: vem som ristade, när och var stenarna restes och
          hur språk, skrift och tro förändrades. Varje del besvarar en fråga – först svaret i korthet, sedan ett förslag till
          tolkning och vad resultatet <em>inte</em> säger. Resultaten är förslag för forskare att pröva, inte färdiga slutsatser.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <details className="group/how rounded-2xl border border-slate-200 bg-white/70 text-sm max-w-3xl">
            <summary className="cursor-pointer list-none px-4 py-2 font-semibold text-slate-800">Så läser du sidan</summary>
            <ul className="px-6 pb-4 space-y-1.5 list-disc text-slate-700">
              <li>Välj en fråga i korten nedan. <strong>Översikten</strong> sammanfattar och tolkar alla frågor på en gång.</li>
              <li>Märkningen <strong>säkert</strong>, <strong>troligt</strong> och <strong>osäkert</strong> visar hur väl resultatet håller – håll muspekaren över märket för en förklaring.</li>
              <li>Ord med prickad understrykning förklaras när du håller muspekaren över dem (eller trycker på dem). Alla förklaringar finns också i ordlistan.</li>
              <li>Klicka på en figur för att förstora den; under varje figur står hur den ska läsas.</li>
              <li>&quot;Signifikant&quot; betyder att resultatet håller även när man räknar med att många saker prövats samtidigt (justerat p-värde, q, under 0,05).</li>
            </ul>
          </details>
          <button type="button" onClick={() => setGlossaryOpen(true)}
            className="px-4 py-2 rounded-2xl border border-slate-200 bg-white/70 text-sm font-semibold text-slate-800 hover:border-[#b7410e]/40">
            Ordlista
          </button>
          {glossaryOpen && <Glossary onClose={() => setGlossaryOpen(false)} />}
        </div>
      </div>

      {error && <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-3 text-sm text-red-800">{error}</div>}

      {(!data || c?.running || (c && !c.ready)) && (
        <div className="liquid-glass-island rounded-[24px] p-5 flex flex-wrap items-center gap-4">
          {!status ? <span className="text-slate-500">Hämtar läget …</span> : !status.r.available ? (
            <div className="text-sm text-amber-900">
              <strong>R är inte tillgängligt på servern.</strong> {status.r.note}
              {status.r.missing.length > 0 && <div className="text-xs mt-1">Saknas: {status.r.missing.join(", ")}</div>}
            </div>
          ) : (
            <>
              <div className="text-sm text-slate-700">
                {c?.running ? "Analyserna räknas just nu – det tar några minuter." : "Analyserna behöver räknas om för den här versionen av data."}
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
            </>
          )}
        </div>
      )}

      {data && (
        <>
          <nav aria-label="Frågor" className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
            {[{ key: "overview" as Tab, question: "Vad säger statistiken sammantaget?", confidence: null as Level | null },
              ...(data.sections ?? []).map(x => ({ key: x.key, question: x.question, confidence: x.confidence as Level | null }))].map(card => (
              <button key={card.key} type="button" onClick={() => setTab(card.key)} aria-pressed={tab === card.key}
                className={`text-left rounded-2xl border p-3 transition-colors ${tab === card.key
                  ? "bg-slate-900 border-slate-900 text-white shadow-lg" : "bg-white/80 border-slate-200 text-slate-800 hover:border-[#b7410e]/40"}`}>
                <div className={`text-[10px] font-bold uppercase tracking-wider ${tab === card.key ? "text-[#f0a37f]" : "text-[#b7410e]"}`}>
                  {card.key === "overview" ? "Översikt" : TOPIC[card.key]}
                </div>
                <div className="text-sm font-semibold leading-snug mt-0.5">{card.question}</div>
                {card.confidence && (
                  <div className={`text-[10px] mt-1.5 ${tab === card.key ? "text-white/70" : "text-slate-500"}`}>{card.confidence}</div>
                )}
              </button>
            ))}
          </nav>
          <div className="liquid-glass-island rounded-[32px] p-5 md:p-7 space-y-5">
            {tab === "overview" && <Overview data={data} onOpen={setTab} />}
            {tab === "geography" && <Geography data={data} />}
            {tab === "clusters" && <Clusters data={data} />}
            {tab === "text" && <TextTab data={data} />}
            {tab === "attribution" && <Attribution data={data} />}
            {tab === "anonymous" && <Anonymous data={data} />}
            {tab === "chronology" && <Chronology data={data} />}
            {tab === "change" && <Change data={data} />}
            {tab === "network" && <Network data={data} />}
            {tab === "words" && <Words data={data} />}
          </div>
          {status?.r.available && (
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 px-1">
              <span>
                Beräknat i {status.r.version} på {c?.n_stones} runstenar (version <span translate="no">{c?.fingerprint}</span>
                {c?.computed_at ? `, ${new Date(c.computed_at).toLocaleString("sv-SE")}` : ""}). Samma analyser används i{" "}
                <Link href="/stenanalys" className="text-[#b7410e] hover:underline">stenanalysen</Link> och ställs mot forskningen i{" "}
                <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>.
              </span>
              <a href={`${API_URL}/api/r/package`} className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white font-bold text-slate-700 hover:bg-slate-50">
                Ladda ner R-skript, data och resultat
              </a>
            </div>
          )}
        </>
      )}
    </div>
  );
}

const STATUS_STYLE: Record<string, string> = {
  "bekräftar": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "mönster att pröva": "bg-amber-50 text-amber-900 border-amber-200",
  "begränsning": "bg-slate-100 text-slate-700 border-slate-300", "svagt": "bg-slate-100 text-slate-700 border-slate-300",
  "svag effekt": "bg-slate-100 text-slate-700 border-slate-300", "indikation": "bg-slate-100 text-slate-700 border-slate-300",
};

const sectionOf = (data: Corpus, key: Tab) => (data.sections ?? []).find(x => x.key === key);

// The statistically significant results, so that they stand out from the descriptive ones
function SignificantBox({ patterns, onOpen }: { patterns: Pattern[]; onOpen: (t: Tab) => void }) {
  const tested = patterns.filter(p => p.significance && p.significance.significant !== null);
  const sig = tested.filter(p => p.significance?.significant);
  const untested = patterns.filter(p => p.significance && p.significance.significant === null);
  if (!patterns.some(p => p.significance)) return null;
  const sectionOfTopic = (topic: string) => (Object.entries(PATTERN_TOPICS).find(([, ts]) => ts.includes(topic))?.[0] ?? "overview") as Tab;
  const topics = Array.from(new Set(sig.map(p => p.topic)));
  return (
    <section className="rounded-3xl border border-emerald-200 bg-emerald-50/60 p-6 md:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">Statistiskt signifikant</div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-900">Upptäckter som klarar signifikanstestet</h3>
        </div>
        <div className="text-sm text-slate-700"><span className="text-3xl font-bold text-emerald-800">{sig.length}</span> av {tested.length} prövade resultat</div>
      </div>
      <p className="text-sm text-slate-700 mt-2 max-w-4xl">
        Ett resultat är <strong>statistiskt signifikant</strong> när p-värdet – eller q, som tar hänsyn till att många saker prövats
        samtidigt – är under 0,05: ett så tydligt mönster vore ovanligt om det inte fanns något verkligt samband. Det är inte sannolikheten att mönstret är verkligt, och det säger inte att tolkningen av det är rätt.
        {untested.length > 0 && ` ${untested.length} resultat är inte prövade med signifikanstest (t.ex. attribueringsmodellen, som i stället prövats med korsvalidering).`}
      </p>
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {topics.map(topic => (
          <div key={topic} className="rounded-2xl bg-white border border-emerald-100 p-4">
            <button type="button" onClick={() => onOpen(sectionOfTopic(topic))} className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e] hover:underline">
              {topic} →
            </button>
            <ul className="mt-2 space-y-2 text-sm">
              {sig.filter(p => p.topic === topic).map((p, i) => (
                <li key={i} className="flex flex-col gap-1">
                  <div className="flex flex-wrap gap-1.5"><SigBadge sig={p.significance} /><PatternBadges pt={p} /></div>
                  <span className="text-slate-700">{p.text}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

function Overview({ data, onOpen }: { data: Corpus; onOpen: (t: Tab) => void }) {
  const s = data.findings_summary;
  const top = data.findings.filter(f => f.verdict !== "stämmer").slice(0, 25);
  const groups: [string, string, string[]][] = [
    ["Stämmer med det forskningen redan utgår från", "Ett tecken på att metoderna fungerar.", ["bekräftar"]],
    ["Nya mönster att pröva", "Mönster som appen inte kan förklara med det den känner till och som håller i båda halvorna av korpusen – kanske ny kunskap, kanske redan beskrivet i litteratur som appen inte har.", ["mönster att pröva"]],
    ["Indikationer", "Mönster som syns i hela korpusen men inte håller i alla kontroller eller i båda halvorna – idéer att pröva, med förbehåll.", ["indikation"]],
    ["Begränsningar", "Cirkulära jämförelser och resultat som visar gränserna för data och metod.", ["begränsning", "svagt", "svag effekt"]],
  ];
  return (
    <div className="space-y-8">
      {data.overview && (
        <section className="rounded-3xl bg-white border border-slate-200 p-6 md:p-8">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">Helhetsbilden</div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-900 mb-4">Vad statistiken säger sammantaget</h3>
          <div className="space-y-4 text-slate-700 leading-relaxed max-w-4xl">
            {data.overview.paragraphs.map((t, i) => <p key={i}><Md text={t} /></p>)}
          </div>
        </section>
      )}

      <SignificantBox patterns={data.patterns} onOpen={onOpen} />

      <section>
        <h3 className="text-xl font-bold text-slate-900 mb-1">Frågorna i korthet</h3>
        <p className="text-sm text-slate-600 mb-4">Svaret, nyckeltalet och den viktigaste tolkningen för varje fråga. Klicka för att läsa mer.</p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {(data.sections ?? []).map(x => (
            <button key={x.key} type="button" onClick={() => onOpen(x.key)}
              className="text-left rounded-2xl bg-white border border-slate-200 p-5 hover:border-[#b7410e]/40 hover:shadow-md transition-shadow flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">{TOPIC[x.key]}</div>
                  <div className="font-bold text-slate-900 leading-snug">{x.question}</div>
                </div>
                <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${LEVEL_STYLE[x.confidence]}`}>{x.confidence}</span>
              </div>
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold tracking-tight text-slate-900">{x.headline.value}</span>
                <span className="text-xs text-slate-500 leading-snug">{x.headline.label}</span>
              </div>
              <p className="text-sm text-slate-800">{x.short}</p>
              {x.interpretation[0] && <p className="text-sm text-slate-600"><span className="font-semibold text-slate-700">Tolkning: </span>{x.interpretation[0]}</p>}
              {(() => {
                const ts = patternsFor(data.patterns, x.key), k = ts.filter(t => t.significance?.significant).length;
                return ts.length > 0 ? (
                  <span className={`text-xs font-semibold ${k ? "text-emerald-800" : "text-slate-500"}`}>
                    {k ? `✓ ${k} av ${ts.length} resultat statistiskt signifikanta` : `Inget av ${ts.length} resultat statistiskt signifikant`}
                  </span>
                ) : null;
              })()}
              <span className="text-xs font-bold text-[#b7410e] mt-auto">Läs mer →</span>
            </button>
          ))}
        </div>
      </section>

      {data.overview && data.overview.next_steps.length > 0 && (
        <section className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900 mb-2">Förslag på nästa steg för forskningen</h3>
          <ol className="list-decimal pl-5 space-y-1.5 text-sm text-slate-700">
            {data.overview.next_steps.map((t, i) => <li key={i}>{t}</li>)}
          </ol>
        </section>
      )}

      <section>
        <h3 className="text-xl font-bold text-slate-900 mb-1">Alla mönster i korpusen</h3>
        <p className="text-sm text-slate-600 mb-4">De enskilda resultaten bakom sammanfattningen, sorterade efter vad de betyder för forskningen.</p>
        <div className="space-y-5">
          {groups.map(([title, help, statuses]) => {
            const items = data.patterns.filter(pt => statuses.includes(pt.status));
            if (!items.length) return null;
            return (
              <div key={title}>
                <h4 className="font-semibold text-slate-900">{title} <span className="text-slate-400 font-normal">({items.length})</span></h4>
                <p className="text-xs text-slate-500 mb-2">{help}</p>
                <ul className="space-y-2 text-sm">
                  {items.map((pt, i) => (
                    <li key={i} className="flex gap-3 rounded-xl bg-white border border-slate-200 p-3">
                      <div className="flex flex-col gap-1 shrink-0">
                        <span className={`h-fit w-fit px-2 py-0.5 rounded-lg border text-[11px] font-bold ${STATUS_STYLE[pt.status] ?? ""}`}><Tip text={GLOSSARY[pt.status]}>{pt.status}</Tip></span>
                        <SigBadge sig={pt.significance} compact />
                        <PatternBadges pt={pt} />
                      </div>
                      <div className="min-w-0">
                        <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">{pt.topic}</div>
                        <PatternBody pt={pt} />
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
        <div className="mt-3"><DocsNote anchor="1l-begränsningar-och-tolkning-av-mönstren">Hur mönstren ska tolkas och vilka reservationer som gäller står i avsnitt 1l.</DocsNote></div>
      </section>

      <Details title={`Fynd per sten (${s.n})`}>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[["Fynd per sten", s.n], ["Nya mot Rundata", s.new], ["Motsäger Rundata", s.contradicts],
            ["Finns redan i nyare källa", s.already_known], ["Nya även mot Runor 2020", s.still_new]].map(([l, v]) => (
            <div key={l as string} className="rounded-2xl bg-white border border-slate-200 p-4">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500"><Tip text={GLOSSARY[l as string]}>{l}</Tip></div>
              <div className="text-2xl font-bold text-slate-900">{v}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500">
          De starkaste nya och motsägande resultaten för enskilda stenar. &quot;Nyare källor&quot; visar avstämningen mot Runor 2020 och
          Wikidata (görs i <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>, där varje fynd också
          får en tolkning). Ett förslag är en hypotes för en runolog att pröva, inte en attribuering.
        </p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Sten</Th><Th>Metod</Th><Th>Mot Rundata</Th><Th>Resultat</Th>
              <Th>Rundata</Th><Th>Nyare källor</Th><Th>Bedömning</Th></tr></thead>
            <tbody>
              {top.map(f => (
                <tr key={`${f.signum}|${f.method}`} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold"><Link href={`/inskrifter/${encodeURIComponent(f.signum)}`} className="hover:underline">{f.signum}</Link>
                    <div className="text-[11px] text-slate-500 font-normal" translate="no">{f.place}</div></td>
                  <td className="p-2 text-xs">{f.method}</td>
                  <td className="p-2 text-xs font-bold">{f.verdict}</td>
                  <td className="p-2 text-xs max-w-[280px]">{f.ours}</td>
                  <td className="p-2 text-xs">{f.existing}</td>
                  <td className="p-2 text-xs" title={f.crosscheck?.runor?.text}>{f.crosscheck?.status ?? "–"}</td>
                  <td className="p-2 text-xs font-semibold">{f.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table></ExportTable>
        </div>
      </Details>
    </div>
  );
}

function Geography({ data }: { data: Corpus }) {
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

const pText = (p: number | null | undefined) => p == null ? "–" : p < 0.001 ? "< 0,001" : d2(p, 3);

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

function Clusters({ data }: { data: Corpus }) {
  const c = data.clusters, f = data.figure_urls.clusters || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "clusters")} patterns={data.patterns} />
      <p className="text-sm text-slate-600">
        {c.n_stones} stenar med tillräckligt många drag ingår. Strukturen är {c.structure} (<Tip text={GLOSSARY["silhuettbredd"]}>silhuettbredd</Tip>{" "}
        {d2(c.best_silhouette)}), och grupperna sammanfaller inte med ristarna (<Tip text={GLOSSARY["justerat Rand-index"]}>justerat Rand-index</Tip> {d2(c.carvers.ari)}).
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.mca} alt="MCA" /><Fig src={f.variables} alt="Kategorier i MCA" />
        <Fig src={f.silhouette} alt="Silhuettbredd" /><Fig src={f.carvers} alt="Ristare per grupp" />
      </div>
      <Details title="Grupperna och vad som utmärker dem" open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Grupp</Th><Th>Stenar</Th><Th>Stabilitet</Th><Th>Utmärks av</Th><Th>Stilgrupper</Th><Th>Landskap</Th></tr></thead>
            <tbody>{c.clusters.map(k => (
              <tr key={k.cluster} className="border-t border-slate-900/5 align-top">
                <td className="p-2 font-semibold">{k.cluster}</td><td className="p-2">{k.n}</td><td className="p-2">{d2(k.stability)}</td>
                <td className="p-2 text-xs">{k.features.slice(0, 4).map(x => `${x.level} (${pc(x.share_in_cluster)} mot ${pc(x.share_overall)})`).join("; ")}</td>
                <td className="p-2 text-xs">{k.styles.map(x => `${x.style} ${x.n}`).join(", ")}</td>
                <td className="p-2 text-xs">{k.provinces.map(x => `${x.province} ${x.n}`).join(", ")}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={c.method} />
    </>
  );
}

function TextTab({ data }: { data: Corpus }) {
  const t = data.text, dl = data.dialect, ft = data.figure_urls.text || {}, fd = data.figure_urls.dialect || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "text")} patterns={data.patterns} />
      <h4 className="font-semibold text-slate-900">Ristarnas stavning och formler</h4>
      <p className="text-sm text-slate-600">
        Hur tydligt formlerna skiljer ristarna åt (<Tip text={GLOSSARY["Cramérs V"]}>Cramérs V</Tip>, 0–1):{" "}
        {t.formulas.tests.map(x => `${x.label.toLowerCase()} ${d2(x.cramers_v)}`).join(", ")}.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={ft.formulas} alt="Formler per ristare" /><Fig src={ft.lemmas} alt="Stavning per ord" /></div>
      <h4 className="font-semibold text-slate-900 pt-2">Stavning och dialekter</h4>
      <p className="text-sm text-slate-600">
        Stavningsavstånd mot geografiskt avstånd mellan {dl.n_districts} härader: <Tip text={GLOSSARY["Mantel r"]}>Mantel r</Tip>{" "}
        {d2(dl.mantel.r)}, <Tip text={GLOSSARY["p"]}>p</Tip> {d2(dl.mantel.p, 3)}.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={fd.distance} alt="Stavning mot avstånd" /><Fig src={fd.groups} alt="Härader med likartad stavning" />
        <Fig src={fd.efter} alt="Stavning av efter" /><Fig src={fd.sten} alt="Diftongen i sten" />
      </div>
      <Details title="Typiska stavningar i häradsgrupperna">
        <ul className="text-sm space-y-1">
          {dl.group_forms.map(g => (
            <li key={g.group}><strong>Grupp {g.group}</strong> ({dl.groups.find(x => x.group === g.group)?.provinces}):{" "}
              {g.forms.map(x => `${x.lemma} = ${x.form} (${pc(x.share_in_group)} mot ${pc(x.share_all)})`).join("; ")}</li>
          ))}
        </ul>
      </Details>
      <Method text={t.method} />
      <Method text={dl.method} caveat={dl.caveat} />
    </>
  );
}

function Attribution({ data }: { data: Corpus }) {
  const a = data.attribution, f = data.figure_urls.attribution || {};
  const all = a.ablation.find(x => x.features === "Alla");
  return (
    <>
      <SectionIntro section={sectionOf(data, "attribution")} patterns={data.patterns} />
      <div className="rounded-2xl bg-white border border-slate-200 p-5">
        <h4 className="font-semibold text-slate-900 mb-3">Hur ofta modellen väljer rätt ristare</h4>
        <div className="space-y-2">
          {[["Modellen, alla belägg", all?.accuracy], ...a.ablation.filter(x => x.features !== "Alla").map(x => [`Bara ${x.features.toLowerCase()}`, x.accuracy] as [string, number]),
            ["Gissa alltid den vanligaste ristaren", a.majority_baseline]].map(([label, v]) => (
            <div key={label as string} className="grid grid-cols-[minmax(0,220px)_1fr_48px] items-center gap-3 text-sm">
              <span className="text-slate-700 truncate">{label}</span>
              <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
                <div className={`h-full rounded-full ${label === "Gissa alltid den vanligaste ristaren" ? "bg-slate-400" : "bg-[#2a78d6]"}`}
                  style={{ width: `${Math.round((v as number ?? 0) * 100)}%` }} />
              </div>
              <span className="text-right font-semibold text-slate-900">{pc(v as number)}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-3">Andel stenar med känd ristare där modellen, utan att ha sett stenen, gav rätt ristare som förstaval.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.ablation} alt="Delmodeller" /><Fig src={f.calibration} alt="Kalibrering" />
        <Fig src={f.importance} alt="Variabler" /><Fig src={f.confusion} alt="Förväxlingar" />
      </div>
      {a.grouped_cv && (
        <Details title="Fungerar modellen på platser den inte har sett?">
          <p className="text-sm text-slate-600">
            Vid vanlig korsvalidering kan stenar från samma plats finnas både i tränings- och testdata. Här hålls hela socknar
            respektive härader utanför träningen; en ristare som bara finns i det utelämnade området kan då inte föreslås och räknas som fel.
          </p>
          <div className="overflow-x-auto">
            <ExportTable><table className="w-full text-sm">
              <thead><tr><Th>Belägg</Th><Th>Slumpvis</Th>
                {Object.entries(a.grouped_cv).map(([k, g]) => <Th key={k} tip={GLOSSARY["Ny socken/härad"]}>Ny {k.toLowerCase()} ({g.n_groups} grupper)</Th>)}</tr></thead>
              <tbody>{a.ablation.map(x => (
                <tr key={x.features} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{x.features}</td><td className="p-2">{pc(x.accuracy)}</td>
                  {Object.entries(a.grouped_cv!).map(([k, g]) => <td key={k} className="p-2">{pc(g.ablation.find(y => y.features === x.features)?.accuracy ?? undefined)}</td>)}</tr>
              ))}</tbody>
            </table></ExportTable>
          </div>
        </Details>
      )}
      <Details title="Hur säkra sannolikheterna är">
        <ul className="text-sm space-y-1 text-slate-700">
          {a.calibration.reliability.map(r => (
            <li key={r.threshold}>När modellen anger minst {Math.round(r.threshold * 100)} % sannolikhet är förstavalet rätt i <strong>{pc(r.accuracy)}</strong> av fallen ({r.n} stenar).</li>
          ))}
        </ul>
      </Details>
      <Details title="Ristarna en och en">
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ristare</Th><Th>Säkra stenar</Th><Th>Hittas (recall)</Th><Th>Rätt när föreslagen (precision)</Th></tr></thead>
            <tbody>{a.per_carver.map(r => (
              <tr key={r.carver} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td>
                <td className="p-2">{pc(r.recall)}</td><td className="p-2">{pc(r.precision)}</td></tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={a.method} caveat={a.caveat} />
    </>
  );
}

function Chronology({ data }: { data: Corpus }) {
  const ch = data.chronology, f = data.figure_urls.chronology || {}, v = ch.validation;
  return (
    <>
      <SectionIntro section={sectionOf(data, "chronology")} patterns={data.patterns} />
      <p className="text-sm text-slate-600">
        Seriationen ordnar stenarna efter vilka språkdrag, formler och innehåll de delar (<Tip text={GLOSSARY["rho"]}>rho</Tip> mot stilgrupperna{" "}
        {d2(v.rho)}; {d2(v.partial_rho)} när hänsyn tas till hur nordligt stenarna står). Medelfel för ett årtal {v.mae_loo_years} år, mot {v.mae_naive_years} år utan modell.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.validation} alt="Seriation mot Gräslund" /><Fig src={f.diagram} alt="Seriationsdiagram" /><Fig src={f.estimates} alt="Skattad tid" />
      </div>
      <Details title="Vad skiljer stenarna åt i hela landet?">
        <p className="text-sm text-slate-600">
          Korrespondensanalysens tre huvudriktningar för hela korpusen och vad var och en följer – tid, geografi eller ristare. Gult är ett mönster
          som inget av dem förklarar.
        </p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Dimension</Th><Th>Inerti</Th><Th>Tid (rho)</Th><Th>Latitud (rho)</Th>
              <Th>Landskap (eta²)</Th><Th>Ristare (eta²)</Th><Th>Förklaras av</Th><Th>Skiljer</Th></tr></thead>
            <tbody>{ch.corpus_dimensions.map(x => (
              <tr key={x.dim} className={`border-t border-slate-900/5 align-top ${x.unexplained ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{x.dim}</td><td className="p-2">{d2(x.inertia_pct, 1)} %</td><td className="p-2">{d2(x.rho_time)}</td>
                <td className="p-2">{d2(x.rho_lat)}</td><td className="p-2">{d2(x.eta2_province)}</td><td className="p-2">{d2(x.eta2_carver)}</td>
                <td className="p-2 text-xs font-semibold">{x.unexplained ? "oförklarat mönster" : asList(x.explained_by).join(", ")}</td>
                <td className="p-2 text-xs">{asList(x.positive).slice(0, 3).join(", ")} ↔ {asList(x.negative).slice(0, 3).join(", ")}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={ch.method} />
    </>
  );
}

function Network({ data }: { data: Corpus }) {
  const n = data.network, f = data.figure_urls.network || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "network")} patterns={data.patterns} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.network} alt="Formelnätverk" /><Fig src={f.kinship} alt="Släktrelationer" /></div>
      <Details title="Orden i varje formelgrupp" open>
        <ul className="text-sm space-y-1">
          {n.communities.map(c => <li key={c.community}><strong>Grupp {c.community}</strong> ({c.size} ord): <span translate="no">{c.words.map(w => w.word).join(", ")}</span></li>)}
        </ul>
      </Details>
      <Details title="Släktrelationer över tid och i kristna inskrifter">
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Relation</Th><Th>Inskrifter</Th><Th>Före ca 1050</Th><Th>Efter ca 1050</Th>
              <Th>q (tid)</Th><Th>Kristna</Th><Th>Övriga</Th><Th>q (kristen)</Th></tr></thead>
            <tbody>{n.kinship.map(k => (
              <tr key={k.relation} className={`border-t border-slate-900/5 ${k.q_period < 0.05 || k.q_christian < 0.05 ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{k.relation}</td><td className="p-2">{k.n}</td><td className="p-2">{pc(k.early)}</td><td className="p-2">{pc(k.late)}</td>
                <td className="p-2">{d2(k.q_period, 3)}</td><td className="p-2">{pc(k.share_christian)}</td><td className="p-2">{pc(k.share_other)}</td><td className="p-2">{d2(k.q_christian, 3)}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500">Gult: signifikant skillnad (q under 0,05) över tid eller mellan kristna och övriga inskrifter.</p>
      </Details>
      <Method text={n.method} />
    </>
  );
}

function Words({ data }: { data: Corpus }) {
  const w = data.words;
  if (!w) return <p className="text-sm text-slate-600">Ordförrådsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const epochs = w.time[0]?.shares.map(s => s.epoch) ?? [];
  const holds = w.region.filter(r => r.holds);
  return (
    <>
      <SectionIntro section={sectionOf(data, "words")} patterns={data.patterns} />
      <p className="text-sm text-slate-600 max-w-3xl">
        Orden är desamma som i <a href="/phonetics#ordmoln" className="underline">ordmolnet</a> på Språk &amp; Fonetik,
        men här prövade: är ordet vanligare i ett landskap än i resten av landet när tiden och textlängden räknats
        bort, och ändras det över tid? Ristaren räknas som slumpeffekt, så en flitig ristares vanor inte blir
        landskapets.
      </p>
      <Details title={`Orden som skiljer landskapen åt (${holds.length} håller i båda sockenhalvorna)`} open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ord</Th><Th>Landskap</Th><Th>Andel där</Th><Th>Andel i övriga</Th><Th>q</Th><Th>Håller i halvorna</Th></tr></thead>
            <tbody>{w.region.map(r => (
              <tr key={`${r.word}|${r.province}`} className={`border-t border-slate-900/5 ${r.holds ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold" translate="no">{r.word}</td>
                <td className="p-2">{r.province}</td>
                <td className="p-2">{pc(r.rate_in)} ({r.k_in} av {r.n_in})</td>
                <td className="p-2">{pc(r.rate_out)}</td>
                <td className="p-2">{qText(r.q)}</td>
                <td className="p-2">{r.holds ? "✓" : "–"}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Gult: signalen har samma riktning och p under 0,05 i båda sockenhalvorna. Riktningen (vanligare eller
          ovanligare än riket) syns i andelarna; q är det tidsjusterade testets justerade p-värde över alla {w.n_region_tests} prov.
        </p>
      </Details>
      <Details title={`Orden som ändras över tid (${w.time.length} av ${w.n_time_tests})`}>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ord</Th><Th>Riktning</Th><Th>q</Th>{epochs.map(e => <Th key={e}>{e}</Th>)}</tr></thead>
            <tbody>{w.time.map(t => (
              <tr key={t.word} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold" translate="no">{t.word}</td>
                <td className="p-2">{t.slope > 0 ? "ökar" : "minskar"}</td>
                <td className="p-2">{qText(t.q)}</td>
                {t.shares.map(s => <td key={s.epoch} className="p-2">{s.n ? pc(s.k / s.n) : "–"}</td>)}
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Andelen stenar med ordet per epok (tiden ur stilgrupperna, därför ungefär 980–1130). Riktningen kommer ur
          modellens tidslutning, justerad för landskap och textlängd.
        </p>
      </Details>
      <Details title="Vilka landskap väljer ord mest lika? (korrespondensanalys)" open>
        <div className="h-[420px]">
          <PlotlyGraph
            data={[
              { type: "scatter", mode: "text", x: w.ca.words.map(x => x.x), y: w.ca.words.map(x => x.y),
                text: w.ca.words.map(x => x.w), name: "Ord", textfont: { size: 10, color: "#94a3b8" },
                hovertemplate: "%{text}<extra>ord</extra>" },
              { type: "scatter", mode: "markers+text", x: w.ca.provinces.map(x => x.x), y: w.ca.provinces.map(x => x.y),
                text: w.ca.provinces.map(x => x.code), name: "Landskap", textposition: "top center",
                marker: { color: "#b7410e", size: 10, line: { color: "#ffffff", width: 1 } },
                textfont: { size: 12, color: "#1f2937" },
                hovertemplate: "%{text}: %{customdata} stenar<extra>landskap</extra>",
                customdata: w.ca.provinces.map(x => x.n) },
            ]}
            layout={{
              autosize: true, margin: { l: 40, r: 10, t: 10, b: 40 },
              xaxis: { title: `Dimension 1 (${Math.round(100 * (w.ca.inertia[0] ?? 0))} % av variationen)`, zeroline: true, zerolinecolor: "rgba(15,23,42,0.1)" },
              yaxis: { title: `Dimension 2 (${Math.round(100 * (w.ca.inertia[1] ?? 0))} %)`, zeroline: true, zerolinecolor: "rgba(15,23,42,0.1)" },
              legend: { orientation: "h" }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
            }}
          />
        </div>
        <p className="text-xs text-slate-500">
          Landskap som står nära varandra har liknande ordprofiler; orden (grå) drar mot de landskap där de är
          vanligast. Mest lika ordval: {w.neighbors.map(n => `${n.a}–${n.b}`).join(", ")}.
        </p>
      </Details>
      <Method text={w.method} />
    </>
  );
}

const SHAPE: Record<string, string> = {
  rises: "ökar", falls: "minskar", peak: "vanligast omkring", trough: "ovanligast omkring", flat: "oförändrad",
};
const qText = (q: number | null | undefined) => q == null ? "–" : q < 0.001 ? "< 0,001" : d2(q, 3);

function Change({ data }: { data: Corpus }) {
  const c = data.change, f = data.figure_urls.change || {};
  if (!c) return <p className="text-sm text-slate-600">Förändringsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const crossing = c.features.filter(x => (x.provinces?.rows || []).filter(r => r.cross_year).length >= 2);
  return (
    <>
      <SectionIntro section={sectionOf(data, "change")} patterns={data.patterns} />
      <div className="rounded-2xl bg-white border border-slate-200 p-4">
        <h4 className="font-semibold text-slate-900">Varje drag över tid</h4>
        <p className="text-xs text-slate-500 mb-3">
          Linjen är andelen stenar med draget från omkring år 1000 till 1115, med plats och ristare konstanta (samma skala 0–100 % på varje rad).
          Gulmarkerade rader är signifikanta (<Tip text={GLOSSARY["q"]}>q</Tip> under 0,05). Tiden kommer från stilgrupperna ({c.n_dated} daterade stenar),
          och varje resultat är omräknat {c.draws} gånger med årtal inom stilgruppens intervall.
        </p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Drag</Th><Th>Förlopp</Th><Th>Justerad andel</Th><Th>q</Th><Th>Omräkningar signifikanta</Th>
              <Th>Vanligast i</Th><Th>Ovanligast i</Th><Th>Daterade stenar</Th></tr></thead>
            <tbody>{c.features.map(x => {
              const t = x.time, sig = t.q != null && t.q < 0.05;
              return (
                <tr key={x.key} className={`border-t border-slate-900/5 ${sig ? "bg-amber-50" : ""}`}>
                  <td className="p-2 font-semibold">{x.label}</td>
                  <td className="p-2 text-xs">
                    <div className="flex items-center gap-2">
                      <Spark curve={t.curve} />
                      <span>{t.tested ? `${SHAPE[t.shape ?? ""] ?? ""}${t.peak_year ? ` ${t.peak_year}` : ""}` : "för få daterade stenar"}</span>
                    </div>
                  </td>
                  <td className="p-2 text-xs whitespace-nowrap">{t.tested ? `${pc(t.first)} → ${pc(t.last)}` : "–"}</td>
                  <td className="p-2">{qText(t.q)}</td>
                  <td className="p-2 text-xs">{t.draws?.n ? pc(t.draws.share_sig) : "–"}</td>
                  <td className="p-2 text-xs">{x.space && x.space.p < 0.05 ? asList(x.space.high).join(", ") : "–"}</td>
                  <td className="p-2 text-xs">{x.space && x.space.p < 0.05 ? asList(x.space.low).join(", ") : "–"}</td>
                  <td className="p-2 text-xs">{t.n}</td>
                </tr>
              );
            })}</tbody>
          </table></ExportTable>
        </div>
      </div>
      <Fig src={f.time} alt="Dragen över tid" />
      <Fig src={f.map} alt="Var dragen är vanligast" />
      <Fig src={f.provinces} alt="Landskapen omkring 1050" />
      {crossing.length > 0 && (
        <Details title="När draget blir vanligt i olika landskap" open>
          <p className="text-sm text-slate-600">Året då draget finns på hälften av stenarna, med 95 % intervall. Ett tidigare år kan betyda att förändringen började där.</p>
          <ul className="text-sm space-y-1">
            {crossing.map(x => (
              <li key={x.key}><strong>{x.label}</strong>{" "}
                (skillnad mellan landskapen i mittperioden <Tip text={GLOSSARY["q"] ?? GLOSSARY["p"]}>q</Tip> {qText(x.provinces!.q_differ ?? x.provinces!.p_differ)}, justerat för alla drag):{" "}
                {x.provinces!.rows.filter(r => r.cross_year).sort((a, b) => a.cross_year! - b.cross_year!)
                  .map(r => `${r.province} omkring ${r.cross_year} (${r.cross_lo}–${r.cross_hi})`).join(", ")}
              </li>
            ))}
          </ul>
        </Details>
      )}
      <Details title="Bro- och vägstenar och kristna drag">
        <p className="text-sm text-slate-600">Prövar tolkningen av brobyggen som kristna själagåvor: har bro- och vägstenar oftare kristna drag än andra stenar?</p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Drag</Th><Th>Brostenar</Th><Th>Andra stenar</Th>
              <Th>Oddskvot (95 % KI)</Th><Th>q</Th><Th>Daterade, med tid</Th></tr></thead>
            <tbody>{c.assoc.map(a => (
              <tr key={a.key} className={`border-t border-slate-900/5 ${a.all?.q != null && a.all.q < 0.05 ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{a.label}</td><td className="p-2">{pc(a.share_x)} av {a.n_x}</td>
                <td className="p-2">{pc(a.share_other)}</td>
                <td className="p-2">{a.all ? `${d2(a.all.or)} (${d2(a.all.lo)}–${d2(a.all.hi)})` : "–"}</td>
                <td className="p-2">{qText(a.all?.q)}</td>
                <td className="p-2 text-xs">{a.dated?.or != null ? `${d2(a.dated.or)} (${d2(a.dated.lo)}–${d2(a.dated.hi)}), p ${qText(a.dated.p)}` : "–"}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <DocsNote anchor="1h-förändring-i-tid-och-rum">Hur förändringsanalysen ska läsas och vilka reservationer som gäller står i avsnitt 1h.</DocsNote>
      <Method text={c.method} />
    </>
  );
}

function Stones({ list }: { list: string[] }) {
  return (
    <span>
      {list.slice(0, 8).map((sg, i) => (
        <span key={sg}>{i > 0 && ", "}<Link href={`/inskrifter/${encodeURIComponent(sg)}`} className="hover:underline">{sg}</Link></span>
      ))}
      {list.length > 8 && ` och ${list.length - 8} till`}
    </span>
  );
}

function Anonymous({ data }: { data: Corpus }) {
  const a = data.anonymous, f = data.figure_urls.anonymous || {};
  if (!a) return <p className="text-sm text-slate-600">Analysen av okända ristare saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const v = a.validation, cal = a.calibration;
  const cands = a.groups.filter(g => g.status === "candidate"), known = a.groups.filter(g => g.status === "known");
  return (
    <>
      <SectionIntro section={sectionOf(data, "anonymous")} patterns={data.patterns} />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[["Möjliga okända ristare", `${cands.length} grupper`], ["Liknar en känd ristare", `${known.length} grupper`],
          ["Prövat på kända ristare", `${pc(v.purity)} samma ristare`], ["Bara närliggande stenar", `${pc(v.purity_geography)} samma ristare`]].map(([l, val]) => (
          <div key={l} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500"><Tip text={GLOSSARY[l]}>{l}</Tip></div>
            <div className="text-xl font-bold text-slate-900">{val}</div>
          </div>
        ))}
      </div>
      <Fig src={f.map} alt="Grupper av stenar utan ristare" narrow />
      <Details title={`Möjliga okända ristare (${cands.length})`} open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Nr</Th><Th>Arbetsnamn</Th><Th>Stenar</Th><Th>Socknar</Th>
              <Th>Stilgrupper</Th><Th>Utmärks av (gruppen mot trakten)</Th><Th>Stabilitet</Th>
              <Th>Närmast liknande ristare i Rundata</Th></tr></thead>
            <tbody>{cands.map(g => {
              const parishes = asList(g.parishes);
              return (
                <tr key={g.id} className="border-t border-slate-900/5 align-top">
                  <td className="p-2">{g.id}</td>
                  <td className="p-2 font-semibold">{g.name}<div className="text-[11px] font-normal text-slate-500">typsten{" "}
                    <Link href={`/inskrifter/${encodeURIComponent(g.type_stone)}`} className="hover:underline">{g.type_stone}</Link></div></td>
                  <td className="p-2 text-xs">{g.n}: <Stones list={asList(g.stones)} /></td>
                  <td className="p-2 text-xs">{parishes.slice(0, 4).join(", ")}{parishes.length > 4 ? " …" : ""}</td>
                  <td className="p-2 text-xs">{(g.styles || []).map(x => `${x.style} ${x.n}`).join(", ") || "–"}</td>
                  <td className="p-2 text-xs">{(g.marks || []).map(m => `${m.feature} (${pc(m.share_group)} mot ${pc(m.share_area)})`).join("; ") || "–"}</td>
                  <td className="p-2">{pc(g.stability)}</td>
                  <td className="p-2 text-xs">{g.nearest_carver ? `${g.nearest_carver.carver} (${d2(g.nearest_carver.km, 0)} km bort, inte lika nära som samma ristares stenar)` : "ingen inom 50 km"}</td>
                </tr>
              );
            })}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      {known.length > 0 && (
        <Details title={`Grupper som liknar en känd ristare (${known.length})`}>
          <p className="text-xs text-slate-500">Stenar utan ristare i Rundata som kan höra till en känd ristare – underlag för attribuering snarare än en ny ristare.</p>
          <div className="overflow-x-auto">
            <ExportTable><table className="w-full text-sm">
              <thead><tr><Th>Nr</Th><Th>Liknar</Th><Th>Stenar</Th><Th>Attribueringsmodellen</Th><Th>Stabilitet</Th></tr></thead>
              <tbody>{known.map(g => (
                <tr key={g.id} className="border-t border-slate-900/5 align-top">
                  <td className="p-2">{g.id}</td>
                  <td className="p-2 font-semibold">{g.nearest_carver?.as_close_as_same_carver ? g.nearest_carver.carver : g.model?.carver}</td>
                  <td className="p-2 text-xs">{g.n}: <Stones list={asList(g.stones)} /></td>
                  <td className="p-2 text-xs">{g.model ? `${g.model.carver} för ${pc(g.model.share)} av ${g.model.n} stenar med förslag` : "–"}</td>
                  <td className="p-2">{pc(g.stability)}</td>
                </tr>))}</tbody>
            </table></ExportTable>
          </div>
        </Details>
      )}
      <Details title="Hur metoden prövades">
        <p className="text-sm text-slate-600">
          När metoden kördes på {v.n_stones} stenar med känd ristare, som om ristaren vore okänd, bestod en grupp i genomsnitt till {pc(v.purity)} av
          samma ristare ({pc(v.share_pure)} av grupperna till minst tre fjärdedelar), mot {pc(v.purity_geography)} för lika många närliggande stenar.
          Två stenar länkas när de ligger inom {cal.link_km} km och är så lika att paret är minst {cal.lr_min} gånger vanligare bland samma ristares
          stenar än bland olika ristares; {pc(cal.precision)} av sådana par med känd ristare är samma ristare.
        </p>
      </Details>
      <DocsNote anchor="1g-okända-ristare">Hur grupperna ska läsas och vilka reservationer som gäller står i avsnitt 1g.</DocsNote>
      <Method text={a.method} />
    </>
  );
}
