"use client";

import { Fragment, cloneElement, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Answer, InfoTip, PageIntro, QuestionCards, SigBadge, Tip, type AnswerProps, type Significance } from "@/components/Explain";
import { PatternBadges, PatternBody, type Pattern } from "@/components/PatternCard";
import { GLOSSARY } from "@/lib/glossary";
import { API_URL } from "@/lib/api";
import { corpus } from "@/lib/corpus";
import { useAuth } from "@/components/AuthContext";
import { GeologyBox, LanguageTraits } from "@/components/StoneContext";
import { SIMILARITY_HELP, fmtP } from "@/lib/significance";
import { DocsNote } from "@/components/KnownLimitations";
import ExportTable from "@/components/ExportTable";
import SavedQuestions from "@/components/SavedQuestions";

interface ProvinceRow {
  code: string; name: string; axelson: boolean; total: number; carver: number; style: number; dated: number;
  uncertain_interpretation: number; lost: number; measured: number;
}
interface Hypothesis extends StoneExtras {
  signum: string; place: string; province: string; style: string | null; carver: string; similarity: number;
  p_value: number | null; p_adjusted: number | null;
  margin: number; runner_up: string; n_words: number; in_carver_area: boolean; carver_area: string[];
  carver_precision: number | null; short_text: boolean; attributed_to?: string[];
}

// Rock type and language traits of the stone, compared with the suggested carver
interface StoneExtras {
  material: string | null; material_fit: boolean | null; material_text?: string;
  language: { agree: number; comparable: number; text: string; fits: boolean | null } | null;
}

function MaterialCell({ x }: { x: StoneExtras }) {
  if (!x.material) return <span className="text-slate-400">–</span>;
  const mark = x.material_fit === true ? "✓" : x.material_fit === false ? "!" : "";
  return (
    <span title={x.material_text ?? ""} className={x.material_fit === false ? "text-amber-800" : ""}>
      {x.material} {mark && <span className={`font-bold ${x.material_fit ? "text-emerald-700" : "text-amber-700"}`}>{mark}</span>}
    </span>
  );
}

function LanguageCell({ x }: { x: StoneExtras }) {
  if (!x.language || !x.language.comparable) return <span className="text-slate-400">–</span>;
  return (
    <span title={x.language.text} className={x.language.fits === false ? "text-amber-800 font-semibold" : ""}>
      {x.language.agree}/{x.language.comparable}
    </span>
  );
}
interface Priority {
  carver: string; inscriptions: number; signed: number; measured: number; measured_signa: string[];
  missing_to_target: number; suggestions: { signum: string; place: string; signed: boolean }[];
}
interface Brief { signum: string; place: string; province: string; style: string | null; dating: string; carvers: string[] }
interface Gaps {
  coverage: { scope: string; totals: Record<string, number>; per_province: ProvinceRow[] };
  hypotheses: { new: Hypothesis[]; reconsider: Hypothesis[]; evaluation: { top1_accuracy: number; signed_only: { top1_accuracy: number | null }; n_carvers: number; chance_top1: number } };
  open_questions: { uninterpreted: { count: number; items: Brief[] }; uncertain_style: { count: number; items: Brief[] } };
  measurement_priorities: Priority[];
  source_note: string;
  attribution: string;
}

type Verdict = "stämmer" | "nytt" | "motsäger";
interface Finding extends StoneExtras {
  stats?: Record<string, number | string | boolean | null>;
  signum: string; place: string; province: string; method: string; verdict: Verdict; ours: string; existing: string;
  evidence: number; novelty: number; relevance: number; score: number; assessment: string; suggested?: string;
  reasons: { belägg: string[]; nyhet: string[]; relevans: string[] };
  crosscheck?: CrossCheck;
  significance?: Significance;
  // The reasoned conclusion (same rules as the interpretation shown when the row is opened; METHODS.md 14d)
  interpretation?: { level: string; support: number; against: number };
}
// The suggestion checked against newer sources (Runor 2020, Wikidata)
interface CrossCheck {
  status: "finns redan" | "nämns" | "annan ristare" | "samma som" | "saknas" | "ej kontrollerad";
  runor?: { status: string; text: string; references: string[]; url?: string | null };
  wikidata?: { text: string };
}
type RPattern = Pattern;
interface Findings {
  r_patterns?: RPattern[];
  r_ready?: boolean;
  findings: Finding[];
  summary: { counts: Record<Verdict, number>; by_method: Record<string, Partial<Record<Verdict, number>>>; likely_new: number };
  technique_note: string | null;
  method_note: string;
}

type Tab = "findings" | "coverage" | "categories" | "size" | "hypotheses" | "reconsider" | "priorities" | "uninterpreted" | "style" | "textgaps";

// The probability model's open gaps (GET /api/research/gaps/textmodel, scripts/textmodel_candidates.py)
interface TextGapCandidate {
  signum: string; province: string; carved: string; gap: number; fill: string | null; word: string | null; p: number;
  alts: [string, number][]; reading: string | null; p_reading: number | null;
}
interface TextGaps {
  available: boolean; note?: string; model_version?: string; computed_at?: string; rundata_version?: string; min_p?: number;
  counts?: { gaps_inventoried: number; open: number; candidates: number; stones: number };
  candidates?: TextGapCandidate[];
}

interface CategoryStats {
  categories: { key: string; label: string; definition: string; base_rate: number; count: number }[];
  n_inscriptions: number;
  carvers: { carver: string; n: number; counts: Record<string, { k: number; share: number; expected: number; p: number; q: number; p_zero: number | null; direction: "över" | "under" | "som genomsnittet" }> }[];
  method: string;
}

// ---- sorting -------------------------------------------------------------------------------
type SortValue = string | number | boolean | null | undefined;
type SortState = { key: string; desc: boolean };

function useSorted<T>(rows: T[], get: Record<string, (r: T) => SortValue>, initial: SortState) {
  const [sort, setSort] = useState<SortState>(initial);
  const sorted = useMemo(() => {
    const f = get[sort.key];
    if (!f) return rows;
    return [...rows].sort((a, b) => {
      const va = f(a), vb = f(b);
      if (va == null && vb == null) return 0;
      if (va == null) return 1; // missing values last
      if (vb == null) return -1;
      const c = typeof va === "string" || typeof vb === "string"
        ? String(va).localeCompare(String(vb), "sv", { numeric: true })
        : Number(va) - Number(vb);
      return sort.desc ? -c : c;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, sort]);
  const header = (key: string, label: string, title?: string) => (
    <th className="p-2 whitespace-nowrap">
      <button onClick={() => setSort(s => ({ key, desc: s.key === key ? !s.desc : rows.length > 0 && typeof get[key](rows[0]) !== "string" }))}
        className={`uppercase tracking-wider hover:text-slate-900 ${sort.key === key ? "text-slate-900" : ""}`}>
        {label}{sort.key === key ? (sort.desc ? " ↓" : " ↑") : ""}
      </button>
      <InfoTip text={GLOSSARY[label] ?? title} />
    </th>
  );
  return { sorted, header, sort, setSort };
}

const VERDICT_STYLE: Record<Verdict, string> = {
  "stämmer": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "nytt": "bg-sky-50 text-sky-800 border-sky-200",
  "motsäger": "bg-amber-50 text-amber-900 border-amber-200",
};

// The interpretation's conclusion, strongest first; dots make the scale readable without colour
const LEVELS: { key: string; dots: string; style: string; help: string }[] = [
  { key: "starkt", dots: "●●●", style: "bg-emerald-50 text-emerald-900 border-emerald-400",
    help: "Minst två oberoende belägg för och inget emot (för ortografin dessutom justerat p under 0,05)." },
  { key: "måttligt", dots: "●●○", style: "bg-sky-50 text-sky-900 border-sky-300",
    help: "Belägg för, minst lika många för som emot, men inte tillräckligt för starkt. En prövbar hypotes." },
  { key: "svagt", dots: "●○○", style: "bg-slate-50 text-slate-700 border-slate-300",
    help: "Lite stöd, belägg emot eller en stilgrupp som talar emot." },
  { key: "bekräftelse", dots: "✓", style: "bg-white text-emerald-800 border-emerald-200",
    help: "Metoden kommer fram till samma sak som Rundata." },
  { key: "redan känt", dots: "○", style: "bg-white text-slate-600 border-slate-200",
    help: "Förslaget finns redan i nyare källor (Runor 2020 eller Wikidata)." },
  { key: "metodfel", dots: "!", style: "bg-amber-50 text-amber-900 border-amber-300",
    help: "Fyndet motsäger en signerad sten – en svaghet i metoden, inte ett fel i Rundata." },
];
const LEVEL_RANK = Object.fromEntries(LEVELS.map((l, i) => [l.key, LEVELS.length - i]));

function SortTh({ className, children }: { className: string; children: React.ReactElement<{ className?: string }> }) {
  return cloneElement(children, { className: `${children.props.className ?? ""} ${className}` });
}

function LevelBadge({ it }: { it?: Finding["interpretation"] }) {
  if (!it) return <span className="text-slate-400 text-xs">–</span>;
  const l = LEVELS.find(x => x.key === it.level);
  return (
    <div className="flex flex-col gap-0.5">
      <Tip text={`${l?.help ?? ""} Klicka på raden för hela resonemanget.`}>
        <span className={`inline-flex w-fit items-center gap-1.5 rounded-lg border px-2 py-0.5 text-xs font-bold ${l?.style ?? "border-slate-200"}`}>
          <span aria-hidden className="tracking-[-0.15em] text-[10px]">{l?.dots}</span>{it.level}
        </span>
      </Tip>
      {!["bekräftelse", "redan känt", "metodfel"].includes(it.level) && (
        <Tip text="Belägg utöver metodens eget: andra metoder, språkdrag, stil och bergart som talar för eller emot förslaget.">
          <span className="text-[11px] text-slate-500">andra belägg: {it.support} för, {it.against} emot</span>
        </Tip>
      )}
    </div>
  );
}

function Score({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-1.5 min-w-[70px]">
      <div className="h-1.5 w-10 bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full bg-slate-700 rounded-full" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className="text-[11px] font-mono text-slate-600">{Math.round(value * 100)}</span>
    </div>
  );
}

const pct = (n: number, d: number) => (d ? Math.round((100 * n) / d) : 0);
const fmt = (v: number | null | undefined, digits = 2) => (v == null ? "–" : v.toFixed(digits).replace(".", ","));

function Bar({ value, total, color }: { value: number; total: number; color: string }) {
  return (
    <div className="flex items-center gap-2 min-w-[110px]">
      <div className="h-2 flex-1 bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct(value, total)}%`, background: color }} />
      </div>
      <span className="text-[11px] font-mono text-slate-600 w-9 text-right">{pct(value, total)} %</span>
    </div>
  );
}

function StoneLinks({ signum, stacked }: { signum: string; stacked?: boolean }) {
  return (
    <span className={stacked ? "flex flex-col text-xs" : "whitespace-nowrap text-xs"} onClick={e => e.stopPropagation()}>
      <Link href={`/inskrifter?signum=${encodeURIComponent(signum)}`} className={`font-bold text-slate-900 hover:text-[#b7410e] ${stacked ? "break-words" : ""}`}>{signum}</Link>
      <Link href={`/3d?signum=${encodeURIComponent(signum)}`} className={`${stacked ? "text-[11px]" : "ml-2"} text-[#b7410e] hover:underline`}
        title="Öppnar 3D-analysen för att mäta huggspåren. Länken betyder inte att stenen redan är mätt.">{stacked ? "mät i 3D" : "öppna i 3D-analysen"}</Link>
    </span>
  );
}

export default function GapsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<Gaps | null>(null);
  const [found, setFound] = useState<Findings | null>(null);
  const [textGaps, setTextGaps] = useState<TextGaps | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/research/gaps/textmodel`).then(r => (r.ok ? r.json() : null)).then(d => setTextGaps(d)).catch(() => setTextGaps(null));
  }, []);
  const [measuredSigna, setMeasuredSigna] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("findings");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      let entries: Awaited<ReturnType<typeof corpus.list>> = [];
      if (user) {
        try { entries = await corpus.list(); } catch { /* corpus optional */ }
      }
      const post = (path: string, body: unknown) => fetch(`${API_URL}${path}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      }).then(async res => {
        if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
        return res.json();
      });
      try {
        const [gaps, findings] = await Promise.all([
          post("/api/research/gaps", { measured_signa: [...new Set(entries.map(e => e.signum))] }),
          post("/api/research/findings", {
            corpus: entries.map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means })),
          }),
        ]);
        if (!cancelled) { setData(gaps); setFound(findings); setMeasuredSigna([...new Set(entries.map(e => e.signum))]); }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Kunde inte hämta översikten.");
      }
    })();
    return () => { cancelled = true; };
  }, [user, reload]);

  if (error) return <div className="max-w-3xl mx-auto p-8 text-red-700 font-semibold">{error}</div>;
  if (!data || !found) return <div className="max-w-3xl mx-auto p-8 text-slate-500">Beräknar översikten …</div>;

  const t = data.coverage.totals;
  const nSig = (rows: Hypothesis[]) => rows.filter(h => h.p_adjusted != null && h.p_adjusted < 0.05).length;
  const cards: { key: Tab; topic: string; question: string; note: string }[] = [
    { key: "findings", topic: "Våra resultat", question: "Vad säger appens analyser jämfört med forskningen?", note: `${found.findings.length} fynd` },
    { key: "coverage", topic: "Luckor", question: "Var saknas uppgifter om runstenarna?", note: `${t.total - t.carver} stenar utan ristare` },
    { key: "hypotheses", topic: "Nya ristare", question: "Vilka stenar utan ristare liknar en känd ristare i stavningen?", note: `${data.hypotheses.new.length} stenar` },
    { key: "reconsider", topic: "Ompröva", question: "Vilka attribueringar kan behöva omprövas?", note: `${data.hypotheses.reconsider.length} stenar` },
    { key: "priorities", topic: "3D-mätning", question: "Vilka stenar vore mest värda att mäta i 3D?", note: `${data.measurement_priorities.length} ristare` },
    { key: "categories", topic: "Syfte", question: "Skiljer sig ristarna i vad inskrifterna handlar om?", note: "9 kategorier" },
    { key: "size", topic: "Storlek", question: "Restes större stenar för större syften?", note: "höjd mot syfte" },
    { key: "uninterpreted", topic: "Tolkning", question: "Vilka inskrifter är osäkert tolkade?", note: `${data.open_questions.uninterpreted.count} inskrifter` },
    { key: "style", topic: "Stilgrupp", question: "Vilka stenar har osäker stilgrupp?", note: `${data.open_questions.uncertain_style.count} stenar` },
    { key: "textgaps", topic: "Luckor i texten", question: "Vilka förlorade runor kan sannolikhetsmodellen fylla i?", note: textGaps?.counts ? `${textGaps.counts.candidates} luckor ≥ 80 %` : "beräknas" },
  ];
  const c = found.summary.counts;
  const sigFound = found.findings.filter(f => f.significance?.significant).length;
  const provinces = data.coverage.per_province.filter(r => r.total >= 30);
  const lowest = provinces.length ? provinces.reduce((m, r) => (r.carver / r.total < m.carver / m.total ? r : m)) : null;
  const ev = data.hypotheses.evaluation;
  const answers: Partial<Record<Tab, AnswerProps>> = {
    findings: {
      topic: "Våra resultat", question: "Vad säger appens analyser jämfört med forskningen?",
      why: "Appens metoder – stavning, den statistiska modellen, seriationen, okända ristare och huggteknik – ställs mot Rundata, som här står för den publicerade forskningen.",
      headline: { value: String(found.summary.likely_new), label: "fynd som sannolikt är ny kunskap enligt uppskattningen" },
      answer: <>{c.stämmer} av appens resultat stämmer med Rundata, {c.nytt} säger något som Rundata saknar och {c.motsäger} pekar på något annat. {sigFound} av fynden är <strong>statistiskt signifikanta</strong>.</>,
      interpretation: [
        "Bekräftelserna är ett test av metoderna: att de ofta kommer fram till samma ristare som forskningen talar för att de fungerar.",
        "De nya förslagen är hypoteser. Klicka på ett fynd för en tolkning som väger samman alla belägg och visar vad som talar emot.",
        "Fynd som redan finns i Runor 2020 eller Wikidata är inte ny kunskap, men de stärker förtroendet för metoden.",
      ],
      notSaying: [
        "Rundata (2018) är inte hela forskningen – ett 'nytt' fynd kan finnas i litteratur som appen inte har.",
        "Uppskattningen (belägg × nyhet × relevans) är en tumregel för att prioritera, inte en sannolikhet.",
        "Statistiskt signifikant betyder att en så stor likhet sällan uppstår utan ett verkligt samband (justerat p under 0,05) – inte att attribueringen är rätt.",
      ],
    },
    coverage: {
      topic: "Luckor", question: "Var saknas uppgifter om runstenarna?",
      why: "Där uppgifter saknas kan nya analyser och mätningar göra mest nytta.",
      headline: { value: `${pct(t.total - t.carver, t.total)} %`, label: "av runstenarna saknar ristare i Rundata" },
      answer: <>Av {t.total} svenska vikingatida runstenar saknar {t.total - t.carver} ristare och {t.total - t.style} säker stilgrupp; {t.dated} är daterade med årtal och {t.measured} är uppmätta i 3D.{lowest && <> Lägst andel med ristare bland landskap med minst 30 stenar har {lowest.name} ({pct(lowest.carver, lowest.total)} %).</>}</>,
      interpretation: [
        "Landskap med få attribueringar är där nya ristarförslag och okända ristare gör mest nytta.",
        "Uppland och Södermanland har flest attribueringar, främst genom Axelsons arbete (1993); i andra landskap kan attribueringar finnas i litteraturen utan att stå i Rundata.",
      ],
      notSaying: ["Att en uppgift saknas i Rundata betyder inte att den saknas i all forskning."],
    },
    hypotheses: {
      topic: "Nya ristare", question: "Vilka stenar utan ristare liknar en känd ristare i stavningen?",
      why: "Ristare hade egna stavningsvanor. En sten utan ristare som stavar som en känd ristare kan vara hans eller hennes.",
      headline: { value: String(data.hypotheses.new.length), label: `stenar utan ristare med tydlig stavningslikhet, varav ${nSig(data.hypotheses.new)} statistiskt signifikanta` },
      answer: <>Ortografin pekar ut en trolig ristare för {data.hypotheses.new.length} stenar utan ristare i Rundata; {nSig(data.hypotheses.new)} av likheterna är statistiskt signifikanta (justerat p under 0,05). Prövad på stenar med känd ristare hamnar rätt ristare först i {Math.round(ev.top1_accuracy * 100)} % av fallen, mot {Math.round(ev.chance_top1 * 100)} % med slumpen.</>,
      interpretation: [
        "Signifikanta likheter inom ristarens område är de bästa kandidaterna att pröva vidare.",
        "Väger tyngre när flera oberoende metoder – t.ex. den statistiska modellen eller huggtekniken – pekar mot samma ristare.",
      ],
      notSaying: [
        "Stavning är bara ett av flera drag; ornamentik, runformer och huggteknik vägs inte in här.",
        "Produktiva ristare som Öpir och Fot drar till sig förslag.",
      ],
    },
    reconsider: {
      topic: "Ompröva", question: "Vilka attribueringar kan behöva omprövas?",
      why: "En attribuerad sten som stavar som en annan ristare kan vara felbedömd – eller visa samarbete.",
      headline: { value: String(data.hypotheses.reconsider.length), label: `attribuerade stenar där stavningen pekar mot någon annan, varav ${nSig(data.hypotheses.reconsider)} signifikanta` },
      answer: <>För {data.hypotheses.reconsider.length} stenar som Rundata attribuerar pekar ortografin mot en annan ristare; {nSig(data.hypotheses.reconsider)} av likheterna är statistiskt signifikanta.</>,
      interpretation: [
        "Det kan vara en felaktig attribuering, men också samarbete, en verkstad eller en ristare som skrev olika vid olika tillfällen.",
        "Signerade stenar ingår inte – där är det metoden som har fel, inte ristaren.",
      ],
      notSaying: ["En stavningslikhet räcker inte för att underkänna en attribuering som bygger på ornamentik och runformer."],
    },
    priorities: {
      topic: "3D-mätning", question: "Vilka stenar vore mest värda att mäta i 3D?",
      why: "Huggtekniken är det enda belägget som inte bygger på tidigare forskares bedömningar, men den kräver flera uppmätta stenar per ristare.",
      answer: <>Listan visar för varje ristare hur många stenar som är uppmätta och vilka som skulle göra mest nytta att mäta – signerade stenar först, eftersom ristaren där är känd.</>,
      interpretation: ["Mät helst flera stenar av samma ristare på samma bergart, eftersom bergarten påverkar huggspåren."],
      notSaying: ["Huggspårsmåtten är ännu inte validerade som spår av ristarens hand."],
    },
    uninterpreted: {
      topic: "Tolkning", question: "Vilka inskrifter är osäkert tolkade?",
      why: "Osäkra läsningar är där nya bilder, RTI och 3D kan ge mest.",
      headline: { value: String(data.open_questions.uninterpreted.count), label: "inskrifter med osäker läsning eller tolkning i Rundata" },
      answer: <>Rundata markerar {data.open_questions.uninterpreted.count} inskrifter som osäkert lästa eller tolkade. Listan visar dem med plats, stil och datering.</>,
      interpretation: ["En ny läsning med strykljus (RTI) eller en 3D-relief kan avgöra oklara runor."],
    },
    style: {
      topic: "Stilgrupp", question: "Vilka stenar har osäker stilgrupp?",
      why: "Stilgruppen är grunden för dateringen; en osäker stilgrupp ger en osäker datering.",
      headline: { value: String(data.open_questions.uncertain_style.count), label: "stenar med osäker stilgrupp i Rundata" },
      answer: <>{data.open_questions.uncertain_style.count} stenar har en osäker stilgrupp. Seriationen i R kan ge ett förslag att pröva mot ornamentiken; appen bedömer inte stilgrupp ur foto.</>,
      notSaying: ["Seriationen bygger på språk och innehåll, inte på ornamentik, och daterar bara relativt."],
    },
  };

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <PageIntro title="Forskningsluckor"
        lead={<>Två saker på en sida: <strong>var kunskapen om runstenarna har luckor</strong> – stenar utan ristare, stilgrupp, datering
          eller mätningar – och <strong>vad appens egna analyser säger jämfört med forskningen</strong>. Varje fråga börjar med svaret i
          korthet och ett förslag till tolkning. Allt är förslag för forskare att pröva, inte färdiga slutsatser.</>}
        howTo={[
          <>Välj en fråga i korten. Under svaret finns tabellerna; klicka på en kolumnrubrik för att sortera.</>,
          <>Märket <strong>✓ Signifikant</strong> betyder att p eller q är under 0,05: ett så tydligt resultat vore ovanligt om det inte fanns något verkligt samband. Det säger inte hur stort eller viktigt resultatet är. Håll muspekaren över ⓘ och prickade ord för förklaringar.</>,
          <>Klicka på ett fynd för en tolkning som väger samman alla belägg och visar vad som talar emot.</>,
          <>Siffrorna i rutorna överst är länkar till inskrifterna bakom dem.</>,
        ]} />

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          ["Runstenar", `${t.total}`, "", gapHref("runestone")],
          ["Med ristare", `${pct(t.carver, t.total)} %`, `${t.total - t.carver} saknar`, gapHref("no_carver")],
          ["Säker stilgrupp", `${pct(t.style, t.total)} %`, `${t.total - t.style} saknar`, gapHref("no_style")],
          ["Datering", `${t.dated}`, `${pct(t.dated, t.total)} % daterade med årtal`, gapHref("dated")],
          ["Uppmätta", `${t.measured}`, user ? "i 3D-korpusen" : "logga in för att se", measuredSigna.length ? signaHref(measuredSigna) : ""],
        ].map(([label, value, sub, href]) => {
          const body = (
            <>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}<InfoTip text={GLOSSARY[label]} /></div>
              <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
              {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
            </>
          );
          return href
            ? <Link key={label} href={href} className="liquid-glass-island rounded-[24px] p-5 hover:ring-2 hover:ring-slate-900/20 transition">{body}</Link>
            : <div key={label} className="liquid-glass-island rounded-[24px] p-5">{body}</div>;
        })}
      </div>

      <Freshness textGaps={textGaps} />
      <QuestionCards items={cards} active={tab} onSelect={k => setTab(k as Tab)} />

      <div className="liquid-glass-island rounded-[32px] p-5 md:p-7 space-y-6">
        {answers[tab] && <Answer {...answers[tab]!} />}
        {tab === "findings" && <FindingsPanel data={found} loggedIn={!!user} onRefresh={() => setReload(r => r + 1)} />}
        {tab === "coverage" && <ProvinceTable rows={data.coverage.per_province} measuredSigna={measuredSigna} />}
        {tab === "categories" && <CategoryPanel />}
        {tab === "size" && <SizePanel />}
        {(tab === "hypotheses" || tab === "reconsider") && (
          <HypothesisTable key={tab} reconsider={tab === "reconsider"} ev={data.hypotheses.evaluation}
            rows={tab === "hypotheses" ? data.hypotheses.new : data.hypotheses.reconsider} />
        )}
        {tab === "priorities" && <PrioritiesPanel rows={data.measurement_priorities} />}
        {tab === "textgaps" && <TextGapsPanel data={textGaps} />}
        {(tab === "uninterpreted" || tab === "style") && (
          <BriefTable key={tab} uninterpreted={tab === "uninterpreted"}
            rows={(tab === "uninterpreted" ? data.open_questions.uninterpreted : data.open_questions.uncertain_style).items} />
        )}
      </div>
      <DocsNote anchor="14-forskningsluckor">Varifrån uppgifterna kommer, hur bedömningarna räknas och vilka reservationer som gäller står i avsnitt 14.</DocsNote>
      <p className="text-[11px] text-slate-500">{data.attribution}</p>
    </div>
  );
}

const TH_ROW = "text-left text-[11px] uppercase tracking-wider text-slate-500";

// Links to the inscriptions behind a number: same definitions as in the table
const gapHref = (gap: string, province?: string) =>
  `/inskrifter?gap=${gap}${province ? `&province=${encodeURIComponent(province)}` : ""}`;
const signaHref = (signa: string[]) => `/inskrifter?signa=${encodeURIComponent(signa.join(","))}`;
const CELL_LINK = "hover:text-[#b7410e] hover:underline decoration-[#b7410e]/40 underline-offset-2";

function BarLink({ value, total, color, has, missing }: { value: number; total: number; color: string; has: string; missing: string }) {
  return (
    <div className="flex items-center gap-2">
      <Link href={has} title={`Visa de ${value} som har uppgiften`} className="flex-1"><Bar value={value} total={total} color={color} /></Link>
      {total - value > 0 && (
        <Link href={missing} title={`Visa de ${total - value} som saknar uppgiften`} className="text-[11px] text-slate-500 whitespace-nowrap hover:text-[#b7410e]">
          {total - value} saknar
        </Link>
      )}
    </div>
  );
}

interface SizeTest { variable: string; n: number; ratio: number | null; p: number | null; q: number | null; median_with_m: number; median_without_m: number }
interface SizeStats {
  n: number; median_height_m: number; quartiles_m: [number, number]; error?: string;
  meta: { n_runestones: number; status: Record<string, number> }; source: string;
  tests: SizeTest[];
  correlations: { variable: string; rho: number; p: number; n: number; partial?: boolean }[];
  carvers: { carver: string; n: number; ratio: number | null; p: number | null; q: number | null; median_m: number }[];
  largest: { signum: string; height_m: number; categories: string[]; status: string[] }[];
}

function SizePanel() {
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

function CategoryPanel() {
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

function ProvinceTable({ rows, measuredSigna }: { rows: ProvinceRow[]; measuredSigna: string[] }) {
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

const CC_STYLE: Record<string, string> = {
  "finns redan": "bg-sky-50 text-sky-800 border-sky-200",
  "nämns": "bg-sky-50 text-sky-800 border-sky-200",
  "annan ristare": "bg-rose-50 text-rose-800 border-rose-200",
  "samma som": "bg-violet-50 text-violet-800 border-violet-200",
  "saknas": "bg-emerald-50 text-emerald-800 border-emerald-200",
};

function CrossCheckCell({ cc }: { cc?: CrossCheck }) {
  if (!cc) return <span className="text-slate-400" title="Inte avstämd mot nyare källor">–</span>;
  return <span className={`px-2 py-0.5 rounded-lg border text-[11px] font-bold whitespace-nowrap ${CC_STYLE[cc.status] ?? ""}`}
    title={[cc.runor?.text, cc.wikidata?.text].filter(Boolean).join(" ")}>{cc.status}</span>;
}

// Corpus-wide patterns from the R analyses: what confirms earlier research, what is worth testing, and the limits
const PATTERN_GROUPS: { key: string; label: string; statuses: string[]; accent: string; pill: string; help: string }[] = [
  { key: "test", label: "Att pröva", statuses: ["mönster att pröva"], accent: "border-l-amber-500", pill: "bg-amber-50 text-amber-900 border-amber-200",
    help: "Nya mönster som statistiken visar och som håller i båda halvorna av korpusen – tydliga hypoteser för runologer att pröva." },
  { key: "confirm", label: "Bekräftar", statuses: ["bekräftar"], accent: "border-l-emerald-600", pill: "bg-emerald-50 text-emerald-800 border-emerald-200",
    help: "Mönster som stämmer med det forskningen redan antar, nu med mätbar osäkerhet." },
  { key: "hint", label: "Indikationer", statuses: ["indikation"], accent: "border-l-amber-300", pill: "bg-amber-50/50 text-amber-800 border-amber-200",
    help: "Mönster som syns i hela korpusen men inte håller i alla kontroller eller i båda halvorna – idéer att pröva, med förbehåll." },
  { key: "limit", label: "Begränsningar", statuses: ["begränsning", "svagt", "svag effekt"], accent: "border-l-slate-400", pill: "bg-slate-100 text-slate-700 border-slate-300",
    help: "Cirkulära jämförelser och det metoden eller datan inte klarar." },
];

function PatternsBox({ patterns }: { patterns: RPattern[] }) {
  const [group, setGroup] = useState("");
  const [onlySig, setOnlySig] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const FIRST = 6;
  const groupOf = (pt: RPattern) => PATTERN_GROUPS.find(g => g.statuses.includes(pt.status)) ?? PATTERN_GROUPS[3];
  const nSig = patterns.filter(p => p.significance?.significant).length;
  const shown = patterns
    .filter(pt => (!group || groupOf(pt).key === group) && (!onlySig || pt.significance?.significant))
    .sort((a, b) => PATTERN_GROUPS.indexOf(groupOf(a)) - PATTERN_GROUPS.indexOf(groupOf(b)));
  const chip = (active: boolean) => `px-3 py-1.5 rounded-xl border text-xs font-bold transition-colors ${active
    ? "bg-slate-900 border-slate-900 text-white" : "bg-white border-slate-300 text-slate-700 hover:bg-slate-50"}`;
  return (
    <details open className="mb-6 rounded-2xl border border-slate-200 bg-white/70 p-4 sm:p-5">
      <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="text-lg font-bold text-slate-900">Mönster i hela korpusen</span>
          <span className="text-sm text-slate-500">statistiken i R för alla svenska vikingatida runstenar · {patterns.length} resultat</span>
          <Link href="/statistik" onClick={e => e.stopPropagation()} className="ml-auto text-xs font-semibold text-[#b7410e] hover:underline">
            Visa figurer och metod →
          </Link>
        </div>
      </summary>
      <div className="flex flex-wrap items-center gap-2 mt-4 mb-4">
        <button onClick={() => setGroup("")} className={chip(!group)}>Alla {patterns.length}</button>
        {PATTERN_GROUPS.map(g => {
          const n = patterns.filter(p => groupOf(p).key === g.key).length;
          return n ? (
            <button key={g.key} onClick={() => setGroup(group === g.key ? "" : g.key)} className={chip(group === g.key)} title={g.help}>
              {g.label} {n}
            </button>
          ) : null;
        })}
        <button onClick={() => setOnlySig(!onlySig)}
          className={`px-3 py-1.5 rounded-xl border text-xs font-bold ${onlySig ? "bg-emerald-700 border-emerald-700 text-white" : "bg-white border-slate-300 text-emerald-800 hover:bg-emerald-50"}`}>
          ✓ Statistiskt signifikanta {nSig}
        </button>
      </div>
      <p className="text-xs text-slate-500 mb-3 max-w-4xl">
        Tre frågor per mönster: <strong>är det statistiskt signifikant</strong> (grönt märke), <strong>håller det i båda
        halvorna</strong> av korpusen (uppdelad per socken – då är det ett tydligt mönster) och <strong>är det känt</strong> i
        forskningen (bekräftar) eller nytt (att pröva). Varje mönster har en hypotes om vad det kan betyda och hur den kan
        prövas – hypotesen är djärv med avsikt, påståendet är försiktigt.
      </p>
      <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {shown.slice(0, showAll ? undefined : FIRST).map((pt, i) => {
          const g = groupOf(pt);
          return (
            <li key={i} className={`rounded-xl border border-slate-200 border-l-4 ${g.accent} bg-white px-4 py-3`}>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{pt.topic}</span>
                <span className="ml-auto flex flex-wrap items-center gap-1.5">
                  <span className={`px-2 py-0.5 rounded-lg border text-[11px] font-bold ${g.pill}`} title={g.help}>{pt.status}</span>
                  <PatternBadges pt={pt} />
                  <SigBadge sig={pt.significance} compact />
                </span>
              </div>
              <PatternBody pt={pt} />
            </li>
          );
        })}
      </ul>
      {shown.length > FIRST && (
        <button onClick={() => setShowAll(!showAll)} className="mt-3 text-sm font-semibold text-[#b7410e] hover:underline">
          {showAll ? "Visa färre" : `Visa alla ${shown.length}`}
        </button>
      )}
      {shown.length === 0 && <p className="text-sm text-slate-500">Inga mönster matchar filtret.</p>}
    </details>
  );
}

function FindingsPanel({ data, loggedIn, onRefresh }: { data: Findings; loggedIn: boolean; onRefresh: () => void }) {
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);
  const crosscheck = async () => {
    setChecking(true); setCheckError(null);
    try {
      const res = await fetch(`${API_URL}/api/r/crosscheck`, { method: "POST" });
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
      onRefresh();
    } catch (e) {
      setCheckError(e instanceof Error ? e.message : "Avstämningen misslyckades.");
    } finally {
      setChecking(false);
    }
  };
  const [verdict, setVerdict] = useState<Verdict | "">("");
  const [method, setMethod] = useState("");
  const [onlyLikely, setOnlyLikely] = useState(false);
  const [onlySignificant, setOnlySignificant] = useState(false);
  const [level, setLevel] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const methods = Object.keys(data.summary.by_method);
  const rows = useMemo(() => data.findings.filter(f =>
    (!verdict || f.verdict === verdict) && (!method || f.method === method)
    && (!onlyLikely || f.assessment.startsWith("Sannolikt ny") || f.assessment === "Värd en omprövning")
    && (!onlySignificant || f.significance?.significant === true)
    && (!level || f.interpretation?.level === level)),
  [data.findings, verdict, method, onlyLikely, onlySignificant, level]);
  const levelCounts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const f of data.findings) if (f.interpretation) c[f.interpretation.level] = (c[f.interpretation.level] ?? 0) + 1;
    return c;
  }, [data.findings]);
  const nSignificant = data.findings.filter(f => f.significance?.significant).length;
  const sortState = useSorted(rows, {
    signum: f => f.signum, place: f => f.place, method: f => f.method, verdict: f => f.verdict,
    suggested: f => f.suggested, existing: f => f.existing, evidence: f => f.evidence, novelty: f => f.novelty,
    relevance: f => f.relevance, score: f => f.score, assessment: f => f.assessment,
    crosscheck: f => f.crosscheck?.status, material: f => f.material, language: f => (f.language?.comparable ? f.language.agree / f.language.comparable : null),
    level: f => (f.interpretation ? LEVEL_RANK[f.interpretation.level] * 1000 + f.score * 100 : null),
  }, { key: "score", desc: true });
  const { sorted, header, sort, setSort } = sortState;
  const SORTS: [string, string, boolean][] = [
    ["score", "Uppskattning", true], ["level", "Tolkning", true], ["evidence", "Belägg", true], ["novelty", "Nyhet", true],
    ["relevance", "Relevans", true], ["language", "Språkdrag", true], ["crosscheck", "Nyare källor", false],
    ["material", "Bergart", false], ["method", "Metod", false], ["verdict", "Mot forskningen", false], ["signum", "Sten", false],
  ];
  const c = data.summary.counts;
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        Appens analyser ställda mot Rundata (version 3.1, 2018), som här står för den publicerade forskningen: ortografisk
        stilometri (alla inskrifter, stenen själv utesluten ur ristarprofilen), huggteknik i mätkorpusen och – när
        statistiken i R är beräknad – attribueringsmodellen, de okända ristarna och Upplands seriation.
        Kolumnen <strong>Nyare källor</strong> visar om förslaget redan finns i Runor 2020 (RAÄ) eller Wikidata. <strong>Uppskattningen</strong> väger belägg × nyhet × relevans (0–100) och är en
        tumregel för att prioritera – inte en granskning av litteraturen. Klicka på en rad för att se skälen.
      </p>
      {data.r_patterns && data.r_patterns.length > 0 && <PatternsBox patterns={data.r_patterns} />}
      <SavedQuestions />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {([["stämmer", "Stämmer med forskningen"], ["nytt", "Nytt – saknas i Rundata"], ["motsäger", "Motsäger forskningen"]] as [Verdict, string][]).map(([v, label]) => (
          <button key={v} onClick={() => setVerdict(verdict === v ? "" : v)}
            className={`rounded-2xl border p-4 text-left ${VERDICT_STYLE[v]} ${verdict === v ? "ring-2 ring-slate-900" : ""}`}>
            <div className="text-[11px] font-bold uppercase tracking-wider">{label}</div>
            <div className="text-2xl font-bold">{c[v]}</div>
          </button>
        ))}
        <button onClick={() => setOnlyLikely(!onlyLikely)}
          className={`rounded-2xl border p-4 text-left bg-white border-slate-200 ${onlyLikely ? "ring-2 ring-slate-900" : ""}`}>
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Sannolikt ny kunskap</div>
          <div className="text-2xl font-bold text-slate-900">{data.summary.likely_new}</div>
          <div className="text-[11px] text-slate-500">klicka för att visa dessa och omprövningar</div>
        </button>
      </div>
      <div className="flex flex-wrap items-center gap-3 mb-3 text-sm">
        <select value={method} onChange={e => setMethod(e.target.value)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-sm font-semibold outline-none">
          <option value="">Alla metoder</option>
          {methods.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <button onClick={() => setOnlySignificant(!onlySignificant)}
          className={`px-3 py-1.5 rounded-xl border text-xs font-bold ${onlySignificant ? "bg-emerald-700 border-emerald-700 text-white" : "bg-white border-slate-300 text-emerald-800 hover:bg-emerald-50"}`}>
          <Tip text={GLOSSARY["Statistiskt signifikant"] + " Ortografin (justerat p), statistiska modellen (q, mot de sannolikheter felaktiga ristare får) och huggtekniken har ett signifikanstest per sten; seriationen och grupperna av stenar utan ristare är skattningar utan test."}>
            ✓ Bara statistiskt signifikanta ({nSignificant})
          </Tip>
        </button>
        <span className="text-slate-500">{sorted.length} fynd</span>
        {data.r_ready && (
          <button onClick={crosscheck} disabled={checking}
            className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:bg-slate-50 disabled:opacity-50">
            {checking ? "Stämmer av …" : "Stäm av mot Runor 2020 och Wikidata"}
          </button>
        )}
        {checkError && <span className="text-xs text-red-700">{checkError}</span>}
        {data.technique_note && <span className="text-amber-800 text-xs">{data.technique_note}{!loggedIn && " Logga in för att ta med mätkorpusen."}</span>}
      </div>
      <div className="flex flex-wrap items-center gap-2 mb-3 text-xs">
        <span className="font-bold uppercase tracking-wider text-[11px] text-slate-500">Tolkning<InfoTip text={GLOSSARY["Tolkning"]} /></span>
        <button onClick={() => setLevel("")}
          className={`px-2.5 py-1 rounded-lg border font-bold ${!level ? "bg-slate-900 border-slate-900 text-white" : "bg-white border-slate-300 text-slate-700 hover:bg-slate-50"}`}>
          Alla
        </button>
        {LEVELS.filter(l => levelCounts[l.key]).map(l => (
          <button key={l.key} onClick={() => setLevel(level === l.key ? "" : l.key)} title={l.help}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border font-bold ${l.style} ${level === l.key ? "ring-2 ring-slate-900" : "hover:brightness-95"}`}>
            <span aria-hidden className="tracking-[-0.15em] text-[10px]">{l.dots}</span>{l.key} <span className="font-normal opacity-70">{levelCounts[l.key]}</span>
          </button>
        ))}
        <label className="ml-auto flex items-center gap-2 text-slate-600">Sortera efter
          <select value={sort.key} onChange={e => setSort({ key: e.target.value, desc: SORTS.find(x => x[0] === e.target.value)?.[2] ?? true })}
            className="liquid-glass-input-wrapper rounded-lg px-2 py-1 text-xs font-semibold outline-none">
            {SORTS.map(([k, name]) => <option key={k} value={k}>{name}</option>)}
          </select>
          <button onClick={() => setSort(x => ({ ...x, desc: !x.desc }))} className="px-2 py-1 rounded-lg border border-slate-300 bg-white font-bold"
            title={sort.desc ? "Störst först – klicka för minst först" : "Minst först – klicka för störst först"}>{sort.desc ? "↓" : "↑"}</button>
        </label>
      </div>
      <div>
        <ExportTable><table className="w-full text-sm table-fixed">
          <colgroup>
            <col className="w-[18%] sm:w-[12%]" /><col /><col className="w-[26%] sm:w-[17%]" /><col className="hidden sm:table-column w-[22%]" />
          </colgroup>
          <thead>
            <tr className={TH_ROW}>
              {header("signum", "Sten")}
              {header("verdict", "Fynd", "Metoden, vad den föreslår och vad Rundata anger. Etiketterna under: nyare källor, bergart och språkdrag.")}
              {header("level", "Tolkning")}
              <SortTh className="hidden sm:table-cell">{header("score", "Uppskattning")}</SortTh>
            </tr>
          </thead>
          <tbody>
            {sorted.slice(0, 300).map(f => {
              const id = `${f.signum}|${f.method}`;
              return (
                <FindingRow key={id} f={f} open={open === id} onToggle={() => setOpen(open === id ? null : id)} />
              );
            })}
          </tbody>
        </table></ExportTable>
        {sorted.length > 300 && <p className="text-xs text-slate-500 mt-2">Visar de 300 första – sortera eller filtrera för att se fler.</p>}
      </div>
      <div className="mt-4"><DocsNote anchor="14b-våra-resultat-mot-befintlig-forskning">Hur belägg, nyhet, relevans och bedömning räknas står i avsnitt 14b.</DocsNote></div>
    </>
  );
}

interface Interpretation { paragraphs: { title: string; text: string }[]; level: string; support: number; against: number }
const interpretations = new Map<string, Interpretation>();
const LEVEL_STYLE: Record<string, string> = {
  starkt: "border-emerald-300 bg-emerald-50/60", "måttligt": "border-sky-300 bg-sky-50/60", svagt: "border-slate-300 bg-slate-50",
  "redan känt": "border-slate-300 bg-slate-50", metodfel: "border-amber-300 bg-amber-50/60", "bekräftelse": "border-emerald-200 bg-white",
};

// A reasoned reading of the finding, weighing its evidence against the other methods and newer sources
function InterpretationBox({ f }: { f: Finding }) {
  const key = `${f.signum}|${f.method}|${f.suggested ?? ""}|${f.crosscheck?.status ?? ""}`;
  const [it, setIt] = useState<Interpretation | null>(interpretations.get(key) ?? null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (interpretations.has(key)) return;
    fetch(`${API_URL}/api/research/interpret`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(f) })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then((d: Interpretation) => { interpretations.set(key, d); setIt(d); })
      .catch(e => setError(e instanceof Error ? e.message : "Tolkningen kunde inte hämtas."));
  }, [key, f]);
  if (error) return <p className="text-red-700">{error}</p>;
  if (!it) return <p className="text-slate-500">Väger samman beläggen …</p>;
  const last = it.paragraphs[it.paragraphs.length - 1];
  return (
    <div className={`rounded-xl border px-4 py-3 mb-3 ${LEVEL_STYLE[it.level] ?? "border-slate-200"}`}>
      <div className="flex flex-wrap items-baseline gap-2 mb-1">
        <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500">Tolkning</span>
        <span className="text-xs font-bold text-slate-900">{it.level}</span>
        <span className="text-[11px] text-slate-500">· {it.support} andra belägg för, {it.against} emot</span>
      </div>
      <p className="text-sm text-slate-900 font-medium">{last.text}</p>
      <details className="mt-2">
        <summary className="cursor-pointer text-[11px] font-semibold text-slate-600">Resonemanget steg för steg</summary>
        <div className="mt-2 space-y-2">
          {it.paragraphs.slice(0, -1).map(p => (
            <div key={p.title}><span className="font-semibold text-slate-800">{p.title}. </span><span>{p.text}</span></div>
          ))}
        </div>
      </details>
      <div className="mt-2"><DocsNote anchor="14d-tolkning-av-fynden">Reglerna bakom tolkningen står i avsnitt 14d.</DocsNote></div>
    </div>
  );
}

// The parts of the old score columns, as one small line: evidence, novelty and relevance
function ScoreParts({ f }: { f: Finding }) {
  const part = (label: string, v: number) => (
    <Tip text={`${label}: ${GLOSSARY[label] ?? ""}`}><span>{label[0]} {Math.round(v * 100)}</span></Tip>
  );
  return <div className="flex gap-2 text-[10px] font-mono text-slate-500">{part("Belägg", f.evidence)}{part("Nyhet", f.novelty)}{part("Relevans", f.relevance)}</div>;
}

function Chip({ label, children, title }: { label: string; children: React.ReactNode; title?: string }) {
  return (
    <span title={title} className="inline-flex items-center gap-1 rounded-md bg-slate-900/[0.04] px-1.5 py-0.5 text-[11px] text-slate-700">
      <span className="text-slate-500">{label}</span>{children}
    </span>
  );
}

function FindingRow({ f, open, onToggle }: { f: Finding; open: boolean; onToggle: () => void }) {
  return (
    <>
      <tr className={`border-t border-slate-900/5 cursor-pointer align-top hover:bg-white/60 ${open ? "bg-white/60" : ""}`} onClick={onToggle}
        aria-expanded={open}>
        <td className="p-2 break-words"><StoneLinks signum={f.signum} stacked /><div className="text-[11px] text-slate-500 mt-0.5" translate="no">{f.place}</div></td>
        <td className="p-2">
          <div className="flex flex-wrap items-center gap-1.5 mb-1">
            <span className={`px-2 py-0.5 rounded-lg border text-[11px] font-bold ${VERDICT_STYLE[f.verdict]}`}>{f.verdict}</span>
            <span className="text-[11px] uppercase tracking-wider text-slate-500">{f.method}</span>
          </div>
          <div className="text-xs text-slate-900">{f.ours}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Rundata: {f.existing}</div>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {f.crosscheck && <Chip label="Nyare källor"><CrossCheckCell cc={f.crosscheck} /></Chip>}
            {f.material && <Chip label="Bergart" title={GLOSSARY["Bergart"]}><MaterialCell x={f} /></Chip>}
            {f.language?.comparable ? <Chip label="Språkdrag" title={GLOSSARY["Språkdrag"]}><LanguageCell x={f} /></Chip> : null}
            <span className="sm:hidden"><Chip label="Uppskattning">{Math.round(f.score * 100)}</Chip></span>
          </div>
        </td>
        <td className="p-2"><div className="flex flex-col gap-1.5"><LevelBadge it={f.interpretation} />
          <SigBadge compact sig={f.significance?.significant && f.interpretation && ["måttligt", "svagt"].includes(f.interpretation.level)
            ? { ...f.significance, qualified: "metodens eget test är signifikant, men tolkningen, som väger in alla belägg, är " + f.interpretation.level }
            : f.significance} /></div></td>
        <td className="p-2 hidden sm:table-cell">
          <Score value={f.score} />
          <div className="text-[11px] text-slate-600 mt-1 leading-snug">{f.assessment}</div>
          <div className="mt-1"><ScoreParts f={f} /></div>
        </td>
      </tr>
      {open && (
        <tr className="bg-white/50">
          <td colSpan={4} className="p-3 text-xs text-slate-700">
            <InterpretationBox f={f} />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(["belägg", "nyhet", "relevans"] as const).map(k => (
                <div key={k}>
                  <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500 mb-1">{k}</div>
                  <ul className="list-disc pl-4 space-y-0.5">{f.reasons[k].map((r, i) => <li key={i}>{r}</li>)}</ul>
                </div>
              ))}
            </div>
            {f.crosscheck && (
              <div className="mt-3 pt-3 border-t border-slate-900/5 space-y-1">
                <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500">Nyare källor</div>
                {f.crosscheck.runor && (
                  <p>{f.crosscheck.runor.text}{" "}
                    {f.crosscheck.runor.url && <a href={f.crosscheck.runor.url} target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Öppna i Runor</a>}
                  </p>
                )}
                {f.crosscheck.runor?.references?.length ? <p>Litteratur i Runor att kontrollera: {f.crosscheck.runor.references.join("; ")}</p> : null}
                {f.crosscheck.wikidata && <p>{f.crosscheck.wikidata.text}</p>}
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pt-3 border-t border-slate-900/5">
              <div className="space-y-2">
                <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500">Bergart</div>
                <p>{f.material_text ?? (f.material ? `Stenen: ${f.material}.` : "Rundata anger inget material.")}</p>
                <GeologyBox signum={f.signum} />
              </div>
              <div className="space-y-2">
                <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500">Språkdrag (fonetisk stil och språkbruk)</div>
                {f.suggested ? <LanguageTraits signum={f.signum} carver={f.suggested} /> : <LanguageTraits signum={f.signum} />}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function HypothesisTable({ rows, reconsider, ev }: { rows: Hypothesis[]; reconsider: boolean; ev: Gaps["hypotheses"]["evaluation"] }) {
  const { sorted, header } = useSorted(rows, {
    signum: h => h.signum, place: h => h.place, attributed: h => h.attributed_to?.join(", "), carver: h => h.carver,
    similarity: h => h.similarity, margin: h => h.margin, precision: h => h.carver_precision, p: h => h.p_adjusted,
    area: h => h.in_carver_area, words: h => h.n_words, material: h => h.material,
    language: h => (h.language?.comparable ? h.language.agree / h.language.comparable : null),
  }, { key: "precision", desc: true });
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        {!reconsider
          ? "Runstenar utan ristare i Rundata där stavning, skiljetecken och bindrunor tydligt liknar en känd ristares. Det är hypoteser att pröva – helst med uppmätt huggteknik – inte attribueringar."
          : "Attribuerade stenar där ortografin pekar mot en annan ristare än litteraturen. Kan bero på samarbete, verkstäder eller en osäker attribuering."}
        {" "}Modellens träffsäkerhet: rätt ristare först i {Math.round(ev.top1_accuracy * 100)} % ({ev.signed_only.top1_accuracy != null ? `${Math.round(ev.signed_only.top1_accuracy * 100)} % för signerade` : ""}) bland {ev.n_carvers} ristare.
        <em> Precision</em> anger hur ofta modellen har rätt när den föreslår just den ristaren.
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead>
            <tr className={TH_ROW}>
              {header("signum", "Sten")}{header("place", "Plats")}
              {reconsider && header("attributed", "Rundata")}
              {header("carver", "Ortografin pekar mot")}{header("similarity", "Likhet", SIMILARITY_HELP)}{header("p", "p (just.)", SIMILARITY_HELP)}{header("margin", "Marginal")}
              {header("precision", "Precision")}{header("area", "Inom ristarens område")}{header("words", "Ord")}
              {header("material", "Bergart", "✓ = bergarten förekommer på ristarens stenar, ! = sällan")}
              {header("language", "Språkdrag", "Jämförbara språkdrag som stämmer med ristaren")}
            </tr>
          </thead>
          <tbody>
            {sorted.map(h => (
              <tr key={h.signum} className="border-t border-slate-900/5">
                <td className="p-2"><StoneLinks signum={h.signum} /></td>
                <td className="p-2 text-slate-600" translate="no">{h.place}</td>
                {reconsider && <td className="p-2">{h.attributed_to?.join(", ")}</td>}
                <td className="p-2 font-semibold">{h.carver} <span className="text-slate-400 font-normal">(sedan {h.runner_up})</span></td>
                <td className="p-2 font-mono text-xs">{fmt(h.similarity)}</td>
                <td className="p-2 font-mono text-xs">{fmtP(h.p_value)} <span className="text-slate-400">({fmtP(h.p_adjusted)})</span></td>
                <td className="p-2 font-mono text-xs">{fmt(h.margin)}</td>
                <td className="p-2 font-mono text-xs">{h.carver_precision != null ? `${Math.round(h.carver_precision * 100)} %` : "–"}</td>
                <td className="p-2 text-xs">{h.in_carver_area ? "Ja" : <span className="text-amber-700">Nej ({h.carver_area.join(", ")}) – kan vara regional stavning</span>}</td>
                <td className="p-2 text-xs">{h.n_words}{h.short_text && <span className="text-amber-700"> kort</span>}</td>
                <td className="p-2 text-xs"><MaterialCell x={h} /></td>
                <td className="p-2 text-xs"><LanguageCell x={h} /></td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
    </>
  );
}

function PrioritiesPanel({ rows }: { rows: Priority[] }) {
  const [key, setKey] = useState<"inscriptions" | "signed" | "measured" | "missing">("inscriptions");
  const sorted = useMemo(() => [...rows].sort((a, b) => {
    if (key === "measured") return a.measured - b.measured || b.inscriptions - a.inscriptions;
    if (key === "missing") return b.missing_to_target - a.missing_to_target || b.inscriptions - a.inscriptions;
    return b[key] - a[key];
  }), [rows, key]);
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p className="text-sm text-slate-600 max-w-3xl">
          Attribuering mot mätkorpusen kräver minst två – helst fem – uppmätta stenar per ristare. Här är ristarna med
          många säkra inskrifter i Rundata men få uppmätta stenar, med förslag på stenar att skanna (signerade först).
        </p>
        <label className="text-sm text-slate-600">Sortera efter{" "}
          <select value={key} onChange={e => setKey(e.target.value as typeof key)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-sm font-semibold outline-none">
            <option value="inscriptions">Flest inskrifter</option>
            <option value="signed">Flest signerade</option>
            <option value="measured">Minst uppmätta</option>
            <option value="missing">Flest mätningar kvar</option>
          </select>
        </label>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sorted.slice(0, 30).map(p => (
          <div key={p.carver} className="bg-white/70 rounded-2xl p-4 border border-slate-200">
            <div className="flex justify-between items-baseline">
              <Link href={`/inskrifter?carver=${encodeURIComponent(p.carver)}`} className="font-bold text-slate-900 hover:text-[#b7410e]">{p.carver}</Link>
              <span className="text-xs text-slate-500">{p.inscriptions} inskrifter ({p.signed} signerade)</span>
            </div>
            <div className="text-xs mt-1">
              Uppmätta: <strong>{p.measured}</strong>{p.missing_to_target > 0 && <span className="text-amber-700"> – {p.missing_to_target} till behövs</span>}
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
              {p.suggestions.slice(0, 6).map(s => (
                <span key={s.signum} className="text-xs">
                  <StoneLinks signum={s.signum} />{s.signed && <span className="text-emerald-700"> (S)</span>}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// When the figures on this page were computed, and on which data: the R corpus analyses, the text model and Rundata
function Freshness({ textGaps }: { textGaps: TextGaps | null }) {
  const [r, setR] = useState<{ computed_at?: string | null; fingerprint?: string; n_stones?: number } | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/rstats/status`).then(x => (x.ok ? x.json() : null)).then(d => setR(d?.corpus ?? null)).catch(() => setR(null));
  }, []);
  const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : "–");
  return (
    <p className="text-[11px] text-slate-500 -mt-2 mb-4">
      Underlag: {textGaps?.rundata_version ?? "Samnordisk runtextdatabas 3.1 (2018)"} · statistiken i R beräknad {day(r?.computed_at)}
      {r?.n_stones ? ` på ${r.n_stones} stenar` : ""} · sannolikhetsmodellen {textGaps?.model_version ?? "–"}, luckorna inventerade {day(textGaps?.computed_at)}.
      Täckning, hypoteser och prioriteringar räknas vid varje anrop.
    </p>
  );
}

function TextGapsPanel({ data }: { data: TextGaps | null }) {
  const [prov, setProv] = useState("");
  const rows = useMemo(() => (data?.candidates ?? []).filter(c => !prov || c.province === prov), [data, prov]);
  if (!data) return <p className="text-sm text-slate-500">Hämtar luckorna …</p>;
  if (!data.available || !data.candidates) return <p className="text-sm text-slate-500">{data.note ?? "Kandidatlistan saknas."}</p>;
  const provinces = [...new Set(data.candidates.map(c => c.province))].sort();
  const c = data.counts!;
  return (
    <>
      <p className="text-sm text-slate-600 mb-3 max-w-4xl">
        Sannolikhetsmodellen (METHODS.md 8.1, {data.model_version}) har gått igenom {c.gaps_inventoried} luckor i de vikingatida
        runstenarnas texter. {c.open} av dem har Rundata lämnat oåterställda; för {c.candidates} luckor på {c.stones} stenar
        fyller modellen i ett känt ord med minst {Math.round((data.min_p ?? 0.8) * 100)} % kalibrerad sannolikhet. Det är
        underlag att granska mot foto och skanning – öppna stenen och panelen <em>Vad skannern ser</em> – inte fynd.
        Kalibreringen är prövad på luckor som utgivarna fyllt (blindtest 2026-10-17); öppna luckor kan vara svårare.
      </p>
      <label className="text-sm text-slate-600 mb-3 block">Landskap{" "}
        <select value={prov} onChange={e => setProv(e.target.value)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-sm font-semibold">
          <option value="">alla ({data.candidates.length})</option>
          {provinces.map(p => <option key={p} value={p}>{p} ({data.candidates!.filter(x => x.province === p).length})</option>)}
        </select>
      </label>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr className={TH_ROW}><th className="p-2 text-left">Sten</th><th className="p-2 text-left">Hugget</th><th className="p-2 text-left">Ifyllnad</th>
            <th className="p-2 text-left">Ord</th><th className="p-2 text-left">p</th><th className="p-2 text-left">Näst bästa</th><th className="p-2 text-left">Läsning</th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.signum}-${r.gap}-${i}`} className="border-t border-slate-900/5 align-top">
                <td className="p-2"><StoneLinks signum={r.signum} /></td>
                <td className="p-2 font-mono text-xs" translate="no">{r.carved}</td>
                <td className="p-2 font-mono text-xs" translate="no">{r.fill ?? "–"}</td>
                <td className="p-2 font-semibold" translate="no">{r.word ?? "–"}</td>
                <td className="p-2">{Math.round(r.p * 100)} %</td>
                <td className="p-2 text-xs text-slate-600" translate="no">{r.alts[0] ? `${r.alts[0][0]} (${Math.round(r.alts[0][1] * 100)} %)` : "–"}</td>
                <td className="p-2 text-xs text-slate-600 max-w-md" translate="no">{r.reading ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
      <p className="text-[11px] text-slate-500 mt-3">
        Byggd {data.computed_at?.slice(0, 10)} ur luckinventeringen (scripts/runlm_gaps.py → scripts/textmodel_candidates.py).
        En lucka kan ha flera rader när flera ifyllnader når gränsen.
      </p>
    </>
  );
}

function BriefTable({ rows, uninterpreted }: { rows: Brief[]; uninterpreted: boolean }) {
  const order = useMemo(() => new Map(rows.map((b, i) => [b.signum, i])), [rows]);
  const { sorted, header } = useSorted(rows, {
    order: b => order.get(b.signum), signum: b => b.signum, place: b => b.place, province: b => b.province,
    style: b => b.style, dating: b => b.dating || null, carvers: b => b.carvers.join(", ") || null,
  }, { key: "order", desc: false });
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        {uninterpreted
          ? "Bevarade runstenar vars normalisering saknas eller är markerad som osäker i Rundata, från början sorterade med de längsta texterna först. RTI-visaren och ristningskartan från 3D kan hjälpa nyläsningar."
          : "Bevarade runstenar där stilgruppen är osäker (?) i Rundata. Ornamentiken får avgöra för ögat – foto, strykljus och ristningskarta finns under Bilder och runformer på 3D-sidan."}
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr className={TH_ROW}>{header("signum", "Sten")}{header("place", "Plats")}{header("province", "Landskap")}{header("style", "Stil")}{header("dating", "Datering")}{header("carvers", "Ristare")}</tr></thead>
          <tbody>
            {sorted.slice(0, 200).map(b => (
              <tr key={b.signum} className="border-t border-slate-900/5">
                <td className="p-2"><StoneLinks signum={b.signum} /></td>
                <td className="p-2 text-slate-600" translate="no">{b.place}</td>
                <td className="p-2">{b.province}</td>
                <td className="p-2">{b.style ?? "–"}</td>
                <td className="p-2">{b.dating || "–"}</td>
                <td className="p-2">{b.carvers.join(", ") || "–"}</td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
    </>
  );
}
