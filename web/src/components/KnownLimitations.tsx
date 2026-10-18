"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { API_URL } from "@/lib/api";

interface Limitation { key: string; title: string; text: string; short: string; needed: string; contexts: string[] }
interface LimitationList { version: string; items: Limitation[] }

// Analysis pages that get a pointer to the known limitations in the documentation
const ANALYSIS_ROUTES = ["/3d", "/stenanalys", "/jamfor", "/korpus", "/synthesis", "/statistik", "/luckor", "/inskrifter",
  "/karta", "/2d", "/phonetics", "/rapporter", "/report", "/oversikt"];

const cache = new Map<string, Promise<LimitationList | null>>();
function load(contexts: string[]): Promise<LimitationList | null> {
  const key = contexts.join(",");
  if (!cache.has(key)) {
    cache.set(key, fetch(`${API_URL}/api/limitations?contexts=${encodeURIComponent(key)}`)
      .then(r => (r.ok ? r.json() : null)).catch(() => null));
  }
  return cache.get(key)!;
}

export function KnownLimitations({ contexts }: { contexts: string[] }) {
  const [data, setData] = useState<LimitationList | null>(null);
  const key = contexts.join(",");
  useEffect(() => {
    let cancelled = false;
    load(key.split(",")).then(d => { if (!cancelled) setData(d); });
    return () => { cancelled = true; };
  }, [key]);
  if (!data || data.items.length === 0) return null;
  return (
    <section className="mt-8 rounded-2xl border border-amber-200 bg-amber-50/70 px-5 py-4 text-sm text-slate-700">
      <h3 className="font-bold text-amber-900">Kända brister i metoden – läs innan du drar slutsatser</h3>
      <p className="text-xs text-slate-500 mt-0.5">
        Samma förteckning står i varje rapport och sparas med varje mätning (version {data.version}, METHODS.md avsnitt 18).
        Klicka på en punkt för detaljer och vad som behövs för att åtgärda den.
      </p>
      <ul className="mt-3 space-y-1.5">
        {data.items.map(x => (
          <li key={x.key}>
            <details>
              <summary className="cursor-pointer font-semibold text-slate-800">{x.title}</summary>
              <p className="mt-1 ml-4 text-slate-700">{x.text}</p>
              {x.needed && <p className="mt-1 ml-4 text-xs text-slate-500"><strong>Behövs:</strong> {x.needed}</p>}
            </details>
          </li>
        ))}
      </ul>
    </section>
  );
}

// A short pointer to the documentation, where methods, caveats and known limitations are described
export function DocsNote({ anchor, children }: { anchor: string; children: React.ReactNode }) {
  return (
    <p className="text-xs text-slate-500">
      {children}{" "}
      <Link href={`/docs/metod#${anchor}`} className="text-[#b7410e] font-semibold hover:underline">Läs i dokumentationen →</Link>
    </p>
  );
}

// Under every analysis page: one line pointing to the known limitations in the documentation (the full list
// is in the documentation and in every report)
export default function RouteLimitations() {
  const path = usePathname() ?? "";
  if (!ANALYSIS_ROUTES.some(r => path === r || path.startsWith(`${r}/`))) return null;
  return (
    <div className="mt-8 border-t border-slate-900/5 pt-3">
      <DocsNote anchor="18-kända-brister">Metoderna har kända brister som gäller också här.</DocsNote>
    </div>
  );
}
