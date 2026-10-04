"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PlotlyGraph from "@/components/PlotlyGraph";
import { rundata, type StyleDistribution, type StyleGroup } from "@/lib/rundata";

const COLORS: Record<string, string> = {
  RAK: "#64748b", Fp: "#0891b2", KB: "#a16207", Pr1: "#16a34a", Pr2: "#65a30d",
  Pr3: "#d97706", Pr4: "#dc2626", Pr5: "#7c3aed",
};

export default function StyleGroupsPage() {
  const [groups, setGroups] = useState<StyleGroup[]>([]);
  const [dist, setDist] = useState<StyleDistribution[]>([]);
  const [source, setSource] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    rundata.styles()
      .then(r => { setGroups(r.groups); setDist(r.distribution); setSource(r.source); })
      .catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta stilgrupper."));
  }, []);

  const byCode = Object.fromEntries(dist.map(d => [d.style, d]));
  const dated = groups.filter(g => g.from !== null);

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Stilgrupper</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Anne-Sofie Gräslunds stilgrupper för vikingatida runstenar, med fördelningen i Rundata.
          Dateringarna är ungefärliga och överlappar – de är inte skarpa gränser.
        </p>
      </div>
      {error && <p className="text-red-700 font-semibold">{error}</p>}

      {dated.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="liquid-glass-island rounded-[32px] p-6">
            <h3 className="font-bold text-slate-900 mb-2">Kronologi (ca)</h3>
            <div className="h-[300px]">
              <PlotlyGraph
                data={dated.map(g => ({
                  type: "bar",
                  orientation: "h",
                  y: [g.code],
                  x: [(g.to ?? 0) - (g.from ?? 0)],
                  base: [g.from],
                  marker: { color: COLORS[g.code] },
                  hovertemplate: `${g.code}: ca ${g.from}–${g.to}<extra></extra>`,
                  name: g.code,
                }))}
                layout={{
                  showlegend: false,
                  barmode: "overlay",
                  margin: { l: 50, r: 20, t: 10, b: 40 },
                  xaxis: { title: "År", range: [970, 1140] },
                  yaxis: { autorange: "reversed" },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                }}
              />
            </div>
          </div>
          <div className="liquid-glass-island rounded-[32px] p-6">
            <h3 className="font-bold text-slate-900 mb-2">Antal inskrifter i Rundata</h3>
            <div className="h-[300px]">
              <PlotlyGraph
                data={[
                  {
                    type: "bar",
                    x: dist.map(d => d.style),
                    y: dist.map(d => d.count - d.uncertain),
                    name: "Säker",
                    marker: { color: dist.map(d => COLORS[d.style]) },
                  },
                  {
                    type: "bar",
                    x: dist.map(d => d.style),
                    y: dist.map(d => d.uncertain),
                    name: "Osäker (?)",
                    marker: { color: dist.map(d => COLORS[d.style]), opacity: 0.35 },
                  },
                ]}
                layout={{
                  barmode: "stack",
                  margin: { l: 40, r: 10, t: 10, b: 40 },
                  legend: { orientation: "h", y: 1.1 },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                }}
              />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {groups.map(g => {
          const d = byCode[g.code];
          return (
            <div key={g.code} id={g.code} className="liquid-glass-island rounded-[32px] p-6 space-y-3 scroll-mt-6">
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 rounded-full" style={{ background: COLORS[g.code] }} />
                <h3 className="text-xl font-bold text-slate-900">{g.code}</h3>
                <span className="text-slate-500 font-medium">{g.name}</span>
                {g.from && <span className="ml-auto text-sm font-bold text-slate-700">ca {g.from}–{g.to}</span>}
              </div>
              <p className="text-sm text-slate-700">{g.features}</p>
              {d && (
                <div className="text-sm text-slate-600 space-y-1">
                  <div><strong>{d.count}</strong> inskrifter i Rundata{d.uncertain > 0 && ` (varav ${d.uncertain} osäkra)`}.</div>
                  <div>Landskap: {Object.entries(d.provinces).map(([p, n]) => `${p} ${n}`).join(", ")}</div>
                  {Object.keys(d.carvers).length > 0 && (
                    <div>
                      Ristare:{" "}
                      {Object.entries(d.carvers).map(([c, n], i) => (
                        <span key={c}>{i > 0 && ", "}<Link href={`/inskrifter?carver=${encodeURIComponent(c)}`} className="text-[#b7410e] hover:underline">{c}</Link> {n}</span>
                      ))}
                    </div>
                  )}
                  {d.examples.length > 0 && (
                    <div>
                      Exempel:{" "}
                      {d.examples.map((ex, i) => (
                        <span key={ex.signum}>{i > 0 && ", "}<Link href={`/inskrifter?signum=${encodeURIComponent(ex.signum)}`} className="text-[#b7410e] hover:underline">{ex.signum}</Link></span>
                      ))}
                    </div>
                  )}
                  <Link href={`/inskrifter?style=${encodeURIComponent(g.code)}`} className="inline-block text-xs font-bold text-slate-900 hover:underline pt-1">Alla {g.code}-inskrifter →</Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
      {source && <p className="text-[11px] text-slate-500">Källa för stilgrupperna: {source} Fördelningen bygger på Samnordisk runtextdatabas.</p>}
    </div>
  );
}
