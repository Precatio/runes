"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import PlotlyGraph from "@/components/PlotlyGraph";
import { useAuth } from "@/components/AuthContext";
import { corpus, corpusToRows, CORPUS_LICENSE, type CorpusEntry } from "@/lib/corpus";
import { downloadFile, toCSV } from "@/lib/export";
import { FEATURE_TYPES, METRICS, METRIC_DIGITS, METRIC_LABELS, formatSummary, type FeatureType } from "@/lib/metrics";
import { rundata, type Carver } from "@/lib/rundata";
import { stats, type ClusterResult } from "@/lib/stats";

// Carver per signum according to Rundata: only one certain signed/attributed carver counts as a label
function labelFrom(carvers: Carver[]): string | null {
  const certain = carvers.filter(c => (c.kind === "S" || c.kind === "A") && !c.uncertain);
  return certain.length === 1 ? certain[0].name : null;
}

export default function CorpusPage() {
  const { user, loginWithGoogle } = useAuth();
  const [entries, setEntries] = useState<CorpusEntry[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [labels, setLabels] = useState<Record<string, string | null>>({});
  const [featureFilter, setFeatureFilter] = useState<FeatureType | "">("rune");
  const [cluster, setCluster] = useState<ClusterResult | null>(null);
  const [clusterError, setClusterError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    corpus.list()
      .then(es => { setEntries(es); setLoaded(true); })
      .catch(e => setError(e instanceof Error ? e.message : "Kunde inte läsa korpusen."));
  }, [user]);

  useEffect(() => {
    const missing = [...new Set(entries.map(e => e.signum))].filter(s => !(s in labels));
    if (missing.length === 0) return;
    Promise.all(missing.map(s => rundata.inscription(s).then(r => [s, labelFrom(r.carvers)] as const).catch(() => [s, null] as const)))
      .then(pairs => setLabels(prev => ({ ...prev, ...Object.fromEntries(pairs) })));
  }, [entries, labels]);

  const visible = useMemo(
    () => entries.filter(e => !featureFilter || e.feature_type === featureFilter),
    [entries, featureFilter],
  );

  const profiles = useMemo(() => {
    const groups: Record<string, CorpusEntry[]> = {};
    for (const e of visible) {
      const l = labels[e.signum];
      if (l) (groups[l] ??= []).push(e);
    }
    return Object.entries(groups)
      .map(([carver, es]) => ({
        carver,
        n: es.length,
        signa: [...new Set(es.map(e => e.signum))],
        means: Object.fromEntries(METRICS.map(m => [m, es.reduce((a, e) => a + e.means[m], 0) / es.length])),
      }))
      .sort((a, b) => b.n - a.n);
  }, [visible, labels]);

  const exportCSV = () => {
    downloadFile(`runforskning_korpus_${new Date().toISOString().slice(0, 10)}.csv`, toCSV(corpusToRows(entries)), "text/csv");
  };

  const runCluster = async () => {
    setClusterError(null);
    try {
      setCluster(await stats.cluster(visible.map(e => ({
        label: `${e.signum}${labels[e.signum] ? ` (${labels[e.signum]})` : ""}`,
        means: e.means,
      }))));
    } catch (e) {
      setCluster(null);
      setClusterError(e instanceof Error ? e.message : "Klustringen misslyckades.");
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Ta bort din mätning ur korpusen?")) return;
    await corpus.remove(id);
    setEntries(es => es.filter(e => e.id !== id));
  };

  if (!user) {
    return (
      <div className="max-w-3xl mx-auto p-8 liquid-glass-island rounded-[32px] text-center space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Delad mätkorpus</h2>
        <p className="text-slate-600">Korpusen är öppen för alla inloggade forskare. Logga in för att läsa och bidra.</p>
        <button onClick={loginWithGoogle} className="px-6 py-3 bg-slate-900 text-white font-bold rounded-2xl">Logga in med Google</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Delad mätkorpus</h2>
          <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
            Huggspårsmätningar som forskare har publicerat under {CORPUS_LICENSE}. Ristare hämtas från Rundata
            (endast säkra signerade eller attribuerade inskrifter). Bidra från 3D-analysen.
          </p>
        </div>
        <div className="flex gap-2">
          <select value={featureFilter} onChange={e => { setFeatureFilter(e.target.value as FeatureType | ""); setCluster(null); }}
            className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none">
            <option value="">Alla spårtyper</option>
            {Object.entries(FEATURE_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <button onClick={exportCSV} disabled={entries.length === 0}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-white border border-slate-300 hover:border-slate-900 disabled:opacity-40">
            Exportera CSV
          </button>
        </div>
      </div>
      {error && <p className="text-red-700 font-semibold">{error}</p>}

      <div className="liquid-glass-island rounded-[32px] p-4 overflow-x-auto">
        {!loaded ? <p className="p-4 text-slate-500">Läser korpusen...</p> : visible.length === 0 ? (
          <p className="p-4 text-slate-600">Inga mätningar ännu. Gör en analys i <Link href="/3d" className="text-[#b7410e] font-semibold">3D-vyn</Link> och välj ”Bidra till korpusen”.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="p-2">Signum</th><th className="p-2">Spår</th><th className="p-2">Ristare (Rundata)</th>
                <th className="p-2">Snitt</th>
                {(["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm"] as const).map(m => <th key={m} className="p-2">{METRIC_LABELS[m]}</th>)}
                <th className="p-2">Bidragsgivare</th><th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {visible.map(e => (
                <tr key={e.id} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold"><Link href={`/inskrifter?signum=${encodeURIComponent(e.signum)}`} className="hover:text-[#b7410e]">{e.signum}</Link></td>
                  <td className="p-2">{FEATURE_TYPES[e.feature_type]}</td>
                  <td className="p-2">{labels[e.signum] ?? <span className="text-slate-400">–</span>}</td>
                  <td className="p-2">{e.slices.length}</td>
                  {(["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm"] as const).map(m => (
                    <td key={m} className="p-2 font-mono text-xs">{formatSummary(e.summary[m], METRIC_DIGITS[m])}</td>
                  ))}
                  <td className="p-2 text-xs text-slate-600">{e.contributorName}{e.institution && `, ${e.institution}`}<br />{e.createdAt.slice(0, 10)} · {e.method_version}</td>
                  <td className="p-2 text-right">
                    {e.contributorUid === user.uid && (
                      <button onClick={() => remove(e.id)} className="text-xs text-red-700 font-semibold hover:underline">Ta bort</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="liquid-glass-island rounded-[32px] p-6">
          <h3 className="text-lg font-bold text-slate-900 mb-1">Ristarprofiler</h3>
          <p className="text-xs text-slate-500 mb-3">Medelvärden per ristare bland uppmätta stenar. Minst två stenar behövs för attribuering.</p>
          {profiles.length === 0 ? <p className="text-sm text-slate-500">Inga uppmätta stenar med känd ristare än.</p> : (
            <div className="space-y-2">
              {profiles.map(p => (
                <div key={p.carver} className="bg-white/60 rounded-xl p-3 text-sm">
                  <div className="flex justify-between font-semibold">
                    <span>{p.carver}</span><span className="text-slate-500">{p.n} mätningar · {p.signa.join(", ")}</span>
                  </div>
                  <div className="text-xs text-slate-600 font-mono mt-1">
                    {METRICS.map(m => `${METRIC_LABELS[m].split(" (")[0]} ${p.means[m].toFixed(METRIC_DIGITS[m])}`).join(" · ")}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="liquid-glass-island rounded-[32px] p-6">
          <div className="flex justify-between items-start mb-1">
            <h3 className="text-lg font-bold text-slate-900">Klustring (Ward)</h3>
            <button onClick={runCluster} disabled={visible.length < 3}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-slate-900 text-white disabled:opacity-40">Klustra</button>
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Hierarkisk klustring på standardiserade medelvärden (Wards metod, euklidiska avstånd), som i Kitzler Åhfeldts
            studier av huggteknik. Jämför helst en spårtyp i taget.
          </p>
          {clusterError && <p className="text-sm text-red-700">{clusterError}</p>}
          {cluster && (
            <div className="h-[360px]">
              <PlotlyGraph
                data={cluster.icoord.map((xs, i) => ({
                  type: "scatter", mode: "lines", x: xs, y: cluster.dcoord[i],
                  line: { color: "#0f172a", width: 1.5 }, hoverinfo: "skip", showlegend: false,
                }))}
                layout={{
                  margin: { l: 40, r: 10, t: 10, b: 120 },
                  xaxis: {
                    tickvals: cluster.order.map((_, i) => 5 + i * 10),
                    ticktext: cluster.order,
                    tickangle: -45,
                    zeroline: false,
                  },
                  yaxis: { title: "Avstånd (Ward)" },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
