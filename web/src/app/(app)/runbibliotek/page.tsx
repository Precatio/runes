/* eslint-disable @next/next/no-img-element */
"use client";

// Referensbiblioteket för runformer (api/routers/runbibliotek.py). Bygg: klicka mitt på varje runa på de öppna
// skanningarnas djupbilder i läsordning; klick nummer k hör till textens runa nummer k, och stenens ristare kommer ur
// Rundata. Biblioteket: runorna per ristare och runa. Runutsnitt i appen jämförs med biblioteket under "Jämför med
// ristare" (components/RuneCropDetail.tsx).
import { useCallback, useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import { runeForLetter } from "@/lib/runes";

type CarverRef = { name: string; kind: string; uncertain: boolean };
type StoneRow = { series: string; stem: string; file: string; signum: string | null; rune_types: string | null;
  carvers: CarverRef[]; runes: number; placed: number; skipped: number; status: string | null };
type Rune = { i: number; letter: string; uncertain: boolean; lost: boolean; word: number };
// w, h: the rune's own box (along and across the band, displayed pixels) when resized; else the stone's box
type Mark = { i: number; x: number | null; y: number | null; skip: boolean; w?: number | null; h?: number | null };
type Band = { points: [number, number][]; height: number };
type Stone = { series: string; stem: string; signum: string | null; file: string; rune_types: string | null;
  transliteration: string | null; runes: Rune[]; carvers: CarverRef[]; width: number; height: number; res_mm: number;
  marks: Mark[]; box: number; status: string | null; rotation: number; bands: Band[] };
type Form = { series: string; stem: string; i: number; signum: string; letter: string; uncertain: boolean;
  carvers: CarverRef[]; url: string; status: string | null };
type CarverSummary = { carver: string; signed: boolean; stones: string[]; runes: number; letters: Record<string, number> };

// The crop's width along the reading direction, as a share of the box (api/routers/runbibliotek.py RUNE_WIDTH)
const RUNE_WIDTH = 0.6;

// The drawn band's reading direction at a point (the nearest segment of the nearest band, within the band's height),
// as api/routers/runbibliotek.band_direction: the order of the clicks does not matter
function bandDirection(bands: Band[], x: number, y: number): number | null {
  let best: [number, number] | null = null;
  for (const b of bands) {
    for (let k = 0; k + 1 < b.points.length; k++) {
      const [x0, y0] = b.points[k], [x1, y1] = b.points[k + 1];
      const dx = x1 - x0, dy = y1 - y0, ll = dx * dx + dy * dy;
      if (ll <= 0) continue;
      const t = Math.max(0, Math.min(1, ((x - x0) * dx + (y - y0) * dy) / ll));
      const d = Math.hypot(x - (x0 + t * dx), y - (y0 + t * dy));
      if (d <= b.height && (!best || d < best[0])) best = [d, Math.atan2(dy, dx)];
    }
  }
  return best ? best[1] : null;
}

const carverText = (cs: CarverRef[]) => cs.filter(c => !c.uncertain).map(c => `${c.name}${c.kind === "S" ? " (signerad)" : ""}`).join(", ")
  || (cs.length ? `${cs.map(c => c.name).join(", ")} (osäker)` : "ingen ristare i Rundata");

export default function RunbibliotekPage() {
  const [tab, setTab] = useState<"bygg" | "bibliotek">("bygg");
  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-2">
        <h1 className="text-lg font-bold mr-4">Referensbibliotek för runformer</h1>
        {([["bygg", "Bygg biblioteket"], ["bibliotek", "Biblioteket"]] as const).map(([v, label]) => (
          <button key={v} type="button" onClick={() => setTab(v)}
            className={`px-3 py-1.5 rounded-lg text-sm font-bold ${tab === v ? "bg-slate-900 text-white" : "border border-slate-300"}`}>{label}</button>
        ))}
      </div>
      <div className="flex-1 min-h-0">{tab === "bygg" ? <Build /> : <Library />}</div>
    </div>
  );
}

// ---- building: place the runes of one scan ----------------------------------------------------------------------
function Build() {
  const [stones, setStones] = useState<StoneRow[]>([]);
  const [filter, setFilter] = useState("");
  const [onlyCarver, setOnlyCarver] = useState(true);
  const [cur, setCur] = useState<Stone | null>(null);
  const [marks, setMarks] = useState<Mark[]>([]);
  const [box, setBox] = useState(40);
  const [rot, setRot] = useState(0);
  const [cursor, setCursor] = useState(0);
  const [msg, setMsg] = useState("");
  const [img, setImg] = useState<HTMLImageElement | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  // Moving or resizing a placed box: which mark, how, and where the drag started; a drag is not also a click
  const [drag, setDrag] = useState<{ i: number; kind: "move" | "size"; from: [number, number]; x: number; y: number } | null>(null);
  const dragged = useRef(false);

  const load = useCallback(() => fetch(`${API_URL}/api/runbibliotek/stones`).then(r => r.json()).then(d => d.stones as StoneRow[]), []);
  useEffect(() => {
    let alive = true;
    load().then(s => { if (alive) setStones(s); }).catch(() => setMsg("Analysmotorn svarar inte."));
    return () => { alive = false; };
  }, [load]);

  // The first rune at or after k that can still be placed (not lost, not placed or skipped)
  const nextOpen = (runes: Rune[], ms: Mark[], k: number) => {
    const done = new Set(ms.map(m => m.i));
    for (let j = k; j < runes.length; j++) if (!runes[j].lost && !done.has(j)) return j;
    return runes.length;
  };

  const open = async (s: StoneRow) => {
    setMsg("");
    const d: Stone = await fetch(`${API_URL}/api/runbibliotek/stone/${s.series}/${s.stem}`).then(r => r.json());
    setCur(d); setMarks(d.marks); setBox(Math.round(d.box)); setRot(d.rotation ?? 0);
    setCursor(nextOpen(d.runes, d.marks, 0));
    const im = new Image();
    im.crossOrigin = "anonymous";
    im.onload = () => setImg(im);
    im.src = `${API_URL}/api/runmodell/depth/${s.series}/${s.stem}.png`;
  };

  const W = cur?.width ?? 1, H = cur?.height ?? 1;
  const viewW = rot % 180 === 0 ? W : H, viewH = rot % 180 === 0 ? H : W;
  const turn = rot === 90 ? `translate(${H},0) rotate(90)` : rot === 180 ? `translate(${W},${H}) rotate(180)`
    : rot === 270 ? `translate(0,${W}) rotate(270)` : undefined;
  const at = (e: React.MouseEvent): [number, number] => {
    const r = svg.current!.getBoundingClientRect();
    const k = viewW / r.width;
    const X = (e.clientX - r.left) * k, Y = (e.clientY - r.top) * k;
    const p = rot === 90 ? [Y, H - X] : rot === 180 ? [W - X, H - Y] : rot === 270 ? [W - Y, X] : [X, Y];
    return [Math.round(p[0] * 10) / 10, Math.round(p[1] * 10) / 10];
  };

  const place = (e: React.MouseEvent) => {
    if (dragged.current) { dragged.current = false; return; }
    if (!cur || cursor >= cur.runes.length) return;
    const [x, y] = at(e);
    const ms = [...marks.filter(m => m.i !== cursor), { i: cursor, x, y, skip: false }].sort((a, b) => a.i - b.i);
    setMarks(ms);
    setCursor(nextOpen(cur.runes, ms, cursor + 1));
  };
  const skip = () => {
    if (!cur || cursor >= cur.runes.length) return;
    const ms = [...marks.filter(m => m.i !== cursor), { i: cursor, x: null, y: null, skip: true }].sort((a, b) => a.i - b.i);
    setMarks(ms);
    setCursor(nextOpen(cur.runes, ms, cursor + 1));
  };
  const undo = () => {
    if (!marks.length) return;
    const last = marks.reduce((a, m) => (m.i > a.i ? m : a), marks[0]);
    setMarks(marks.filter(m => m !== last));
    setCursor(last.i);
  };
  const save = async (status: "utkast" | "granskad") => {
    if (!cur) return;
    const r = await fetch(`${API_URL}/api/runbibliotek/stone/${cur.series}/${cur.stem}`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ marks, box, status, rotation: rot, by: "Vitki" }) });
    setMsg(r.ok ? `Sparat: ${marks.filter(m => !m.skip).length} runor, ${status}.` : `Kunde inte spara: ${(await r.json()).detail ?? r.status}`);
    setStones(await load());
  };

  // The reading direction at a mark (radians, y down): the drawn band's where the rune stands; without a band, from the
  // placed rune before to the one after, when near
  const directionAt = (m: Mark, ms: Mark[]) => {
    const fromBand = cur && m.x != null ? bandDirection(cur.bands, m.x, m.y!) : null;
    if (fromBand !== null) return fromBand;
    const placed = ms.filter(q => !q.skip && q.x != null);
    const j = placed.findIndex(q => q.i === m.i);
    const near = (q?: Mark) => q && q.x != null && Math.hypot(q.x - m.x!, q.y! - m.y!) <= 3 * box ? q : undefined;
    const a = near(placed[j - 1]) ?? m, b = near(placed[j + 1]) ?? m;
    return a === b ? 0 : Math.atan2(b.y! - a.y!, b.x! - a.x!);
  };
  const hOf = (m: Mark) => m.h ?? box;
  const wOf = (m: Mark) => m.w ?? box * RUNE_WIDTH;
  // Dragging: the box follows the pointer (move), or its corner does (resize, in the box's own turned frame)
  const onMove = (e: React.MouseEvent) => {
    if (!drag || !cur) return;
    const p = at(e);
    dragged.current = true;
    setMarks(ms => ms.map(m => {
      if (m.i !== drag.i || m.x == null) return m;
      if (drag.kind === "move") return { ...m, x: Math.round((drag.x + p[0] - drag.from[0]) * 10) / 10, y: Math.round((drag.y + p[1] - drag.from[1]) * 10) / 10 };
      const a = directionAt(m, ms), dx = p[0] - m.x, dy = p[1] - m.y!;
      const along = Math.abs(dx * Math.cos(a) + dy * Math.sin(a)), across = Math.abs(-dx * Math.sin(a) + dy * Math.cos(a));
      return { ...m, w: Math.max(6, Math.round(2 * along)), h: Math.max(6, Math.round(2 * across)) };
    }));
  };
  const startDrag = (e: React.MouseEvent, m: Mark, kind: "move" | "size") => {
    e.stopPropagation();
    dragged.current = false;
    setCursor(m.i);
    setDrag({ i: m.i, kind, from: at(e), x: m.x!, y: m.y! });
  };
  const resetSize = (i: number) => setMarks(ms => ms.map(m => (m.i === i ? { ...m, w: null, h: null } : m)));

  // A preview of the last placed runes, cut out as the library will (turned by the reading direction, the rune's width)
  const preview = (m: Mark, ms: Mark[]) => {
    if (!img || m.x == null || m.y == null) return null;
    const ang = directionAt(m, ms);
    const c = document.createElement("canvas");
    c.width = c.height = 72;
    const ctx = c.getContext("2d")!;
    ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, 72, 72);
    ctx.save();
    const big = Math.max(hOf(m), wOf(m));
    ctx.translate(36, 36); ctx.scale(72 / big, 72 / big); ctx.rotate(-ang);
    ctx.drawImage(img, -m.x, -m.y);
    ctx.restore();
    const sw = (72 * (1 - wOf(m) / big)) / 2, sh = (72 * (1 - hOf(m) / big)) / 2;
    ctx.fillRect(0, 0, sw, 72); ctx.fillRect(72 - sw, 0, sw, 72);
    ctx.fillRect(0, 0, 72, sh); ctx.fillRect(0, 72 - sh, 72, sh);
    return c.toDataURL();
  };

  const shown = stones.filter(s => (!onlyCarver || s.carvers.some(c => !c.uncertain))
    && (!filter || `${s.signum ?? ""} ${s.file} ${s.carvers.map(c => c.name).join(" ")}`.toLowerCase().includes(filter.toLowerCase())));
  const current = cur?.runes[cursor];
  const placedN = marks.filter(m => !m.skip).length;
  const lastPlaced = [...marks].filter(m => !m.skip).sort((a, b) => b.i - a.i).slice(0, 8);

  return (
    <div className="flex h-full w-full">
      <aside className="w-72 shrink-0 border-r border-slate-200 overflow-y-auto p-3 text-sm">
        <p className="text-xs text-slate-500 mb-2">{`${stones.length} skanningar med text · ${stones.filter(s => s.placed).length} påbörjade · ${stones.reduce((a, s) => a + s.placed, 0)} runor placerade`}</p>
        <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Sök signum, fil eller ristare"
          className="w-full mb-2 rounded-lg border border-slate-300 px-2 py-1" />
        <label className="flex items-center gap-1.5 text-xs mb-2"><input type="checkbox" checked={onlyCarver} onChange={e => setOnlyCarver(e.target.checked)} />
          Bara stenar med säker ristare</label>
        <ul className="space-y-0.5">
          {shown.map(s => (
            <li key={`${s.series}/${s.stem}`}>
              <button type="button" onClick={() => void open(s)}
                className={`w-full text-left rounded px-2 py-1 hover:bg-slate-100 ${cur?.stem === s.stem ? "bg-slate-200" : ""}`}>
                <span className="font-semibold">{s.signum ?? "–"}</span>{" "}
                <span className="text-xs text-slate-600">{s.carvers.filter(c => !c.uncertain).map(c => c.name).join(", ")}</span>
                <span className="block text-[11px] text-slate-500">{s.file.slice(0, 30)} · {s.placed}/{s.runes}
                  {s.status && <span className={`ml-1 font-bold ${s.status === "granskad" ? "text-emerald-700" : "text-amber-700"}`}>{s.status}</span>}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="flex-1 overflow-auto p-4">
        {!cur ? (
          <div className="max-w-2xl text-slate-600 leading-relaxed space-y-2">
            <h2 className="text-xl font-bold text-slate-900">Bygg referensbiblioteket</h2>
            <p>Välj en skanning. Under bilden står Rundatas text som runor i läsordning, och den runa som står på tur är
              markerad. Klicka mitt på den runan i djupbilden. Appen går då vidare till nästa runa i texten.</p>
            <p>Syns en runa inte, eller är den för skadad, tryck på Hoppa över. Klickar du på en runa i texten kan du
              placera om den. Rutan ska rymma en hel runa, och storleken ändras med reglaget. Utsnitten vrids upprätt
              efter slingans läsriktning där runan står, så du kan klicka runorna i vilken ordning du vill, bara du väljer
              rätt runa i texten. Klicka inte samma runa på stenen två gånger.</p>
            <p>En placerad ruta kan dras till rätt plats, och hörnhandtaget ändrar dess bredd och höjd. Dubbelklicka på
              rutan för att återgå till standardstorleken.</p>
            <p>Börja gärna med stenar som Rundata anger som signerade: de är det säkra facit när biblioteket prövas.</p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2 mb-2 text-sm">
              <strong className="text-base">{cur.signum ?? cur.file}</strong>
              <span className="text-slate-600">{carverText(cur.carvers)}</span>
              {cur.rune_types && <span className="text-slate-500">· {cur.rune_types}</span>}
              <span className="ml-auto text-emerald-800">{msg}</span>
            </div>
            <p className="mb-1 text-[11px] text-slate-500">
              Texten i den yngre futharken, med Rundatas bokstav under varje runa
              {/stavlös/i.test(cur.rune_types ?? "") ? ". Stavlösa runor finns inte som tecken, så de visas som kortkvistrunor." : "."}
            </p>
            <div className="mb-2 flex flex-wrap gap-x-3 gap-y-2 text-sm bg-slate-50 border border-slate-200 rounded p-2">
              {Object.values(cur.runes.reduce<Record<number, Rune[]>>((acc, r) => { (acc[r.word] ??= []).push(r); return acc; }, {})).map((w, k) => (
                <span key={k} className="flex">
                  {w.map(r => {
                    const m = marks.find(q => q.i === r.i);
                    const cls = r.i === cursor ? "ring-2 ring-[#b7410e] bg-white" : m?.skip ? "text-slate-400 line-through"
                      : m ? "bg-emerald-100 text-emerald-900" : r.lost ? "text-slate-300" : "";
                    return (
                      <button key={r.i} type="button" disabled={r.lost} onClick={() => setCursor(r.i)}
                        title={`Runa ${r.i + 1}${r.uncertain ? " (osäker läsning)" : ""}`}
                        className={`px-0.5 rounded flex flex-col items-center leading-none ${cls} ${r.uncertain ? "opacity-70" : ""}`}>
                        <span className="text-xl">{runeForLetter(r.letter, cur.rune_types)}</span>
                        <span className="text-[9px] font-mono text-slate-500 mt-0.5">{r.letter}</span>
                      </button>
                    );
                  })}
                </span>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2 mb-2 text-sm">
              {current ? (
                <span className="font-bold">{`På tur: runa ${cursor + 1}`}{" "}<span className="text-2xl align-middle">{runeForLetter(current.letter, cur.rune_types)}</span>{" "}
                  <span className="font-mono text-xs text-slate-500">{current.letter}</span>{current.uncertain ? " (osäker)" : ""}</span>
              ) : <span className="font-bold">Alla runor är placerade eller överhoppade.</span>}
              <button type="button" onClick={skip} disabled={!current} className="px-2 py-1 rounded border border-slate-300 disabled:opacity-40">Hoppa över</button>
              <button type="button" onClick={undo} className="px-2 py-1 rounded border border-slate-300">Ångra</button>
              <label className="flex items-center gap-1">{`Ruta ${Math.round(box * cur.res_mm)} mm`}
                <input type="range" min={10} max={160} value={box} onChange={e => setBox(+e.target.value)} />
              </label>
              <button type="button" onClick={() => setRot(r => (r + 90) % 360)} className="px-2 py-1 rounded border border-slate-300">↻ 90°</button>
              <span className="text-slate-500">{`${placedN} placerade`}</span>
              <button type="button" onClick={() => void save("utkast")} className="px-3 py-1 rounded bg-slate-700 text-white">Spara utkast</button>
              <button type="button" onClick={() => void save("granskad")} className="px-3 py-1 rounded bg-emerald-700 text-white">Spara som granskad</button>
            </div>
            {lastPlaced.length > 0 && (
              <div className="mb-2 flex gap-2 items-end">
                {lastPlaced.map(m => {
                  const src = preview(m, marks);
                  return src ? (
                    <div key={m.i} className="text-center text-[10px] text-slate-500">
                      <img src={src} alt={`Runa ${m.i + 1}`} className="w-16 h-16 border border-slate-200 rounded" />
                      {m.i + 1} {runeForLetter(cur.runes[m.i]?.letter ?? "", cur.rune_types)}
                    </div>
                  ) : null;
                })}
                <span className="text-[11px] text-slate-500 ml-2">Så klipps runorna ut (förhandsvisning i lägre upplösning).</span>
              </div>
            )}
            <div className="max-w-full" style={{ width: `min(100%, ${viewW}px)` }}>
              <svg ref={svg} viewBox={`0 0 ${viewW} ${viewH}`} className="block w-full h-auto cursor-crosshair select-none"
                role="img" aria-label={`Djupbild av ${cur.signum ?? cur.file}`} onClick={place}
                onMouseMove={onMove} onMouseUp={() => setDrag(null)} onMouseLeave={() => setDrag(null)}>
                <g transform={turn}>
                  <image href={`${API_URL}/api/runmodell/depth/${cur.series}/${cur.stem}.png`} width={W} height={H} />
                  {cur.bands.map((b, i) => (
                    <polyline key={i} points={b.points.map(p => p.join(",")).join(" ")} fill="none" stroke="#1d4ed8"
                      strokeOpacity={0.08} strokeWidth={b.height} strokeLinejoin="round" strokeLinecap="round" />
                  ))}
                  {marks.filter(m => !m.skip && m.x != null).map(m => (
                    <g key={m.i}>
                      <g transform={`translate(${m.x} ${m.y}) rotate(${(directionAt(m, marks) * 180) / Math.PI})`}>
                        <rect x={-wOf(m) / 2} y={-hOf(m) / 2} width={wOf(m)} height={hOf(m)} fill="#15803d" fillOpacity={0.04}
                          stroke={m.i === cursor ? "#b7410e" : "#15803d"} strokeWidth={W / 600} className="cursor-move"
                          onMouseDown={e => startDrag(e, m, "move")} onClick={e => e.stopPropagation()}
                          onDoubleClick={e => { e.stopPropagation(); resetSize(m.i); }}>
                          <title>Dra för att flytta, dubbelklicka för rutans standardstorlek</title>
                        </rect>
                        <rect x={wOf(m) / 2 - W / 160} y={hOf(m) / 2 - W / 160} width={W / 80} height={W / 80}
                          fill={m.i === cursor ? "#b7410e" : "#15803d"} className="cursor-nwse-resize"
                          onMouseDown={e => startDrag(e, m, "size")} onClick={e => e.stopPropagation()}>
                          <title>Dra för att ändra rutans storlek</title>
                        </rect>
                      </g>
                      <text x={m.x! - box / 2} y={m.y! - box / 2 - W / 300} fontSize={W / 60} fill="#15803d">{m.i + 1} {runeForLetter(cur.runes[m.i]?.letter ?? "", cur.rune_types)}</text>
                    </g>
                  ))}
                </g>
              </svg>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

// ---- the library: runes per carver and letter -----------------------------------------------------------------------
function Library() {
  const [sum, setSum] = useState<{ carvers: CarverSummary[]; runes: number } | null>(null);
  const [carver, setCarver] = useState<string | null>(null);
  const [letter, setLetter] = useState<string | null>(null);
  const [forms, setForms] = useState<Form[]>([]);
  useEffect(() => {
    let alive = true;
    fetch(`${API_URL}/api/runbibliotek/summary`).then(r => r.json()).then(d => { if (alive) setSum(d); }).catch(() => {});
    return () => { alive = false; };
  }, []);
  const pick = async (l: string) => {
    setLetter(l);
    const d = await fetch(`${API_URL}/api/runbibliotek/forms?letter=${encodeURIComponent(l)}&with_vectors=false`).then(r => r.json());
    setForms(d.forms);
  };
  if (!sum) return <p className="p-4 text-sm text-slate-500">Hämtar biblioteket … (första gången räknas formerna fram, det kan ta en stund)</p>;
  if (!sum.runes) return <p className="p-4 text-sm text-slate-600">Biblioteket är tomt ännu. Placera runor under Bygg biblioteket.</p>;
  const cur = sum.carvers.find(c => c.carver === carver);
  const byCarver = (f: Form) => f.carvers.filter(c => !c.uncertain).map(c => c.name);
  const groups = letter ? sum.carvers.map(c => ({
    c, items: forms.filter(f => c.carver === "(ingen säker ristare)" ? byCarver(f).length === 0 : byCarver(f).includes(c.carver)),
  })).filter(g => g.items.length && (!carver || g.c.carver === carver)) : [];
  return (
    <div className="flex h-full w-full">
      <aside className="w-72 shrink-0 border-r border-slate-200 overflow-y-auto p-3 text-sm">
        {(() => { const n = new Set(sum.carvers.flatMap(c => c.stones)).size; return (
          <p className="text-xs text-slate-500 mb-2">{`${sum.runes} runor från ${n} ${n === 1 ? "sten" : "stenar"}`}</p>); })()}
        <button type="button" onClick={() => setCarver(null)} className={`w-full text-left rounded px-2 py-1 ${!carver ? "bg-slate-200" : "hover:bg-slate-100"}`}>Alla ristare</button>
        {sum.carvers.map(c => (
          <button key={c.carver} type="button" onClick={() => setCarver(c.carver)}
            className={`w-full text-left rounded px-2 py-1 ${carver === c.carver ? "bg-slate-200" : "hover:bg-slate-100"}`}>
            <span className="font-semibold">{c.carver}</span>{c.signed && <span className="ml-1 text-[10px] font-bold text-emerald-700">signerar</span>}
            <span className="block text-[11px] text-slate-500">{`${c.runes} runor på ${c.stones.length} ${c.stones.length === 1 ? "sten" : "stenar"}`}</span>
          </button>
        ))}
      </aside>
      <main className="flex-1 overflow-auto p-4 space-y-4">
        <div>
          <p className="text-sm text-slate-700 mb-2">{cur ? `${cur.carver}: ${cur.stones.join(", ")}` : "Välj en runa för att se den hos alla ristare, eller en ristare till vänster."}</p>
          <div className="flex flex-wrap gap-1">
            {Object.entries(cur ? cur.letters : sum.carvers.reduce<Record<string, number>>((acc, c) => {
              for (const [l, n] of Object.entries(c.letters)) acc[l] = (acc[l] ?? 0) + n;
              return acc;
            }, {})).sort((a, b) => b[1] - a[1]).map(([l, n]) => (
              <button key={l} type="button" onClick={() => void pick(l)}
                className={`px-2 py-1 rounded border ${letter === l ? "bg-slate-900 text-white border-slate-900" : "border-slate-300"}`}><span className="text-lg">{runeForLetter(l)}</span> <span className="font-mono text-xs">{l}</span> <span className="text-[10px]">{n}</span></button>
            ))}
          </div>
        </div>
        {groups.map(g => (
          <div key={g.c.carver}>
            <h3 className="text-sm font-bold text-slate-800 mb-1">{g.c.carver}{g.c.signed ? " (signerar)" : ""} · {g.items.length}</h3>
            <div className="flex flex-wrap gap-2">
              {g.items.map(f => (
                <div key={`${f.series}/${f.stem}/${f.i}`} className="text-center text-[10px] text-slate-500" title={`${f.signum}, runa ${f.i + 1}${f.uncertain ? " (osäker)" : ""}`}>
                  <img src={`${API_URL}${f.url}`} alt={`${f.letter} på ${f.signum}`} className="w-16 h-16 border border-slate-200 rounded bg-white" />
                  {f.signum}
                </div>
              ))}
            </div>
          </div>
        ))}
        <p className="text-[11px] text-slate-500 max-w-3xl">
          Runorna är utklippta ur de öppna 3D-skanningarnas djupbilder och vridna upprätt efter läsriktningen. Ristaren är
          den Rundata anger med säkerhet (signerad eller attribuerad). Rundatas attribueringar bygger delvis på runformer,
          så de signerade stenarna är det säkra facit när biblioteket prövas.
        </p>
      </main>
    </div>
  );
}
