"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { corpus } from "@/lib/corpus";
import { db } from "@/lib/db";
import { useAuth } from "@/components/AuthContext";

interface ProvinceRow {
  code: string; name: string; axelson: boolean; total: number; carver: number; style: number; dated: number;
  uncertain_interpretation: number; lost: number; measured: number;
}
interface Hypothesis {
  signum: string; place: string; province: string; style: string | null; carver: string; similarity: number;
  margin: number; runner_up: string; n_words: number; in_carver_area: boolean; carver_area: string[];
  carver_precision: number | null; short_text: boolean; attributed_to?: string[];
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
interface Finding {
  signum: string; place: string; province: string; method: string; verdict: Verdict; ours: string; existing: string;
  evidence: number; novelty: number; relevance: number; score: number; assessment: string; suggested?: string;
  reasons: { belägg: string[]; nyhet: string[]; relevans: string[] };
}
interface Findings {
  findings: Finding[];
  summary: { counts: Record<Verdict, number>; by_method: Record<string, Partial<Record<Verdict, number>>>; likely_new: number };
  technique_note: string | null;
  method_note: string;
}

type Tab = "findings" | "hypotheses" | "reconsider" | "priorities" | "uninterpreted" | "style";

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
    <th className="p-2 whitespace-nowrap" title={title}>
      <button onClick={() => setSort(s => ({ key, desc: s.key === key ? !s.desc : rows.length > 0 && typeof get[key](rows[0]) !== "string" }))}
        className={`uppercase tracking-wider hover:text-slate-900 ${sort.key === key ? "text-slate-900" : ""}`}>
        {label}{sort.key === key ? (sort.desc ? " ↓" : " ↑") : ""}
      </button>
    </th>
  );
  return { sorted, header };
}

const VERDICT_STYLE: Record<Verdict, string> = {
  "stämmer": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "nytt": "bg-sky-50 text-sky-800 border-sky-200",
  "motsäger": "bg-amber-50 text-amber-900 border-amber-200",
};

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

function StoneLinks({ signum }: { signum: string }) {
  return (
    <span className="whitespace-nowrap text-xs">
      <Link href={`/inskrifter?signum=${encodeURIComponent(signum)}`} className="font-bold text-slate-900 hover:text-[#b7410e]">{signum}</Link>
      <Link href={`/3d?signum=${encodeURIComponent(signum)}`} className="ml-2 text-[#b7410e] hover:underline">mät i 3D</Link>
    </span>
  );
}

export default function GapsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<Gaps | null>(null);
  const [found, setFound] = useState<Findings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("findings");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      let entries: Awaited<ReturnType<typeof corpus.list>> = [];
      if (user) {
        try { entries = await corpus.list(); } catch { /* corpus optional */ }
      }
      // AI style assessments saved in the user's own projects
      const styles = (await db.getProjects().catch(() => []))
        .filter(p => p.metaText && p.twoDResults?.predicted_style)
        .map(p => ({ signum: p.metaText, style: p.twoDResults!.predicted_style, confidence: p.twoDResults!.confidence }));
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
            corpus: entries.map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means })), styles,
          }),
        ]);
        if (!cancelled) { setData(gaps); setFound(findings); }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Kunde inte hämta översikten.");
      }
    })();
    return () => { cancelled = true; };
  }, [user]);

  if (error) return <div className="max-w-3xl mx-auto p-8 text-red-700 font-semibold">{error}</div>;
  if (!data || !found) return <div className="max-w-3xl mx-auto p-8 text-slate-500">Beräknar översikten …</div>;

  const t = data.coverage.totals;
  const tabs: [Tab, string, number][] = [
    ["findings", "Våra resultat mot forskningen", found.findings.length],
    ["hypotheses", "Ortografiska hypoteser", data.hypotheses.new.length],
    ["reconsider", "Ompröva attribuering", data.hypotheses.reconsider.length],
    ["priorities", "Mätningar som gör mest nytta", data.measurement_priorities.length],
    ["uninterpreted", "Osäkert tolkade", data.open_questions.uninterpreted.count],
    ["style", "Osäker stilgrupp", data.open_questions.uncertain_style.count],
  ];

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Forskningsluckor</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Var saknas uppgifter om de svenska vikingatida runstenarna, var kan nya mätningar och analyser göra skillnad –
          och vad säger appens egna resultat jämfört med den befintliga forskningen? Klicka på en kolumnrubrik för att sortera.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          ["Runstenar", `${t.total}`, ""],
          ["Med ristare", `${pct(t.carver, t.total)} %`, `${t.total - t.carver} saknar`],
          ["Med säker stilgrupp", `${pct(t.style, t.total)} %`, `${t.total - t.style} saknar`],
          ["Daterade med årtal", `${t.dated}`, `${pct(t.dated, t.total)} %`],
          ["Uppmätta i korpusen", `${t.measured}`, user ? "" : "logga in för att se"],
        ].map(([label, value, sub]) => (
          <div key={label} className="liquid-glass-island rounded-[24px] p-5">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
            <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
            {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
          </div>
        ))}
      </div>

      <div className="rounded-2xl bg-amber-50 border border-amber-200 px-5 py-3 text-sm text-amber-900">
        <strong>Läs med källkritik:</strong> {data.source_note}
      </div>

      <ProvinceTable rows={data.coverage.per_province} />

      <div className="flex flex-wrap gap-2">
        {tabs.map(([key, label, n]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2 rounded-xl text-sm font-bold border ${tab === key ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
            {label} <span className="opacity-60">({n})</span>
          </button>
        ))}
      </div>

      <div className="liquid-glass-island rounded-[32px] p-5">
        {tab === "findings" && <FindingsPanel data={found} loggedIn={!!user} />}
        {(tab === "hypotheses" || tab === "reconsider") && (
          <HypothesisTable key={tab} reconsider={tab === "reconsider"} ev={data.hypotheses.evaluation}
            rows={tab === "hypotheses" ? data.hypotheses.new : data.hypotheses.reconsider} />
        )}
        {tab === "priorities" && <PrioritiesPanel rows={data.measurement_priorities} />}
        {(tab === "uninterpreted" || tab === "style") && (
          <BriefTable key={tab} uninterpreted={tab === "uninterpreted"}
            rows={(tab === "uninterpreted" ? data.open_questions.uninterpreted : data.open_questions.uncertain_style).items} />
        )}
      </div>
      <p className="text-[11px] text-slate-500">{data.attribution}</p>
    </div>
  );
}

const TH_ROW = "text-left text-[11px] uppercase tracking-wider text-slate-500";

function ProvinceTable({ rows }: { rows: ProvinceRow[] }) {
  const { sorted, header } = useSorted(rows, {
    name: r => r.name, total: r => r.total, carver: r => r.carver / r.total, style: r => r.style / r.total,
    uncertain: r => r.uncertain_interpretation, lost: r => r.lost, measured: r => r.measured,
  }, { key: "total", desc: true });
  return (
    <div className="liquid-glass-island rounded-[32px] p-4 overflow-x-auto">
      <table className="w-full text-sm">
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
              <td className="p-2">{r.total}</td>
              <td className="p-2"><Bar value={r.carver} total={r.total} color="#b7410e" /></td>
              <td className="p-2"><Bar value={r.style} total={r.total} color="#0369a1" /></td>
              <td className="p-2">{r.uncertain_interpretation}</td>
              <td className="p-2">{r.lost}</td>
              <td className="p-2">{r.measured}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FindingsPanel({ data, loggedIn }: { data: Findings; loggedIn: boolean }) {
  const [verdict, setVerdict] = useState<Verdict | "">("");
  const [method, setMethod] = useState("");
  const [onlyLikely, setOnlyLikely] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const methods = Object.keys(data.summary.by_method);
  const rows = useMemo(() => data.findings.filter(f =>
    (!verdict || f.verdict === verdict) && (!method || f.method === method)
    && (!onlyLikely || f.assessment.startsWith("Sannolikt ny") || f.assessment === "Värd en omprövning")),
  [data.findings, verdict, method, onlyLikely]);
  const { sorted, header } = useSorted(rows, {
    signum: f => f.signum, place: f => f.place, method: f => f.method, verdict: f => f.verdict,
    suggested: f => f.suggested, existing: f => f.existing, evidence: f => f.evidence, novelty: f => f.novelty,
    relevance: f => f.relevance, score: f => f.score, assessment: f => f.assessment,
  }, { key: "score", desc: true });
  const c = data.summary.counts;
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        Appens analyser ställda mot Rundata, som här står för den publicerade forskningen: ortografisk stilometri
        (alla inskrifter, stenen själv utesluten ur ristarprofilen), huggteknik i mätkorpusen och AI-bedömd stilgrupp
        från bilder i dina projekt. <strong>Uppskattningen</strong> väger belägg × nyhet × relevans (0–100) och är en
        tumregel för att prioritera – inte en granskning av litteraturen. Klicka på en rad för att se skälen.
      </p>
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
        <span className="text-slate-500">{sorted.length} fynd</span>
        {data.technique_note && <span className="text-amber-800 text-xs">{data.technique_note}{!loggedIn && " Logga in för att ta med mätkorpusen."}</span>}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className={TH_ROW}>
              {header("signum", "Sten")}{header("method", "Metod")}{header("verdict", "Mot forskningen")}
              {header("suggested", "Vårt resultat")}{header("existing", "Rundata")}
              {header("evidence", "Belägg", "Hur pålitlig analysen är i just detta fall")}
              {header("novelty", "Nyhet", "Hur mycket fyndet tillför jämfört med Rundata")}
              {header("relevance", "Relevans", "Landskapets kunskapsläge, ristarens betydelse, om stenen finns kvar")}
              {header("score", "Uppskattning")}{header("assessment", "Bedömning")}
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
        </table>
        {sorted.length > 300 && <p className="text-xs text-slate-500 mt-2">Visar de 300 första – sortera eller filtrera för att se fler.</p>}
      </div>
      <details className="mt-4 text-xs text-slate-600">
        <summary className="cursor-pointer font-semibold">Hur uppskattningen räknas</summary>
        <pre className="whitespace-pre-wrap font-sans mt-2">{data.method_note}</pre>
      </details>
    </>
  );
}

function FindingRow({ f, open, onToggle }: { f: Finding; open: boolean; onToggle: () => void }) {
  return (
    <>
      <tr className="border-t border-slate-900/5 cursor-pointer hover:bg-white/60" onClick={onToggle}>
        <td className="p-2"><StoneLinks signum={f.signum} /><div className="text-[11px] text-slate-500">{f.place}</div></td>
        <td className="p-2 text-xs">{f.method}</td>
        <td className="p-2"><span className={`px-2 py-0.5 rounded-lg border text-xs font-bold ${VERDICT_STYLE[f.verdict]}`}>{f.verdict}</span></td>
        <td className="p-2 text-xs max-w-[260px]">{f.ours}</td>
        <td className="p-2 text-xs">{f.existing}</td>
        <td className="p-2"><Score value={f.evidence} /></td>
        <td className="p-2"><Score value={f.novelty} /></td>
        <td className="p-2"><Score value={f.relevance} /></td>
        <td className="p-2"><Score value={f.score} /></td>
        <td className="p-2 text-xs font-semibold">{f.assessment}</td>
      </tr>
      {open && (
        <tr className="bg-white/50">
          <td colSpan={10} className="p-3 text-xs text-slate-700">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(["belägg", "nyhet", "relevans"] as const).map(k => (
                <div key={k}>
                  <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500 mb-1">{k}</div>
                  <ul className="list-disc pl-4 space-y-0.5">{f.reasons[k].map((r, i) => <li key={i}>{r}</li>)}</ul>
                </div>
              ))}
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
    similarity: h => h.similarity, margin: h => h.margin, precision: h => h.carver_precision,
    area: h => h.in_carver_area, words: h => h.n_words,
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
        <table className="w-full text-sm">
          <thead>
            <tr className={TH_ROW}>
              {header("signum", "Sten")}{header("place", "Plats")}
              {reconsider && header("attributed", "Rundata")}
              {header("carver", "Ortografin pekar mot")}{header("similarity", "Likhet")}{header("margin", "Marginal")}
              {header("precision", "Precision")}{header("area", "Inom ristarens område")}{header("words", "Ord")}
            </tr>
          </thead>
          <tbody>
            {sorted.map(h => (
              <tr key={h.signum} className="border-t border-slate-900/5">
                <td className="p-2"><StoneLinks signum={h.signum} /></td>
                <td className="p-2 text-slate-600">{h.place}</td>
                {reconsider && <td className="p-2">{h.attributed_to?.join(", ")}</td>}
                <td className="p-2 font-semibold">{h.carver} <span className="text-slate-400 font-normal">(sedan {h.runner_up})</span></td>
                <td className="p-2 font-mono text-xs">{fmt(h.similarity)}</td>
                <td className="p-2 font-mono text-xs">{fmt(h.margin)}</td>
                <td className="p-2 font-mono text-xs">{h.carver_precision != null ? `${Math.round(h.carver_precision * 100)} %` : "–"}</td>
                <td className="p-2 text-xs">{h.in_carver_area ? "Ja" : <span className="text-amber-700">Nej ({h.carver_area.join(", ")}) – kan vara regional stavning</span>}</td>
                <td className="p-2 text-xs">{h.n_words}{h.short_text && <span className="text-amber-700"> kort</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
          : "Bevarade runstenar där stilgruppen är osäker (?) i Rundata. En 2D-stilanalys av foto eller ristningskarta kan ge underlag – AI:ns bedömning är dock okalibrerad."}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className={TH_ROW}>{header("signum", "Sten")}{header("place", "Plats")}{header("province", "Landskap")}{header("style", "Stil")}{header("dating", "Datering")}{header("carvers", "Ristare")}</tr></thead>
          <tbody>
            {sorted.slice(0, 200).map(b => (
              <tr key={b.signum} className="border-t border-slate-900/5">
                <td className="p-2"><StoneLinks signum={b.signum} /></td>
                <td className="p-2 text-slate-600">{b.place}</td>
                <td className="p-2">{b.province}</td>
                <td className="p-2">{b.style ?? "–"}</td>
                <td className="p-2">{b.dating || "–"}</td>
                <td className="p-2">{b.carvers.join(", ") || "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
