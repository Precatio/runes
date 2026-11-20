"use client";

// The overview of one gap: every word the probability model tries there, not only its five best – with the
// probability in the context, how often the word is written in the corpus, which preserved runes around the gap it
// fits and where the candidate came from. The number of lost runes can be changed when Rundata is unsure of it.
// An admin can save a candidate as Vitki's proposal or confirmed filling (src/vitki_fills.py). See
// src/textmodel_overview.py and METHODS.md 8.1.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/AuthContext";
import {
  EVIDENCE_LABEL, textmodel, type CandidateOrigin, type EvidenceKind, type FillMethod, type GapOverview as Overview,
  type GapWord,
} from "@/lib/textmodel";

const ORIGIN: Record<CandidateOrigin, string> = {
  vocabulary: "ordförrådet", names: "sammansatt namn", nearby: "namn på en närliggande sten", carver: "ristarens stenar",
  stone: "samma sten", variant: "stavningsvariant", runes: "runa för runa",
};

// 100 % only for certainty; small shares with one decimal, the smallest as "under 0,1 %"
export const pctFine = (p: number) =>
  p >= 1 ? "100 %" : p >= 0.01 ? `${Math.min(99, Math.round(p * 100))} %`
    : p >= 0.001 ? `${(p * 100).toFixed(1).replace(".", ",")} %` : "under 0,1 %";

type SortKey = "p" | "p_model" | "word" | "stones" | "origin";

function Fit({ left, fill, right }: { left: string; fill: string; right: string }) {
  return (
    <span className="font-mono" translate="no">
      {left}<span className="bg-[#b7410e]/10 text-[#b7410e] font-bold px-0.5 rounded">{fill}</span>{right}
    </span>
  );
}

function SaveForm({ signum, data, word, onSaved }: { signum: string; data: Overview; word: GapWord; onSaved: () => void }) {
  const { authHeaders } = useAuth();
  const [fill, setFill] = useState(word.fills[0]?.fill ?? "");
  const [status, setStatus] = useState<"förslag" | "bekräftad">("förslag");
  const [method, setMethod] = useState<FillMethod>("sannolikhetsmodellen");
  const [comment, setComment] = useState("");
  const [evidence, setEvidence] = useState<{ kind: EvidenceKind; ref: string }[]>([{ kind: "sri", ref: "" }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const save = async () => {
    setBusy(true); setError(null);
    try {
      await textmodel.saveFill(await authHeaders(), {
        signum, gap: data.gap!.number, kind: data.gap!.kind, n: data.gap!.n, fill, method, status, comment,
        evidence: evidence.filter(e => e.ref.trim()),
      });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ifyllningen kunde inte sparas.");
    } finally {
      setBusy(false);
    }
  };
  const field = "rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs";
  return (
    <div className="rounded-xl border border-slate-300 bg-white/80 p-3 space-y-2 text-xs">
      <div className="font-semibold text-slate-800">
        Spara <span translate="no">{word.word}</span> som Vitkis ifyllning
      </div>
      <p className="text-[11px] text-slate-500">
        Sparas i Vitkis eget lager ovanpå Rundata (data/vitki_ifyllningar.json, CC BY 4.0). Rundata ändras inte, och
        sannolikhetsmodellen tränas och prövas aldrig på ifyllningarna. Sannolikheten och modellversionen hämtas av servern.
      </p>
      <div className="flex flex-wrap gap-2 items-center">
        <label>Runor{" "}
          <select value={fill} onChange={e => setFill(e.target.value)} className={field} translate="no">
            {word.fills.map(f => <option key={f.fill} value={f.fill}>{f.fill}</option>)}
          </select>
        </label>
        <label>Status{" "}
          <select value={status} onChange={e => setStatus(e.target.value as "förslag" | "bekräftad")} className={field}>
            <option value="förslag">förslag</option><option value="bekräftad">bekräftad</option>
          </select>
        </label>
        <label>Metod{" "}
          <select value={method} onChange={e => setMethod(e.target.value as FillMethod)} className={field}>
            <option value="sannolikhetsmodellen">sannolikhetsmodellen</option>
            <option value="spår ur skanningen">spår ur skanningen</option>
            <option value="utgivarens läsning">utgivarens läsning</option>
          </select>
        </label>
      </div>
      <label className="block">Kommentar (krävs)
        <textarea value={comment} onChange={e => setComment(e.target.value)} rows={2} className={`${field} w-full mt-1`} />
      </label>
      <div className="space-y-1">
        <div>Belägg</div>
        {evidence.map((ev, i) => (
          <div key={i} className="flex flex-wrap gap-2">
            <select value={ev.kind} className={field}
              onChange={e => setEvidence(evidence.map((x, j) => (j === i ? { ...x, kind: e.target.value as EvidenceKind } : x)))}>
              {(Object.keys(EVIDENCE_LABEL) as EvidenceKind[]).map(k => <option key={k} value={k}>{EVIDENCE_LABEL[k]}</option>)}
            </select>
            <input value={ev.ref} placeholder="sida, fil eller länk" className={`${field} flex-1 min-w-[10rem]`}
              onChange={e => setEvidence(evidence.map((x, j) => (j === i ? { ...x, ref: e.target.value } : x)))} />
          </div>
        ))}
        <button type="button" onClick={() => setEvidence([...evidence, { kind: "skanning", ref: "" }])}
          className="text-[#b7410e] font-semibold hover:underline">Lägg till belägg</button>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <button onClick={save} disabled={busy || !comment.trim() || !fill}
          className="px-3 py-1.5 rounded-lg bg-slate-900 text-white font-semibold disabled:opacity-40">
          {busy ? "Sparar …" : status === "bekräftad" ? "Spara som bekräftad" : "Spara som förslag"}
        </button>
        {error && <span className="text-red-700">{error}</span>}
      </div>
    </div>
  );
}

export default function GapOverview({ signum, gap, kind = "gap", initialN, onClose, onSaved }: {
  signum: string; gap: number; kind?: "gap" | "open"; initialN?: number; onClose?: () => void; onSaved?: () => void;
}) {
  const { isAdmin } = useAuth();
  const [n, setN] = useState<number | undefined>(initialN);
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "p", dir: -1 });
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  // the latest answer and the question it answers: while a new length is computed the old list stays in view
  const ask = `${signum}|${gap}|${n ?? ""}|${kind}`;
  const [res, setRes] = useState<{ ask: string; data?: Overview; error?: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    textmodel.candidates(signum, gap, n, kind)
      .then(d => { if (!cancelled) setRes({ ask, data: d }); })
      .catch(e => { if (!cancelled) setRes(r => ({ ask, data: r?.data, error: e instanceof Error ? e.message : "Kandidaterna kunde inte hämtas." })); });
    return () => { cancelled = true; };
  }, [ask, signum, gap, n, kind]);
  const busy = res?.ask !== ask;
  const data = res?.data ?? null;
  const error = !busy ? res?.error ?? null : null;

  const words = useMemo(() => {
    const ws = [...(data?.words ?? [])];
    const val = (w: GapWord): number | string => {
      switch (sort.key) {
        case "p": return w.p ?? (w.p_model - 1); // the calibrated words first, the rest by the model's share
        case "p_model": return w.p_model;
        case "word": return w.unknown ? "￿" : (w.word ?? "");
        case "stones": return w.corpus?.stones ?? -1;
        case "origin": return w.origins.map(o => ORIGIN[o]).join(", ");
      }
    };
    ws.sort((a, b) => {
      const x = val(a), y = val(b);
      const c = typeof x === "string" ? x.localeCompare(String(y), "sv") : (x as number) - (y as number);
      return c * sort.dir || b.p_model - a.p_model;
    });
    return ws;
  }, [data, sort]);

  const g = data?.gap;
  const top3 = (data?.words ?? []).filter(w => !w.unknown).slice(0, 3);
  const list = (xs: string[]) => (xs.length <= 1 ? xs.join("") : `${xs.slice(0, -1).join(", ")} och ${xs[xs.length - 1]}`);
  const head = (key: SortKey, label: string, cls = "") => (
    <th className={`p-2 text-left ${cls}`} aria-sort={sort.key === key ? (sort.dir === 1 ? "ascending" : "descending") : "none"}>
      <button type="button" className="font-semibold hover:text-[#b7410e]"
        onClick={() => setSort(s => ({ key, dir: s.key === key ? ((-s.dir) as 1 | -1) : key === "word" || key === "origin" ? 1 : -1 }))}>
        {label}{sort.key === key ? (sort.dir === 1 ? " ↑" : " ↓") : ""}
      </button>
    </th>
  );

  return (
    <div className="rounded-2xl border border-[#b7410e]/40 bg-white/80 p-4 space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="text-sm font-semibold text-slate-900">
          Alla ord som passar luckan
          {g && <> · <span className="font-mono" translate="no">{g.carved.slice(0, g.start)}<span className="text-[#b7410e]">{"?".repeat(g.n)}</span>{g.carved.slice(g.end)}</span></>}
        </div>
        {onClose && <button onClick={onClose} className="text-xs font-semibold text-slate-600 hover:underline">Stäng överblicken</button>}
      </div>

      {g && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-600">
            Rundata anger <strong>{g.rundata_n}</strong> {g.rundata_n === 1 ? "förlorad runa" : "förlorade runor"}; valt: <strong>{g.n}</strong>.
          </span>
          {g.adjustable ? (
            <span className="flex flex-wrap gap-1" role="group" aria-label="Antal förlorade runor">
              {Array.from({ length: g.max_n - g.min_n + 1 }, (_, i) => g.min_n + i).map(k => (
                <button key={k} type="button" disabled={busy} onClick={() => setN(k === g.rundata_n ? undefined : k)}
                  aria-pressed={k === g.n}
                  className={`w-7 h-7 rounded-lg border font-semibold ${k === g.n ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-300 hover:border-slate-900"} ${k === g.rundata_n ? "ring-2 ring-[#b7410e]/40" : ""}`}
                  title={k === g.rundata_n ? "Rundatas antal" : undefined}>
                  {k}
                </button>
              ))}
            </span>
          ) : (
            <span className="text-slate-500">Luckan har bevarade runor inne i sig, så antalet kan inte ändras.</span>
          )}
        </div>
      )}
      {g && !g.tested && (
        <p className="text-xs text-amber-800 bg-amber-50 rounded-lg p-2">
          Modellen är prövad på luckor om en till fyra runor. Med {g.n} förlorade runor är sannolikheterna inte prövade och
          bör läsas som en rangordning, inte som procent att lita på.
        </p>
      )}

      {busy && <p className="text-xs text-slate-500">Modellen prövar kandidaterna … (första gången några sekunder)</p>}
      {error && <p className="text-xs text-red-700">{error}</p>}
      {data && !data.available && <p className="text-xs text-slate-600">{data.reason}</p>}

      {data?.available && data.words && (
        <>
          <p className="text-sm text-slate-800">
            Modellen prövade {data.n_words} ord ({data.n_tried} sätt att fylla luckan) som passar de bevarade runorna
            {top3.length > 0 && <>; de tre troligaste är <span translate="no">{list(top3.map(w => `${w.word} (${w.p != null ? pctFine(w.p) : "okalibrerat"})`))}</span></>}.
            Sannolikheten är modellens bedömning i sammanhanget, prövad på kända texter (se{" "}
            <Link href="/docs/metod" className="text-[#b7410e] hover:underline">valideringen</Link>).
          </p>
          {data.top_unsure && (
            <p className="text-xs text-amber-900 bg-amber-50 border border-amber-300 rounded-lg p-2">
              Osäkert: inget ord når 45 %. I blindtestet bar fyra av fem felaktiga förslag den här varningen; läs listan
              som möjligheter att pröva mot sten, skanning och utgåvor.
            </p>
          )}
          <div className="max-h-[28rem] overflow-auto rounded-xl border border-slate-200">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-50 text-slate-600">
                <tr>
                  {head("word", "Ord")}
                  {head("p", "Sannolikhet", "min-w-[9rem]")}
                  {head("p_model", "Modellens andel")}
                  <th className="p-2 text-left">Runor i luckan</th>
                  {head("stones", "Belägg i korpusen")}
                  {head("origin", "Kandidaten kom från")}
                  {isAdmin && <th className="p-2" />}
                </tr>
              </thead>
              <tbody>
                {words.map((w, i) => {
                  const k = w.unknown ? `unk-${i}` : (w.word ?? `w-${i}`);
                  const f0 = w.fills[0];
                  return (
                    <tr key={k} className="border-t border-slate-100 align-top">
                      <td className="p-2" translate="no">
                        <span className={w.unknown ? "text-slate-400" : w.name ? "font-semibold" : ""}>
                          {w.unknown ? "ett okänt ord" : w.word}
                        </span>
                        {w.class && <span className="block text-[10px] text-slate-500">{w.class}</span>}
                      </td>
                      <td className="p-2">
                        {w.p != null ? (
                          <>
                            <span className="tabular-nums">{pctFine(w.p)}</span>
                            <div className="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden mt-1">
                              <div className="h-full bg-[#b7410e]" style={{ width: `${Math.max(2, w.p * 100)}%` }} />
                            </div>
                          </>
                        ) : (
                          <>
                            <span className="text-slate-400">ej kalibrerad</span>
                            <div className="h-1 w-full rounded-full bg-slate-100 overflow-hidden mt-1">
                              <div className="h-full bg-slate-400" style={{ width: `${Math.max(1, w.p_model * 100)}%` }} />
                            </div>
                          </>
                        )}
                      </td>
                      <td className="p-2 tabular-nums text-slate-600">{pctFine(w.p_model)}</td>
                      <td className="p-2">
                        {f0 && (f0.left || f0.right ? <Fit left={f0.left} fill={f0.fill} right={f0.right} />
                          : <><Fit left="" fill={f0.fill} right="" /> <span className="text-slate-500">hela ordet i luckan</span></>)}
                        {w.n_fills > 1 && <span className="block text-[10px] text-slate-500" translate="no">
                          {w.n_fills} stavningar: {w.fills.slice(0, 6).map(f => f.fill).join(", ")}{w.n_fills > 6 ? " …" : ""}
                        </span>}
                      </td>
                      <td className="p-2 text-slate-700">
                        {w.corpus ? (
                          w.corpus.stones > 0 ? (
                            <>
                              {w.corpus.count} gånger på {w.corpus.stones} {w.corpus.stones === 1 ? "runsten" : "runstenar"}
                              <span className="block text-[10px] text-slate-500" translate="no">t.ex. {w.corpus.examples.join(", ")}</span>
                            </>
                          ) : <span className="text-slate-500">inte på någon annan runsten</span>
                        ) : <span className="text-slate-400">–</span>}
                        {w.corpus && w.corpus.other_stones > 0 && (
                          <span className="block text-[10px] text-slate-500">och på {w.corpus.other_stones} andra föremål</span>
                        )}
                      </td>
                      <td className="p-2 text-slate-600">{w.origins.map(o => ORIGIN[o]).join(", ")}</td>
                      {isAdmin && (
                        <td className="p-2">
                          {!w.unknown && (
                            <button type="button" onClick={() => setSaving(saving === k ? null : k)}
                              className="text-[#b7410e] font-semibold hover:underline whitespace-nowrap">
                              {saving === k ? "Avbryt" : "Spara …"}
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {saving && (() => {
            const w = words.find((x, i) => (x.unknown ? `unk-${i}` : (x.word ?? `w-${i}`)) === saving);
            return w ? <SaveForm signum={signum} data={data} word={w}
              onSaved={() => { setSaving(null); setSaved(w.word); onSaved?.(); }} /> : null;
          })()}
          {saved && <p className="text-xs text-emerald-800">Sparat: <span translate="no">{saved}</span>. Det visas nu på stensidan.</p>}
          <div className="text-[11px] text-slate-500 space-y-1">
            <p>
              <strong>Sannolikhet</strong> är kalibrerad på samma sätt som appens förslag och ges åt de {data.kmax} troligaste
              orden.{data.unassigned != null && <> Övriga ord, och möjligheten att inget av de prövade orden är rätt, delar på {pctFine(data.unassigned)}.</>}{" "}
              <strong>Modellens andel</strong> är hur mycket bättre ordet passar runorna och sammanhanget än de andra
              kandidaterna, före kalibreringen; den blir lätt hög för namn och ovanliga ord.{" "}
              <strong>Belägg i korpusen</strong> räknar ordet i alla dess former på de vikingatida runstenarna, utom den här stenen.
            </p>
            {data.context && data.context.length > 0 && (
              <p>
                De andra luckorna i inskriften är fyllda med läsningens val medan den här prövas:{" "}
                <span translate="no">{data.context.map(c => c.fill).join(", ")}</span>. Spår du angett i panelen räknas inte här.
              </p>
            )}
            {data.truncated && <p>Listan visar de {data.limit} första av {data.n_tried} prövade fyllningarna.</p>}
          </div>
        </>
      )}
    </div>
  );
}
