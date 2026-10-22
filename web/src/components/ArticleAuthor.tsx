import Link from "next/link";
import type { Author } from "@/lib/site";

// The author under an article's title and the card about the person behind Vitki at its end: the same on the Swedish
// article (components/BlogArticle.tsx) and on its English edition (app/en/artiklar/[slug]/page.tsx). The author page
// and LinkedIn are what the structured data's author (lib/blogSeo.ts articleJsonLd) points to as well.

export function AuthorByline({ name, author, lang }: { name: string; author: Author | null; lang: string }) {
  return (
    <div className="mt-7 flex items-center gap-3 border-y border-slate-900/10 py-4" translate="no">
      <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#b7410e] text-sm font-bold text-white">
        {name.split(/\s+/).map(w => w[0]).slice(0, 2).join("")}
      </span>
      <div className="leading-tight">
        <div className="text-xs uppercase tracking-wider text-slate-500">{lang === "en" ? "By" : "Av"}</div>
        {author
          ? <Link href={author.page} rel="author" className="text-base font-bold text-slate-900 hover:text-[#b7410e]">{name}</Link>
          : <span className="text-base font-bold text-slate-900">{name}</span>}
        {author && <div className="text-sm text-slate-500">{lang === "en" ? author.role_en : author.role}</div>}
      </div>
      {author && (
        <a href={author.linkedin} target="_blank" rel="noopener noreferrer" className="ml-auto text-sm font-bold text-[#b7410e] hover:underline">
          LinkedIn ↗
        </a>
      )}
    </div>
  );
}

export function AuthorCard({ author, lang }: { author: Author; lang: string }) {
  return (
    <aside className="mt-16 rounded-2xl border border-slate-900/10 bg-white p-6" translate="no">
      <div className="text-xs font-bold uppercase tracking-wider text-[#b7410e]">{lang === "en" ? "The person behind Vitki" : "Personen bakom Vitki"}</div>
      <Link href={author.page} rel="author" className="mt-2 inline-block text-lg font-bold text-slate-900 hover:text-[#b7410e]">{author.name}</Link>
      <p className="mt-2 text-slate-600 leading-relaxed">{lang === "en" ? author.bio_en : author.bio}</p>
      <div className="mt-3 flex flex-wrap gap-4 text-sm font-bold text-[#b7410e]">
        <Link href={author.page} className="hover:underline">{lang === "en" ? "The person behind Vitki, and contact →" : "Personen bakom Vitki, och kontakt →"}</Link>
        <a href={author.linkedin} target="_blank" rel="noopener noreferrer" className="hover:underline">LinkedIn ↗</a>
      </div>
    </aside>
  );
}
