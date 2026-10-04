"use client";

import Link from "next/link";
import RuneCanvasBackground from "@/components/RuneCanvasBackground";
import { db, ProjectData } from "@/lib/db";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthContext";

export default function DashboardPage() {
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const { user } = useAuth();

  const loadProjects = async () => {
    const data = await db.getProjects();
    setProjects(data);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadProjects();
  }, [user]);

  return (
    <>
      <RuneCanvasBackground />
      <div className="flex flex-col h-full w-full max-w-5xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
      
      {/* Hero Section */}
      <div className="mb-10 text-center mt-8">
        <div className="w-24 h-24 mx-auto mb-6 flex items-center justify-center transform -rotate-3 hover:rotate-0 transition-transform duration-300">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-20 h-20 text-[#b7410e] drop-shadow-md">
            {/* Huvudstav */}
            <path d="M12 2v20" />
            {/* Ansuz (A) grenar */}
            <path d="M12 6l6 4" />
            <path d="M12 10l6 4" />
            {/* Asymmetrisk gren */}
            <path d="M12 14l-6 4" />
            {/* Tiwaz (T) pilspets */}
            <path d="M12 2l-5 5" />
            <path d="M12 2l5 5" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 mb-4">
          Välkommen till Vitki AI
        </h1>
        <p className="text-slate-600 text-[18px] leading-relaxed max-w-2xl mx-auto font-medium">
          Ditt centrala arbetsverktyg för epigrafik och runologi. Analysera 3D-modeller, interagera med AI-runologen och hantera dina projekt.
        </p>
        <p className="text-slate-500 text-[14px] leading-relaxed max-w-2xl mx-auto mt-3 italic">
          (En &rdquo;Vitki&rdquo; var under fornnordisk tid en mästare på runor – en runristare eller magiker som besatt djup kunskap om runornas hemligheter och formler.)
        </p>
      </div>

      {/* Grid Menu */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto w-full">
        <Link href="/3d" className="group">
          <div className="liquid-glass-island rounded-[32px] p-8 h-full border border-white/50 hover:shadow-xl hover:border-white/80 transition-all duration-300 transform group-hover:-translate-y-1">
            <div className="w-14 h-14 bg-[#b7410e]/10 text-[#b7410e] rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-7 h-7">
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">3D-Analys</h3>
            <p className="text-slate-600 text-sm font-medium leading-relaxed">
              Utför vetenskaplig huggspårsanalys. Ladda upp modeller (.stl / .obj / .ply), markera spår med den nya interaktiva 3D-vyn, och få fram V-vinklar, spårdjup och asymmetri.
            </p>
          </div>
        </Link>

        <Link href="/2d" className="group">
          <div className="liquid-glass-island rounded-[32px] p-8 h-full border border-white/50 hover:shadow-xl hover:border-white/80 transition-all duration-300 transform group-hover:-translate-y-1">
            <div className="w-14 h-14 bg-slate-900/10 text-slate-800 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-7 h-7">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-3">
              2D-Bildanalys
            </h3>
            <p className="text-slate-600 text-sm font-medium leading-relaxed">
              Utför paleografisk analys och tyda runor på foton. AI:n extraherar Gräslunds stilgrupper, analyserar ornamentik och transkriberar inskrifter.
            </p>
          </div>
        </Link>
      </div>

      {/* Info Notice */}
      <div className="mt-10 max-w-4xl mx-auto w-full">
        <div className="glass-btn-3d rounded-2xl p-5 flex items-start gap-4">
          <div className="mt-0.5 text-[#b7410e]">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 mb-1">Global AI-Assistent</h4>
            <p className="text-sm text-slate-600 font-medium">
              Glöm inte att AI-runologen nu finns tillgänglig när som helst nere i högra hörnet. Den läser automatiskt in resultaten från din senaste 3D-analys så du kan ställa frågor direkt i kontext.
            </p>
          </div>
        </div>
      </div>

      {/* Saved Projects Section */}
      <div className="mt-12 max-w-4xl mx-auto w-full">
        <h3 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 text-[#b7410e]">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
          </svg>
          Mina Projekt
        </h3>
        
        {projects.length === 0 ? (
          <div className="liquid-glass-island rounded-[32px] p-8 text-center border border-white/50">
            <p className="text-slate-500 font-medium">Du har inga sparade projekt ännu.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {projects.map(p => (
              <div key={p.id} className="liquid-glass-island rounded-[24px] p-6 border border-white/50 hover:border-[#b7410e]/50 hover:shadow-md transition-all group relative">
                <button 
                  onClick={async () => {
                    await db.deleteProject(p.id);
                    loadProjects();
                  }}
                  className="absolute top-4 right-4 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Ta bort projekt"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                    <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
                  </svg>
                </button>
                <Link href={`/3d?projectId=${p.id}`}>
                  <h4 className="text-lg font-bold text-slate-900 mb-1">{p.name || p.fileName}</h4>
                  <div className="flex gap-2 mb-3">
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{p.metaStone}</span>
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{p.metaWeathering} vittring</span>
                  </div>
                  <div className="text-sm text-slate-500 font-medium">
                    {p.slices.length} sparade snitt &nbsp;&bull;&nbsp; {new Date(p.updatedAt).toLocaleDateString("sv-SE")}
                  </div>
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      </div>
    </>
  );
}
