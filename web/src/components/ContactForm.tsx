"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageContext";
import { CONTACT_ENDPOINT, CONTACT_SERVICE_URL } from "@/lib/site";

// The contact form on the public website. The site is static (GitHub Pages) and has no server of its own, so the
// message is sent through FormSubmit, which emails it on to the founder; the sender's address becomes the reply-to.
// A hidden field (_honey) that people never fill in stops the simplest spam robots.
const MAX = { name: 120, email: 200, message: 5000 };

type State = "idle" | "busy" | "sent" | "error";

export default function ContactForm() {
  const { lang } = useLanguage();
  const en = lang === "en";
  const [state, setState] = useState<State>("idle");
  const [form, setForm] = useState({ name: "", email: "", message: "", _honey: "" });
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form._honey) { setState("sent"); return; }
    setState("busy");
    try {
      const r = await fetch(CONTACT_ENDPOINT, {
        method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          name: form.name.trim(), email: form.email.trim(), message: form.message.trim(),
          _replyto: form.email.trim(), _subject: `Vitki: meddelande från ${form.name.trim() || "webbplatsen"}`,
          _template: "table", _captcha: "false", _honey: "", sida: typeof window !== "undefined" ? window.location.href : "",
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || String(d.success) === "false") throw new Error(d.message || String(r.status));
      setState("sent");
    } catch {
      setState("error");
    }
  };

  const field = "mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 " +
                "focus:border-[#b7410e] focus:outline-none focus:ring-2 focus:ring-[#b7410e]/20";
  const label = "block text-sm font-semibold text-slate-700";

  if (state === "sent") {
    return (
      <div className="rounded-2xl border border-[#b7410e]/30 bg-[#fbf3ee] p-6" translate="no" role="status">
        <h2 className="text-xl font-serif font-bold">{en ? "Thank you for your message!" : "Tack för ditt meddelande!"}</h2>
        <p className="mt-2 text-slate-700 leading-relaxed">
          {en ? "It has been sent. I read everything and will answer as soon as I can."
              : "Det är skickat. Jag läser allt och svarar så snart jag kan."}
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={send} className="space-y-5" translate="no">
      <div className="grid gap-5 sm:grid-cols-2">
        <label className={label}>{en ? "Name" : "Namn"}
          <input required maxLength={MAX.name} autoComplete="name" value={form.name} onChange={set("name")} className={field} />
        </label>
        <label className={label}>{en ? "Email" : "E-post"}
          <input required type="email" maxLength={MAX.email} autoComplete="email" value={form.email} onChange={set("email")} className={field} />
        </label>
      </div>
      <label className={label}>{en ? "Message" : "Meddelande"}
        <textarea required rows={7} maxLength={MAX.message} value={form.message} onChange={set("message")} className={field} />
      </label>
      {/* Hidden from people; robots that fill in every field give themselves away */}
      <div aria-hidden className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
        <label>Lämna tomt<input tabIndex={-1} autoComplete="off" value={form._honey} onChange={set("_honey")} /></label>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <button type="submit" disabled={state === "busy"}
          className="px-7 py-3 rounded-full bg-[#b7410e] text-white font-bold hover:bg-[#9a350b] disabled:opacity-50">
          {state === "busy" ? (en ? "Sending…" : "Skickar…") : (en ? "Send" : "Skicka")}
        </button>
        {state === "error" && (
          <p className="text-sm text-red-700" role="alert">
            {en ? "The message could not be sent just now. Please try again in a while."
                : "Meddelandet kunde inte skickas just nu. Försök gärna igen om en stund."}
          </p>
        )}
      </div>
      <p className="text-xs text-slate-500 leading-relaxed">
        {en ? <>The message is sent by email to Viktor Kvant through the service <a href={CONTACT_SERVICE_URL} target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-900">FormSubmit</a>. Your name and address are used only to answer you and are not saved on this website.</>
            : <>Meddelandet skickas med e-post till Viktor Kvant via tjänsten <a href={CONTACT_SERVICE_URL} target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-900">FormSubmit</a>. Ditt namn och din adress används bara för att svara dig och sparas inte på webbplatsen.</>}
      </p>
    </form>
  );
}
