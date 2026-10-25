"use client";

// Runmodellen: rita runslingornas mittlinjer på djupbilderna (api/routers/runmodell.py). Mittlinjen följer slingan i
// läsriktning, och bandet runt den ska täcka runorna men inte ramarna utanför; modellen läser sedan den uträtade
// slingan mot Rundatas text. En intern forskningssida, inte i menyn.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { API_URL } from "@/lib/api";

type Stone = { series: string; stem: string; file: string; signum: string | null; object: string | null;
  rune_types: string | null; transliteration: string | null; width: number; height: number; res_mm: number;
  bands: number; status: string | null };
type Band = { points: [number, number][]; height: number };

const COLORS = ["#b7410e", "#1d4ed8", "#15803d", "#7e22ce", "#b45309", "#0e7490"];

export default function RunmodellPage() {
  const [stones, setStones] = useState<Stone[]>([]);
  const [filter, setFilter] = useState("");
  const [cur, setCur] = useState<Stone | null>(null);
  const [bands, setBands] = useState<Band[]>([]);
  const [active, setActive] = useState(0);
  const [drag, setDrag] = useState<[number, number] | null>(null);
  const [msg, setMsg] = useState("");
  const svg = useRef<SVGSVGElement>(null);

  const load = useCallback(() => fetch(`${API_URL}/api/runmodell/stones`).then(r => r.json()).then(d => d.stones as Stone[]), []);
  useEffect(() => {
    let alive = true;
    load().then(s => { if (alive) setStones(s); }).catch(() => {});
    return () => { alive = false; };
  }, [load]);

  const open = async (s: Stone) => {
    setCur(s); setMsg("");
    const r = await fetch(`${API_URL}/api/runmodell/band/${s.series}/${s.stem}`);
    const b = await r.json();
    setBands(b.bands?.length ? b.bands : [{ points: [], height: Math.round(70 / s.res_mm) }]);
    setActive(0);
  };

  // Click coordinates in image pixels (the SVG's viewBox is the image)
  const at = (e: React.MouseEvent): [number, number] => {
    const r = svg.current!.getBoundingClientRect();
    const k = cur!.width / r.width;
    return [Math.round((e.clientX - r.left) * k), Math.round((e.clientY - r.top) * k)];
  };
  const addPoint = (e: React.MouseEvent) => {
    if (drag || !cur) return;
    const p = at(e);
    setBands(bs => bs.map((b, i) => (i === active ? { ...b, points: [...b.points, p] } : b)));
  };
  const move = (e: React.MouseEvent) => {
    if (!drag || !cur) return;
    const p = at(e);
    setBands(bs => bs.map((b, i) => (i === drag[0] ? { ...b, points: b.points.map((q, j) => (j === drag[1] ? p : q)) } : b)));
  };
  const undo = () => setBands(bs => bs.map((b, i) => (i === active ? { ...b, points: b.points.slice(0, -1) } : b)));
  const setHeight = (h: number) => setBands(bs => bs.map((b, i) => (i === active ? { ...b, height: h } : b)));
  const newBand = () => { setBands(bs => [...bs, { points: [], height: bands[active]?.height ?? 60 }]); setActive(bands.length); };
  const dropBand = () => { setBands(bs => bs.filter((_, i) => i !== active)); setActive(0); };

  const save = async (status: "utkast" | "granskad") => {
    if (!cur) return;
    const body = { bands: bands.filter(b => b.points.length >= 2), status, by: "Vitki", note: "" };
    const r = await fetch(`${API_URL}/api/runmodell/band/${cur.series}/${cur.stem}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    setMsg(r.ok ? `Sparat (${body.bands.length} slingor, ${status}).` : `Kunde inte spara: ${(await r.json()).detail ?? r.status}`);
    setStones(await load());
  };

  const shown = useMemo(() => stones.filter(s =>
    !filter || `${s.signum ?? ""} ${s.file} ${s.series}`.toLowerCase().includes(filter.toLowerCase())), [stones, filter]);
  const done = stones.filter(s => s.status === "granskad").length;

  return (
    <div className="flex h-full w-full">
      <aside className="w-72 shrink-0 border-r border-slate-200 overflow-y-auto p-3 text-sm">
        <h1 className="text-lg font-bold">Runmodell</h1>
        <p className="text-xs text-slate-500 mb-2">{stones.length} djupbilder · {done} granskade</p>
        <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Sök signum eller fil"
          className="w-full mb-2 rounded-lg border border-slate-300 px-2 py-1" />
        <ul className="space-y-0.5">
          {shown.map(s => (
            <li key={`${s.series}/${s.stem}`}>
              <button type="button" onClick={() => void open(s)}
                className={`w-full text-left rounded px-2 py-1 hover:bg-slate-100 ${cur?.stem === s.stem ? "bg-slate-200" : ""}`}>
                <span className="font-semibold">{s.signum ?? "–"}</span>{" "}
                <span className="text-slate-500 text-xs">{s.file.slice(0, 26)}</span>
                {s.status && <span className={`ml-1 text-[10px] font-bold ${s.status === "granskad" ? "text-emerald-700" : "text-amber-700"}`}>{s.status}</span>}
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="flex-1 overflow-auto p-4">
        {!cur ? (
          <div className="max-w-xl text-slate-600 leading-relaxed">
            <h2 className="text-xl font-bold text-slate-900 mb-2">Rita runslingornas mittlinjer</h2>
            <p>Välj en sten. Klicka längs mitten av runslingan <strong>i läsriktning</strong>, från textens början.
              Det halvgenomskinliga bandet ska täcka runorna men inte ramar och ornamentik utanför; ändra höjden med
              reglaget. En slinga som avbryts får en ny linje (Ny slinga), i textens ordning. Dra en punkt för att
              flytta den.</p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2 mb-2 text-sm">
              <strong className="text-base">{cur.signum ?? cur.file}</strong>
              <span className="text-slate-500">{cur.object ?? ""}{cur.rune_types ? ` · ${cur.rune_types}` : ""}</span>
              <span className="ml-auto">{msg}</span>
            </div>
            <p className="mb-2 text-sm font-mono bg-slate-50 border border-slate-200 rounded p-2 break-words">
              {cur.transliteration ?? "Ingen text i Rundata."}</p>
            <div className="flex flex-wrap items-center gap-2 mb-2 text-sm">
              {bands.map((b, i) => (
                <button key={i} type="button" onClick={() => setActive(i)}
                  className={`px-2 py-1 rounded border ${i === active ? "font-bold" : ""}`} style={{ borderColor: COLORS[i % COLORS.length] }}>
                  Slinga {i + 1} ({b.points.length})
                </button>
              ))}
              <button type="button" onClick={newBand} className="px-2 py-1 rounded border border-slate-300">Ny slinga</button>
              <button type="button" onClick={undo} className="px-2 py-1 rounded border border-slate-300">Ångra punkt</button>
              <button type="button" onClick={dropBand} className="px-2 py-1 rounded border border-slate-300">Ta bort slingan</button>
              <label className="flex items-center gap-1">Höjd {Math.round((bands[active]?.height ?? 0) * cur.res_mm)} mm
                <input type="range" min={10} max={250} value={bands[active]?.height ?? 60} onChange={e => setHeight(+e.target.value)} />
              </label>
              <button type="button" onClick={() => void save("utkast")} className="px-3 py-1 rounded bg-slate-700 text-white">Spara utkast</button>
              <button type="button" onClick={() => void save("granskad")} className="px-3 py-1 rounded bg-emerald-700 text-white">Spara som granskad</button>
            </div>
            <div className="relative inline-block max-w-full">
              {/* eslint-disable-next-line @next/next/no-img-element -- a local depth image, not optimised */}
              <img src={`${API_URL}/api/runmodell/depth/${cur.series}/${cur.stem}.png`} alt={`Djupbild av ${cur.signum ?? cur.file}`}
                className="block max-w-full h-auto select-none" draggable={false} />
              <svg ref={svg} viewBox={`0 0 ${cur.width} ${cur.height}`} className="absolute inset-0 w-full h-full cursor-crosshair"
                onClick={addPoint} onMouseMove={move} onMouseUp={() => setTimeout(() => setDrag(null), 0)}>
                <defs>
                  {COLORS.map((c, i) => (
                    <marker key={i} id={`pil${i}`} viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                      <path d="M0,0 L10,5 L0,10 z" fill={c} />
                    </marker>
                  ))}
                </defs>
                {bands.map((b, i) => {
                  const c = COLORS[i % COLORS.length];
                  const pts = b.points.map(p => p.join(",")).join(" ");
                  return (
                    <g key={i}>
                      <polyline points={pts} fill="none" stroke={c} strokeOpacity={0.18} strokeWidth={b.height} strokeLinejoin="round" strokeLinecap="round" />
                      <polyline points={pts} fill="none" stroke={c} strokeWidth={cur.width / 500} markerEnd={`url(#pil${i % COLORS.length})`} />
                      {b.points.map((p, j) => (
                        <circle key={j} cx={p[0]} cy={p[1]} r={cur.width / 220} fill={j === 0 ? "#fff" : c} stroke={c} strokeWidth={cur.width / 900}
                          onMouseDown={e => { e.stopPropagation(); setActive(i); setDrag([i, j]); }} className="cursor-move" />
                      ))}
                    </g>
                  );
                })}
              </svg>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
