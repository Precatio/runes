"use client";

import { CERTAINTY, DASH, EPOCHS, epochOf, REALM_SOURCES, REALM_UNKNOWN, REALMS, type Certainty } from "@/lib/realms";

// The choice of time for the layer of realms, its legend and, folded, what each area builds on and the sources
// (src/lib/realms.ts). The same on the point map and the pattern map.

function Swatch({ color, certainty }: { color: string; certainty: Certainty }) {
  return (
    <svg width="22" height="12" aria-hidden className="shrink-0">
      <rect x="1" y="1" width="20" height="10" rx="2" fill={color} fillOpacity={certainty === "karna" ? 0.25 : 0.1}
        stroke={color} strokeWidth="1.8" strokeDasharray={DASH[certainty]?.replace(/\d+/g, n => String(Math.max(2, Number(n) / 2)))} />
    </svg>
  );
}

export default function RealmPanel({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const epoch = epochOf(value);
  const seg = (on: boolean) => `px-3 py-1.5 rounded-lg text-xs font-bold border ${on ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"}`;
  // One entry per realm in the legend, and the kinds of line that occur
  // (the contested areas are shown by their kind of line, not as a realm)
  const realms = epoch ? [...new Set(epoch.regions.map(r => r.realm))].filter(r => r !== "omstridd") : [];
  const kinds = epoch ? [...new Set(epoch.regions.map(r => r.certainty))] : [];
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Riken och gränser">
        <span className="text-[11px] font-bold text-slate-500 mr-1">Riken och gränser</span>
        <button onClick={() => onChange("")} aria-pressed={!epoch} className={seg(!epoch)}>Av</button>
        {EPOCHS.map(e => (
          <button key={e.key} onClick={() => onChange(e.key)} aria-pressed={epoch?.key === e.key} title={e.title} className={seg(epoch?.key === e.key)}>
            {e.label}
          </button>
        ))}
      </div>
      {epoch && (
        <div className="text-xs text-slate-700 space-y-1.5">
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {realms.map(r => (
              <span key={r} className="flex items-center gap-1.5"><Swatch color={REALMS[r]?.color ?? "#64748b"} certainty="karna" />{REALMS[r]?.label ?? r}</span>
            ))}
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-slate-500">
            {kinds.map(k => <span key={k} className="flex items-center gap-1.5"><Swatch color="#475569" certainty={k} />{CERTAINTY[k]}</span>)}
          </div>
          <details>
            <summary className="cursor-pointer font-semibold text-slate-700">{epoch.title}: vad gränserna bygger på</summary>
            <div className="mt-1.5 space-y-1.5">
              <p>{epoch.text}</p>
              <ul className="space-y-1">
                {epoch.regions.map(r => (
                  <li key={r.id} className="flex gap-2">
                    <span className="pt-0.5"><Swatch color={REALMS[r.realm]?.color ?? "#64748b"} certainty={r.certainty} /></span>
                    <span><span className="font-semibold">{r.name}</span>{r.certainty !== "karna" && <span className="text-slate-500"> ({CERTAINTY[r.certainty].toLowerCase()})</span>}: {r.note}</span>
                  </li>
                ))}
              </ul>
              <p className="text-slate-500">{REALM_UNKNOWN}</p>
              <p className="text-slate-500"><span className="font-semibold">Källor:</span> {REALM_SOURCES.join(" ")}</p>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
