"use client";
import React, { useState, useRef, useEffect } from 'react';
import { useAnalysis } from './AnalysisContext';
import { useSettings } from './SettingsContext';
import { API_URL } from "@/lib/api";

export default function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<{role: 'user' | 'model', content: string}[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const initialOffset = useRef({ x: 0, y: 0 });

  const { geminiKey, addUsedTokens } = useSettings();
  
  const { latest3DResults, latestLinguisticResults, latest2DResults } = useAnalysis();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) scrollToBottom();
  }, [messages, isOpen, isMinimized]);

  const handlePointerDown = (e: React.PointerEvent) => {
    if ((e.target as HTMLElement).closest('button')) return;
    isDragging.current = true;
    dragStart.current = { x: e.clientX, y: e.clientY };
    initialOffset.current = { ...offset };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current) return;
    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;
    setOffset({
      x: initialOffset.current.x + dx,
      y: initialOffset.current.y + dy
    });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!isDragging.current) return;
    isDragging.current = false;
    (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const payload = {
        messages: [...messages, { role: 'user', content: userMessage }],
        context_data: {
          three_d_results: latest3DResults?.results || latest3DResults,
          linguistic_results: latestLinguisticResults,
          two_d_results: latest2DResults
        }
      };

      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Gemini-Api-Key": geminiKey
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        let errorDetail = "Ett okänt fel uppstod i chat-servern.";
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch {
          // ignore
        }
        throw new Error(errorDetail);
      }
      
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'model', content: data.reply }]);
      if (data.tokens_used) {
        addUsedTokens(data.tokens_used);
      }
    } catch (err: unknown) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'model', content: (err as Error).message || "Ett nätverksfel uppstod vid kommunikation med analysmotorn." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatMessage = (text: string) => {
    // Escape HTML first to prevent XSS
    let safeText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    
    // Replace bold and italic first so they work inside tables
    safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    safeText = safeText.replace(/\*(.*?)\*/g, '<em>$1</em>');

    const lines = safeText.split('\n');
    const htmlLines = [];
    let isTable = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Handle Headings
      if (line.startsWith('### ')) {
        htmlLines.push(`<h3 style="color: #b7410e; font-weight: 800; font-size: 1.1rem; margin-top: 16px; margin-bottom: 4px;">${line.substring(4)}</h3>`);
        continue;
      }
      if (line.startsWith('## ')) {
        htmlLines.push(`<h2 style="color: #b7410e; font-weight: 800; font-size: 1.25rem; margin-top: 16px; margin-bottom: 4px;">${line.substring(3)}</h2>`);
        continue;
      }
      if (line.startsWith('# ')) {
        htmlLines.push(`<h1 style="color: #b7410e; font-weight: 900; font-size: 1.5rem; margin-top: 18px; margin-bottom: 6px;">${line.substring(2)}</h1>`);
        continue;
      }

      // Handle Tables
      if (line.startsWith('|') && line.endsWith('|')) {
        if (!isTable) {
          htmlLines.push('<div class="overflow-x-auto"><table class="w-full text-sm text-left mt-3 mb-4 border-collapse">');
          isTable = true;
        }
        
        // Skip markdown separator row like |---|---|
        if (line.replace(/\|/g, '').replace(/-/g, '').replace(/:/g, '').trim() === '') {
          continue;
        }
        
        // Parse cells
        const cells = line.split('|').map(c => c.trim());
        // Remove first and last empty elements caused by starting/ending with |
        cells.shift();
        cells.pop();
        
        // Assume first row is header
        const isHeader: boolean = htmlLines[htmlLines.length - 1] === '<div class="overflow-x-auto"><table class="w-full text-sm text-left mt-3 mb-4 border-collapse">';
        const Tag = isHeader ? 'th' : 'td';
        
        htmlLines.push(`<tr class="border-b border-slate-900/10 ${isHeader ? 'bg-slate-900/5' : ''}">`);
        cells.forEach(cell => {
          htmlLines.push(`<${Tag} class="p-2 ${isHeader ? 'font-bold text-slate-700' : 'text-slate-600'}">${cell}</${Tag}>`);
        });
        htmlLines.push('</tr>');
        continue;
      } else if (isTable) {
        htmlLines.push('</table></div>');
        isTable = false;
      }

      // Handle empty lines (converted to simple breaks, but avoid excessive spacing after headings)
      if (line === '') {
        const prevLine = htmlLines[htmlLines.length - 1] || '';
        if (prevLine.startsWith('<h') || prevLine === '<br/>') {
          // Skip adding <br/> immediately after a heading or another <br/> to prevent huge gaps
          continue;
        }
        htmlLines.push('<br/>');
        continue;
      }
      
      // Handle list items
      if (line.startsWith('- ') || line.startsWith('* ')) {
        htmlLines.push(`<div style="display:flex; gap:6px; margin-top:4px;"><span style="color:#b7410e">&bull;</span><span>${line.substring(2)}</span></div>`);
        continue;
      }

      // Regular text
      htmlLines.push(`<span>${line}</span>`);
    }

    if (isTable) {
      htmlLines.push('</table></div>');
    }

    return { __html: htmlLines.join('') };
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      {isOpen && (
        <div 
          className={`mb-4 liquid-glass-island rounded-3xl flex flex-col overflow-hidden shadow-2xl animate-in slide-in-from-bottom-5 ${isMinimized ? 'w-96 h-auto' : ''}`}
          style={isMinimized ? { 
            transform: `translate(${offset.x}px, ${offset.y}px)` 
          } : { 
            transform: `translate(${offset.x}px, ${offset.y}px)`,
            width: '384px',
            height: '500px',
            minWidth: '300px',
            minHeight: '300px',
            maxWidth: '90vw',
            maxHeight: '90vh',
            resize: 'both',
            overflow: 'hidden'
          }}
        >
          <div 
            className="bg-[#0f172a] text-white p-4 font-semibold flex justify-between items-center cursor-move select-none touch-none"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
          >
            <div className="flex items-center gap-2 pointer-events-none">
              <span className="w-2.5 h-2.5 rounded-full bg-[#b7410e] animate-pulse shadow-[0_0_8px_rgba(183,65,14,0.8)]" />
              <span className="text-white text-sm font-semibold tracking-wide">Rune (AI Runolog)</span>
            </div>
            <div className="flex items-center gap-1">
              <button 
                onClick={() => setIsMinimized(!isMinimized)} 
                className="opacity-70 hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-white/10"
                title={isMinimized ? "Maximera" : "Minimera"}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                  {isMinimized ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12h-15" />
                  )}
                </svg>
              </button>
              <button 
                onClick={() => { setIsOpen(false); setIsMinimized(false); }} 
                className="opacity-70 hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-white/10"
                title="Stäng"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          {!isMinimized && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                  <div className="text-slate-500 text-sm text-center mt-10">
                    <div className="w-16 h-16 mx-auto mb-4 opacity-30 rounded-full bg-slate-200 flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
                        <path fillRule="evenodd" d="M9 4.5a.75.75 0 01.721.544l.813 2.846a3.75 3.75 0 002.576 2.576l2.846.813a.75.75 0 010 1.442l-2.846.813a3.75 3.75 0 00-2.576 2.576l-.813 2.846a.75.75 0 01-1.442 0l-.813-2.846a3.75 3.75 0 00-2.576-2.576l-2.846-.813a.75.75 0 010-1.442l2.846-.813a3.75 3.75 0 002.576-2.576l.813-2.846A.75.75 0 019 4.5zM18 1.5a.75.75 0 01.728.568l.258 1.036c.236.94.97 1.674 1.91 1.91l1.036.258a.75.75 0 010 1.456l-1.036.258c-.94.236-1.674.97-1.91 1.91l-.258 1.036a.75.75 0 01-1.456 0l-.258-1.036a2.625 2.625 0 00-1.91-1.91l-1.036-.258a.75.75 0 010-1.456l1.036-.258a2.625 2.625 0 001.91-1.91l.258-1.036A.75.75 0 0118 1.5zM16.5 15a.75.75 0 01.712.513l.394 1.183c.15.447.5.799.948.948l1.183.395a.75.75 0 010 1.422l-1.183.395c-.447.15-.799.5-.948.948l-.395 1.183a.75.75 0 01-1.422 0l-.395-1.183a1.5 1.5 0 00-.948-.948l-1.183-.395a.75.75 0 010-1.422l1.183-.395c.447-.15.799-.5.948-.948l.395-1.183A.75.75 0 0116.5 15z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <p className="font-semibold text-slate-800 mb-2">Fråga mig om dina analyser!</p>
                    <p className="text-xs">Jag har automatisk tillgång till din senaste 3D- och lingvistikdata.</p>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div 
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${msg.role === 'user' ? 'bg-[#0f172a] text-white rounded-br-sm' : 'bg-white/70 text-slate-900 shadow-sm border border-white/50 rounded-bl-sm backdrop-blur-md'}`}
                      dangerouslySetInnerHTML={msg.role === 'model' ? formatMessage(msg.content) : undefined}
                    >
                      {msg.role === 'user' ? msg.content : null}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white/70 text-slate-500 rounded-2xl px-4 py-3 text-sm flex gap-1 items-center border border-white/50 rounded-bl-sm">
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" />
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-100" />
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={handleSubmit} className="p-3 border-t border-slate-900/10 bg-white/40 backdrop-blur-md">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Fråga AI:n..." 
                  className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 shadow-inner"
                />
              </form>
            </>
          )}
        </div>
      )}

      {/* Floating Action Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 bg-[#0f172a] text-white rounded-full shadow-2xl shadow-[#b7410e]/20 flex items-center justify-center hover:scale-105 active:scale-95 transition-all relative"
      >
        {!isOpen && messages.length > 0 && (
          <span className="absolute top-0 right-0 w-3.5 h-3.5 bg-red-500 border-2 border-[#e2e7ec] rounded-full" />
        )}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
        </svg>
      </button>
    </div>
  );
}
