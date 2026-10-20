"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { STATS_OFF_URL } from "@/lib/site";

// GET /api/admin/site/stats: the public website's visitor counts (components/SiteTracker.tsx writes them), seen only here
interface Row { key: string; n: number }
interface Stats {
  since: string; days: number; day: string | null; views: number; visits: number; computed_at: string;
  per_day: { day: string; views: number; visits: number }[];
  pages: { path: string; title: string | null; n: number }[];
  sections: { key: string; n: number; share: number | null }[];
  referrers: Row[]; direct: number; countries: Row[]; languages: Row[]; devices: Row[];
  searches: { total: number; top: Row[]; no_hits: Row[] };
  clicks: { share: Row[]; outbound: Row[]; language: Row[]; shared_pages: Row[] };
  via: Row[]; flow: Row[]; entries: { path: string; title: string | null; n: number }[];
}
type Call = (path: string, init?: RequestInit) => Promise<any>; // eslint-disable-line @typescript-eslint/no-explicit-any

// The start page's sections (their id in app/page.tsx)
const SECTIONS: Record<string, string> = {
  artiklar: "Artiklar", r: "Vad är R?", forskning: "För forskningen", appen: "Så ser Vitki ut (skärmbilder)",
  nytt: "Vad är nytt", landskap: "Stenarna i sitt landskap", kallor: "Källor", oppen: "Öppen källkod",
  om: "Om grundaren och licens", "kom-igang": "Kör Vitki (och röstningen)",
};
const RANGES = [7, 30, 90, 365];
const BAR_AREA = 104; // px för den högsta stapeln; talen får 26 px ovanför
const pct = (v: number | null) => (v == null ? "–" : `${Math.round(v * 100)} %`);
const num = (n: number) => n.toLocaleString("sv-SE");

function Bars({ rows, total, label = r => r.key }: { rows: Row[]; total: number; label?: (r: Row) => string }) {
  if (!rows.length) return <p className="text-sm text-slate-500">Inget än.</p>;
  return (
    <div className="space-y-1.5">
      {rows.map(r => (
        <div key={r.key} className="grid grid-cols-[minmax(0,1fr)_5rem_auto] items-center gap-3 text-sm">
          <span className="truncate text-slate-700" title={label(r)}>{label(r)}</span>
          <span className="h-2 rounded-full bg-slate-100"><span className="block h-2 rounded-full bg-[#2a78d6]" style={{ width: `${total ? Math.max(2, Math.round(r.n / total * 100)) : 0}%` }} /></span>
          <span className="w-10 text-right tabular-nums text-slate-700">{num(r.n)}</span>
        </div>
      ))}
    </div>
  );
}

function Box({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-900/10 bg-white/70 p-4">
      <p className="font-semibold text-slate-900">{title}</p>
      {note && <p className="mt-0.5 text-xs text-slate-500">{note}</p>}
      <div className="mt-3">{children}</div>
    </div>
  );
}

export default function SiteStats({ call }: { call: Call }) {
  const [days, setDays] = useState(30);
  // En klickad stapel: allt utom staplarna räknas då på den dagen ensam (servern filtrerar raderna)
  const [day, setDay] = useState<string | null>(null);
  const [data, setData] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const load = useCallback((fresh = false) => call(`/api/admin/site/stats?days=${days}${day ? `&day=${day}` : ""}${fresh ? "&fresh=true" : ""}`)
    .then(d => { setData(d); setError(null); })
    .catch(e => setError(e instanceof Error ? e.message : "Besöksstatistiken kunde inte hämtas.")), [call, days, day]);
  useEffect(() => { load(); }, [load]);
  // Längre perioder än bredden rymmer scrollar i sidled; senaste dagen ska synas först
  const dayScroll = useRef<HTMLDivElement>(null);
  useEffect(() => { const el = dayScroll.current; if (el) el.scrollLeft = el.scrollWidth; }, [data?.since, data?.days]);
  const dayLabel = day ? new Date(day).toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long" }) : null;

  const max = Math.max(1, ...(data?.per_day ?? []).map(d => d.views));
  const copy = () => navigator.clipboard?.writeText(STATS_OFF_URL).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });

  return (
    <section className="liquid-glass-island rounded-[24px] p-4 sm:p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Besökare på webbplatsen</h3>
          <p className="text-sm text-slate-600">Sidvisningar, sökord, delningar och klick på vitkirunor.se, utan kakor och utan IP-adresser. Bara du ser statistiken.</p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {RANGES.map(r => (
            <button key={r} onClick={() => { setDays(r); setDay(null); }}
              className={`px-3 py-1.5 rounded-lg border text-xs font-bold ${r === days ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white"}`}>
              {r === 365 ? "1 år" : `${r} dagar`}
            </button>
          ))}
          <button onClick={() => load(true)} className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold">Uppdatera</button>
        </div>
      </div>
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}

      {data && (
        <>
          {dayLabel && (
            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[#2a78d6]/30 bg-[#2a78d6]/5 px-3 py-2 text-sm text-slate-800">
              <span>Visar <strong>{dayLabel}</strong> ({day}): talen, sidorna, länderna och sökorden nedan gäller bara den dagen. Staplarna visar hela perioden.</span>
              <button onClick={() => setDay(null)} className="ml-auto px-2.5 py-1 rounded-lg border border-slate-300 bg-white text-xs font-bold">Visa hela perioden</button>
            </div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Sidvisningar", value: num(data.views) },
              { label: "Besök", value: num(data.visits), note: "sidvisningar som började utifrån" },
              { label: "Sidor per besök", value: data.visits ? (data.views / data.visits).toFixed(1).replace(".", ",") : "–" },
              { label: "Via andra webbplatser", value: data.visits ? pct((data.visits - data.direct) / data.visits) : "–", note: "av besöken" },
            ].map(t => (
              <div key={t.label} className="rounded-xl border border-slate-900/10 bg-white/70 p-3">
                <div className="text-xs font-semibold text-slate-500">{t.label}</div>
                <div className="mt-1 text-2xl font-bold tabular-nums text-slate-900">{t.value}</div>
                {t.note && <div className="text-[11px] text-slate-500">{t.note}</div>}
              </div>
            ))}
          </div>

          <Box title="Sidvisningar per dag" note={`Från ${data.since}. Det fetstilta talet över varje stapel är dagens sidvisningar, det grå under det är dagens besök (sidvisningar som började utifrån). Klicka på en stapel så visar allt nedanför bara den dagen; klicka igen för hela perioden.`}>
            <div ref={dayScroll} className="overflow-x-auto pb-1">
              <div className="flex items-end gap-[2px]" style={{ height: BAR_AREA + 26 }} role="img" aria-label="Sidvisningar och besök per dag">
                {data.per_day.map(d => (
                  <button key={d.day} type="button" onClick={() => setDay(day === d.day ? null : d.day)} aria-pressed={day === d.day}
                    className={`group flex h-full min-w-6 flex-1 cursor-pointer flex-col items-center justify-end rounded-t-[3px] ${day === d.day ? "bg-[#2a78d6]/10" : ""}`}
                    title={`${d.day}: ${d.views} sidvisningar, ${d.visits} besök – klicka för att visa dagen`}>
                    <span className={`whitespace-nowrap text-[10px] font-bold leading-3 tabular-nums ${d.views ? "text-slate-800" : "text-slate-400"}`}>{d.views}</span>
                    <span className="whitespace-nowrap text-[9px] leading-3 tabular-nums text-slate-400">{d.visits}</span>
                    <div className={`w-full rounded-t-[3px] ${day === d.day ? "bg-[#b7410e]" : day ? "bg-[#2a78d6]/40 group-hover:bg-[#1c5aa6]" : "bg-[#2a78d6] group-hover:bg-[#1c5aa6]"}`} style={{ height: d.views ? Math.max(3, Math.round(d.views / max * BAR_AREA)) : 0 }} />
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-1 flex justify-between text-[11px] text-slate-500"><span>{data.per_day[0]?.day}</span><span>högst {num(max)} per dag</span><span>{data.per_day.at(-1)?.day}</span></div>
          </Box>

          <div className="grid gap-3 lg:grid-cols-2">
            <Box title="Mest besökta sidor">
              <Bars rows={data.pages.map(p => ({ key: p.path, n: p.n }))} total={data.pages[0]?.n ?? 0}
                label={r => data.pages.find(p => p.path === r.key)?.title ?? r.key} />
            </Box>
            <Box title="Avsnitt på startsidan" note="Andel av startsidans visningar där besökaren scrollade till avsnittet.">
              {data.sections.length ? (
                <div className="space-y-1.5">
                  {data.sections.map(s => (
                    <div key={s.key} className="grid grid-cols-[minmax(0,1fr)_5rem_auto] items-center gap-3 text-sm">
                      <span className="truncate text-slate-700">{SECTIONS[s.key] ?? s.key}</span>
                      <span className="h-2 rounded-full bg-slate-100"><span className="block h-2 rounded-full bg-[#2a78d6]" style={{ width: `${Math.round((s.share ?? 0) * 100)}%` }} /></span>
                      <span className="w-10 text-right tabular-nums text-slate-700">{pct(s.share)}</span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-slate-500">Inget än.</p>}
            </Box>
            <Box title="Varifrån besökarna kommer" note={`Webbplatsen besöket började från. Direkt eller okänt: ${num(data.direct)}.`}>
              <Bars rows={data.referrers} total={data.referrers[0]?.n ?? 0} />
            </Box>
            <Box title="Land (ungefärligt)" note="Ur webbläsarens tidszon. Stad går inte att visa utan besökarens IP-adress, som inte sparas.">
              <Bars rows={data.countries} total={data.countries[0]?.n ?? 0} />
            </Box>
            <Box title="Webbläsarens språk"><Bars rows={data.languages} total={data.languages[0]?.n ?? 0} /></Box>
            <Box title="Enhet" note="Efter skärmens bredd."><Bars rows={data.devices} total={data.devices[0]?.n ?? 0} /></Box>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <Box title="Sökningar på webbplatsen" note={`${num(data.searches.total)} sökningar i artikelsökningen. Orden besökarna skriver, utan koppling till någon person.`}>
              <Bars rows={data.searches.top} total={data.searches.top[0]?.n ?? 0} />
            </Box>
            <Box title="Sökningar utan träff" note="Det besökarna söker efter som ingen artikel tar upp än – idéer till nya texter.">
              <Bars rows={data.searches.no_hits} total={data.searches.no_hits[0]?.n ?? 0} />
            </Box>
            <Box title="Delningar per kanal" note="Klick på delningsknapparna under artiklarna.">
              <Bars rows={data.clicks.share} total={data.clicks.share[0]?.n ?? 0} />
            </Box>
            <Box title="Besök från delade länkar" note="Besök som började i en länk som delats från sajten, per kanal. Märket tas bort ur adressfältet efter ankomsten.">
              <Bars rows={data.via} total={data.via[0]?.n ?? 0} />
            </Box>
            <Box title="Mest delade artiklar">
              <Bars rows={data.clicks.shared_pages} total={data.clicks.shared_pages[0]?.n ?? 0} />
            </Box>
            <Box title="Utgående länkar" note="Vilka webbplatser besökarna lämnar till (bara webbplatsen, inte hela adressen).">
              <Bars rows={data.clicks.outbound} total={data.clicks.outbound[0]?.n ?? 0} />
            </Box>
            <Box title="Vad läser man härnäst" note="Vägen från en sida till nästa inom samma besök. Minns bara i webbläsarens minne och försvinner vid omladdning.">
              <Bars rows={data.flow} total={data.flow[0]?.n ?? 0} />
            </Box>
            <Box title="Sidorna besöken börjar på" note="Där besökare som kommer utifrån först landar.">
              <Bars rows={data.entries.map(p => ({ key: p.path, n: p.n }))} total={data.entries[0]?.n ?? 0}
                label={r => data.entries.find(p => p.path === r.key)?.title ?? r.key} />
            </Box>
            <Box title="Språkbyten" note="Klick mellan den svenska och den engelska versionen av en artikel.">
              <Bars rows={data.clicks.language} total={data.clicks.language[0]?.n ?? 0} />
            </Box>
          </div>
        </>
      )}

      <div className="rounded-xl border border-amber-300/60 bg-amber-50 p-4 text-sm text-slate-700">
        <p className="font-semibold text-slate-900">Räkna inte dina egna besök</p>
        <p className="mt-1">
          Webbplatsen ser inga IP-adresser, så dina besök stängs av per webbläsare: öppna länken nedan en gång i varje
          webbläsare du använder (dator, mobil, surfplatta). Efter det räknas den inte. Lägg till <code>?rakna</code> i
          stället för att räkna den igen.
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <a href={STATS_OFF_URL} target="_blank" rel="noopener noreferrer" className="font-mono text-xs underline">{STATS_OFF_URL}</a>
          <button onClick={copy} className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white text-xs font-bold">{copied ? "Kopierad" : "Kopiera"}</button>
        </div>
      </div>
      {data && <p className="text-xs text-slate-500">Hämtad {new Date(data.computed_at).toLocaleString("sv-SE", { dateStyle: "medium", timeStyle: "short" })}. Besök är inte unika personer: samma person räknas igen vid nästa besök utifrån.</p>}
    </section>
  );
}
