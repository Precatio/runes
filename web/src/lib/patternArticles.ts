"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { API_URL } from "@/lib/api";

// The articles written about the R patterns (GET /api/r/pattern-articles), and whether patterns that already have an
// article are hidden. The choice is the same on Statistik and Forskningsluckor and is remembered in this browser.
export interface PatternArticle { title: string; slug: string; published: boolean }
type Articles = Record<string, PatternArticle[]>;

export const patternKey = (p: { topic: string; key?: string }) => `${p.topic}|${p.key ?? ""}`;

let cache: Articles | null = null;
let pending: Promise<Articles> | null = null;

export function usePatternArticles(): Articles {
  const [articles, setArticles] = useState<Articles>(cache ?? {});
  useEffect(() => {
    if (cache) return;
    pending ??= fetch(`${API_URL}/api/r/pattern-articles`).then(r => (r.ok ? r.json() : { articles: {} }))
      .then(d => (cache = d.articles ?? {})).catch(() => ({}));
    pending.then(setArticles);
  }, []);
  return articles;
}

const KEY = "vitki_hide_written";
const listeners = new Set<() => void>();
function read(): boolean {
  try { return localStorage.getItem(KEY) === "1"; } catch { return false; }
}
function subscribe(fn: () => void) {
  listeners.add(fn);
  return () => { listeners.delete(fn); };
}

export function useHideWritten(): [boolean, (v: boolean) => void] {
  const hide = useSyncExternalStore(subscribe, read, () => false);
  const set = (v: boolean) => {
    try { localStorage.setItem(KEY, v ? "1" : "0"); } catch { /* blocked storage: the choice lasts until reload */ }
    listeners.forEach(fn => fn());
  };
  return [hide, set];
}

/** The patterns to show: all, or those without an article when hiding is on; and how many were hidden. */
export function useWrittenFilter<T extends { topic: string; key?: string }>(patterns: T[]) {
  const articles = usePatternArticles();
  const [hide, setHide] = useHideWritten();
  const written = patterns.filter(p => (articles[patternKey(p)] ?? []).length > 0).length;
  const shown = hide ? patterns.filter(p => !(articles[patternKey(p)] ?? []).length) : patterns;
  return { articles, hide, setHide, written, shown };
}
