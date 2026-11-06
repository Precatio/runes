"use client";

// The marking panel of the automatic analysis' review: Markera runorna (one click per rune, plain marks) and Runa för
// runa (each click tied to the next rune of the transliteration, lib/runeLinks.ts). The clicks themselves are made in
// the review image (AutoGrooveReview); this panel shows the transliteration as a strip, what the next click links to,
// and the actions, all undoable.
import { followingToken, LINKABLE, linksOf, markOfToken, nextToken, skippedOf, type MarkStep, type TransliterationState } from "@/lib/runeLinks";

export type MarkMode = "plain" | "linked";

interface Props {
  mode: MarkMode | null;
  steps: MarkStep[];
  onStepsChange: (steps: MarkStep[]) => void;
  translit: TransliterationState;
  section: string | null;
  onSectionChange: (s: string | null) => void;
  bindNext: boolean;
  onBindNextChange: (b: boolean) => void;
  hoverMark: number | null;
  onHoverMark: (k: number | null) => void;
  assigned: number; // rune slices that belong to a mark
  runeSlices: number;
  emptyMarks: number; // marks with no slice
}

export default function RuneLinkPanel({ mode, steps, onStepsChange, translit, section, onSectionChange, bindNext,
  onBindNextChange, hoverMark, onHoverMark, assigned, runeSlices, emptyMarks }: Props) {
  const nMarks = steps.filter(s => s.kind === "mark").length;
  const tr = translit.status === "ok" ? translit.data : null;
  const linked = mode === "linked" || linksOf(steps).length > 0;
  const tokens = tr ? tr.tokens.filter(t => section === null || t.section === section) : [];
  const next = tr ? nextToken(tr.tokens, steps, section) : null;
  const second = tr && next !== null ? followingToken(tr.tokens, next, section) : null;
  const owner = markOfToken(steps);
  const skipped = new Set(skippedOf(steps));
  const nLinkable = tokens.filter(t => LINKABLE.has(t.kind)).length;
  const nLinked = tokens.filter(t => owner.has(t.i)).length;
  const nextTok = tr && next !== null ? tr.tokens.find(t => t.i === next) : undefined;
  const hovered = new Set(hoverMark === null ? [] : [...owner].filter(([, k]) => k === hoverMark).map(([t]) => t));

  const undo = () => onStepsChange(steps.slice(0, -1));
  const skip = () => { if (next !== null) onStepsChange([...steps, { kind: "skip", token: next }]); };

  return (
    <div className="rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 text-xs text-slate-700 space-y-2">
      {linked ? (
        <div className="space-y-1.5">
          <p><strong>Runa för runa.</strong> Klicka en gång mitt på varje runa, i läsordning. Varje klick kopplas till
            runan som är markerad i remsan nedan, och skiljetecken hoppas över av sig själva. Syns inte runan, tryck
            på Hoppa över. Täcker ett klick två runor (en bindruna), tryck på Bindruna före klicket. Ångra tar bort det
            senaste, klick eller överhopp.</p>
          <p className="text-slate-500">Kopplingarna blir facit för runigenkänningen och en utgåva i TEI/EpiDoc med en
            3D-punkt per runa (Exportera). För musen över en runa i remsan eller en markering i bilden så visas den andra.
            Märk efter reliefen; gissa inte en runa som inte syns.</p>
        </div>
      ) : (
        <p><strong>Markera runorna.</strong> Klicka en gång mitt på varje runa, i läsordning. Du behöver inte veta
          vilken runa det är. Varje snitt som är märkt som runa hör sedan till den närmaste markeringen, så att
          måtten räknas med runan som enhet: varje runa väger lika mycket, hur många snitt den än har. Snitt långt
          från alla markeringar, till exempel i en runa du hoppat över, hör inte till någon runa och visas bleka.</p>
      )}

      {linked && tr && tr.sections.length > 1 && !tr.part && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="font-semibold">Sida:</span>
          {[null, ...tr.sections].map(s => (
            <button key={s ?? "alla"} type="button" onClick={() => onSectionChange(s)}
              className={`px-2 py-0.5 rounded-md border font-bold ${section === s ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-300"}`}>
              {s === null ? "Alla" : <span translate="no">{s}</span>}
            </button>
          ))}
        </div>
      )}

      {linked && tr && (
        <div translate="no" className="rounded-lg bg-white border border-orange-200 px-2 py-2 font-mono text-sm leading-8 flex flex-wrap items-center gap-x-0.5"
          onMouseLeave={() => onHoverMark(null)}>
          {tokens.map((t, idx) => {
            const k = owner.get(t.i);
            const isNext = mode === "linked" && (t.i === next || (bindNext && t.i === second));
            const wordGap = idx > 0 && tokens[idx - 1].word !== t.word && t.kind !== "divider" && tokens[idx - 1].kind !== "divider";
            if (!LINKABLE.has(t.kind)) {
              return <span key={t.i} className={`text-slate-400 ${wordGap ? "ml-2" : ""} ${t.kind === "divider" ? "mx-1" : ""}`}>{t.kind === "gap" ? "…" : t.orig}</span>;
            }
            const cls = hovered.has(t.i) ? "bg-slate-900 text-white border-slate-900"
              : isNext ? "bg-[#b7410e] text-white border-[#b7410e]"
              : k !== undefined ? "bg-orange-100 text-[#7c2d0b] border-orange-300"
              : skipped.has(t.i) ? "bg-slate-100 text-slate-400 border-slate-200 line-through"
              : "bg-white text-slate-700 border-slate-200";
            return (
              <span key={t.i} onMouseEnter={() => onHoverMark(k ?? null)}
                title={`${t.kind === "uncertain" ? "osäker läsning" : t.kind === "lost" ? "förlorad runa" : "runa"}${k !== undefined ? ` · klick ${k + 1}` : ""}`}
                className={`relative inline-flex flex-col items-center justify-center min-w-[1.4rem] h-7 px-0.5 rounded border ${cls} ${wordGap ? "ml-2" : ""}`}>
                <span className={t.kind === "uncertain" ? "italic" : ""}>{t.kind === "lost" ? (t.orig === "?" ? "?" : "–") : t.char}</span>
                {k !== undefined && <span className="absolute -bottom-2 text-[9px] leading-none text-slate-500">{k + 1}</span>}
              </span>
            );
          })}
        </div>
      )}

      {linked && translit.status === "loading" && <p className="text-slate-500">Hämtar translittereringen ur Rundata …</p>}
      {linked && translit.status === "error" && <p className="text-amber-900">Translittereringen kunde inte hämtas från analysmotorn.</p>}

      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold">
          {linked && tr
            ? `${nLinked} av ${nLinkable} runor kopplade · ${skipped.size} överhoppade · ${nMarks} klick`
            : `${nMarks} runor markerade · ${assigned} av ${runeSlices} runsnitt fördelade`}
          {emptyMarks > 0 ? ` · ${emptyMarks} markeringar utan snitt` : ""}
        </span>
        {mode === "linked" && tr && (
          <>
            <button type="button" disabled={next === null} onClick={skip}
              className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white font-bold disabled:opacity-40">Hoppa över (syns inte)</button>
            <button type="button" disabled={second === null} onClick={() => onBindNextChange(!bindNext)} aria-pressed={bindNext}
              title="Nästa klick täcker den markerade runan och runan efter"
              className={`px-2.5 py-1 rounded-lg border font-bold disabled:opacity-40 ${bindNext ? "bg-[#b7410e] text-white border-[#b7410e]" : "bg-white border-slate-300"}`}>Bindruna</button>
          </>
        )}
        <button type="button" disabled={!steps.length} onClick={undo}
          className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white font-bold disabled:opacity-40">Ångra senaste</button>
        <button type="button" disabled={!steps.length} onClick={() => onStepsChange([])}
          className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white font-bold disabled:opacity-40">Ta bort alla</button>
      </div>
      {mode === "linked" && tr && next === null && nLinkable > 0 && (
        <p className="text-emerald-800 font-semibold">Varje runa är kopplad eller överhoppad.</p>
      )}
      {mode === "linked" && nextTok?.bind_next && !bindNext && (
        <p className="text-slate-600">Rundata anger en bindruna här. Tryck på Bindruna om ett klick täcker båda runorna.</p>
      )}
      {!linked && nMarks > 0 && nMarks < 10 && (
        <p className="text-amber-900">Riktvärdet är minst 10 mätta runor för att beskriva en sten och 20 för att jämföra den med andra.</p>
      )}
    </div>
  );
}
