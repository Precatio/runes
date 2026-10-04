"use client";

import { useState, useEffect } from "react";
import { db, ProjectData } from "@/lib/db";
import { useRouter } from "next/navigation";
import { useSettings } from "@/components/SettingsContext";
import { useAuth } from "@/components/AuthContext";
import { API_URL } from "@/lib/api";
import { corpus } from "@/lib/corpus";
import { stats } from "@/lib/stats";

interface Candidate {
  name: string;
  strength: "stark" | "måttlig" | "svag";
  evidence: { source: string; description: string }[];
  reasoning: string;
}

interface SynthesisResult {
  candidates: Candidate[];
  geology_analysis: string;
  theory_analysis: string;
  dating_analysis: string;
  summary: string;
  sources: string[];
  ai_used: boolean;
}

const STRENGTH_STYLE: Record<Candidate["strength"], string> = {
  stark: "bg-emerald-100 text-emerald-800 border-emerald-300",
  måttlig: "bg-amber-100 text-amber-800 border-amber-300",
  svag: "bg-slate-100 text-slate-600 border-slate-300",
};

export default function SynthesisPage() {
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [selectedProject, setSelectedProject] = useState<ProjectData | null>(null);
  const { geminiKey } = useSettings();
  const { user } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SynthesisResult | null>(null);
  const [status, setStatus] = useState("");
  const router = useRouter();

  useEffect(() => {
    const load = async () => {
      setProjects(await db.getProjects());
    };
    load();
  }, [user]);

  const handleAnalyze = async () => {
    if (!selectedProject) {
      alert("Välj ett projekt.");
      return;
    }
    
    setLoading(true);
    setResults(null);
    
    try {
      // Compare the latest groove analysis with the shared corpus (if signed in and measured)
      let grooveAttribution = null;
      const latest = selectedProject.grooveAnalyses?.at(-1);
      if (user && latest && selectedProject.metaText) {
        setStatus("Jämför huggteknik med korpusen...");
        try {
          const entries = await corpus.list();
          grooveAttribution = await stats.attribute(
            { label: selectedProject.metaText, signum: selectedProject.metaText, feature_type: latest.feature_type, slices: latest.slices },
            entries.map(e => ({ label: e.label, signum: e.signum, feature_type: e.feature_type, means: e.means })),
          );
        } catch (e) {
          console.error("Korpusjämförelsen misslyckades", e);
        }
      }
      setStatus("Sammanställer belägg...");
      const payload = {
        signum: selectedProject.metaText || "Okänt",
        stoneType: selectedProject.metaStone || "Okänd",
        weathering: selectedProject.metaWeathering || "Okänt",
        attributed_carver: selectedProject.attributedCarver || "Ingen hypotes",
        location: selectedProject.location || "Okänd plats",
        ornamentation: selectedProject.metaOrnamentation || "Okänd",
        period: selectedProject.metaPeriod || "Okänd",
        slices: selectedProject.slices,
        feature_type: latest?.feature_type,
        groove_attribution: grooveAttribution,
      };

      const res = await fetch(`${API_URL}/api/synthesis/analyze`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Gemini-Api-Key": geminiKey
        },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        console.error("Backend error:", errData);
        throw new Error(errData?.detail || "API fel");
      }
      
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Något gick fel vid syntesen.");
    } finally {
      setLoading(false);
      setStatus("");
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Syntes & Attribuering</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Väg samman uppgifter från Rundata, ortografisk jämförelse och uppmätt huggteknik. Kandidaterna räknas fram ur
          beläggen; AI:n skriver bara en sammanfattning och hittar inte på sannolikheter.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Settings Sidebar */}
        <div className="liquid-glass-island rounded-[36px] p-8 h-fit">
          <div className="space-y-6">
            <div>
              <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Välj Projekt</label>
              <select 
                className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none"
                value={selectedProject?.id || ""}
                onChange={(e) => {
                  const proj = projects.find(p => p.id === e.target.value);
                  setSelectedProject(proj || null);
                  setResults(null);
                }}
              >
                <option value="" disabled>-- Välj projekt --</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name} ({p.metaText})</option>
                ))}
              </select>
            </div>
            
            {selectedProject && (
              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3">Vald data</h4>
                <ul className="text-sm text-slate-700 space-y-2 font-medium">
                  <li className="flex justify-between"><span>Signum:</span> <span>{selectedProject.metaText || "-"}</span></li>
                  <li className="flex justify-between"><span>Stenart:</span> <span>{selectedProject.metaStone || "-"}</span></li>
                  <li className="flex justify-between"><span>Sparade 3D-snitt:</span> <span>{selectedProject.slices.length} st</span></li>
                  <li className="flex justify-between"><span>Fullständiga analyser:</span> <span>{selectedProject.grooveAnalyses?.length ?? 0} st</span></li>
                </ul>
              </div>
            )}

            <button 
              onClick={handleAnalyze}
              disabled={loading || !selectedProject}
              className="w-full py-3.5 bg-[#b7410e] hover:bg-[#9a350b] active:scale-[0.98] disabled:opacity-40 text-white font-semibold text-sm rounded-2xl transition-all shadow-lg flex justify-center items-center gap-2 mt-4"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {status || "Beräknar..."}
                </>
              ) : "Kör Syntesmotor"}
            </button>
          </div>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-2 space-y-8 flex flex-col">
          {results ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-500">
              
              <div className="liquid-glass-island rounded-[36px] p-8 shadow-sm border border-white/50">
                <h3 className="text-xl font-bold text-slate-900 mb-6">Attribueringskandidater</h3>
                
                {results.candidates.length === 0 ? (
                  <p className="text-slate-600">Underlaget räcker inte för att peka ut någon ristare.</p>
                ) : (
                  <div className="space-y-5">
                    {results.candidates.map(cand => (
                      <div key={cand.name} className="bg-white/50 rounded-2xl p-4 border border-white">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-lg font-bold text-slate-900">{cand.name}</span>
                          <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${STRENGTH_STYLE[cand.strength]}`}>
                            {cand.strength} belägg
                          </span>
                        </div>
                        <ul className="text-sm text-slate-700 space-y-1 mb-2">
                          {cand.evidence.map((e, i) => (
                            <li key={i}><span className="font-semibold">{e.source}:</span> {e.description}</li>
                          ))}
                        </ul>
                        {cand.reasoning && <p className="text-sm text-slate-600 italic">{cand.reasoning}</p>}
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-[11px] text-slate-500 mt-4">
                  Styrka: stark = signerad i Rundata eller stöd från alla tre källorna; måttlig = attribuerad i litteraturen eller stöd från två källor; svag = en källa.
                </p>
              </div>

              <div className="liquid-glass-island rounded-[36px] p-8 shadow-sm border border-slate-900/10">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                  <span className="text-lg">🌍</span> Geologisk Ursprungsanalys
                </h3>
                <p className="text-[15px] font-medium text-slate-800 leading-relaxed">
                  {results.geology_analysis || "Ingen geologisk data returnerades."}
                </p>
              </div>

              <div className="liquid-glass-island rounded-[36px] p-8 shadow-sm border border-[#b7410e]/20 bg-[#b7410e]/5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#b7410e] mb-3 flex items-center gap-2">
                  <span className="text-lg">⚖️</span> 3D-Data vs Historisk Teori
                </h3>
                <p className="text-[15px] font-medium text-slate-800 leading-relaxed">
                  {results.theory_analysis || "Ingen teorianalys returnerades."}
                </p>
              </div>
              
              {/* New Chronology Panel */}
              <div className="liquid-glass-island rounded-[36px] p-8 shadow-sm border border-slate-900/10">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-[#b7410e] text-white p-2 rounded-xl">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Tidsbedömning & Kronologi</h3>
                    <p className="text-xl font-bold text-slate-900">När höggs stenen?</p>
                  </div>
                </div>
                <p className="text-[15px] font-medium text-slate-700 leading-relaxed">
                  {results.dating_analysis}
                </p>
                <div className="mt-4 flex gap-3 text-xs font-bold uppercase tracking-wide text-slate-500">
                  <span className="bg-slate-200 px-3 py-1 rounded-full">Region: {selectedProject?.location || "Okänd"}</span>
                  <span className="bg-slate-200 px-3 py-1 rounded-full">Stilgrupp: {selectedProject?.metaOrnamentation || "Okänd"}</span>
                </div>
              </div>
              
              <div className="liquid-glass-island rounded-[36px] p-8 shadow-sm border border-slate-900/10 bg-slate-50">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">Sammanfattning</h3>
                <p className="text-[15px] font-medium text-slate-800 leading-relaxed">
                  {results.summary}
                </p>
                <p className="text-[11px] text-slate-500 mt-3">
                  {results.ai_used ? "Texten är AI-genererad utifrån beläggen ovan och ska granskas." : "Ingen AI-text (ingen API-nyckel eller AI-fel) – beläggen är framräknade utan AI."}
                </p>
                {results.sources.length > 0 && (
                  <div className="mt-3 text-[11px] text-slate-500">
                    <div className="font-bold uppercase tracking-wider">Källor</div>
                    <ul className="list-disc pl-4">{results.sources.map(src => <li key={src}>{src}</li>)}</ul>
                  </div>
                )}
              </div>
              
              <div className="flex justify-end pt-4">
                <button 
                  onClick={() => router.push(`/report/${selectedProject?.id}`)}
                  className="px-8 py-4 bg-slate-900 hover:bg-black text-white font-bold rounded-2xl shadow-lg transition-transform active:scale-95 flex items-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  Generera Akademisk Rapport
                </button>
              </div>

            </div>
          ) : (
            <div className="liquid-glass-island rounded-[36px] p-12 h-full flex flex-col items-center justify-center text-center shadow-sm border border-white/50 opacity-60">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className="w-16 h-16 text-slate-400 mb-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
              </svg>
              <h3 className="text-lg font-bold text-slate-700 mb-2">Ingen analys körd</h3>
              <p className="text-sm text-slate-500 max-w-sm">
                Välj ett projekt i panelen och klicka på &quot;Kör Syntesmotor&quot; för att väga samman beläggen.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
