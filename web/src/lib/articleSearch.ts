// The article search shared by the articles page and the landing page: a slim index with plain text per
// published article (src/blog_search.py), fetched only when the search is used – locally from the analysis
// engine, on the static website from /artiklar-sok.json written by the export.
import { API_URL } from "@/lib/api";
import { PUBLIC_SITE } from "@/lib/site";

export interface IndexPost {
  slug: string; title: string; title_en: string;
  text: string; text_en: string; summary: string; summary_en: string;
}

let cache: IndexPost[] | null = null;
let pending: Promise<IndexPost[] | null> | null = null;

export async function loadIndex(): Promise<IndexPost[] | null> {
  if (cache) return cache;
  if (!pending) {
    const url = PUBLIC_SITE ? "/artiklar-sok.json" : `${API_URL}/api/blog/search_index`;
    pending = fetch(url)
      .then(r => (r.ok ? r.json() : null))
      .then(d => (d ? (cache = (d as { posts: IndexPost[] }).posts) : null))
      .catch(() => null)
      .finally(() => { pending = null; });
  }
  return pending;
}

export const searchTerms = (q: string) => q.toLowerCase().split(/\s+/).filter(t => t.length >= 2);

export const haystack = (p: IndexPost) =>
  `${p.title.toLowerCase()} ${p.title_en.toLowerCase()} ${p.summary} ${p.summary_en} ${p.text} ${p.text_en}`;

export const matches = (p: IndexPost, terms: string[]) => terms.every(t => haystack(p).includes(t));

// A short excerpt around the first hit in the body text, to show where the word stands
export function snippet(p: IndexPost, term: string): string | null {
  for (const text of [p.text, p.text_en]) {
    const i = text.indexOf(term);
    if (i >= 0) {
      const from = Math.max(0, i - 60);
      const to = Math.min(text.length, i + term.length + 90);
      return `${from > 0 ? "…" : ""}${text.slice(from, to).trim()}${to < text.length ? "…" : ""}`;
    }
  }
  return null;
}
