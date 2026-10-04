"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/AuthContext";
import ReportPreview, { downloadBlob, type ReportResult } from "@/components/ReportPreview";
import StoneReportPanel from "@/components/StoneReportPanel";
import { useSettings } from "@/components/SettingsContext";
import { API_URL } from "@/lib/api";
import { corpus, type CorpusEntry } from "@/lib/corpus";
import { safeFilename } from "@/lib/export";
import { FEATURE_TYPES, type FeatureType } from "@/lib/metrics";
import { rundata, type Carver } from "@/lib/rundata";

type ScopeType = "corpus" | "carver" | "province" | "stones";

function certainCarver(carvers: Carver[]): string | null {
  const c = carvers.filter(x => (x.kind === "S" || x.kind === "A") && !x.uncertain);
  return c.length === 1 ? c[0].name : null;
}

export default function ReportsPage() {
  const [tab, setTab] = useState<"stone" | "corpus">("stone");
  const tabBtn = (t: "stone" | "corpus", text: string) => (
    <button onClick={() => setTab(t)}
      className={`px-4 py-2 rounded-xl text-sm font-bold ${tab === t ? "bg-slate-900 text-white" : "bg-white/70 text-slate-700 border border-slate-200"}`}>
      {text}
    </button>
  );
  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Akademisk rapport</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Manusutkast där material, metod, tabeller och figurer räknas fram ur data. Stenrapporten följer
          runologisk praxis (signum, translitterering i fetstil, normalisering i kursiv, översättning inom
          citattecken, utgåva i Sveriges runinskrifter) och redovisar 3D-analysen som en arkeometrisk studie med
          paradata. AI kan formulera sammanfattning, inledning och diskussion – bara ur de framräknade
          resultaten, och markerat som AI-text.
        </p>
      </div>
      <div className="flex gap-2">
        {tabBtn("stone", "Stenrapport – en sten")}
        {tabBtn("corpus", "Korpusrapport – flera stenar")}
      </div>
      {tab === "stone" ? <StoneReportPanel /> : <CorpusReportPanel />}
    </div>
  );
}

function CorpusReportPanel() {
  const { user, loginWithGoogle } = useAuth();
  const { userName, userInstitution, geminiKey } = useSettings();
  const [entries, setEntries] = useState<CorpusEntry[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [carverOf, setCarverOf] = useState<Record<string, string | null>>({});
  const [scope, setScope] = useState<ScopeType>("corpus");
  const [scopeValue, setScopeValue] = useState("");
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [featureFilter, setFeatureFilter] = useState<FeatureType | "">("rune");
  const [title, setTitle] = useState("");
  const [useAI, setUseAI] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportResult | null>(null);

  useEffect(() => {
    if (!user) return;
    corpus.list().then(es => { setEntries(es); setLoaded(true); }).catch(e => setError(String(e)));
  }, [user]);

  useEffect(() => {
    const missing = [...new Set(entries.map(e => e.signum))].filter(s => !(s in carverOf));
    if (!missing.length) return;
    Promise.all(missing.map(s => rundata.inscription(s).then(r => [s, certainCarver(r.carvers)] as const).catch(() => [s, null] as const)))
      .then(pairs => setCarverOf(prev => ({ ...prev, ...Object.fromEntries(pairs) })));
  }, [entries, carverOf]);

  const carvers = useMemo(() => [...new Set(Object.values(carverOf).filter(Boolean) as string[])].sort(), [carverOf]);
  const provinces = useMemo(() => [...new Set(entries.map(e => e.signum.split(" ")[0]))].sort(), [entries]);

  const selection = useMemo(() => entries.filter(e => {
    if (featureFilter && e.feature_type !== featureFilter) return false;
    if (scope === "carver") return carverOf[e.signum] === scopeValue;
    if (scope === "province") return e.signum.split(" ")[0] === scopeValue;
    if (scope === "stones") return picked.has(e.id);
    return true;
  }), [entries, featureFilter, scope, scopeValue, picked, carverOf]);

  const defaultTitle = scope === "carver" && scopeValue ? `Huggteknik hos ${scopeValue}`
    : scope === "province" && scopeValue ? `Huggteknik på runstenar i ${scopeValue}`
    : "Huggteknik i runstenskorpusen";

  const request = (format: "json" | "docx", aiText: Record<string, string> | null = null) => fetch(`${API_URL}/api/reports/academic`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Gemini-Api-Key": geminiKey },
    body: JSON.stringify({
      scope: { type: scope, value: scopeValue || null, title: title || defaultTitle },
      entries: selection, author: userName, institution: userInstitution, use_ai: useAI, format, ai_text: aiText,
    }),
  });

  const generate = async () => {
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

  const base = safeFilename(title || defaultTitle);
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
  if (!user) {
    return (
      <div className="p-8 liquid-glass-island rounded-[32px] text-center space-y-4">
        <p className="text-slate-600">Korpusrapporten byggs på den delade mätkorpusen. Logga in för att skapa en.</p>
        <button onClick={loginWithGoogle} className="px-6 py-3 bg-slate-900 text-white font-bold rounded-2xl">Logga in med Google</button>
      </div>
    );
  }

  const select = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none";

  return (
    <div className="space-y-6">
      <div className="liquid-glass-island rounded-[32px] p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Urval
            <select value={scope} onChange={e => { setScope(e.target.value as ScopeType); setScopeValue(""); }} className={`${select} w-full mt-1`}>
              <option value="corpus">Hela korpusen</option>
              <option value="carver">En ristare</option>
              <option value="province">Ett landskap</option>
              <option value="stones">Valda stenar</option>
            </select>
          </label>
          {scope === "carver" && (
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Ristare
              <select value={scopeValue} onChange={e => setScopeValue(e.target.value)} className={`${select} w-full mt-1`}>
                <option value="">– välj –</option>
                {carvers.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
          )}
          {scope === "province" && (
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Landskap
              <select value={scopeValue} onChange={e => setScopeValue(e.target.value)} className={`${select} w-full mt-1`}>
                <option value="">– välj –</option>
                {provinces.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </label>
          )}
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Spårtyp
            <select value={featureFilter} onChange={e => setFeatureFilter(e.target.value as FeatureType | "")} className={`${select} w-full mt-1`}>
              <option value="">Alla</option>
              {Object.entries(FEATURE_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 md:col-span-2">Titel
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder={defaultTitle} className={`${select} w-full mt-1`} />
          </label>
        </div>

        {scope === "stones" && (
          <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
            {entries.map(e => (
              <label key={e.id} className={`px-2 py-1 rounded-lg border text-xs cursor-pointer ${picked.has(e.id) ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-300"}`}>
                <input type="checkbox" className="hidden" checked={picked.has(e.id)}
                  onChange={() => setPicked(prev => { const n = new Set(prev); if (n.has(e.id)) n.delete(e.id); else n.add(e.id); return n; })} />
                {e.label}
              </label>
            ))}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)} />
            Låt AI formulera sammanfattning, inledning och diskussion
          </label>
          <span className="text-sm text-slate-500">
            {loaded ? `${selection.length} mätningar i urvalet` : "Läser korpusen …"} · författare {userName}{userInstitution ? `, ${userInstitution}` : ""}
            {" "}(<Link href="/account" className="underline">ändra</Link>)
          </span>
          <button onClick={generate} disabled={busy || selection.length === 0 || ((scope === "carver" || scope === "province") && !scopeValue)}
            className="ml-auto px-6 py-2.5 bg-[#b7410e] hover:bg-[#9a350b] text-white font-bold rounded-xl disabled:opacity-40">
            {busy && !report ? "Skapar rapport …" : "Skapa rapport"}
          </button>
        </div>
        {loaded && entries.length === 0 && (
          <p className="text-sm text-slate-600">Korpusen är tom. Gör en mätning i <Link href="/3d" className="text-[#b7410e] font-semibold">3D-vyn</Link> och bidra med den först.</p>
        )}
        {error && <p className="text-sm text-red-700 font-semibold">{error}</p>}
      </div>

      {report && <ReportPreview report={report} base={base} busy={busy} onDocx={downloadDocx} />}
    </div>
  );
}
