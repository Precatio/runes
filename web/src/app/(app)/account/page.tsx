"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthContext";
import { useSettings } from "@/components/SettingsContext";
import { useRouter } from "next/navigation";
import { db, ReportData } from "@/lib/db";
import Link from "next/link";

export default function AccountOverview() {
  const { user, logout } = useAuth();
  const { 
    userName, userInstitution, geminiKey, openaiKey, anthropicKey, aiProvider,
    setGeminiKey, setOpenaiKey, setUserName, setUserInstitution, setAnthropicKey, setAiProvider,
    totalTokensUsed, tokenHistory
  } = useSettings();
  const router = useRouter();
  const [projectCount, setProjectCount] = useState<number>(0);
  const [reports, setReports] = useState<ReportData[]>([]);

  const [tempGemini, setTempGemini] = useState("");
  const [tempAnthropic, setTempAnthropic] = useState("");
  const [tempProvider, setTempProvider] = useState<"claude" | "gemini">("claude");
  const [tempOpenai, setTempOpenai] = useState("");
  const [tempName, setTempName] = useState("");
  const [tempInst, setTempInst] = useState("");
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    // If not logged in and auth resolves, redirect to home.
    if (user === null) {
      router.push("/start");
    }
  }, [user, router]);

  useEffect(() => {
    async function loadStats() {
      const projs = await db.getProjects();
      setProjectCount(projs.length);
      const reps = await db.getReports();
      setReports(reps);
    }
    loadStats();
  }, [user]);

  // Copy current settings into the form whenever they change
  const settingsKey = [geminiKey, openaiKey, anthropicKey, aiProvider, userName, userInstitution].join("\u0000");
  const [prevSettingsKey, setPrevSettingsKey] = useState<string | null>(null);
  if (settingsKey !== prevSettingsKey) {
    setPrevSettingsKey(settingsKey);
    setTempGemini(geminiKey);
    setTempAnthropic(anthropicKey);
    setTempProvider(aiProvider);
    setTempOpenai(openaiKey);
    setTempName(userName);
    setTempInst(userInstitution);
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-full w-full">
        <div className="w-10 h-10 border-4 border-slate-200 border-t-[#b7410e] rounded-full animate-spin"></div>
      </div>
    );
  }

  const getInitials = (name: string) => {
    return name.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 2);
  };

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };
  
  const handleSaveSettings = () => {
    setGeminiKey(tempGemini);
    setAnthropicKey(tempAnthropic);
    setAiProvider(tempProvider);
    setOpenaiKey(tempOpenai);
    setUserName(tempName);
    setUserInstitution(tempInst);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  // Generate last 14 days data for chart
  const last14Days = Array.from({ length: 14 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (13 - i));
    const dateStr = d.toISOString().split('T')[0];
    return {
      date: dateStr,
      displayDate: d.toLocaleDateString('sv-SE', { day: 'numeric', month: 'short' }),
      tokens: tokenHistory?.[dateStr] || 0
    };
  });
  
  const maxTokens = Math.max(...last14Days.map(d => d.tokens), 100); // Prevent div by 0

  return (
    <div className="w-full h-full p-8 overflow-y-auto relative bg-slate-50">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/start" className="p-2 bg-white rounded-full border border-slate-200 text-slate-500 hover:text-slate-900 shadow-sm transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
          </Link>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Mitt Konto</h1>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Profile Card */}
          <div className="col-span-1 lg:col-span-2 bg-white border border-slate-200 rounded-[24px] p-8 shadow-sm flex flex-col md:flex-row items-center md:items-start gap-8">
            {user.photoURL ? (
              // External Google avatar; next/image would need remotePatterns for a 128px image
              // eslint-disable-next-line @next/next/no-img-element
              <img src={user.photoURL} alt="Profile" className="w-32 h-32 rounded-full shadow-md object-cover border-4 border-white" />
            ) : (
              <div className="w-32 h-32 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-4xl shadow-md border-4 border-white">
                {getInitials(user.displayName || user.email || "?")}
              </div>
            )}
            
            <div className="flex-1 text-center md:text-left space-y-2">
              <h2 className="text-2xl font-bold text-slate-900">{userName || user.displayName || "Forskare"}</h2>
              <div className="text-slate-500 font-medium flex items-center justify-center md:justify-start gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
                </svg>
                {user.email}
              </div>
              {userInstitution && (
                <div className="text-[#b7410e] font-semibold flex items-center justify-center md:justify-start gap-2 mt-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.315 48.315 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z" />
                  </svg>
                  {userInstitution}
                </div>
              )}
            </div>
            
            <div className="flex flex-col gap-3 mt-4 md:mt-0">
              <button 
                onClick={handleLogout}
                className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold py-2.5 px-6 rounded-xl transition-all shadow-sm border border-slate-200 flex items-center justify-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
                </svg>
                Logga ut
              </button>
            </div>
          </div>
          
          {/* Quick Stats */}
          <div className="col-span-1 flex flex-col gap-6">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[24px] p-6 text-white shadow-lg flex flex-col justify-center items-center text-center flex-1">
              <h3 className="text-slate-400 font-bold uppercase tracking-wider text-xs mb-1">Sparade Projekt</h3>
              <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 mt-2">
                {projectCount}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-[#b7410e] to-orange-900 rounded-[24px] p-6 text-white shadow-lg flex flex-col justify-center items-center text-center flex-1">
              <h3 className="text-orange-200/70 font-bold uppercase tracking-wider text-[10px] mb-1">Livstids Tokens (AI)</h3>
              <div className="text-4xl font-black text-white mt-1">
                {totalTokensUsed.toLocaleString('sv-SE')}
              </div>
              <div className="mt-3 text-[10px] text-orange-100 font-medium bg-black/20 px-3 py-1.5 rounded-lg w-full flex flex-col gap-1">
                <span>Modell: {aiProvider === "claude" ? "Claude (Anthropic)" : "Gemini (Google)"}</span>
                <p className="text-orange-200/50 text-[10px] mt-1">Kostnaden beror på modell; se leverantörens prislista.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Token Usage Graph */}
        <div className="bg-white border border-slate-200 rounded-[24px] p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Förbrukning över tid</h2>
          <p className="text-sm text-slate-600 mb-8">
            Dina analyser de senaste 14 dagarna mätt i antal förbrukade AI-tokens.
          </p>
          
          <div className="h-48 flex items-end justify-between gap-1 sm:gap-2 pb-6 border-b border-slate-100">
            {last14Days.map((day, idx) => {
              const heightPct = (day.tokens / maxTokens) * 100;
              return (
                <div key={idx} className="relative flex flex-col items-center justify-end h-full w-full group">
                  {/* Tooltip */}
                  <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-white text-xs py-1 px-2 rounded-lg pointer-events-none whitespace-nowrap z-10 shadow-lg">
                    {day.tokens.toLocaleString('sv-SE')} tokens
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-slate-800"></div>
                  </div>
                  
                  {/* Bar */}
                  <div 
                    className="w-full bg-gradient-to-t from-orange-200 to-[#b7410e] rounded-t-sm transition-all duration-500 ease-out group-hover:opacity-80"
                    style={{ height: `${Math.max(heightPct, 2)}%` }}
                  />
                  <span className="absolute -bottom-6 text-[10px] text-slate-400 rotate-[-45deg] origin-top-left -ml-2 whitespace-nowrap">
                    {day.displayDate}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Saved Reports Section */}
        <div className="bg-white border border-slate-200 rounded-[24px] p-8 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-1">Dina Sparade Rapporter</h2>
              <p className="text-sm text-slate-600">
                Redigerbara akademiska rapporter som du har genererat och sparat.
              </p>
            </div>
            <span className="bg-[#b7410e]/10 text-[#b7410e] text-xs font-bold px-3 py-1 rounded-full">
              {reports.length} st
            </span>
          </div>
          
          {reports.length === 0 ? (
            <div className="text-center p-8 bg-slate-50 border border-slate-200 border-dashed rounded-2xl">
              <p className="text-slate-500 font-medium">Inga rapporter sparade ännu.</p>
              <p className="text-sm text-slate-400 mt-1">Gå till Syntes-fliken för att generera en rapport.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reports.map((report) => (
                <div 
                  key={report.id} 
                  onClick={() => router.push(`/report/${report.id}`)}
                  className="p-5 border border-slate-200 rounded-2xl hover:border-[#b7410e]/50 hover:shadow-md cursor-pointer transition-all bg-white group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-slate-800 text-lg group-hover:text-[#b7410e] transition-colors">{report.title}</h3>
                      <p className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                        {new Date(report.createdAt).toLocaleDateString('sv-SE', { year: 'numeric', month: 'long', day: 'numeric' })}
                      </p>
                    </div>
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-[#b7410e]/10 group-hover:text-[#b7410e] transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Settings Section */}
        <div className="bg-white border border-slate-200 rounded-[24px] p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Inställningar & API-Nycklar</h2>
          <p className="text-sm text-slate-600 mb-6 leading-relaxed">
            Ställ in din användarprofil för akademiska rapporter, och hantera dina BYOK API-nycklar. 
            All data sparas säkert lokalt i din webbläsare.
          </p>

          <div className="space-y-6 max-w-2xl">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <label className="block text-sm font-bold text-slate-700 mb-2">Ditt Namn</label>
                <input 
                  type="text"
                  value={tempName}
                  onChange={(e) => setTempName(e.target.value)}
                  placeholder="Namn Efternamn"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#b7410e] text-slate-900 text-sm font-semibold"
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-bold text-slate-700 mb-2">Institution / Organisation</label>
                <input 
                  type="text"
                  value={tempInst}
                  onChange={(e) => setTempInst(e.target.value)}
                  placeholder="T.ex. Uppsala Universitet"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#b7410e] text-slate-900 text-sm font-semibold"
                />
              </div>
            </div>
            
            <hr className="border-slate-200" />
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">AI-modell</label>
              <div className="flex gap-2">
                {([["claude", "Claude (Anthropic) – rekommenderas"], ["gemini", "Gemini (Google)"]] as const).map(([v, l]) => (
                  <button key={v} type="button" onClick={() => setTempProvider(v)}
                    className={`px-4 py-2 rounded-xl text-sm font-bold border ${tempProvider === v ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
                    {l}
                  </button>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Används för 2D-analys, läsning, syntesens och rapporternas texter och AI-assistenten. Oavsett modell
                prövas läsningar mot Rundata, och AI anger aldrig sannolikheter.
              </p>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Anthropic API-nyckel (för Claude)</label>
              <input
                type="password"
                value={tempAnthropic}
                onChange={(e) => setTempAnthropic(e.target.value)}
                placeholder="sk-ant-..."
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#b7410e] text-slate-900 font-mono text-sm"
              />
              <p className="text-xs text-slate-500 mt-2">
                Skapa en nyckel på <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">console.anthropic.com</a>.
                Ett Claude-abonnemang (Pro/Max) kan inte användas av appen; API:t faktureras separat efter användning.
              </p>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Google Gemini API-nyckel (om du väljer Gemini)</label>
              <input 
                type="password"
                value={tempGemini}
                onChange={(e) => setTempGemini(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#b7410e] text-slate-900 font-mono text-sm"
              />
              <p className="text-xs text-slate-500 mt-2">
                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Skapa en nyckel här</a>.
              </p>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">OpenAI API-Nyckel (Talsyntes)</label>
              <input 
                type="password"
                value={tempOpenai}
                onChange={(e) => setTempOpenai(e.target.value)}
                placeholder="sk-..."
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#b7410e] text-slate-900 font-mono text-sm"
              />
              <p className="text-xs text-slate-500 mt-2">
                Krävs för att låta Vitki läsa upp fornnordiska. <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Skapa en nyckel här</a>.
              </p>
            </div>
          </div>

          <div className="mt-8 flex items-center gap-4">
            <button 
              onClick={handleSaveSettings}
              className="px-6 py-2.5 bg-[#b7410e] text-white rounded-xl font-bold shadow-lg shadow-orange-900/20 hover:bg-[#9a350b] transition-colors"
            >
              Spara Ändringar
            </button>
            {isSaved && (
              <span className="text-sm font-bold text-green-600 animate-pulse">Sparat!</span>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
