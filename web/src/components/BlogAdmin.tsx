"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import BlogBody, { monthLabel, type BlogPost } from "@/components/BlogBody";
import { useSettings } from "@/components/SettingsContext";
import { metaDescription, postUrl, seoChecks } from "@/lib/blogSeo";

const field = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none w-full";
const thisMonth = () => new Date().toISOString().slice(0, 7);
const slugify = (s: string) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80);

type Draft = Omit<BlogPost, "id" | "published"> & { id?: string };
// A topic for the post: a pattern the R analyses found that holds (GET /api/admin/blog/topics, src/blog_topics.py)
interface Topic { key: string; topic: string; status: string; replicated: boolean; title: string; text: string; hypothesis: string;
                  significance?: string | null; chart: boolean; used: boolean }

// A photo of a stone from Wikimedia Commons (POST /api/admin/blog/images, src/commons.py)
interface StoneImage { signum: string; thumb: string; page: string; author: string; licence: string; markdown: string; markdown_en: string }

/** The picture block after the first paragraph that names the stone, or last when no paragraph does. */
function insertPicture(text: string, signum: string, block: string) {
  const blocks = (text || "").split(/\n\s*\n/);
  const re = new RegExp(`(^|[^\\w])${signum.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?![\\w])`);
  // Not within a :::box or :::chart, which may hold blank lines
  let inside = false, i = -1;
  for (let j = 0; j < blocks.length && i < 0; j++) {
    const b = blocks[j], opens = b.startsWith(":::") && b.trim() !== ":::", closes = /\n:::\s*$/.test(b) || b.trim() === ":::";
    if (!inside && !opens && !b.startsWith("![") && re.test(b)) i = j;
    inside = (inside || opens) && !closes;
  }
  if (i < 0) return [...blocks.filter(b => b.trim()), block].join("\n\n");
  return [...blocks.slice(0, i + 1), block, ...blocks.slice(i + 1)].join("\n\n");
}
const empty = (author: string): Draft => ({ slug: "", title: "", summary: "", body: "", title_en: "", summary_en: "", body_en: "",
                                           month: thisMonth(), author, topic: "" });

// The monthly blog post (api/routers/blog.py): written and published here, by hand. "Utkast från månadens fynd" fills
// the form with the patterns and findings that are new or changed since the last published post, to edit from.
export default function BlogAdmin({ call }: { call: (path: string, init?: RequestInit) => Promise<any> }) { // eslint-disable-line @typescript-eslint/no-explicit-any
  const { userName } = useSettings();
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [draft, setDraft] = useState<Draft>(() => empty(userName));
  const [slugTouched, setSlugTouched] = useState(false);
  const [showEn, setShowEn] = useState(false);
  const [preview, setPreview] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [images, setImages] = useState<{ images: StoneImage[]; missing: string[] } | null>(null);
  const [topics, setTopics] = useState<Topic[] | null>(null);

  const load = useCallback(() => {
    call("/api/admin/blog/posts").then(d => setPosts(d.posts)).catch(e => setError(e.message));
  }, [call]);
  useEffect(() => { load(); }, [load]);

  const set = (k: keyof Draft, v: string) => setDraft(d => {
    const next = { ...d, [k]: v };
    if (k === "title" && !slugTouched) next.slug = slugify(v);
    return next;
  });

  const showTopics = async () => {
    if (topics) { setTopics(null); return; }
    setBusy("topics"); setError(null);
    try {
      setTopics((await call("/api/admin/blog/topics")).topics);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ämnena kunde inte hämtas.");
    } finally {
      setBusy(null);
    }
  };

  const fromFindings = async (topic?: string) => {
    if ((draft.title || draft.body) && !window.confirm("Ersätta texten i formuläret med ett nytt utkast?")) return;
    setBusy(topic ? `topic:${topic}` : "draft"); setError(null); setNote(null);
    try {
      const d = await call(`/api/admin/blog/draft?month=${encodeURIComponent(draft.month || thisMonth())}`
        + (topic ? `&topic=${encodeURIComponent(topic)}` : ""));
      setDraft(x => ({ ...x, ...d.draft, id: x.id, author: x.author || userName }));
      setSlugTouched(false);
      if (topic) setTopics(null);
      setSources(d.sources ?? []);
      setNote(d.note ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Utkastet kunde inte skapas.");
    } finally {
      setBusy(null);
    }
  };

  // Photos of the stones the text names, collected from Wikidata and Wikimedia Commons with photographer and licence
  const findImages = async () => {
    setBusy("images"); setError(null);
    try {
      setImages(await call("/api/admin/blog/images", { method: "POST", body: JSON.stringify({ text: `${draft.body ?? ""}\n${draft.body_en ?? ""}` }) }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Bilderna kunde inte hämtas.");
    } finally {
      setBusy(null);
    }
  };
  const addImage = (img: StoneImage) => setDraft(d => ({
    ...d, body: insertPicture(d.body ?? "", img.signum, img.markdown),
    body_en: (d.body_en ?? "").trim() ? insertPicture(d.body_en ?? "", img.signum, img.markdown_en) : d.body_en,
  }));

  const save = async (published: boolean) => {
    setBusy(published ? "publish" : "save"); setError(null); setNote(null);
    try {
      const d = await call("/api/admin/blog/posts", { method: "POST", body: JSON.stringify({ ...draft, published }) });
      setDraft(x => ({ ...x, id: d.post.id }));
      setNote(published ? `Publicerat: /blogg/${d.post.slug}` : "Sparat som utkast.");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Inlägget kunde inte sparas.");
    } finally {
      setBusy(null);
    }
  };

  const edit = (p: BlogPost) => {
    setDraft({ id: p.id, slug: p.slug, title: p.title, summary: p.summary, body: p.body ?? "", title_en: p.title_en ?? "",
               summary_en: p.summary_en ?? "", body_en: p.body_en ?? "", month: p.month, author: p.author ?? "", topic: p.topic ?? "" });
    setSlugTouched(true); setShowEn(!!(p.title_en || p.body_en)); setSources([]); setNote(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const remove = async (p: BlogPost) => {
    if (!window.confirm(`Ta bort "${p.title}"? Det går inte att ångra.`)) return;
    try { await call(`/api/admin/blog/posts/${encodeURIComponent(p.id)}`, { method: "DELETE" }); load(); if (draft.id === p.id) setDraft(empty(userName)); }
    catch (e) { setError(e instanceof Error ? e.message : "Det gick inte."); }
  };

  const unpublish = async (p: BlogPost) => {
    try { await call("/api/admin/blog/posts", { method: "POST", body: JSON.stringify({ ...p, published: false }) }); load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Det gick inte."); }
  };

  const ready = draft.title.trim() && draft.slug.trim() && (draft.body ?? "").trim();
  return (
    <section className="liquid-glass-island rounded-[24px] p-4 sm:p-6 space-y-4">
      <div className="flex flex-wrap items-center gap-3 justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Månadens fynd (blogg)</h3>
          <p className="text-sm text-slate-600 max-w-3xl">
            Ett inlägg i månaden om de mest intressanta mönstren och fynden, på <Link href="/blogg" className="text-[#b7410e] underline">/blogg</Link>.
            Utkastet bygger på det som är nytt eller har ändrat status sedan förra publicerade inlägget; skriv om det med egna ord innan du publicerar.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={showTopics} disabled={busy === "topics"} className="px-4 py-2 rounded-xl bg-[#b7410e] text-white text-sm font-bold disabled:opacity-40">
            {busy === "topics" ? "Hämtar …" : topics ? "Dölj ämnena" : "Välj ämne ur R-analyserna"}
          </button>
          <button onClick={() => fromFindings()} disabled={busy === "draft"} className="px-4 py-2 rounded-xl border border-[#b7410e] text-[#b7410e] bg-white text-sm font-bold disabled:opacity-40">
            {busy === "draft" ? "Skapar …" : "Utkast från månadens fynd"}
          </button>
          <button onClick={() => { setDraft(empty(userName)); setSlugTouched(false); setSources([]); setNote(null); }}
            className="px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold">Nytt inlägg</button>
        </div>
      </div>
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}
      {topics && (
        <div className="rounded-xl border border-slate-200 bg-white/70 p-4 space-y-3">
          <p className="text-sm text-slate-600 max-w-3xl">
            Utmärkande eller dolda mönster som R-analyserna har hittat och som håller – nya mönster att pröva först. Välj ett
            ämne så skrivs ett utkast efter bloggens mall, med appens siffror, diagram och foton; skriv sedan om det med egna
            ord och en skarp hypotes.
          </p>
          {topics.length === 0 && <p className="text-sm text-slate-500">Inga mönster håller just nu.</p>}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {topics.map(t => (
              <div key={t.key} className={`rounded-xl border p-3 text-sm ${t.used ? "border-slate-200 bg-slate-50" : "border-[#b7410e]/25 bg-white"}`}>
                <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-bold">
                  <span className="rounded-md border border-slate-300 px-1.5 text-slate-600">{t.topic}</span>
                  <span className={`rounded-md px-1.5 ${t.status === "mönster att pröva" ? "bg-[#fbf3ee] text-[#9a350b]" : "bg-emerald-50 text-emerald-800"}`}>{t.status}</span>
                  {t.replicated && <span className="rounded-md bg-slate-100 px-1.5 text-slate-700">båda halvorna</span>}
                  {t.chart && <span className="rounded-md bg-slate-100 px-1.5 text-slate-700">diagram</span>}
                  {t.used && <span className="rounded-md bg-slate-200 px-1.5 text-slate-700">redan skrivet</span>}
                </div>
                <p className="mt-1.5 font-semibold text-slate-900">{t.title}</p>
                <p className="mt-1 text-xs text-slate-600"><span className="font-semibold">Hypotes:</span> {t.hypothesis}</p>
                {t.significance && <p className="mt-0.5 text-[11px] text-slate-500">{t.significance}</p>}
                <button onClick={() => fromFindings(t.key)} disabled={!!busy}
                  className="mt-2 text-xs font-bold text-[#b7410e] hover:underline disabled:opacity-40">
                  {busy === `topic:${t.key}` ? "Skriver …" : "Skriv utkast om det här →"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      {note && <p className="text-sm font-semibold text-emerald-700">{note}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <label className="text-xs font-bold text-slate-600 sm:col-span-1">Månad
          <input type="month" value={draft.month} onChange={e => set("month", e.target.value)} className={`${field} mt-1`} />
        </label>
        <label className="text-xs font-bold text-slate-600 sm:col-span-3">Författare
          <input value={draft.author ?? ""} onChange={e => set("author", e.target.value)} placeholder="Namn (från Inställningar)" className={`${field} mt-1`} />
        </label>
        <input value={draft.title} onChange={e => set("title", e.target.value)} placeholder="Rubrik" maxLength={160} className={`${field} sm:col-span-4 font-semibold`} />
        <label className="text-xs font-bold text-slate-600 sm:col-span-4">Adress
          <div className="flex items-center gap-1 mt-1">
            <span className="text-sm text-slate-500">/blogg/</span>
            <input value={draft.slug} onChange={e => { setSlugTouched(true); set("slug", slugify(e.target.value)); }} className={field} />
          </div>
        </label>
        <textarea value={draft.summary} onChange={e => set("summary", e.target.value)} placeholder="Ingress (en eller två meningar)" rows={2} maxLength={600} className={`${field} sm:col-span-4`} />
        {preview ? (
          <div className="sm:col-span-4 rounded-xl border border-slate-200 bg-white p-5"><BlogBody text={draft.body ?? ""} /></div>
        ) : (
          <textarea value={draft.body} onChange={e => set("body", e.target.value)} rows={18} maxLength={40000}
            placeholder={"Text. ## Rubrik, - punktlista, **fet**, *kursiv*, [länk](/karta). Tom rad mellan stycken. Se Formatering nedan."}
            className={`${field} sm:col-span-4 font-mono text-[13px]`} />
        )}
      </div>

      <details open={showEn} onToggle={e => setShowEn((e.target as HTMLDetailsElement).open)} className="rounded-xl border border-slate-200 bg-white/60 p-3">
        <summary className="cursor-pointer text-sm font-bold text-slate-700">Engelsk version (valfri)</summary>
        <div className="grid gap-3 mt-3">
          <input value={draft.title_en ?? ""} onChange={e => set("title_en", e.target.value)} placeholder="Title" className={field} />
          <textarea value={draft.summary_en ?? ""} onChange={e => set("summary_en", e.target.value)} placeholder="Summary" rows={2} className={field} />
          <textarea value={draft.body_en ?? ""} onChange={e => set("body_en", e.target.value)} placeholder="Text" rows={10} className={`${field} font-mono text-[13px]`} />
        </div>
      </details>

      {(() => {
        // What search engines will show and how the post measures up (lib/blogSeo.ts); the page gets its metadata,
        // structured data and share image by itself when it is published
        const checks = seoChecks({ ...draft, body: draft.body ?? "" });
        const passed = checks.filter(c => c.ok).length;
        const title = `${draft.title || "Rubrik"} | Vitki`;
        return (
          <details className="rounded-xl border border-slate-200 bg-white/60 p-3">
            <summary className="cursor-pointer text-sm font-bold text-slate-700">SEO-kontroll ({passed} av {checks.length} uppfyllda)</summary>
            <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3 max-w-2xl">
              <p className="text-[11px] text-slate-500 truncate" translate="no">{postUrl(draft.slug || "adress")}</p>
              <p className="text-[17px] text-[#1a0dab] leading-snug truncate" translate="no">{title.length > 62 ? `${title.slice(0, 60)}…` : title}</p>
              <p className="text-xs text-slate-600 leading-snug" translate="no">{metaDescription(draft.summary || draft.body || "") || "Ingressen blir beskrivningen."}</p>
            </div>
            <ul className="mt-3 space-y-1 text-xs">
              {checks.map(c => (
                <li key={c.text} className="flex gap-2">
                  <span className={c.ok ? "text-emerald-700" : "text-amber-700"} aria-hidden="true">{c.ok ? "✓" : "!"}</span>
                  <span className={c.ok ? "text-slate-600" : "text-slate-800"}>{c.text}</span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[11px] text-slate-500">
              När inlägget publiceras får sidan av sig själv titel, beskrivning, kanonisk adress, Open Graph och Twitter-kort,
              strukturerade data (BlogPosting), en egen delningsbild med första fotot, plats i sitemap och RSS-flödet.
            </p>
          </details>
        );
      })()}

      <details className="text-xs text-slate-600">
        <summary className="cursor-pointer font-semibold">Formatering</summary>
        <div className="mt-2 grid gap-1 font-mono text-[12px] text-slate-700">
          <span>## Rubrik · ### Underrubrik · - punkt · 1. numrerad · &gt; citat · **fet** · *kursiv* · [länk](/karta)</span>
          <span>![Runstenen U 431](https://upload.wikimedia.org/…) – bild; bildtexten på nästa rad</span>
          <span>:::box Kort sagt … ::: – faktaruta (stycken och listor inuti)</span>
          <span>:::chart Rubrik / + Etikett | 36 | 87 stenar / Etikett | 8 / # Grupp / Källa: … / ::: – stapeldiagram i procent</span>
        </div>
      </details>

      <div className="rounded-xl border border-slate-200 bg-white/60 p-3 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-bold text-slate-700">Bilder</p>
          <button onClick={findImages} disabled={busy === "images" || !(draft.body ?? "").trim()}
            className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs font-bold disabled:opacity-40">
            {busy === "images" ? "Hämtar …" : "Hämta bilder till stenarna i texten"}
          </button>
        </div>
        <p className="text-xs text-slate-500">
          Foton av de stenar texten nämner, ur Wikidata och Wikimedia Commons. Bara fritt licensierade bilder; fotograf och
          licens följer med i bildtexten. Infoga lägger bilden efter stycket som nämner stenen, på båda språken.
        </p>
        {images && (
          images.images.length ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {images.images.map(img => (
                <figure key={img.signum} className="rounded-lg border border-slate-200 bg-white p-2 text-xs">
                  {/* eslint-disable-next-line @next/next/no-img-element -- Commons thumbnail */}
                  <img src={img.thumb} alt={img.signum} loading="lazy" className="h-28 w-full object-cover rounded" />
                  <figcaption className="mt-1">
                    <span className="font-semibold text-slate-900" translate="no">{img.signum}</span>
                    <span className="block text-slate-500 truncate" title={`${img.author}, ${img.licence}`}>{img.author}, {img.licence}</span>
                  </figcaption>
                  <button onClick={() => addImage(img)} className="mt-1 text-[#b7410e] font-semibold hover:underline">Infoga</button>
                </figure>
              ))}
            </div>
          ) : <p className="text-xs text-slate-500">Inga fritt licensierade bilder hittades.</p>
        )}
        {images && images.missing.length > 0 && (
          <p className="text-xs text-slate-500">Utan bild: <span translate="no">{images.missing.join(", ")}</span></p>
        )}
      </div>

      {sources.length > 0 && (
        <details className="text-xs text-slate-600">
          <summary className="cursor-pointer font-semibold">Underlag för utkastet ({sources.length})</summary>
          <ul className="mt-1 list-disc pl-5 space-y-0.5">{sources.map(s => <li key={s}>{s}</li>)}</ul>
        </details>
      )}

      <div className="flex flex-wrap gap-2">
        <button onClick={() => setPreview(p => !p)} className="px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold">{preview ? "Redigera" : "Förhandsgranska"}</button>
        <button onClick={() => save(false)} disabled={!ready || !!busy} className="px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold disabled:opacity-40">
          {busy === "save" ? "Sparar …" : "Spara utkast"}
        </button>
        <button onClick={() => save(true)} disabled={!ready || !!busy} className="px-4 py-2 rounded-xl bg-[#b7410e] text-white text-sm font-bold disabled:opacity-40">
          {busy === "publish" ? "Publicerar …" : "Publicera"}
        </button>
      </div>

      {posts.length > 0 && (
        <ul className="divide-y divide-slate-900/5 pt-2">
          {posts.map(p => (
            <li key={p.id} className="py-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <span className="text-[11px] text-slate-500 w-28 shrink-0">{monthLabel(p.month)}</span>
              <span className={`text-[10px] font-bold rounded-md px-1.5 border ${p.published ? "border-emerald-300 bg-emerald-50 text-emerald-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
                {p.published ? "publicerad" : "utkast"}
              </span>
              <span className="min-w-0 flex-1 font-semibold text-slate-900 truncate" translate="no">{p.title}</span>
              <button onClick={() => edit(p)} className="text-xs font-semibold text-[#b7410e] hover:underline">Redigera</button>
              {p.published && <button onClick={() => unpublish(p)} className="text-xs font-semibold text-slate-500 hover:text-slate-900">Avpublicera</button>}
              <button onClick={() => remove(p)} className="text-xs font-semibold text-slate-500 hover:text-red-700">Ta bort</button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
