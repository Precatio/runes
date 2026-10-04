"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { corpus } from "@/lib/corpus";
import { useAuth } from "@/components/AuthContext";

interface ProvinceRow {
  code: string; name: string; axelson: boolean; total: number; carver: number; style: number; dated: number;
  uncertain_interpretation: number; lost: number; measured: number;
}
interface Hypothesis {
  signum: string; place: string; province: string; style: string | null; carver: string; similarity: number;
  margin: number; runner_up: string; n_words: number; in_carver_area: boolean; carver_area: string[];
  carver_precision: number | null; short_text: boolean; attributed_to?: string[];
}
interface Priority {
  carver: string; inscriptions: number; signed: number; measured: number; measured_signa: string[];
  missing_to_target: number; suggestions: { signum: string; place: string; signed: boolean }[];
}
interface Brief { signum: string; place: string; province: string; style: string | null; dating: string; carvers: string[] }
interface Gaps {
  coverage: { scope: string; totals: Record<string, number>; per_province: ProvinceRow[] };
  hypotheses: { new: Hypothesis[]; reconsider: Hypothesis[]; evaluation: { top1_accuracy: number; signed_only: { top1_accuracy: number | null }; n_carvers: number; chance_top1: number } };
  open_questions: { uninterpreted: { count: number; items: Brief[] }; uncertain_style: { count: number; items: Brief[] } };
  measurement_priorities: Priority[];
  source_note: string;
  attribution: string;
}

type Tab = "hypotheses" | "reconsider" | "priorities" | "uninterpreted" | "style";

const pct = (n: number, d: number) => (d ? Math.round((100 * n) / d) : 0);
const fmt = (v: number | null | undefined, digits = 2) => (v == null ? "–" : v.toFixed(digits).replace(".", ","));

function Bar({ value, total, color }: { value: number; total: number; color: string }) {
  return (
    <div className="flex items-center gap-2 min-w-[110px]">
      <div className="h-2 flex-1 bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct(value, total)}%`, background: color }} />
      </div>
      <span className="text-[11px] font-mono text-slate-600 w-9 text-right">{pct(value, total)} %</span>
    </div>
  );
}

function StoneLinks({ signum }: { signum: string }) {
  return (
    <span className="whitespace-nowrap text-xs">
      <Link href={`/inskrifter?signum=${encodeURIComponent(signum)}`} className="font-bold text-slate-900 hover:text-[#b7410e]">{signum}</Link>
      <Link href={`/3d?signum=${encodeURIComponent(signum)}`} className="ml-2 text-[#b7410e] hover:underline">mät i 3D</Link>
    </span>
  );
}

export default function GapsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<Gaps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("hypotheses");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      let measured: string[] = [];
      if (user) {
        try { measured = [...new Set((await corpus.list()).map(e => e.signum))]; } catch { /* corpus optional */ }
      }
      try {
        const res = await fetch(`${API_URL}/api/research/gaps`, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ measured_signa: measured }),
        });
        if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
        const body = await res.json();
        if (!cancelled) setData(body);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Kunde inte hämta översikten.");
      }
    })();
    return () => { cancelled = true; };
  }, [user]);

  if (error) return <div className="max-w-3xl mx-auto p-8 text-red-700 font-semibold">{error}</div>;
  if (!data) return <div className="max-w-3xl mx-auto p-8 text-slate-500">Beräknar översikten …</div>;

  const t = data.coverage.totals;
  const ev = data.hypotheses.evaluation;
  const tabs: [Tab, string, number][] = [
    ["hypotheses", "Ortografiska hypoteser", data.hypotheses.new.length],
    ["reconsider", "Ompröva attribuering", data.hypotheses.reconsider.length],
    ["priorities", "Mätningar som gör mest nytta", data.measurement_priorities.length],
    ["uninterpreted", "Osäkert tolkade", data.open_questions.uninterpreted.count],
    ["style", "Osäker stilgrupp", data.open_questions.uncertain_style.count],
  ];

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Forskningsluckor</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Var saknas uppgifter om de svenska vikingatida runstenarna, och var kan nya mätningar och analyser göra skillnad?
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          ["Runstenar", `${t.total}`, ""],
          ["Med ristare", `${pct(t.carver, t.total)} %`, `${t.total - t.carver} saknar`],
          ["Med säker stilgrupp", `${pct(t.style, t.total)} %`, `${t.total - t.style} saknar`],
          ["Daterade med årtal", `${t.dated}`, `${pct(t.dated, t.total)} %`],
          ["Uppmätta i korpusen", `${t.measured}`, user ? "" : "logga in för att se"],
        ].map(([label, value, sub]) => (
          <div key={label} className="liquid-glass-island rounded-[24px] p-5">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
            <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
            {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
          </div>
        ))}
      </div>

      <div className="rounded-2xl bg-amber-50 border border-amber-200 px-5 py-3 text-sm text-amber-900">
        <strong>Läs med källkritik:</strong> {data.source_note}
      </div>

      <div className="liquid-glass-island rounded-[32px] p-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
              <th className="p-2">Landskap</th><th className="p-2">Runstenar</th><th className="p-2">Med ristare</th>
              <th className="p-2">Säker stilgrupp</th><th className="p-2">Osäkert tolkade</th><th className="p-2">Försvunna</th><th className="p-2">Uppmätta</th>
            </tr>
          </thead>
          <tbody>
            {data.coverage.per_province.map(r => (
              <tr key={r.code} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold">
                  <Link href={`/inskrifter?province=${encodeURIComponent(r.code)}`} className="hover:text-[#b7410e]">{r.name}</Link>
                  {r.axelson && <span className="ml-2 text-[10px] font-bold text-slate-400" title="Ristaruppgifter främst ur Axelson 1993">AXELSON</span>}
                </td>
                <td className="p-2">{r.total}</td>
                <td className="p-2"><Bar value={r.carver} total={r.total} color="#b7410e" /></td>
                <td className="p-2"><Bar value={r.style} total={r.total} color="#0369a1" /></td>
                <td className="p-2">{r.uncertain_interpretation}</td>
                <td className="p-2">{r.lost}</td>
                <td className="p-2">{r.measured}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map(([key, label, n]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2 rounded-xl text-sm font-bold border ${tab === key ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
            {label} <span className="opacity-60">({n})</span>
          </button>
        ))}
      </div>

      <div className="liquid-glass-island rounded-[32px] p-5">
        {(tab === "hypotheses" || tab === "reconsider") && (
          <>
            <p className="text-sm text-slate-600 mb-4 max-w-4xl">
              {tab === "hypotheses"
                ? "Runstenar utan ristare i Rundata där stavning, skiljetecken och bindrunor tydligt liknar en känd ristares. Det är hypoteser att pröva – helst med uppmätt huggteknik – inte attribueringar."
                : "Attribuerade stenar där ortografin pekar mot en annan ristare än litteraturen. Kan bero på samarbete, verkstäder eller en osäker attribuering."}
              {" "}Modellens träffsäkerhet: rätt ristare först i {Math.round(ev.top1_accuracy * 100)} % ({ev.signed_only.top1_accuracy != null ? `${Math.round(ev.signed_only.top1_accuracy * 100)} % för signerade` : ""}) bland {ev.n_carvers} ristare.
              <em> Precision</em> anger hur ofta modellen har rätt när den föreslår just den ristaren.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="p-2">Sten</th><th className="p-2">Plats</th>
                    {tab === "reconsider" && <th className="p-2">Rundata</th>}
                    <th className="p-2">Ortografin pekar mot</th><th className="p-2">Likhet</th><th className="p-2">Precision</th>
                    <th className="p-2">Inom ristarens område</th><th className="p-2">Ord</th>
                  </tr>
                </thead>
                <tbody>
                  {(tab === "hypotheses" ? data.hypotheses.new : data.hypotheses.reconsider).map(h => (
                    <tr key={h.signum} className="border-t border-slate-900/5">
                      <td className="p-2"><StoneLinks signum={h.signum} /></td>
                      <td className="p-2 text-slate-600">{h.place}</td>
                      {tab === "reconsider" && <td className="p-2">{h.attributed_to?.join(", ")}</td>}
                      <td className="p-2 font-semibold">{h.carver} <span className="text-slate-400 font-normal">(sedan {h.runner_up})</span></td>
                      <td className="p-2 font-mono text-xs">{fmt(h.similarity)}</td>
                      <td className="p-2 font-mono text-xs">{h.carver_precision != null ? `${Math.round(h.carver_precision * 100)} %` : "–"}</td>
                      <td className="p-2 text-xs">{h.in_carver_area ? "Ja" : <span className="text-amber-700">Nej ({h.carver_area.join(", ")}) – kan vara regional stavning</span>}</td>
                      <td className="p-2 text-xs">{h.n_words}{h.short_text && <span className="text-amber-700"> kort</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {tab === "priorities" && (
          <>
            <p className="text-sm text-slate-600 mb-4 max-w-4xl">
              Attribuering mot mätkorpusen kräver minst två – helst fem – uppmätta stenar per ristare. Här är ristarna med
              många säkra inskrifter i Rundata men få uppmätta stenar, med förslag på stenar att skanna (signerade först).
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.measurement_priorities.slice(0, 20).map(p => (
                <div key={p.carver} className="bg-white/70 rounded-2xl p-4 border border-slate-200">
                  <div className="flex justify-between items-baseline">
                    <Link href={`/inskrifter?carver=${encodeURIComponent(p.carver)}`} className="font-bold text-slate-900 hover:text-[#b7410e]">{p.carver}</Link>
                    <span className="text-xs text-slate-500">{p.inscriptions} inskrifter ({p.signed} signerade)</span>
                  </div>
                  <div className="text-xs mt-1">
                    Uppmätta: <strong>{p.measured}</strong>{p.missing_to_target > 0 && <span className="text-amber-700"> – {p.missing_to_target} till behövs</span>}
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
                    {p.suggestions.slice(0, 6).map(s => (
                      <span key={s.signum} className="text-xs">
                        <StoneLinks signum={s.signum} />{s.signed && <span className="text-emerald-700"> (S)</span>}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {(tab === "uninterpreted" || tab === "style") && (() => {
          const block = tab === "uninterpreted" ? data.open_questions.uninterpreted : data.open_questions.uncertain_style;
          return (
            <>
              <p className="text-sm text-slate-600 mb-4 max-w-4xl">
                {tab === "uninterpreted"
                  ? "Bevarade runstenar vars normalisering saknas eller är markerad som osäker i Rundata, sorterade efter textens längd. RTI-visaren och ristningskartan från 3D kan hjälpa nyläsningar."
                  : "Bevarade runstenar där stilgruppen är osäker (?) i Rundata. En 2D-stilanalys av foto eller ristningskarta kan ge underlag – AI:ns bedömning är dock okalibrerad."}
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="text-left text-[11px] uppercase tracking-wider text-slate-500"><th className="p-2">Sten</th><th className="p-2">Plats</th><th className="p-2">Stil</th><th className="p-2">Datering</th><th className="p-2">Ristare</th></tr></thead>
                  <tbody>
                    {block.items.slice(0, 150).map(b => (
                      <tr key={b.signum} className="border-t border-slate-900/5">
                        <td className="p-2"><StoneLinks signum={b.signum} /></td>
                        <td className="p-2 text-slate-600">{b.place}</td>
                        <td className="p-2">{b.style ?? "–"}</td>
                        <td className="p-2">{b.dating || "–"}</td>
                        <td className="p-2">{b.carvers.join(", ") || "–"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          );
        })()}
      </div>
      <p className="text-[11px] text-slate-500">{data.attribution}</p>
    </div>
  );
}
