"use client";

import { useEffect, useMemo, useState } from "react";
import PlotlyGraph from "@/components/PlotlyGraph";
import { useAuth } from "@/components/AuthContext";
import { useAnalysis } from "@/components/AnalysisContext";
import { DocsNote } from "@/components/KnownLimitations";
import { InfoTip, PageIntro, SigBadge, Tip } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import { corpus } from "@/lib/corpus";
import { db } from "@/lib/db";
import { FEATURE_TYPES, METRIC_DIGITS, formatSummary, type FeatureType, type SliceMetrics } from "@/lib/metrics";
import { formatP, stats, type ComparisonResult } from "@/lib/stats";

interface StoneOption {
  key: string;
  label: string;
  group: string;
  signum: string;
  feature_type: FeatureType;
  slices: SliceMetrics[];
  provenance?: Record<string, unknown>;
  profile?: { x: number[]; z: number[] };
}
interface CorpusRef { signum?: string; feature_type?: string; means?: Record<string, number>; method_version?: string }

// Categorical slots 1 and 2 of the validated palette; A and B are also named in the legend
const COLOR_A = "#2a78d6";
const COLOR_B = "#eb6834";
const STABLE_LABELS: Record<string, string> = { apex_vinkel_deg: "V-vinkel (°)", "spårdjup_mm": "Spårdjup (mm)", "spårbredd_mm": "Spårbredd (mm)", djup_bredd_kvot: "Djup/bredd" };

// Shift a profile so its lowest point is at (0, 0), making two grooves comparable in one plot
function normalizeProfile(p: { x: number[]; z: number[] }) {
  let k = 0;
  for (let i = 1; i < p.z.length; i++) if (p.z[i] < p.z[k]) k = i;
  return { x: p.x.map(v => v - p.x[k]), z: p.z.map(v => v - p.z[k]) };
}
const jitter = (i: number) => ((i * 9301 + 49297) % 233280) / 233280 * 0.5 - 0.25;

export default function ComparePage() {
  const { user } = useAuth();
  const { latest3DResults, latest3DMeta } = useAnalysis();
  const [options, setOptions] = useState<StoneOption[]>([]);
  const [corpusRefs, setCorpusRefs] = useState<CorpusRef[]>([]);
  const [aKey, setAKey] = useState("");
  const [bKey, setBKey] = useState("");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sessionOption = useMemo<StoneOption | null>(() => {
    if (!latest3DResults?.slices?.length) return null;
    return {
      key: "session",
      label: `Aktuell analys${latest3DMeta.text ? ` – ${latest3DMeta.text}` : ""}`,
      group: "Denna session",
      signum: latest3DMeta.text,
      feature_type: (latest3DResults.provenance?.feature_type as FeatureType) ?? "unknown",
      slices: latest3DResults.slices,
      provenance: latest3DResults.provenance as unknown as Record<string, unknown>,
      profile: latest3DResults.plot_data ? { x: latest3DResults.plot_data.x, z: latest3DResults.plot_data.z } : undefined,
    };
  }, [latest3DResults, latest3DMeta.text]);

  useEffect(() => {
    (async () => {
      const opts: StoneOption[] = [];
      const projects = await db.getProjects();
      for (const p of projects) {
        for (const a of p.grooveAnalyses ?? []) {
          const runes = new Set(a.slices.map(s => s.rune_id).filter(v => v != null)).size;
          opts.push({
            key: `proj_${a.id}`,
            label: `${p.metaText || p.name} – ${FEATURE_TYPES[a.feature_type]} (${runes ? `${runes} runor, ` : ""}${a.slices.length} snitt, ${a.savedAt.slice(0, 10)})`,
            group: "Mina projekt",
            signum: p.metaText,
            feature_type: a.feature_type,
            slices: a.slices,
            provenance: a.provenance as unknown as Record<string, unknown>,
          });
        }
      }
      if (user) {
        try {
          const entries = await corpus.list();
          setCorpusRefs(entries.map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means, method_version: e.method_version })));
          for (const e of entries) {
            opts.push({
              key: `corpus_${e.id}`,
              label: `${e.label} – ${e.contributorName} (${e.slices.length} snitt)`,
              group: "Delad korpus",
              signum: e.signum,
              feature_type: e.feature_type,
              slices: e.slices,
              provenance: e.provenance as unknown as Record<string, unknown>,
              profile: e.profile,
            });
          }
        } catch (e) {
          console.error(e);
        }
      }
      setOptions(opts);
    })();
  }, [user]);

  const all = useMemo(() => (sessionOption ? [sessionOption, ...options] : options), [sessionOption, options]);
  const a = all.find(o => o.key === aKey);
  const b = all.find(o => o.key === bKey);
  const groups = [...new Set(all.map(o => o.group))];

  const run = async () => {
    if (!a || !b) return;
    setRunning(true);
    setError(null);
    try {
      setResult(await stats.compare(
        { label: a.label, signum: a.signum, feature_type: a.feature_type, slices: a.slices, provenance: a.provenance },
        { label: b.label, signum: b.signum, feature_type: b.feature_type, slices: b.slices, provenance: b.provenance },
        corpusRefs,
      ));
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "Jämförelsen misslyckades.");
    } finally {
      setRunning(false);
    }
  };

  const picker = (value: string, set: (v: string) => void) => (
    <select value={value} onChange={e => { set(e.target.value); setResult(null); }}
      className="w-full liquid-glass-input-wrapper rounded-xl px-3 py-2.5 text-sm font-semibold outline-none">
      <option value="">– Välj sten –</option>
      {groups.map(g => (
        <optgroup key={g} label={g}>
          {all.filter(o => o.group === g).map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
        </optgroup>
      ))}
    </select>
  );

  const unitText = result?.unit === "runa" ? `per runa (${result.n_units?.[0]} och ${result.n_units?.[1]} runor)` : `per snitt (${result?.n_units?.[0]} och ${result?.n_units?.[1]} snitt)`;
  const stable = result?.per_metric.filter(r => r.stable !== false) ?? [];
  const unstable = result?.per_metric.filter(r => r.stable === false) ?? [];

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6">
      <PageIntro title="Jämför två stenar"
        lead={<>Kan två stenar vara huggna av samma hand? Huggspåren jämförs runa mot runa, avståndet ställs mot stenpar i den delade
          mätkorpusen – par av samma och av olika ristare – och har stenarna signum jämförs också ristare, stil, stavning och språkdrag.</>}
        howTo={[
          <>Välj två uppmätta stenar och tryck Jämför. Slutsatsen kommer först, sedan om mätningarna alls går att jämföra.</>,
          <>En <strong>säkerställd skillnad</strong> i huggspåren talar för olika händer (eller olika bergart, verktyg, vittring). Ingen säkerställd skillnad betyder bara att mätningarna inte skiljer stenarna åt – inte att de är huggna av samma ristare.</>,
          <>Asymmetri och bottenradie är osäkra mått och ingår inte i den samlade jämförelsen.</>,
        ]} />
      <DocsNote anchor="3-jämförelse-av-två-stenar">Hur jämförelsen räknas står i avsnitt 3.</DocsNote>

      <div className="liquid-glass-island rounded-[32px] p-6 grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-4 items-end">
        <div><label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Sten A</label>{picker(aKey, setAKey)}</div>
        <div><label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Sten B</label>{picker(bKey, setBKey)}</div>
        <button onClick={run} disabled={!a || !b || aKey === bKey || running}
          className="px-6 py-2.5 bg-slate-900 text-white font-bold rounded-xl disabled:opacity-40">
          {running ? "Beräknar..." : "Jämför"}
        </button>
        {all.length === 0 && (
          <p className="md:col-span-3 text-sm text-slate-500">
            Inga mätningar att välja bland. Analysera i 3D-vyn och spara till ett projekt, eller logga in för att använda den delade korpusen.
          </p>
        )}
        {!user && all.length > 0 && <p className="md:col-span-3 text-xs text-slate-500">Logga in för att ställa avståndet mot den delade mätkorpusen.</p>}
      </div>
      {error && <p className="text-red-700 font-semibold">{error}</p>}

      {result && a && b && (
        <>
          <div className={`liquid-glass-island rounded-[32px] p-6 border-l-8 ${
            result.overall.p_value !== null && result.overall.p_value < 0.05 ? "border-amber-600" : "border-emerald-600"}`}>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Slutsats</span>
              {result.overall.p_value !== null && (
                <span className="flex items-center gap-1.5 text-[11px] text-slate-600">skillnad i huggspåren:
                  <SigBadge sig={{ significant: result.overall.p_value < 0.05, label: `p ${formatP(result.overall.p_value)}`,
                    test: "samlat permutationstest på de stabila måtten" }} />
                </span>
              )}
            </div>
            <ul className="mt-2 space-y-1.5 text-slate-800">
              {(result.conclusion ?? [result.interpretation]).map((s, i) => <li key={i} className={i === 0 ? "font-semibold text-slate-900" : ""}>{s}</li>)}
            </ul>
          </div>

          {result.comparability && result.comparability.length > 0 && (
            <div className="liquid-glass-island rounded-[24px] p-5">
              <h3 className="font-bold text-slate-900 mb-2">Går mätningarna att jämföra?</h3>
              <ul className="space-y-1 text-sm">
                {result.comparability.map(c => (
                  <li key={c.key} className="flex gap-2">
                    <span className={c.ok ? "text-emerald-700 font-bold" : "text-amber-700 font-bold"}>{c.ok ? "✓" : "⚠"}</span>
                    <span className="text-slate-700">{c.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="liquid-glass-island rounded-[32px] p-4 overflow-x-auto">
              <h3 className="font-bold text-sm text-slate-700 mb-1 px-2">Huggspåren {unitText}</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="p-2">Mått<InfoTip text={GLOSSARY["Mått"]} /></th><th className="p-2">A<InfoTip text={GLOSSARY["A"]} /></th><th className="p-2">B<InfoTip text={GLOSSARY["B"]} /></th>
                    <th className="p-2">p (just.)<InfoTip text="Permutationstest per mått, Bonferroni-justerat för antalet mått. Under 0,05 = säkerställd skillnad." /></th>
                    <th className="p-2">d<InfoTip text={GLOSSARY["d"]} /></th>
                  </tr>
                </thead>
                <tbody>
                  {[...stable, ...unstable].map(r => (
                    <tr key={r.metric} className={`border-t border-slate-900/5 ${r.stable === false ? "text-slate-400" : ""}`}>
                      <td className="p-2 font-semibold"><Tip text={GLOSSARY[r.label]}>{r.label}</Tip>{r.stable === false && <span className="font-normal text-[10px]"> (osäkert mått)</span>}</td>
                      <td className="p-2 font-mono text-xs">{formatSummary(r.a, METRIC_DIGITS[r.metric])}</td>
                      <td className="p-2 font-mono text-xs">{formatSummary(r.b, METRIC_DIGITS[r.metric])}</td>
                      <td className={`p-2 font-mono text-xs ${r.p_adjusted !== null && r.p_adjusted < 0.05 && r.stable !== false ? "text-amber-700 font-bold" : ""}`}>{formatP(r.p_adjusted)}</td>
                      <td className="p-2 font-mono text-xs">{r.effect_size_d != null ? r.effect_size_d.toFixed(2) : "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-[11px] text-slate-500 p-2">
                Medel ± SD {result.unit === "runa" ? "av runornas medelvärden" : "av snitten"}. Samlat test på de stabila måtten:
                p = {formatP(result.overall.p_value)}. Asymmetri och bottenradie är osäkra mått och ingår inte i det samlade testet.
              </p>
            </div>

            {result.unit_values && (
              <div className="liquid-glass-island rounded-[32px] p-4">
                <h3 className="font-bold text-sm text-slate-700 mb-1 px-2">{result.unit === "runa" ? "Varje runa" : "Varje snitt"}, A och B</h3>
                <div className="h-[320px]">
                  <PlotlyGraph
                    data={Object.keys(STABLE_LABELS).flatMap((m, k) => [0, 1].map(side => {
                      const vals = result.unit_values![side][m] ?? [];
                      return {
                        type: "scatter", mode: "markers", xaxis: `x${k + 1}`, yaxis: `y${k + 1}`, showlegend: k === 0,
                        name: side === 0 ? "A" : "B", legendgroup: side === 0 ? "A" : "B",
                        x: vals.map((_, i) => side + jitter(i)), y: vals,
                        marker: { color: side === 0 ? COLOR_A : COLOR_B, size: 7, opacity: 0.75, line: { color: "#ffffff", width: 1 } },
                        hovertemplate: `${side === 0 ? "A" : "B"}: %{y:.2f}<extra>${STABLE_LABELS[m]}</extra>`,
                      };
                    }))}
                    layout={{
                      autosize: true, margin: { l: 40, r: 10, t: 24, b: 30 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
                      grid: { rows: 1, columns: 4, pattern: "independent" }, legend: { orientation: "h", y: -0.12 },
                      annotations: Object.values(STABLE_LABELS).map((t, k) => ({ text: t, x: 0.5, y: 1.08, xref: `x${k + 1} domain`, yref: `y${k + 1} domain`, showarrow: false, font: { size: 11, color: "#52514e" } })),
                      ...Object.fromEntries(Object.keys(STABLE_LABELS).flatMap((_, k) => [
                        [`xaxis${k + 1}`, { tickvals: [0, 1], ticktext: ["A", "B"], range: [-0.6, 1.6], showgrid: false, zeroline: false }],
                        [`yaxis${k + 1}`, { gridcolor: "rgba(15,23,42,0.06)", zeroline: false, tickfont: { size: 10 } }],
                      ])),
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {result.reference ? (
            <div className="liquid-glass-island rounded-[24px] p-5 space-y-3">
              <h3 className="font-bold text-slate-900">Hur stort är avståndet?</h3>
              <p className="text-sm text-slate-600">
                Avståndet mellan stenarnas medelvärden (stabila mått, standardiserade) jämfört med alla {result.reference.n_pairs} stenpar
                bland {result.reference.n_stones} stenar i mätkorpusen. Längre till vänster: mer lika än de flesta par.
              </p>
              {[["Alla par", result.reference.percentile_all, result.reference.n_pairs],
                ["Par med samma ristare i Rundata", result.reference.percentile_same, result.reference.n_same],
                ["Par med olika ristare i Rundata", result.reference.percentile_different, result.reference.n_different]].map(([label, pct, n]) => (
                <div key={label as string} className="text-sm">
                  <div className="flex justify-between text-xs text-slate-600"><span>{label as string} ({n as number})</span>
                    <span>{pct == null ? "för få par" : `större än ${pct} % av paren`}</span></div>
                  <div className="relative h-2.5 rounded-full bg-slate-200 mt-1">
                    {pct != null && <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-slate-900 border-2 border-white" style={{ left: `calc(${pct as number}% - 6px)` }} />}
                  </div>
                </div>
              ))}
              <p className="text-[11px] text-slate-500">
                Rundatas ristare är bedömningar, och skillnaderna mellan stenar beror också på bergart och skanning; skalan visar var paret
                hamnar, inte vem som ristade.
              </p>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Referensskalan visas när den delade mätkorpusen har minst fem stenar med samma spårtyp och mätmetod{user ? "" : " (logga in)"}.</p>
          )}

          {result.context && (
            <div className="liquid-glass-island rounded-[24px] p-5">
              <h3 className="font-bold text-slate-900 mb-2">Mer än huggspår</h3>
              <table className="w-full text-sm">
                <thead><tr className="text-left text-[11px] uppercase tracking-wider text-slate-500"><th className="p-2"></th><th className="p-2">A</th><th className="p-2">B</th></tr></thead>
                <tbody>{result.context.rows.map(r => (
                  <tr key={r.label} className="border-t border-slate-900/5"><td className="p-2 text-slate-600">{r.label}</td><td className="p-2">{r.a}</td><td className="p-2">{r.b}</td></tr>
                ))}</tbody>
              </table>
              <ul className="mt-3 space-y-1 text-sm text-slate-700">
                {result.context.distance_km != null && <li>Avstånd: {result.context.distance_km < 1 ? "samma plats" : `${Math.round(result.context.distance_km)} km`}.</li>}
                {result.context.orthography && <li>Stavning: likhet {result.context.orthography.similarity.toFixed(2).replace(".", ",")} – mer lika än {result.context.orthography.percentile} % av sten A:s jämförelser med {result.context.orthography.n} andra inskrifter.</li>}
                {result.context.language && <li>Språkdrag: {result.context.language.agree} av {result.context.language.comparable} jämförbara stämmer överens{result.context.language.differ.length ? ` (skiljer: ${result.context.language.differ.join("; ")})` : ""}.</li>}
              </ul>
            </div>
          )}

          <div className="liquid-glass-island rounded-[32px] p-4">
            <h3 className="font-bold text-sm text-slate-700 mb-2 px-2">Representativa profiler (lägsta punkt i origo)</h3>
            {a.profile && b.profile ? (
              <div className="h-[300px]">
                <PlotlyGraph
                  data={[a, b].map((s, i) => {
                    const p = normalizeProfile(s.profile!);
                    return { x: p.x, y: p.z, mode: "lines", name: i === 0 ? "A" : "B", line: { color: i === 0 ? COLOR_A : COLOR_B, width: 2 } };
                  })}
                  layout={{
                    margin: { l: 40, r: 10, t: 10, b: 40 },
                    xaxis: { title: "mm" }, yaxis: { title: "mm", scaleanchor: "x" },
                    legend: { orientation: "h" },
                    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
                  }}
                />
              </div>
            ) : (
              <p className="text-sm text-slate-500 px-2">Profilkurvor finns bara för korpusposter och aktuell analys.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
