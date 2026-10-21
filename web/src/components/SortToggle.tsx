"use client";

import { useSyncExternalStore } from "react";
import type { BlogPost } from "@/components/BlogBody";
import { hasViews, type Order } from "@/lib/featured";

/** The order in the address (?sortera=mest-lasta): kept there like the label, so that a link can open the list
 * sorted by what readers have read most, and the choice survives a reload. On the server the order is the newest. */
const EVENT = "vitki-sortera";
const subscribe = (cb: () => void) => {
  window.addEventListener("popstate", cb);
  window.addEventListener(EVENT, cb);
  return () => { window.removeEventListener("popstate", cb); window.removeEventListener(EVENT, cb); };
};
const read = (): Order => (new URLSearchParams(window.location.search).get("sortera") === "mest-lasta" ? "mest-lasta" : "senaste");
export function useOrderFromAddress(): [Order, (o: Order) => void] {
  const order = useSyncExternalStore(subscribe, read, () => "senaste" as Order);
  const choose = (o: Order) => {
    const url = new URL(window.location.href);
    if (o === "mest-lasta") url.searchParams.set("sortera", o); else url.searchParams.delete("sortera");
    window.history.replaceState(null, "", url.toString());
    window.dispatchEvent(new Event(EVENT));
  };
  return [order, choose];
}

// Two buttons, newest or most read; shown once the website has counted page views on at least one article
export default function SortToggle({ posts, lang, value, onChange, className = "" }:
  { posts: BlogPost[]; lang: string; value: Order; onChange: (o: Order) => void; className?: string }) {
  if (!hasViews(posts)) return null;
  const en = lang === "en";
  const options: [Order, string][] = [["senaste", en ? "Newest" : "Senaste"], ["mest-lasta", en ? "Most read" : "Mest lästa"]];
  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`} role="group" aria-label={en ? "Sort the articles" : "Sortera artiklarna"}>
      <span className="w-16 shrink-0 text-[11px] font-bold uppercase tracking-wider text-slate-500">{en ? "Order" : "Ordning"}</span>
      {options.map(([o, text]) => {
        const on = value === o;
        return (
          <button key={o} type="button" onClick={() => onChange(o)} aria-pressed={on}
            className={`rounded-full border px-3 py-1 text-[13px] font-semibold transition ${
              on ? "border-[#b7410e] bg-[#b7410e] text-white" : "border-slate-300 bg-white/80 text-slate-700 hover:border-[#b7410e]"}`}>
            {text}
          </button>
        );
      })}
      {value === "mest-lasta" && (
        <span className="text-xs text-slate-500">{en ? "By page views on vitkirunor.se, updated when the site is published." : "Efter sidvisningar på vitkirunor.se, uppdaterat när webbplatsen publiceras."}</span>
      )}
    </div>
  );
}
