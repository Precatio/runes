"use client";

import { useMemo, useRef, useState } from "react";
import PlotlyGraph from "@/components/PlotlyGraph";
import { API_URL } from "@/lib/api";
import type { ThreeDAnalysisResult, ToolHeuristic } from "@/lib/db";
import { downloadFile, safeFilename, toCSV } from "@/lib/export";
import { METRICS, METRIC_DIGITS, METRIC_LABELS, type FeatureType, type Metric, type SliceMetrics, type Summary } from "@/lib/metrics";
import { angleColor, runeSampleNote, type AutoAnalysisResult, type AutoLabel, type AutoSlice } from "@/lib/mesh";
import { useSettings } from "@/components/SettingsContext";

const LABELS: Record<AutoLabel, { name: string; color: string }> = {
  rune: { name: "Runa", color: "#b7410e" },
  ornament: { name: "Ornamentik", color: "#0369a1" },
  unknown: { name: "Ej märkt", color: "#0f172a" },
  excluded: { name: "Utesluten", color: "#94a3b8" },
};

interface Props {
  result: AutoAnalysisResult;
  signum: string;
  metaStone: string;
  metaWeathering: string;
  labels: AutoLabel[];
  onLabelsChange: (labels: AutoLabel[]) => void;
  onUse: (result: ThreeDAnalysisResult, featureType: FeatureType) => void;
  onSendToTwoD?: () => void;
  facitMode?: boolean;
}

function quickStats(values: number[]) {
  if (values.length === 0) return null;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const sd = values.length > 1 ? Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / (values.length - 1)) : 0;
  return { mean, sd };
}

export default function AutoGrooveReview({ result, signum, metaStone, metaWeathering, labels, onLabelsChange, onUse, onSendToTwoD, facitMode }: Props) {
  const { userName } = useSettings();
  const svgRef = useRef<SVGSVGElement>(null);
  const [tool, setTool] = useState<AutoLabel>("rune");
  const [drag, setDrag] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [using, setUsing] = useState(false);
  const range = result.angle_color_range;
  const W = result.image_width;
  const H = result.image_height;

  const toImage = (e: React.PointerEvent) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return { x: ((e.clientX - rect.left) / rect.width) * W, y: ((e.clientY - rect.top) / rect.height) * H };
  };

  const finishDrag = () => {
    if (!drag) return;
    const [xa, xb] = [Math.min(drag.x0, drag.x1), Math.max(drag.x0, drag.x1)];
    const [ya, yb] = [Math.min(drag.y0, drag.y1), Math.max(drag.y0, drag.y1)];
    const isClick = xb - xa < 4 && yb - ya < 4;
    if (isClick) {
      // Select the nearest accepted point
      let best = -1;
      let bestD = 12 * 12;
      result.slices.forEach((s, i) => {
        if (!s.accepted) return;
        const d = (s.img_x - drag.x0) ** 2 + (s.img_y - drag.y0) ** 2;
        if (d < bestD) { bestD = d; best = i; }
      });
      setSelected(best >= 0 ? best : null);
    } else {
      onLabelsChange(labels.map((l, i) => {
        const s = result.slices[i];
        return s.accepted && s.img_x >= xa && s.img_x <= xb && s.img_y >= ya && s.img_y <= yb ? tool : l;
      }));
    }
    setDrag(null);
  };

  const groups = useMemo(() => {
    const out: Record<AutoLabel, AutoSlice[]> = { rune: [], ornament: [], unknown: [], excluded: [] };
    result.slices.forEach((s, i) => { if (s.accepted) out[labels[i]].push(s); });
    return out;
  }, [result.slices, labels]);

  const use = async (featureType: FeatureType, picked: AutoSlice[]) => {
    if (picked.length < 2) return;
    setUsing(true);
    try {
      const slices: SliceMetrics[] = picked.map(s => ({
        ...(Object.fromEntries(METRICS.map(m => [m, s[m] as number])) as Record<Metric, number>),
        position_mm: s.position_mm,
        fit_r2: s.fit_r2,
        profile: s.profile,
        point: s.point,
        direction: s.direction,
        up: s.up,
      }));
      const res = await fetch(`${API_URL}/api/stats/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slices, meta_stone: metaStone, meta_weathering: metaWeathering }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Sammanfattningen misslyckades");
      const body: { summary: Record<Metric, Summary>; means: Record<Metric, number>; n: number; tool_heuristic: ToolHeuristic } = await res.json();
      // Representative profile: the slice closest to the median angle
      const sorted = [...picked].sort((a, b) => (a.apex_vinkel_deg ?? 0) - (b.apex_vinkel_deg ?? 0));
      const rep = sorted[Math.floor(sorted.length / 2)];
      onUse({
        results: {
          ...body.means,
          troligt_verktyg: body.tool_heuristic.label,
        },
        summary: body.summary,
        slices,
        tool_heuristic: body.tool_heuristic,
        provenance: {
          ...result.provenance,
          feature_type: featureType,
          parameters: {
            ...result.provenance.parameters,
            selection: { label: featureType, n_slices: picked.length, n_accepted_total: result.counts.accepted },
          },
        },
        plot_data: rep.profile ? { x: rep.profile.x, z: rep.profile.z } : null,
      }, featureType);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Kunde inte använda urvalet.");
    } finally {
      setUsing(false);
    }
  };

  const exportCSV = () => {
    const rows = result.slices.map((s, i) => ({
      signum,
      label: s.accepted ? labels[i] : "rejected",
      accepted: s.accepted,
      reason: s.reason ?? "",
      ...Object.fromEntries(METRICS.map(m => [m, s[m]])),
      fit_r2: s.fit_r2,
      halfwidth_mm: s.halfwidth_mm,
      x: s.point?.[0], y: s.point?.[1], z: s.point?.[2],
      dir_x: s.direction?.[0], dir_y: s.direction?.[1], dir_z: s.direction?.[2],
      method_version: result.provenance.method_version,
      mesh_sha256: result.provenance.mesh?.sha256,
    }));
    downloadFile(`${safeFilename(signum || "automatisk")}_automatisk_analys.csv`, toCSV(rows), "text/csv");
  };

  // Facit for evaluating the rune detection (scripts/evaluate_rune_detection.py): positions and the researcher's labels
  const saveFacit = () => {
    const marked = result.slices.flatMap((s, i) => (s.accepted && s.point && labels[i] !== "unknown"
      ? [{ point: s.point, direction: s.direction, label: labels[i] }] : []));
    const facit = {
      type: "vitki-rune-facit", version: 1, signum, labeller: userName, created: new Date().toISOString(),
      mesh: result.provenance.mesh, method_version: result.provenance.method_version, parameters: result.parameters,
      legend: { rune: "runa", ornament: "slinglinje eller ornamentik", excluded: "spricka, vittring eller annat som inte är huggning" },
      labels: marked,
    };
    downloadFile(`${safeFilename(signum || "sten")}_facit.json`, JSON.stringify(facit, null, 1), "application/json");
  };
  const nUnmarked = result.slices.filter((s, i) => s.accepted && labels[i] === "unknown").length;

  const sel = selected !== null ? result.slices[selected] : null;
  const reasons = Object.entries(result.counts.rejection_reasons).sort((a, b) => b[1] - a[1]);
  const runesOnly = result.parameters.runes_only === true;
  const runeNote = runesOnly ? runeSampleNote(result.counts.runes_measured ?? 0) : null;

  return (
    <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-white/50 space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Granska den automatiska analysen</h3>
          <p className="text-xs text-slate-500 font-medium mt-1 max-w-2xl">
            {result.counts.accepted} godkända snitt av {result.counts.candidates}
            {runesOnly && <> i {result.counts.runes_measured} runor (av {result.counts.runes_identified} igenkända)</>}.
            Orange = hittade spår, grått = för brett för ett huggspår (mäts inte).
            {runesOnly && " Bara spår som känns igen som runor mäts; ornamentik, slingkanter och möjliga sprickor visas som små grå punkter."}
            {" "}Dra en ruta för att märka punkter, klicka på en punkt för att se dess profil.
          </p>
          {result.provenance.protocol && (
            <p className={`text-xs mt-2 ${result.provenance.protocol.compliant ? "text-emerald-800" : "text-amber-900"}`}>
              {result.provenance.protocol.compliant
                ? `Följer Vitki-protokollet (${result.provenance.protocol.version}).`
                : `Avviker från Vitki-protokollet: ${result.provenance.protocol.deviations.join("; ")}. Jämför bara med stenar mätta på samma sätt.`}
              {result.provenance.protocol.notes.map(n => ` ${n.charAt(0).toUpperCase()}${n.slice(1)}.`).join("")}
            </p>
          )}
          {runeNote && (
            <p className={`text-xs font-semibold mt-2 px-3 py-1.5 rounded-lg inline-block ${runeNote.ok ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}>
              {runeNote.text}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {onSendToTwoD && (
            <button onClick={onSendToTwoD} title="Ristningskartan visar spårdjupet oberoende av belysning och färg. Runutsnitt som ritas där får huggspårsmåtten inom utsnittet."
              className="px-3 py-2 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl">
              Öppna ristningskartan i 2D
            </button>
          )}
          <button onClick={exportCSV} className="px-3 py-2 bg-white border border-slate-300 hover:border-slate-900 text-xs font-bold rounded-xl">
            Exportera alla snitt (CSV)
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mr-1">Märk med ruta:</span>
        {(Object.keys(LABELS) as AutoLabel[]).map(l => (
          <button key={l} type="button" onClick={() => setTool(l)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${tool === l ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
            <span className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-middle" style={{ background: LABELS[l].color }} />
            {LABELS[l].name}
          </button>
        ))}
        <button type="button" onClick={() => onLabelsChange(result.slices.map(s => (!s.accepted ? "excluded" : !facitMode && s.feature === "rune" ? "rune" : "unknown")))}
          className="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-500 hover:text-slate-900">Återställ</button>
      </div>

      {facitMode && (
        <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-xs text-slate-700 space-y-2">
          <p><strong>Facit-läge.</strong> Alla spår är mätta och inget är förmärkt. Märk med rutor: <em>Runa</em> för runor,
            <em> Ornamentik</em> för slinglinjer och ornament, <em>Utesluten</em> för sprickor, vittring och annat som inte är
            huggning. Omärkta punkter räknas inte. Märk efter reliefen, inte efter färgerna.</p>
          <div className="flex flex-wrap items-center gap-2">
            <span>{nUnmarked} omärkta punkter.</span>
            <button type="button" onClick={saveFacit} className="px-3 py-1.5 bg-sky-700 hover:bg-sky-800 text-white font-bold rounded-lg">
              Spara facit (JSON)
            </button>
          </div>
        </div>
      )}

      <div className="relative w-full rounded-2xl overflow-hidden border border-slate-200 bg-white select-none">
        {/* eslint-disable-next-line @next/next/no-img-element -- generated data-URI image */}
        <img src={result.image_base64} alt="Spårkarta med mätpunkter" className="w-full h-auto block" draggable={false} />
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 w-full h-full cursor-crosshair touch-none"
          onPointerDown={e => { const p = toImage(e); setDrag({ x0: p.x, y0: p.y, x1: p.x, y1: p.y }); (e.target as Element).setPointerCapture?.(e.pointerId); }}
          onPointerMove={e => { if (drag) { const p = toImage(e); setDrag({ ...drag, x1: p.x, y1: p.y }); } }}
          onPointerUp={finishDrag}>
          {result.slices.map((s, i) => s.accepted && (
            <circle key={i} cx={s.img_x} cy={s.img_y} r={i === selected ? 7 : 4.5}
              fill={labels[i] === "excluded" ? "#cbd5e1" : angleColor(s.apex_vinkel_deg ?? 0, range)}
              stroke={LABELS[labels[i]].color} strokeWidth={labels[i] === "unknown" ? 1 : 2.5} />
          ))}
          {drag && (
            <rect x={Math.min(drag.x0, drag.x1)} y={Math.min(drag.y0, drag.y1)} width={Math.abs(drag.x1 - drag.x0)} height={Math.abs(drag.y1 - drag.y0)}
              fill={`${LABELS[tool].color}22`} stroke={LABELS[tool].color} strokeWidth={2} strokeDasharray="6 4" />
          )}
        </svg>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
        <span>V-vinkel:</span>
        <span className="h-2.5 w-40 rounded-full" style={{ background: `linear-gradient(90deg, ${["#440154", "#3e4989", "#26828e", "#35b779", "#fde725"].join(",")})` }} />
        <span>{range[0]}° – {range[1]}°</span>
        <span className="ml-auto">
          Upplösning {Number(result.parameters.resolution_mm).toFixed(2)} mm · brus {Number(result.parameters.noise_mm).toFixed(2)} mm ·
          tröskel {Number(result.parameters.threshold_mm).toFixed(2)} mm
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="p-2">Urval</th><th className="p-2">n</th><th className="p-2">V-vinkel</th><th className="p-2">Djup</th><th className="p-2">Bredd</th>
              </tr>
            </thead>
            <tbody>
              {(["rune", "ornament", "unknown"] as const).map(l => {
                const g = groups[l];
                const a = quickStats(g.map(s => s.apex_vinkel_deg ?? 0));
                const d = quickStats(g.map(s => s.spårdjup_mm ?? 0));
                const w = quickStats(g.map(s => s.spårbredd_mm ?? 0));
                return (
                  <tr key={l} className="border-t border-slate-900/5">
                    <td className="p-2 font-semibold"><span className="inline-block w-2.5 h-2.5 rounded-full mr-1.5" style={{ background: LABELS[l].color }} />{LABELS[l].name}</td>
                    <td className="p-2">{g.length}</td>
                    <td className="p-2 font-mono text-xs">{a ? `${a.mean.toFixed(1)} ± ${a.sd.toFixed(1)}°` : "–"}</td>
                    <td className="p-2 font-mono text-xs">{d ? `${d.mean.toFixed(2)} mm` : "–"}</td>
                    <td className="p-2 font-mono text-xs">{w ? `${w.mean.toFixed(2)} mm` : "–"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="flex flex-wrap gap-2 mt-3">
            <button disabled={using || groups.rune.length < 2} onClick={() => use("rune", groups.rune)}
              className="px-4 py-2 bg-[#b7410e] hover:bg-[#9a350b] text-white text-xs font-bold rounded-xl disabled:opacity-40">
              Använd runorna som resultat
            </button>
            <button disabled={using || groups.ornament.length < 2} onClick={() => use("ornament", groups.ornament)}
              className="px-4 py-2 bg-[#0369a1] hover:bg-[#075985] text-white text-xs font-bold rounded-xl disabled:opacity-40">
              Använd ornamentiken
            </button>
            <button disabled={using || groups.rune.length + groups.ornament.length + groups.unknown.length < 2}
              onClick={() => use("unknown", [...groups.rune, ...groups.ornament, ...groups.unknown])}
              className="px-4 py-2 bg-white border border-slate-300 hover:border-slate-900 text-xs font-bold rounded-xl disabled:opacity-40">
              Använd alla som inte är uteslutna
            </button>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Runor och ornamentik huggs ofta olika – märk dem separat för jämförbara resultat. Resultatet kan sedan exporteras,
            sparas i projektet eller delas i korpusen.
          </p>
          {reasons.length > 0 && (
            <details className="text-[11px] text-slate-500 mt-3">
              <summary className="cursor-pointer font-semibold">Varför {result.counts.rejected} snitt sorterades bort</summary>
              <ul className="mt-1 space-y-0.5">{reasons.map(([r, n]) => <li key={r}>{r}: {n}</li>)}</ul>
            </details>
          )}
        </div>

        <div>
          {sel ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-bold text-slate-900">Valt snitt</div>
                <div className="flex gap-1">
                  {(Object.keys(LABELS) as AutoLabel[]).map(l => (
                    <button key={l} type="button" onClick={() => onLabelsChange(labels.map((x, i) => (i === selected ? l : x)))}
                      className={`px-2 py-1 rounded-md text-[11px] font-bold border ${labels[selected!] === l ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-300 text-slate-600"}`}>
                      {LABELS[l].name}
                    </button>
                  ))}
                </div>
              </div>
              {sel.profile && (
                <div className="h-[200px] bg-white/70 rounded-xl border border-slate-200">
                  <PlotlyGraph
                    data={[{ x: sel.profile.x, y: sel.profile.z, mode: "lines+markers", marker: { size: 3, color: "#0f172a" }, line: { color: "#b7410e" } }]}
                    layout={{ margin: { l: 35, r: 10, t: 10, b: 30 }, xaxis: { title: "mm" }, yaxis: { title: "mm", scaleanchor: "x" }, showlegend: false, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }}
                  />
                </div>
              )}
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-700">
                {METRICS.map(m => (
                  <div key={m} className="flex justify-between"><span className="text-slate-500">{METRIC_LABELS[m]}</span><span className="font-mono">{(sel[m] as number)?.toFixed(METRIC_DIGITS[m])}</span></div>
                ))}
                <div className="flex justify-between"><span className="text-slate-500">Väggpassning (R²)</span><span className="font-mono">{sel.fit_r2?.toFixed(2)}</span></div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Klicka på en punkt i bilden för att se tvärsnittet och märka den.</p>
          )}
        </div>
      </div>
    </div>
  );
}
