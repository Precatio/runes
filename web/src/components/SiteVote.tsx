"use client";

import { useState, useSyncExternalStore } from "react";
import { useLanguage } from "@/components/LanguageContext";
import { DOWNLOAD_URL, SITE_PROJECT, siteCollection } from "@/lib/site";

// A vote on the start page: should Vitki also be usable in the browser, without installing anything? The vote is
// written straight to Firestore through its REST interface (the rules in firestore.rules allow exactly this and nothing
// else), one per browser; the result is shown only to the founder, in Admin.
const KEY = "vitki-vote-webbapp";
const URL_ = siteCollection("site_votes");

// The vote this browser has already cast (localStorage), read without a render on the server: there it is always none
const stored = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
const noop = () => () => {};

export default function SiteVote() {
  const { lang } = useLanguage();
  const en = lang === "en";
  const earlier = useSyncExternalStore(noop, stored, () => null);
  const [justVoted, setVoted] = useState<string | null>(null);
  const voted = justVoted ?? earlier;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  if (!SITE_PROJECT) return null;

  const vote = async (choice: "ja" | "nej") => {
    setBusy(true); setError(false);
    try {
      const r = await fetch(URL_, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields: { question: { stringValue: "webbapp" }, choice: { stringValue: choice }, lang: { stringValue: en ? "en" : "sv" } } }),
      });
      if (!r.ok) throw new Error(String(r.status));
      try { localStorage.setItem(KEY, choice); } catch { /* the vote is counted anyway */ }
      setVoted(choice);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-12 mx-auto max-w-xl rounded-2xl border border-[#b7410e]/30 bg-[#fbf3ee] p-6 text-left" translate="no">
      <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">{en ? "Your vote" : "Din röst"}</div>
      <h3 className="mt-2 text-xl font-serif font-bold text-slate-900">{en ? "Vitki in the browser?" : "Vitki i webbläsaren?"}</h3>
      {voted ? (
        <p className="mt-2 text-slate-700">{en ? "Thank you for voting! It helps us decide what to build next." : "Tack för din röst! Den hjälper oss att välja vad vi bygger härnäst."}</p>
      ) : (
        <>
          <p className="mt-2 text-slate-700 leading-relaxed">
            {en ? "Today you install Vitki on your own computer. Would you rather use it straight in the browser, with no setup?"
                : "I dag installerar du Vitki på din egen dator. Skulle du hellre använda den direkt i webbläsaren, utan installation?"}
          </p>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            {en ? "Installing it yourself takes Python and Node.js, a few commands in the terminal and preferably R for the statistics – plus your own API key for the AI features. "
                : "Egen installation kräver i dag Python och Node.js, några kommandon i terminalen och helst R för statistiken – för AI-funktionerna också en egen API-nyckel. "}
            <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#b7410e] hover:underline">
              {en ? "See the instructions" : "Se anvisningen"}
            </a>
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" onClick={() => vote("ja")} disabled={busy}
              className="px-5 py-2.5 rounded-full bg-[#b7410e] text-white text-sm font-bold hover:bg-[#9a350b] disabled:opacity-50">
              {en ? "Yes, please" : "Ja, gärna"}
            </button>
            <button type="button" onClick={() => vote("nej")} disabled={busy}
              className="px-5 py-2.5 rounded-full bg-white border border-slate-300 text-sm font-bold hover:border-slate-900 disabled:opacity-50">
              {en ? "No, I install it myself" : "Nej, jag installerar själv"}
            </button>
          </div>
          {error && <p className="mt-3 text-sm text-red-700">{en ? "The vote could not be sent just now. Please try again later." : "Rösten kunde inte skickas just nu. Försök gärna igen senare."}</p>}
          <p className="mt-3 text-xs text-slate-500">{en ? "Anonymous: only your choice is saved." : "Anonymt: bara ditt val sparas."}</p>
        </>
      )}
    </div>
  );
}
