"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";
import { db, type SavedQuestion } from "@/lib/db";
import { GLOSSARY } from "@/lib/glossary";
import { Tip } from "@/components/Explain";
import { pct, pIs, VERDICT } from "@/components/OwnQuestion";

// The questions saved from Pröva en egen fråga (components/OwnQuestion.tsx), shown in Forskningsluckor → Våra resultat.
// A self-chosen question is exploratory however small its p: the evidence stays "svagt" unless the pattern held in both
// halves of the parishes, and "måttligt" at most – strong evidence needs an analysis plan written before the question
// was asked (METHODS.md 1x, 1y).
const EVIDENCE: Record<string, { label: string; help: string }> = {
  "håller": { label: "måttligt", help: "Håller i båda halvorna och efter justeringen för besökets frågor. Starkare än så blir en egen fråga inte förrän den prövats enligt en analysplan." },
  "håller men inte justerat": { label: "svagt", help: "Håller i båda halvorna, men inte när besökets alla frågor räknas in." },
  "beror på ristarna": { label: "svagt", help: "Håller i halvorna men inte med ristaren som slumpeffekt." },
  "kan vara platsen": { label: "svagt", help: "Håller i halvorna men inte när stenarnas läge får forma en egen yta." },
  "bara i hela": { label: "svagt", help: "Syns i hela korpusen men inte i båda halvorna av socknarna." },
  "ingen skillnad": { label: "–", help: "Ingen säker skillnad: ett negativt resultat, sparat för att det också är kunskap." },
};

interface Recheck { verdict: string; p: number | null; replicated: boolean; corpus: string }

export default function SavedQuestions() {
  const [list, setList] = useState<SavedQuestion[] | null>(null);
  const [recheck, setRecheck] = useState<Record<string, Recheck | "fel">>({});

  useEffect(() => { db.getQuestions().then(setList).catch(() => setList([])); }, []);
  if (!list || list.length === 0) return null;

  const remove = async (id: string) => {
    if (!window.confirm("Ta bort det sparade fyndet?")) return;
    await db.deleteQuestion(id);
    setList(l => (l ?? []).filter(x => x.id !== id));
  };
  // The same question on the corpus as it is now, on its own (no earlier questions): does the pattern still hold?
  const again = async (s: SavedQuestion) => {
    try {
      const res = await fetch(`${API_URL}/api/research/question`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ a: s.a.key, kind: s.b.kind, key: s.b.key }),
      });
      if (!res.ok) throw new Error();
      const d = await res.json();
      setRecheck(r => ({ ...r, [s.id]: { verdict: d.verdict, p: d.adjusted?.p ?? null, replicated: !!d.halves?.replicated, corpus: d.corpus } }));
    } catch {
      setRecheck(r => ({ ...r, [s.id]: "fel" }));
    }
  };

  return (
    <details open className="mb-6 rounded-2xl border border-slate-200 bg-white/70 p-4 sm:p-5">
      <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="text-lg font-bold text-slate-900">Egna frågor</span>
          <span className="text-sm text-slate-500">sparade ur Pröva en egen fråga · {list.length}</span>
          <Link href="/statistik#egen-fraga" onClick={e => e.stopPropagation()} className="ml-auto text-xs font-semibold text-[#b7410e] hover:underline">
            Pröva en ny fråga →
          </Link>
        </div>
      </summary>
      <p className="text-xs text-slate-500 mt-3 mb-3 max-w-4xl">
        Siffrorna är som de var när frågan sparades. Ett svar på en egen fråga är en hypotes: beläggen räknas som högst
        måttliga, och bara om mönstret höll i båda halvorna av socknarna. För att använda ett av dem i en text behövs en
        analysplan som skrivs innan frågan ställs igen.
      </p>
      <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {list.map(s => {
          const v = VERDICT[s.verdict as keyof typeof VERDICT] ?? { label: s.verdict, style: "bg-slate-100 text-slate-700 border-slate-300" };
          const ev = EVIDENCE[s.verdict];
          const rc = recheck[s.id];
          const open = `/statistik?a=${encodeURIComponent(s.a.key)}&jamfor=${encodeURIComponent(s.b.kind)}&varde=${encodeURIComponent(s.b.key)}#egen-fraga`;
          return (
            <li key={s.id} className="rounded-xl border border-slate-200 border-l-4 border-l-slate-500 bg-white px-4 py-3 space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Egen fråga</span>
                <span className="ml-auto flex flex-wrap items-center gap-1.5">
                  <span className={`px-2 py-0.5 rounded-lg border text-[11px] font-bold ${v.style}`}>{v.label}</span>
                  {ev && <span className="px-2 py-0.5 rounded-lg border border-slate-200 text-[11px] text-slate-600" title={ev.help}>belägg {ev.label}</span>}
                </span>
              </div>
              <p className="text-sm text-slate-800">
                <strong>{s.a.label}</strong> {s.b.yes}: <strong>{pct(s.withB.share)}</strong> av {s.withB.n} stenar, mot{" "}
                <strong>{pct(s.withoutB.share)}</strong> av {s.withoutB.n} {s.b.no}.
              </p>
              <p className="text-xs text-slate-600">
                Justerat för {s.b.adjusted}: <Tip text={GLOSSARY["Oddskvot"]}>oddskvot</Tip> {s.or == null ? "–" : s.or.toFixed(2).replace(".", ",")}, p {pIs(s.p)};
                {" "}<Tip text={GLOSSARY["Båda halvorna"]}>halvorna</Tip> p {pIs(s.halves.pA)} och p {pIs(s.halves.pB)}
                {s.carver ? <>; utan {s.carver.name} {s.carver.holds ? "håller det" : "håller det inte"}</> : null}
                ; fråga {s.nQuestions} under besöket, <Tip text={GLOSSARY["Frågor under besöket"]}>q</Tip> {pIs(s.q)}.
              </p>
              {s.note && <p className="text-sm text-slate-700 italic">{s.note}</p>}
              {rc && (
                <p className={`text-xs rounded-lg px-2 py-1 ${rc === "fel" ? "bg-red-50 text-red-800" : "bg-slate-50 text-slate-700"}`}>
                  {rc === "fel" ? "Kunde inte räkna om." : (
                    <>Omräknad nu, som enda fråga{rc.corpus !== s.corpus ? " och på en nyare version av korpusen" : ""}: {VERDICT[rc.verdict as keyof typeof VERDICT]?.label ?? rc.verdict} (p {pIs(rc.p)}{rc.replicated ? ", håller i båda halvorna" : ""}).</>
                  )}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-3 text-xs">
                <span className="text-slate-500">
                  Sparad {new Date(s.createdAt).toLocaleDateString("sv-SE")} · korpus <span translate="no">{s.corpus || "–"}</span>
                </span>
                <span className="ml-auto flex gap-3">
                  <button type="button" onClick={() => again(s)} className="font-semibold text-[#b7410e] hover:underline">Räkna om</button>
                  <Link href={open} className="font-semibold text-[#b7410e] hover:underline">Öppna i Statistik</Link>
                  <button type="button" onClick={() => remove(s.id)} className="font-semibold text-slate-500 hover:underline">Ta bort</button>
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </details>
  );
}
