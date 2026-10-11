"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";

// The app's frame: the sidebar is fixed on wide screens and a drawer (opened from the top bar) on phones and tablets
export default function AppShell({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="flex h-dvh overflow-hidden">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      {menuOpen && (
        <button aria-label="Stäng menyn" onClick={() => setMenuOpen(false)}
          className="lg:hidden fixed inset-0 z-40 bg-slate-900/30 backdrop-blur-[2px]" />
      )}
      <main className="flex-1 min-w-0 flex flex-col h-[calc(100dvh-1rem)] sm:h-[calc(100dvh-2rem)] m-2 sm:m-4 rounded-[22px] sm:rounded-[32px] liquid-glass relative z-10 overflow-hidden shadow-2xl transition-all duration-300">
        <TopBar onMenu={() => setMenuOpen(true)} />
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 sm:p-6 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
