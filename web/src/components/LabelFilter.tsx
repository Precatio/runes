"use client";

import { useSyncExternalStore } from "react";
import type { BlogPost } from "@/components/BlogBody";
import { SUBJECTS, TYPES, labelName } from "@/lib/labels";

/** The label in the address (?etikett=…): read from the browser's address so that a chip link opens the list filtered,
 * and kept there when the reader chooses another, without a page load. On the server there is no label. */
const EVENT = "vitki-etikett";
const subscribe = (cb: () => void) => {
  window.addEventListener("popstate", cb);
  window.addEventListener(EVENT, cb);
  return () => { window.removeEventListener("popstate", cb); window.removeEventListener(EVENT, cb); };
};
const read = () => new URLSearchParams(window.location.search).get("etikett");
export function useLabelFromAddress(): [string | null, (l: string | null) => void] {
  const label = useSyncExternalStore(subscribe, read, () => null);
  const choose = (l: string | null) => {
    const url = new URL(window.location.href);
    if (l) url.searchParams.set("etikett", l); else url.searchParams.delete("etikett");
    window.history.replaceState(null, "", url.toString());
    window.dispatchEvent(new Event(EVENT));
  };
  return [label, choose];
}

export const withLabel = (posts: BlogPost[], label: string | null) =>
  label ? posts.filter(p => p.labels?.includes(label)) : posts;

// Two rows of chips – what kind of article, and what it is about – with the number of articles behind each; one
// label at a time, and "Alla" clears it. Labels that no listed article carries are left out.
export default function LabelFilter({ posts, lang, value, onChange }:
  { posts: BlogPost[]; lang: string; value: string | null; onChange: (l: string | null) => void }) {
  const count = (l: string) => posts.filter(p => p.labels?.includes(l)).length;
  const row = (pairs: [string, string][]) => pairs.filter(([sv]) => count(sv) > 0);
  const types = row(TYPES), subjects = row(SUBJECTS);
  if (!types.length && !subjects.length) return null;
  const chip = (l: string | null, text: string, n?: number) => {
    const on = value === l;
    return (
      <button key={l ?? "alla"} type="button" onClick={() => onChange(on ? null : l)} aria-pressed={on}
        className={`rounded-full border px-3 py-1 text-[13px] font-semibold transition ${
          on ? "border-[#b7410e] bg-[#b7410e] text-white" : "border-slate-300 bg-white/80 text-slate-700 hover:border-[#b7410e]"}`}>
        {text}{n != null && <span className={`ml-1.5 text-[11px] ${on ? "text-white/80" : "text-slate-400"}`}>{n}</span>}
      </button>
    );
  };
  return (
    <div className="space-y-2.5" aria-label={lang === "en" ? "Filter the articles" : "Filtrera artiklarna"}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="w-16 shrink-0 text-[11px] font-bold uppercase tracking-wider text-slate-500">{lang === "en" ? "Kind" : "Typ"}</span>
        {chip(null, lang === "en" ? "All" : "Alla", posts.length)}
        {types.map(([sv]) => chip(sv, labelName(sv, lang), count(sv)))}
      </div>
      {subjects.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="w-16 shrink-0 text-[11px] font-bold uppercase tracking-wider text-slate-500">{lang === "en" ? "Subject" : "Ämne"}</span>
          {subjects.map(([sv]) => chip(sv, labelName(sv, lang), count(sv)))}
        </div>
      )}
    </div>
  );
}
