"use client";

// Bedrock at the stone's site (SGU) and the inscription's language traits, shared by the pages that
// compare stones and carvers.
import { useState } from "react";
import { API_URL } from "@/lib/api";

export interface Geology {
  signum: string; place: string; material: string; material_families: string[];
  at_site: { rock: string; unit: string; minerals: string; texture: string; colour: string } | null;
  radius_km: number; points_with_data: number; sample_points: number;
  rocks_nearby: [string, number][]; families_nearby: Record<string, number>;
  verdict: "på platsen" | "i närheten" | "inte i närheten" | "okänt"; text: string; source: string; caveat: string;
}

export interface LanguageTrait { trait: string; group: "ljud" | "bruk"; label: string; definition: string; value: string }
export interface LanguageComparison {
  rows: { trait: string; group: string; label: string; definition: string; stone: string; carver_common: string; share: number; n: number; agrees: boolean }[];
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
            <p className="mt-1">Inom {data.radius_km} km ({data.points_with_data} provpunkter): {data.rocks_nearby.map(([r, n]) => `${r} (${n})`).join(", ")}</p>
          )}
        </>
      )}
      <p className="mt-1 opacity-80">{data.caveat} Källa: {data.source}</p>
    </div>
  );
}

export function LanguageTraits({ signum, carver }: { signum: string; carver?: string }) {
  const [data, setData] = useState<{ traits: LanguageTrait[]; comparison?: LanguageComparison } | null>(null);
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
      {data.traits.length === 0 && <li className="text-slate-500">Inga bestämbara språkdrag (för kort eller skadad text).</li>}
      {data.traits.map(t => (
        <li key={t.trait} title={t.definition}>
          <span className="text-slate-500">{t.group === "ljud" ? "Ljud" : "Bruk"}:</span> <span className="font-semibold">{t.label}</span> – {t.value}
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
        <table className="w-full">
          <thead><tr className="text-left text-slate-500"><th className="py-0.5">Drag</th><th>Stenen</th><th>Hos ristaren</th><th></th></tr></thead>
          <tbody>
            {comparison.rows.map(r => (
              <tr key={r.trait} className="border-t border-slate-900/5" title={r.definition}>
                <td className="py-0.5">{r.label} <span className="text-slate-400">({r.group === "ljud" ? "ljud" : "bruk"})</span></td>
                <td>{r.stone}</td>
                <td>{r.carver_common} <span className="text-slate-400">({Math.round(r.share * 100)} % som stenen, n={r.n})</span></td>
                <td className={r.agrees ? "text-emerald-700 font-bold" : "text-amber-700 font-bold"}>{r.agrees ? "✓" : "!"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="text-[10px] text-slate-500 mt-1">Håll muspekaren över ett drag för definitionen. Ljud = fonetisk stil, bruk = formler och stavning.</p>
    </div>
  );
}
