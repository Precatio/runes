"use client";

// Bedrock at the stone's site (SGU) and the inscription's language traits, shared by the pages that
// compare stones and carvers, and where the literature register mentions the stone.
import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";
import ExportTable from "@/components/ExportTable";

export interface Geology {
  signum: string; place: string; material: string; material_families: string[];
  at_site: { rock: string; unit: string; minerals: string; texture: string; colour: string } | null;
  radius_km: number; points_with_data: number; sample_points: number;
  rocks_nearby: { rock: string; n: number }[]; families_nearby: Record<string, number>;
  verdict: "på platsen" | "i närheten" | "inte i närheten" | "okänt"; text: string; source: string; caveat: string;
}

const GROUP_LABEL: Record<string, string> = { ljud: "Ljud", bruk: "Bruk", skrift: "Skrift" };

export interface LanguageTrait { trait: string; group: "ljud" | "bruk" | "skrift"; label: string; definition: string; value: string }
export interface LanguageComparison {
  rows: { trait: string; group: string; label: string; definition: string; stone: string; carver_common: string; share: number; n: number; agrees: boolean;
    repeats?: boolean; region_share?: number; lr?: number }[];
  agree: number; comparable: number; text: string;
}

const enc = (s: string) => encodeURIComponent(s);

const VERDICT_STYLE: Record<Geology["verdict"], string> = {
  "på platsen": "bg-emerald-50 border-emerald-200 text-emerald-900",
  "i närheten": "bg-sky-50 border-sky-200 text-sky-900",
  "inte i närheten": "bg-amber-50 border-amber-300 text-amber-900",
  "okänt": "bg-slate-50 border-slate-200 text-slate-700",
};

export function GeologyBox({ signum, compact = false }: { signum: string; compact?: boolean }) {
  const [data, setData] = useState<Geology | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/research/geology/${enc(signum)}`);
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Berggrunden kunde inte hämtas.");
      setData(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Berggrunden kunde inte hämtas.");
    } finally {
      setBusy(false);
    }
  };
  if (!data) {
    return (
      <div className="text-xs">
        <button onClick={load} disabled={busy} className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 font-semibold hover:border-slate-900 disabled:opacity-50">
          {busy ? "Hämtar berggrund från SGU …" : "Jämför bergarten med berggrunden (SGU)"}
        </button>
        {error && <span className="ml-2 text-red-700">{error}</span>}
      </div>
    );
  }
  return (
    <div className={`rounded-xl border px-3 py-2 text-xs ${VERDICT_STYLE[data.verdict]}`}>
      <div className="font-bold uppercase tracking-wider text-[10px] mb-0.5">Berggrund: {data.verdict}</div>
      <p>{data.text}</p>
      {!compact && (
        <>
          {data.at_site && <p className="mt-1">På platsen: {data.at_site.rock}{data.at_site.texture ? `, ${data.at_site.texture}` : ""} – {data.at_site.unit}</p>}
          {data.rocks_nearby.length > 0 && (
            <p className="mt-1">Inom {data.radius_km} km ({data.points_with_data} provpunkter): {data.rocks_nearby.map(({ rock, n }) => `${rock} (${n})`).join(", ")}</p>
          )}
        </>
      )}
      <p className="mt-1 opacity-80">{data.caveat} Källa: {data.source}</p>
    </div>
  );
}

export function LanguageTraits({ signum, carver }: { signum: string; carver?: string }) {
  const [data, setData] = useState<{ traits: LanguageTrait[]; comparison?: LanguageComparison;
    categories?: { key: string; label: string; definition: string }[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const load = async () => {
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/research/language/${enc(signum)}${carver ? `?carver=${enc(carver)}` : ""}`);
      if (res.ok) setData(await res.json());
    } finally {
      setBusy(false);
    }
  };
  if (!data) {
    return (
      <button onClick={load} disabled={busy} className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold hover:border-slate-900 disabled:opacity-50">
        {busy ? "Läser språkdrag …" : carver ? `Jämför språkdrag med ${carver}` : "Visa språkdrag"}
      </button>
    );
  }
  if (data.comparison) return <LanguageTable comparison={data.comparison} />;
  return (
    <ul className="text-xs space-y-1">
      {data.categories && data.categories.length > 0 && (
        <li className="mb-1">
          <span className="text-slate-500">Inskriftstyp:</span>{" "}
          {data.categories.map((c, i) => <span key={c.key} title={c.definition} className="font-semibold">{i > 0 && ", "}{c.label}</span>)}
        </li>
      )}
      {data.traits.length === 0 && <li className="text-slate-500">Inga bestämbara språkdrag (för kort eller skadad text).</li>}
      {data.traits.map(t => (
        <li key={t.trait} title={t.definition}>
          <span className="text-slate-500">{GROUP_LABEL[t.group] ?? t.group}:</span> <span className="font-semibold">{t.label}</span> – {t.value}
        </li>
      ))}
    </ul>
  );
}

export function LanguageTable({ comparison }: { comparison: LanguageComparison }) {
  return (
    <div className="text-xs">
      <p className="mb-1.5">{comparison.text}</p>
      {comparison.rows.length > 0 && (
        <ExportTable><table className="w-full">
          <thead><tr className="text-left text-slate-500"><th className="py-0.5">Drag</th><th>Stenen</th><th>Hos ristaren</th>
            {comparison.rows.some(r => r.region_share != null) && <th>I landskapet</th>}<th></th></tr></thead>
          <tbody>
            {comparison.rows.map(r => (
              <tr key={r.trait} className={`border-t border-slate-900/5 ${r.repeats ? "text-slate-400" : ""}`} title={r.definition}>
                <td className="py-0.5">{r.label} <span className="text-slate-400">({(GROUP_LABEL[r.group] ?? r.group).toLowerCase()})</span>
                  {r.repeats && <span className="ml-1 text-[10px] italic">upprepar ett annat drag, räknas inte</span>}</td>
                <td>{r.stone}</td>
                <td>{r.carver_common} <span className="text-slate-400">({Math.round(r.share * 100)} % som stenen, n={r.n})</span></td>
                {comparison.rows.some(x => x.region_share != null) && <td>{r.region_share != null ? `${Math.round(r.region_share * 100)} %` : "–"}</td>}
                <td className={r.repeats ? "text-slate-400" : r.agrees ? "text-emerald-700 font-bold" : "text-amber-700 font-bold"}>{r.agrees ? "✓" : "!"}</td>
              </tr>
            ))}
          </tbody>
        </table></ExportTable>
      )}
      <p className="text-[10px] text-slate-500 mt-1">
        Håll muspekaren över ett drag för definitionen. Ljud = fonetisk stil, bruk = formler och stavning. Drag som upprepar ett
        annat (t.ex. stungna runor bredvid stungen i, själsbön bredvid bön) visas men räknas inte, och ett drag som stämmer med
        ristaren men är lika vanligt i hela landskapet säger lite om just den ristaren.
      </p>
    </div>
  );
}

// The literature register (src/literature.py): where dissertations and editions mention the stone
interface LitSnippet { page: string; text: string; entry?: boolean }
interface LitWork {
  work: { id: string; author: string; year: number; title: string; kind: string; series?: string; url?: string; access: string };
  pages: string[]; n: number; snippets: LitSnippet[]; entry_pages: string[]; list_pages: string[];
}
interface LitCatalogWork { id: string; author: string; year: number; title: string; access: string; indexed: boolean; n_stones: number; url?: string }

const ACCESS: Record<string, string> = { "öppen": "fri fulltext", "sverige": "fulltext inom Sverige", "tryck": "bara tryckt" };

/** Where the dissertations and editions in the register mention the stone, with printed page and a short excerpt. */
export function LiteratureBox({ signum }: { signum: string }) {
  const [data, setData] = useState<{ works: LitWork[]; n_indexed: number } | null>(null);
  const [catalog, setCatalog] = useState<LitCatalogWork[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/research/literature/${enc(signum)}`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error("Litteraturen kunde inte hämtas."))))
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [signum]);
  const loadCatalog = () => {
    if (catalog) return;
    fetch(`${API_URL}/api/research/literature`).then(r => r.json()).then(d => setCatalog(d.works)).catch(() => setCatalog([]));
  };
  if (error) return <p className="text-xs text-red-700">{error}</p>;
  if (!data) return <p className="text-xs text-slate-500">Söker i litteraturregistret …</p>;
  return (
    <div className="space-y-3 text-sm">
      {data.works.length === 0 ? (
        <p className="text-xs text-slate-600">Ingen av de {data.n_indexed} indexerade avhandlingarna och utgåvorna nämner stenen.</p>
      ) : (
        <ul className="space-y-2">
          {data.works.map(w => (
            <li key={w.work.id} className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2">
              <div className="flex flex-wrap items-baseline gap-x-2">
                <span className="font-semibold text-slate-900" translate="no">{w.work.author.split(",")[0]} {w.work.year}</span>
                <span className="text-xs text-slate-600 italic" translate="no">{w.work.title}</span>
                <span className="text-[11px] text-slate-500">{w.work.kind}</span>
              </div>
              <div className="text-xs text-slate-700 mt-0.5">
                {w.pages.length > 0 ? "s. " : ""}{w.pages.map((p, i) => (
                  <span key={p}>{i > 0 && ", "}<span className={w.entry_pages.includes(p) ? "font-bold" : ""}
                    title={w.entry_pages.includes(p) ? "Stenens egen artikel i utgåvan" : undefined}>{p}</span></span>
                ))}
                {w.entry_pages.length > 0 && <span className="text-slate-500"> (fetstil: stenens egen artikel)</span>}
                {w.list_pages.length > 0 && <span className="text-slate-500">{w.pages.length ? "; " : ""}i register eller listor s. {w.list_pages.join(", ")}</span>}
                {w.work.url && <> · <a href={w.work.url} target="_blank" rel="noreferrer" className="text-[#b7410e] underline">{ACCESS[w.work.access] ?? "verket"}</a></>}
              </div>
              {w.snippets.length > 0 && <details className="mt-1">
                <summary className="cursor-pointer text-xs font-semibold text-slate-600 hover:text-slate-900">Utdrag ({Math.min(w.snippets.length, w.n)} av {w.n})</summary>
                <ul className="mt-1 space-y-1">
                  {w.snippets.map((s, i) => (
                    <li key={i} className="text-xs text-slate-600 leading-relaxed"><span className="font-semibold text-slate-500">s. {s.page}: </span><span translate="no">{s.text}</span></li>
                  ))}
                </ul>
              </details>}
            </li>
          ))}
        </ul>
      )}
      <details onToggle={e => { if ((e.target as HTMLDetailsElement).open) loadCatalog(); }} className="text-xs text-slate-500">
        <summary className="cursor-pointer font-semibold text-slate-600 hover:text-slate-900">Vilka verk finns i registret?</summary>
        {catalog && (
          <ul className="mt-1 space-y-0.5">
            {catalog.map(c => (
              <li key={c.id}>
                <span className={c.indexed ? "text-emerald-700 font-semibold" : "text-slate-400"}>{c.indexed ? "✓" : "○"}</span>{" "}
                <span translate="no">{c.author.split(",")[0]} {c.year}, <span className="italic">{c.title}</span></span>
                {c.indexed ? ` – ${c.n_stones} stenar` : ` – inte indexerad (${ACCESS[c.access] ?? c.access})`}
              </li>
            ))}
          </ul>
        )}
      </details>
      <p className="text-[11px] text-slate-500">Korta utdrag med tryckt sida ur appens litteraturregister. Ett signum kan nämnas i förbigående; läs sidan innan något citeras.</p>
    </div>
  );
}
