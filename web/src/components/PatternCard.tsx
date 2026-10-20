"use client";

import Link from "next/link";
import type { Significance } from "./Explain";
import { patternKey, usePatternArticles, useHideWritten } from "@/lib/patternArticles";

// A corpus pattern from the R analyses (src/r_findings.py)
export interface Pattern {
  key?: string;
  topic: string;
  status: string;
  text: string;
  note?: string | null;
  significance?: Significance;
  hypothesis?: string;
  test?: string;
  replicated?: boolean | null;
  small?: boolean;
}

/** What we see, a hypothesis and how it can be tested; the caveats folded away so that they do not drown the idea. */
export function PatternBody({ pt }: { pt: Pattern }) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-slate-800 leading-relaxed">
        {pt.hypothesis && <span className="font-semibold text-slate-900">Vad vi ser: </span>}{pt.text}
      </p>
      {pt.hypothesis && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2 text-sm leading-relaxed text-slate-800">
          <p><span className="font-semibold text-amber-900">Hypotes: </span>{pt.hypothesis}</p>
          {pt.test && <p className="mt-1"><span className="font-semibold text-amber-900">Så kan den prövas: </span>{pt.test}</p>}
        </div>
      )}
      {pt.note && (
        <details className="text-xs text-slate-500">
          <summary className="cursor-pointer font-semibold text-slate-600 hover:text-slate-900">Förbehåll och kontroller</summary>
          <p className="mt-1 leading-relaxed">{pt.note}</p>
        </details>
      )}
    </div>
  );
}

/** Whether the pattern holds in both halves of the corpus (split by parish), and whether the effect is small. */
export function PatternBadges({ pt }: { pt: Pattern }) {
  const pill = "px-2 py-0.5 rounded-lg border text-[11px] font-bold whitespace-nowrap";
  return (
    <>
      {pt.replicated === true && (
        <span className={`${pill} border-emerald-300 bg-emerald-50 text-emerald-800`}
              title="Mönstret håller i båda halvorna av korpusen, uppdelad per socken – ett tydligt mönster, inte ett utslag av några få socknar eller ristare.">
          ✓ Håller i båda halvorna
        </span>
      )}
      {pt.replicated === false && (
        <span className={`${pill} border-slate-300 bg-slate-50 text-slate-600`}
              title="Mönstret syns i hela korpusen men håller inte i båda halvorna, uppdelad per socken – en idé att pröva vidare.">
          Bara i en halva
        </span>
      )}
      {pt.small && (
        <span className={`${pill} border-sky-200 bg-sky-50 text-sky-800`}
              title="En liten men stabil förändring (under 10 procentenheter) – ett mönster, men ett litet.">
          liten effekt
        </span>
      )}
      <ArticleBadge pt={pt} />
    </>
  );
}

/** The article (or draft) written about the pattern, linked; nothing when there is none. */
export function ArticleBadge({ pt }: { pt: Pattern }) {
  const articles = usePatternArticles()[patternKey(pt)] ?? [];
  const pill = "px-2 py-0.5 rounded-lg border text-[11px] font-bold whitespace-nowrap border-[#b7410e]/30 bg-[#b7410e]/5 text-[#9a350b]";
  return (
    <>
      {articles.map(a => a.published ? (
        <Link key={a.slug} href={`/artiklar/${a.slug}`} className={`${pill} hover:underline`} title={`Artikel: ${a.title}`}>
          Artikel ✓
        </Link>
      ) : (
        <span key={a.slug} className={pill} title={`Utkast (opublicerat): ${a.title}`}>Utkast skrivet</span>
      ))}
    </>
  );
}

/** One click to hide the patterns we have already written about; the choice applies on every page that lists them. */
export function HideWrittenToggle({ written }: { written: number }) {
  const [hide, setHide] = useHideWritten();
  if (!written) return null;
  return (
    <button type="button" onClick={() => setHide(!hide)} aria-pressed={hide}
      className={`px-3 py-1.5 rounded-xl border text-xs font-bold ${hide ? "bg-[#b7410e] border-[#b7410e] text-white" : "bg-white border-slate-300 text-[#9a350b] hover:bg-[#b7410e]/5"}`}
      title="Mönster som vi redan skrivit en artikel eller ett utkast om. Valet gäller både Statistik och Forskningsluckor.">
      {hide ? `Visa de vi skrivit om (${written})` : `Dölj de vi skrivit om (${written})`}
    </button>
  );
}
