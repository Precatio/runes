import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { InfoTip, SigBadge, Tip } from "@/components/Explain";
import { PatternBadges, PatternBody, HideWrittenToggle } from "@/components/PatternCard";
import { GLOSSARY } from "@/lib/glossary";
import { API_URL } from "@/lib/api";
import { GeologyBox, LanguageTraits } from "@/components/StoneContext";
import { DocsNote } from "@/components/KnownLimitations";
import ExportTable from "@/components/ExportTable";
import SavedQuestions from "@/components/SavedQuestions";
import { useWrittenFilter } from "@/lib/patternArticles";
import type { CrossCheck, Finding, Findings, Interpretation, RPattern, Verdict } from "./typer";
import { Chip, LEVELS, LEVEL_RANK, LanguageCell, LevelBadge, MaterialCell, Score, SortTh, StoneLinks, TH_ROW, VERDICT_STYLE, useSorted } from "./gemensamt";

const pageLabel = (p: string) => (p.startsWith("pdf ") ? `pdf-sida ${p.slice(4)}` : `s. ${p}`);

const CC_STYLE: Record<string, string> = {
  "finns redan": "bg-sky-50 text-sky-800 border-sky-200",
  "nämns": "bg-sky-50 text-sky-800 border-sky-200",
  "annan ristare": "bg-rose-50 text-rose-800 border-rose-200",
  "samma som": "bg-[#b7410e]/5 text-[#9a350b] border-[#b7410e]/25",
  "saknas": "bg-emerald-50 text-emerald-800 border-emerald-200",
};

// A stone can have several findings by the same method (two family links, two filled gaps), so the row id also needs
// what tells them apart; it is the React key, the open state and the interpretation cache key
function findingId(f: Finding): string {
  const x = f as Finding & { linked?: string; gap?: { carved?: string } };
  return [f.signum, f.method, f.suggested ?? "", x.linked ?? "", x.gap?.carved ?? "", f.ours].join("|");
}

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

function PatternsBox({ patterns: all }: { patterns: RPattern[] }) {
  const { shown: patterns, written } = useWrittenFilter(all);
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
        <HideWrittenToggle written={written} />
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

export function FindingsPanel({ data, loggedIn, onRefresh }: { data: Findings; loggedIn: boolean; onRefresh: () => void }) {
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
  const [notInLiterature, setNotInLiterature] = useState(false);
  const [level, setLevel] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const methods = Object.keys(data.summary.by_method);
  const rows = useMemo(() => data.findings.filter(f =>
    (!verdict || f.verdict === verdict) && (!method || f.method === method)
    && (!onlyLikely || f.assessment.startsWith("Sannolikt ny") || f.assessment === "Värd en omprövning")
    && (!onlySignificant || f.significance?.significant === true)
    && (!notInLiterature || !f.literature)
    && (!level || f.interpretation?.level === level)),
  [data.findings, verdict, method, onlyLikely, onlySignificant, notInLiterature, level]);
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
        <button onClick={() => setNotInLiterature(!notInLiterature)} aria-pressed={notInLiterature}
          className={`px-3 py-1.5 rounded-xl border text-xs font-bold ${notInLiterature ? "bg-[#b7410e] border-[#b7410e] text-white" : "bg-white border-slate-300 text-[#9a350b] hover:bg-[#b7410e]/5"}`}>
          <Tip text="Döljer fynd på stenar som diskuteras i någon avhandling eller utgåva i litteraturregistret. Det som blir kvar har ingen litteratur att läsa först – i de verk registret har.">
            Inte i litteraturen ({data.findings.filter(f => !f.literature).length})
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
              const id = findingId(f);
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
const interpretations = new Map<string, Interpretation>();
const LEVEL_STYLE: Record<string, string> = {
  starkt: "border-emerald-300 bg-emerald-50/60", "måttligt": "border-sky-300 bg-sky-50/60", svagt: "border-slate-300 bg-slate-50",
  "redan känt": "border-slate-300 bg-slate-50", metodfel: "border-amber-300 bg-amber-50/60", "bekräftelse": "border-emerald-200 bg-white",
};

// A reasoned reading of the finding, weighing its evidence against the other methods and newer sources
function InterpretationBox({ f }: { f: Finding }) {
  const key = `${findingId(f)}|${f.crosscheck?.status ?? ""}`;
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
        {it.level !== "ej tillämplig" && <span className="text-[11px] text-slate-500">· {it.support} andra belägg för, {it.against} emot</span>}
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
            {f.literature && <Chip label="Litteratur" title="Stenen diskuteras i avhandlingar eller utgåvor i litteraturregistret – läs sidorna innan fyndet kallas nytt.">
              <span translate="no">{f.literature.works.slice(0, 2).map(w => `${w.author} ${w.year}`).join(", ")}{f.literature.n_works > 2 ? ` +${f.literature.n_works - 2}` : ""}</span></Chip>}
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
            {f.literature && (
              <div className="mt-3 pt-3 border-t border-slate-900/5 space-y-1">
                <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500">Litteraturen om stenen</div>
                <ul className="space-y-0.5">
                  {f.literature.works.map(w => (
                    <li key={w.id}><span className="font-semibold" translate="no">{w.author} {w.year}</span>, <span className="italic" translate="no">{w.title}</span>:{" "}
                      {w.pages.map(p => (w.entry_pages.includes(p) ? `${pageLabel(p)} (stenens artikel)` : pageLabel(p))).join(", ")}</li>
                  ))}
                </ul>
                <Link href={`/inskrifter?signum=${encodeURIComponent(f.signum)}`} className="text-[#b7410e] hover:underline">Utdragen på stenens sida</Link>
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
