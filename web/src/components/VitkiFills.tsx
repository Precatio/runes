"use client";

// Vitki's own fillings of lost runes on a stone (src/vitki_fills.py): confirmed ones in their own colour, proposals
// dashed, each with method, probability, date and evidence. Rundata's text is never changed; this is a layer on top.
// An admin can confirm, reject or reopen a filling, always with a comment.
import { useState } from "react";
import { useAuth } from "@/components/AuthContext";
import { EVIDENCE_LABEL, textmodel, type FillStatus, type VitkiFill } from "@/lib/textmodel";

export const FILL_STYLE: Record<"bekräftad" | "förslag", string> = {
  bekräftad: "border-teal-600 bg-teal-50 text-teal-900",
  förslag: "border-dashed border-amber-500 bg-amber-50/70 text-amber-900",
};

// The carved group with the filling in place of the lost runes
export function FilledGroup({ x }: { x: VitkiFill }) {
  const c = x.gap.carved;
  return (
    <span className="font-mono" translate="no">
      {c.slice(0, x.gap.start)}
      <span className={`font-bold px-0.5 rounded ${x.status === "bekräftad" ? "bg-teal-600 text-white" : "bg-amber-200 text-amber-950"}`}>{x.fill}</span>
      {c.slice(x.gap.end)}
    </span>
  );
}

function StatusChange({ x, onDone }: { x: VitkiFill; onDone: () => void }) {
  const { authHeaders } = useAuth();
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const next: FillStatus[] = x.status === "förslag" ? ["bekräftad", "avvisad"] : x.status === "bekräftad" ? ["avvisad"] : ["förslag"];
  const go = async (s: FillStatus) => {
    setBusy(true); setError(null);
    try {
      await textmodel.setFillStatus(await authHeaders(), x.id, s, comment);
      setComment("");
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Statusen kunde inte ändras.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex flex-wrap items-center gap-2 mt-2">
      <input value={comment} onChange={e => setComment(e.target.value)} placeholder="Kommentar (krävs)"
        className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs flex-1 min-w-[12rem]" />
      {next.map(s => (
        <button key={s} type="button" disabled={busy || !comment.trim()} onClick={() => go(s)}
          className="px-2.5 py-1 rounded-lg bg-slate-900 text-white text-xs font-semibold disabled:opacity-40">
          {s === "bekräftad" ? "Bekräfta" : s === "avvisad" ? "Avvisa" : "Gör till förslag"}
        </button>
      ))}
      {error && <span className="text-xs text-red-700">{error}</span>}
    </div>
  );
}

export default function VitkiFills({ fills, onChange }: { fills: VitkiFill[]; onChange?: () => void }) {
  const { isAdmin } = useAuth();
  if (!fills.length) return null;
  return (
    <section className="space-y-2">
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Vitkis ifyllningar</div>
      {fills.map(x => (
        <div key={x.id} className={`rounded-xl border-2 p-3 text-sm ${FILL_STYLE[x.status === "bekräftad" ? "bekräftad" : "förslag"]}`}>
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <FilledGroup x={x} />
            {x.word && <span translate="no" className={x.name ? "font-semibold" : ""}>{x.word}</span>}
            <span className="text-xs">{x.label}</span>
          </div>
          <p className="text-xs mt-1 opacity-90">{x.comment} <span className="opacity-70">({x.by})</span></p>
          {x.evidence.length > 0 && (
            <p className="text-[11px] mt-1 opacity-80">
              Belägg: {x.evidence.map(e => `${EVIDENCE_LABEL[e.kind]}: ${e.ref}`).join(" · ")}
            </p>
          )}
          {x.model_version && <p className="text-[11px] opacity-70">Modellversion {x.model_version}</p>}
          {isAdmin && <StatusChange x={x} onDone={() => onChange?.()} />}
        </div>
      ))}
      <p className="text-[11px] text-slate-500">
        Ett eget lager ovanpå Rundata, som inte ändras. Heldragen ram: bekräftad av Vitki efter granskning mot belägg;
        streckad ram: förslag som ännu inte är granskat. Sannolikhetsmodellen tränas och prövas aldrig på ifyllningarna.
      </p>
    </section>
  );
}
