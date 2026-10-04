"use client";

import React, { useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { runologyData, RunologySection } from "@/lib/runologyData";

function KnowledgeBaseContent() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get("search") || "";
  const [searchTerm, setSearchTerm] = useState(initialSearch);

  // Follow ?search= when the URL changes (e.g. a link from the attribution panel)
  const [prevInitialSearch, setPrevInitialSearch] = useState(initialSearch);
  if (initialSearch !== prevInitialSearch) {
    setPrevInitialSearch(initialSearch);
    if (initialSearch) setSearchTerm(initialSearch);
  }

  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return runologyData;
    const lowerSearch = searchTerm.toLowerCase();
    
    return runologyData.filter(item => {
      const matchTitle = item.title.toLowerCase().includes(lowerSearch);
      const matchContent = item.content.toLowerCase().includes(lowerSearch);
      const matchKeywords = item.keywords.some(kw => kw.toLowerCase().includes(lowerSearch));
      return matchTitle || matchContent || matchKeywords;
    });
  }, [searchTerm]);

  const categories = {
    alfabet: "Runalfabet & Historik",
    betydelse: "Runornas Betydelse",
    syfte: "Stenarnas Syfte & Klassificering",
    ristare: "Kända Runristare",
    oattribuerad: "Oattribuerade Mästerverk"
  };

  // Group by category
  const groupedData = filteredData.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, RunologySection[]>);

  const formatMarkdown = (text: string) => {
    // Very simple bold and italic parser for the UI (escape HTML first)
    let formatted = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return { __html: formatted };
  };

  return (
    <div className="w-full min-h-full p-8 max-w-5xl mx-auto space-y-8 animate-fade-in">
      
      {/* Header & Search */}
      <div className="bg-white border border-slate-200 rounded-[32px] p-8 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#b7410e] opacity-5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        <div className="relative z-10 flex flex-col items-center text-center max-w-2xl mx-auto space-y-6">
          
          <div className="w-16 h-16 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-center shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-[#b7410e]">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
            </svg>
          </div>
          
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight font-serif">Runologiskt Arkiv</h1>
            <p className="text-slate-500 mt-3 text-lg leading-relaxed">
              Sökbart referensarkiv över runradens utveckling, fonetik, monumentens syften och kända epigrafiska mästare.
            </p>
          </div>

          <div className="w-full relative mt-4">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
            <input
              type="text"
              className="block w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-[#b7410e] focus:border-[#b7410e] sm:text-lg transition-shadow shadow-sm focus:bg-white text-slate-900 placeholder:text-slate-400 outline-none"
              placeholder="Sök efter 'Futhark', 'Odal', 'Öpir'..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Results */}
      {Object.keys(groupedData).length === 0 ? (
        <div className="text-center py-20 bg-white border border-slate-200 border-dashed rounded-[32px]">
          <p className="text-slate-500 font-medium text-lg">Inga träffar för &rdquo;{searchTerm}&rdquo;</p>
          <p className="text-slate-400 mt-2">Testa att söka på ett annat nyckelord.</p>
        </div>
      ) : (
        <div className="space-y-12">
          {Object.entries(categories).map(([catKey, catName]) => {
            const items = groupedData[catKey];
            if (!items || items.length === 0) return null;

            return (
              <div key={catKey} className="space-y-6">
                <h2 className="text-2xl font-bold text-slate-800 font-serif border-b border-slate-200 pb-2">
                  {catName}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {items.map((item) => (
                    <div 
                      key={item.id} 
                      className="bg-white border border-slate-200 p-6 rounded-[24px] shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden"
                    >
                      <div className="absolute top-0 left-0 w-1.5 h-full bg-[#b7410e]/20 group-hover:bg-[#b7410e] transition-colors"></div>
                      <h3 className="text-xl font-bold text-slate-900 mb-3">{item.title}</h3>
                      <p 
                        className="text-slate-600 leading-relaxed text-sm whitespace-pre-line"
                        dangerouslySetInnerHTML={formatMarkdown(item.content)}
                      />
                      
                      <div className="mt-6 flex flex-wrap gap-2">
                        {item.keywords.map((kw, i) => (
                          <span key={i} className="px-2.5 py-1 bg-slate-100 text-slate-500 text-[10px] font-bold uppercase tracking-wider rounded-md border border-slate-200">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function KnowledgeBasePage() {
  return (
    <Suspense fallback={<div className="p-8">Laddar arkiv...</div>}>
      <KnowledgeBaseContent />
    </Suspense>
  );
}
