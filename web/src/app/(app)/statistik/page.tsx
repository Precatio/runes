"use client";
import { useEffect, useState } from "react";
import { Glossary, type Level } from "@/components/Explain";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import OwnQuestion from "@/components/OwnQuestion";
import type { Corpus, Status, Tab } from "./_delar/typer";
import { PATTERN_TOPICS, TOPIC, memo } from "./_delar/gemensamt";
import { Messages } from "./_delar/budskap";
import { People } from "./_delar/manniskor";
import { NewBadge } from "@/components/PatternCard";
import { GITHUB_URL } from "@/lib/site";
import { Overview } from "./_delar/oversikt";
import { Geography } from "./_delar/geografi";
import { Change, Chronology, Clusters, Network, TextTab, Words } from "./_delar/text";
import { Anonymous, Attribution } from "./_delar/ristare";

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
      if (window.location.hash === "#egen-fraga") setTab("question");
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

      {!data && status && (
        <div className="liquid-glass-island rounded-[32px] p-5 md:p-7"><OwnQuestion /></div>
      )}

      {data && (
        <>
          <NewPatterns data={data} onOpen={setTab} />
          <nav aria-label="Frågor" className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
            {[{ key: "overview" as Tab, question: "Vad säger statistiken sammantaget?", confidence: null as Level | null },
              { key: "question" as Tab, question: "Pröva en egen fråga", confidence: null as Level | null },
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
            {tab === "question" && <OwnQuestion />}
            {tab === "geography" && <Geography data={data} />}
            {tab === "clusters" && <Clusters data={data} />}
            {tab === "text" && <TextTab data={data} />}
            {tab === "attribution" && <Attribution data={data} />}
            {tab === "anonymous" && <Anonymous data={data} />}
            {tab === "chronology" && <Chronology data={data} />}
            {tab === "change" && <Change data={data} />}
            {tab === "network" && <Network data={data} />}
            {tab === "words" && <Words data={data} />}
            {tab === "messages" && <Messages data={data} />}
            {tab === "people" && <People data={data} />}
          </div>
          {status?.r.available && (
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 px-1">
              <span>
                Beräknat i {status.r.version} på {c?.n_stones} runstenar (version <span translate="no">{c?.fingerprint}</span>
                {c?.computed_at ? `, ${new Date(c.computed_at).toLocaleString("sv-SE")}` : ""}). Samma analyser används i{" "}
                <Link href="/stenanalys" className="text-[#b7410e] hover:underline">stenanalysen</Link> och ställs mot forskningen i{" "}
                <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>.
              </span>
              <a href={`${GITHUB_URL}/tree/main/r`} target="_blank" rel="noopener noreferrer"
                className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white font-bold text-slate-700 hover:bg-slate-50">
                R-skripten på GitHub ↗
              </a>
            </div>
          )}
        </>
      )}
    </div>
  );
}

const firstSentence = (t: string) => { const s = t.split(/(?<=[a-zåäö0-9)])\.\s/)[0].trim(); return /[.!?]$/.test(s) ? s : `${s}.`; };

/** The patterns that appeared (or changed status) in the last 30 days, first on the page, each opening its question. */
function NewPatterns({ data, onOpen }: { data: Corpus; onOpen: (t: Tab) => void }) {
  const fresh = (data.patterns ?? []).filter(p => p.new);
  if (!fresh.length) return null;
  const tabOf = (topic: string) => (Object.entries(PATTERN_TOPICS).find(([, ts]) => ts.includes(topic))?.[0] ?? "overview") as Tab;
  return (
    <section aria-label="Nya mönster" className="rounded-[24px] border border-violet-200 bg-violet-50/60 p-4 md:p-5 space-y-2">
      <h3 className="text-sm font-bold uppercase tracking-wider text-violet-900">Nya mönster i datan ({fresh.length})</h3>
      <p className="text-xs text-violet-900/80">Mönster som dykt upp eller bytt status de senaste 30 dagarna. Ett nytt mönster märks Nytt först när det håller i båda halvorna av korpusen och klarar den gemensamma justeringen över alla mönster; innan dess Nytt, obekräftat. Klicka för att öppna frågan de hör till.</p>
      <ul className="space-y-1.5">
        {fresh.map(p => (
          <li key={`${p.topic}|${p.key}`}>
            <button type="button" onClick={() => onOpen(tabOf(p.topic))}
              className="w-full text-left flex flex-wrap items-start gap-2 rounded-xl bg-white/80 border border-violet-100 px-3 py-2 hover:border-violet-300">
              <NewBadge pt={p} />
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e] pt-0.5">{p.topic}</span>
              <span className="text-sm text-slate-800 flex-1 min-w-[16rem]">{firstSentence(p.text)}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
