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
  // The pattern registry (src/pattern_registry.py): when the pattern first appeared, and "nytt" / "ändrat" the first
  // 30 days after it appeared or its status changed
  first_seen?: string | null;
  new?: "nytt" | "obekräftat" | "ändrat";
  previous_status?: string;
  status_changed?: string;
  // The robustness ladder (src/robustness.py, r/robustness.R) and the common Benjamini–Hochberg over all patterns
  ladder?: Ladder;
  q_global?: number | null;
  confirmed?: boolean | null;
}

export interface LadderRung {
  key: string;
  label: string;
  holds: boolean | null;
  or?: number | null;
  ci?: number[] | null;
  p?: number | null;
  n?: number | null;
  error?: string;
  skipped?: string;
  without?: string;
  n_provinces?: number;
  flips?: string[];
  singular?: boolean;
}

export interface Ladder {
  n: number;
  k: number;
  direction: number;
  p: number;
  rungs: LadderRung[];
  passed: number;
  tested: number;
  halves: boolean;
  first_fail: string | null;
  time: boolean;
  note?: string | null;
  effect?: { share_lo?: number; share_hi?: number; diff?: number; diff_ci?: number[]; error?: string } | null;
  check?: { uniformity_p?: number; dispersion_p?: number; spatial_p?: number; ok?: boolean; error?: string } | null;
  coding?: { var: string; n_sim: number; share_holds: number; or_median: number; or_range: number[]; ppv: number[]; npv: number[]; error?: string } | null;
}

const pct = (x?: number | null) => (x == null ? "–" : `${Math.round(x * 100)} %`);
const pp = (x?: number | null) => (x == null ? "–" : `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(Math.round(x * 1000) / 10).toLocaleString("sv-SE")}`);
const num = (x?: number | null, d = 2) => (x == null ? "–" : x.toLocaleString("sv-SE", { maximumFractionDigits: d, minimumFractionDigits: d }));
const pv = (x?: number | null) => (x == null ? "–" : x < 0.001 ? "< 0,001" : x.toLocaleString("sv-SE", { maximumFractionDigits: 3 }));

/** The ladder rung by rung: the same checks for every pattern that can be recounted stone by stone. */
export function LadderDetails({ pt }: { pt: Pattern }) {
  const l = pt.ladder;
  if (!l) return null;
  const e = l.effect && !l.effect.error ? l.effect : null;
  const c = l.check && !l.check.error ? l.check : null;
  const cod = l.coding && !l.coding.error ? l.coding : null;
  const [lo, hi] = l.time ? ["omkring 1000", "omkring 1100"] : ["utan", "med"];
  return (
    <details className="text-xs text-slate-600">
      <summary className="cursor-pointer font-semibold text-slate-600 hover:text-slate-900">
        Robusthetstrappan: håller i {l.passed} av {l.tested} steg
      </summary>
      <div className="mt-2 space-y-2 leading-relaxed">
        <p>
          Samma kontroller för varje mönster som kan räknas om sten för sten ({l.n} stenar, {l.k} med draget). Ett steg
          håller när skillnaden går åt samma håll som i den justerade modellen och p är under 0,05.
          {l.note && <> Jämförelsen: {l.note}.</>}
        </p>
        {e && e.diff != null && (
          <p>
            <span className="font-semibold text-slate-800">Skillnaden i procentenheter: </span>
            {pp(e.diff)} procentenheter ({e.diff_ci ? `${pp(e.diff_ci[0])} till ${pp(e.diff_ci[1])}` : "–"}): {pct(e.share_lo)} {lo} mot {pct(e.share_hi)} {hi},
            med landskap och tid konstanta (medelvärdet över stenarna).
          </p>
        )}
        <ul className="space-y-0.5">
          {l.rungs.map(r => (
            <li key={r.key} className="flex flex-wrap gap-x-2">
              <span className={`w-4 font-bold ${r.holds === true ? "text-emerald-700" : r.holds === false ? "text-red-700" : "text-slate-400"}`}>
                {r.holds === true ? "✓" : r.holds === false ? "✗" : "–"}
              </span>
              <span className="text-slate-800">{r.label}{r.without ? ` (sämst utan ${r.without})` : ""}{r.flips?.length ? ` – riktningen vänder utan ${r.flips.join(", ")}` : ""}</span>
              <span className="text-slate-500">
                {r.error ? "kunde inte räknas" : r.skipped ? r.skipped
                  : `oddskvot ${num(r.or)}${r.ci ? ` (${num(r.ci[0])}–${num(r.ci[1])})` : ""}, p ${pv(r.p)}${r.n ? `, ${r.n} stenar` : ""}${r.singular ? ", slumpeffekten skattas till noll" : ""}`}
              </span>
            </li>
          ))}
        </ul>
        {pt.q_global != null && (
          <p>
            <span className="font-semibold text-slate-800">Alla mönster samtidigt: </span>
            q {pv(pt.q_global)} efter en gemensam Benjamini–Hochberg-justering över alla mönster på sidan
            {pt.q_global < 0.05 ? " – mönstret klarar att jämföras med alla de andra." : " – med så många mönster prövade kan det vara ett av de falska larmen."}
          </p>
        )}
        {cod && (
          <p>
            <span className="font-semibold text-slate-800">Kodningsfel: </span>
            {cod.var === "y" ? "Utfallet" : "Jämförelsen"} kodas av regler. Med reglernas fel enligt handkodningen
            ({cod.ppv[0]} av {cod.ppv[0] + cod.ppv[1]} rätt bland regelns ja, {cod.npv[0]} av {cod.npv[0] + cod.npv[1]} bland dess nej)
            förda vidare i {cod.n_sim} omräkningar håller mönstret i {pct(cod.share_holds)} av dem (oddskvot {num(cod.or_median)}, {num(cod.or_range[0])}–{num(cod.or_range[1])}).
          </p>
        )}
        {c && (
          <p>
            <span className="font-semibold text-slate-800">Modellkontroll (DHARMa): </span>
            {c.ok ? "residualerna ser ut som de ska" : [
              (c.uniformity_p ?? 1) < 0.05 && "residualerna är inte jämnt fördelade",
              (c.dispersion_p ?? 1) < 0.05 && "spridningen är större eller mindre än modellen väntar",
              (c.spatial_p ?? 1) < 0.05 && "det finns ett kvarvarande rumsligt mönster – grannstenar liknar varandra mer än modellen förklarar",
            ].filter(Boolean).join("; ")}.
          </p>
        )}
      </div>
    </details>
  );
}

/** What we see, a hypothesis and how it can be tested; the caveats folded away so that they do not drown the idea. */
export function PatternBody({ pt }: { pt: Pattern }) {
  return (
    <div className="space-y-2">
      {pt.text && (
        <p className="text-sm text-slate-800 leading-relaxed">
          {pt.hypothesis && <span className="font-semibold text-slate-900">Vad vi ser: </span>}{pt.text}
        </p>
      )}
      {pt.hypothesis && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2 text-sm leading-relaxed text-slate-800">
          <p><span className="font-semibold text-amber-900">Hypotes: </span>{pt.hypothesis}</p>
          {pt.test && <p className="mt-1"><span className="font-semibold text-amber-900">Så kan den prövas: </span>{pt.test}</p>}
        </div>
      )}
      <LadderDetails pt={pt} />
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
      <NewBadge pt={pt} />
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
      {pt.ladder && (
        <span className={`${pill} ${pt.ladder.passed === pt.ladder.tested ? "border-emerald-300 bg-emerald-50 text-emerald-800"
          : pt.ladder.passed >= pt.ladder.tested - 1 ? "border-amber-200 bg-amber-50 text-amber-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}
              title="Robusthetstrappan: hur många av de gemensamma kontrollerna mönstret klarar (rått, justerat, ristare, socken, plats, båda halvorna, utan ett landskap i taget, utan flyttade stenar). Se Robusthetstrappan under mönstret.">
          Robust {pt.ladder.passed}/{pt.ladder.tested}
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

/** "Nytt" the first 30 days after a confirmed pattern appeared in the analyses, "Nytt, obekräftat" before it is
 * confirmed (both halves and the common BH), "Ändrat" after its status changed. */
export function NewBadge({ pt }: { pt: Pattern }) {
  if (!pt.new) return null;
  const pill = "px-2 py-0.5 rounded-lg border text-[11px] font-bold whitespace-nowrap";
  // The date as numbers (2026-10-27), not a month name: the translator masks numbers, so one catalog entry serves
  // every month
  const day = (d?: string | null) => (d ? d.slice(0, 10) : "");
  if (pt.new === "obekräftat") return (
    <span className={`${pill} border-dashed border-violet-300 bg-white text-violet-700`}
          title={`Mönstret dök upp i analyserna ${day(pt.first_seen)} men är inte bekräftat: det håller inte i båda halvorna av korpusen, klarar inte den gemensamma justeringen över alla mönster, eller går inte att pröva i halvor.`}>
      Nytt, obekräftat
    </span>
  );
  return pt.new === "nytt" ? (
    <span className={`${pill} border-violet-300 bg-violet-50 text-violet-800`}
          title={`Mönstret dök upp i analyserna ${day(pt.first_seen)} och är bekräftat i båda halvorna av korpusen. Det märks som nytt i 30 dagar.`}>
      Nytt
    </span>
  ) : (
    <span className={`${pill} border-violet-200 bg-white text-violet-700`}
          title={`Statusen ändrades ${day(pt.status_changed)}.${pt.previous_status ? ` Förut: ${pt.previous_status}.` : ""}`}>
      Ändrat
    </span>
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
