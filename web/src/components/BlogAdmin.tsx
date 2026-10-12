"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import BlogBody, { monthLabel, type BlogPost } from "@/components/BlogBody";
import { useSettings } from "@/components/SettingsContext";

const field = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm outline-none w-full";
const thisMonth = () => new Date().toISOString().slice(0, 7);
const slugify = (s: string) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80);

type Draft = Omit<BlogPost, "id" | "published"> & { id?: string };
const empty = (author: string): Draft => ({ slug: "", title: "", summary: "", body: "", title_en: "", summary_en: "", body_en: "",
                                           month: thisMonth(), author });

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

  const load = useCallback(() => {
    call("/api/admin/blog/posts").then(d => setPosts(d.posts)).catch(e => setError(e.message));
  }, [call]);
  useEffect(() => { load(); }, [load]);

  const set = (k: keyof Draft, v: string) => setDraft(d => {
    const next = { ...d, [k]: v };
    if (k === "title" && !slugTouched) next.slug = slugify(v);
    return next;
  });

  const fromFindings = async () => {
    if ((draft.title || draft.body) && !window.confirm("Ersätta texten i formuläret med ett nytt utkast från månadens fynd?")) return;
    setBusy("draft"); setError(null); setNote(null);
    try {
      const d = await call(`/api/admin/blog/draft?month=${encodeURIComponent(draft.month || thisMonth())}`);
      setDraft(x => ({ ...x, ...d.draft, id: x.id, author: x.author || userName }));
      setSlugTouched(false);
      setSources(d.sources ?? []);
      setNote(d.note ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Utkastet kunde inte skapas.");
    } finally {
      setBusy(null);
    }
  };

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
               summary_en: p.summary_en ?? "", body_en: p.body_en ?? "", month: p.month, author: p.author ?? "" });
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
          <button onClick={fromFindings} disabled={busy === "draft"} className="px-4 py-2 rounded-xl border border-[#b7410e] text-[#b7410e] bg-white text-sm font-bold disabled:opacity-40">
            {busy === "draft" ? "Skapar …" : "Utkast från månadens fynd"}
          </button>
          <button onClick={() => { setDraft(empty(userName)); setSlugTouched(false); setSources([]); setNote(null); }}
            className="px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold">Nytt inlägg</button>
        </div>
      </div>
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}
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
            placeholder={"Text. ## Rubrik, - punktlista, **fet**, *kursiv*, [länk](/karta). Tom rad mellan stycken."}
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
