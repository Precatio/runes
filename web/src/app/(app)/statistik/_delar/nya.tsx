"use client";
// "Nya mönster i datan": the patterns that appeared or changed status in the last 30 days (src/pattern_registry.py),
// catalogued – a summary, filters on state and topic, grouped by topic, compact cards with the robustness ladder as a
// meter and the full pattern folded away.
import { useMemo, useState, useSyncExternalStore } from "react";
import { PatternBody, type Pattern } from "@/components/PatternCard";
import { Tip } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import type { Corpus, Tab } from "./typer";
import { PATTERN_TOPICS, TOPIC } from "./gemensamt";

type State = "bekräftat" | "obekräftat" | "ändrat";
const STATE: Record<State, { label: string; help: string; pill: string; dot: string; short: string }> = {
  "bekräftat": { label: "Nytt · bekräftat", help: "Nytt och bekräftat: håller i båda halvorna av korpusen och klarar den gemensamma justeringen över alla mönster.",
    pill: "border-[#b7410e]/40 bg-[#b7410e] text-white", dot: "bg-[#b7410e]", short: "Bekräftade" },
  "obekräftat": { label: "Nytt · obekräftat", help: "Nytt men inte bekräftat: håller inte i båda halvorna, klarar inte den gemensamma justeringen, eller går inte att pröva i halvor.",
    pill: "border-dashed border-[#b7410e]/40 bg-white text-[#9a350b]", dot: "bg-[#b7410e]/40", short: "Obekräftade" },
  "ändrat": { label: "Ändrad status", help: "Mönstret fanns redan men har bytt status de senaste 30 dagarna.",
    pill: "border-slate-300 bg-slate-50 text-slate-700", dot: "bg-slate-400", short: "Ändrade" },
};
const stateOf = (p: Pattern): State => (p.new === "ändrat" ? "ändrat" : p.new === "obekräftat" ? "obekräftat" : "bekräftat");
const ORDER: State[] = ["bekräftat", "obekräftat", "ändrat"];
// The research status as a dot: agrees with research, a pattern to test, or weaker
const STATUS_DOT: Record<string, string> = { "bekräftar": "bg-emerald-500", "mönster att pröva": "bg-amber-500" };
const PER_TOPIC = 3;  // cards per topic before "Visa alla"

const firstSentence = (t: string) => { const s = t.split(/(?<=[a-zåäö0-9)])\.\s/)[0].trim(); return /[.!?]$/.test(s) ? s : `${s}.`; };
const tabOf = (topic: string) => (Object.entries(PATTERN_TOPICS).find(([, ts]) => ts.includes(topic))?.[0] ?? "overview") as Tab;
const fmtQ = (q?: number | null) => (q == null ? null : q < 0.001 ? "q < 0,001" : `q ${q.toLocaleString("sv-SE", { maximumFractionDigits: 3 })}`);
const day = (d?: string | null) => (d ? d.slice(0, 10) : "");

// The chosen filters live in localStorage (per viewer), read like the other saved choices (lib/patternArticles.ts)
const KEY = "vitki.nya-monster";
const listeners = new Set<() => void>();
const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };
function useStored<T>(name: string, initial: T): [T, (v: T) => void] {
  const raw = useSyncExternalStore(subscribe, () => { try { return localStorage.getItem(`${KEY}.${name}`); } catch { return null; } }, () => null);
  let v = initial;
  try { if (raw != null) v = JSON.parse(raw) as T; } catch { /* a value from an older version */ }
  const set = (x: T) => {
    try { localStorage.setItem(`${KEY}.${name}`, JSON.stringify(x)); } catch { /* blocked storage: lasts until reload */ }
    listeners.forEach(fn => fn());
  };
  return [v, set];
}

/** The ladder as a row of small segments: green holds, red fails, grey not tested. */
function LadderMeter({ pt }: { pt: Pattern }) {
  const l = pt.ladder;
  if (!l) return <span className="text-[11px] text-slate-400" title="Mönstret prövas på annat sätt än med robusthetstrappan.">egen prövning</span>;
  return (
    <span className="inline-flex items-center gap-1.5" title={l.rungs.map(r => `${r.holds === true ? "✓" : r.holds === false ? "✗" : "–"} ${r.label}`).join("\n")}>
      <span className="inline-flex gap-[2px]" aria-hidden>
        {l.rungs.map(r => (
          <span key={r.key} className={`h-2.5 w-1.5 rounded-[2px] ${r.holds === true ? "bg-emerald-500" : r.holds === false ? "bg-rose-400" : "bg-slate-200"}`} />
        ))}
      </span>
      <span className="text-[11px] font-semibold text-slate-600 tabular-nums">{l.passed}/{l.tested}</span>
      <span className="sr-only">Robusthetstrappan: håller i {l.passed} av {l.tested} steg</span>
    </span>
  );
}

function Card({ pt, onOpen }: { pt: Pattern; onOpen: (t: Tab) => void }) {
  const [open, setOpen] = useState(false);
  const st = STATE[stateOf(pt)];
  const q = fmtQ(pt.q_global);
  const diff = pt.ladder?.effect?.diff;
  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm hover:border-[#b7410e]/40 transition-colors flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded-lg border text-[11px] font-bold ${st.pill}`} title={st.help}>{st.label}</span>
        <span className="ml-auto text-[11px] text-slate-400 tabular-nums whitespace-nowrap">
          {pt.new === "ändrat" ? `ändrat ${day(pt.status_changed)}` : day(pt.first_seen)}
        </span>
      </div>
      <p className="text-sm text-slate-800 leading-snug">{firstSentence(pt.text)}</p>
      {pt.new === "ändrat" && pt.previous_status && (
        <p className="text-[11px] text-slate-500">Förut: {pt.previous_status} → nu: {pt.status}</p>
      )}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
        <span className="inline-flex items-center gap-1" title="Mönstrets status i Statistik: stämmer det med forskningen, är det nytt att pröva, eller en antydan?">
          <span className={`h-2 w-2 rounded-full ${STATUS_DOT[pt.status] ?? "bg-slate-400"}`} aria-hidden />
          <Tip text={GLOSSARY[pt.status]}>{pt.status}</Tip>
        </span>
        <LadderMeter pt={pt} />
        {diff != null && <span className="tabular-nums" title="Skillnaden i procentenheter, med landskap och tid konstanta.">{diff > 0 ? "+" : "−"}{Math.abs(Math.round(diff * 100))} procentenheter</span>}
        {q && <span className="tabular-nums" title="Efter den gemensamma justeringen (Benjamini–Hochberg) över alla mönster på sidan.">{q} alla mönster</span>}
      </div>
      <div className="flex items-center gap-3 pt-1 border-t border-slate-100">
        <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
          className="text-xs font-semibold text-slate-600 hover:text-slate-900">{open ? "Dölj detaljer" : "Visa detaljer"}</button>
        <button type="button" onClick={() => onOpen(tabOf(pt.topic))}
          className="ml-auto text-xs font-semibold text-[#9a350b] hover:underline">Öppna {TOPIC[tabOf(pt.topic)] ?? pt.topic} →</button>
      </div>
      {open && <div className="pt-1"><PatternBody pt={{ ...pt, text: pt.text.slice(firstSentence(pt.text).length).trim() }} /></div>}
    </li>
  );
}

/** The new and changed patterns, catalogued: summary, filters, groups by topic. */
export function NewPatterns({ data, onOpen }: { data: Corpus; onOpen: (t: Tab) => void }) {
  const fresh = useMemo(() => (data.patterns ?? []).filter(p => p.new), [data.patterns]);
  const [state, setState] = useStored<State | "alla">("state", "alla");
  const [topic, setTopic] = useStored<string>("topic", "alla");
  const [collapsed, setCollapsed] = useStored<boolean>("collapsed", false);
  const [expanded, setExpanded] = useState<string[]>([]);
  const counts = useMemo(() => Object.fromEntries(ORDER.map(s => [s, fresh.filter(p => stateOf(p) === s).length])) as Record<State, number>, [fresh]);
  const topics = useMemo(() => {
    const c = new Map<string, number>();
    fresh.forEach(p => c.set(p.topic, (c.get(p.topic) ?? 0) + 1));
    return [...c.entries()].sort((a, b) => b[1] - a[1]);
  }, [fresh]);
  if (!fresh.length) return null;
  const shown = fresh.filter(p => (state === "alla" || stateOf(p) === state) && (topic === "alla" || p.topic === topic));
  // Confirmed first, then the most robust, then the newest
  const rank = (p: Pattern) => [ORDER.indexOf(stateOf(p)), -((p.ladder?.passed ?? 0) / Math.max(1, p.ladder?.tested ?? 1)), -(Date.parse(p.first_seen ?? "") || 0)];
  const cmp = (a: Pattern, b: Pattern) => { const x = rank(a), y = rank(b); for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return x[i] - y[i]; return 0; };
  const groups = topics.map(([t]) => [t, shown.filter(p => p.topic === t).sort(cmp)] as const).filter(([, ps]) => ps.length);
  const chip = (active: boolean) => `px-3 py-1.5 rounded-xl border text-xs font-semibold transition-colors ${active
    ? "bg-slate-900 border-slate-900 text-white" : "bg-white border-slate-200 text-slate-700 hover:border-[#b7410e]/40"}`;

  return (
    <section aria-label="Nya mönster" className="rounded-[24px] border border-[#b7410e]/25 bg-[#b7410e]/[0.03] p-4 md:p-6 space-y-4">
      <div className="flex flex-wrap items-start gap-3">
        <div className="flex-1 min-w-[16rem]">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#7c2d0a]">Nya mönster i datan</h3>
          <p className="text-xs text-[#7c2d0a]/80 mt-1 max-w-3xl">
            Mönster som dykt upp eller bytt status de senaste 30 dagarna. Ett nytt mönster är <strong>bekräftat</strong> när det håller i båda
            halvorna av korpusen och klarar den gemensamma justeringen över alla mönster.
          </p>
        </div>
        <button type="button" onClick={() => setCollapsed(!collapsed)} aria-expanded={!collapsed}
          className="px-3 py-1.5 rounded-xl border border-[#b7410e]/25 bg-white text-xs font-semibold text-[#7c2d0a] hover:border-[#b7410e]/60">
          {collapsed ? `Visa alla ${fresh.length}` : "Fäll ihop"}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-2 md:gap-3">
        {ORDER.map(s => (
          <button key={s} type="button" onClick={() => { setState(state === s ? "alla" : s); setCollapsed(false); }} aria-pressed={state === s}
            title={STATE[s].help}
            className={`text-left rounded-2xl border p-2.5 md:p-3 transition-colors ${state === s ? "border-[#b7410e] bg-white ring-2 ring-[#b7410e]/25" : "border-[#b7410e]/15 bg-white/80 hover:border-[#b7410e]/40"}`}>
            <div className="flex items-center gap-1.5 text-[10px] md:text-[11px] font-bold uppercase tracking-wide md:tracking-wider text-slate-500">
              <span className={`h-2 w-2 shrink-0 rounded-full ${STATE[s].dot}`} />{STATE[s].short}
            </div>
            <div className="text-2xl font-bold text-slate-900 tabular-nums">{counts[s]}</div>
          </button>
        ))}
      </div>

      {!collapsed && (
        <>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Ämne">
            <button type="button" className={chip(topic === "alla")} aria-pressed={topic === "alla"} onClick={() => setTopic("alla")}>
              Alla ämnen <span className="opacity-60">{fresh.length}</span>
            </button>
            {topics.map(([t, n]) => (
              <button key={t} type="button" className={chip(topic === t)} aria-pressed={topic === t} onClick={() => setTopic(topic === t ? "alla" : t)}>
                {t} <span className="opacity-60">{n}</span>
              </button>
            ))}
            {(state !== "alla" || topic !== "alla") && (
              <button type="button" onClick={() => { setState("alla"); setTopic("alla"); }} className="px-2 text-xs font-semibold text-[#9a350b] hover:underline">
                Rensa filter
              </button>
            )}
          </div>

          {groups.length === 0 && <p className="text-sm text-slate-600">Inga mönster med det filtret.</p>}
          <div className="space-y-5">
            {groups.map(([t, ps]) => (
              <div key={t} className="space-y-2">
                <div className="flex items-baseline gap-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">{t}</h4>
                  <span className="text-[11px] text-slate-500">{ps.length} {ps.length === 1 ? "mönster" : "mönster"}</span>
                  <span className="flex-1 border-t border-[#b7410e]/15" />
                </div>
                <ul className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                  {(expanded.includes(t) || topic === t ? ps : ps.slice(0, PER_TOPIC)).map(p => <Card key={`${p.topic}|${p.key}`} pt={p} onOpen={onOpen} />)}
                </ul>
                {ps.length > PER_TOPIC && topic !== t && (
                  <button type="button" onClick={() => setExpanded(expanded.includes(t) ? expanded.filter(x => x !== t) : [...expanded, t])}
                    className="text-xs font-semibold text-[#9a350b] hover:underline">
                    {expanded.includes(t) ? `Visa färre i ${t}` : `Visa alla ${ps.length} i ${t}`}
                  </button>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
