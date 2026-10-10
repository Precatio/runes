"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { corpus } from "@/lib/corpus";
import { db } from "@/lib/db";
import { useAuth } from "@/components/AuthContext";
import { GeologyBox, LanguageTraits } from "@/components/StoneContext";
import { SIMILARITY_HELP, fmtP } from "@/lib/significance";

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
  signum: string; place: string; province: string; method: string; verdict: Verdict; ours: string; existing: string;
  evidence: number; novelty: number; relevance: number; score: number; assessment: string; suggested?: string;
  reasons: { belägg: string[]; nyhet: string[]; relevans: string[] };
  crosscheck?: CrossCheck;
}
// The suggestion checked against newer sources (Runor 2020, Wikidata)
interface CrossCheck {
  status: "finns redan" | "nämns" | "annan ristare" | "samma som" | "saknas" | "ej kontrollerad";
  runor?: { status: string; text: string; references: string[]; url?: string | null };
  wikidata?: { text: string };
}
interface RPattern { topic: string; status: string; text: string; note?: string | null }
interface Findings {
  r_patterns?: RPattern[];
  r_ready?: boolean;
  findings: Finding[];
  summary: { counts: Record<Verdict, number>; by_method: Record<string, Partial<Record<Verdict, number>>>; likely_new: number };
  technique_note: string | null;
  method_note: string;
}

type Tab = "findings" | "categories" | "size" | "hypotheses" | "reconsider" | "priorities" | "uninterpreted" | "style";

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
  const tabs: [Tab, string, number][] = [
    ["findings", "Våra resultat mot forskningen", found.findings.length],
    ["categories", "Inskrifternas syfte per ristare", 9],
    ["size", "Storlek och syfte", 1],
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
          ["Runstenar", `${t.total}`, "", gapHref("runestone")],
          ["Med ristare", `${pct(t.carver, t.total)} %`, `${t.total - t.carver} saknar`, gapHref("no_carver")],
          ["Med säker stilgrupp", `${pct(t.style, t.total)} %`, `${t.total - t.style} saknar`, gapHref("no_style")],
          ["Daterade med årtal", `${t.dated}`, `${pct(t.dated, t.total)} %`, gapHref("dated")],
          ["Uppmätta i korpusen", `${t.measured}`, user ? "" : "logga in för att se", measuredSigna.length ? signaHref(measuredSigna) : ""],
        ].map(([label, value, sub, href]) => {
          const body = (
            <>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
              <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
              {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
            </>
          );
          return href
            ? <Link key={label} href={href} className="liquid-glass-island rounded-[24px] p-5 hover:ring-2 hover:ring-slate-900/20 transition">{body}</Link>
            : <div key={label} className="liquid-glass-island rounded-[24px] p-5">{body}</div>;
        })}
      </div>

      <div className="rounded-2xl bg-amber-50 border border-amber-200 px-5 py-3 text-sm text-amber-900">
        <strong>Läs med källkritik:</strong> {data.source_note}
      </div>

      <ProvinceTable rows={data.coverage.per_province} measuredSigna={measuredSigna} />

      <div className="flex flex-wrap gap-2">
        {tabs.map(([key, label, n]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2 rounded-xl text-sm font-bold border ${tab === key ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
            {label} <span className="opacity-60">({n})</span>
          </button>
        ))}
      </div>

      <div className="liquid-glass-island rounded-[32px] p-5">
        {tab === "findings" && <FindingsPanel data={found} loggedIn={!!user} onRefresh={() => setReload(r => r + 1)} />}
        {tab === "categories" && <CategoryPanel />}
        {tab === "size" && <SizePanel />}
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
  return (
    <div className="space-y-5 text-sm">
      <p className="text-slate-600 max-w-4xl">
        Restes större stenar för större syften och av mäktigare personer? Höjden för {data.n} av {data.meta.n_runestones}{" "}
        vikingatida runstenar kunde läsas ur Kulturmiljöregistret (median {fmt(data.median_height_m)} m, kvartiler{" "}
        {fmt(data.quartiles_m[0])}–{fmt(data.quartiles_m[1])} m; fragment uteslutna). Alla jämförelser görs <em>inom landskap</em>{" "}
        (bergart och lokal sed påverkar storleken): skillnaden anges som hur mycket högre eller lägre stenarna är, med
        permutationstest inom landskap och q-värden korrigerade för antalet test.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead><tr><th className="p-2 text-left text-[11px] uppercase text-slate-500">Variabel</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Stenar</th>
            <th className="p-2 text-left text-[11px] uppercase text-slate-500">Höjd mot övriga (inom landskap)</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Median med / utan</th>
            <th className="p-2 text-left text-[11px] uppercase text-slate-500">p</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">q</th></tr></thead>
          <tbody>{data.tests.map(t => (
            <tr key={t.variable} className={`border-t border-slate-900/5 ${sig(t.q)}`}>
              <td className="p-2">{t.variable}</td><td className="p-2">{t.n}</td><td className="p-2">{ratio(t.ratio)}</td>
              <td className="p-2">{fmt(t.median_with_m)} / {fmt(t.median_without_m)} m</td><td className="p-2">{fmtP(t.p)}</td><td className="p-2">{fmtP(t.q)}</td>
            </tr>
          ))}</tbody>
        </table>
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
          <table className="w-full">
            <thead><tr><th className="p-2 text-left text-[11px] uppercase text-slate-500">Ristare</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Stenar</th>
              <th className="p-2 text-left text-[11px] uppercase text-slate-500">Median</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">Höjd mot andra i landskapet</th>
              <th className="p-2 text-left text-[11px] uppercase text-slate-500">p</th><th className="p-2 text-left text-[11px] uppercase text-slate-500">q</th></tr></thead>
            <tbody>{data.carvers.map(c => (
              <tr key={c.carver} className={`border-t border-slate-900/5 ${sig(c.q)}`}>
                <td className="p-2"><Link href={`/inskrifter?carver=${encodeURIComponent(c.carver)}`} className="text-[#b7410e] hover:underline">{c.carver}</Link></td>
                <td className="p-2">{c.n}</td><td className="p-2">{fmt(c.median_m)} m</td><td className="p-2">{ratio(c.ratio)}</td><td className="p-2">{fmtP(c.p)}</td><td className="p-2">{fmtP(c.q)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-xs text-amber-900 space-y-1">
        <p><strong>Läs med källkritik.</strong> Höjden är oftast höjden över mark i Kulturmiljöregistrets beskrivning, inte stenens hela längd,
          och stenar har flyttats och rests om. Måtten finns för knappt hälften av stenarna; fornlämningar med flera stenar som inte går
          att skilja åt är uteslutna. Stenar där minnesformeln inte går att läsa är oftare skadade och därför lägre. Statusorden är grova
          mått på makt – betydelsen av t.ex. <em>drengr</em> och <em>þegn</em> är omdiskuterad. Källa: {data.source}</p>
      </div>
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
  return (
    <>
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
        <table className="w-full text-sm">
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
        </table>
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
      </table>
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

function PatternsBox({ patterns }: { patterns: RPattern[] }) {
  const style: Record<string, string> = {
    "bekräftar": "bg-emerald-50 text-emerald-800 border-emerald-200",
    "mönster att pröva": "bg-amber-50 text-amber-900 border-amber-200",
    "begränsning": "bg-slate-100 text-slate-700 border-slate-300", "svagt": "bg-slate-100 text-slate-700 border-slate-300",
  };
  return (
    <details open className="mb-5 rounded-2xl border border-slate-200 bg-white/70 p-4">
      <summary className="cursor-pointer font-bold text-slate-900">Mönster i hela korpusen (statistik i R)
        <Link href="/statistik" className="ml-3 text-xs font-semibold text-[#b7410e] hover:underline">visa figurer och metod</Link>
      </summary>
      <ul className="mt-3 space-y-2 text-sm">
        {patterns.map((pt, i) => (
          <li key={i} className="flex gap-3">
            <span className={`shrink-0 h-fit px-2 py-0.5 rounded-lg border text-[11px] font-bold ${style[pt.status] ?? ""}`}>{pt.status}</span>
            <div><span className="text-[11px] uppercase tracking-wider text-slate-500 mr-2">{pt.topic}</span>{pt.text}
              {pt.note && <div className="text-xs text-slate-500 mt-0.5">{pt.note}</div>}</div>
          </li>
        ))}
      </ul>
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
    crosscheck: f => f.crosscheck?.status, material: f => f.material, language: f => (f.language?.comparable ? f.language.agree / f.language.comparable : null),
  }, { key: "score", desc: true });
  const c = data.summary.counts;
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        Appens analyser ställda mot Rundata (version 3.1, 2018), som här står för den publicerade forskningen: ortografisk
        stilometri (alla inskrifter, stenen själv utesluten ur ristarprofilen), huggteknik i mätkorpusen, AI-bedömd stilgrupp
        från bilder i dina projekt och – när statistiken i R är beräknad – attribueringsmodellen och Upplands seriation.
        Kolumnen <strong>Nyare källor</strong> visar om förslaget redan finns i Runor 2020 (RAÄ) eller Wikidata. <strong>Uppskattningen</strong> väger belägg × nyhet × relevans (0–100) och är en
        tumregel för att prioritera – inte en granskning av litteraturen. Klicka på en rad för att se skälen.
      </p>
      {data.r_patterns && data.r_patterns.length > 0 && <PatternsBox patterns={data.r_patterns} />}
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
        {data.r_ready && (
          <button onClick={crosscheck} disabled={checking}
            className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:bg-slate-50 disabled:opacity-50">
            {checking ? "Stämmer av …" : "Stäm av mot Runor 2020 och Wikidata"}
          </button>
        )}
        {checkError && <span className="text-xs text-red-700">{checkError}</span>}
        {data.technique_note && <span className="text-amber-800 text-xs">{data.technique_note}{!loggedIn && " Logga in för att ta med mätkorpusen."}</span>}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className={TH_ROW}>
              {header("signum", "Sten")}{header("method", "Metod")}{header("verdict", "Mot forskningen")}
              {header("suggested", "Vårt resultat")}{header("existing", "Rundata")}
              {header("crosscheck", "Nyare källor", "Förslaget i Runor 2020 (RAÄ) och Wikidata: finns redan, nämns, annan ristare, samma som en annan sten, saknas")}
              {header("material", "Bergart", "Stenens material i Rundata; ✓ = förekommer på den föreslagna ristarens stenar, ! = sällan")}
              {header("language", "Språkdrag", "Hur många jämförbara språkdrag (ljud och språkbruk) som stämmer med den föreslagna ristaren")}
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
        <td className="p-2"><CrossCheckCell cc={f.crosscheck} /></td>
        <td className="p-2 text-xs"><MaterialCell x={f} /></td>
        <td className="p-2 text-xs"><LanguageCell x={f} /></td>
        <td className="p-2"><Score value={f.evidence} /></td>
        <td className="p-2"><Score value={f.novelty} /></td>
        <td className="p-2"><Score value={f.relevance} /></td>
        <td className="p-2"><Score value={f.score} /></td>
        <td className="p-2 text-xs font-semibold">{f.assessment}</td>
      </tr>
      {open && (
        <tr className="bg-white/50">
          <td colSpan={13} className="p-3 text-xs text-slate-700">
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
                {f.suggested && f.method !== "stilgrupp (AI, bild)" ? <LanguageTraits signum={f.signum} carver={f.suggested} /> : <LanguageTraits signum={f.signum} />}
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
        <table className="w-full text-sm">
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
                <td className="p-2 text-slate-600">{h.place}</td>
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
