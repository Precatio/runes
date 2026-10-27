// The stone's details on the 3D page: stone type, weathering, signum with "Autofyll info", and what was fetched.
import Link from "next/link";

export default function StoneMetaFields(p: {
  metaStone: string; setMetaStone: (v: string) => void;
  metaWeathering: string; setMetaWeathering: (v: string) => void;
  metaText: string; setMetaText: (v: string) => void;
  handleFetchRAA: () => void; fetchingRaa: boolean;
  attributedCarver: string; location: string; metaOrnamentation: string; metaPeriod: string;
  raaSource: { source: string; signum?: string; attribution?: string } | null;
}) {
  const { metaStone, setMetaStone, metaWeathering, setMetaWeathering, metaText, setMetaText, handleFetchRAA, fetchingRaa,
    attributedCarver, location, metaOrnamentation, metaPeriod, raaSource } = p;
  return (
    <div className="space-y-5 pt-2">
      <div>
        <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Stenart</label>
        <select value={metaStone} onChange={e => setMetaStone(e.target.value)} className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none">
          <option value="Granit">Granit</option>
          <option value="Gnejs">Gnejs</option>
          <option value="Gråsten">Gråsten</option>
          <option value="Sandsten">Sandsten</option>
          <option value="Kalksten">Kalksten</option>
          <option value="Skiffer">Skiffer</option>
          <option value="Porfyr">Porfyr</option>
          <option value="Kvartsit">Kvartsit</option>
          <option value="Okänd">Okänd</option>
        </select>
      </div>

      <div>
        <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Yttre påverkan (Vittring)</label>
        <select value={metaWeathering} onChange={e => setMetaWeathering(e.target.value)} className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none">
          <option value="Låg">Låg</option>
          <option value="Medel">Medel</option>
          <option value="Hög">Hög</option>
        </select>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-slate-500 text-[12px] font-bold uppercase tracking-wider">Signum (RAÄ)</label>
          <button 
            type="button" 
            onClick={handleFetchRAA}
            disabled={fetchingRaa || !metaText}
            className="text-[10px] bg-slate-900 hover:bg-black text-white font-bold px-3 py-1.5 rounded-full transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
          >
            {fetchingRaa ? (
              <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
                <path fillRule="evenodd" d="M10.5 3.75a6.75 6.75 0 1 0 0 13.5 6.75 6.75 0 0 0 0-13.5ZM2.25 10.5a8.25 8.25 0 1 1 14.59 5.28l4.69 4.69a.75.75 0 1 1-1.06 1.06l-4.69-4.69A8.25 8.25 0 0 1 2.25 10.5Z" clipRule="evenodd" />
              </svg>
            )}
            {fetchingRaa ? "Hämtar..." : "Autofyll info"}
          </button>
        </div>
        <input 
          type="text" 
          placeholder="t.ex. Sö 112" 
          value={metaText} 
          onChange={e => setMetaText(e.target.value)} 
          className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none placeholder:text-slate-400"
        />
        
        {/* Auto-fetched Hypothesis Info */}
        {(attributedCarver || location || metaOrnamentation || metaPeriod) && (
          <div className="mt-3 bg-slate-900/5 rounded-xl p-3 border border-slate-900/10 animate-in fade-in grid grid-cols-2 gap-2">
            {raaSource && (
              <div className="col-span-2 text-[10px] font-bold uppercase tracking-wider">
                {raaSource.source === "rundata" ? (
                  <Link href={`/inskrifter?signum=${encodeURIComponent(raaSource.signum || metaText)}`} className="text-emerald-700 hover:underline">
                    Källa: Rundata (Samnordisk runtextdatabas) →
                  </Link>
                ) : (
                  <span className="text-amber-700">Källa: K-samsök, tolkat av AI – kontrollera uppgifterna</span>
                )}
              </div>
            )}
            {attributedCarver && (
              <div className="text-[11px] text-slate-600 mb-1">
                <span className="font-bold uppercase tracking-wider text-slate-900">Ristare:</span> {attributedCarver}
              </div>
            )}
            {location && (
              <div className="text-[11px] text-slate-600">
                <span className="font-bold uppercase tracking-wider text-slate-900">Plats:</span> {location}
              </div>
            )}
            {metaOrnamentation && (
              <div className="text-[11px] text-slate-600">
                <span className="font-bold uppercase tracking-wider text-slate-900">Stilgrupp:</span> {metaOrnamentation}
              </div>
            )}
            {metaPeriod && (
              <div className="text-[11px] text-slate-600">
                <span className="font-bold uppercase tracking-wider text-slate-900">Datering (RAÄ):</span> {metaPeriod}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
