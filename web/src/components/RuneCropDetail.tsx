/* eslint-disable @next/next/no-img-element */
"use client";

// A saved rune crop on its own: turn it upright (a rune cut where the text runs at an angle, e.g. 45°, compares badly
// until it stands as in an upright row), set or change which rune it is, remove it, and compare its form with the same
// rune on other stones – the most alike, and grouped by the carvers Rundata names for the stones.
import { useEffect, useState } from "react";
import { RUNE_TAGS } from "@/lib/runes";
import { rundata, type Inscription } from "@/lib/rundata";
import {
  carversOf, comparable, cosine, saveCrop, turnCrop, type CropWithStone,
} from "@/lib/runeForms";

const fmt = (v: number, d = 2) => (Number.isFinite(v) ? v.toFixed(d).replace(".", ",") : "–");
const TURNS: [number, string][] = [[-90, "↺ 90°"], [-45, "↺ 45°"], [-15, "↺ 15°"], [15, "↻ 15°"], [45, "↻ 45°"], [90, "↻ 90°"], [180, "180°"]];

interface CarverGroup { carver: string; own: boolean; crops: (CropWithStone & { likeness: number })[]; stones: number; mean: number }

export default function RuneCropDetail({ item, all, onClose, onChanged }: {
  item: CropWithStone; all: CropWithStone[]; onClose: () => void; onChanged: (updated: CropWithStone | null) => void;
}) {
  const [turn, setTurn] = useState(0);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [sameTagOnly, setSameTagOnly] = useState(true);
  const [view, setView] = useState<"alike" | "carvers">("alike");
  const [recs, setRecs] = useState<Record<string, Inscription | null>>({});
  const crop = item.crop;

  // Rundata for every stone that has crops, for the carvers (fetched once per stone)
  const signa = [...new Set(all.map(c => c.signum).filter(Boolean))];
  const signaKey = signa.join("|");
  useEffect(() => {
    let cancelled = false;
    const missing = signa.filter(s => !(s in recs));
    if (!missing.length) return;
    Promise.all(missing.map(s => rundata.inscription(s).then(r => [s, r] as const).catch(() => [s, null] as const)))
      .then(rows => { if (!cancelled) setRecs(r => ({ ...r, ...Object.fromEntries(rows) })); });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps -- signaKey stands for signa
  }, [signaKey, recs]);

  const others = all.filter(c => c.crop.id !== crop.id && comparable(crop, c.crop) && (!sameTagOnly || c.crop.tag === crop.tag));
  const alike = others
    .map(c => ({ ...c, likeness: cosine(crop.featureVector!, c.crop.featureVector!) }))
    .sort((a, b) => b.likeness - a.likeness);
  const ownCarvers = carversOf(recs[item.signum]?.carvers).certain;

  // The same rune grouped by carver: the stone itself as a reference (how alike the rune is to its siblings), each
  // certain carver's other stones, and the stones with no certain carver
  const groups: CarverGroup[] = (() => {
    const same = alike.filter(c => c.crop.tag === crop.tag);
    const by = new Map<string, (CropWithStone & { likeness: number })[]>();
    const add = (k: string, c: CropWithStone & { likeness: number }) => by.set(k, [...(by.get(k) ?? []), c]);
    for (const c of same) {
      if (c.signum === item.signum) { add("\u0000Samma sten", c); continue; }
      const names = carversOf(recs[c.signum]?.carvers).certain;
      if (!names.length) add("\u0001Utan säker ristare", c);
      for (const n of names) add(n, c);
    }
    return [...by.entries()].map(([k, cs]) => ({
      carver: k.replace(/^[\u0000\u0001]/, ""), own: ownCarvers.includes(k),
      crops: cs, stones: new Set(cs.map(c => c.signum)).size, mean: cs.reduce((a, c) => a + c.likeness, 0) / cs.length,
    })).sort((a, b) => (a.carver === "Samma sten" ? -1 : b.carver === "Samma sten" ? 1 : b.mean - a.mean));
  })();

  const save = async (updated: PaleographicCropLike | null, message: string) => {
    setBusy(true);
    setNote(null);
    try {
      await saveCrop(item.projectId, crop.id, updated);
      onChanged(updated ? { ...item, crop: updated } : null);
      setNote(message);
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Kunde inte spara.");
    } finally {
      setBusy(false);
    }
  };
  const applyTurn = async () => {
    if (!turn) return;
    setBusy(true);
    try {
      const turned = await turnCrop(crop, turn);
      setTurn(0);
      await save(turned, `Utsnittet är vridet ${turn > 0 ? "medurs" : "moturs"} ${Math.abs(turn)}° och formen är beskriven på nytt.`);
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Kunde inte vrida utsnittet.");
      setBusy(false);
    }
  };

  return (
    <div className="liquid-glass-island rounded-[36px] p-6 border border-[#b7410e]/20 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-800">{crop.tag} · {item.signum}</h3>
        <button onClick={onClose} className="text-xs text-slate-500 hover:text-slate-900">Stäng</button>
      </div>

      <div className="flex gap-4 items-start">
        <div className="w-40 h-40 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-center overflow-hidden">
          <img src={crop.imageBase64} alt={crop.tag} className="max-w-full max-h-full object-contain transition-transform"
            style={{ transform: `rotate(${turn}deg)` }} />
        </div>
        <div className="flex-1 space-y-2 text-xs text-slate-600">
          <label className="block font-bold text-slate-700">Runa
            <select value={crop.tag} disabled={busy}
              onChange={e => save({ ...crop, tag: e.target.value }, "Runan är ändrad.")}
              className="mt-1 w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 font-semibold">
              {RUNE_TAGS.map(r => <option key={r.tag} value={r.tag}>{r.tag}{r.name ? ` (${r.name})` : ""}</option>)}
            </select>
          </label>
          <div>
            <div className="font-bold text-slate-700">Vrid utsnittet</div>
            <p className="mt-0.5">
              Vrid så att runan står upprätt, som i en lodrät rad. Formjämförelsen tar hänsyn till riktningen, så en runa
              som är ristad i en lutande slinga jämförs först rätt när den står upp.
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {TURNS.map(([d, label]) => (
                <button key={d} type="button" disabled={busy} onClick={() => setTurn(t => ((t + d + 540) % 360) - 180)}
                  className="px-2 py-1 rounded-lg border border-slate-300 bg-white font-bold hover:border-slate-900 disabled:opacity-40">{label}</button>
              ))}
            </div>
            <input type="range" min={-180} max={180} value={turn} disabled={busy} onChange={e => setTurn(Number(e.target.value))}
              className="w-full accent-[#b7410e] mt-1" aria-label="Vridning i grader" />
            <div className="flex items-center gap-2">
              <span className="tabular-nums">{turn > 0 ? `medurs ${turn}°` : turn < 0 ? `moturs ${-turn}°` : "ingen vridning"}</span>
              <button type="button" disabled={busy || !turn} onClick={applyTurn}
                className="ml-auto px-3 py-1.5 rounded-lg bg-slate-900 text-white font-bold disabled:opacity-40">Spara vridningen</button>
              {turn !== 0 && <button type="button" onClick={() => setTurn(0)} className="text-slate-500 underline">Ångra</button>}
            </div>
            {!!crop.rotationDeg && <p className="mt-1 text-slate-500">{`Vridet ${crop.rotationDeg > 0 ? "medurs" : "moturs"} ${Math.abs(crop.rotationDeg)}° sedan det sparades.`}</p>}
          </div>
          {crop.formPng && (
            <div className="flex items-center gap-2">
              <img src={crop.formPng} alt="Normaliserad form" className="w-12 h-12 border border-slate-200 rounded bg-white" />
              <span>Formen som jämförs.</span>
            </div>
          )}
          <button type="button" disabled={busy}
            onClick={() => { if (confirm("Ta bort runutsnittet ur projektet?")) save(null, "Utsnittet är borttaget."); }}
            className="text-red-700 underline disabled:opacity-40">Ta bort utsnittet</button>
          {note && <p className="text-emerald-800">{note}</p>}
        </div>
      </div>

      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
        {([["alike", "Mest lika runformer"], ["carvers", "Jämför med ristare"]] as const).map(([v, label]) => (
          <button key={v} type="button" onClick={() => setView(v)}
            className={`flex-1 py-1.5 rounded-lg ${view === v ? "bg-white shadow-sm text-slate-900" : "text-slate-500"}`}>{label}</button>
        ))}
      </div>

      {!crop.featureVersion && <p className="text-xs text-amber-700">Utsnittet är sparat med en äldre formbeskrivning. En vridning ger det en ny, så att det kan jämföras.</p>}

      {view === "alike" && (
        <div>
          <label className="flex items-center gap-2 text-xs text-slate-600 mb-2">
            <input type="checkbox" checked={sameTagOnly} onChange={e => setSameTagOnly(e.target.checked)} /> Bara samma runa
          </label>
          {alike.length === 0 ? <p className="text-sm text-slate-500">Inga jämförbara utsnitt ännu. Spara samma runa från fler stenar.</p> : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {alike.slice(0, 12).map(c => (
                <div key={c.crop.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                  <div className="h-20 flex items-center justify-center bg-slate-50 p-1.5">
                    <img src={c.crop.imageBase64} alt={c.crop.tag} className="max-w-full max-h-full object-contain" />
                  </div>
                  <div className="px-2 py-1.5 text-[11px]">
                    <div className="font-bold text-slate-800 truncate">{c.signum}</div>
                    <div className="text-slate-500">{c.crop.tag} · formlikhet {fmt(c.likeness)}</div>
                    {c.crop.grooveSummary && <div className="text-emerald-700">{fmt(c.crop.grooveSummary.angle_mean, 1)}° ({c.crop.grooveSummary.n} snitt)</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {view === "carvers" && (
        <div className="space-y-3">
          <p className="text-xs text-slate-600">
            Samma runa på stenar som Rundata tillskriver en ristare med säkerhet (signerad eller attribuerad). Raden
            Samma sten visar hur lika runan är sina syskon på samma sten. En ristare vars runor är lika lika som dem är
            en kandidat, men få utsnitt ger stor osäkerhet.
            {ownCarvers.length > 0 && <> Stenens ristare enligt Rundata: <strong>{ownCarvers.join(", ")}</strong>.</>}
          </p>
          {groups.length === 0 ? <p className="text-sm text-slate-500">Inga utsnitt av samma runa på andra stenar ännu.</p> : (
            <div className="divide-y divide-slate-100 bg-white rounded-xl border border-slate-200">
              {groups.map(g => (
                <div key={g.carver} className={`p-3 ${g.own ? "bg-amber-50" : ""}`}>
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <span className="font-bold text-slate-800">{g.carver}{g.own ? " (stenens ristare)" : ""}</span>
                    <span className="text-xs text-slate-600 tabular-nums">
                      {`formlikhet ${fmt(g.mean)} i medel, ${g.crops.length} utsnitt på ${g.stones} ${g.stones === 1 ? "sten" : "stenar"}`}
                    </span>
                  </div>
                  {g.carver === "Samma sten" && g.mean < 0.5 && (
                    <p className="mt-1 text-xs text-amber-700">Runan liknar inte sina syskon på samma sten. Kontrollera att utsnitten är vridna lika.</p>
                  )}
                  <div className="mt-2 flex gap-2 overflow-x-auto">
                    {g.crops.slice(0, 8).map(c => (
                      <div key={c.crop.id} className="flex-shrink-0 w-16 text-center" title={`${c.signum}: formlikhet ${fmt(c.likeness)}`}>
                        <div className="w-16 h-16 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-center overflow-hidden">
                          <img src={c.crop.imageBase64} alt={c.crop.tag} className="max-w-full max-h-full object-contain" />
                        </div>
                        <div className="text-[10px] text-slate-500 truncate">{c.signum}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <p className="text-[11px] text-slate-500">
        Formlikheten jämför normaliserade svartvita runformer (kantriktningar, täthet och proportioner). På syntetiska
        testrunor hittas samma runa i 85 % av fallen. På verkliga stenar påverkar skador, vittring och hur utsnittet är
        gjort. Den är ett underlag för jämförelse, inte ett bevis för samma ristare.
      </p>
    </div>
  );
}

type PaleographicCropLike = CropWithStone["crop"];
