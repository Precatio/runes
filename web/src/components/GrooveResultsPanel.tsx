"use client";

import { useState } from "react";
import Link from "next/link";
import type { ThreeDAnalysisResult } from "@/lib/db";
import { METRICS, METRIC_DIGITS, METRIC_LABELS, FEATURE_TYPES, type FeatureType } from "@/lib/metrics";
import { downloadFile, safeFilename, toCSV } from "@/lib/export";
import { corpus, CORPUS_LICENSE, type StoneCondition } from "@/lib/corpus";
import { db, type PaleographicCrop } from "@/lib/db";
import { useAnalysis } from "@/components/AnalysisContext";
import { stats, type GrooveAttribution } from "@/lib/stats";
import { useAuth } from "@/components/AuthContext";
import { useSettings } from "@/components/SettingsContext";

interface Props {
  results: ThreeDAnalysisResult;
  signum: string;
  featureType: FeatureType;
}

export default function GrooveResultsPanel({ results, signum, featureType }: Props) {
  const { user } = useAuth();
  const { userName, userInstitution } = useSettings();
  const [attribution, setAttribution] = useState<GrooveAttribution | null>(null);
  const [attributing, setAttributing] = useState(false);
  const [showContribute, setShowContribute] = useState(false);
  const [scanner, setScanner] = useState("");
  const [notes, setNotes] = useState("");
  const [resolution, setResolution] = useState("");
  const [accuracy, setAccuracy] = useState("");
  const [scanDate, setScanDate] = useState("");
  const [scannedBy, setScannedBy] = useState("");
  const [scanUrl, setScanUrl] = useState("");
  const [scanLicense, setScanLicense] = useState("");
  const [weathering, setWeathering] = useState<StoneCondition["weathering"] | "">("");
  const [lichen, setLichen] = useState(false);
  const [paint, setPaint] = useState(false);
  const [includeRaw, setIncludeRaw] = useState(true);
  const [includeForms, setIncludeForms] = useState(true);
  const [projectCrops, setProjectCrops] = useState<PaleographicCrop[]>([]);
  const { activeProjectId } = useAnalysis();
  const [consent, setConsent] = useState(false);
  const [contributing, setContributing] = useState(false);
  const [contributed, setContributed] = useState(false);

  const summary = results.summary;
  const slices = results.slices ?? [];
  const provenance = results.provenance;
  const tool = results.tool_heuristic;
  const baseName = safeFilename(`${signum || "analys"}_${provenance?.timestamp?.slice(0, 10) ?? ""}`);

  const exportCSV = () => {
    const rows = slices.map((s, i) => ({
      signum,
      feature_type: featureType,
      slice: i + 1,
      position_mm: s.position_mm,
      ...Object.fromEntries(METRICS.map(m => [m, s[m]])),
      method_version: provenance?.method_version,
      mesh_sha256: provenance?.mesh?.sha256,
    }));
    downloadFile(`${baseName}_snitt.csv`, toCSV(rows), "text/csv");
  };

  const exportJSON = () => {
    const payload = { signum, feature_type: featureType, ...results };
    downloadFile(`${baseName}.json`, JSON.stringify(payload, null, 2), "application/json");
  };

  const runAttribution = async () => {
    setAttributing(true);
    try {
      const entries = await corpus.list();
      const reference = entries.map(e => ({
        label: e.label, signum: e.signum, feature_type: e.feature_type, means: e.means,
      }));
      setAttribution(await stats.attribute(
        { label: signum || "Aktuell sten", signum, feature_type: featureType, slices },
        reference,
      ));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Attribueringen misslyckades.");
    } finally {
      setAttributing(false);
    }
  };

  const openContribute = async () => {
    setShowContribute(v => !v);
    if (activeProjectId) {
      const p = await db.getProject(activeProjectId);
      setProjectCrops((p?.paleographicCrops ?? []).filter(c => c.featureVersion));
    }
  };

  const num = (v: string) => (v.trim() ? Number(v.replace(",", ".")) : undefined);

  const contribute = async () => {
    if (!summary || !provenance) return;
    setContributing(true);
    try {
      await corpus.add({
        signum,
        label: `${signum} (${FEATURE_TYPES[featureType].toLowerCase()})`,
        feature_type: featureType,
        contributorName: userName,
        institution: userInstitution,
        method_version: provenance.method_version,
        means: Object.fromEntries(METRICS.map(m => [m, summary[m]?.mean ?? NaN])) as Record<(typeof METRICS)[number], number>,
        summary,
        slices,
        profile: results.plot_data ? { x: results.plot_data.x, z: results.plot_data.z } : null,
        provenance,
        scanner: scanner || undefined,
        notes: notes || undefined,
        scan: {
          device: scanner || undefined, resolution_mm: num(resolution), accuracy_mm: num(accuracy),
          date: scanDate || undefined, scanned_by: scannedBy || undefined, url: scanUrl || undefined,
          license: scanLicense || undefined,
        },
        condition: { weathering: weathering || undefined, lichen, paint },
      }, { includeRaw, runeForms: includeForms ? projectCrops : [] });
      setContributed(true);
      setShowContribute(false);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Kunde inte spara till korpusen.");
    } finally {
      setContributing(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {tool && (
        <div className="flex justify-center">
          <div
            className="bg-slate-900 text-white px-5 py-2 rounded-full text-xs font-bold tracking-wide shadow-lg border border-slate-700"
            title={`${tool.note} Tröskel ${tool.threshold_deg}°${tool.adjustments.length ? ` (${tool.adjustments.join(", ")})` : ""}`}
          >
            Heuristisk verktygsbedömning: {tool.label}
            <span className="ml-2 text-slate-400 font-medium normal-case">· tumregel, ej kalibrerad</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {METRICS.map(m => {
          const s = summary?.[m];
          const digits = METRIC_DIGITS[m];
          const mean = s?.mean ?? results.results[m];
          return (
            <div key={m} className="liquid-glass-island rounded-[28px] p-5 text-center shadow-sm border border-white/50"
              title={s?.ci95 ? `95 % konfidensintervall: ${s.ci95[0].toFixed(digits)}–${s.ci95[1].toFixed(digits)}` : undefined}>
              <div className="text-slate-500 text-[11px] uppercase tracking-wider font-bold mb-1">{METRIC_LABELS[m]}</div>
              <div className="text-2xl font-bold tracking-tight text-slate-900">
                {typeof mean === "number" ? mean.toFixed(digits) : "–"}
              </div>
              {s && s.n > 1 && s.sd !== null && (
                <div className="text-[11px] text-slate-500 font-semibold mt-1">± {s.sd.toFixed(digits)} SD · n={s.n}</div>
              )}
            </div>
          );
        })}
        <div className="liquid-glass-island rounded-[28px] p-5 text-center shadow-sm border border-white/50">
          <div className="text-slate-500 text-[11px] uppercase tracking-wider font-bold mb-1">Spårtyp</div>
          <div className="text-2xl font-bold tracking-tight text-slate-900">{FEATURE_TYPES[featureType]}</div>
          <div className="text-[11px] text-slate-500 font-semibold mt-1">{slices.length} snitt</div>
        </div>
      </div>

      {/* Attribution against the shared corpus */}
      <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-white/50">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <h3 className="text-slate-900 text-lg font-bold">Huggteknik jämfört med mätkorpusen</h3>
            <p className="text-xs text-slate-500 font-medium mt-1 max-w-xl">
              Jämför med stenar i den delade korpusen vars ristare är signerad eller attribuerad i Rundata.
              Resultatet redovisas med korsvaliderad träffsäkerhet.
            </p>
          </div>
          <button onClick={runAttribution} disabled={attributing || !user || slices.length === 0}
            className="px-4 py-2 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl disabled:opacity-40 whitespace-nowrap">
            {attributing ? "Beräknar..." : "Jämför"}
          </button>
        </div>
        {!user && <p className="text-xs text-slate-500">Logga in för att använda den delade korpusen.</p>}
        {attribution && (
          attribution.ranking.length === 0 ? (
            <p className="text-sm text-slate-600 bg-white/60 rounded-xl p-3">
              {attribution.note} Bidra med fler mätningar via <Link href="/korpus" className="text-[#b7410e] font-semibold hover:underline">korpusen</Link>.
            </p>
          ) : (
            <div className="space-y-2">
              {attribution.ranking.slice(0, 5).map((r, i) => (
                <div key={r.group} className="flex justify-between items-center bg-white/60 rounded-xl px-4 py-2.5 text-sm">
                  <span className="font-semibold text-slate-800">{i + 1}. {r.group}</span>
                  <span className="text-xs text-slate-500 font-mono">avstånd {r.distance.toFixed(2)} · {r.n} stenar</span>
                </div>
              ))}
              {attribution.evaluation && (
                <p className="text-xs text-slate-500 pt-2">
                  Träffsäkerhet (lämna-en-ute): rätt ristare först i {(attribution.evaluation.top1_accuracy * 100).toFixed(0)} %
                  av {attribution.evaluation.n_stones} stenar, slumpnivå {(attribution.evaluation.chance_top1 * 100).toFixed(0)} %.
                  Kortare avstånd betyder mer lik huggteknik.
                </p>
              )}
            </div>
          )
        )}
      </div>

      {/* Export, provenance and contribution */}
      <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-white/50 space-y-4">
        <div className="flex flex-wrap gap-3">
          <button onClick={exportCSV} disabled={slices.length === 0}
            className="px-4 py-2 bg-white border border-slate-300 hover:border-slate-900 text-slate-800 text-xs font-bold rounded-xl disabled:opacity-40">
            Exportera snitt (CSV)
          </button>
          <button onClick={exportJSON}
            className="px-4 py-2 bg-white border border-slate-300 hover:border-slate-900 text-slate-800 text-xs font-bold rounded-xl">
            Exportera allt (JSON)
          </button>
          <button onClick={openContribute} disabled={!user || !summary || contributed}
            className="px-4 py-2 bg-[#b7410e] hover:bg-[#9a350b] text-white text-xs font-bold rounded-xl disabled:opacity-40">
            {contributed ? "Tillagd i korpusen ✓" : "Bidra till korpusen"}
          </button>
        </div>

        {showContribute && (
          <div className="bg-white/70 rounded-2xl p-4 border border-slate-200 space-y-3 text-sm">
            <p className="text-slate-600">
              Mätvärdena för <strong>{signum || "(inget signum)"}</strong> ({FEATURE_TYPES[featureType].toLowerCase()}) blir synliga för alla
              inloggade forskare, med dig ({userName}{userInstitution ? `, ${userInstitution}` : ""}) som bidragsgivare.
              Bilder och 3D-filen delas inte.
            </p>
            {!signum && <p className="text-red-700 font-semibold">Ange ett signum innan du bidrar.</p>}
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 pt-1">Skanning</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input value={scanner} onChange={e => setScanner(e.target.value)} placeholder="Instrument (t.ex. Artec Space Spider)" className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
              <input value={scannedBy} onChange={e => setScannedBy(e.target.value)} placeholder="Skannad av" className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
              <input value={resolution} onChange={e => setResolution(e.target.value)} placeholder="Upplösning (mm), t.ex. 0,1" className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
              <input value={accuracy} onChange={e => setAccuracy(e.target.value)} placeholder="Noggrannhet (mm), t.ex. 0,05" className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
              <input type="date" value={scanDate} onChange={e => setScanDate(e.target.value)} className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
              <input value={scanLicense} onChange={e => setScanLicense(e.target.value)} placeholder="Skanningens licens (t.ex. CC BY 4.0)" className="liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
              <input value={scanUrl} onChange={e => setScanUrl(e.target.value)} placeholder="Var skanningen finns (DOI eller länk)" className="sm:col-span-2 liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none" />
            </div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 pt-1">Stenens skick vid mätningen</div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-700">
              <select value={weathering} onChange={e => setWeathering(e.target.value as StoneCondition["weathering"] | "")} className="liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs outline-none">
                <option value="">Vittring: ej angiven</option><option value="låg">Låg vittring</option><option value="medel">Måttlig vittring</option><option value="hög">Hög vittring</option>
              </select>
              <label className="flex items-center gap-1.5"><input type="checkbox" checked={lichen} onChange={e => setLichen(e.target.checked)} /> Lav/påväxt</label>
              <label className="flex items-center gap-1.5"><input type="checkbox" checked={paint} onChange={e => setPaint(e.target.checked)} /> Ommålad</label>
            </div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 pt-1">Data som följer med</div>
            <label className="flex items-start gap-2 text-xs text-slate-600">
              <input type="checkbox" checked={includeRaw} onChange={e => setIncludeRaw(e.target.checked)} className="mt-0.5" />
              Råa tvärsnittsprofiler (rekommenderas) – gör att mätningen kan räknas om när mätmetoden förbättras.
            </label>
            {projectCrops.length > 0 && (
              <label className="flex items-start gap-2 text-xs text-slate-600">
                <input type="checkbox" checked={includeForms} onChange={e => setIncludeForms(e.target.checked)} className="mt-0.5" />
                {projectCrops.length} runformer från 2D-analysen i projektet{projectCrops.some(c => c.grooveSummary) ? ", med huggspårsmått per runa" : ""}.
              </label>
            )}
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Anteckningar (vilken runa/del av ornamentiken, skick ...)"
              className="w-full liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none min-h-[60px]" />
            <label className="flex items-start gap-2 text-xs text-slate-600">
              <input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} className="mt-0.5" />
              Jag publicerar mätvärdena under licensen {CORPUS_LICENSE} (fri användning med angivande av bidragsgivare).
            </label>
            <button onClick={contribute} disabled={!consent || !signum || contributing}
              className="px-4 py-2 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl disabled:opacity-40">
              {contributing ? "Sparar..." : "Publicera i korpusen"}
            </button>
          </div>
        )}

        {provenance && (
          <details className="text-xs text-slate-500">
            <summary className="cursor-pointer font-semibold">Proveniens och reproducerbarhet</summary>
            <div className="mt-2 space-y-1 font-mono break-all">
              <div>Metod: {provenance.method_version} · Programversion: {provenance.version}</div>
              <div>Tidpunkt: {provenance.timestamp}</div>
              {provenance.mesh.mock ? <div>Fil: testmodell (mock)</div> : (
                <div>Fil: {provenance.mesh.filename} · SHA-256: {provenance.mesh.sha256} · {provenance.mesh.faces} ytor</div>
              )}
              <div>Parametrar: {JSON.stringify(provenance.parameters)}</div>
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
