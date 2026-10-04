"use client";

import { useEffect, useMemo, useState } from "react";
import PlotlyGraph from "@/components/PlotlyGraph";
import { useAuth } from "@/components/AuthContext";
import { useAnalysis } from "@/components/AnalysisContext";
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
  profile?: { x: number[]; z: number[] };
}

// Shift a profile so its lowest point is at (0, 0), making two grooves comparable in one plot
function normalizeProfile(p: { x: number[]; z: number[] }) {
  let k = 0;
  for (let i = 1; i < p.z.length; i++) if (p.z[i] < p.z[k]) k = i;
  return { x: p.x.map(v => v - p.x[k]), z: p.z.map(v => v - p.z[k]) };
}

export default function ComparePage() {
  const { user } = useAuth();
  const { latest3DResults, latest3DMeta } = useAnalysis();
  const [options, setOptions] = useState<StoneOption[]>([]);
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
      profile: latest3DResults.plot_data ? { x: latest3DResults.plot_data.x, z: latest3DResults.plot_data.z } : undefined,
    };
  }, [latest3DResults, latest3DMeta.text]);

  useEffect(() => {
    (async () => {
      const opts: StoneOption[] = [];
      const projects = await db.getProjects();
      for (const p of projects) {
        for (const a of p.grooveAnalyses ?? []) {
          opts.push({
            key: `proj_${a.id}`,
            label: `${p.metaText || p.name} – ${FEATURE_TYPES[a.feature_type]} (${a.slices.length} snitt, ${a.savedAt.slice(0, 10)})`,
            group: "Mina projekt",
            signum: p.metaText,
            feature_type: a.feature_type,
            slices: a.slices,
          });
        }
      }
      if (user) {
        try {
          for (const e of await corpus.list()) {
            opts.push({
              key: `corpus_${e.id}`,
              label: `${e.label} – ${e.contributorName} (${e.slices.length} snitt)`,
              group: "Delad korpus",
              signum: e.signum,
              feature_type: e.feature_type,
              slices: e.slices,
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
        { label: a.label, signum: a.signum, feature_type: a.feature_type, slices: a.slices },
        { label: b.label, signum: b.signum, feature_type: b.feature_type, slices: b.slices },
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

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Jämför två stenar</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Kan två spår vara huggna med samma verktyg eller av samma hand? Snittmätningarna jämförs med permutationstest,
          mått för mått och för alla mått samtidigt.
        </p>
      </div>

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
      </div>
      {error && <p className="text-red-700 font-semibold">{error}</p>}

      {result && a && b && (
        <>
          <div className={`liquid-glass-island rounded-[32px] p-6 border-l-8 ${
            result.overall.p_value !== null && result.overall.p_value < 0.05 ? "border-amber-600" : "border-emerald-600"}`}>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Samlat test (alla mått)</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">p = {formatP(result.overall.p_value)}</div>
            <p className="text-slate-700 mt-2">{result.interpretation}</p>
            {result.warnings.map(w => <p key={w} className="text-amber-800 text-sm font-semibold mt-2">⚠ {w}</p>)}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="liquid-glass-island rounded-[32px] p-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="p-2">Mått</th><th className="p-2">A</th><th className="p-2">B</th>
                    <th className="p-2" title="Bonferroni-justerat">p (just.)</th><th className="p-2" title="Cohens d">d</th>
                  </tr>
                </thead>
                <tbody>
                  {result.per_metric.map(r => (
                    <tr key={r.metric} className="border-t border-slate-900/5">
                      <td className="p-2 font-semibold">{r.label}</td>
                      <td className="p-2 font-mono text-xs">{formatSummary(r.a, METRIC_DIGITS[r.metric])}</td>
                      <td className="p-2 font-mono text-xs">{formatSummary(r.b, METRIC_DIGITS[r.metric])}</td>
                      <td className={`p-2 font-mono text-xs ${r.p_adjusted !== null && r.p_adjusted < 0.05 ? "text-amber-700 font-bold" : ""}`}>{formatP(r.p_adjusted)}</td>
                      <td className="p-2 font-mono text-xs">{r.effect_size_d != null ? r.effect_size_d.toFixed(2) : "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-[11px] text-slate-500 p-2">
                Medel ± SD. p-värden från permutationstest (5 000 permutationer), Bonferroni-justerade.
                Vittring, bergart och skanningsupplösning kan också ge skillnader.
              </p>
            </div>
            <div className="liquid-glass-island rounded-[32px] p-4">
              <h3 className="font-bold text-sm text-slate-700 mb-2 px-2">Profiler (lägsta punkt i origo)</h3>
              {a.profile && b.profile ? (
                <div className="h-[320px]">
                  <PlotlyGraph
                    data={[a, b].map((s, i) => {
                      const p = normalizeProfile(s.profile!);
                      return { x: p.x, y: p.z, mode: "lines", name: i === 0 ? "A" : "B", line: { color: i === 0 ? "#0f172a" : "#b7410e", width: 2 } };
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
          </div>
        </>
      )}
    </div>
  );
}
