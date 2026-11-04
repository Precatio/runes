"use client";

// The article library (/artiklar/ and /en/artiklar/): built to stay easy to survey with many articles. A side panel
// filters on kind and subject together (and on series), sorts, and switches between cards and a compact list; the
// articles are grouped by month, with the reading time on each. On a phone the panel folds into "Filtrera och sortera".
// Search finds any word in title, summary or text (lib/articleSearch.ts). Everything the reader chooses stands in the
// address (?q, ?typ, ?amne, ?serie, ?sortera, ?vy; the older ?etikett= from the label chips is read as kind or subject),
// so a link opens the same view. Every article is in the page from the start, also the ones behind "Visa fler", so that
// search engines find them all.
import Link from "next/link";
import { useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from "react";
import { postDate, type BlogPost } from "@/components/BlogBody";
import { Picture } from "@/components/BlogList";
import { hasViews, inOrder, type Order } from "@/lib/featured";
import { SUBJECTS, TYPES, isType, labelName, typeOf } from "@/lib/labels";
import { MIN_PARTS, SERIES, seriesOf } from "@/lib/series";
import { readerPath } from "@/lib/blogSeo";
import { loadIndex, matches, searchTerms, snippet, type IndexPost } from "@/lib/articleSearch";
import { trackSearch } from "@/lib/track";
import { useLanguage } from "@/components/LanguageContext";

type View = "kort" | "lista";
const PAGE = 12;

// ---- the address ------------------------------------------------------------------------------------------------
const EVENT = "vitki-bibliotek";
const subscribe = (cb: () => void) => {
  window.addEventListener("popstate", cb);
  window.addEventListener(EVENT, cb);
  return () => { window.removeEventListener("popstate", cb); window.removeEventListener(EVENT, cb); };
};
const readSearch = () => window.location.search;
function useAddress(): [URLSearchParams, (changes: Record<string, string | null>) => void] {
  const search = useSyncExternalStore(subscribe, readSearch, () => "");
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const set = (changes: Record<string, string | null>) => {
    const url = new URL(window.location.href);
    for (const [k, v] of Object.entries(changes)) {
      if (v) url.searchParams.set(k, v); else url.searchParams.delete(k);
    }
    url.searchParams.delete("etikett");  // replaced by typ/amne once the reader chooses
    window.history.replaceState(null, "", url.toString());
    window.dispatchEvent(new Event(EVENT));
  };
  return [params, set];
}

// ---- small pieces -----------------------------------------------------------------------------------------------
const minutes = (p: BlogPost, en: boolean) => {
  const w = en ? p.words_en || p.words : p.words;
  return w ? Math.max(1, Math.round(w / 200)) : null;
};
// In the list the month is the group's heading, so a row shows the day and the short month ("4 nov.")
const shortDate = (p: BlogPost, en: boolean) => p.publishedAt
  ? new Intl.DateTimeFormat(en ? "en-GB" : "sv-SE", { day: "numeric", month: "short" }).format(new Date(p.publishedAt))
  : postDate(p, en ? "en" : "sv");
const monthKey = (p: BlogPost) => (p.publishedAt ?? p.month ?? "").slice(0, 7);
function monthHeading(key: string, en: boolean) {
  if (!/^\d{4}-\d{2}$/.test(key)) return en ? "Undated" : "Odaterade";
  const s = new Intl.DateTimeFormat(en ? "en-GB" : "sv-SE", { month: "long", year: "numeric" }).format(new Date(`${key}-15T12:00:00Z`));
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function Option({ on, onClick, children, count }: { on: boolean; onClick: () => void; children: ReactNode; count?: number }) {
  return (
    <button type="button" onClick={onClick} aria-pressed={on}
      className={`flex w-full items-center justify-between gap-3 rounded-lg px-2.5 py-1.5 text-left text-[14px] transition ${
        on ? "bg-[#b7410e] text-white font-semibold" : "text-slate-700 hover:bg-white hover:text-slate-900"}`}>
      <span>{children}</span>
      {count != null && <span className={`text-[12px] tabular-nums ${on ? "text-white/80" : "text-slate-400"}`}>{count}</span>}
    </button>
  );
}

function Segmented<T extends string>({ value, options, onChange, label }:
  { value: T; options: [T, string][]; onChange: (v: T) => void; label: string }) {
  return (
    <div role="group" aria-label={label} className="inline-flex rounded-full border border-slate-300 bg-white p-0.5">
      {options.map(([v, text]) => (
        <button key={v} type="button" aria-pressed={value === v} onClick={() => onChange(v)}
          className={`rounded-full px-3 py-1 text-[13px] font-semibold transition ${value === v ? "bg-[#b7410e] text-white" : "text-slate-600 hover:text-slate-900"}`}>
          {text}
        </button>
      ))}
    </div>
  );
}

const Heading = ({ children }: { children: ReactNode }) => (
  <div className="mb-1.5 px-2.5 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-500">{children}</div>
);

// ---- the cards and the rows -----------------------------------------------------------------------------------------
function Card({ p, en, big, eager }: { p: BlogPost; en: boolean; big?: boolean; eager?: boolean }) {
  const title = en ? p.title_en || p.title : p.title, summary = en ? p.summary_en || p.summary : p.summary;
  const kind = typeOf(p.labels), min = minutes(p, en), series = seriesOf(p);
  return (
    <article className={big ? "md:col-span-2" : ""}>
      <Link href={readerPath(p, en ? "en" : "sv")} prefetch={false}
        className={`group flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white/80 transition hover:-translate-y-0.5 hover:border-[#b7410e]/50 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#b7410e] ${big ? "md:flex-row" : ""}`}>
        <Picture post={p} big={!!big} eager={eager} className={big ? "aspect-[16/9] w-full md:aspect-auto md:w-1/2 md:min-h-[18rem] shrink-0" : "aspect-[16/9] w-full shrink-0"} />
        <div className={`flex flex-1 flex-col ${big ? "p-6 md:p-8" : "p-5"}`}>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#b7410e]">
            {p.featured && <span>{en ? "Article of the week" : "Veckans artikel"}</span>}
            {p.featured && kind && <span className="text-slate-300">·</span>}
            {kind && <span>{labelName(kind, en ? "en" : "sv")}</span>}
            {series && <><span className="text-slate-300">·</span><span className="text-slate-500">{en ? series.en : series.sv}</span></>}
          </div>
          <h3 className={`mt-1.5 font-serif font-bold leading-snug text-slate-900 group-hover:text-[#b7410e] ${big ? "text-3xl" : "text-xl"}`} translate="no">{title}</h3>
          <p className={`mt-2 text-slate-600 leading-relaxed ${big ? "line-clamp-4 text-[16px]" : "line-clamp-3 text-[15px]"}`} translate="no">{summary}</p>
          <div className="mt-auto pt-4 text-[13px] text-slate-500">
            <time dateTime={p.publishedAt ?? p.month}>{postDate(p, en ? "en" : "sv")}</time>
            {min && <> · {en ? `${min} min read` : `${min} min läsning`}</>}
          </div>
        </div>
      </Link>
    </article>
  );
}

function Row({ p, en }: { p: BlogPost; en: boolean }) {
  const title = en ? p.title_en || p.title : p.title;
  const kind = typeOf(p.labels), min = minutes(p, en);
  const subjects = (p.labels ?? []).filter(l => !isType(l));
  return (
    <li className="grid grid-cols-[4.5rem_1fr] gap-x-4 border-t border-slate-200 py-3 sm:grid-cols-[5rem_1fr_auto]">
      <time dateTime={p.publishedAt ?? p.month} className="pt-0.5 text-[13px] tabular-nums text-slate-500">{shortDate(p, en)}</time>
      <div className="min-w-0">
        <Link href={readerPath(p, en ? "en" : "sv")} prefetch={false} className="font-serif text-[17px] font-bold leading-snug text-slate-900 hover:text-[#b7410e]" translate="no">{title}</Link>
        <div className="mt-0.5 text-[12.5px] text-slate-500">
          {kind && <span className="font-semibold text-[#b7410e]">{labelName(kind, en ? "en" : "sv")}</span>}
          {subjects.length > 0 && <>{kind && " · "}{subjects.map(s => labelName(s, en ? "en" : "sv")).join(", ")}</>}
          {min && <span className="sm:hidden"> · {en ? `${min} min` : `${min} min`}</span>}
        </div>
      </div>
      <span className="hidden pt-0.5 text-right text-[13px] tabular-nums text-slate-500 sm:block">{min ? `${min} min` : ""}</span>
    </li>
  );
}

// ---- the library ------------------------------------------------------------------------------------------------------
export default function ArticleLibrary({ posts, lang: pageLang = "sv", failed = false }: { posts: BlogPost[]; lang?: "sv" | "en"; failed?: boolean }) {
  // The English page is English; the Swedish page follows the reader's language choice (the labels, months and reading
  // times are then rendered in English directly, the titles and summaries from the article's English edition)
  const chosen = useLanguage().lang;
  const lang: "sv" | "en" = pageLang === "en" || chosen === "en" ? "en" : "sv";
  const en = lang === "en";
  const [params, set] = useAddress();
  const legacy = params.get("etikett");
  const kind = params.get("typ") ?? (legacy && isType(legacy) ? legacy : null);
  const subject = params.get("amne") ?? (legacy && !isType(legacy) ? legacy : null);
  const series = params.get("serie");
  const order: Order = params.get("sortera") === "mest-lasta" ? "mest-lasta" : "senaste";
  const view: View = params.get("vy") === "lista" ? "lista" : "kort";
  const q = params.get("q") ?? "";
  const [typed, setTyped] = useState<string | null>(null);
  const query = typed ?? q;
  const [index, setIndex] = useState<IndexPost[] | null>(null);
  const [all, setAll] = useState(false);
  const [panel, setPanel] = useState(false);

  useEffect(() => { if (q) loadIndex().then(setIndex); }, [q]);
  // The query goes into the address once the typing has settled, and is counted (lib/track.ts: anonymous)
  useEffect(() => {
    if (typed == null) return;
    const t = setTimeout(() => set({ q: typed.trim() || null }), 400);
    return () => clearTimeout(t);
  }, [typed]); // eslint-disable-line react-hooks/exhaustive-deps

  const terms = useMemo(() => searchTerms(query), [query]);
  const by = useMemo(() => new Map((index ?? []).map(p => [p.slug, p])), [index]);
  const hits = useMemo(() => {
    if (!terms.length) return null;
    return posts.filter(p => {
      const ix = by.get(p.slug);
      if (ix) return matches(ix, terms);
      const hay = `${p.title} ${p.title_en ?? ""} ${p.summary ?? ""} ${p.summary_en ?? ""}`.toLowerCase();
      return terms.every(t => hay.includes(t));
    });
  }, [terms, posts, by]);
  useEffect(() => {
    if (!hits || !index) return;
    const t = setTimeout(() => trackSearch(query, hits.length), 1500);
    return () => clearTimeout(t);
  }, [query, hits, index]);

  const seriesShown = SERIES.filter(s => posts.filter(p => s.match.test(p.title)).length >= MIN_PARTS);
  const base = hits ?? posts;
  const filtered = base.filter(p => (!kind || p.labels?.includes(kind)) && (!subject || p.labels?.includes(subject))
    && (!series || seriesOf(p)?.key === series));
  const shown = inOrder(filtered, order);
  // Counts for the panel: what each choice would give together with the other choices
  const countWith = (k: string | null, s: string | null) => base.filter(p => (!k || p.labels?.includes(k)) && (!s || p.labels?.includes(s))
    && (!series || seriesOf(p)?.key === series)).length;
  const types = TYPES.filter(([sv]) => posts.some(p => p.labels?.includes(sv)));
  const subjects = SUBJECTS.filter(([sv]) => posts.some(p => p.labels?.includes(sv)));
  const active = [kind, subject, series].filter(Boolean).length + (terms.length ? 1 : 0);
  const plain = !active && order === "senaste";
  const featured = plain ? shown.find(p => p.featured) : undefined;
  const rest = featured ? shown.filter(p => p !== featured) : shown;
  const cardLimit = all ? Infinity : PAGE;

  // Grouped by month in date order; "most read" is one list without months
  const groups: [string, BlogPost[]][] = [];
  if (order === "senaste") {
    for (const p of rest) {
      const k = monthKey(p);
      const g = groups[groups.length - 1];
      if (g && g[0] === k) g[1].push(p); else groups.push([k, [p]]);
    }
  } else groups.push(["", rest]);

  const clear = () => { setTyped(""); set({ q: null, typ: null, amne: null, serie: null }); };
  const filters = (
    <div className="space-y-6">
      <div>
        <Heading>{en ? "Kind" : "Typ"}</Heading>
        <Option on={!kind} onClick={() => set({ typ: null })} count={countWith(null, subject)}>{en ? "All kinds" : "Alla typer"}</Option>
        {types.map(([sv]) => (
          <Option key={sv} on={kind === sv} onClick={() => set({ typ: kind === sv ? null : sv })} count={countWith(sv, subject)}>
            {labelName(sv, lang)}
          </Option>
        ))}
      </div>
      <div>
        <Heading>{en ? "Subject" : "Ämne"}</Heading>
        <Option on={!subject} onClick={() => set({ amne: null })} count={countWith(kind, null)}>{en ? "All subjects" : "Alla ämnen"}</Option>
        {subjects.map(([sv]) => (
          <Option key={sv} on={subject === sv} onClick={() => set({ amne: subject === sv ? null : sv })} count={countWith(kind, sv)}>
            {labelName(sv, lang)}
          </Option>
        ))}
      </div>
      {seriesShown.length > 0 && (
        <div>
          <Heading>{en ? "Series" : "Serier"}</Heading>
          {seriesShown.map(s => (
            <Option key={s.key} on={series === s.key} onClick={() => set({ serie: series === s.key ? null : s.key })}
              count={posts.filter(p => s.match.test(p.title)).length}>
              {en ? s.en : s.sv}
            </Option>
          ))}
        </div>
      )}
      {active > 0 && (
        <button type="button" onClick={clear} className="px-2.5 text-sm font-semibold text-[#b7410e] hover:underline">
          {en ? "Clear the filters" : "Rensa filtren"}
        </button>
      )}
    </div>
  );

  if (!posts.length) {
    return <p className="mt-10 text-slate-500">{failed ? (en ? "The articles could not be fetched right now." : "Artiklarna kunde inte hämtas just nu.")
      : (en ? "No articles yet." : "Inga artiklar ännu. Den första kommer snart.")}</p>;
  }

  return (
    <div className="mt-10 lg:grid lg:grid-cols-[15rem_1fr] lg:gap-10">
      {/* The panel: beside the list on a wide screen, folded on a phone */}
      <aside className="hidden lg:block">
        <div className="sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto pb-6 pr-1">{filters}</div>
      </aside>

      <div className="min-w-0">
        <input value={query} onChange={e => setTyped(e.target.value)} onFocus={() => loadIndex().then(setIndex)}
          placeholder={en ? "Search the articles – a word, a signum, a name …" : "Sök i artiklarna – ett ord, ett signum, ett namn …"}
          aria-label={en ? "Search the articles" : "Sök i artiklarna"}
          className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-3.5 text-[16px] text-slate-900 placeholder:text-slate-400 shadow-sm outline-none focus:border-[#b7410e] focus:ring-2 focus:ring-[#b7410e]/20" />

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-600" aria-live="polite">
            {shown.length === posts.length ? (en ? `${posts.length} articles` : `${posts.length} artiklar`)
              : (en ? `${shown.length} of ${posts.length} articles` : `${shown.length} av ${posts.length} artiklar`)}
            {terms.length > 0 && !index && (en ? " · searching titles while the texts load …" : " · söker i titlarna medan texterna hämtas …")}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {hasViews(posts) && (
              <Segmented label={en ? "Sort the articles" : "Sortera artiklarna"} value={order} onChange={o => set({ sortera: o === "mest-lasta" ? o : null })}
                options={[["senaste", en ? "Newest" : "Senaste"], ["mest-lasta", en ? "Most read" : "Mest lästa"]]} />
            )}
            <Segmented label={en ? "Show as" : "Visa som"} value={view} onChange={v => set({ vy: v === "lista" ? v : null })}
              options={[["kort", en ? "Cards" : "Kort"], ["lista", en ? "List" : "Lista"]]} />
            <button type="button" onClick={() => setPanel(o => !o)} aria-expanded={panel}
              className="rounded-full border border-slate-300 bg-white px-3 py-1 text-[13px] font-semibold text-slate-700 lg:hidden">
              {en ? "Filter" : "Filtrera"}{active ? ` (${active})` : ""}
            </button>
          </div>
        </div>
        {panel && <div className="mt-4 rounded-2xl border border-slate-200 bg-white/80 p-4 lg:hidden">{filters}</div>}

        {/* The chosen filters, removable one by one */}
        {(kind || subject || series) && (
          <div className="mt-3 flex flex-wrap gap-2">
            {[[kind, "typ"], [subject, "amne"], [series, "serie"]].filter(([v]) => v).map(([v, k]) => (
              <button key={k} type="button" onClick={() => set({ [k as string]: null })}
                className="rounded-full bg-[#b7410e]/10 px-3 py-1 text-[13px] font-semibold text-[#9a350b] hover:bg-[#b7410e]/20">
                {k === "serie" ? (en ? SERIES.find(s => s.key === v)?.en : SERIES.find(s => s.key === v)?.sv) : labelName(v as string, lang)} ×
              </button>
            ))}
          </div>
        )}

        {terms.length > 0 && index && shown.length > 0 && (
          <ul className="mt-4 space-y-1.5">
            {shown.flatMap(p => {
              const ix = by.get(p.slug);
              const s = ix ? snippet(ix, terms[0]) : null;
              return s ? [<li key={p.slug} className="text-sm text-slate-500 leading-relaxed"><span className="font-semibold text-slate-700">{en ? p.title_en || p.title : p.title}:</span> ”{s}”</li>] : [];
            })}
          </ul>
        )}

        {shown.length === 0 && (
          <p className="mt-10 text-slate-500">{en ? "No article matches. " : "Ingen artikel matchar. "}
            <button type="button" onClick={clear} className="font-semibold text-[#b7410e] hover:underline">{en ? "Clear the filters" : "Rensa filtren"}</button>
          </p>
        )}

        {featured && (
          <div className="mt-8 grid gap-6 md:grid-cols-2"><Card p={featured} en={en} big eager /></div>
        )}

        {(() => {
          let n = 0;  // cards shown so far, for "Visa fler"
          return groups.map(([key, list]) => {
            const first = n;
            // A month whose cards are all behind "Visa fler" is hidden with them (still in the page, for search engines)
            const hidden = view === "kort" && first >= cardLimit;
            return (
            <section key={key || "alla"} className={`mt-10${hidden ? " hidden" : ""}`}>
              {key && (
                <h2 className="mb-4 flex items-baseline gap-3 font-serif text-xl font-bold text-slate-900">
                  {monthHeading(key, en)}
                  <span className="font-sans text-[13px] font-normal text-slate-400">{list.length}</span>
                </h2>
              )}
              {view === "lista" ? (
                <ul>{list.map(p => <Row key={p.slug} p={p} en={en} />)}</ul>
              ) : (
                <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                  {list.map(p => {
                    const hide = n++ >= cardLimit;
                    return <div key={p.slug} className={hide ? "hidden" : "contents"}><Card p={p} en={en} eager={!featured && n === 1} /></div>;
                  })}
                </div>
              )}
            </section>
            );
          });
        })()}

        {view === "kort" && !all && rest.length > PAGE && (
          <div className="mt-10 text-center">
            <button type="button" onClick={() => setAll(true)}
              className="rounded-full border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:border-[#b7410e] hover:text-[#b7410e]">
              {en ? `Show all ${rest.length + (featured ? 1 : 0)} articles` : `Visa alla ${rest.length + (featured ? 1 : 0)} artiklar`}
            </button>
            <p className="mt-2 text-xs text-slate-500">{en ? "or switch to List for an overview" : "eller välj Lista för en överblick"}</p>
          </div>
        )}
      </div>
    </div>
  );
}
