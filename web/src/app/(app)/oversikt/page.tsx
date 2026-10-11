"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import PlotlyGraph from "@/components/PlotlyGraph";
import { API_URL } from "@/lib/api";
import { DocsNote } from "@/components/KnownLimitations";

type Status = "kan vara felbedömd" | "omstridd" | "stöds" | "svagt underlag" | "signerad" | "nytt förslag" | "möjligt förslag" | "inget förslag";

interface StoneRow {
  signum: string; province: string; place: string; carver: string | null; carvers?: string[]; carver_kind: "S" | "A" | "?" | null;
  status: Status; support: number | null; alternative: { carver: string; strength: number } | null; n_sources: number;
}
interface OverviewData {
  stones: StoneRow[]; counts: Record<Status, number>; status_order: Status[]; r_available: boolean;
  control: { n_signed: number; flagged: number; would_be_misjudged: number };
}
interface Source { value: number; points_to: string | null; text: string }
interface Profile extends StoneRow {
  sources: Record<string, Source>;
  alternatives: { carver: string; strength: number; model: number; orthography: number; checks: Record<string, boolean | null>; check_texts?: Record<string, string> }[];
  model: { kind: string; probabilities: Record<string, number> } | null;
  orthography: { ranking: { carver: string; similarity: number; reliability: number }[]; n_words: number } | null;
  variables: {
    height_m?: number; height_pct?: number | null; rune_height_cm?: number; fragment: boolean; kmr_url?: string;
    n_words: number; n_words_pct: number | null; n_names: number; n_names_pct: number | null;
    categories: string[]; status_words: string[]; style: string | null; style_uncertain: boolean; dating: string;
    material: string; lost: boolean; province: string; n_province: number;
    seriation?: { year: number; lo: number; hi: number }; cluster?: number;
  };
  crosscheck: { status: string; text?: string; url?: string } | null;
}

// Status colours (good / warning / critical) always come with a symbol and a label
const STATUS: Record<Status, { color: string; symbol: string; icon: string; text: string }> = {
  "stöds": { color: "#0ca30c", symbol: "circle", icon: "●", text: "Beläggen stämmer med Rundatas ristare." },
  "omstridd": { color: "#fab219", symbol: "diamond", icon: "◆", text: "Beläggen stöder Rundatas ristare men pekar också tydligt mot en annan." },
  "kan vara felbedömd": { color: "#d03b3b", symbol: "x", icon: "✕", text: "Beläggen talar emot Rundatas ristare och pekar mot en annan." },
  "svagt underlag": { color: "#8f8e8a", symbol: "circle-open", icon: "○", text: "För få metoder kan uttala sig, eller beläggen är svaga." },
  "signerad": { color: "#334155", symbol: "square-open", icon: "□", text: "Signerad sten – kontroll: här är ristaren känd." },
  "nytt förslag": { color: "#1c5cab", symbol: "circle", icon: "●", text: "Stenen saknar ristare i Rundata; beläggen pekar starkt mot en." },
  "möjligt förslag": { color: "#86b6ef", symbol: "circle", icon: "●", text: "Stenen saknar ristare i Rundata; beläggen pekar svagt mot en." },
  "inget förslag": { color: "#c9c8c3", symbol: "circle", icon: "·", text: "Stenen saknar ristare och inget förslag är starkt nog." },
};
const ATTRIBUTED: Status[] = ["kan vara felbedömd", "omstridd", "stöds", "svagt underlag", "signerad"];
const UNATTRIBUTED: Status[] = ["nytt förslag", "möjligt förslag", "inget förslag"];
const SOURCE_LABELS: Record<string, string> = {
  modell: "Statistisk modell (R)", ortografi: "Ortografi", "område": "Område", stil: "Stilgrupp", "språkdrag": "Språkdrag", bergart: "Bergart",
};
const CHECK_ABBR: Record<string, string> = { "område": "Om", stil: "St", "språkdrag": "Sp", bergart: "Be" };
const AXIS = { gridcolor: "rgba(15,23,42,0.06)", zerolinecolor: "rgba(15,23,42,0.15)", tickfont: { color: "#52514e", size: 11 } };
const d2 = (v: number | null | undefined) => (v == null ? "–" : v.toFixed(2).replace(".", ","));
// Small deterministic jitter so that stones with the same values do not hide each other
const jitter = (s: string, amp: number) => { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return ((h % 1000) / 1000) * amp; };

export default function OverviewPage() {
  return <Suspense fallback={null}><Overview /></Suspense>;
}

// Kept for the rest of the visit, so that returning to the page is instant (the server also caches it on disk)
let overviewMemo: OverviewData | null = null;
const profileMemo = new Map<string, Profile>();

function Overview() {
  const params = useSearchParams();
  const [data, setData] = useState<OverviewData | null>(overviewMemo);
  const [error, setError] = useState<string | null>(null);
  const [province, setProvince] = useState("");
  const [carver, setCarver] = useState("");
  const [query, setQuery] = useState("");
  const [hidden, setHidden] = useState<Set<Status>>(new Set(["inget förslag"]));
  const [selected, setSelected] = useState<string | null>(params.get("signum"));
  const [showTable, setShowTable] = useState(false);

  useEffect(() => {
    if (overviewMemo) return;
    fetch(`${API_URL}/api/research/overview`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then((d: OverviewData) => { overviewMemo = d; setData(d); })
      .catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta översikten."));
  }, []);

  const provinces = useMemo(() => [...new Set((data?.stones ?? []).map(s => s.province))].sort(), [data]);
  const carvers = useMemo(() => [...new Set((data?.stones ?? []).flatMap(s => [s.carver, s.alternative?.carver]).filter(Boolean) as string[])].sort(), [data]);
  const rows = useMemo(() => (data?.stones ?? []).filter(s =>
    !hidden.has(s.status) && (!province || s.province === province)
    && (!carver || s.carver === carver || s.alternative?.carver === carver)
    && (!query || s.signum.toLowerCase().includes(query.toLowerCase()) || s.place.toLowerCase().includes(query.toLowerCase()))), [data, hidden, province, carver, query]);

  const toggle = (st: Status) => setHidden(h => { const n = new Set(h); if (n.has(st)) n.delete(st); else n.add(st); return n; });
  const pick = (e: { points?: { customdata?: string }[] }) => { const s = e.points?.[0]?.customdata; if (s) setSelected(s); };

  if (error) return <div className="max-w-3xl mx-auto p-8 text-red-700 font-semibold">{error}</div>;
  if (!data) return <div className="max-w-3xl mx-auto p-8 text-slate-500">Samlar beläggen för alla runstenar (första gången tar det en halv minut) …</div>;

  const attributedTraces = ATTRIBUTED.map(st => {
    const pts = rows.filter(s => s.status === st && s.support != null);
    return {
      type: "scatter", mode: "markers", name: st,
      x: pts.map(s => Math.min(1, (s.support ?? 0) + jitter(s.signum, 0.02) - 0.01)),
      y: pts.map(s => (s.alternative?.strength ?? 0) + jitter(s.signum + "y", 0.02)),
      customdata: pts.map(s => s.signum),
      text: pts.map(s => `<b>${s.signum}</b> ${s.place}<br>Rundata: ${s.carver ?? "–"}${s.carver_kind === "?" ? " (osäker)" : ""}<br>Stöd ${d2(s.support)} · ${s.n_sources} metoder<br>Alternativ: ${s.alternative ? `${s.alternative.carver} (${d2(s.alternative.strength)})` : "–"}`),
      hovertemplate: "%{text}<extra></extra>",
      marker: { color: STATUS[st].color, symbol: STATUS[st].symbol, size: selected ? 8 : 9, opacity: 0.85,
                line: { color: st === "signerad" || st === "svagt underlag" ? STATUS[st].color : "#ffffff", width: st.includes("open") ? 1.5 : 1 } },
    };
  });
  const sel = rows.find(s => s.signum === selected);
  if (sel && sel.support != null && ATTRIBUTED.includes(sel.status)) {
    attributedTraces.push({ type: "scatter", mode: "markers", name: "vald sten", x: [sel.support], y: [sel.alternative?.strength ?? 0],
      customdata: [sel.signum], text: [sel.signum], hovertemplate: "%{text}<extra></extra>", showlegend: false,
      marker: { color: "rgba(0,0,0,0)", symbol: "circle-open", size: 26, opacity: 1, line: { color: "#b7410e", width: 3 } } } as never);
  }
  const quadrant = (x: number, y: number, text: string) => ({ x, y, text, showarrow: false, font: { size: 11, color: "#8f8e8a" }, xref: "x", yref: "y" });
  const lines = [
    { type: "line", x0: 0, x1: 1.02, y0: 0.4, y1: 0.4, line: { color: "rgba(15,23,42,0.25)", width: 1, dash: "dot" } },
    { type: "line", x0: 0.4, x1: 0.4, y0: 0.4, y1: 1.02, line: { color: "rgba(15,23,42,0.25)", width: 1, dash: "dot" } },
    { type: "line", x0: 0.6, x1: 0.6, y0: -0.02, y1: 0.4, line: { color: "rgba(15,23,42,0.25)", width: 1, dash: "dot" } },
  ];

  const unattributed = rows.filter(s => UNATTRIBUTED.includes(s.status) && (s.alternative?.strength ?? 0) > 0);
  const provOrder = [...new Set(unattributed.map(s => s.province))].sort((a, b) =>
    unattributed.filter(s => s.province === b).length - unattributed.filter(s => s.province === a).length);
  const unTraces = UNATTRIBUTED.map(st => {
    const pts = unattributed.filter(s => s.status === st);
    return {
      type: "scatter", mode: "markers", name: st,
      x: pts.map(s => s.alternative?.strength ?? 0),
      y: pts.map(s => provOrder.indexOf(s.province) + jitter(s.signum, 0.6) - 0.3),
      customdata: pts.map(s => s.signum),
      text: pts.map(s => `<b>${s.signum}</b> ${s.place}<br>Förslag: ${s.alternative ? `${s.alternative.carver} (${d2(s.alternative.strength)})` : "–"}`),
      hovertemplate: "%{text}<extra></extra>",
      marker: { color: STATUS[st].color, size: 8, opacity: 0.85, line: { color: "#ffffff", width: 1 } },
    };
  });

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-5">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Stenöversikt</h2>
        <p className="text-slate-600 text-[15px] leading-relaxed max-w-4xl">
          Varje punkt är en runsten. Sex metoder – statistisk modell, ortografi, område, stilgrupp, språkdrag och bergart – säger
          var för sig något om vem som ristade den. Här vägs de samman mot Rundatas ristare: hur väl beläggen <em>stöder</em> den, och hur
          starkt det bästa <em>alternativet</em> är. Klicka på en sten för att se vad varje metod säger. Måtten är index för att sortera
          och prioritera, inte sannolikheter.
        </p>
        <div className="mt-2"><DocsNote anchor="13c-översikt-per-sten">Hur måtten och statusen räknas, och hur ofta de larmar i onödan, står i avsnitt 13c.</DocsNote></div>
      </div>

      <div className="flex flex-wrap gap-2">
        {data.status_order.map(st => (
          <button key={st} onClick={() => toggle(st)} title={STATUS[st].text}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-1.5 ${hidden.has(st) ? "bg-white text-slate-400 border-slate-200 line-through" : "bg-white text-slate-800 border-slate-300"}`}>
            <span style={{ color: STATUS[st].color }}>{STATUS[st].icon}</span>{st} <span className="text-slate-500 font-semibold">{data.counts[st]}</span>
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-3 items-end">
        <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Landskap
          <select value={province} onChange={e => setProvince(e.target.value)} className="block mt-1 liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none">
            <option value="">Alla</option>{provinces.map(p => <option key={p}>{p}</option>)}
          </select>
        </label>
        <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Ristare (Rundata eller alternativ)
          <select value={carver} onChange={e => setCarver(e.target.value)} className="block mt-1 liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none">
            <option value="">Alla</option>{carvers.map(c => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Sök sten
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="t.ex. Sö 179 eller Gripsholm"
            className="block mt-1 liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none" />
        </label>
        <span className="text-xs text-slate-500 pb-2">{rows.length} stenar visas</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-5 items-start">
        <div className="space-y-5 min-w-0">
          <section className="liquid-glass-island rounded-[24px] p-4">
            <h3 className="font-bold text-slate-900">Stenar med ristare i Rundata</h3>
            <p className="text-xs text-slate-500 mb-1">Längre åt höger: beläggen stöder Rundatas ristare. Högre upp: en annan ristare får starkt stöd.</p>
            <div className="h-[460px]">
              <PlotlyGraph data={attributedTraces} onClick={pick} layout={{
                autosize: true, margin: { l: 56, r: 16, t: 10, b: 50 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
                hovermode: "closest", font: { family: "inherit", color: "#0b0b0b" },
                xaxis: { ...AXIS, title: { text: "Stöd för Rundatas ristare", font: { size: 12, color: "#52514e" } }, range: [-0.03, 1.04] },
                yaxis: { ...AXIS, title: { text: "Starkaste alternativ", font: { size: 12, color: "#52514e" } }, range: [-0.03, 1.04] },
                legend: { orientation: "h", y: -0.18, font: { size: 11, color: "#52514e" } }, shapes: lines,
                annotations: [quadrant(0.18, 0.98, "kan vara felbedömd"), quadrant(0.75, 0.98, "omstridd"),
                              quadrant(0.85, 0.05, "stöds"), quadrant(0.3, 0.05, "svagt underlag")],
              }} />
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Kontroll: av {data.control.n_signed} signerade stenar (där ristaren är känd) hade {data.control.flagged} fått ett starkt
              alternativ ({Math.round((100 * data.control.flagged) / Math.max(1, data.control.n_signed))} %) och {data.control.would_be_misjudged} hamnat
              som &quot;kan vara felbedömd&quot;. &quot;Omstridd&quot; larmar alltså ofta i onödan; &quot;kan vara felbedömd&quot; sällan.
            </p>
          </section>

          <section className="liquid-glass-island rounded-[24px] p-4">
            <h3 className="font-bold text-slate-900">Stenar utan ristare i Rundata</h3>
            <p className="text-xs text-slate-500 mb-1">Längre åt höger: beläggen pekar starkare mot en ristare. Stenar utan något förslag visas inte här ({data.counts["inget förslag"]}).</p>
            <div style={{ height: Math.max(220, 34 * provOrder.length + 90) }}>
              <PlotlyGraph data={unTraces} onClick={pick} layout={{
                autosize: true, margin: { l: 56, r: 16, t: 10, b: 50 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
                hovermode: "closest", font: { family: "inherit", color: "#0b0b0b" },
                xaxis: { ...AXIS, title: { text: "Styrka för det bästa förslaget", font: { size: 12, color: "#52514e" } }, range: [0, 1.02] },
                yaxis: { ...AXIS, tickvals: provOrder.map((_, i) => i), ticktext: provOrder, autorange: "reversed", zeroline: false },
                legend: { orientation: "h", y: -0.25, font: { size: 11, color: "#52514e" } },
                shapes: [0.3, 0.5].map(x => ({ type: "line", x0: x, x1: x, y0: -0.6, y1: provOrder.length - 0.4, line: { color: "rgba(15,23,42,0.25)", width: 1, dash: "dot" } })),
              }} />
            </div>
          </section>

          <div>
            <button onClick={() => setShowTable(v => !v)} className="text-sm font-semibold text-[#b7410e] hover:underline">
              {showTable ? "Dölj tabellen" : `Visa som tabell (${rows.length} stenar)`}
            </button>
            {showTable && <StoneTable rows={rows} onPick={setSelected} />}
          </div>
        </div>

        <div className="xl:sticky xl:top-4">
          {selected ? <StoneProfile key={selected} signum={selected} onClose={() => setSelected(null)} /> : (
            <div className="liquid-glass-island rounded-[24px] p-5 text-sm text-slate-600">
              Klicka på en sten i diagrammen eller tabellen för att se vad varje metod säger om den, vilka andra ristare som är tänkbara
              och hur stenen förhåller sig till andra i landskapet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StoneTable({ rows, onPick }: { rows: StoneRow[]; onPick: (s: string) => void }) {
  const sorted = [...rows].sort((a, b) => (b.alternative?.strength ?? 0) - (a.alternative?.strength ?? 0));
  return (
    <div className="overflow-x-auto mt-2 liquid-glass-island rounded-[24px] p-3">
      <table className="w-full text-sm">
        <thead><tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
          <th className="p-2">Sten</th><th className="p-2">Status</th><th className="p-2">Rundata</th><th className="p-2">Stöd</th>
          <th className="p-2">Starkaste alternativ</th><th className="p-2">Metoder</th></tr></thead>
        <tbody>{sorted.slice(0, 400).map(s => (
          <tr key={s.signum} onClick={() => onPick(s.signum)} className="border-t border-slate-900/5 cursor-pointer hover:bg-slate-50">
            <td className="p-2 font-semibold">{s.signum} <span className="text-slate-500 font-normal">{s.place}</span></td>
            <td className="p-2"><span style={{ color: STATUS[s.status].color }}>{STATUS[s.status].icon}</span> {s.status}</td>
            <td className="p-2">{s.carver ?? "–"}{s.carver_kind === "?" ? " (osäker)" : s.carver_kind === "S" ? " (signerad)" : ""}</td>
            <td className="p-2">{d2(s.support)}</td>
            <td className="p-2">{s.alternative ? `${s.alternative.carver} (${d2(s.alternative.strength)})` : "–"}</td>
            <td className="p-2">{s.n_sources}</td>
          </tr>
        ))}</tbody>
      </table>
      {sorted.length > 400 && <p className="text-xs text-slate-500 mt-2">Visar de 400 med starkast alternativ – filtrera för att se fler.</p>}
    </div>
  );
}

function Bar({ value, color = "#2a78d6" }: { value: number | null | undefined; color?: string }) {
  return (
    <span className="inline-block w-24 h-2 rounded-full bg-slate-200 align-middle overflow-hidden">
      {value != null && <span className="block h-full rounded-full" style={{ width: `${Math.max(2, Math.min(100, value * 100))}%`, background: color }} />}
    </span>
  );
}

function StoneProfile({ signum, onClose }: { signum: string; onClose: () => void }) {
  const [p, setP] = useState<Profile | null>(profileMemo.get(signum) ?? null);
  const [error, setError] = useState<string | null>(null);
  // Keyed by signum in the parent, so a new stone starts with empty state
  useEffect(() => {
    if (profileMemo.has(signum)) return;
    fetch(`${API_URL}/api/research/overview/${encodeURIComponent(signum)}`).then(r => (r.ok ? r.json() : r.json().then(j => Promise.reject(new Error(j.detail)))))
      .then((d: Profile) => { profileMemo.set(signum, d); setP(d); }).catch(e => setError(e instanceof Error ? e.message : "Kunde inte hämta stenen."));
  }, [signum]);
  if (error) return <div className="liquid-glass-island rounded-[24px] p-5 text-sm text-red-700">{error}</div>;
  if (!p) return <div className="liquid-glass-island rounded-[24px] p-5 text-sm text-slate-500">Hämtar {signum} …</div>;
  const v = p.variables;
  const st = STATUS[p.status];
  const verdict = (s: Source | undefined) => (s == null ? { icon: "–", cls: "text-slate-400", label: "kan inte uttala sig" }
    : s.value >= 0.6 ? { icon: "✓", cls: "text-emerald-700", label: "stöder" } : s.value > 0 ? { icon: "≈", cls: "text-amber-700", label: "delvis" }
    : { icon: "✕", cls: "text-red-700", label: "talar emot" });
  const pctLine = (label: string, value: string, pct: number | null | undefined) => (
    <div className="flex items-center justify-between gap-2">
      <span className="text-slate-600">{label}</span>
      <span className="flex items-center gap-2"><span className="font-semibold text-slate-900">{value}</span>
        <Bar value={pct != null ? pct / 100 : null} color="#6da7ec" />
        <span className="text-xs text-slate-500 w-14 text-right">{pct != null ? `${pct}:e pct` : "–"}</span></span>
    </div>
  );
  return (
    <div className="liquid-glass-island rounded-[24px] p-5 space-y-4 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-xl font-bold text-slate-900">{p.signum}</h3>
          <p className="text-slate-600">{p.place}, {v.province}{v.lost ? " · försvunnen" : ""}</p>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-900 text-lg leading-none" aria-label="Stäng">×</button>
      </div>
      <div className="rounded-xl border px-3 py-2" style={{ borderColor: st.color }}>
        <p className="font-bold" style={{ color: "#0f172a" }}><span style={{ color: st.color }}>{st.icon}</span> {p.status}</p>
        <p className="text-xs text-slate-600 mt-0.5">{st.text}</p>
        <p className="text-xs text-slate-700 mt-1">
          Rundata: <strong>{p.carver ?? "ingen ristare"}</strong>{p.carver_kind === "S" ? " (signerad)" : p.carver_kind === "?" ? " (osäker)" : p.carver_kind === "A" ? " (attribuerad)" : ""}
          {(p.carvers?.length ?? 0) > 1 && <> – Rundata anger också {p.carvers!.filter(c => c !== p.carver).join(", ")}</>}.
          {p.support != null && <> Stöd {d2(p.support)} från {p.n_sources} metoder.</>}
          {p.alternative && <> Starkaste {p.carver ? "alternativ" : "förslag"}: <strong>{p.alternative.carver}</strong> ({d2(p.alternative.strength)}).</>}
        </p>
        {p.crosscheck && <p className="text-xs text-slate-600 mt-1">Runor 2020 / Wikidata: {p.crosscheck.status}{p.crosscheck.text ? ` – ${p.crosscheck.text}` : ""}</p>}
      </div>

      {p.carver && (
        <div>
          <p className="font-bold text-slate-900 mb-1">Vad metoderna säger om {p.carver}</p>
          <ul className="space-y-1.5">
            {Object.keys(SOURCE_LABELS).map(k => {
              const s = p.sources[k]; const vd = verdict(s);
              return (
                <li key={k} className="flex gap-2" title={s?.text}>
                  <span className={`w-4 font-bold ${vd.cls}`}>{vd.icon}</span>
                  <span className="w-36 shrink-0 text-slate-700">{SOURCE_LABELS[k]}</span>
                  <span className="text-xs text-slate-600">{s ? s.text : "Kan inte uttala sig."}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {p.alternatives.length > 0 && (
        <div>
          <p className="font-bold text-slate-900 mb-1">{p.carver ? "Andra tänkbara ristare" : "Tänkbara ristare"}</p>
          <table className="w-full text-xs">
            <thead><tr className="text-left text-slate-500"><th className="py-1">Ristare</th><th>Styrka</th><th>Modell</th><th>Ortografi</th><th>Kontroller</th></tr></thead>
            <tbody>{p.alternatives.map(a => (
              <tr key={a.carver} className="border-t border-slate-900/5">
                <td className="py-1 font-semibold">{a.carver}</td>
                <td><Bar value={a.strength} /> {d2(a.strength)}</td><td>{d2(a.model)}</td><td>{d2(a.orthography)}</td>
                <td title={Object.entries(a.check_texts ?? {}).map(([k, t]) => `${k}: ${t}`).join("\n")}>
                  {Object.entries(a.checks).map(([k, ok]) => <span key={k} className={ok == null ? "text-slate-400" : ok ? "text-emerald-700" : "text-red-700"}>{CHECK_ABBR[k] ?? k}{ok == null ? "–" : ok ? "✓" : "✕"} </span>)}
                </td>
              </tr>
            ))}</tbody>
          </table>
          <p className="text-[11px] text-slate-500 mt-1">Kontroller: Om = område, St = stilgrupp, Sp = språkdrag, Be = bergart; ✓ klarar, ✕ klarar inte, – kan inte prövas (håll muspekaren över raden för detaljer).</p>
        </div>
      )}

      <div>
        <p className="font-bold text-slate-900 mb-1">Stenen jämförd med {v.n_province} runstenar i {v.province}</p>
        <div className="space-y-1">
          {pctLine("Höjd", v.height_m ? `${d2(v.height_m)} m${v.fragment ? " (fragment)" : ""}` : "okänd", v.height_pct)}
          {pctLine("Textens längd", `${v.n_words} ord`, v.n_words_pct)}
          {pctLine("Namngivna personer", `${v.n_names}`, v.n_names_pct)}
        </div>
        <div className="flex flex-wrap gap-1.5 mt-2 text-xs">
          {v.categories.map(c => <span key={c} className="px-2 py-0.5 rounded-lg bg-slate-100">{c}</span>)}
          {v.status_words.map(c => <span key={c} className="px-2 py-0.5 rounded-lg bg-slate-100">statusord: {c}</span>)}
          {v.style && <span className="px-2 py-0.5 rounded-lg bg-slate-100">stil {v.style}{v.style_uncertain ? "?" : ""}</span>}
          {v.seriation && <span className="px-2 py-0.5 rounded-lg bg-slate-100">seriation ca {v.seriation.year} ({v.seriation.lo}–{v.seriation.hi})</span>}
          {v.cluster != null && <span className="px-2 py-0.5 rounded-lg bg-slate-100">grupp {v.cluster} (stil, språk, innehåll)</span>}
          {v.material && <span className="px-2 py-0.5 rounded-lg bg-slate-100">{v.material}</span>}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 pt-1">
        <Link href={`/inskrifter?signum=${encodeURIComponent(p.signum)}`} className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:border-slate-900">Inskriften</Link>
        <Link href={`/karta?signum=${encodeURIComponent(p.signum)}`} className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:border-slate-900">Visa på karta</Link>
        {v.kmr_url && <a href={v.kmr_url} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold hover:border-slate-900">Kulturmiljöregistret</a>}
      </div>
    </div>
  );
}
