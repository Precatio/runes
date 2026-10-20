"use client";

import Link from "next/link";
import { isType, labelName, labelPath } from "@/lib/labels";

// The article's labels as small chips: the type in rust, the subjects in grey; each links to the list filtered on it.
// Inside a card that is itself a link the chips are plain text (a link in a link is not allowed), so `linked` turns it off.
export default function LabelChips({ labels, lang, linked = false, className = "" }:
  { labels?: string[]; lang: string; linked?: boolean; className?: string }) {
  if (!labels?.length) return null;
  return (
    <ul className={`flex flex-wrap gap-1.5 ${className}`} aria-label={lang === "en" ? "Labels" : "Etiketter"}>
      {labels.map(l => {
        const type = isType(l);
        const cls = `inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-bold tracking-wide ${
          type ? "border-[#b7410e]/40 bg-[#fbf3ee] text-[#b7410e]" : "border-slate-300 bg-white/80 text-slate-600"}`;
        return (
          <li key={l}>
            {linked
              ? <Link href={labelPath(l, lang)} className={`${cls} hover:border-[#b7410e]`}>{labelName(l, lang)}</Link>
              : <span className={cls}>{labelName(l, lang)}</span>}
          </li>
        );
      })}
    </ul>
  );
}
