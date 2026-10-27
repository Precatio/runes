// The automatic analysis's options on the 3D page: what is measured, staveless runes, how runes are told from
// ornament, the Vitki protocol, the parameters, facit mode, the run button and the result's status line.
import type { AutoAnalysisResult } from "@/lib/mesh";
import { allStaveless, someStaveless } from "@/lib/staveless";

export interface AutoAnalysisOptionsProps {
  autoMeasure: "runes" | "ornament";
  setAutoMeasure: (v: "runes" | "ornament") => void;
  facitMode: boolean;
  setFacitMode: (v: boolean) => void;
  autoStaveless: boolean;
  setAutoStaveless: (v: boolean) => void;
  runeTypes: string | null;
  useProtocol: boolean;
  setUseProtocol: (v: boolean) => void;
  autoSpacing: number;
  setAutoSpacing: (v: number) => void;
  autoSensitivity: number;
  setAutoSensitivity: (v: number) => void;
  autoMaxWidth: number;
  setAutoMaxWidth: (v: number) => void;
  canRun: boolean;
  autoBusy: boolean;
  onRun: () => void;
  autoError: string | null;
  autoResult: AutoAnalysisResult | null;
}

export default function AutoAnalysisOptions({
  autoMeasure, setAutoMeasure, facitMode, setFacitMode, autoStaveless, setAutoStaveless, runeTypes, useProtocol,
  setUseProtocol, autoSpacing, setAutoSpacing, autoSensitivity, setAutoSensitivity, autoMaxWidth, setAutoMaxWidth,
  canRun, autoBusy, onRun, autoError, autoResult,
}: AutoAnalysisOptionsProps) {
  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white/70 p-3">
      <div>
        <div className="text-[11px] font-bold text-slate-500 mb-1">Vad ska mätas?</div>
        <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Vad ska mätas">
          {([["runes", "Runor"], ["ornament", "Ornamentik"]] as const).map(([v, name]) => (
            <button key={v} type="button" role="radio" aria-checked={autoMeasure === v} disabled={facitMode}
              onClick={() => setAutoMeasure(v)}
              className={`py-1.5 rounded-lg text-xs font-bold border ${autoMeasure === v && !facitMode ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-600 border-slate-300"} disabled:opacity-40`}>
              {name}</button>
          ))}
        </div>
      </div>
      {autoMeasure === "runes" && !facitMode && (
        <label className="flex items-start gap-2 text-[11px] text-slate-600">
          <input type="checkbox" checked={autoStaveless} onChange={e => setAutoStaveless(e.target.checked)} className="mt-0.5" />
          <span><strong>Stavlösa runor</strong> (hälsingerunor): korta streck utan huvudstav delas upp i runor efter
            var de står längs slingan.{" "}
            {allStaveless(runeTypes)
              ? "Påslaget, eftersom Rundata anger stavlösa runor för stenen."
              : someStaveless(runeTypes)
                ? "Rundata anger stavlösa runor bara för en del av runorna. Slå på läget om de flesta är stavlösa."
                : "Slå på det om stenen har stavlösa runor."}{" "}
            Indelningen är ett ungefärligt förslag; vill du ha den exakt, markera runorna för hand i granskningen.</span>
        </label>
      )}
      <details className="text-[11px] text-slate-600 leading-relaxed" open>
        <summary className="cursor-pointer font-bold text-slate-700">Så avgör Vitki vad som är runor</summary>
        <ol className="mt-1.5 list-decimal pl-4 space-y-1">
          <li>Vitki letar först upp <strong>runslingorna</strong> – banden som texten står i – på stenens djupbild.
            För de öppna skanningarna används slingor som har ritats och granskats för hand; annars föreslår
            slingmodellen dem.</li>
          <li>Ett tvärsnitt räknas som <strong>runa</strong> om det ligger inne i en slinga och går tvärs eller snett
            över den. Spår som löper längs slingan är <strong>slingkanter</strong> och mäts inte.</li>
          <li>Spår <strong>utanför slingorna</strong> räknas som ornamentik. Väljer du Ornamentik mäts de i stället.</li>
          <li>I granskningsbilden syns slingorna som ett <strong>ljusblått fält</strong>. Ligger en runa utanför det
            blå, eller ornamentik inne i det, har slingorna blivit fel: vrid stenen så att den ristade sidan vetter
            rakt mot dig (knappen <em>Vänd ristade sidan mot mig</em> i 3D-vyn) och kör igen, eller mät runorna
            för hand med <em>Ett klick</em> eller <em>Manuellt</em>.</li>
          <li>Med <strong>Stavlösa runor</strong> påslaget delas runorna efter var strecken står längs slingan: streck
            som står tätt hör till samma runa, och gränsen mellan två runor räknas fram ur stenens egna avstånd.
            Utan slingor godtas kortare streck (5 mm i stället för 12) som runstreck.</li>
          <li>Vill du att varje runa ska väga lika mycket, klicka på <strong>Markera runorna</strong> i granskningen och
            klicka en gång mitt på varje runa, i läsordning.</li>
        </ol>
      </details>
      <label className="flex items-start gap-2 text-[11px] text-slate-600">
        <input type="checkbox" checked={useProtocol} onChange={e => setUseProtocol(e.target.checked)} className="mt-0.5" />
        <span><strong>Vitki-protokollet</strong> (rekommenderas): fasta parametrar – 0,6 mm rutnät, känslighet normal,
          3 mm mellan snitten – så att stenen kan jämföras med andra stenar.{" "}
          <a href="/docs/metod#vitki-protokollet" className="underline">Läs mer</a></span>
      </label>
      <div className={`grid grid-cols-3 gap-2 ${useProtocol && !facitMode ? "opacity-40 pointer-events-none" : ""}`}>
        <label className="text-[11px] font-bold text-slate-500">Avstånd
          <select value={autoSpacing} onChange={e => setAutoSpacing(+e.target.value)} className="mt-1 w-full liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs font-semibold outline-none">
            {[2, 3, 5, 8].map(v => <option key={v} value={v}>{v} mm</option>)}
          </select>
        </label>
        <label className="text-[11px] font-bold text-slate-500">Känslighet
          <select value={autoSensitivity} onChange={e => setAutoSensitivity(+e.target.value)} className="mt-1 w-full liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs font-semibold outline-none">
            <option value={4}>Låg</option><option value={3}>Normal</option><option value={2}>Hög</option>
          </select>
        </label>
        <label className="text-[11px] font-bold text-slate-500">Max bredd
          <select value={autoMaxWidth} onChange={e => setAutoMaxWidth(+e.target.value)} className="mt-1 w-full liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs font-semibold outline-none">
            {[10, 16, 24, 32].map(v => <option key={v} value={v}>{v} mm</option>)}
          </select>
        </label>
      </div>
      <label className="flex items-start gap-2 text-[11px] text-slate-600">
        <input type="checkbox" checked={facitMode} onChange={e => setFacitMode(e.target.checked)} className="mt-0.5" />
        <span><strong>Facit-läge:</strong> mät alla spår och märk själv vilka som är runor. Märkningen sparas som
          facit och används för att mäta hur träffsäker runigenkänningen är.</span>
      </label>
      <button type="button" onClick={onRun} disabled={!canRun || autoBusy}
        className="w-full py-3 bg-slate-900 hover:bg-black text-white font-semibold text-sm rounded-xl disabled:opacity-40 flex justify-center items-center gap-2">
        {autoBusy ? (<><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Analyserar stenen …</>) : "Kör automatisk analys"}
      </button>
      {autoError && <p className="text-xs text-amber-800">{autoError}</p>}
      {autoResult && !facitMode && (
        autoResult.bands?.source ? (
          <p className="text-[11px] text-slate-600" role="status">
            <strong>Runslingor:</strong>{" "}
            {autoResult.bands.source === "ritade" ? "ritade och granskade för hand" : "föreslagna av slingmodellen – kontrollera dem i granskningsbilden"}
            {autoResult.bands.coverage != null ? ` (täcker ${Math.round(autoResult.bands.coverage * 100)} % av ytan)` : ""}.
            {" "}Mätt: {autoResult.parameters.measure === "ornament" ? "ornamentiken utanför slingorna" : "runorna i slingorna"}.
            {autoResult.parameters.staveless ? " Stavlöst läge: runorna delade efter var de står längs slingan." : ""}
          </p>
        ) : (
          <p className="text-[11px] text-amber-800" role="status">
            <strong>Inga runslingor hittades</strong>, så analysen föll tillbaka på den äldre igenkänningen, som kan
            blanda ihop runor och ornamentik. Kontrollera granskningsbilden noga eller mät runorna för hand.
          </p>
        )
      )}
    </div>
  );
}
