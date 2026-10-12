"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import {
  nearPlace, periodShares, PLACE_STYLE, provinceTable, SHARE_CLASSES, TOO_FEW, type MapCircle, type MapMarker, type PatternStone,
  type PlaceKind, type PlaceLayer,
} from "@/lib/patternMap";
import type { Scan } from "@/components/LandscapeScan";

const PatternMaps = dynamic(() => import("@/components/PatternMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-slate-500">Laddar karta...</div>,
});
const LandscapeScan = dynamic(() => import("@/components/LandscapeScan"), { ssr: false });

// The pattern map (GET /api/research/pattern-map), the R scan of the landscape (GET /api/r/scan) and the hot spots and
// clusters (GET /api/r/hotspots), arranged around the user's question: which pattern, compared with what, and what it shows
interface PatternDef { key: string; label: string; group: string; help: string }
interface PlaceTest {
  km: number; n_near: number; n_far: number; k_near: number; k_far: number; share_near: number; share_far: number;
  or_crude: number; p_crude: number; or_mh: number | null; p_mh: number | null; strata: number;
}
interface HotCluster {
  center: string; lat: number; lon: number; radius_km: number; n: number; cases: number; rate_in: number; rate_out: number;
  rr: number; p: number; q_bh?: number; provinces: Record<string, number>; stones: string[]; halves?: { replicated: boolean };
}
interface HotPattern {
  key: string; n: number; cases: number; share: number; moran: { i: number; p: number; q_bh: number };
  n_hot: number; n_cold: number; stones: { signum: string; z: number; q: number }[]; clusters: HotCluster[]; best_cluster_p: number | null;
}
interface Hotspots { available: boolean; reason?: string; computed_at?: string; patterns: HotPattern[] }

type Mode = "" | "tid" | "plats" | "kluster";
const MODES: [Mode, string, string][] = [
  ["", "Andel", "Var mönstret är vanligt"],
  ["tid", "Tid", "Före och efter omkring 1050"],
  ["plats", "Platser", "Nära ortnamn, kyrkor, fornlämningar"],
  ["kluster", "Kluster", "Hot spots och kluster ur R"],
];
const HEX_SIZES = [10, 20, 40];
const NEAR_KM = [0.5, 1, 2, 3, 5];
const MIN_STONES = 5;
const HOT = "#b7410e", COLD = "#1c5cab";

// Province names when the page has not loaded its own yet
const PROVINCES: Record<string, string> = {
  U: "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", Vg: "Västergötland", Sm: "Småland", "Öl": "Öland", G: "Gotland",
  Vs: "Västmanland", Gs: "Gästrikland", "Nä": "Närke", Hs: "Hälsingland", M: "Medelpad", "Ån": "Ångermanland", J: "Jämtland",
  D: "Dalarna", Vr: "Värmland", Bo: "Bohuslän", Hr: "Härjedalen", Ds: "Dalsland", Sk: "Skåne", Bl: "Blekinge", Ha: "Halland",
};
const pct = (x: number) => `${Math.round(x * 100)} %`;
const n2 = (x: number | null | undefined) => (x == null ? "–" : x.toFixed(2).replace(".", ","));
const pText = (p: number | null | undefined) => (p == null ? "–" : p < 0.001 ? "< 0,001" : p.toFixed(3).replace(".", ","));
const kmText = (km: number) => `${String(km).replace(".", ",")} km`;

export default function PatternExplorer({ f, set, patch, onError, provinceName: pageName }: {
  f: Record<string, string>; set: (k: string, v: string) => void; patch: (p: Record<string, string>) => void;
  onError: (e: string) => void; provinceName: (code: string) => string;
}) {
  const provinceName = (code: string) => { const n = pageName(code); return n && n !== code ? n : PROVINCES[code] ?? code; };
  const [data, setData] = useState<{ patterns: PatternDef[]; placeKinds: PlaceKind[]; stones: PatternStone[] } | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);
  const [hot, setHot] = useState<Hotspots | null>(null);
  const [layers, setLayers] = useState<Record<string, PlaceLayer>>({});
  const [placeTest, setPlaceTest] = useState<{ key: string; result: PlaceTest | null } | null>(null);
  const [pickedCluster, setPickedCluster] = useState(0);

  useEffect(() => {
    fetch(`${API_URL}/api/research/pattern-map`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      // The values come as arrays in the order of the patterns and kinds of place (smaller to send); here they get keys
      .then((d: { patterns: PatternDef[]; place_kinds?: PlaceKind[];
                  stones: (Omit<PatternStone, "v" | "d"> & { v: (0 | 1 | null)[]; d?: (number | null)[] })[] }) => {
        const kinds = d.place_kinds ?? [];
        setData({ patterns: d.patterns, placeKinds: kinds, stones: d.stones.map(st => ({
          ...st, v: Object.fromEntries(d.patterns.map((x, i) => [x.key, st.v[i]])),
          d: Object.fromEntries(kinds.map((k, i) => [k.key, st.d?.[i] ?? null])) })) });
      })
      .catch(e => onError(e instanceof Error ? e.message : "Mönsterkartan kunde inte hämtas."));
    fetch(`${API_URL}/api/r/scan`).then(r => (r.ok ? r.json() : null)).then(setScan).catch(() => setScan(null));
    fetch(`${API_URL}/api/r/hotspots`).then(r => (r.ok ? r.json() : null)).then(setHot).catch(() => setHot(null));
  }, [onError]);

  const mode: Mode = (f.mode as Mode) || (f.split === "1" ? "tid" : "");
  const patternKey = f.pattern || data?.patterns[0]?.key || "";
  const patternDef = data?.patterns.find(x => x.key === patternKey);
  const label = (k: string) => data?.patterns.find(x => x.key === k)?.label ?? k;
  const kindLabel = (k: string) => data?.placeKinds.find(x => x.key === k)?.label ?? scan?.kind_labels?.[k] ?? k;
  const hexKm = Number(f.hex) || 20;
  const nearKind = mode === "plats" ? f.near : "";
  const nearKm = Number(f.km) || 2;
  const nearDef = data?.placeKinds.find(k => k.key === nearKind);
  const hp = hot?.available ? hot.patterns.find(x => x.key === patternKey) : undefined;

  // Place layers: the kind being compared is shown by itself; more can be added under "Fler inställningar"
  const extraKinds = useMemo(() => (f.places || "").split(",").filter(Boolean), [f.places]);
  const shownKinds = useMemo(() => [...new Set([...(nearKind ? [nearKind] : []), ...extraKinds])], [nearKind, extraKinds]);
  useEffect(() => {
    shownKinds.filter(k => !layers[k]).forEach(k => {
      fetch(`${API_URL}/api/research/places?kind=${encodeURIComponent(k)}`)
        .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
        .then((d: PlaceLayer) => setLayers(x => ({ ...x, [k]: d })))
        .catch(e => onError(e instanceof Error ? e.message : "Platserna kunde inte hämtas."));
    });
  }, [shownKinds, layers, onError]);
  const overlays = shownKinds.map(k => layers[k]).filter(Boolean);

  const testKey = nearKind && patternKey ? `${patternKey}|${nearKind}|${nearKm}` : "";
  useEffect(() => {
    if (!testKey) return;
    const [pt, kind, km] = testKey.split("|");
    fetch(`${API_URL}/api/research/place-test?pattern=${encodeURIComponent(pt)}&kind=${encodeURIComponent(kind)}&km=${km}`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(d => setPlaceTest({ key: testKey, result: d.result }))
      .catch(() => setPlaceTest({ key: testKey, result: null }));
  }, [testKey]);
  const test = placeTest?.key === testKey ? placeTest.result : undefined;

  const mapStones = useMemo(() => (data && nearKind && f.nearonly === "1" ? nearPlace(data.stones, nearKind, nearKm) : data?.stones ?? []),
                                [data, nearKind, nearKm, f.nearonly]);
  const periods = useMemo(() => (data && patternKey ? periodShares(data.stones, patternKey) : null), [data, patternKey]);
  const provinces = useMemo(() => (data && patternKey ? provinceTable(data.stones, patternKey) : []), [data, patternKey]);

  // Clusters and hot or cold stones of the chosen pattern, when comparing with clusters
  const coords = useMemo(() => new Map((data?.stones ?? []).map(s => [s.s, s])), [data]);
  const circles: MapCircle[] = mode === "kluster" && hp ? hp.clusters.map((c, i) => ({
    lat: c.lat, lon: c.lon, radiusKm: c.radius_km, color: HOT, dashed: i !== pickedCluster,
    label: `${pct(c.rate_in)} inne mot ${pct(c.rate_out)} utanför (${c.n} stenar, p ${pText(c.p)})`,
  })) : [];
  const markers: MapMarker[] = mode === "kluster" && hp ? hp.stones.flatMap(s => {
    const st = coords.get(s.signum);
    return st ? [{ lat: st.lat, lon: st.lon, color: s.z > 0 ? HOT : COLD, label: `${s.signum}: ${s.z > 0 ? "hett" : "kallt"} område (Gi* ${n2(s.z)})` }] : [];
  }) : [];

  // Discover: the strongest findings, one click away
  const discover = useMemo(() => {
    const out: { key: string; title: string; sub: string; text: string; strong: boolean; go: Record<string, string> }[] = [];
    for (const c of scan?.available ? scan.cells : []) {
      if (c.q_bh >= 0.05 || !c.halves?.replicated || c.feature === "neutral") continue;
      out.push({ key: `s-${c.feature}-${c.kind}`, title: label(c.feature), sub: kindLabel(c.kind), strong: true,
                 text: `${c.or > 1 ? "Vanligare" : "Ovanligare"} närmare: oddskvot ${n2(c.or)} när avståndet halveras`,
                 go: { pattern: c.feature, mode: "plats", near: c.kind, km: c.radius_km === 2 ? "" : String(c.radius_km), split: "" } });
    }
    for (const p of hot?.available ? hot.patterns : []) {
      p.clusters.forEach((c, i) => {
        if (!c.halves?.replicated || p.key === "neutral") return;
        out.push({ key: `h-${p.key}-${i}`, title: label(p.key), sub: `Kluster: ${c.center}`, strong: (c.q_bh ?? 1) < 0.05,
                   text: `${pct(c.rate_in)} inne mot ${pct(c.rate_out)} utanför, ${kmText(c.radius_km)}`,
                   go: { pattern: p.key, mode: "kluster", split: "" } });
      });
    }
    return out.sort((a, b) => Number(b.strong) - Number(a.strong));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scan, hot, data]);

  const box = "liquid-glass-island rounded-[24px] p-4";
  const step = "text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2";
  const seg = (on: boolean) => `px-3 py-1.5 rounded-lg text-xs font-bold border ${on ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"}`;

  if (!data) return <div className={`${box} text-slate-500`}>Hämtar mönstren …</div>;
  return (
    <div className="space-y-4">
      {discover.length > 0 && (
        <div>
          <p className={step}>Upptäck – fynd som håller i båda halvorna av korpusen</p>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {discover.map(d => (
              <button key={d.key} type="button" onClick={() => { patch(d.go); setPickedCluster(0); }}
                className="shrink-0 w-60 text-left rounded-2xl border border-slate-200 bg-white px-3 py-2.5 hover:border-slate-900 transition">
                <span className="block text-sm font-bold text-slate-900">{d.title}</span>
                <span className="block text-xs font-semibold text-[#b7410e]">{d.sub}</span>
                <span className="block text-xs text-slate-600 mt-1">{d.text}</span>
                {!d.strong && <span className="block text-[10px] text-slate-500 mt-1">möjligt – klarar inte justeringen över alla mönster</span>}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 items-start">
        <aside className="space-y-4">
          <div className={box}>
            <p className={step}>1. Mönster</p>
            <div className="space-y-2">
              {[...new Set(data.patterns.map(x => x.group))].map(g => (
                <div key={g}>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{g}</p>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {data.patterns.filter(x => x.group === g).map(x => (
                      <button key={x.key} onClick={() => set("pattern", x.key)} title={x.help} aria-pressed={patternKey === x.key}
                        className={`px-2 py-1 rounded-lg text-xs font-semibold border ${patternKey === x.key ? "bg-[#1c5cab] text-white border-[#1c5cab]" : "bg-white text-slate-700 border-slate-200 hover:border-slate-400"}`}>
                        {x.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            {patternDef && <p className="text-xs text-slate-600 mt-2">{patternDef.help}</p>}
          </div>

          <div className={box}>
            <p className={step}>2. Jämför med</p>
            <div className="grid grid-cols-2 gap-1.5" role="tablist" aria-label="Jämför med">
              {MODES.map(([k, l, help]) => (
                <button key={k || "andel"} role="tab" aria-selected={mode === k} title={help}
                  onClick={() => patch({ mode: k, split: "" })} className={`${seg(mode === k)} text-left`}>
                  <span className="block">{l}</span>
                  <span className={`block text-[10px] font-normal ${mode === k ? "text-slate-300" : "text-slate-500"}`}>{help}</span>
                </button>
              ))}
            </div>
            {mode === "plats" && (
              <div className="mt-3 space-y-2">
                <div className="flex flex-wrap gap-1">
                  {data.placeKinds.map(k => (
                    <button key={k.key} onClick={() => set("near", f.near === k.key ? "" : k.key)} title={k.help}
                      className={`${seg(f.near === k.key)} flex items-center gap-1.5`}>
                      <span className="w-2 h-2 rounded-full inline-block ring-1 ring-white" style={{ background: PLACE_STYLE[k.key]?.color }} />{k.label}
                    </button>
                  ))}
                </div>
                {nearKind && (
                  <>
                    <div className="flex flex-wrap items-center gap-1">
                      <span className="text-[11px] font-bold text-slate-500 mr-1">Inom</span>
                      {NEAR_KM.map(km => <button key={km} onClick={() => set("km", km === 2 ? "" : String(km))} className={seg(nearKm === km)}>{kmText(km)}</button>)}
                    </div>
                    <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                      <input type="checkbox" checked={f.nearonly === "1"} onChange={e => set("nearonly", e.target.checked ? "1" : "")} />
                      Visa bara stenarna nära på kartan
                    </label>
                  </>
                )}
              </div>
            )}
          </div>

          <details className={box}>
            <summary className="cursor-pointer text-xs font-bold text-slate-700">Fler inställningar</summary>
            <div className="mt-3 space-y-3">
              <div>
                <p className="text-[11px] font-bold text-slate-500 mb-1">Områdets storlek</p>
                <div className="flex gap-1">
                  {HEX_SIZES.map(km => <button key={km} onClick={() => set("hex", km === 20 ? "" : String(km))} className={seg(hexKm === km)}>{km} km</button>)}
                </div>
              </div>
              <div>
                <p className="text-[11px] font-bold text-slate-500 mb-1">Fler platser på kartan</p>
                <div className="flex flex-wrap gap-1">
                  {data.placeKinds.map(k => {
                    const on = extraKinds.includes(k.key);
                    return (
                      <button key={k.key} title={k.help} aria-pressed={on} className={`${seg(on)} flex items-center gap-1.5`}
                        onClick={() => set("places", (on ? extraKinds.filter(x => x !== k.key) : [...extraKinds, k.key]).join(","))}>
                        <span className="w-2 h-2 rounded-full inline-block ring-1 ring-white" style={{ background: PLACE_STYLE[k.key]?.color }} />{k.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </details>
        </aside>

        <div className="space-y-2 lg:sticky lg:top-4">
          <div className="rounded-2xl border border-slate-200 bg-white/90 px-4 py-3">
            <p className={step}>3. Vad kartan visar{patternDef ? ` – ${patternDef.label}` : ""}</p>
            {result()}
          </div>
          <div className="liquid-glass-island rounded-[24px] p-1.5 h-[64dvh] min-h-[460px] relative">
            {patternDef && (
              <PatternMaps stones={mapStones} boundsFrom={data.stones} patternKey={patternKey} label={patternDef.label}
                widthKm={hexKm} minStones={MIN_STONES} split={mode === "tid"} overlays={overlays} circles={circles} markers={markers}
                focus={mode === "kluster" && hp?.clusters[pickedCluster]
                  ? { lat: hp.clusters[pickedCluster].lat, lon: hp.clusters[pickedCluster].lon, radiusKm: hp.clusters[pickedCluster].radius_km }
                  : undefined} />
            )}
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-2 text-[11px] text-slate-600">
            <span className="font-bold">Andel med mönstret</span>
            {SHARE_CLASSES.map(c => (
              <span key={c.label} className="flex items-center gap-1"><span className="w-3.5 h-2.5 inline-block rounded-sm" style={{ background: c.color }} />{c.label}</span>
            ))}
            <span className="flex items-center gap-1"><span className="w-3.5 h-2.5 inline-block rounded-sm border border-dashed border-slate-400" style={{ background: TOO_FEW }} />Färre än {MIN_STONES} stenar</span>
            {overlays.map(l => (
              <span key={l.kind} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full inline-block" style={{ background: PLACE_STYLE[l.kind]?.color }} />{l.label}
              </span>
            ))}
            {mode === "kluster" && hp && (
              <>
                <span className="flex items-center gap-1"><span className="w-3 h-3 inline-block rounded-full border-2" style={{ borderColor: HOT }} />Kluster</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 inline-block rounded-full" style={{ background: HOT }} />Hett område</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 inline-block rounded-full" style={{ background: COLD }} />Kallt område</span>
              </>
            )}
          </div>
        </div>
      </div>

      <details className={box}>
        <summary className="cursor-pointer text-sm font-bold text-slate-800">
          Alla samband i landskapet (R){scan?.available ? `: ${scan.n_replicated} håller i båda halvorna av ${scan.n_tests} prövade` : ""}
        </summary>
        <div className="mt-3">
          <LandscapeScan scan={scan} current={nearKind ? { feature: patternKey, kind: nearKind } : undefined}
            onPick={(feature, kind, km) => patch({ pattern: feature, mode: "plats", near: kind, km: km === 2 ? "" : String(km), split: "" })} />
        </div>
      </details>
      <details className={box}>
        <summary className="cursor-pointer text-sm font-bold text-slate-800">Andel per landskap (samma siffror som tabell)</summary>
        <div className="overflow-x-auto mt-2">
          <table className="text-sm min-w-[360px]">
            <thead><tr className="text-left text-[11px] uppercase tracking-wider text-slate-500"><th className="p-2">Landskap</th><th className="p-2">Stenar</th><th className="p-2">Med mönstret</th><th className="p-2">Andel</th></tr></thead>
            <tbody>
              {provinces.filter(r => r.n >= MIN_STONES).map(r => (
                <tr key={r.p} className="border-t border-slate-900/5"><td className="p-2">{provinceName(r.p)}</td><td className="p-2">{r.n}</td><td className="p-2">{r.k}</td><td className="p-2 font-semibold">{pct(r.share)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );

  // The answer for exactly what the map shows, in words
  function result() {
    if (!patternDef || !periods) return null;
    const top = provinces.filter(r => r.n >= 20).sort((a, b) => b.share - a.share).slice(0, 3);
    if (mode === "tid") {
      return (
        <div className="text-sm text-slate-700 space-y-1.5">
          <p>{`Bland stenar med säker stilgrupp har ${pct(periods.early.k / Math.max(1, periods.early.n))} av ${periods.early.n} stenar före omkring 1050 mönstret, och ${pct(periods.late.k / Math.max(1, periods.late.n))} av ${periods.late.n} efter.`}</p>
          <p className="text-xs text-slate-500">
            Kartorna jämför trakterna sida vid sida. Förändringen med plats och ristare konstanta, och om den håller i båda
            halvorna av korpusen, finns under <Link href="/statistik" className="underline">Statistik → Förändring</Link>.
          </p>
        </div>
      );
    }
    if (mode === "plats") {
      if (!nearKind || !nearDef) return <p className="text-sm text-slate-600">Välj en sorts plats ovan för att jämföra stenarna nära med övriga.</p>;
      if (test === undefined) return <p className="text-sm text-slate-500">Räknar …</p>;
      if (test === null) return <p className="text-sm text-slate-500">För få stenar nära den valda sortens platser för en jämförelse.</p>;
      return (
        <div className="text-sm text-slate-700 space-y-1.5">
          <p>{`${pct(test.share_near)} av de ${test.n_near} stenarna inom ${kmText(test.km)} har mönstret, mot ${pct(test.share_far)} av ${test.n_far} övriga stenar.`}</p>
          <p>{`Oddskvot ${n2(test.or_mh)} med landskapet konstant (p ${pText(test.p_mh)}).`}</p>
          <p className="text-xs text-slate-500">
            Ett utforskande prov: flyttade stenar räknas inte, men tiden hålls inte konstant och den som prövar många
            kombinationer hittar några skillnader av en slump. Pröva hellre under ”Alla samband i landskapet” nedan, där alla
            kombinationer är justerade tillsammans och prövade i båda halvorna.
          </p>
        </div>
      );
    }
    if (mode === "kluster") {
      if (!hot) return <p className="text-sm text-slate-500">Hämtar …</p>;
      if (!hot.available || !hp) return <p className="text-sm text-slate-500">{hot.reason ?? "Hot spots saknas för mönstret."}</p>;
      const clusters = hp.moran.q_bh < 0.05;
      return (
        <div className="text-sm text-slate-700 space-y-2">
          <p>{clusters
            ? `Mönstret klustrar geografiskt mer än slumpen ger (Morans I ${n2(hp.moran.i)}, q ${pText(hp.moran.q_bh)}).`
            : `Mönstret klustrar inte tydligt geografiskt (Morans I ${n2(hp.moran.i)}, q ${pText(hp.moran.q_bh)}).`}</p>
          <p>{`${hp.n_hot} stenar ligger i heta områden och ${hp.n_cold} i kalla (Getis-Ord Gi*, justerat).`}</p>
          {hp.clusters.length === 0 ? <p className="text-slate-600">Kulldorffs scanstatistik hittar inget kluster som klarar provet.</p> : (
            <ul className="space-y-1.5">
              {hp.clusters.map((c, i) => (
                <li key={i}>
                  <button type="button" onClick={() => setPickedCluster(i)}
                    className={`w-full text-left rounded-xl border px-2.5 py-1.5 ${i === pickedCluster ? "border-slate-900 bg-white" : "border-slate-200 bg-white/60 hover:border-slate-400"}`}>
                    <span className="block text-xs font-bold text-slate-900">{`Kluster: ${c.center}`}</span>
                    <span className="block text-xs text-slate-600">{`${kmText(c.radius_km)} runt mitten, ${c.n} stenar`}</span>
                    <span className="block text-xs text-slate-600">{`${pct(c.rate_in)} inne mot ${pct(c.rate_out)} utanför (${n2(c.rr)} gånger så vanligt), p ${pText(c.p)}`}</span>
                    <span className="block text-[10px] font-semibold text-slate-500">
                      {c.halves?.replicated ? "✓ håller i båda halvorna" : "håller inte i båda halvorna"}
                      {(c.q_bh ?? 1) < 0.05 ? " · klarar justeringen över alla mönster" : " · klarar inte justeringen över alla mönster"}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-slate-500">
            Klustren söks bland alla cirklar som rymmer högst en tiondel av stenarna (Kulldorff, 999 simuleringar); flyttade stenar
            räknas inte. Ett kluster är en plats att titta närmare på – en ristare, en verkstad eller en bygd – inte en förklaring.
          </p>
        </div>
      );
    }
    return (
      <div className="text-sm text-slate-700 space-y-1.5">
        <p>{`${pct(periods.all.k / Math.max(1, periods.all.n))} av ${periods.all.n} stenar där det kan avgöras har mönstret.`}</p>
        {top.length > 0 && <p>{`Vanligast i ${top.map(r => `${provinceName(r.p)} (${pct(r.share)})`).join(", ")}.`}</p>}
        <p className="text-xs text-slate-500">
          Färgen visar andelen i varje område, inte antalet stenar, så att Upplands täthet inte döljer mönstret. Välj
          ”Jämför med” för att pröva tid, platser eller kluster.
        </p>
      </div>
    );
  }
}
