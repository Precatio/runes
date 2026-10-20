"use client";

import { useState, useSyncExternalStore } from "react";
import { useLanguage } from "@/components/LanguageContext";
import { trackClick } from "@/lib/track";

// A vote on the articles page: which content readers want more of. Up to three topics and an own suggestion, sent as
// anonymous click rows in the visitor statistics (lib/track.ts: label "rost:<topic>" and "rost-eget:<text>"), so no
// new database rule is needed; one vote per browser. The founder sees the result in Admin (src/site_stats.py, the
// topics' names in VOTE_TOPICS there – keep the keys the same).
const KEY = "vitki-vote-innehall";
const MAX = 3;
const OWN_MAX = 70;
const TOPICS: { key: string; sv: string; en: string }[] = [
  { key: "ristare", sv: "Ristarna och deras händer", en: "The carvers and their hands" },
  { key: "tro", sv: "Tro – från Tor till Kristus", en: "Belief – from Thor to Christ" },
  { key: "kvinnor", sv: "Kvinnor och barn på stenarna", en: "Women and children on the stones" },
  { key: "fard", sv: "Vikingafärder: England, Grekland, Ingvar", en: "Viking journeys: England, Greece, Ingvar" },
  { key: "sprak", sv: "Språket och stavningen", en: "Language and spelling" },
  { key: "lasning", sv: "Skadade och olästa inskrifter", en: "Damaged and unread inscriptions" },
  { key: "landskap", sv: "Stenarna i landskapet", en: "The stones in the landscape" },
  { key: "magi", sv: "Magi, förbannelser och skydd", en: "Magic, curses and protection" },
  { key: "eddan", sv: "Eddan och fornnordisk dikt", en: "The Edda and Old Norse poetry" },
  { key: "norden", sv: "Danmark, Norge och gränserna", en: "Denmark, Norway and the borders" },
  { key: "metod", sv: "Hur metoderna fungerar – statistik och 3D", en: "How the methods work – statistics and 3D" },
  { key: "guider", sv: "Guider till Vitki, steg för steg", en: "Step-by-step guides to Vitki" },
];

const stored = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
const noop = () => () => {};

export default function ContentVote() {
  const { lang } = useLanguage();
  const en = lang === "en";
  const earlier = useSyncExternalStore(noop, stored, () => null);
  const [sent, setSent] = useState(false);
  const [picked, setPicked] = useState<string[]>([]);
  const [own, setOwn] = useState("");
  const done = sent || !!earlier;

  const toggle = (k: string) =>
    setPicked(p => (p.includes(k) ? p.filter(x => x !== k) : p.length < MAX ? [...p, k] : p));
  const send = () => {
    for (const k of picked) trackClick(`rost:${k}`);
    const text = own.trim().replace(/\s+/g, " ").slice(0, OWN_MAX);
    if (text) trackClick(`rost-eget:${text}`);
    try { localStorage.setItem(KEY, new Date().toISOString().slice(0, 10)); } catch { /* the vote is counted anyway */ }
    setSent(true);
  };

  return (
    <div className="mt-14 rounded-2xl border border-[#b7410e]/30 bg-[#fbf3ee] p-6" translate="no">
      <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">{en ? "Your vote" : "Din röst"}</div>
      <h2 className="mt-2 text-xl font-serif font-bold text-slate-900">{en ? "What would you like to read more about?" : "Vad vill du läsa mer om?"}</h2>
      {done ? (
        <p className="mt-2 text-slate-700">
          {en ? "Thank you! Your vote helps us choose what to write about next." : "Tack! Din röst hjälper oss att välja vad vi skriver om härnäst."}
        </p>
      ) : (
        <>
          <p className="mt-2 text-slate-700 leading-relaxed">
            {en ? `Choose up to ${MAX} topics, or write your own suggestion.` : `Välj upp till ${MAX} ämnen, eller skriv ett eget förslag.`}
          </p>
          <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label={en ? "Topics" : "Ämnen"}>
            {TOPICS.map(t => {
              const on = picked.includes(t.key);
              return (
                <button key={t.key} type="button" onClick={() => toggle(t.key)} aria-pressed={on}
                  disabled={!on && picked.length >= MAX}
                  className={`px-3.5 py-2 rounded-full border text-sm font-semibold transition-colors disabled:opacity-40 ${on
                    ? "bg-[#b7410e] border-[#b7410e] text-white" : "bg-white border-slate-300 text-slate-800 hover:border-[#b7410e]/60"}`}>
                  {on ? "✓ " : ""}{en ? t.en : t.sv}
                </button>
              );
            })}
          </div>
          <label className="mt-4 block text-sm font-semibold text-slate-700">
            {en ? "Your own suggestion (optional)" : "Eget förslag (valfritt)"}
            <input value={own} onChange={e => setOwn(e.target.value)} maxLength={OWN_MAX}
              placeholder={en ? "e.g. a particular stone, region or question" : "t.ex. en viss sten, en trakt eller en fråga"}
              className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900" />
          </label>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button type="button" onClick={send} disabled={!picked.length && !own.trim()}
              className="px-5 py-2.5 rounded-full bg-[#b7410e] text-white text-sm font-bold hover:bg-[#9a350b] disabled:opacity-40">
              {en ? "Send my vote" : "Skicka min röst"}
            </button>
            <span className="text-xs text-slate-500">
              {en ? "Anonymous: only your choices are saved. Please do not write personal details."
                  : "Anonymt: bara dina val sparas. Skriv inga personuppgifter."}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
