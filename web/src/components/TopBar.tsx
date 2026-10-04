/* eslint-disable @next/next/no-img-element */

"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "./AuthContext";

export default function TopBar() {
  const router = useRouter();
  const { user, loginWithGoogle } = useAuth();
  const [isFocused, setIsFocused] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const getInitials = (name: string) => {
    return name.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 2);
  };

  // Keyboard shortcut CMD+K or CTRL+K to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="w-full flex items-center justify-between px-4 py-3 flex-shrink-0 z-30">
      <div className="flex-1" />
      
      {/* Spotlight Search (High Contrast Liquid Glass Pill) */}
      <div 
        className={`relative max-w-md w-full transition-all duration-300 ease-out ${
          isFocused ? "scale-[1.02]" : "scale-100"
        }`}
      >
        <div className="liquid-glass-input-wrapper rounded-full flex items-center px-4 py-2 transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className={`w-4 h-4 mr-3 transition-colors duration-300 ${isFocused ? 'text-slate-900' : 'text-slate-500'}`}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input 
            ref={inputRef}
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={isFocused ? "Sök på sten, plats, eller analys..." : "Sök (Kortkommando: Cmd+K)"} 
            className="w-full bg-transparent text-[14px] font-semibold text-slate-900 placeholder:text-slate-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="flex-1 flex justify-end items-center gap-4">
        <div className="flex items-center gap-4">
          {/* Generate Report Quick Button */}
          <button 
            onClick={() => router.push("/report/current")}
            title="Generera Akademisk Rapport för aktuellt arbetspass"
            className="p-2 text-slate-500 hover:text-white bg-white hover:bg-[#b7410e] rounded-full transition-colors border border-slate-200"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </button>
          


          {/* User Profile Pill */}
          <div className="relative">
            {user ? (
              <Link 
                href="/account"
                title="Mitt Konto"
                className="flex items-center gap-2 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-full transition-colors"
              >
                {user.photoURL ? (
                  <img src={user.photoURL} alt="Profile" className="w-6 h-6 rounded-full" />
                ) : (
                  <div className="w-6 h-6 bg-slate-900 text-white rounded-full flex items-center justify-center font-bold text-[10px]">
                    {getInitials(user.displayName || user.email || "?")}
                  </div>
                )}
                <span className="text-xs font-bold text-slate-700">{user.displayName || user.email}</span>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3 text-slate-400">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                </svg>
              </Link>
            ) : (
              <button 
                onClick={loginWithGoogle}
                className="flex items-center gap-2 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-full transition-colors"
              >
                <div className="w-6 h-6 bg-slate-200 text-slate-500 rounded-full flex items-center justify-center font-bold text-[10px]">
                  ?
                </div>
                <span className="text-xs font-bold text-slate-700">Logga in</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
