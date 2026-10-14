/* eslint-disable @next/next/no-img-element */
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/AuthContext";
import { API_URL } from "@/lib/api";
import BlogAdmin from "@/components/BlogAdmin";
import GithubStats from "@/components/GithubStats";
import SiteVotes from "@/components/SiteVotes";

interface UserRow {
  uid: string; email: string | null; name: string | null; photo: string | null; disabled: boolean;
  created: string | null; last_sign_in: string | null; providers: string[];
}
interface Users {
  summary: { total: number; disabled: number; new_7d: number; new_30d: number; active_30d: number };
  per_month: Record<string, number>;
  users: UserRow[];
}
interface SentMessage { id: string; title: string; body: string; to: string; level: string; createdAt: string }

const field = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none w-full";
const date = (s: string | null) => (s ? new Date(s).toLocaleDateString("sv-SE", { dateStyle: "medium" }) : "–");

// The founder's admin: who has registered, suspending accounts, messages in the app (api/routers/admin.py) and the
// articles (api/routers/blog.py)
export default function AdminPage() {
  const { user, isAdmin, authHeaders, loading } = useAuth();
  const [users, setUsers] = useState<Users | null>(null);
  const [messages, setMessages] = useState<SentMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [draft, setDraft] = useState({ title: "", body: "", to: "all", level: "info" });
  const [sent, setSent] = useState<string | null>(null);

  const call = useCallback(async (path: string, init: RequestInit = {}) => {
    const r = await fetch(`${API_URL}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(await authHeaders()), ...(init.headers ?? {}) } });
    if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail || `Fel ${r.status}`);
    return r.json();
  }, [authHeaders]);

  const load = useCallback(() => {
    setError(null);
    call("/api/admin/users").then(setUsers).catch(e => setError(e.message));
    call("/api/admin/messages").then(d => setMessages(d.messages)).catch(e => setError(e.message));
  }, [call]);

  useEffect(() => {
    if (!isAdmin) return;
    let cancelled = false;
    Promise.all([call("/api/admin/users"), call("/api/admin/messages")])
      .then(([u, m]) => { if (!cancelled) { setUsers(u); setMessages(m.messages); } })
      .catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [isAdmin, call]);

  const shown = useMemo(() => (users?.users ?? []).filter(u => !filter
    || `${u.email ?? ""} ${u.name ?? ""} ${u.uid}`.toLowerCase().includes(filter.toLowerCase())), [users, filter]);
  const months = Object.entries(users?.per_month ?? {});
  const maxMonth = Math.max(1, ...months.map(([, n]) => n));

  const toggleBan = async (u: UserRow) => {
    let reason = "";
    if (!u.disabled) {
      const answer = window.prompt(`Stäng av ${u.email ?? u.uid}? Kontot kan då inte logga in. Skäl (sparas, visas inte för användaren):`, "");
      if (answer === null) return;
      reason = answer;
    } else if (!window.confirm(`Öppna ${u.email ?? u.uid} igen?`)) return;
    setBusy(u.uid);
    try {
      await call(`/api/admin/users/${encodeURIComponent(u.uid)}/${u.disabled ? "unban" : "ban"}`, { method: "POST", body: JSON.stringify({ reason }) });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Det gick inte.");
    } finally {
      setBusy(null);
    }
  };

  const send = async () => {
    setBusy("send"); setSent(null);
    try {
      await call("/api/admin/messages", { method: "POST", body: JSON.stringify(draft) });
      const who = draft.to === "all" ? "alla" : users?.users.find(u => u.uid === draft.to)?.email ?? draft.to;
      setSent(`Skickat till ${who}.`);
      setDraft({ title: "", body: "", to: "all", level: "info" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Meddelandet kunde inte skickas.");
    } finally {
      setBusy(null);
    }
  };

  const remove = async (id: string) => {
    if (!window.confirm("Ta bort meddelandet? Det försvinner för alla mottagare.")) return;
    try { await call(`/api/admin/messages/${encodeURIComponent(id)}`, { method: "DELETE" }); load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Det gick inte."); }
  };

  if (loading) return null;
  if (!user || !isAdmin) {
    return (
      <div className="max-w-xl mx-auto mt-16 liquid-glass-island rounded-[28px] p-8 text-center">
        <h2 className="text-2xl font-bold text-slate-900">Admin</h2>
        <p className="mt-2 text-slate-600">Den här sidan är bara för appens grundare.</p>
      </div>
    );
  }

  const tile = (label: string, value: number, note?: string) => (
    <div className="liquid-glass-island rounded-2xl p-4">
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-3xl font-bold text-slate-900">{value.toLocaleString("sv-SE")}</div>
      {note && <div className="text-[11px] text-slate-500">{note}</div>}
    </div>
  );

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto gap-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Admin</h2>
        <p className="text-slate-600 max-w-3xl">Registrerade konton, avstängning, meddelanden i appen och månadens blogginlägg. Bara du ser sidan.</p>
      </div>
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}

      {users && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {tile("Registrerade", users.summary.total)}
            {tile("Nya, 7 dagar", users.summary.new_7d)}
            {tile("Nya, 30 dagar", users.summary.new_30d)}
            {tile("Aktiva, 30 dagar", users.summary.active_30d, "loggat in")}
            {tile("Avstängda", users.summary.disabled)}
          </div>
          {months.length > 0 && (
            <div className="liquid-glass-island rounded-2xl p-4">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">Registreringar per månad</div>
              <div className="space-y-1">
                {months.map(([m, n]) => (
                  <div key={m} className="flex items-center gap-3 text-xs">
                    <span className="w-16 shrink-0 font-mono text-slate-600">{m}</span>
                    <div className="h-3 rounded-r bg-[#b7410e]" style={{ width: `${(n / maxMonth) * 70}%` }} />
                    <span className="text-slate-700">{n}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <section className="liquid-glass-island rounded-[24px] p-4 sm:p-6 space-y-3">
        <h3 className="text-lg font-bold text-slate-900">Skicka ett meddelande</h3>
        <p className="text-sm text-slate-600">Visas under klockan i appens sidhuvud. Meddelanden till alla syns också för den som inte är inloggad.</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input value={draft.title} onChange={e => setDraft(d => ({ ...d, title: e.target.value }))} placeholder="Rubrik" maxLength={120} className={`${field} sm:col-span-3`} />
          <textarea value={draft.body} onChange={e => setDraft(d => ({ ...d, body: e.target.value }))} placeholder="Meddelande" rows={4} maxLength={4000} className={`${field} sm:col-span-3`} />
          <select value={draft.to} onChange={e => setDraft(d => ({ ...d, to: e.target.value }))} className={field}>
            <option value="all">Till alla</option>
            {(users?.users ?? []).filter(u => !u.disabled).map(u => <option key={u.uid} value={u.uid}>{u.email ?? u.name ?? u.uid}</option>)}
          </select>
          <select value={draft.level} onChange={e => setDraft(d => ({ ...d, level: e.target.value }))} className={field}>
            <option value="info">Information</option><option value="viktigt">Viktigt</option>
          </select>
          <button onClick={send} disabled={!draft.title.trim() || !draft.body.trim() || busy === "send"}
            className="px-4 py-2 rounded-xl bg-[#b7410e] text-white font-bold disabled:opacity-40">
            {busy === "send" ? "Skickar …" : "Skicka"}
          </button>
        </div>
        {sent && <p className="text-sm text-emerald-700 font-semibold">{sent}</p>}
        {messages.length > 0 && (
          <ul className="divide-y divide-slate-900/5 pt-2">
            {messages.map(m => (
              <li key={m.id} className="py-2 flex flex-wrap items-start gap-x-3 gap-y-1 text-sm">
                <span className="text-[11px] text-slate-500 w-24 shrink-0">{date(m.createdAt)}</span>
                <div className="min-w-0 flex-1">
                  <span className="font-semibold text-slate-900">{m.title}</span>
                  {m.level === "viktigt" && <span className="ml-2 text-[10px] font-bold text-red-700">viktigt</span>}
                  <span className="ml-2 text-xs text-slate-500">till {m.to === "all" ? "alla" : users?.users.find(u => u.uid === m.to)?.email ?? m.to}</span>
                  <p className="text-slate-600 whitespace-pre-wrap break-words">{m.body}</p>
                </div>
                <button onClick={() => remove(m.id)} className="text-xs font-semibold text-slate-500 hover:text-red-700">Ta bort</button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <GithubStats call={call} />

      <SiteVotes call={call} />

      <BlogAdmin call={call} />

      <section className="liquid-glass-island rounded-[24px] p-4 sm:p-6 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-lg font-bold text-slate-900">Konton</h3>
          <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Sök e-post eller namn" className={`${field} max-w-xs`} />
          <button onClick={load} className="text-xs font-semibold text-[#b7410e] hover:underline">Uppdatera</button>
        </div>
        <ul className="divide-y divide-slate-900/5">
          {shown.map(u => (
            <li key={u.uid} className="py-3 flex flex-wrap items-center gap-x-4 gap-y-2">
              {u.photo ? <img src={u.photo} alt="" className="w-8 h-8 rounded-full" /> : <div className="w-8 h-8 rounded-full bg-slate-200" />}
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-slate-900 truncate">{u.name ?? u.email ?? u.uid}
                  {u.uid === user.uid && <span className="ml-2 text-[10px] font-bold text-[#b7410e]">du</span>}
                  {u.disabled && <span className="ml-2 rounded-md bg-red-50 border border-red-200 px-1.5 text-[10px] font-bold text-red-700">avstängd</span>}
                </div>
                <div className="text-xs text-slate-500 truncate">{u.email}</div>
              </div>
              <div className="text-xs text-slate-600 w-full sm:w-auto">Registrerad {date(u.created)} · senast inloggad {date(u.last_sign_in)}</div>
              <div className="flex gap-2">
                <button onClick={() => { setDraft(d => ({ ...d, to: u.uid })); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                  disabled={u.disabled} className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold disabled:opacity-40">Meddelande</button>
                {u.uid !== user.uid && (
                  <button onClick={() => toggleBan(u)} disabled={busy === u.uid}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${u.disabled ? "border-slate-300 bg-white text-slate-700" : "border-red-300 bg-red-50 text-red-700"}`}>
                    {busy === u.uid ? "…" : u.disabled ? "Öppna igen" : "Stäng av"}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
        {users && shown.length === 0 && <p className="text-sm text-slate-500">Inga konton matchar.</p>}
      </section>
    </div>
  );
}
