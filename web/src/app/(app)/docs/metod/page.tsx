"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import DOMPurify from "dompurify";
import { API_URL } from "@/lib/api";
import { KnownLimitations } from "@/components/KnownLimitations";

interface Methods { html: string; toc: { level: number; id: string; text: string }[]; source: string; limitations_version: string }
interface CodeEntry { path: string; url: string; summary: string; text: string }
interface Code { modules: CodeEntry[]; scripts: CodeEntry[]; r: CodeEntry[] }

const STEPS = [
  ["Skanningen", "3D-modellen läses in och centreras. Ingenting i den ändras; filens kontrollsumma (SHA-256) sparas."],
  ["Höjdkarta", "Den ristade sidan projiceras på ett plan till en höjdkarta (oftast 0,6 mm rutor)."],
  ["Stenytan utan ristningar", "En jämn referensyta räknas fram (morfologisk stängning, 20 mm). Allt som ligger tydligt under den – mer än 0,3 mm och tre gånger mätbruset – är spår."],
  ["Runor eller inte", "Spåren tunnas ut till mittlinjer och delas i streck. Bara raka, jämnbreda streck av runors längd som står i rader räknas som runor; slinglinjer, ornamentik och sprickor sorteras bort."],
  ["Tvärsnitt", "Var 3:e mm längs runstrecken skärs ett tvärsnitt vinkelrätt mot spåret, genom själva 3D-modellen."],
  ["Mått", "Spårväggarna anpassas till räta linjer mellan 20 och 80 % av djupet. Ur dem fås V-vinkel, djup, bredd, djup/bredd, asymmetri, bottenradie och ytråhet."],
  ["Kvalitet", "Snitt med dålig väggpassning, orimlig vinkel, för litet djup eller utan spårkant sorteras bort – skälen redovisas."],
  ["Stenens resultat", "Medelvärdet över runorna (runan som enhet), med konfidensintervall, metodversion, parametrar och de kända bristerna."],
];

export default function MethodsPage() {
  const [methods, setMethods] = useState<Methods | null>(null);
  const [code, setCode] = useState<Code | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/docs/methods`).then(r => (r.ok ? r.json() : Promise.reject())).then(setMethods)
      .catch(() => setError("Metodbeskrivningen kunde inte hämtas från analysmotorn."));
    fetch(`${API_URL}/api/docs/code`).then(r => (r.ok ? r.json() : null)).then(setCode).catch(() => setCode(null));
  }, []);

  const html = useMemo(() => (methods ? DOMPurify.sanitize(methods.html, { ADD_ATTR: ["target"] }) : ""), [methods]);

  return (
    <div className="w-full max-w-7xl mx-auto p-4 md:p-6">
      <div className="mb-6">
        <Link href="/docs" className="text-sm text-[#b7410e] hover:underline">← Om Vitki</Link>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-2 mb-2">Metodik och beräkningar</h1>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Så mäter Vitki huggspår och räknar statistik – varje steg, formel, parameter och validering, och vad metoden
          ännu inte klarar. Texten nedan är projektets metodbeskrivning (METHODS.md) och hämtas direkt från den kod
          som körs, så den är alltid aktuell. Hänvisningar till källkoden leder till GitHub.
        </p>
      </div>

      <section className="liquid-glass-island rounded-[24px] p-6 mb-6">
        <h2 className="text-lg font-bold text-slate-900 mb-3">Huggspårsmätningen i åtta steg</h2>
        <ol className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {STEPS.map(([title, text], i) => (
            <li key={title} className="flex gap-3 text-sm text-slate-700">
              <span className="shrink-0 w-7 h-7 rounded-full bg-[#b7410e] text-white font-bold flex items-center justify-center text-xs">{i + 1}</span>
              <span><strong className="text-slate-900">{title}.</strong> {text}</span>
            </li>
          ))}
        </ol>
        <p className="text-xs text-slate-500 mt-4">
          Urvalet görs med samma regler på varje sten och beror inte på vem som mäter, så mätningen kan upprepas exakt.
          Reglerna är själva val – de redovisas nedan (avsnitt 1c) tillsammans med hur robusta resultaten är (1e) och
          de kända bristerna (18).
        </p>
      </section>

      {error && <p className="text-sm text-red-700 font-semibold">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6">
        {methods && (
          <nav className="hidden lg:block">
            <div className="sticky top-4 max-h-[calc(100vh-8rem)] overflow-y-auto text-sm space-y-1 pr-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">Innehåll</p>
              {methods.toc.map(t => (
                <a key={t.id} href={`#${t.id}`}
                  className={`block hover:text-[#b7410e] ${t.level === 2 ? "font-semibold text-slate-800 mt-2" : "pl-3 text-slate-600"}`}>
                  {t.text}
                </a>
              ))}
              <a href="#kod" className="block font-semibold text-slate-800 mt-2 hover:text-[#b7410e]">Moduler och skript</a>
            </div>
          </nav>
        )}

        <div className="min-w-0">
          {methods ? (
            <article className="liquid-glass-island rounded-[24px] p-6 md:p-8">
              <div className="methods-doc" dangerouslySetInnerHTML={{ __html: html }} />
              <p className="text-xs text-slate-500 mt-8">
                Källa: <a className="underline" href={methods.source} target="_blank" rel="noopener noreferrer">METHODS.md</a> ·
                kända brister version {methods.limitations_version}
              </p>
            </article>
          ) : !error && <p className="text-sm text-slate-500">Hämtar metodbeskrivningen …</p>}

          {code && (
            <section id="kod" className="liquid-glass-island rounded-[24px] p-6 md:p-8 mt-6 scroll-mt-4">
              <h2 className="text-xl font-bold text-slate-900 mb-1">Moduler och skript</h2>
              <p className="text-sm text-slate-600 mb-4">
                Varje del av beräkningarna beskriver sig själv i koden; beskrivningarna nedan hämtas därifrån.
              </p>
              {([["Analysmoduler (Python)", code.modules], ["Skript för studier och omräkning", code.scripts], ["Statistik i R", code.r]] as const).map(([title, list]) => (
                <div key={title} className="mb-6">
                  <h3 className="font-bold text-slate-900 mb-2">{title}</h3>
                  <ul className="space-y-1.5">
                    {list.map(e => (
                      <li key={e.path}>
                        <details className="text-sm">
                          <summary className="cursor-pointer">
                            <a href={e.url} target="_blank" rel="noopener noreferrer" className="font-mono text-[13px] text-[#b7410e] hover:underline">{e.path}</a>
                            <span className="text-slate-600"> – {e.summary}</span>
                          </summary>
                          <pre className="mt-2 ml-4 whitespace-pre-wrap text-xs text-slate-700 bg-slate-50 rounded-lg p-3">{e.text}</pre>
                        </details>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </section>
          )}

          <KnownLimitations contexts={["grooves", "auto", "comparison", "attribution", "statistics", "research", "ai", "rundata", "software", "r"]} />
        </div>
      </div>
    </div>
  );
}
