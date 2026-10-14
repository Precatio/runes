"use client";

import { useCallback, useEffect, useState } from "react";

// GET /api/admin/site/votes: the public website's vote, seen only here (components/SiteVote.tsx casts it)
interface Question { question: string; total: number; choices: Record<string, number>; first: string | null; last: string | null }
const QUESTIONS: Record<string, { title: string; labels: Record<string, string> }> = {
  webbapp: { title: "Vitki i webbläsaren?", labels: { ja: "Ja, gärna", nej: "Nej, jag installerar själv" } },
};
const day = (s: string | null) => (s ? new Date(s).toLocaleString("sv-SE", { dateStyle: "medium", timeStyle: "short" }) : "–");

export default function SiteVotes({ call }: { call: (path: string, init?: RequestInit) => Promise<any> }) { // eslint-disable-line @typescript-eslint/no-explicit-any
  const [data, setData] = useState<Question[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => call("/api/admin/site/votes")
    .then(d => { setData(d.questions); setError(null); })
    .catch(e => setError(e instanceof Error ? e.message : "Rösterna kunde inte hämtas.")), [call]);
  useEffect(() => { load(); }, [load]);

  return (
    <section className="liquid-glass-island rounded-[24px] p-4 sm:p-6 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Röstning på webbplatsen</h3>
          <p className="text-sm text-slate-600">Besökarnas röster på vitkirunor.se. Bara du ser resultatet; webbläsare kan inte läsa rösterna.</p>
        </div>
        <button onClick={load} className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold">Uppdatera</button>
      </div>
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}
      {data && !data.length && <p className="text-sm text-slate-600">Inga röster än.</p>}
      {data?.map(q => {
        const meta = QUESTIONS[q.question] ?? { title: q.question, labels: {} };
        return (
          <div key={q.question} className="rounded-xl border border-slate-900/10 bg-white/70 p-4">
            <p className="font-semibold text-slate-900">{meta.title} <span className="font-normal text-slate-500">– {q.total} röster</span></p>
            <div className="mt-3 space-y-2">
              {Object.entries(q.choices).sort((a, b) => b[1] - a[1]).map(([choice, n]) => {
                const share = q.total ? n / q.total : 0;
                return (
                  <div key={choice} className="grid grid-cols-[minmax(0,12rem)_1fr_auto] items-center gap-3 text-sm">
                    <span className="truncate text-slate-700">{meta.labels[choice] ?? choice}</span>
                    <span className="h-2.5 rounded-full bg-slate-100"><span className="block h-2.5 rounded-full bg-[#2a78d6]" style={{ width: `${Math.round(share * 100)}%` }} /></span>
                    <span className="tabular-nums text-slate-700">{n} ({Math.round(share * 100)} %)</span>
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-slate-500">Första rösten {day(q.first)} · senaste {day(q.last)}. En röst per webbläsare, men den som vill kan rösta igen från en annan, så se resultatet som en fingervisning.</p>
          </div>
        );
      })}
    </section>
  );
}
