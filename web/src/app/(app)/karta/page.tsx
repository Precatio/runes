"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { API_URL } from "@/lib/api";
import { PERIOD_LABEL, rundata, type RundataMeta } from "@/lib/rundata";
import { corpus } from "@/lib/corpus";
import { useAuth } from "@/components/AuthContext";
import { InfoTip } from "@/components/Explain";
import type { MapPoint } from "@/components/RuneMap";
import PatternExplorer from "@/components/PatternExplorer";
import RealmPanel from "@/components/RealmPanel";
import NordicExplorer from "@/components/NordicExplorer";

const RuneMap = dynamic(() => import("@/components/RuneMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-slate-500">Laddar karta...</div>,
});

const STYLE_COLORS: Record<string, string> = {
  RAK: "#64748b", Fp: "#0891b2", KB: "#a16207", Pr1: "#16a34a", Pr2: "#65a30d",
  Pr3: "#d97706", Pr4: "#dc2626", Pr5: "#7c3aed",
};
const PERIOD_COLORS: Record<string, string> = { U: "#7c3aed", V: "#b7410e", M: "#0369a1" };
const STATUS_COLORS: Record<string, string> = { S: "#b7410e", A: "#0369a1", "?": "#d97706" };
const STATUS_LABEL: Record<string, string> = { S: "Signerad", A: "Attribuerad", "?": "Osäker attribuering", "": "Ingen ristare" };
const OVERVIEW_COLORS: Record<string, string> = {
  "kan vara felbedömd": "#dc2626", "omstridd": "#d97706", "stöds": "#16a34a", "svagt underlag": "#a3a3a3",
  "signerad": "#b7410e", "nytt förslag": "#0369a1", "möjligt förslag": "#7dd3fc", "inget förslag": "#cbd5e1",
};
// Categorical colours for the modes whose values come from the data (material, content, language trait)
const PALETTE = ["#0891b2", "#b7410e", "#16a34a", "#7c3aed", "#d97706", "#db2777", "#0369a1", "#65a30d", "#a16207", "#475569"];
const NONE = "#94a3b8";

type ColorMode = "style" | "period" | "status" | "material" | "category" | "trait" | "overview";
const COLOR_MODES: [ColorMode, string][] = [
  ["style", "stilgrupp"], ["period", "period"], ["status", "ristarstatus"], ["material", "material"],
  ["category", "innehåll"], ["trait", "språkdrag"], ["overview", "status i Stenöversikt"],
];

interface Labels { provinces: Record<string, string>; categories: Record<string, string>; traits: Record<string, { group: string; label: string }> }
interface Trait { key: string; label: string; definition: string; values: Record<string, number>; rows: Record<string, string> }

// The filters, as they appear in the address bar (so a map view can be shared)
const FILTER_KEYS = ["q", "province", "period", "style", "carver", "category", "material", "status", "cross", "trait", "value",
  "overview", "runestones", "measured", "color", "view", "pattern", "split", "hex", "places", "near", "km", "nearonly",
  "mode", "year", "borders", "npattern", "grouping"] as const;
type FilterKey = typeof FILTER_KEYS[number];
type Filters = Record<FilterKey, string>;
const EMPTY: Filters = Object.fromEntries(FILTER_KEYS.map(k => [k, ""])) as Filters;

function MapContent() {
  const params = useSearchParams();
  const selected = params.get("signum");
  const { user } = useAuth();
  const [points, setPoints] = useState<MapPoint[]>([]);
  const [labels, setLabels] = useState<Labels | null>(null);
  const [meta, setMeta] = useState<RundataMeta | null>(null);
  const [measured, setMeasured] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [f, setF] = useState<Filters>(() => ({ ...EMPTY, ...Object.fromEntries(FILTER_KEYS.map(k => [k, params.get(k) ?? ""])) }));
  const [qInput, setQInput] = useState(f.q);
  const [found, setFound] = useState<{ q: string; signa: Set<string> } | null>(null);
  const [loadedTrait, setLoadedTrait] = useState<Trait | null>(null);
  const [overview, setOverview] = useState<Map<string, string> | null>(null);
  const [copied, setCopied] = useState(false);
  const set = (k: FilterKey, v: string) => setF(x => ({ ...x, [k]: v, ...(k === "trait" ? { value: "" } : {}) }));
  const colorMode = (f.color || "style") as ColorMode;
  // The pattern map is the default view; a shared link with point filters (or a selected stone) opens the points
  const pointFilters = FILTER_KEYS.slice(0, 14).some(k => f[k]);
  const view = f.view || (selected || pointFilters ? "punkter" : "monster");
  const [showFilters, setShowFilters] = useState(pointFilters);

  useEffect(() => {
    rundata.geo()
      .then(g => {
        setLabels({ provinces: g.provinces, categories: g.categories, traits: g.traits });
        setPoints(g.rows.map(([signum, lat, lon, per, st, carvers, lost, province, object, material, cross, status, categories, runestone]) => ({
          signum, lat, lon, period: per, style: st, carvers, lost: lost === 1, province, object, material,
          cross: cross === 1, carverStatus: status, categories, runestone: runestone === 1,
        })));
      })
      .catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta kartdata."));
    rundata.meta().then(setMeta).catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    corpus.list().then(es => setMeasured(new Set(es.map(e => e.signum)))).catch(() => {});
  }, [user]);

  // Free text: wait until typing stops, then ask the server which inscriptions contain the text
  useEffect(() => {
    const t = setTimeout(() => setF(x => (x.q === qInput.trim() ? x : { ...x, q: qInput.trim() })), 400);
    return () => clearTimeout(t);
  }, [qInput]);
  useEffect(() => {
    if (f.q.length < 2) return;
    let cancelled = false;
    fetch(`${API_URL}/api/rundata/geo/match?q=${encodeURIComponent(f.q)}`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then((d: { signa: string[] }) => { if (!cancelled) setFound({ q: f.q, signa: new Set(d.signa) }); })
      .catch(() => { if (!cancelled) setFound({ q: f.q, signa: new Set() }); });
    return () => { cancelled = true; };
  }, [f.q]);
  const matches = f.q.length >= 2 && found?.q === f.q ? found.signa : null;

  // A language trait is fetched when it is used as a filter or for colour
  useEffect(() => {
    if (!f.trait || loadedTrait?.key === f.trait) return;
    let cancelled = false;
    fetch(`${API_URL}/api/rundata/geo/trait/${encodeURIComponent(f.trait)}`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then((d: Trait) => { if (!cancelled) setLoadedTrait(d); })
      .catch(e => setError(e instanceof Error ? e.message : "Språkdraget kunde inte hämtas."));
    return () => { cancelled = true; };
  }, [f.trait, loadedTrait]);
  const trait = f.trait && loadedTrait?.key === f.trait ? loadedTrait : null;

  // Stenöversikt's status (support for Rundata's carver, alternatives) for the Swedish Viking Age runestones
  useEffect(() => {
    if ((!f.overview && colorMode !== "overview") || overview) return;
    fetch(`${API_URL}/api/research/overview`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then((d: { stones: { signum: string; status: string }[] }) => setOverview(new Map(d.stones.map(s => [s.signum, s.status]))))
      .catch(e => setError(e instanceof Error ? e.message : "Stenöversikten kunde inte hämtas."));
  }, [f.overview, colorMode, overview]);

  // Keep the address bar in step with the filters
  useEffect(() => {
    const qs = new URLSearchParams();
    if (selected) qs.set("signum", selected);
    for (const k of FILTER_KEYS) if (f[k]) qs.set(k, f[k]);
    const url = `${window.location.pathname}${qs.size ? `?${qs}` : ""}`;
    window.history.replaceState(null, "", url);
  }, [f, selected]);

  const carverOptions = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of points) for (const c of p.carvers.split("; ").filter(Boolean)) counts.set(c, (counts.get(c) ?? 0) + 1);
    return [...counts.entries()].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).map(([c]) => c);
  }, [points]);
  const count = (key: (p: MapPoint) => string[]) => {
    const c = new Map<string, number>();
    for (const p of points) for (const v of key(p)) if (v) c.set(v, (c.get(v) ?? 0) + 1);
    return [...c.entries()].sort((a, b) => b[1] - a[1]);
  };
  const provinceOptions = useMemo(() => count(p => [p.province]), [points]); // eslint-disable-line react-hooks/exhaustive-deps
  const materialOptions = useMemo(() => count(p => [p.material]), [points]); // eslint-disable-line react-hooks/exhaustive-deps
  const categoryOptions = useMemo(() => count(p => p.categories), [points]); // eslint-disable-line react-hooks/exhaustive-deps

  const visible = useMemo(() => points
    .map(p => ({ ...p, measured: measured.has(p.signum), note: trait ? `${trait.label}: ${trait.rows[p.signum] ?? "–"}` : undefined }))
    .filter(p => ((!f.period || p.period === f.period)
      && (!f.style || p.style === f.style)
      && (!f.carver || p.carvers.split("; ").includes(f.carver))
      && (!f.province || p.province === f.province)
      && (!f.category || p.categories.includes(f.category))
      && (!f.material || p.material === f.material)
      && (!f.status || (f.status === "none" ? p.carverStatus === "" : p.carverStatus === f.status))
      && (!f.cross || (f.cross === "ja") === p.cross)
      && (!f.runestones || p.runestone)
      && (!f.measured || p.measured)
      && (!matches || matches.has(p.signum))
      && (!f.trait || !trait || (f.value ? trait.rows[p.signum] === f.value : p.signum in trait.rows))
      && (!f.overview || !overview || overview.get(p.signum) === f.overview))
      || p.signum === selected),
  [points, measured, f, matches, trait, overview, selected]);

  // Colours for the modes whose values come from the data
  const dataColors = useMemo(() => {
    const values = colorMode === "material" ? materialOptions.map(([k]) => k)
      : colorMode === "category" ? categoryOptions.map(([k]) => k)
      : colorMode === "trait" && trait ? Object.keys(trait.values) : [];
    return Object.fromEntries(values.slice(0, PALETTE.length).map((v, i) => [v, PALETTE[i]]));
  }, [colorMode, materialOptions, categoryOptions, trait]);
  // An inscription's main content: the rarest of its categories (most inscriptions are memorials)
  const mainCategory = (p: MapPoint) => p.categories.length ? [...p.categories].sort((a, b) =>
    (categoryOptions.find(c => c[0] === a)?.[1] ?? 0) - (categoryOptions.find(c => c[0] === b)?.[1] ?? 0))[0] : "";

  const colorFor = (p: MapPoint) => {
    switch (colorMode) {
      case "period": return PERIOD_COLORS[p.period ?? ""] ?? NONE;
      case "status": return STATUS_COLORS[p.carverStatus] ?? NONE;
      case "material": return dataColors[p.material] ?? NONE;
      case "category": return dataColors[mainCategory(p)] ?? NONE;
      case "trait": return trait ? dataColors[trait.rows[p.signum] ?? ""] ?? NONE : NONE;
      case "overview": return OVERVIEW_COLORS[overview?.get(p.signum) ?? ""] ?? NONE;
      default: return STYLE_COLORS[p.style ?? ""] ?? NONE;
    }
  };
  const legend: (readonly [string, string])[] =
    colorMode === "period" ? Object.entries(PERIOD_COLORS).map(([k, c]) => [PERIOD_LABEL[k], c] as const)
    : colorMode === "status" ? Object.entries(STATUS_COLORS).map(([k, c]) => [STATUS_LABEL[k], c] as const)
    : colorMode === "overview" ? Object.entries(OVERVIEW_COLORS).map(([k, c]) => [k, c] as const)
    : colorMode === "category" ? Object.entries(dataColors).map(([k, c]) => [labels?.categories[k] ?? k, c] as const)
    : colorMode === "material" || colorMode === "trait" ? Object.entries(dataColors).map(([k, c]) => [k, c] as const)
    : Object.entries(STYLE_COLORS).map(([k, c]) => [k, c] as const);
  const noneLabel = colorMode === "trait" ? (trait ? "Draget går inte att avgöra" : "Välj ett språkdrag")
    : colorMode === "overview" ? "Ingen vikingatida runsten i Sverige" : colorMode === "category" ? "Ingen kategori" : "Uppgift saknas";

  // Where the visible inscriptions are
  const byProvince = useMemo(() => {
    const c = new Map<string, number>();
    for (const p of visible) c.set(p.province, (c.get(p.province) ?? 0) + 1);
    return [...c.entries()].sort((a, b) => b[1] - a[1]);
  }, [visible]);

  const name = (code: string) => labels?.provinces[code] ?? code;
  const chips: [FilterKey, string][] = [
    ["q", f.q && `Text: "${f.q}"`], ["province", f.province && name(f.province)], ["period", f.period && PERIOD_LABEL[f.period]],
    ["style", f.style && `Stil ${f.style}`], ["carver", f.carver && `Ristare: ${f.carver}`],
    ["category", f.category && (labels?.categories[f.category] ?? f.category)], ["material", f.material && `Material: ${f.material}`],
    ["status", f.status && (f.status === "none" ? "Ingen ristare" : STATUS_LABEL[f.status])], ["cross", f.cross && (f.cross === "ja" ? "Med kors" : "Utan kors")],
    ["trait", f.trait && `${labels?.traits[f.trait]?.label ?? f.trait}${f.value ? `: ${f.value}` : ""}`],
    ["overview", f.overview && `Stenöversikt: ${f.overview}`], ["runestones", f.runestones && "Vikingatida runstenar"],
    ["measured", f.measured && "Uppmätta"],
  ].filter(([, v]) => v) as [FilterKey, string][];
  const nFilters = chips.length;

  const exportCsv = () => {
    const head = ["signum", "landskap", "lat", "lon", "period", "stilgrupp", "ristare", "ristarstatus", "material", "kors", "innehåll", "föremål", "försvunnen"]
      .concat(trait ? [trait.label] : []).concat(overview ? ["status i Stenöversikt"] : []);
    const esc = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
    const rows = visible.map(p => [p.signum, name(p.province), p.lat, p.lon, p.period ?? "", p.style ?? "", p.carvers, STATUS_LABEL[p.carverStatus],
      p.material, p.cross ? "ja" : "nej", p.categories.map(c => labels?.categories[c] ?? c).join("; "), p.object, p.lost ? "ja" : "nej"]
      .concat(trait ? [trait.rows[p.signum] ?? ""] : []).concat(overview ? [overview.get(p.signum) ?? ""] : []));
    const blob = new Blob(["﻿" + [head, ...rows].map(r => r.map(esc).join(";")).join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "karta-inskrifter.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };
  const copyLink = async () => {
    try { await navigator.clipboard.writeText(window.location.href); setCopied(true); setTimeout(() => setCopied(false), 1800); } catch { /* clipboard unavailable */ }
  };

  const select = "liquid-glass-input-wrapper rounded-xl px-2 sm:px-3 py-2 text-slate-900 text-sm font-semibold outline-none w-full max-w-full";
  const label = "flex flex-col gap-1 text-[11px] font-bold uppercase tracking-wider text-slate-500 min-w-0";

  // min-h-full, not h-full: the pattern view is taller than the window, and the note the app layout puts after the
  // page must come after all of it, not at the window's height
  return (
    <div className="flex flex-col min-h-full w-full max-w-7xl mx-auto p-4 md:p-6 gap-4">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Karta</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Hitta mönster och samband: välj ett drag – tro, skrift eller innehåll – och jämför det med tiden, med platser som
          ortnamn, kyrkor och fornlämningar, eller med kluster som R har hittat. Börja gärna med ett fynd under Upptäck. Under
          Punkter finns varje inskrift med filter, och vyn kan delas och laddas ner som tabell. Under Jämför länder ställs
          danska, norska och svenska runstenar mot varandra, och där finns spåren av påverkan över gränserna. Rikenas
          ungefärliga gränser omkring 890, 1025 och 1200 kan läggas på alla kartor.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2" role="tablist" aria-label="Kartvy">
        {([["monster", "Mönsterkarta"], ["punkter", "Punkter"], ["norden", "Jämför länder"]] as const).map(([k, l]) => (
          <button key={k} role="tab" aria-selected={view === k}
            // The comparison of the countries opens with the realms about 1025 on the map
            onClick={() => setF(x => ({ ...x, view: k, ...(k === "norden" && !x.borders ? { borders: "1025" } : {}) }))}
            className={`px-4 py-2 rounded-full text-sm font-bold border ${view === k ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"}`}>
            {l}
          </button>
        ))}
      </div>

      {view === "monster" && (
        <PatternExplorer f={f} set={(k, v) => set(k as FilterKey, v)} patch={p => setF(x => ({ ...x, ...p }))}
          onError={setError} provinceName={name} />
      )}

      {view === "norden" && <NordicExplorer f={f} set={(k, v) => set(k as FilterKey, v)} onError={setError} />}

      {view === "punkter" && (
      <>
      <div className="liquid-glass-island rounded-[28px] p-4 space-y-3">
        {showFilters && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
          <label className={`${label} col-span-2 sm:col-span-3 lg:col-span-2`}>Sök i texten
            <input value={qInput} onChange={e => setQInput(e.target.value)} placeholder="t.ex. grikk, bro, Ingvar"
              className={`${select} font-normal`} />
          </label>
          <label className={label}>Landskap
            <select value={f.province} onChange={e => set("province", e.target.value)} className={select}>
              <option value="">Alla</option>
              {provinceOptions.map(([k, n]) => <option key={k} value={k}>{name(k)} ({n})</option>)}
            </select>
          </label>
          <label className={label}>Period
            <select value={f.period} onChange={e => set("period", e.target.value)} className={select}>
              <option value="">Alla</option>
              {Object.entries(PERIOD_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <label className={label}>Stilgrupp
            <select value={f.style} onChange={e => set("style", e.target.value)} className={select}>
              <option value="">Alla</option>
              {Object.keys(STYLE_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className={label}>Ristare
            <select value={f.carver} onChange={e => set("carver", e.target.value)} className={select}>
              <option value="">Alla</option>
              {carverOptions.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className={label}>Innehåll
            <select value={f.category} onChange={e => set("category", e.target.value)} className={select}>
              <option value="">Allt</option>
              {categoryOptions.map(([k, n]) => <option key={k} value={k}>{labels?.categories[k] ?? k} ({n})</option>)}
            </select>
          </label>
          <label className={label}>Ristarstatus
            <select value={f.status} onChange={e => set("status", e.target.value)} className={select}>
              <option value="">Alla</option>
              <option value="S">Signerad</option><option value="A">Attribuerad</option><option value="?">Osäker attribuering</option>
              <option value="none">Ingen ristare</option>
            </select>
          </label>
          <label className={label}>Material
            <select value={f.material} onChange={e => set("material", e.target.value)} className={select}>
              <option value="">Alla</option>
              {materialOptions.map(([k, n]) => <option key={k} value={k}>{k} ({n})</option>)}
            </select>
          </label>
          <label className={label}>Kors
            <select value={f.cross} onChange={e => set("cross", e.target.value)} className={select}>
              <option value="">Med eller utan</option><option value="ja">Med kors</option><option value="nej">Utan kors</option>
            </select>
          </label>
          <label className={label}>
            <span>Språkdrag<InfoTip text="Drag i ljud, stavning, språkbruk och skrift, lästa ur inskriften där ordet finns (METHODS.md, avsnitt 9). Välj ett drag och eventuellt ett värde." /></span>
            <select value={f.trait} onChange={e => set("trait", e.target.value)} className={select}>
              <option value="">Inget</option>
              {labels && Object.entries(labels.traits).map(([k, t]) => <option key={k} value={k}>{t.label}</option>)}
            </select>
          </label>
          <label className={label}>Värde
            <select value={f.value} onChange={e => set("value", e.target.value)} className={select} disabled={!trait}>
              <option value="">{trait ? "Alla där draget går att avgöra" : "–"}</option>
              {trait && Object.entries(trait.values).map(([v, n]) => <option key={v} value={v}>{v} ({n})</option>)}
            </select>
          </label>
          <label className={label}>
            <span>Stenöversikt<InfoTip text="Stödet för Rundatas ristare och starkaste alternativ, för svenska vikingatida runstenar (se Stenöversikt)." /></span>
            <select value={f.overview} onChange={e => set("overview", e.target.value)} className={select}>
              <option value="">Alla</option>
              {Object.keys(OVERVIEW_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
        </div>
        )}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm font-semibold text-slate-700">
          <button onClick={() => setShowFilters(!showFilters)} aria-expanded={showFilters}
            className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:bg-slate-50">
            {showFilters ? "Dölj filter" : `Filter${nFilters ? ` (${nFilters})` : ""}`}
          </button>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={!!f.runestones} onChange={e => set("runestones", e.target.checked ? "1" : "")} />
            Bara svenska vikingatida runstenar
          </label>
          {user && (
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={!!f.measured} onChange={e => set("measured", e.target.checked ? "1" : "")} />
              Endast uppmätta ({measured.size})
            </label>
          )}
          <label className="flex items-center gap-2">Färg efter
            <select value={colorMode} onChange={e => set("color", e.target.value === "style" ? "" : e.target.value)} className={`${select} py-1.5`}>
              {COLOR_MODES.map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <span className="ml-auto text-slate-500">{visible.length.toLocaleString("sv-SE")} inskrifter</span>
          <button onClick={exportCsv} disabled={!visible.length} className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:bg-slate-50 disabled:opacity-40">
            Ladda ner tabell (CSV)
          </button>
          <button onClick={copyLink} className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:bg-slate-50">
            {copied ? "Länken kopierad" : "Kopiera länk"}
          </button>
        </div>
        {nFilters > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {chips.map(([k, v]) => (
              <button key={k} onClick={() => { set(k, ""); if (k === "q") setQInput(""); }}
                className="inline-flex items-center gap-1.5 rounded-full bg-slate-900 text-white px-3 py-1 text-xs font-semibold hover:bg-black"
                title="Ta bort filtret">
                {v}<span aria-hidden>×</span>
              </button>
            ))}
            <button onClick={() => { setF(x => ({ ...EMPTY, color: x.color, borders: x.borders })); setQInput(""); }} className="text-xs font-semibold text-[#b7410e] hover:underline">
              Rensa alla
            </button>
          </div>
        )}
        {byProvince.length > 0 && nFilters > 0 && (
          <p className="text-xs text-slate-600">
            <span className="font-bold text-slate-500 uppercase tracking-wider text-[11px] mr-2">Fördelning</span>
            {byProvince.slice(0, 8).map(([k, n]) => `${name(k)} ${n}`).join(" · ")}{byProvince.length > 8 ? ` · ${byProvince.length - 8} till` : ""}
          </p>
        )}
        {trait && <p className="text-xs text-slate-600"><span className="font-semibold">{trait.label}:</span> {trait.definition}</p>}
        <div className="border-t border-slate-900/5 pt-3">
          <RealmPanel value={f.borders} onChange={v => set("borders", v)} />
        </div>
      </div>

      {error && <p className="text-red-700 font-semibold">{error}</p>}

      <div className="liquid-glass-island rounded-[24px] sm:rounded-[32px] p-1.5 sm:p-2 flex-1 min-h-[70dvh] sm:min-h-[520px] relative">
        <RuneMap points={visible} colorFor={colorFor} selected={selected} realm={f.borders || undefined}
          fitKey={nFilters ? JSON.stringify({ ...f, color: "", borders: "" }) + (matches ? matches.size : "") + (trait ? trait.key : "") + (overview ? "o" : "") : undefined} />
        <div className="absolute bottom-3 left-3 sm:bottom-6 sm:left-6 z-[500] bg-white/90 rounded-xl px-3 py-2 shadow text-[11px] sm:text-xs space-y-1 max-h-[40%] sm:max-h-[60%] max-w-[60%] overflow-y-auto">
          {legend.map(([l, color]) => (
            <div key={l} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full inline-block shrink-0" style={{ background: color }} />{l}
            </div>
          ))}
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block shrink-0" style={{ background: NONE }} />{noneLabel}</div>
          <div className="text-slate-500 pt-1">Streckad: försvunnen · svart kant: uppmätt</div>
        </div>
      </div>
      </>
      )}
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
