"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAnalysis } from "@/components/AnalysisContext";
import { useAuth } from "@/components/AuthContext";
import { LanguageTable } from "@/components/StoneContext";
import { useSettings } from "@/components/SettingsContext";
import { corpus } from "@/lib/corpus";
import { db, type ProjectData } from "@/lib/db";
import { FEATURE_TYPES, METRICS, METRIC_DIGITS, METRIC_LABELS, formatSummary, type FeatureType } from "@/lib/metrics";
import { fromProject } from "@/lib/stoneReport";
import { runSynthesis, type Candidate, type LiteratureVerdict, type SynthesisResult } from "@/lib/synthesis";

const STRENGTH_STYLE: Record<Candidate["strength"], string> = {
  stark: "bg-emerald-100 text-emerald-800 border-emerald-300",
  måttlig: "bg-amber-100 text-amber-800 border-amber-300",
  svag: "bg-slate-100 text-slate-600 border-slate-300",
};

const VERDICT_STYLE: Record<LiteratureVerdict, string> = {
  "stämmer": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "stämmer delvis": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "nytt": "bg-sky-50 text-sky-800 border-sky-200",
  "motsäger": "bg-amber-50 text-amber-900 border-amber-200",
  "okänt": "bg-slate-50 text-slate-700 border-slate-200",
  "inget": "bg-slate-50 text-slate-700 border-slate-200",
};

const pct = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)} %`);
const num = (v: number | null | undefined, d = 2) => (v == null ? "–" : v.toFixed(d).replace(".", ","));
const card = "liquid-glass-island rounded-[32px] p-6 md:p-8 shadow-sm border border-white/50";
const h3 = "text-sm font-bold uppercase tracking-wider text-slate-500 mb-3";

export default function SynthesisPage() {
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [analysisId, setAnalysisId] = useState<string>("");
  const { geminiKey } = useSettings();
  const { user } = useAuth();
  const { setStoneReportInput } = useAnalysis();
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SynthesisResult | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    db.getProjects().then(setProjects);
  }, [user]);

  const project = projects.find(p => p.id === selectedId) ?? null;
  const analyses = useMemo(() => project?.grooveAnalyses ?? [], [project]);

  const selectProject = (id: string) => {
    const p = projects.find(x => x.id === id) ?? null;
    setSelectedId(id);
    setError(null);
    // Default analysis: the latest rune analysis, otherwise the latest of any kind
    const list = p?.grooveAnalyses ?? [];
    const runes = list.filter(a => a.feature_type === "rune");
    setAnalysisId((runes.at(-1) ?? list.at(-1))?.id ?? "");
    // Reopen a saved synthesis
    setResults(p?.synthesis?.result ?? null);
    setSavedAt(p?.synthesis?.savedAt ?? null);
  };

  const handleAnalyze = async () => {
    if (!project) return;
    setLoading(true);
    setResults(null);
    setSavedAt(null);
    setError(null);
    try {
      let entries = null;
      if (user) {
        setStatus("Hämtar mätkorpusen …");
        entries = await corpus.list().catch(() => []);
      }
      setStatus("Väger samman beläggen …");
      setResults(await runSynthesis(project, analysisId || null, geminiKey, entries));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Något gick fel vid syntesen.");
    } finally {
      setLoading(false);
      setStatus("");
    }
  };

  const saveToProject = async () => {
    if (!project || !results) return;
    const a = analyses.find(x => x.id === analysisId);
    const synthesis = { result: results, analysisId: analysisId || null, featureType: a?.feature_type ?? "rune", savedAt: new Date().toISOString() };
    const saved = await db.saveProject({ id: project.id, synthesis });
    setProjects(ps => ps.map(p => (p.id === saved.id ? saved : p)));
    setSavedAt(synthesis.savedAt);
  };

  const openStoneReport = () => {
    if (!project) return;
    const input = fromProject({ ...project, synthesis: results ? { result: results, analysisId: analysisId || null, featureType: "", savedAt: savedAt ?? "" } : project.synthesis });
    if (!input) { setError("Projektet har ingen sparad 3D-analys att rapportera."); return; }
    setStoneReportInput({ ...input, source: `Syntes för ${project.name}` });
    router.push("/rapporter?typ=sten");
  };

  const ev = results?.evidence;

  return (
    <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Syntes & Attribuering</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Väger samman Rundata, ortografisk jämförelse och uppmätt huggteknik. Ortografi och huggteknik vägs efter
          hur träffsäkra de är i just detta fall. Kandidaterna prövas mot geografi, ristarens stilgrupper och – om
          ristarens stenar är uppmätta – sten mot sten. Motsägelser redovisas; inga sannolikheter anges.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className={`${card} h-fit space-y-5`}>
          <label className="block text-slate-500 text-[12px] font-bold uppercase tracking-wider">Projekt
            <select className="w-full mt-2 liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none normal-case tracking-normal"
              value={selectedId} onChange={e => selectProject(e.target.value)}>
              <option value="" disabled>-- Välj projekt --</option>
              {projects.map(p => <option key={p.id} value={p.id}>{p.name}{p.metaText ? ` (${p.metaText})` : ""}</option>)}
            </select>
          </label>

          {project && (
            <>
              <label className="block text-slate-500 text-[12px] font-bold uppercase tracking-wider">3D-analys att jämföra
                <select className="w-full mt-2 liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none normal-case tracking-normal"
                  value={analysisId} onChange={e => setAnalysisId(e.target.value)} disabled={!analyses.length}>
                  {!analyses.length && <option value="">Ingen sparad analys</option>}
                  {analyses.map(a => (
                    <option key={a.id} value={a.id}>
                      {FEATURE_TYPES[a.feature_type as FeatureType] ?? a.feature_type} · {a.slices.length} snitt · {a.savedAt.slice(0, 10)}
                    </option>
                  ))}
                </select>
              </label>
              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
                <ul className="text-sm text-slate-700 space-y-2 font-medium">
                  <li className="flex justify-between"><span>Signum</span><span>{project.metaText || "–"}</span></li>
                  <li className="flex justify-between"><span>Stenart / vittring</span><span>{project.metaStone || "–"} / {project.metaWeathering || "–"}</span></li>
                  <li className="flex justify-between"><span>Sparade analyser</span><span>{analyses.length}</span></li>
                  <li className="flex justify-between"><span>2D-stilanalys</span><span>{project.twoDResults?.predicted_style ?? "–"}</span></li>
                  <li className="flex justify-between"><span>Egen läsning</span><span>{project.linguisticResults?.transliteration ? "ja" : <Link href="/phonetics" className="underline">nej</Link>}</span></li>
                  <li className="flex justify-between"><span>Mätkorpus</span><span>{user ? "jämförs" : "logga in"}</span></li>
                </ul>
              </div>
              {!project.metaText && <p className="text-xs text-amber-800">Projektet saknar signum – Rundata och ortografi kan inte användas.</p>}
              {!analyses.length && (
                <p className="text-xs text-amber-800">
                  Ingen fullständig 3D-analys sparad. Gör en mätning i <Link href="/3d" className="underline">3D-vyn</Link> och spara den i projektet.
                </p>
              )}
            </>
          )}

          <button onClick={handleAnalyze} disabled={loading || !project}
            className="w-full py-3.5 bg-[#b7410e] hover:bg-[#9a350b] active:scale-[0.98] disabled:opacity-40 text-white font-semibold text-sm rounded-2xl transition-all shadow-lg flex justify-center items-center gap-2">
            {loading ? (<><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />{status || "Beräknar …"}</>) : "Kör syntesen"}
          </button>
          {error && <p className="text-sm text-red-700 font-semibold">{error}</p>}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {!results ? (
            <div className={`${card} p-12 flex flex-col items-center justify-center text-center opacity-70`}>
              <h3 className="text-lg font-bold text-slate-700 mb-2">Ingen syntes körd</h3>
              <p className="text-sm text-slate-500 max-w-sm">Välj ett projekt och en 3D-analys och klicka på &quot;Kör syntesen&quot;.</p>
            </div>
          ) : (
            <>
              {savedAt && <p className="text-xs text-slate-500">Sparad syntes från {savedAt.slice(0, 16).replace("T", " ")}. Kör om för att uppdatera med nya mätningar.</p>}

              {results.outcome && (
                <div className={`rounded-[28px] border px-6 py-5 ${VERDICT_STYLE[results.outcome.verdict]}`}>
                  <div className="text-[11px] font-bold uppercase tracking-wider mb-1">Mot befintlig forskning: {results.outcome.verdict}</div>
                  <p className="text-[15px] font-semibold leading-relaxed">{results.outcome.text}</p>
                  {results.analysis_used && (
                    <p className="text-xs mt-2 opacity-80">
                      Huggteknik: {FEATURE_TYPES[results.analysis_used.feature_type as FeatureType] ?? results.analysis_used.feature_type}, {results.analysis_used.n} tvärsnitt.
                    </p>
                  )}
                </div>
              )}

              <div className={card}>
                <h3 className="text-xl font-bold text-slate-900 mb-5">Attribueringskandidater</h3>
                {results.candidates.length === 0 ? <p className="text-slate-600">Underlaget räcker inte för att peka ut någon ristare.</p> : (
                  <div className="space-y-5">{results.candidates.map(c => <CandidateCard key={c.name} c={c} />)}</div>
                )}
                <p className="text-[11px] text-slate-500 mt-4">
                  Vikter: signerad 4, attribuerad 2, parsten/liknar 1; ortografi och huggteknik 2 för plats 1 och 1 för plats 2–3,
                  multiplicerat med metodens tillförlitlighet i fallet. Stark = summa ≥ 4 (eller ≥ 3 från tre källor); måttlig = ≥ 2,5
                  (eller ≥ 1,5 från två källor); annars svag.
                </p>
              </div>

              <div className={`${card} ${results.conflicts.length ? "bg-amber-50/60" : ""}`}>
                <h3 className={h3}>Motsägelser mellan källorna</h3>
                {results.conflicts.length ? (
                  <ul className="list-disc pl-5 space-y-1 text-sm text-slate-800">{results.conflicts.map((c, i) => <li key={i}>{c}</li>)}</ul>
                ) : <p className="text-sm text-slate-700">Inga – källorna pekar inte åt olika håll.</p>}
                {results.missing.length > 0 && (
                  <>
                    <h3 className={`${h3} mt-5`}>Belägg som saknas</h3>
                    <ul className="list-disc pl-5 space-y-1 text-sm text-slate-700">{results.missing.map((m, i) => <li key={i}>{m}</li>)}</ul>
                  </>
                )}
                {ev?.style_check && (
                  <p className={`mt-4 rounded-2xl px-4 py-3 text-sm ${ev.style_check.rundata_style ? (ev.style_check.agrees ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800") : "bg-slate-100 text-slate-700"}`}>
                    <strong>Stilgrupp:</strong> AI-bedömning från 2D-analysen {ev.style_check.ai_style}
                    {ev.style_check.ai_confidence != null && ` (självskattning ${ev.style_check.ai_confidence} %, okalibrerad)`};
                    Rundata {ev.style_check.rundata_style ?? "saknar uppgift"}{ev.style_check.rundata_style && (ev.style_check.agrees ? " – stämmer." : " – skiljer sig.")}
                  </p>
                )}
              </div>

              <EvidenceDetails r={results} />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className={card}>
                  <h3 className={h3}>Material och vittring</h3>
                  <p className="text-[15px] text-slate-800 leading-relaxed">{results.geology_analysis}</p>
                  {ev?.geology && (
                    <div className="mt-3 rounded-xl bg-white/70 border border-slate-200 px-3 py-2 text-xs text-slate-700">
                      <div className="font-bold uppercase tracking-wider text-[10px] text-slate-500 mb-0.5">Berggrund (SGU): {ev.geology.verdict}</div>
                      <p>{ev.geology.text}</p>
                      {ev.geology.at_site && <p className="mt-1">På platsen: {ev.geology.at_site.rock} – {ev.geology.at_site.unit}</p>}
                      <p className="mt-1 text-slate-500">{ev.geology.caveat}</p>
                    </div>
                  )}
                </div>
                <div className={card}>
                  <h3 className={h3}>Datering</h3>
                  <p className="text-[15px] text-slate-800 leading-relaxed">{results.dating_analysis}</p>
                </div>
              </div>

              <div className={`${card} bg-slate-50`}>
                <h3 className={h3}>Tolkning</h3>
                <p className="text-[15px] text-slate-800 leading-relaxed mb-3">{results.theory_analysis}</p>
                <h3 className={h3}>Sammanfattning</h3>
                <p className="text-[15px] text-slate-800 leading-relaxed">{results.summary}</p>
                <p className="text-[11px] text-slate-500 mt-3">
                  {results.ai_used ? "Tolkning och sammanfattning är AI-genererade utifrån beläggen ovan och ska granskas." : "Ingen AI-text – texterna är framräknade direkt ur beläggen."}
                </p>
                {results.sources.length > 0 && (
                  <div className="mt-3 text-[11px] text-slate-500">
                    <div className="font-bold uppercase tracking-wider">Källor</div>
                    <ul className="list-disc pl-4">{results.sources.map(src => <li key={src}>{src}</li>)}</ul>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap justify-end gap-3 pt-2">
                <button onClick={saveToProject} className="px-6 py-3.5 bg-white border border-slate-300 text-slate-800 font-bold rounded-2xl">
                  {savedAt ? "Spara igen i projektet" : "Spara i projektet"}
                </button>
                <button onClick={openStoneReport} className="px-6 py-3.5 bg-slate-900 hover:bg-black text-white font-bold rounded-2xl shadow-lg">
                  Skapa stenrapport med attribueringen
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function CandidateCard({ c }: { c: Candidate }) {
  return (
    <div className="bg-white/60 rounded-2xl p-5 border border-white">
      <div className="flex flex-wrap justify-between items-center gap-2 mb-3">
        <Link href={`/inskrifter?carver=${encodeURIComponent(c.name)}`} className="text-lg font-bold text-slate-900 hover:text-[#b7410e]">{c.name}</Link>
        <div className="flex gap-2 items-center">
          {c.literature && <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${VERDICT_STYLE[c.literature.verdict]}`}>{c.literature.verdict}</span>}
          <span className={`text-[11px] font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${STRENGTH_STYLE[c.strength]}`}>
            {c.strength} belägg{c.score != null && ` · ${num(c.score, 1)}`}
          </span>
        </div>
      </div>
      <ul className="text-sm text-slate-700 space-y-1 mb-3">
        {c.evidence.map((e, i) => (
          <li key={i}><span className="font-semibold">{e.source}</span>{e.weight != null && <span className="text-slate-400 font-mono text-xs"> ({num(e.weight, 1)})</span>}: {e.description}</li>
        ))}
      </ul>
      {(c.literature || c.geography || c.styles || c.stone_tests) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-700 border-t border-slate-200 pt-3">
          {c.literature && <Check label="Litteraturen" ok={c.literature.verdict.startsWith("stämmer") ? true : c.literature.verdict === "motsäger" ? false : null} text={c.literature.text} />}
          {c.geography && <Check label="Geografi" ok={c.geography.plausible} text={c.geography.text} />}
          {c.styles && <Check label="Stilgrupp och datering" ok={c.styles.fits} text={c.styles.text} />}
          {c.material && <Check label="Bergart" ok={c.material.fits} text={c.material.text} />}
          {c.stone_tests && (
            <Check label="Sten mot sten (huggteknik)" ok={c.stone_tests.n ? c.stone_tests.compatible > 0 : null}
              text={`${c.stone_tests.text}${c.stone_tests.tests.length ? ": " + c.stone_tests.tests.map(t => `${t.signum} p ${t.p_value != null && t.p_value < 0.001 ? "< 0,001" : "= " + num(t.p_value, 3)}`).join(", ") : ""}.`} />
          )}
        </div>
      )}
      {c.language && c.language.comparable > 0 && (
        <details className="mt-3 text-xs text-slate-700">
          <summary className={`cursor-pointer font-semibold ${c.language.fits === false ? "text-amber-800" : ""}`}>
            Språkdrag: {c.language.agree} av {c.language.comparable} stämmer med ristarens inskrifter
          </summary>
          <div className="mt-2"><LanguageTable comparison={c.language} /></div>
        </details>
      )}
      {c.reasoning && <p className="text-sm text-slate-600 italic mt-3">{c.reasoning}</p>}
    </div>
  );
}

function Check({ label, ok, text }: { label: string; ok: boolean | null; text: string }) {
  const icon = ok === true ? "✓" : ok === false ? "!" : "·";
  const color = ok === true ? "text-emerald-700" : ok === false ? "text-amber-700" : "text-slate-400";
  return (
    <div className="flex gap-2">
      <span className={`font-bold ${color}`}>{icon}</span>
      <div><span className="font-semibold">{label}:</span> {text}</div>
    </div>
  );
}

function EvidenceDetails({ r }: { r: SynthesisResult }) {
  const o = r.evidence?.orthography;
  const g = r.evidence?.groove;
  const m = r.evidence?.measurements_by_feature;
  return (
    <div className={card}>
      <h3 className="text-xl font-bold text-slate-900 mb-4">Beläggen i detalj</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className={h3}>{o?.source ?? "Ortografi"}</h3>
          {r.evidence?.reading_check && <p className="text-xs text-slate-600 mb-2">Vår läsning mot Rundata: {r.evidence.reading_check.summary}</p>}
          {o ? (
            <>
              <table className="w-full text-xs">
                <thead><tr className="text-left text-slate-500"><th className="py-1">Ristare</th><th>Likhet</th><th>Precision</th><th>Område</th><th>Vikt</th></tr></thead>
                <tbody>{o.ranking.map(x => (
                  <tr key={x.carver} className="border-t border-slate-900/5">
                    <td className="py-1 font-semibold">{x.carver}</td><td>{num(x.similarity)}</td><td>{pct(x.precision)}</td>
                    <td>{x.in_area ? "inom" : <span className="text-amber-700">utanför</span>}</td><td>{num(x.reliability)}</td>
                  </tr>
                ))}</tbody>
              </table>
              <p className="text-[11px] text-slate-500 mt-2">
                {o.n_words} läsbara ord{!o.usable && " – för kort, vägs inte in"}. Modellen: rätt ristare först i {pct(o.evaluation.top1_accuracy)}
                {o.evaluation.signed_top1 != null && ` (${pct(o.evaluation.signed_top1)} för signerade)`} bland {o.evaluation.n_carvers} ristare; slumpnivå {pct(o.evaluation.chance_top1)}.
              </p>
            </>
          ) : <p className="text-sm text-slate-500">Ingen ortografisk jämförelse.</p>}
        </div>
        <div>
          <h3 className={h3}>Huggteknik mot mätkorpusen</h3>
          {g?.ranking?.length ? (
            <>
              <table className="w-full text-xs">
                <thead><tr className="text-left text-slate-500"><th className="py-1">Ristare</th><th>Avstånd</th><th>Stenar</th></tr></thead>
                <tbody>{g.ranking.map(x => (
                  <tr key={x.group} className="border-t border-slate-900/5"><td className="py-1 font-semibold">{x.group}</td><td>{num(x.distance)}</td><td>{x.n}</td></tr>
                ))}</tbody>
              </table>
              <p className="text-[11px] text-slate-500 mt-2">
                {g.evaluation ? `Korsvaliderad träffsäkerhet ${pct(g.evaluation.top1_accuracy)} (${g.evaluation.n_stones} stenar, ${g.evaluation.n_groups} ristare; slumpnivå ${pct(g.evaluation.chance_top1)}). ` : ""}
                Tillförlitlighet över slumpnivån: {num(g.reliability ?? 0)}. Kortare avstånd = mer lik.
              </p>
            </>
          ) : <p className="text-sm text-slate-500">Ingen jämförelse – se &quot;Belägg som saknas&quot;.</p>}
        </div>
      </div>
      {m && Object.keys(m).length > 0 && (
        <div className="mt-6 overflow-x-auto">
          <h3 className={h3}>Uppmätta spår (senaste analysen per spårtyp)</h3>
          <table className="w-full text-xs">
            <thead><tr className="text-left text-slate-500"><th className="py-1">Spår</th><th>n</th>{METRICS.slice(0, 4).map(k => <th key={k}>{METRIC_LABELS[k]}</th>)}</tr></thead>
            <tbody>{Object.entries(m).map(([ft, v]) => (
              <tr key={ft} className="border-t border-slate-900/5">
                <td className="py-1 font-semibold">{FEATURE_TYPES[ft as FeatureType] ?? ft}</td><td>{v.n}</td>
                {METRICS.slice(0, 4).map(k => <td key={k}>{formatSummary(v.summary[k], METRIC_DIGITS[k])}</td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}
