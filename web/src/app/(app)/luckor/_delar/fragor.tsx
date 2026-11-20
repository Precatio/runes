import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Answer } from "@/components/Explain";
import { API_URL } from "@/lib/api";
import { TONE, toggle } from "@/lib/tone";
import type { ResearchQuestion, ResearchQuestions } from "./typer";

// Öppna frågor i forskningen: the question list from the literature review (src/fragelista.py). INTERNAL steering
// document (PUBLICERINGSPLAN.md, "det vi behåller"): this card exists only in the local app – the public build removes
// web/src/app/(app), and the API is not on the website. The question texts come from the API and are never put in the
// i18n catalogue, so they stay untranslated and out of the public repository's language files.

const LEVEL_STYLE: Record<number, string> = { 1: TONE.fill, 2: TONE.tint, 3: TONE.outline, 4: TONE.neutral };
const STATE_STYLE: Record<ResearchQuestion["study_state"], string> = {
  "körd": TONE.fill, "låst plan": TONE.tint, "planerad": TONE.outline, "reservlista": TONE.neutral,
};
const STATE_HELP: Record<ResearchQuestion["study_state"], string> = {
  "körd": "Studien är körd; läget enligt publiceringsplanen står under frågan.",
  "låst plan": "Analysplanen är låst (sha256 och commit) men studien är inte körd.",
  "planerad": "Studien står i publiceringsplanen men har ingen låst plan än.",
  "reservlista": "Frågan står på reservlistan för populärspåret, utan egen studie.",
};
const FIRST = 40;

function InternalBanner({ note }: { note: string }) {
  return (
    <div className={`rounded-xl border px-4 py-3 text-sm ${TONE.tint}`} role="note">
      <span className="font-bold uppercase tracking-wider text-[11px] mr-2">Internt</span>{note}
    </div>
  );
}

function Sources({ q }: { q: ResearchQuestion }) {
  const [all, setAll] = useState(false);
  const shown = all ? q.sources : q.sources.slice(0, 3);
  if (!q.sources.length) return <p className="text-xs text-slate-500">Inga påståenden kopplade till frågan.</p>;
  return (
    <div className="text-xs">
      <ul className="space-y-1">
        {shown.map(s => (
          <li key={s.id}>
            <span className="font-semibold" translate="no">{s.author ?? "Okänd"} {s.year}</span>
            {s.title && <span className="italic" translate="no">, {s.title}</span>}
            <span className="text-slate-500" translate="no"> ({s.journal}{s.page ? `, ${s.page}` : ""})</span>
            {!s.page && <span className="text-slate-500"> – citatet hittades inte i texten, ingen sida</span>}
            {s.quote && <div className="text-slate-600" translate="no">»{s.quote}»</div>}
          </li>
        ))}
      </ul>
      {q.sources.length > 3 && (
        <button onClick={() => setAll(!all)} className="mt-1 font-semibold text-[#b7410e] hover:underline">
          {all ? "Visa färre källor" : `Visa alla ${q.sources.length} källor`}
        </button>
      )}
    </div>
  );
}

function QuestionCard({ q }: { q: ResearchQuestion }) {
  return (
    <li className="rounded-xl border border-slate-200 bg-white px-4 py-3">
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <span className="text-[11px] font-mono text-slate-500">nr {q.nr}</span>
        <span className={`px-2 py-0.5 rounded-lg border text-[11px] font-bold ${LEVEL_STYLE[q.level] ?? TONE.neutral}`}>{q.level_label}</span>
        <span className="text-[11px] uppercase tracking-wider text-slate-500" translate="no">{q.theme}</span>
        <span className={`ml-auto px-2 py-0.5 rounded-lg border text-[11px] font-bold ${STATE_STYLE[q.study_state]}`} title={STATE_HELP[q.study_state]}>
          {q.study_state}
        </span>
      </div>
      <div className="font-semibold text-slate-900" translate="no">{q.title}</div>
      <p className="text-sm text-slate-700 mt-0.5" translate="no">{q.question}</p>
      <div className="mt-2 text-xs text-slate-700 space-y-1">
        <div>
          <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500 mr-1.5">Studie</span>
          <span translate="no">{q.study}</span>
          {q.study_status && <span className="text-slate-600"> – läge enligt publiceringsplanen: <span translate="no">{q.study_status}</span></span>}
        </div>
        {q.plans.length > 0 && (
          <div>
            <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500 mr-1.5">Analysplaner</span>
            {q.plans.map((p, i) => (
              <span key={p.file}>{i > 0 && ", "}
                <a href={p.url} target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline" translate="no">{p.file}</a>
                {p.locked && <span className="text-slate-500"> (låst)</span>}
              </span>
            ))}
          </div>
        )}
        {q.articles.length > 0 && (
          <div>
            <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500 mr-1.5">Artiklar som kan beröra frågan</span>
            {q.articles.map((a, i) => (
              <span key={a.slug}>{i > 0 && "; "}
                <Link href={a.url} className="text-[#b7410e] hover:underline" translate="no">{a.title}</Link>
              </span>
            ))}
            <span className="text-slate-500"> – ordlikhet, inte kontrollerad</span>
          </div>
        )}
        <div className="pt-1">
          <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500">Källor</span>{" "}
          <span className="text-slate-500">{q.n_claims} påståenden ur {q.n_texts ?? "–"} texter{q.decades.length ? `, ${q.decades[0]}–${q.decades[q.decades.length - 1]}-talet` : ""}</span>
          <Sources q={q} />
        </div>
      </div>
    </li>
  );
}

export function QuestionsPanel() {
  const [data, setData] = useState<ResearchQuestions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState<number | null>(null);
  const [state, setState] = useState<string>("");
  const [theme, setTheme] = useState("");
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(false);
  useEffect(() => {
    fetch(`${API_URL}/api/research/questions`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(setData).catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta frågelistan."));
  }, []);
  const themes = useMemo(() => [...new Set((data?.questions ?? []).map(q => q.theme))].sort(), [data]);
  const rows = useMemo(() => (data?.questions ?? []).filter(q =>
    (level == null || q.level === level) && (!state || q.study_state === state) && (!theme || q.theme === theme)
    && (!query || `${q.title} ${q.question}`.toLowerCase().includes(query.toLowerCase()))), [data, level, state, theme, query]);
  if (error) return <p className="text-red-700 font-semibold">{error}</p>;
  if (!data) return <p className="text-slate-500">Hämtar frågelistan …</p>;
  if (!data.available) return <div className="space-y-3"><InternalBanner note={data.note} /><p className="text-slate-600">Frågelistan finns inte på den här datorn.</p></div>;
  const lv = data.levels ?? {};
  const st = data.states ?? {};
  const decisive = data.questions.filter(q => q.level === 1);
  const decisiveRun = decisive.filter(q => q.study_state !== "planerad" && q.study_state !== "reservlista").length;
  return (
    <div className="space-y-4">
      <InternalBanner note={data.note} />
      <Answer topic="Öppna frågor" question="Vilka frågor i forskningen kan Vitki hjälpa till att besvara?"
        why="Litteraturgenomgången läste Fornvännen 1906–2023 och Futhark 1–15 och samlade det forskarna påstått men inte kunnat pröva på hela materialet. Frågelistan styr vilka studier Vitki gör och i vilken ordning."
        headline={{ value: String(data.n), label: `öppna frågor, varav ${lv["avgörande"] ?? 0} avgörande och ${lv["betydande"] ?? 0} betydande för forskningen` }}
        answer={<>{data.n} frågor bygger på {data.n_sources} påståenden i tidskrifterna. {st["körd"] ?? 0} hör till en studie som är körd,
          {" "}{st["låst plan"] ?? 0} till en studie med låst plan, {st["planerad"] ?? 0} till en planerad studie och {st["reservlista"] ?? 0} till
          reservlistan för populärartiklar. Av de {decisive.length} avgörande frågorna har {decisiveRun} en körd studie eller en låst plan.</>}
        interpretation={[
          "Relevansklassen säger hur mycket ett svar skulle betyda för forskningen, inte hur svår frågan är att besvara.",
          `För ${data.pages_found} av ${data.n_sources} källor hittades citatet i tidskriftens text, och sidan står med (tryckt sida där den går att läsa, annars pdf-sida). Där citatet inte hittades saknas sidan; kontrollera mot originalet innan citatet används.`,
        ]}
        notSaying={[
          "Frågorna är formulerade av oss utifrån påståenden i tidskrifterna; de är inte forskarnas egna frågor.",
          `Kopplingen till artiklarna är en ordlikhet (minst ${data.min_shared} gemensamma innehållsord), inte en kontrollerad koppling.`,
          "Hur varje fråga ska prövas och varför den är relevant visas inte här; det hålls tillbaka tills studien är publicerad.",
        ]} />
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-bold uppercase tracking-wider text-[11px] text-slate-500">Relevans</span>
        <button onClick={() => setLevel(null)} className={toggle(level == null)}>Alla {data.n}</button>
        {[1, 2, 3, 4].map(l => {
          const label = ["avgörande", "betydande", "användbar", "begränsad"][l - 1];
          return (
            <button key={l} onClick={() => setLevel(level === l ? null : l)} className={toggle(level === l)} title={data.level_help?.[label]}>
              {label} {lv[label] ?? 0}
            </button>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-bold uppercase tracking-wider text-[11px] text-slate-500">Studiens läge</span>
        <button onClick={() => setState("")} className={toggle(!state)}>Alla</button>
        {(["körd", "låst plan", "planerad", "reservlista"] as const).map(s => (
          <button key={s} onClick={() => setState(state === s ? "" : s)} className={toggle(state === s)} title={STATE_HELP[s]}>
            {s} {st[s] ?? 0}
          </button>
        ))}
        <select value={theme} onChange={e => setTheme(e.target.value)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-xs font-semibold outline-none">
          <option value="">Alla teman</option>
          {themes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Sök i frågorna"
          className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-xs outline-none" />
        <span className="text-slate-500">{rows.length} frågor</span>
      </div>
      <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {rows.slice(0, showAll ? undefined : FIRST).map(q => <QuestionCard key={q.nr} q={q} />)}
      </ul>
      {rows.length > FIRST && (
        <button onClick={() => setShowAll(!showAll)} className="text-sm font-semibold text-[#b7410e] hover:underline">
          {showAll ? "Visa färre" : `Visa alla ${rows.length}`}
        </button>
      )}
      <p className="text-[11px] text-slate-500 max-w-4xl">
        Ur utdata/litteraturgenomgang/artikelkandidater/fragelista.jsonl (samma ordning och nummer som kalkylbladet
        Forskningsfrågor_Fornvännen_Futhark.xlsx), påståendena i pastaenden.jsonl och studiernas läge i PUBLICERINGSPLAN.md.
        Sidorna räknas fram av scripts/build_fragelista_sidor.py.
      </p>
    </div>
  );
}
