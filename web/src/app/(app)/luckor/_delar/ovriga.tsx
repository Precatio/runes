import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { SIMILARITY_HELP, fmtP } from "@/lib/significance";
import ExportTable from "@/components/ExportTable";
import type { Brief, Gaps, Hypothesis, Priority, TextGaps } from "./typer";
import { LanguageCell, MaterialCell, StoneLinks, TH_ROW, fmt, useSorted } from "./gemensamt";

export function HypothesisTable({ rows, reconsider, ev }: { rows: Hypothesis[]; reconsider: boolean; ev: Gaps["hypotheses"]["evaluation"] }) {
  const { sorted, header } = useSorted(rows, {
    signum: h => h.signum, place: h => h.place, attributed: h => h.attributed_to?.join(", "), carver: h => h.carver,
    similarity: h => h.similarity, margin: h => h.margin, precision: h => h.carver_precision, p: h => h.p_adjusted,
    area: h => h.in_carver_area, words: h => h.n_words, material: h => h.material,
    language: h => (h.language?.comparable ? h.language.agree / h.language.comparable : null),
  }, { key: "precision", desc: true });
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        {!reconsider
          ? "Runstenar utan ristare i Rundata där stavning, skiljetecken och bindrunor tydligt liknar en känd ristares. Det är hypoteser att pröva – helst med uppmätt huggteknik – inte attribueringar."
          : "Attribuerade stenar där ortografin pekar mot en annan ristare än litteraturen. Kan bero på samarbete, verkstäder eller en osäker attribuering."}
        {" "}Modellens träffsäkerhet: rätt ristare först i {Math.round(ev.top1_accuracy * 100)} % ({ev.signed_only.top1_accuracy != null ? `${Math.round(ev.signed_only.top1_accuracy * 100)} % för signerade` : ""}) bland {ev.n_carvers} ristare.
        <em> Precision</em> anger hur ofta modellen har rätt när den föreslår just den ristaren.
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead>
            <tr className={TH_ROW}>
              {header("signum", "Sten")}{header("place", "Plats")}
              {reconsider && header("attributed", "Rundata")}
              {header("carver", "Ortografin pekar mot")}{header("similarity", "Likhet", SIMILARITY_HELP)}{header("p", "p (just.)", SIMILARITY_HELP)}{header("margin", "Marginal")}
              {header("precision", "Precision")}{header("area", "Inom ristarens område")}{header("words", "Ord")}
              {header("material", "Bergart", "✓ = bergarten förekommer på ristarens stenar, ! = sällan")}
              {header("language", "Språkdrag", "Jämförbara språkdrag som stämmer med ristaren")}
            </tr>
          </thead>
          <tbody>
            {sorted.map(h => (
              <tr key={h.signum} className="border-t border-slate-900/5">
                <td className="p-2"><StoneLinks signum={h.signum} /></td>
                <td className="p-2 text-slate-600" translate="no">{h.place}</td>
                {reconsider && <td className="p-2">{h.attributed_to?.join(", ")}</td>}
                <td className="p-2 font-semibold">{h.carver} <span className="text-slate-400 font-normal">(sedan {h.runner_up})</span></td>
                <td className="p-2 font-mono text-xs">{fmt(h.similarity)}</td>
                <td className="p-2 font-mono text-xs">{fmtP(h.p_value)} <span className="text-slate-400">({fmtP(h.p_adjusted)})</span></td>
                <td className="p-2 font-mono text-xs">{fmt(h.margin)}</td>
                <td className="p-2 font-mono text-xs">{h.carver_precision != null ? `${Math.round(h.carver_precision * 100)} %` : "–"}</td>
                <td className="p-2 text-xs">{h.in_carver_area ? "Ja" : <span className="text-amber-700">Nej ({h.carver_area.join(", ")}) – kan vara regional stavning</span>}</td>
                <td className="p-2 text-xs">{h.n_words}{h.short_text && <span className="text-amber-700"> kort</span>}</td>
                <td className="p-2 text-xs"><MaterialCell x={h} /></td>
                <td className="p-2 text-xs"><LanguageCell x={h} /></td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
    </>
  );
}

export function PrioritiesPanel({ rows }: { rows: Priority[] }) {
  const [key, setKey] = useState<"inscriptions" | "signed" | "measured" | "missing">("inscriptions");
  const sorted = useMemo(() => [...rows].sort((a, b) => {
    if (key === "measured") return a.measured - b.measured || b.inscriptions - a.inscriptions;
    if (key === "missing") return b.missing_to_target - a.missing_to_target || b.inscriptions - a.inscriptions;
    return b[key] - a[key];
  }), [rows, key]);
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p className="text-sm text-slate-600 max-w-3xl">
          Attribuering mot mätkorpusen kräver minst två – helst fem – uppmätta stenar per ristare. Här är ristarna med
          många säkra inskrifter i Rundata men få uppmätta stenar, med förslag på stenar att skanna (signerade först).
        </p>
        <label className="text-sm text-slate-600">Sortera efter{" "}
          <select value={key} onChange={e => setKey(e.target.value as typeof key)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-sm font-semibold outline-none">
            <option value="inscriptions">Flest inskrifter</option>
            <option value="signed">Flest signerade</option>
            <option value="measured">Minst uppmätta</option>
            <option value="missing">Flest mätningar kvar</option>
          </select>
        </label>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sorted.slice(0, 30).map(p => (
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
  );
}

// When the figures on this page were computed, and on which data: the R corpus analyses, the text model and Rundata
export function Freshness({ textGaps }: { textGaps: TextGaps | null }) {
  const [r, setR] = useState<{ computed_at?: string | null; fingerprint?: string; n_stones?: number } | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/r/status`).then(x => (x.ok ? x.json() : null)).then(d => setR(d?.corpus ?? null)).catch(() => setR(null));
  }, []);
  const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : "–");
  return (
    <p className="text-[11px] text-slate-500 -mt-2 mb-4">
      Underlag: {textGaps?.rundata_version ?? "Samnordisk runtextdatabas 3.1 (2018)"} · statistiken i R beräknad {day(r?.computed_at)}
      {r?.n_stones ? ` på ${r.n_stones} stenar` : ""} · sannolikhetsmodellen {textGaps?.model_version ?? "–"}, luckorna inventerade {day(textGaps?.computed_at)}.
      Täckning, hypoteser och prioriteringar räknas vid varje anrop.
    </p>
  );
}

export function TextGapsPanel({ data }: { data: TextGaps | null }) {
  const [prov, setProv] = useState("");
  // Runestones only by default (the app's rule for every count); other objects on request, with their own figures
  const [others, setOthers] = useState(false);
  const shown = useMemo(() => (data?.candidates ?? []).filter(c => others || c.runestone !== false), [data, others]);
  const rows = useMemo(() => shown.filter(c => !prov || c.province === prov), [shown, prov]);
  if (!data) return <p className="text-sm text-slate-500">Hämtar luckorna …</p>;
  if (!data.available || !data.candidates) return <p className="text-sm text-slate-500">{data.note ?? "Kandidatlistan saknas."}</p>;
  const provinces = [...new Set(shown.map(c => c.province))].sort();
  const all = data.counts!;
  const rs = all.runsten ?? all;
  const ot = all.annat;
  const pct = (x: number | undefined) => (x == null ? "–" : `${Math.round(x * 100)} %`);
  const minP = Math.round((data.min_p ?? 0.5) * 100), sureP = Math.round((data.sure_p ?? 0.8) * 100);
  return (
    <>
      <p className="text-sm text-slate-600 mb-3 max-w-4xl">
        Sannolikhetsmodellen (METHODS.md 8.1, {data.model_version}) har gått igenom {rs.gaps_inventoried} luckor i de vikingatida
        runstenarnas texter. {rs.open} av dem har Rundata lämnat oåterställda. I {rs.candidates} av dem, på {rs.stones} runstenar,
        fyller modellen i ett känt ord med minst {minP} % kalibrerad sannolikhet, och i {rs.sure ?? "–"} med minst {sureP} %.
        Det är underlag att granska mot foto, skanning och utgåvornas kommentarer – öppna stenen och panelen <em>Vad skannern ser</em> –
        inte fynd. Kalibreringen är prövad på luckor som utgivarna fyllt (blindtest 2026-10-17); de öppna luckorna är ofta de
        svåraste, där utgivarna själva avstått, så procenten kan vara för höga där.
        {ot ? <> Andra föremål (berghällar, gravhällar, ben, amuletter) har {ot.candidates} luckor på samma nivå; de visas bara på begäran.</> : null}
      </p>
      <div className="flex flex-wrap items-center gap-4 mb-3">
        <label className="text-sm text-slate-600">Landskap{" "}
          <select value={prov} onChange={e => setProv(e.target.value)} className="liquid-glass-input-wrapper rounded-xl px-3 py-1.5 text-sm font-semibold">
            <option value="">alla ({shown.length})</option>
            {provinces.map(p => <option key={p} value={p}>{p} ({shown.filter(x => x.province === p).length})</option>)}
          </select>
        </label>
        {ot ? (
          <label className="text-sm text-slate-600 flex items-center gap-2">
            <input type="checkbox" checked={others} onChange={e => { setOthers(e.target.checked); setProv(""); }} />
            Visa även andra föremål ({ot.candidates})
          </label>
        ) : null}
      </div>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr className={TH_ROW}><th className="p-2 text-left">Sten</th><th className="p-2 text-left">Föremål</th>
            <th className="p-2 text-left">Hugget</th><th className="p-2 text-left">Ifyllnad</th><th className="p-2 text-left">Ord</th>
            <th className="p-2 text-left">Kalibrerad</th><th className="p-2 text-left">Modellens råa</th><th className="p-2 text-left">Näst bästa</th>
            <th className="p-2 text-left">Läsning</th><th className="p-2 text-left">Översättning (utkast)</th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.signum}-${r.gap}-${i}`} className="border-t border-slate-900/5 align-top">
                <td className="p-2"><StoneLinks signum={r.signum} /></td>
                <td className="p-2 text-xs text-slate-600">{r.object ?? "–"}</td>
                <td className="p-2 font-mono text-xs" translate="no">{r.carved}</td>
                <td className="p-2 font-mono text-xs" translate="no">{r.fill ?? "–"}</td>
                <td className="p-2 font-semibold" translate="no">{r.word ?? "–"}</td>
                <td className="p-2 font-semibold">{pct(r.p)}</td>
                <td className="p-2 text-xs text-slate-500">{pct(r.p_model)}</td>
                <td className="p-2 text-xs text-slate-600" translate="no">{r.alts[0] ? `${r.alts[0][0]} (${pct(r.alts[0][1])})` : "–"}</td>
                <td className="p-2 text-xs text-slate-600 max-w-md" translate="no">{r.reading ?? "–"}</td>
                <td className="p-2 text-xs text-slate-600 max-w-md" translate="no">{r.translation_sv ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
      <p className="text-[11px] text-slate-500 mt-3 max-w-4xl">
        <strong>Kalibrerad</strong> är procenten efter kalibreringen mot utgivarnas facit; <strong>modellens råa</strong> är
        hur mycket bättre ordet passar runorna och sammanhanget än alla andra ord modellen känner, före kalibreringen, och
        blir lätt hög för namn och ovanliga ord. <strong>Översättningen</strong> är ett utkast ord för ord ur en ordlista som
        modellen lärt sig av Rundatas egna översättningar utan stenen själv – ingen AI och ingen runolog har granskat den; ord
        som ordlistan inte kan översätta står kvar på fornspråk och namn som de lästs. Byggd {data.computed_at?.slice(0, 10)} ur
        luckinventeringen (scripts/runlm_gaps.py → scripts/textmodel_candidates.py). En lucka kan ha flera rader när flera
        ifyllnader når gränsen.
      </p>
    </>
  );
}

export function BriefTable({ rows, uninterpreted }: { rows: Brief[]; uninterpreted: boolean }) {
  const order = useMemo(() => new Map(rows.map((b, i) => [b.signum, i])), [rows]);
  const { sorted, header } = useSorted(rows, {
    order: b => order.get(b.signum), signum: b => b.signum, place: b => b.place, province: b => b.province,
    style: b => b.style, dating: b => b.dating || null, carvers: b => b.carvers.join(", ") || null,
  }, { key: "order", desc: false });
  return (
    <>
      <p className="text-sm text-slate-600 mb-4 max-w-4xl">
        {uninterpreted
          ? "Bevarade runstenar vars normalisering saknas eller är markerad som osäker i Rundata, från början sorterade med de längsta texterna först. RTI-visaren och ristningskartan från 3D kan hjälpa nyläsningar."
          : "Bevarade runstenar där stilgruppen är osäker (?) i Rundata. Ornamentiken får avgöra för ögat – foto, strykljus och ristningskarta finns under Bilder och runformer på 3D-sidan."}
      </p>
      <div className="overflow-x-auto">
        <ExportTable><table className="w-full text-sm">
          <thead><tr className={TH_ROW}>{header("signum", "Sten")}{header("place", "Plats")}{header("province", "Landskap")}{header("style", "Stil")}{header("dating", "Datering")}{header("carvers", "Ristare")}</tr></thead>
          <tbody>
            {sorted.slice(0, 200).map(b => (
              <tr key={b.signum} className="border-t border-slate-900/5">
                <td className="p-2"><StoneLinks signum={b.signum} /></td>
                <td className="p-2 text-slate-600" translate="no">{b.place}</td>
                <td className="p-2">{b.province}</td>
                <td className="p-2">{b.style ?? "–"}</td>
                <td className="p-2">{b.dating || "–"}</td>
                <td className="p-2">{b.carvers.join(", ") || "–"}</td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      </div>
    </>
  );
}
