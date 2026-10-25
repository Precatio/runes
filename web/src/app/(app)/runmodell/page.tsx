"use client";

// Runmodellen: rita runslingornas mittlinjer på djupbilderna (api/routers/runmodell.py). Mittlinjen följer slingan i
// läsriktning, och bandet runt den ska täcka runorna men inte ramarna utanför; modellen läser sedan den uträtade
// slingan mot Rundatas text. En intern forskningssida, inte i menyn.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { API_URL } from "@/lib/api";

type Stone = { series: string; stem: string; file: string; signum: string | null; object: string | null;
  rune_types: string | null; transliteration: string | null; width: number; height: number; res_mm: number;
  bands: number; status: string | null; quality: string };
type Band = { points: [number, number][]; height: number };

const COLORS = ["#b7410e", "#1d4ed8", "#15803d", "#7e22ce", "#b45309", "#0e7490"];

// The ribbon's two edges: the centre line moved half the band height to each side (normals from neighbouring points)
function edges(points: [number, number][], half: number): string[] {
  if (points.length < 2) return [];
  const side = (s: number) => points.map((p, i) => {
    const a = points[Math.max(0, i - 1)], b = points[Math.min(points.length - 1, i + 1)];
    const dx = b[0] - a[0], dy = b[1] - a[1], n = Math.hypot(dx, dy) || 1;
    return `${p[0] - (s * half * dy) / n},${p[1] + (s * half * dx) / n}`;
  }).join(" ");
  return [side(1), side(-1)];
}

export default function RunmodellPage() {
  const [stones, setStones] = useState<Stone[]>([]);
  const [filter, setFilter] = useState("");
  const [cur, setCur] = useState<Stone | null>(null);
  const [bands, setBands] = useState<Band[]>([]);
  const [active, setActive] = useState(0);
  const [drag, setDrag] = useState<[number, number] | null>(null);
  const [msg, setMsg] = useState("");
  const [rot, setRot] = useState(0); // degrees clockwise the stone is shown turned; points stay in image coordinates
  const [quality, setQuality] = useState("");
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
    setRot(b.rotation ?? 0);
    setQuality(b.quality ?? "");
    setActive(0);
  };

  // The shown (turned) picture's size, and a click taken back to the image's own pixels
  const W = cur?.width ?? 1, H = cur?.height ?? 1;
  const viewW = rot % 180 === 0 ? W : H, viewH = rot % 180 === 0 ? H : W;
  const turn = rot === 90 ? `translate(${H},0) rotate(90)` : rot === 180 ? `translate(${W},${H}) rotate(180)`
    : rot === 270 ? `translate(0,${W}) rotate(270)` : undefined;
  const at = (e: React.MouseEvent): [number, number] => {
    const r = svg.current!.getBoundingClientRect();
    const k = viewW / r.width;
    const X = (e.clientX - r.left) * k, Y = (e.clientY - r.top) * k;
    const p = rot === 90 ? [Y, H - X] : rot === 180 ? [W - X, H - Y] : rot === 270 ? [W - Y, X] : [X, Y];
    return [Math.round(p[0]), Math.round(p[1])];
  };
  const addPoint = (e: React.MouseEvent) => {
    if (drag || !cur) return;
    const p = at(e);
    // Always a band to draw in: the first click on an empty stone starts one
    setBands(bs => (bs.length ? bs.map((b, i) => (i === active ? { ...b, points: [...b.points, p] } : b))
                              : [{ points: [p], height: Math.round(70 / cur.res_mm) }]));
    if (!bands.length) setActive(0);
  };
  const move = (e: React.MouseEvent) => {
    if (!drag || !cur) return;
    const p = at(e);
    setBands(bs => bs.map((b, i) => (i === drag[0] ? { ...b, points: b.points.map((q, j) => (j === drag[1] ? p : q)) } : b)));
  };
  const undo = () => setBands(bs => bs.map((b, i) => (i === active ? { ...b, points: b.points.slice(0, -1) } : b)));
  // The runes are usually the same height all over a stone: the height applies to every band
  const setHeight = (h: number) => setBands(bs => bs.map(b => ({ ...b, height: h })));
  const newBand = () => { setBands(bs => [...bs, { points: [], height: bands[active]?.height ?? 60 }]); setActive(bands.length); };
  const dropBand = () => { setBands(bs => bs.filter((_, i) => i !== active)); setActive(0); };

  // Pulls the drawn lines onto the runes (the analysis engine moves each point across the band to the densest grooves)
  const snap = async () => {
    if (!cur) return;
    const drawn = bands.map((b, i) => [b, i] as const).filter(([b]) => b.points.length >= 2);
    if (!drawn.length) { setMsg("Rita först minst två punkter längs slingan, sedan kan linjen fästas."); return; }
    const r = await fetch(`${API_URL}/api/runmodell/snap/${cur.series}/${cur.stem}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bands: drawn.map(([b]) => b) }) });
    if (!r.ok) { setMsg("Kunde inte fästa linjerna."); return; }
    const snapped: Band[] = (await r.json()).bands;
    // Only the drawn lines are replaced; bands with fewer than two points stay as they are
    setBands(bs => bs.map((b, i) => { const k = drawn.findIndex(([, j]) => j === i); return k >= 0 ? snapped[k] : b; }));
    setMsg("Linjerna fästa mot runorna – kontrollera och spara.");
  };

  // How readable the runes are; saved on its own, without touching the bands
  const rate = async (q: string) => {
    if (!cur) return;
    const r = await fetch(`${API_URL}/api/runmodell/quality/${cur.series}/${cur.stem}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ quality: q }) });
    if (r.ok) { setQuality(q); setStones(await load()); setMsg(q ? `Betyg: ${q}.` : "Betyget borttaget."); }
    else setMsg(`Kunde inte spara betyget: ${(await r.json()).detail ?? r.status}`);
  };

  const save = async (status: "utkast" | "granskad" | "överhoppad", note = "") => {
    if (!cur) return;
    const body = { bands: status === "överhoppad" ? [] : bands.filter(b => b.points.length >= 2), status, by: "Vitki", note,
                   rotation: rot, quality };
    if (status !== "överhoppad" && !body.bands.length && !window.confirm("Ingen slinga har minst två punkter. Spara stenen utan slingor?")) return;
    const r = await fetch(`${API_URL}/api/runmodell/band/${cur.series}/${cur.stem}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    setMsg(r.ok ? (status === "överhoppad" ? "Överhoppad – tas inte med i träningen." : `Sparat (${body.bands.length} slingor, ${status}).`)
                : `Kunde inte spara: ${(await r.json()).detail ?? r.status}`);
    setStones(await load());
  };

  const shown = useMemo(() => stones.filter(s =>
    filter === "betyg?" ? s.status === "granskad" && !s.quality
      : !filter || `${s.signum ?? ""} ${s.file} ${s.series}`.toLowerCase().includes(filter.toLowerCase())), [stones, filter]);
  const unrated = stones.filter(s => s.status === "granskad" && !s.quality).length;
  const done = stones.filter(s => s.status === "granskad").length;

  return (
    <div className="flex h-full w-full">
      <aside className="w-72 shrink-0 border-r border-slate-200 overflow-y-auto p-3 text-sm">
        <h1 className="text-lg font-bold">Runmodell</h1>
        <p className="text-xs text-slate-500 mb-2">{stones.length} djupbilder · {done} granskade ·{" "}
          <button type="button" className="underline" onClick={() => setFilter(f => (f === "betyg?" ? "" : "betyg?"))}>{unrated} utan läsbarhetsbetyg</button></p>
        <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Sök signum eller fil"
          className="w-full mb-2 rounded-lg border border-slate-300 px-2 py-1" />
        <ul className="space-y-0.5">
          {shown.map(s => (
            <li key={`${s.series}/${s.stem}`}>
              <button type="button" onClick={() => void open(s)}
                className={`w-full text-left rounded px-2 py-1 hover:bg-slate-100 ${cur?.stem === s.stem ? "bg-slate-200" : ""}`}>
                <span className="font-semibold">{s.signum ?? "–"}</span>{" "}
                <span className="text-slate-500 text-xs">{s.file.slice(0, 26)}</span>
                {s.status && <span className={`ml-1 text-[10px] font-bold ${s.status === "granskad" ? "text-emerald-700" : s.status === "överhoppad" ? "text-slate-400" : "text-amber-700"}`}>{s.status}</span>}
                {s.quality && <span className="ml-1 text-[10px] font-bold text-sky-700">{s.quality}</span>}
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
              flytta den. Ligger stenen ned, vrid den upprätt med ↻ 90° innan du ritar. Det räcker att rita grovt: <strong>Fäst mot runorna</strong> drar linjen till där spåren är tätast.
              Spara som granskad när slingorna stämmer och läsriktningen är rätt.</p>
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
              <label className="flex items-center gap-1" title="Bandets bredd tvärs över slingan, för alla slingor på stenen">Höjd {Math.round((bands[active]?.height ?? 0) * cur.res_mm)} mm
                <input type="range" min={10} max={250} value={bands[active]?.height ?? 60} onChange={e => setHeight(+e.target.value)} />
              </label>
              <button type="button" onClick={() => setRot(r => (r + 90) % 360)} className="px-2 py-1 rounded border border-slate-300" title="Vrid stenen så att den står upprätt">↻ 90°</button>
              <button type="button" onClick={() => void snap()} className="px-3 py-1 rounded border border-[#b7410e] text-[#b7410e] font-bold">Fäst mot runorna</button>
              <button type="button" onClick={() => void save("utkast")} className="px-3 py-1 rounded bg-slate-700 text-white">Spara utkast</button>
              <button type="button" onClick={() => void save("granskad")} className="px-3 py-1 rounded bg-emerald-700 text-white">Spara som granskad</button>
              <button type="button" className="px-3 py-1 rounded border border-slate-400 text-slate-600"
                onClick={() => { const why = window.prompt("Varför hoppas stenen över? (t.ex. runorna syns inte, stavlösa, för skadad)", "runorna syns inte på djupbilden"); if (why !== null) void save("överhoppad", why); }}>
                Hoppa över</button>
              <span className="ml-2 text-slate-500">Läsbarhet:</span>
              {(["tydlig", "medel", "svår"] as const).map(q => (
                <button key={q} type="button" onClick={() => void rate(quality === q ? "" : q)}
                  title="Hur tydligt runorna syns på djupbilden; modellen tränas först på de tydliga"
                  className={`px-2 py-1 rounded border ${quality === q ? "bg-slate-800 text-white border-slate-800" : "border-slate-300"}`}>{q}</button>
              ))}
            </div>
            <div className="max-w-full" style={{ width: `min(100%, ${viewW}px)` }}>
              <svg ref={svg} viewBox={`0 0 ${viewW} ${viewH}`} className="block w-full h-auto cursor-crosshair select-none"
                role="img" aria-label={`Djupbild av ${cur.signum ?? cur.file}`}
                onClick={addPoint} onMouseMove={move} onMouseUp={() => setTimeout(() => setDrag(null), 0)}>
                <g transform={turn}>
                <image href={`${API_URL}/api/runmodell/depth/${cur.series}/${cur.stem}.png`} width={W} height={H} />
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
                      <polyline points={pts} fill="none" stroke={c} strokeOpacity={0.15} strokeWidth={b.height} strokeLinejoin="round" strokeLinecap="round" />
                      {edges(b.points, b.height / 2).map((e, k) => (
                        <polyline key={k} points={e} fill="none" stroke={c} strokeWidth={cur.width / 700} strokeDasharray={`${cur.width / 150} ${cur.width / 300}`} />
                      ))}
                      <polyline points={pts} fill="none" stroke={c} strokeWidth={cur.width / 500} markerEnd={`url(#pil${i % COLORS.length})`} />
                      {b.points.map((p, j) => (
                        <circle key={j} cx={p[0]} cy={p[1]} r={cur.width / 220} fill={j === 0 ? "#fff" : c} stroke={c} strokeWidth={cur.width / 900}
                          onMouseDown={e => { e.stopPropagation(); setActive(i); setDrag([i, j]); }} className="cursor-move" />
                      ))}
                    </g>
                  );
                })}
                </g>
              </svg>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
