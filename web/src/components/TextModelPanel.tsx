"use client";

// The probability model on the inscription page: its reading word by word, the lost runes it fills in (recomputed with
// what is visible of them), the dating from the language and draft translations. See src/textmodel.py and
// METHODS.md 8.1 for the model and the tests behind the numbers shown.
import { useState } from "react";
import Link from "next/link";
import { TRACE_RUNES, textmodel, type TextModelBoundary, type TextModelGap, type TextModelReading } from "@/lib/textmodel";

const pct = (p: number) => `${Math.round(p * 100)} %`;
const tone = (p: number) =>
  p >= 0.9 ? "bg-emerald-50 border-emerald-300" : p >= 0.5 ? "bg-amber-50 border-amber-300" : "bg-slate-50 border-slate-300";

function Bar({ p }: { p: number }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
      <div className="h-full bg-[#b7410e]" style={{ width: `${Math.max(2, p * 100)}%` }} />
    </div>
  );
}

// The carved group with the gap marked, the filled runes shown in place of the question marks
function Carved({ gap }: { gap: TextModelGap }) {
  const g = gap.carved;
  return (
    <span className="font-mono" translate="no">
      {g.slice(0, gap.start)}
      <span className="bg-[#b7410e]/10 text-[#b7410e] font-bold px-0.5 rounded">{g.slice(gap.start, gap.end)}</span>
      {g.slice(gap.end)}
    </span>
  );
}

// The gap read again with the editors' word boundaries, where the model divided the words differently and the best
// word changes (U Fv1971;212B: Víseti across the name Ragnví, Siggi with Rundata's alternative division)
function Boundary({ xs }: { xs: TextModelBoundary[] }) {
  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50/80 p-3 space-y-3">
      <div className="space-y-1">
        <div className="text-xs font-semibold text-amber-900">Ordgränsen avgör förslaget</div>
        <p className="text-[11px] text-slate-600">
          Runorna står utan skiljetecken här, och modellen väljer själv var orden börjar. Med utgivarnas indelning blir
          det ett annat ord.
        </p>
        <div className="grid grid-cols-[auto_1fr] gap-x-3 text-xs">
          <span className="text-slate-500">Modellens indelning</span>
          <span className="font-mono" translate="no">{xs[0].model_runes}</span>
        </div>
      </div>
      <div className={`grid grid-cols-1 ${xs.length > 1 ? "md:grid-cols-2" : ""} gap-4`}>
        {xs.map(x => (
          <div key={x.variant} className="space-y-1.5">
            <div className="grid grid-cols-[auto_1fr] gap-x-3 text-xs">
              <span className="text-slate-500">{x.variant === "main" ? "Rundatas läsning" : "Rundatas alternativa läsning"}</span>
              <span className="font-mono" translate="no">{x.editor_runes}</span>
            </div>
            {x.words.slice(0, 3).map(w => (
              <div key={w.word} className="grid grid-cols-[1fr_auto] gap-2 items-center text-sm" translate="no">
                <span className={w.word === "<unk>" ? "text-slate-400" : ""}>{w.word === "<unk>" ? "ett okänt ord" : w.word}</span>
                <span className="text-xs text-slate-600 tabular-nums">{pct(w.p)}</span>
                <div className="col-span-2"><Bar p={w.p} /></div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function TracePicker({ n, value, onChange }: { n: number; value: string[]; onChange: (v: string[]) => void }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="flex flex-wrap items-center gap-1">
          <span className="text-[11px] text-slate-500 w-20">Runa {i + 1}:</span>
          {TRACE_RUNES.map(([glyph, letter]) => {
            const on = (value[i] || "").includes(letter);
            return (
              <button key={letter} type="button" title={letter}
                onClick={() => {
                  const cur = value[i] || "";
                  const next = [...value];
                  next[i] = on ? cur.replace(letter, "") : cur + letter;
                  onChange(next);
                }}
                className={`w-8 h-8 rounded-lg border text-base leading-none ${on ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-300 hover:border-slate-900"}`}>
                {glyph}
              </button>
            );
          })}
          <span className="text-[11px] text-slate-500 ml-1">{value[i] ? `möjliga: ${value[i]}` : "inget synligt"}</span>
        </div>
      ))}
    </div>
  );
}

export default function TextModelPanel({ signum }: { signum: string }) {
  const [data, setData] = useState<TextModelReading | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [traces, setTraces] = useState<Record<number, string[]>>({});
  const [open, setOpen] = useState<number | null>(null);
  const [withTraces, setWithTraces] = useState(false);

  const load = async () => {
    setBusy(true); setError(null);
    try {
      setData(await textmodel.read(signum));
      setWithTraces(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Modellen kunde inte läsa inskriften.");
    } finally {
      setBusy(false);
    }
  };

  const recompute = async () => {
    const allowed = Object.fromEntries(Object.entries(traces).filter(([, v]) => v.some(Boolean)));
    if (Object.keys(allowed).length === 0) return load();
    setBusy(true); setError(null);
    try {
      setData(await textmodel.withTraces(signum, allowed));
      setWithTraces(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Modellen kunde inte räkna om.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="liquid-glass-island rounded-[32px] p-8 space-y-6">
      <div>
        <h3 className="text-xl font-bold text-slate-900">Läsning och luckor</h3>
        <p className="text-xs text-slate-500 font-medium mt-1">
          Sannolikhetsmodellen läser de huggna runorna utan att se Rundatas tolkning av just den här stenen, fyller i
          förlorade runor och daterar texten ur språket. Den bedömer språket, inte stenen: det som syns på stenen eller
          i en skanning väger tyngre.
        </p>
      </div>

      {!data && (
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={load} disabled={busy}
            className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-black disabled:opacity-50">
            {busy ? "Modellen läser … (första gången upp till en minut)" : "Läs med sannolikhetsmodellen"}
          </button>
          {error && <span className="text-sm text-red-700">{error}</span>}
        </div>
      )}

      {data && !data.available && <p className="text-sm text-slate-600 bg-white/60 rounded-xl p-3">{data.reason}</p>}

      {data?.available && data.reading && (
        <>
          <section className="space-y-2">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Modellens läsning {withTraces && <span className="normal-case text-[#b7410e]">· med de spår du angett</span>}
            </div>
            <div className="flex flex-wrap gap-1.5" translate="no">
              {data.reading.map((w, i) => (
                <span key={i} className="flex items-center gap-1.5">
                  <span title={w.unknown ? "Ett ord modellen inte känner" : `${pct(w.p)} sannolikt`}
                    className={`inline-flex flex-col items-center rounded-lg border px-2 py-1 ${tone(w.p)} ${w.filled ? "border-dashed" : ""}`}>
                    <span className="font-mono text-[11px] text-slate-500">{w.runes}</span>
                    <span className={`text-sm ${w.name ? "font-semibold" : ""} ${w.unknown ? "text-slate-400" : "text-slate-900"}`}>
                      {w.unknown ? "?" : w.name ? w.word.charAt(0).toUpperCase() + w.word.slice(1) : w.word}
                    </span>
                    <span className="text-[10px] text-slate-500">{w.unknown ? "okänt" : pct(w.p)}</span>
                  </span>
                  {w.break_after && i < data.reading!.length - 1 && <span className="text-slate-400 text-xs" title="Förlorad text eller ett tecken som inte läses">…</span>}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-slate-500">
              Streckad ram: ordet innehåller ifyllda runor, och procenten är hur sannolikt ordet är i luckan. För de
              bevarade orden är procenten modellens egen och brukar vara något för hög; luckornas sannolikheter är prövade.
            </p>
          </section>

          {data.gaps && data.gaps.length > 0 && (
            <section className="space-y-3">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Förlorade runor</div>
              {data.gaps.map(g => (
                <div key={g.number} className="rounded-2xl border border-slate-200 bg-white/70 p-4 space-y-3">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <div className="text-sm">
                      <Carved gap={g} /> <span className="text-slate-500">· {g.n} {g.n === 1 ? "förlorad runa" : "förlorade runor"}</span>
                      {g.best && <> → <span className="font-mono font-bold" translate="no">{g.best}</span></>}
                    </div>
                    <button onClick={() => setOpen(open === g.number ? null : g.number)}
                      className="text-xs font-semibold text-[#b7410e] hover:underline">
                      {open === g.number ? "Dölj spåren" : "Ange vad som syns"}
                    </button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <div className="text-[11px] text-slate-500">Ordet i luckan</div>
                      {g.words.slice(0, 5).map(w => (
                        <div key={w.word} className="grid grid-cols-[1fr_auto] gap-2 items-center text-sm" translate="no">
                          <span className={w.word === "<unk>" ? "text-slate-400" : ""}>{w.word === "<unk>" ? "ett okänt ord" : w.word}</span>
                          <span className="text-xs text-slate-600 tabular-nums">{pct(w.p)}</span>
                          <div className="col-span-2"><Bar p={w.p} /></div>
                        </div>
                      ))}
                    </div>
                    <div className="space-y-1">
                      <div className="text-[11px] text-slate-500">Runorna som fyller luckan</div>
                      <div className="flex flex-wrap gap-1.5" translate="no">
                        {g.fills.slice(0, 8).map(f => (
                          <span key={f.fill} className="text-xs bg-white border border-slate-200 rounded-lg px-2 py-0.5">
                            <span className="font-mono font-bold">{f.fill}</span>
                            {f.word && f.word !== "<unk>" && <span className="text-slate-500"> ({f.word})</span>} {pct(f.p)}
                          </span>
                        ))}
                      </div>
                      {g.traces && <p className="text-[11px] text-[#b7410e]">Räknat med spåren: {g.traces.map(t => t || "–").join(" · ")}</p>}
                    </div>
                  </div>
                  {(data.boundaries || []).some(x => x.gap === g.number) &&
                    <Boundary xs={data.boundaries!.filter(x => x.gap === g.number)} />}
                  {open === g.number && (
                    <div className="space-y-3 border-t border-slate-200 pt-3">
                      <p className="text-xs text-slate-600">
                        Markera för varje förlorad runa vilka runor spåret kan vara – en stav, en bistav, en halv runa i
                        skanningen eller på fotot. Lämna tomt där inget syns. Modellen väljer sedan bara bland dem.
                      </p>
                      <TracePicker n={g.n} value={traces[g.number] || Array(g.n).fill("")}
                        onChange={v => setTraces({ ...traces, [g.number]: v })} />
                    </div>
                  )}
                </div>
              ))}
              {Object.values(traces).some(v => v.some(Boolean)) && (
                <div className="flex flex-wrap items-center gap-3">
                  <button onClick={recompute} disabled={busy}
                    className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-black disabled:opacity-50">
                    {busy ? "Räknar om …" : "Räkna om med spåren"}
                  </button>
                  <button onClick={() => { setTraces({}); load(); }} disabled={busy}
                    className="px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-semibold hover:border-slate-900">
                    Utan spår
                  </button>
                  {error && <span className="text-sm text-red-700">{error}</span>}
                </div>
              )}
            </section>
          )}
          {data.open_gaps && data.open_gaps.length > 0 && (
            <p className="text-xs text-slate-500">
              {data.open_gaps.length} längre {data.open_gaps.length === 1 ? "lucka" : "luckor"} (fler än fyra förlorade runor)
              lämnas öppna: där har modellen inte prövats.
            </p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.dating && (
              <section className="space-y-2">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Datering ur språket</div>
                {data.dating.epochs.map(e => (
                  <div key={e.epoch} className="grid grid-cols-[6.5rem_1fr_3rem] gap-2 items-center text-sm">
                    <span>{e.label}</span><Bar p={e.p} /><span className="text-xs tabular-nums text-slate-600 text-right">{pct(e.p)}</span>
                  </div>
                ))}
                <p className="text-[11px] text-slate-500">
                  {data.dating.calibrated ? "Kalibrerad på daterade stenar. " : ""}
                  Rätt epok i {pct(data.validation.dating_epoch)} av provet, högst en epok fel i {pct(data.validation.dating_near)}.
                  {data.dating.rundata && <> Rundata: {data.dating.rundata}.</>}
                </p>
              </section>
            )}
            {data.translation && (
              <section className="space-y-2">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Översättningsutkast</div>
                <p className="text-sm text-slate-900" translate="no">{data.translation.sv}</p>
                <p className="text-xs text-slate-500" translate="no">{data.translation.en}</p>
                <p className="text-[11px] text-slate-500">
                  Ord för ord ur modellens läsning, via de danska och engelska översättningarna i Danske Runeindskrifter och
                  Rundata. Ett utkast, inte en tolkning.
                </p>
              </section>
            )}
          </div>

          <section className="rounded-2xl bg-white/60 p-4 text-xs text-slate-600 space-y-1">
            <div className="font-semibold text-slate-800">Hur säker är modellen?</div>
            <p>
              Prövad på stenar där svaret är känt men dolts: saknas några runor inne i ett ord ger den rätt ord i{" "}
              {pct(data.validation.inside_word)} av fallen, saknas ett helt ord i {pct(data.validation.whole_word)}. När
              den säger sig vara minst 95 % säker har den rätt i {pct(data.validation.sure_right)}, och på verkliga skador
              kommer den då fram till samma ord som Rundatas utgivare i {pct(data.validation.rundata_sure)}. I ett simulerat
              prov där halva runan syns steg rätt ord för ett helt ord till {pct(data.validation.with_traces)}
              {data.validation.with_misread_traces != null && <>, och till {pct(data.validation.with_misread_traces)} även när vart
              femte spår var felläst – spåren räknas som troliga, inte säkra</>}.
              {data.calibrated && <> Procenten vid orden är kalibrerade: ett ord med 80 % stämmer ungefär åtta gånger av tio
              (prövat på 808 stenar med känt svar). Namn får ofta låga procent, eftersom ett namn sällan kan säkras ur språket.</>}{" "}
              Procenten är prövade på luckor som utgivarna redan har fyllt. Luckor som står öppna är ofta just de där
              ingen vanlig formel passar, och där kan modellen vara säker och ändå ha fel: den kan inte kasusböjning
              och väljer själv var orden börjar.{" "}
              <Link href="/docs/metod" className="text-[#b7410e] hover:underline">Metoden</Link>
            </p>
          </section>
        </>
      )}
    </div>
  );
}
