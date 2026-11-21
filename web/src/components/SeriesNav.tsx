import Link from "next/link";
import type { BlogPost } from "@/components/BlogBody";
import { ARTICLES_PATH, EN_ARTICLES_PATH, readerPath } from "@/lib/blogSeo";
import type { Series } from "@/lib/series";

// The series an article belongs to (lib/series.ts): a small marker above the article ("Del 2 av 3 i serien …") that
// leads to the box under it, with all the published parts in reading order, the one being read marked, and the next.
type Part = Pick<BlogPost, "slug" | "title" | "title_en">;
type Info = Pick<Series, "key" | "sv" | "en" | "about" | "aboutEn">;
export const seriesInfo = ({ key, sv, en, about, aboutEn }: Series): Info => ({ key, sv, en, about, aboutEn });

const listPath = (key: string, en: boolean) => `${en ? EN_ARTICLES_PATH : ARTICLES_PATH}?serie=${key}`;

export function SeriesMarker({ series, parts, current, lang }: { series: Info; parts: Part[]; current: string; lang: "sv" | "en" }) {
  const en = lang === "en", n = parts.findIndex(p => p.slug === current) + 1;
  if (!n) return null;
  return (
    <a href="#serien" className="inline-flex items-center gap-2 rounded-full bg-[#b7410e]/10 px-3 py-1 text-[13px] font-semibold text-[#9a350b] hover:bg-[#b7410e]/20">
      <span aria-hidden="true">❖</span>
      {en ? `Part ${n} of ${parts.length} in the series ${series.en}` : `Del ${n} av ${parts.length} i serien ${series.sv}`}
    </a>
  );
}

export default function SeriesNav({ series, parts, current, lang }: { series: Info; parts: Part[]; current: string; lang: "sv" | "en" }) {
  const en = lang === "en", i = parts.findIndex(p => p.slug === current);
  if (i < 0) return null;
  const next = parts[i + 1];
  const title = (p: Part) => (en ? p.title_en || p.title : p.title);
  return (
    <section id="serien" className="max-w-3xl mx-auto px-6 pb-12 scroll-mt-24" aria-labelledby="serien-rubrik">
      <div className="rounded-2xl border border-[#b7410e]/25 bg-[#f3ede4]/70 p-6">
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#9a350b]">{en ? "Article series" : "Artikelserie"}</p>
        <h2 id="serien-rubrik" className="mt-1 font-serif text-2xl font-bold text-slate-900">
          <Link href={listPath(series.key, en)} prefetch={false} className="hover:text-[#b7410e]">{en ? series.en : series.sv}</Link>
        </h2>
        <p className="mt-1 text-slate-600">{en ? series.aboutEn : series.about}</p>
        <ol className="mt-4 space-y-2">
          {parts.map((p, k) => (
            <li key={p.slug} className="flex gap-3 leading-snug">
              <span className="w-14 shrink-0 text-sm font-semibold text-slate-500">{en ? `Part ${k + 1}` : `Del ${k + 1}`}</span>
              {k === i ? (
                <span className="font-semibold text-slate-900" aria-current="page" translate="no">
                  {title(p)} <span className="font-normal text-slate-500">{en ? "– you are reading it" : "– den du läser"}</span>
                </span>
              ) : (
                <Link href={readerPath(p, lang)} prefetch={false} className="font-semibold text-[#b7410e] hover:underline" translate="no">{title(p)}</Link>
              )}
            </li>
          ))}
        </ol>
        {next ? (
          <Link href={readerPath(next, lang)} prefetch={false}
            className="mt-6 inline-block rounded-full bg-[#b7410e] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#9a350b]">
            {en ? "Next part" : "Nästa del"}: <span translate="no">{title(next)}</span> →
          </Link>
        ) : (
          <p className="mt-4 text-sm text-slate-500">{en ? "More parts are on the way." : "Fler delar är på väg."}</p>
        )}
      </div>
    </section>
  );
}
