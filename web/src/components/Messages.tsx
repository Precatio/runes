"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Timestamp } from "firebase/firestore";
import { firestoreLib } from "@/firebase/config";
import { API_URL } from "@/lib/api";
import { useAuth } from "./AuthContext";

// createdAt is a Firestore timestamp for the account's own messages and an ISO date for the messages to everyone (GET /api/messages)
interface Message { id: string; title: string; body: string; to: string; level: "info" | "viktigt"; createdAt?: Timestamp | string }
const millis = (t?: Timestamp | string) => (!t ? 0 : typeof t === "string" ? Date.parse(t) : t.toMillis());

const READ_KEY = "vitki_read_messages";

function readIds(): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(READ_KEY) || "[]")); } catch { return new Set(); }
}

// Messages from the app's founder (to everyone, or to the signed-in account), under a bell in the top bar
export default function Messages() {
  const { user, accountNotice } = useAuth();
  const [all, setAll] = useState<Message[]>([]);
  const [mine, setMine] = useState<Message[]>([]);
  const [read, setRead] = useState<Set<string>>(() => (typeof window === "undefined" ? new Set() : readIds()));
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  // The messages to everyone come from the server; only a signed-in account listens to its own in Firestore
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/messages`).then(r => (r.ok ? r.json() : { messages: [] }))
      .then(d => { if (!cancelled) setAll(d.messages ?? []); }).catch(() => { if (!cancelled) setAll([]); });
    return () => { cancelled = true; };
  }, []);
  useEffect(() => {
    if (!user) return;
    let unsub = () => {};
    let cancelled = false;
    firestoreLib().then(({ db, collection, onSnapshot, query, where }) => {
      if (cancelled) return;
      unsub = onSnapshot(query(collection(db, "messages"), where("to", "==", user.uid)),
        s => setMine(s.docs.map(d => ({ id: d.id, ...d.data() }) as Message)), () => setMine([]));
    }).catch(() => setMine([]));
    return () => { cancelled = true; unsub(); };
  }, [user]);

  // Close when clicking outside the panel
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    window.addEventListener("mousedown", close);
    return () => window.removeEventListener("mousedown", close);
  }, [open]);

  const messages = useMemo(() => [...all, ...(user ? mine : [])]
    .sort((a, b) => millis(b.createdAt) - millis(a.createdAt)), [all, mine, user]);
  const unread = messages.filter(m => !read.has(m.id));
  const important = unread.some(m => m.level === "viktigt");
  const markRead = () => {
    const next = new Set([...read, ...messages.map(m => m.id)]);
    setRead(next);
    try { localStorage.setItem(READ_KEY, JSON.stringify([...next])); } catch { /* private window */ }
  };

  return (
    <div className="relative" ref={box}>
      <button onClick={() => setOpen(o => !o)} aria-label={`Meddelanden${unread.length ? `, ${unread.length} olästa` : ""}`}
        className="relative p-2 text-slate-500 hover:text-slate-900 bg-white rounded-full border border-slate-200 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
        {unread.length > 0 && (
          <span className={`absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold text-white flex items-center justify-center ${important ? "bg-red-600" : "bg-[#b7410e]"}`}>
            {unread.length}
          </span>
        )}
      </button>
      {accountNotice && (
        <div className="absolute right-0 top-12 w-[min(20rem,calc(100vw-2rem))] rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 shadow-xl z-50">
          {accountNotice}
        </div>
      )}
      {open && (
        <div className="absolute right-0 top-12 w-[min(24rem,calc(100vw-1.5rem))] max-h-[70dvh] overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <span className="font-bold text-slate-900">Meddelanden</span>
            {unread.length > 0 && <button onClick={markRead} className="text-xs font-semibold text-[#b7410e] hover:underline">Markera som lästa</button>}
          </div>
          {messages.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">Inga meddelanden.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {messages.map(m => (
                <li key={m.id} className={`px-4 py-3 ${read.has(m.id) ? "" : "bg-[#b7410e]/[0.04]"}`}>
                  <div className="flex items-center gap-2">
                    {m.level === "viktigt" && <span className="rounded-md bg-red-50 border border-red-200 px-1.5 text-[10px] font-bold text-red-700">viktigt</span>}
                    {m.to !== "all" && <span className="rounded-md bg-slate-100 px-1.5 text-[10px] font-bold text-slate-600">till dig</span>}
                    <span className="font-semibold text-sm text-slate-900">{m.title}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-700 whitespace-pre-wrap">{m.body}</p>
                  {m.createdAt && <p className="mt-1 text-[11px] text-slate-400">{new Date(millis(m.createdAt)).toLocaleString("sv-SE", { dateStyle: "medium", timeStyle: "short" })}</p>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
