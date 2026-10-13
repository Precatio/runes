"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ExportTable from "@/components/ExportTable";

// GET /api/admin/github (src/github_stats.py)
interface Day { day: string; clones?: number; clones_uniques?: number; views?: number; views_uniques?: number }
interface Stats {
  repo: string; url: string; stars: number; forks: number; watchers: number; open_issues: number;
  created_at: string; pushed_at: string; fetched_at: string; release_downloads: number;
  releases: { tag: string; name: string; published_at: string; downloads: number }[];
  traffic: {
    available: boolean; reason?: string;
    last14?: { clones: number; clone_uniques: number; views: number; view_uniques: number };
    total?: { clones: number; views: number; since: string | null };
    days?: Day[];
    referrers?: { referrer: string; count: number; uniques: number }[];
    paths?: { path: string; title?: string; count: number; uniques: number }[];
  };
}

const BLUE = "#2a78d6";
const nf = (n: number) => n.toLocaleString("sv-SE");
const shortDay = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString("sv-SE", { day: "numeric", month: "short" });

/** Every day from the first to the last, also the days without activity. */
function continuous(days: Day[]): Day[] {
  if (!days.length) return [];
  const by = new Map(days.map(d => [d.day, d]));
  const out: Day[] = [];
  for (let t = Date.parse(`${days[0].day}T12:00:00Z`); t <= Date.parse(`${days[days.length - 1].day}T12:00:00Z`); t += 86400000) {
    const day = new Date(t).toISOString().slice(0, 10);
    out.push(by.get(day) ?? { day });
  }
  return out;
}

function Tile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-900/10 bg-white/70 px-4 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-2xl font-bold tabular-nums text-slate-900">{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

/** Daily counts as bars: one series, its own scale, a tooltip per bar. */
function DailyBars({ title, days, k, unit }: { title: string; days: Day[]; k: "clones" | "views"; unit: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const values = days.map(d => d[k] ?? 0);
  const max = Math.max(1, ...values);
  const h = hover !== null ? days[hover] : null;
  return (
    <figure className="rounded-xl border border-slate-900/10 bg-white px-4 pt-3 pb-2">
      <figcaption className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-semibold text-slate-900">{title}</span>
        <span className="text-xs text-slate-600 tabular-nums" aria-live="polite">
          {h ? `${shortDay(h.day)}: ${nf(h[k] ?? 0)} ${unit}, ${nf(h[`${k}_uniques`] ?? 0)} unika` : `högst ${nf(max)} per dag`}
        </span>
      </figcaption>
      <div className="relative mt-2 h-32">
        <div className="absolute inset-x-0 top-1/2 border-t border-dashed border-slate-200" aria-hidden="true" />
        <div className="absolute inset-0 flex items-end gap-[2px]" onMouseLeave={() => setHover(null)}>
          {days.map((d, i) => (
            <button key={d.day} type="button" className="relative h-full flex-1 min-w-[3px] flex items-end focus:outline-none"
              onMouseEnter={() => setHover(i)} onFocus={() => setHover(i)}
              aria-label={`${shortDay(d.day)}: ${values[i]} ${unit}, ${d[`${k}_uniques`] ?? 0} unika`}>
              <span className="block w-full rounded-t-[4px]"
                style={{ height: `${values[i] ? Math.max(2, (values[i] / max) * 100) : 0}%`, background: BLUE, opacity: hover === null || hover === i ? 1 : 0.55 }} />
            </button>
          ))}
        </div>
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-slate-500 tabular-nums">
        <span>{days.length ? shortDay(days[0].day) : ""}</span>
        <span>{days.length ? shortDay(days[days.length - 1].day) : ""}</span>
      </div>
    </figure>
  );
}

/** The repository on GitHub: stars, forks, releases and – with a token – clones and visits over time. */
export default function GithubStats({ call }: { call: (path: string, init?: RequestInit) => Promise<any> }) { // eslint-disable-line @typescript-eslint/no-explicit-any
  const [data, setData] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);

  const fetchStats = useCallback((refresh: boolean) => call(`/api/admin/github${refresh ? "?refresh=true" : ""}`)
    .then((d: Stats) => { setData(d); setError(null); })
    .catch(e => setError(e instanceof Error ? e.message : "GitHub kunde inte nås."))
    .finally(() => setBusy(false)), [call]);
  useEffect(() => { fetchStats(false); }, [fetchStats]);
  const load = (refresh: boolean) => { setBusy(true); fetchStats(refresh); };

  const days = useMemo(() => continuous(data?.traffic.days ?? []), [data]);
  const t = data?.traffic;

  return (
    <section className="liquid-glass-island rounded-[24px] p-4 sm:p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-slate-900">GitHub</h3>
          <p className="text-sm text-slate-600">
            Hur många som hittar och hämtar Vitki{data ? <> – <a href={data.url} target="_blank" rel="noopener noreferrer" className="text-[#b7410e] underline" translate="no">{data.repo}</a></> : null}.
          </p>
        </div>
        <button onClick={() => load(true)} disabled={busy} className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold disabled:opacity-40">
          {busy ? "Hämtar …" : "Uppdatera"}
        </button>
      </div>
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}
      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {t?.available && t.last14 && (
              <>
                <Tile label="Kloner, 14 dagar" value={nf(t.last14.clones)} sub={`${nf(t.last14.clone_uniques)} unika`} />
                <Tile label="Besök, 14 dagar" value={nf(t.last14.views)} sub={`${nf(t.last14.view_uniques)} unika besökare`} />
                <Tile label="Kloner totalt" value={nf(t.total?.clones ?? 0)} sub={t.total?.since ? `sedan ${shortDay(t.total.since)}` : undefined} />
                <Tile label="Besök totalt" value={nf(t.total?.views ?? 0)} sub={t.total?.since ? `sedan ${shortDay(t.total.since)}` : undefined} />
              </>
            )}
            <Tile label="Stjärnor" value={nf(data.stars)} />
            <Tile label="Forkar" value={nf(data.forks)} sub="egna kopior av koden" />
            <Tile label="Bevakare" value={nf(data.watchers)} />
            <Tile label="Nedladdningar" value={nf(data.release_downloads)} sub={data.releases.length ? `${data.releases.length} releaser` : "inga releaser än"} />
          </div>

          {t?.available && days.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <DailyBars title="Kloner per dag" days={days} k="clones" unit="kloner" />
                <DailyBars title="Besök per dag" days={days} k="views" unit="besök" />
              </div>
              <details className="text-xs text-slate-600">
                <summary className="cursor-pointer font-semibold">Visa som tabell</summary>
                <ExportTable name="GitHub, kloner och besök per dag" sources={["GitHub, trafikstatistik för repot (API: /traffic/clones och /traffic/views)."]}>
                  <table className="mt-2 w-full text-sm">
                    <thead><tr className="text-left text-slate-500"><th className="p-1.5">Dag</th><th className="p-1.5">Kloner</th><th className="p-1.5">Unika</th><th className="p-1.5">Besök</th><th className="p-1.5">Unika</th></tr></thead>
                    <tbody>{[...days].reverse().map(d => (
                      <tr key={d.day} className="border-t border-slate-900/5 tabular-nums">
                        <td className="p-1.5">{d.day}</td><td className="p-1.5">{d.clones ?? 0}</td><td className="p-1.5">{d.clones_uniques ?? 0}</td>
                        <td className="p-1.5">{d.views ?? 0}</td><td className="p-1.5">{d.views_uniques ?? 0}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </ExportTable>
              </details>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {!!t.referrers?.length && (
                  <div>
                    <p className="font-semibold text-slate-900">Varifrån besökarna kommer (14 dagar)</p>
                    <ul className="mt-1 space-y-0.5 text-slate-700">{t.referrers.slice(0, 8).map(r => (
                      <li key={r.referrer} className="flex justify-between gap-2"><span translate="no">{r.referrer}</span><span className="tabular-nums text-slate-500">{nf(r.count)} ({nf(r.uniques)} unika)</span></li>
                    ))}</ul>
                  </div>
                )}
                {!!t.paths?.length && (
                  <div>
                    <p className="font-semibold text-slate-900">Mest besökta sidor (14 dagar)</p>
                    <ul className="mt-1 space-y-0.5 text-slate-700">{t.paths.slice(0, 6).map(p => (
                      <li key={p.path} className="flex justify-between gap-2"><span className="truncate" translate="no">{p.path.replace(`/${data.repo}`, "") || "/"}</span><span className="tabular-nums text-slate-500 shrink-0">{nf(p.count)}</span></li>
                    ))}</ul>
                  </div>
                )}
              </div>
            </>
          )}

          {!t?.available && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 space-y-2">
              <p className="font-semibold">Kloner och besök kräver en GitHub-token</p>
              <p>{t?.reason}</p>
              <ol className="list-decimal pl-5 space-y-1">
                <li>På GitHub: Settings → Developer settings → Personal access tokens → <em>Fine-grained tokens</em> → Generate new token.</li>
                <li>Repository access: <em>Only select repositories</em> → <span translate="no">{data.repo}</span>. Permissions: <em>Administration: Read-only</em>.</li>
                <li>Lägg raden <code>GITHUB_TOKEN=…</code> i filen <code>.env</code> i projektets rot (den laddas aldrig upp till GitHub) och tryck Uppdatera.</li>
              </ol>
            </div>
          )}

          <p className="text-xs text-slate-500">
            En klon är en nedladdning med git, också från robotar och tjänster, så de unika är det bästa måttet på personer.
            GitHub räknar inte nedladdningar av källkodens zip-fil; filer som bifogas en release räknas under Nedladdningar.
            GitHub sparar trafiken i 14 dagar – appen sparar varje hämtning, så historiken växer så länge Admin öppnas minst
            varannan vecka. Hämtat {new Date(data.fetched_at).toLocaleString("sv-SE")}.
          </p>
        </>
      )}
    </section>
  );
}
