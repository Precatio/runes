"use client";

// Stenar som kan ha samma hand (/ristare, under ristarna): grupperna ur den inlärda parmodellen (src/hand_groups.py,
// METHODS 14l), byggda av korpusjobbet och lästa från GET /api/r/handgrupper. Förslag, inte nya ristare.
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

interface Group {
  id: string; stones: string[]; type: "okänd hand" | "med" | "blandad"; carver: string | null;
  carvers: Record<string, string>; signed: string[]; evidence: "gott" | "svagt"; stability: number | null;
  text_share: number; mean_p: number; diameter_km: number; provinces: Record<string, number>; parishes: string[];
  styles: Record<string, number>; runor: Record<string, string>;
}
interface Data {
  version: string; tau: number; groups: Group[];
  tested: { facit_groups: number; together: number; control: number; unnamed_groups: number; unnamed_together: number;
    unnamed_control: number; precision_named: number };
  counts: { groups: number; stones: number; unknown_good: number };
}

const pct = (v: number) => `${Math.round(100 * v)} %`;
const TYPES = [
  { key: "okänd hand", label: "Okänd hand" },
  { key: "med", label: "Med en känd ristare" },
  { key: "blandad", label: "Blandad" },
  { key: "", label: "Alla" },
] as const;

export default function HandGroups({ src }: { src: string }) {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [type, setType] = useState<string>("okänd hand");
  const [province, setProvince] = useState("");
  const [hideWeak, setHideWeak] = useState(true);
  const [stableOnly, setStableOnly] = useState(false);

  useEffect(() => {
    fetch(src)
      .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then(setData)
      .catch(e => setError(`Grupperna kunde inte läsas (${e.message}). De byggs av korpusanalyserna under Statistik.`));
  }, [src]);

  const provinces = useMemo(() => [...new Set((data?.groups ?? []).flatMap(g => Object.keys(g.provinces)))].sort(), [data]);
  const shown = useMemo(() => (data?.groups ?? []).filter(g =>
    (!type || g.type === type) && (!province || g.provinces[province]) && (!hideWeak || g.evidence === "gott")
    && (!stableOnly || (g.stability ?? 0) >= 0.8)), [data, type, province, hideWeak, stableOnly]);

  const panel = "liquid-glass-island rounded-[32px] p-6 md:p-7 min-w-0";
  return (
    <div className="max-w-6xl mx-auto px-4 md:px-6 pb-24">
      <section className={panel} style={{ borderColor: "rgba(183,65,14,0.25)" }} id="samma-hand">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Förslag</div>
        <h2 className="mt-2 text-2xl md:text-3xl font-serif font-bold tracking-tight text-slate-900">Stenar som kan ha samma hand</h2>
        {error && <p className="mt-3 text-slate-600">{error}</p>}
        {!data && !error && <p className="mt-3 text-slate-500">Läser in …</p>}
        {data && (
          <>
            <p className="mt-3 text-slate-700 leading-relaxed max-w-[80ch]">
              Grupper av runstenar som en modell tror är gjorda av samma ristare – också där ingen namngiven ristare passar. Modellen
              väger samman stavning och skiljetecken, språkdrag, stilgrupp, korsets form, ord om ornamentik och runformer i Sveriges
              runinskrifter och avståndet. Den prövades mot runologernas egna uttalanden om ”samme ristare”, med hälften av dem
              undanhållna tills metoden var bestämd: {pct(data.tested.together)} av deras stenpar hamnade i samma grupp, mot{" "}
              {pct(data.tested.control)} av grannstenar på samma avstånd. För händer utan namn var det {pct(data.tested.unnamed_together)}{" "}
              mot {pct(data.tested.unnamed_control)}.
            </p>
            <p className="mt-2 text-sm text-slate-600 max-w-[80ch]">
              Omkring {pct(data.tested.precision_named)} av stenparen i samma grupp har samma ristare, mätt på stenar med känd
              ristare. <b>Stabil</b> anger hur stor del av gruppens par som stannar ihop när modellen tränas om. <b>Svagt underlag</b>{" "}
              betyder att gruppen mest hålls ihop av platsen, ofta fragment från samma fyndplats. Grupperna är hypoteser att pröva
              med ornamentik, runformer och huggteknik – inte nya ristare.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
              {TYPES.map(t => (
                <button key={t.key} type="button" onClick={() => setType(t.key)}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold ${type === t.key ? "bg-[#b7410e] text-white border-[#b7410e]" : "bg-white border-slate-300 hover:border-slate-900"}`}>
                  {t.label}
                </button>
              ))}
              <select value={province} onChange={e => setProvince(e.target.value)} className="liquid-glass-input-wrapper px-2 py-1.5 rounded-xl text-xs" aria-label="Landskap">
                <option value="">Alla landskap</option>
                {provinces.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <label className="flex items-center gap-1.5 text-xs text-slate-700">
                <input type="checkbox" checked={hideWeak} onChange={e => setHideWeak(e.target.checked)} /> Dölj svagt underlag
              </label>
              <label className="flex items-center gap-1.5 text-xs text-slate-700">
                <input type="checkbox" checked={stableOnly} onChange={e => setStableOnly(e.target.checked)} /> Bara stabila (minst 80 %)
              </label>
              <span className="text-xs text-slate-500 tabular-nums">{shown.length} grupper, {shown.reduce((n, g) => n + g.stones.length, 0)} stenar</span>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {shown.map(g => <GroupCard key={g.id} g={g} />)}
            </div>
            <p className="mt-4 text-xs text-slate-500">
              Metod: Vitki (src/hand_groups.py, METHODS 14l), efter Rundata, Runor 2020 (RAÄ) och Sveriges runinskrifter.
              Gränsen för en grupp är en sannolikhet för samma hand på minst {data.tau.toLocaleString("sv-SE")}, och gruppens stenar
              ligger högst 30 km från varandra.
            </p>
          </>
        )}
      </section>
    </div>
  );
}

function GroupCard({ g }: { g: Group }) {
  const kind = g.type === "okänd hand" ? "Okänd hand" : g.type === "med" ? `Med ${g.carver}` : "Blandad";
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/70 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-bold text-slate-900 tabular-nums">{g.id}</span>
        <span className="px-2 py-0.5 rounded-lg text-xs font-bold bg-[#b7410e]/10 text-[#8a300a]">{kind}</span>
        {g.evidence === "svagt" && <span className="px-2 py-0.5 rounded-lg text-xs bg-slate-100 text-slate-600">svagt underlag</span>}
        {g.stability != null && <span className="px-2 py-0.5 rounded-lg text-xs bg-slate-100 text-slate-700">stabil {pct(g.stability)}</span>}
        <span className="text-xs text-slate-500">{g.stones.length} stenar · inom {g.diameter_km.toLocaleString("sv-SE")} km</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {g.stones.map(s => (
          <Link key={s} href={`/oversikt?signum=${encodeURIComponent(s)}`} translate="no"
            className={`px-2 py-0.5 rounded-lg border text-xs hover:border-slate-900 ${g.carvers[s] ? "border-[#b7410e]/40 bg-[#b7410e]/5" : "border-slate-300 bg-white"}`}
            title={g.carvers[s] ? `${s}: ${g.carvers[s]}${g.signed.includes(s) ? " (signerad)" : ""}` : `${s}: ingen ristare i Rundata`}>
            {s}{g.carvers[s] ? ` · ${g.carvers[s]}` : ""}
          </Link>
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-600">
        {g.parishes.slice(0, 6).join(", ")}{g.parishes.length > 6 ? " …" : ""}
        {Object.keys(g.styles).length > 0 && <> · stil {Object.entries(g.styles).map(([k, n]) => `${k} ${n}`).join(", ")}</>}
      </p>
      {Object.keys(g.runor).length > 0 && (
        <p className="mt-1 text-xs text-slate-500">Runor 2020: {Object.entries(g.runor).slice(0, 3).map(([s, t]) => `${s} – ${t}`).join("; ")}</p>
      )}
    </div>
  );
}
