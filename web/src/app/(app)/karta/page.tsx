"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { PERIOD_LABEL, rundata, type RundataMeta } from "@/lib/rundata";
import { corpus } from "@/lib/corpus";
import { useAuth } from "@/components/AuthContext";
import type { MapPoint } from "@/components/RuneMap";

const RuneMap = dynamic(() => import("@/components/RuneMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-slate-500">Laddar karta...</div>,
});

const STYLE_COLORS: Record<string, string> = {
  RAK: "#64748b", Fp: "#0891b2", KB: "#a16207", Pr1: "#16a34a", Pr2: "#65a30d",
  Pr3: "#d97706", Pr4: "#dc2626", Pr5: "#7c3aed",
};
const PERIOD_COLORS: Record<string, string> = { U: "#7c3aed", V: "#b7410e", M: "#0369a1" };
const NONE = "#94a3b8";

type ColorMode = "style" | "period";

function MapContent() {
  const params = useSearchParams();
  const selected = params.get("signum");
  const { user } = useAuth();
  const [points, setPoints] = useState<MapPoint[]>([]);
  const [meta, setMeta] = useState<RundataMeta | null>(null);
  const [measured, setMeasured] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<ColorMode>("style");
  const [period, setPeriod] = useState("");
  const [style, setStyle] = useState("");
  const [carver, setCarver] = useState("");
  const [onlyMeasured, setOnlyMeasured] = useState(false);

  useEffect(() => {
    rundata.geo()
      .then(g => setPoints(g.rows.map(([signum, lat, lon, per, st, carvers, lost]) => ({
        signum, lat, lon, period: per, style: st, carvers, lost: lost === 1,
      }))))
      .catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta kartdata."));
    rundata.meta().then(setMeta).catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    corpus.list().then(es => setMeasured(new Set(es.map(e => e.signum)))).catch(() => {});
  }, [user]);

  const carverOptions = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of points) for (const c of p.carvers.split("; ").filter(Boolean)) counts.set(c, (counts.get(c) ?? 0) + 1);
    return [...counts.entries()].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).map(([c]) => c);
  }, [points]);

  const visible = useMemo(() => points
    .map(p => ({ ...p, measured: measured.has(p.signum) }))
    .filter(p => (!period || p.period === period)
      && (!style || p.style === style)
      && (!carver || p.carvers.split("; ").includes(carver))
      && (!onlyMeasured || p.measured)
      || p.signum === selected),
  [points, measured, period, style, carver, onlyMeasured, selected]);

  const colorFor = (p: MapPoint) =>
    colorMode === "style" ? STYLE_COLORS[p.style ?? ""] ?? NONE : PERIOD_COLORS[p.period ?? ""] ?? NONE;
  const legend = colorMode === "style"
    ? Object.entries(STYLE_COLORS).map(([k, c]) => [k, c] as const)
    : Object.entries(PERIOD_COLORS).map(([k, c]) => [PERIOD_LABEL[k], c] as const);

  const select = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-slate-900 text-sm font-semibold outline-none";

  return (
    <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 gap-4">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Karta</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Geografisk spridning av inskrifter med koordinater i Rundata. Filtrera på period, stilgrupp och ristare.
        </p>
      </div>

      <div className="liquid-glass-island rounded-[28px] p-4 flex flex-wrap gap-3 items-center">
        <select value={colorMode} onChange={e => setColorMode(e.target.value as ColorMode)} className={select}>
          <option value="style">Färg efter stilgrupp</option>
          <option value="period">Färg efter period</option>
        </select>
        <select value={period} onChange={e => setPeriod(e.target.value)} className={select}>
          <option value="">Alla perioder</option>
          {Object.entries(PERIOD_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={style} onChange={e => setStyle(e.target.value)} className={select}>
          <option value="">Alla stilgrupper</option>
          {Object.keys(STYLE_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={carver} onChange={e => setCarver(e.target.value)} className={select}>
          <option value="">Alla ristare</option>
          {carverOptions.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        {user && (
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <input type="checkbox" checked={onlyMeasured} onChange={e => setOnlyMeasured(e.target.checked)} />
            Endast uppmätta ({measured.size})
          </label>
        )}
        <span className="ml-auto text-sm text-slate-500 font-semibold">{visible.length.toLocaleString("sv-SE")} inskrifter</span>
      </div>

      {error && <p className="text-red-700 font-semibold">{error}</p>}

      <div className="liquid-glass-island rounded-[32px] p-2 flex-1 min-h-[520px] relative">
        <RuneMap points={visible} colorFor={colorFor} selected={selected} />
        <div className="absolute bottom-6 left-6 z-[500] bg-white/90 rounded-xl px-3 py-2 shadow text-xs space-y-1">
          {legend.map(([label, color]) => (
            <div key={label} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full inline-block" style={{ background: color }} />{label}
            </div>
          ))}
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block" style={{ background: NONE }} />Uppgift saknas</div>
          <div className="text-slate-500 pt-1">Streckad: försvunnen · svart kant: uppmätt</div>
        </div>
      </div>
      {meta && <p className="text-[11px] text-slate-500">Uppgifter ur {meta.source}. {meta.attribution} Kartdata © OpenStreetMap-bidragsgivare.</p>}
    </div>
  );
}

export default function MapPage() {
  return (
    <Suspense fallback={null}>
      <MapContent />
    </Suspense>
  );
}
