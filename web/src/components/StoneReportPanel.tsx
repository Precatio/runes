"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAnalysis } from "@/components/AnalysisContext";
import { useAuth } from "@/components/AuthContext";
import { useSettings } from "@/components/SettingsContext";
import ReportPreview, { downloadBlob, type ReportResult } from "@/components/ReportPreview";
import { API_URL } from "@/lib/api";
import { corpus, type ScanMetadata, type StoneCondition } from "@/lib/corpus";
import { db, type ProjectData } from "@/lib/db";
import { safeFilename } from "@/lib/export";
import { FEATURE_TYPES } from "@/lib/metrics";
import { fromProject, hasPositions, hasProfiles, type StoneReportInput } from "@/lib/stoneReport";

const field = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none w-full mt-1";
const label = "text-[11px] font-bold uppercase tracking-wider text-slate-500";

export default function StoneReportPanel() {
  const { stoneReportInput } = useAnalysis();
  const { user } = useAuth();
  const { userName, userInstitution, geminiKey } = useSettings();
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [sourceKey, setSourceKey] = useState<string>(stoneReportInput ? "session" : "");
  const [scan, setScan] = useState<ScanMetadata>({});
  const [condition, setCondition] = useState<StoneCondition>({});
  const [title, setTitle] = useState("");
  const [useAI, setUseAI] = useState(true);
  const [withCorpus, setWithCorpus] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<(ReportResult & { surface: boolean; surface_note: string | null }) | null>(null);

  useEffect(() => {
    db.getProjects().then(ps => {
      const usable = ps.filter(p => p.grooveAnalyses?.length);
      setProjects(usable);
      setSourceKey(k => k || (usable[0] ? usable[0].id : ""));
    });
  }, []);

  const input: StoneReportInput | null = useMemo(() => {
    if (sourceKey === "session") return stoneReportInput;
    const p = projects.find(x => x.id === sourceKey);
    return p ? fromProject(p) : null;
  }, [sourceKey, stoneReportInput, projects]);

  const signum = input?.signum || "Okänd sten";
  const base = safeFilename(title || `${signum} stenrapport`);
  const nSlices = input?.analyses.reduce((n, a) => n + a.slices.length, 0) ?? 0;

  const request = async (format: "json" | "docx", aiText: Record<string, string> | null = null) => {
    const corpusEntries = withCorpus && user ? await corpus.list().catch(() => []) : [];
    return fetch(`${API_URL}/api/reports/stone`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Gemini-Api-Key": geminiKey },
      body: JSON.stringify({
        signum: input!.signum, title: title || null, author: userName, institution: userInstitution,
        meta: input!.meta, scan, analyses: input!.analyses, counts: input!.counts ?? null,
        mesh_id: input!.meshId ?? null, view: input!.view ?? null,
        corpus: corpusEntries.map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means })),
        // Weathering from the 3D page's metadata unless set here
        condition: { ...condition, weathering: condition.weathering ?? input!.meta.weathering?.toLowerCase() },
        two_d: input!.twoD ?? null, synthesis: input!.synthesis ?? null, use_ai: useAI, format, ai_text: aiText,
      }),
    });
  };

  const generate = async () => {
    if (!input) return;
    setBusy(true);
    setError(null);
    setReport(null);
    try {
      const res = await request("json");
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
      setReport(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Rapporten kunde inte skapas.");
    } finally {
      setBusy(false);
    }
  };

  const downloadDocx = async () => {
    setBusy(true);
    try {
      const res = await request("docx", report?.ai_text ?? null);
      if (!res.ok) throw new Error("Word-filen kunde inte skapas.");
      await downloadBlob(res, `${base}.docx`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Word-filen kunde inte skapas.");
    } finally {
      setBusy(false);
    }
  };

  const setNum = (k: "resolution_mm" | "accuracy_mm", v: string) =>
    setScan(s => ({ ...s, [k]: v === "" ? undefined : Number(v.replace(",", ".")) }));

  return (
    <div className="space-y-6">
      <div className="liquid-glass-island rounded-[32px] p-6 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className={`${label} md:col-span-1`}>Underlag
            <select value={sourceKey} onChange={e => { setSourceKey(e.target.value); setReport(null); }} className={field}>
              {stoneReportInput && <option value="session">{stoneReportInput.source} – {stoneReportInput.signum || "utan signum"}</option>}
              {projects.map(p => <option key={p.id} value={p.id}>Projekt: {p.name}{p.metaText ? ` (${p.metaText})` : ""}</option>)}
              {!stoneReportInput && projects.length === 0 && <option value="">Inga analyser ännu</option>}
            </select>
          </label>
          <label className={`${label} md:col-span-2`}>Titel
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder={`${signum}: huggteknik dokumenterad med 3D-skanning`} className={field} />
          </label>
        </div>

        {!input ? (
          <p className="text-sm text-slate-600">
            Gör en analys i <Link href="/3d" className="text-[#b7410e] font-semibold">3D-vyn</Link> och klicka på
            &quot;Skapa stenrapport&quot;, eller spara analysen i ett projekt.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="px-2 py-1 rounded-lg bg-slate-100 font-semibold">{signum}</span>
              {input.analyses.map((a, i) => (
                <span key={i} className="px-2 py-1 rounded-lg bg-slate-100">{FEATURE_TYPES[a.feature_type]}: {a.slices.length} snitt</span>
              ))}
              <Badge ok={hasProfiles(input)} yes="tvärsnittsprofiler" no="profiler saknas – inga profilfigurer" />
              <Badge ok={hasPositions(input)} yes="snittpositioner" no="positioner saknas – snitten visas inte på ytan" />
              <Badge ok={!!input.meshId} yes="3D-modell kopplad" no="ingen 3D-modell – inga ytbilder" />
              <Badge ok={!!input.synthesis} yes="attribueringssyntes" no="ingen sparad syntes – inget attribueringsavsnitt" />
            </div>
            {input.meshId && (
              <p className="text-xs text-slate-500">
                Ytbilderna (strykljus, djupkarta, snittpositioner) räknas ur skanningen och kräver att den är inläst i
                analysmotorn. Om den inte är det, öppna samma fil i 3D-vyn först.
              </p>
            )}

            <div>
              <p className="text-sm font-bold text-slate-900 mb-2">3D-dokumentation (paradata)</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <label className={label}>Skanner<input className={field} value={scan.device ?? ""} onChange={e => setScan(s => ({ ...s, device: e.target.value }))} placeholder="t.ex. Artec Space Spider" /></label>
                <label className={label}>Skannat av<input className={field} value={scan.scanned_by ?? ""} onChange={e => setScan(s => ({ ...s, scanned_by: e.target.value }))} /></label>
                <label className={label}>Datum<input type="date" className={field} value={scan.date ?? ""} onChange={e => setScan(s => ({ ...s, date: e.target.value }))} /></label>
                <label className={label}>Licens för skanningen<input className={field} value={scan.license ?? ""} onChange={e => setScan(s => ({ ...s, license: e.target.value }))} placeholder="t.ex. CC BY 4.0" /></label>
                <label className={label}>Upplösning (mm)<input inputMode="decimal" className={field} value={scan.resolution_mm ?? ""} onChange={e => setNum("resolution_mm", e.target.value)} /></label>
                <label className={label}>Noggrannhet (mm)<input inputMode="decimal" className={field} value={scan.accuracy_mm ?? ""} onChange={e => setNum("accuracy_mm", e.target.value)} /></label>
                <label className={`${label} col-span-2`}>Länk eller DOI till skanningen<input className={field} value={scan.url ?? ""} onChange={e => setScan(s => ({ ...s, url: e.target.value }))} /></label>
                <label className={label}>Vittring
                  <select className={field} value={condition.weathering ?? ""} onChange={e => setCondition(c => ({ ...c, weathering: (e.target.value || undefined) as StoneCondition["weathering"] }))}>
                    <option value="">–</option><option value="låg">Låg</option><option value="medel">Medel</option><option value="hög">Hög</option>
                  </select>
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700 mt-5"><input type="checkbox" checked={!!condition.lichen} onChange={e => setCondition(c => ({ ...c, lichen: e.target.checked }))} /> Lav</label>
                <label className="flex items-center gap-2 text-sm text-slate-700 mt-5"><input type="checkbox" checked={!!condition.paint} onChange={e => setCondition(c => ({ ...c, paint: e.target.checked }))} /> Ommålad</label>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)} /> AI formulerar sammanfattning, inledning och diskussion
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700" title={user ? "" : "Kräver inloggning"}>
                <input type="checkbox" checked={withCorpus && !!user} disabled={!user} onChange={e => setWithCorpus(e.target.checked)} /> Jämför med mätkorpusen
              </label>
              <span className="text-sm text-slate-500">
                {nSlices} tvärsnitt · författare {userName}{userInstitution ? `, ${userInstitution}` : ""} (<Link href="/account" className="underline">ändra</Link>)
              </span>
              <button onClick={generate} disabled={busy || nSlices === 0}
                className="ml-auto px-6 py-2.5 bg-[#b7410e] hover:bg-[#9a350b] text-white font-bold rounded-xl disabled:opacity-40">
                {busy && !report ? "Skapar rapport (räknar figurer) …" : "Skapa stenrapport"}
              </button>
            </div>
          </>
        )}
        {error && <p className="text-sm text-red-700 font-semibold">{error}</p>}
        {report?.surface_note && <p className="text-sm text-amber-800 font-semibold">{report.surface_note}</p>}
      </div>

      {report && <ReportPreview report={report} base={base} busy={busy} onDocx={downloadDocx} />}
    </div>
  );
}

function Badge({ ok, yes, no }: { ok: boolean; yes: string; no: string }) {
  return (
    <span className={`px-2 py-1 rounded-lg ${ok ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>
      {ok ? `✓ ${yes}` : no}
    </span>
  );
}
