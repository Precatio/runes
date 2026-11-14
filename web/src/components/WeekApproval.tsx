"use client";

import { useEffect, useState } from "react";
import { dateLabel } from "@/components/BlogBody";

// One planned publication from data/publiceringsschema.json with its status (GET /api/admin/blog/week,
// api/routers/blog_week.py)
interface WeekEntry {
  datum: string; tid: string; id: string; titel: string; spar: "P" | "F";
  bluesky: { text: string; tags: string[] } | null; godkand: string | null;
  publish_at: string | null; state: "utkast" | "schemalagd" | "publicerad" | "saknas"; exists: boolean;
  publishedAt: string | null; slug: string | null; title: string | null; title_en: boolean; body_en: boolean;
  labels: string[]; labels_problem: string | null; bluesky_length: number | null; bluesky_limit: number;
  can_approve: boolean; reason: string | null;
}
interface Week { from: string; to: string; week: number; entries: WeekEntry[] }
interface Result { id: string; ok: boolean; reason?: string; titel?: string; slug?: string; publishedAt?: string; bluesky?: string | null }

// "2026-11-16" moved a number of days, without the browser's time zone getting in the way
const shift = (day: string, days: number) => {
  const d = new Date(`${day}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};
const dayLabel = (day: string) =>
  new Date(`${day}T12:00:00Z`).toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
const capital = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const TRACK = { P: "Populärspåret", F: "Forskningsspåret" } as const;

const chip = "text-[10px] font-bold rounded-md px-1.5 border";
const good = `${chip} border-emerald-300 bg-emerald-50 text-emerald-800`;
const warn = `${chip} border-amber-300 bg-amber-50 text-amber-800`;
const plain = `${chip} border-slate-300 bg-slate-50 text-slate-600`;
const STATE: Record<WeekEntry["state"], string> = {
  utkast: plain, schemalagd: warn, publicerad: good, saknas: `${chip} border-red-300 bg-red-50 text-red-700`,
};

/** "Veckans publiceringar": the week's planned articles, approved and scheduled with one click (and a confirmation).
 *  onEdit opens an article in the editor below; onChanged reloads the list and the website status after an approval. */
export default function WeekApproval({ call, onEdit, onChanged }: {
  call: (path: string, init?: RequestInit) => Promise<any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  onEdit: (id: string) => void;
  onChanged: () => void;
}) {
  const [from, setFrom] = useState<string | null>(null);
  const [week, setWeek] = useState<Week | null>(null);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState<"approve" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Result[] | null>(null);
  // Bumped after an approval, so that the week is read again with its new status
  const [round, setRound] = useState(0);

  // The week (GET /api/admin/blog/week); without from the coming Monday–Sunday. State is set only when the answer comes
  useEffect(() => {
    let alive = true;
    call(`/api/admin/blog/week${from ? `?from=${from}` : ""}`)
      .then((w: Week) => {
        if (!alive) return;
        setWeek(w); setError(null);
        setChecked(new Set(w.entries.filter(e => e.can_approve).map(e => e.id)));
      })
      .catch(e => { if (alive) setError(e instanceof Error ? e.message : "Veckans publiceringar kunde inte hämtas."); });
    return () => { alive = false; };
  }, [call, from, round]);
  const go = (days: number) => {
    if (!week) return;
    setFrom(shift(week.from, days)); setResults(null); setConfirming(false);
  };

  const chosen = (week?.entries ?? []).filter(e => e.can_approve && checked.has(e.id));
  const toggle = (id: string) => setChecked(s => {
    const next = new Set(s);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

  const approve = async () => {
    if (!week) return;
    setBusy("approve"); setError(null);
    try {
      const d = await call("/api/admin/blog/week/approve", { method: "POST", body: JSON.stringify({ from: week.from, ids: chosen.map(e => e.id) }) });
      setResults(d.results);
      onChanged();
      setRound(r => r + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Godkännandet misslyckades.");
    } finally {
      setBusy(null); setConfirming(false);
    }
  };

  return (
    <div className="rounded-xl border border-[#b7410e]/30 bg-white/80 p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h4 className="text-base font-bold text-slate-900" style={{ fontFamily: "var(--font-serif)" }}>
            Veckans publiceringar{week ? ` (vecka ${week.week})` : ""}
          </h4>
          <p className="text-xs text-slate-500">
            {week ? `${dayLabel(week.from)} – ${dayLabel(week.to)}. ` : ""}
            Ur publiceringsschemat (data/publiceringsschema.json). Godkända artiklar schemaläggs till sin tid och deras
            engelska inlägg läggs i Bluesky-kön och går ut samma dag kl. 13 (kön postar tisdagar och fredagar).
          </p>
        </div>
        <div className="flex gap-1.5">
          <button onClick={() => go(-7)} disabled={!week || busy !== null}
            className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold disabled:opacity-40">← Förra veckan</button>
          <button onClick={() => go(7)} disabled={!week || busy !== null}
            className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold disabled:opacity-40">Nästa vecka →</button>
        </div>
      </div>

      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}
      {!week && !error && <p className="text-sm text-slate-500">Hämtar …</p>}
      {week && week.entries.length === 0 && (
        <p className="text-sm text-slate-500">Inget planerat den här veckan. Lägg till rader i data/publiceringsschema.json.</p>
      )}

      {week && week.entries.length > 0 && (
        <ul className="divide-y divide-slate-900/5">
          {week.entries.map(e => (
            <li key={`${e.id}-${e.datum}`} className="py-2.5 flex gap-3 text-sm">
              <input type="checkbox" checked={e.can_approve && checked.has(e.id)} disabled={!e.can_approve || busy !== null}
                onChange={() => toggle(e.id)} aria-label={`Godkänn ${e.titel}`} className="mt-1 accent-[#b7410e]" />
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                  <span className="text-[12px] font-semibold text-slate-600 w-44 shrink-0">{capital(dayLabel(e.datum))} kl. {e.tid}</span>
                  <button onClick={() => onEdit(e.id)} disabled={!e.exists} title="Öppna i redigeraren"
                    className="min-w-0 text-left font-semibold text-slate-900 hover:text-[#b7410e] hover:underline disabled:hover:no-underline" translate="no">
                    {e.title || e.titel}
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className={plain}>{TRACK[e.spar] ?? e.spar}</span>
                  <span className={STATE[e.state]}>
                    {e.state === "schemalagd" ? `schemalagd ${dateLabel(e.publishedAt, "sv", true)}` : e.state}
                  </span>
                  {e.exists && <span className={e.title_en && e.body_en ? good : warn}>{e.title_en && e.body_en ? "engelska" : "engelska saknas"}</span>}
                  {e.exists && <span className={e.labels_problem ? warn : good} title={e.labels.join(", ")}>{e.labels_problem ? "etiketter: fel" : "etiketter"}</span>}
                  {e.bluesky_length !== null
                    ? <span className={e.bluesky_length > e.bluesky_limit ? warn : good}>Bluesky {e.bluesky_length}/{e.bluesky_limit}</span>
                    : <span className={plain}>inget Bluesky-inlägg</span>}
                  {e.godkand && <span className={`${chip} border-[#b7410e]/40 bg-[#fbf3ee] text-[#9a350b]`}>godkänd {dateLabel(e.godkand, "sv", true)}</span>}
                  {e.slug && <span className="text-[11px] text-slate-400" translate="no">/artiklar/{e.slug}</span>}
                </div>
                {!e.can_approve && e.reason && <p className="text-xs text-slate-500">{e.reason}</p>}
                {e.labels_problem && <p className="text-xs text-amber-700">{e.labels_problem}</p>}
                {e.bluesky && (
                  <details className="text-xs text-slate-600">
                    <summary className="cursor-pointer font-semibold">Bluesky-inlägget</summary>
                    <p className="mt-1 whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-2" lang="en" translate="no">
                      {e.bluesky.text}{"\n\n"}{e.bluesky.tags.map(t => `#${t}`).join(" ")}
                    </p>
                  </details>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {week && week.entries.length > 0 && !confirming && (
        <button onClick={() => { setConfirming(true); setResults(null); }} disabled={chosen.length === 0 || busy !== null}
          className="px-4 py-2 rounded-xl bg-[#b7410e] text-white text-sm font-bold disabled:opacity-40">
          Godkänn veckans publiceringar{chosen.length ? ` (${chosen.length})` : ""}
        </button>
      )}

      {confirming && (
        <div className="rounded-xl border border-[#b7410e]/40 bg-[#fbf3ee] p-3 space-y-2 text-sm">
          <p className="font-bold text-slate-900">Det här schemaläggs:</p>
          <ul className="list-disc pl-5 space-y-0.5 text-slate-700">
            {chosen.map(e => (
              <li key={e.id}>
                {capital(dayLabel(e.datum))} kl. {e.tid}: <span translate="no">{e.title || e.titel}</span>
                {e.bluesky ? (e.body_en ? " – och Bluesky-inlägget samma dag kl. 13" : " – inget Bluesky-inlägg (ingen engelsk utgåva)") : ""}
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-600">Texterna ändras inte. Artiklarna går live av sig själva vid sin tid, så länge appen är igång.</p>
          <div className="flex gap-2">
            <button onClick={approve} disabled={busy !== null} className="px-4 py-2 rounded-xl bg-[#b7410e] text-white text-sm font-bold disabled:opacity-40">
              {busy === "approve" ? "Schemalägger …" : "Ja, schemalägg"}
            </button>
            <button onClick={() => setConfirming(false)} disabled={busy !== null} className="px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold disabled:opacity-40">
              Avbryt
            </button>
          </div>
        </div>
      )}

      {results && (
        <ul className="space-y-1 text-sm">
          {results.map(r => (
            <li key={r.id} className={r.ok ? "text-emerald-700" : "text-red-700"}>
              <span className="font-semibold" translate="no">{r.titel ?? r.id}</span>:{" "}
              {r.ok
                ? <>schemalagd {dateLabel(r.publishedAt, "sv", true)}{r.bluesky ? `; Bluesky: ${r.bluesky}` : ""}.</>
                : <>inte schemalagd – {r.reason}</>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
