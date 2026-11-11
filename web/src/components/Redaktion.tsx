"use client";

// The web admin (/redaktion): sign in with Google, see what is scheduled, and schedule, publish or unpublish articles
// straight in Firestore – from any device, without the local app. The Firestore rules (web/firestore.rules) let only
// the editor read the articles and change their publication fields; the fields and their meaning are those of the local
// app's save (lib/redaktion.ts). Texts are written and deleted only in the local app. The public website follows within
// about half an hour (.github/workflows/publicera.yml). "Veckan" approves the week's planned articles (RedaktionWeek).
import { useCallback, useEffect, useMemo, useState } from "react";
import type { User } from "firebase/auth";
import BlogBody from "@/components/BlogBody";
import RedaktionWeek from "@/components/RedaktionWeek";
import { FIREBASE_CONFIGURED, firebaseAuth, firestoreLib } from "@/firebase/config";
import { postPath } from "@/lib/blogSeo";
import { reportPath } from "@/lib/report";
import { GITHUB_URL } from "@/lib/site";
import {
  type AdminPost, explainError, type Filter, formatStockholm, fromStockholm, isReport, latestPublished, matches, ordered,
  type PublicationFields, publishNow, schedule, status, type Status, toStockholmInput, unpublish, upcoming,
} from "@/lib/redaktion";

const RUST = "#b7410e";
const REPO_API = "https://api.github.com/repos/Precatio/runes/actions/workflows";
const WORKFLOWS: [string, string][] = [["site.yml", "Webbplatsens bygge"], ["publicera.yml", "Export ur Firestore"], ["bluesky.yml", "Bluesky-kön"]];
const STATUS_LABEL: Record<Status, string> = { utkast: "Utkast", schemalagd: "Schemalagd", publicerad: "Publicerad" };
const STATUS_STYLE: Record<Status, string> = {
  utkast: "bg-slate-100 text-slate-600",
  schemalagd: "bg-[#b7410e]/10 text-[#9a350b]",
  publicerad: "bg-emerald-50 text-emerald-700",
};
const FILTERS: [Filter, string][] = [["alla", "Alla"], ["utkast", "Utkast"], ["schemalagd", "Schemalagda"], ["publicerad", "Publicerade"], ["rapporter", "Rapporter"]];

type Phase = "laddar" | "ej-konfigurerad" | "utloggad" | "inloggad";
interface Problem { notActive: boolean; text: string }
interface Run { name: string; status: string; conclusion: string | null; url: string; at: string }

const toDate = (v: unknown): Date | null =>
  v && typeof v === "object" && "toDate" in v && typeof (v as { toDate: unknown }).toDate === "function"
    ? (v as { toDate: () => Date }).toDate() : typeof v === "string" && v ? new Date(v) : null;

const codeOf = (e: unknown) => (e && typeof e === "object" && "code" in e ? String((e as { code: unknown }).code) : undefined);

/** Writes one publication change: exactly the fields lib/redaktion.ts gives, plus the server's time. "Schemalägg",
 *  "Publicera nu", "Avpublicera" and the week's approval all write through here. */
async function savePublication(id: string, fields: PublicationFields): Promise<void> {
  const { db, doc, updateDoc, serverTimestamp, Timestamp } = await firestoreLib();
  const data: Record<string, unknown> = { published: fields.published, by: fields.by, updatedAt: serverTimestamp() };
  if (fields.publishedAt) data.publishedAt = Timestamp.fromDate(fields.publishedAt);
  if (fields.month) data.month = fields.month;
  await updateDoc(doc(db, "posts", id), data);
}

function problemOf(e: unknown): Problem {
  return explainError(codeOf(e)) ?? { notActive: false, text: `Något gick fel: ${e instanceof Error ? e.message : String(e)}` };
}

export default function Redaktion() {
  const [phase, setPhase] = useState<Phase>(FIREBASE_CONFIGURED ? "laddar" : "ej-konfigurerad");
  const [user, setUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<AdminPost[] | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [tab, setTab] = useState<"oversikt" | "veckan" | "innehall">("oversikt");
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    if (!FIREBASE_CONFIGURED) return;
    let unsub = () => {};
    firebaseAuth().then(({ auth, lib }) => {
      unsub = lib.onAuthStateChanged(auth, u => { setUser(u); setPhase(u ? "inloggad" : "utloggad"); });
    }).catch(e => { setProblem(problemOf(e)); setPhase("utloggad"); });
    return () => unsub();
  }, []);

  // The clock for the states (a scheduled article becomes published while the page is open)
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(t);
  }, []);

  const load = useCallback(async () => {
    setProblem(null);
    try {
      const { db, collection, getDocs } = await firestoreLib();
      const snap = await getDocs(collection(db, "posts"));
      setPosts(snap.docs.map(d => {
        const x = d.data();
        return {
          id: d.id, slug: String(x.slug ?? ""), title: String(x.title ?? "(utan titel)"), summary: x.summary ?? "",
          body: x.body ?? "", published: !!x.published, publishedAt: toDate(x.publishedAt), updatedAt: toDate(x.updatedAt),
          month: x.month, labels: Array.isArray(x.labels) ? x.labels : [], featured: !!x.featured,
          titleEn: !!x.title_en, bodyEn: !!x.body_en,
        };
      }));
      setNow(new Date());
    } catch (e) {
      setPosts(null);
      setProblem(problemOf(e));
    }
  }, []);

  useEffect(() => {
    if (phase === "inloggad") load(); // eslint-disable-line react-hooks/set-state-in-effect
  }, [phase, load]);

  const signIn = async () => {
    setProblem(null);
    try {
      const { auth, lib } = await firebaseAuth();
      await lib.signInWithPopup(auth, new lib.GoogleAuthProvider());
    } catch (e) {
      setProblem(problemOf(e));
    }
  };
  const signOut = async () => {
    const { auth, lib } = await firebaseAuth();
    await lib.signOut(auth);
    setPosts(null);
  };

  /** One publication change from the Innehåll list, with a notice and the list read again. */
  const write = async (p: AdminPost, fields: PublicationFields, done: string) => {
    setProblem(null);
    setNotice(null);
    try {
      await savePublication(p.id, fields);
      setNotice(`${done} Webbplatsen följer efter inom ungefär en halvtimme (eller direkt, om den lokala appen är igång).`);
      await load();
    } catch (e) {
      setProblem(problemOf(e));
    }
  };

  return (
    <div className="min-h-screen bg-[#f6f4f1] text-slate-900">
      <header className="border-b border-slate-900/10 bg-white/70">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center gap-3 justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em]" style={{ color: RUST }}>Vitki</div>
            <h1 className="text-2xl font-serif font-bold">Redaktion</h1>
          </div>
          {user && (
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-500 hidden sm:inline">{user.displayName || "Inloggad"}</span>
              <button onClick={signOut} className="px-3 py-1.5 rounded border border-slate-300 hover:bg-white">Logga ut</button>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        {phase === "ej-konfigurerad" && (
          <NotActive text="Webbplatsen är byggd utan inloggningens konfiguration (repovariablerna FIREBASE_WEB_API_KEY och FIREBASE_WEB_APP_ID saknas i GitHub)." />
        )}
        {phase === "laddar" && <p className="text-slate-500">Laddar …</p>}
        {phase === "utloggad" && (
          <div className="max-w-md mx-auto mt-10 bg-white rounded-xl border border-slate-200 p-6 text-center">
            <p className="mb-5 text-slate-600">Logga in med det Google-konto som är redaktör för Vitki.</p>
            <button onClick={signIn} className="px-5 py-2.5 rounded-lg text-white font-medium" style={{ background: RUST }}>
              Logga in med Google
            </button>
          </div>
        )}
        {problem && (problem.notActive ? <NotActive text={problem.text} /> : (
          <div role="alert" className="my-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{problem.text}</div>
        ))}
        {notice && <div role="status" className="my-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div>}

        {phase === "inloggad" && posts && (
          <>
            <nav className="flex gap-1 mb-6 border-b border-slate-200" aria-label="Vyer">
              {([["oversikt", "Översikt"], ["veckan", "Veckan"], ["innehall", "Innehåll"]] as const).map(([k, label]) => (
                <button key={k} onClick={() => setTab(k)} aria-current={tab === k ? "page" : undefined}
                        className={`px-3 sm:px-4 py-2 -mb-px border-b-2 font-medium ${tab === k ? "border-[#b7410e] text-[#9a350b]" : "border-transparent text-slate-500 hover:text-slate-800"}`}>
                  {label}
                </button>
              ))}
              <button onClick={load} className="ml-auto px-2 sm:px-3 py-2 text-sm text-slate-500 hover:text-slate-800">Uppdatera</button>
            </nav>
            {tab === "oversikt" && <Overview posts={posts} now={now} />}
            {tab === "veckan" && <RedaktionWeek posts={posts} now={now} uid={user!.uid} save={savePublication} reload={load} />}
            {tab === "innehall" && <Content posts={posts} now={now} uid={user!.uid} write={write} />}
          </>
        )}
      </main>
    </div>
  );
}

function NotActive({ text }: { text: string }) {
  return (
    <div className="my-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
      <h2 className="font-semibold text-amber-900 mb-1">Redaktionen är inte aktiverad än</h2>
      <p className="text-sm text-amber-900/80">{text}</p>
      <p className="text-sm text-amber-900/80 mt-2">
        Stegen står i <a className="underline" href={`${GITHUB_URL}/blob/main/ADMIN_PA_WEBBEN.md`} target="_blank" rel="noopener noreferrer">ADMIN_PA_WEBBEN.md</a>.
        Under tiden publicerar du som vanligt i den lokala appen.
      </p>
    </div>
  );
}

function Overview({ posts, now }: { posts: AdminPost[]; now: Date }) {
  const next = upcoming(posts, now);
  const drafts = posts.filter(p => status(p, now) === "utkast").length;
  const latest = latestPublished(posts, now);
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card title="Schemalagt de närmaste fyra veckorna">
        {next.length ? (
          <ul className="divide-y divide-slate-100">
            {next.map(p => (
              <li key={p.id} className="py-2">
                <div className="text-sm font-medium" style={{ color: RUST }}>{formatStockholm(p.publishedAt)}</div>
                <div>{p.title}{isReport(p) && <span className="ml-2 text-xs text-slate-500">Rapport</span>}</div>
              </li>
            ))}
          </ul>
        ) : <p className="text-slate-500 text-sm">Inget schemalagt.</p>}
      </Card>
      <div className="grid gap-6">
        <Card title="Utkast"><div className="text-3xl font-serif font-bold">{drafts}</div></Card>
        <Card title="Senast publicerat">
          <ul className="space-y-1.5">
            {latest.map(p => (
              <li key={p.id} className="text-sm">
                <a href={isReport(p) ? reportPath(p.slug) : postPath(p.slug)} target="_blank" rel="noopener noreferrer" className="hover:underline">{p.title}</a>
                <span className="text-slate-500"> · {formatStockholm(p.publishedAt)}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <div className="md:col-span-2"><BuildStatus /></div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white rounded-xl border border-slate-200 p-5">
      <h2 className="text-xs font-bold uppercase tracking-[0.15em] text-slate-500 mb-3">{title}</h2>
      {children}
    </section>
  );
}

/** The latest run of each workflow, from GitHub's open API (the repository is public; no token). */
function BuildStatus() {
  const [runs, setRuns] = useState<Run[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    Promise.all(WORKFLOWS.map(async ([file, name]) => {
      const r = await fetch(`${REPO_API}/${file}/runs?per_page=1`, { headers: { Accept: "application/vnd.github+json" } });
      if (!r.ok) throw new Error(String(r.status));
      const run = (await r.json()).workflow_runs?.[0];
      return run ? { name, status: run.status, conclusion: run.conclusion, url: run.html_url, at: run.created_at } : null;
    })).then(rs => setRuns(rs.filter((r): r is Run => !!r))).catch(() => setFailed(true));
  }, []);
  const word = (r: Run) => r.status !== "completed" ? "pågår" : r.conclusion === "success" ? "klar" : r.conclusion === "skipped" ? "hoppades över" : r.conclusion ?? "okänt";
  const style = (r: Run) => r.status !== "completed" ? "text-amber-700" : r.conclusion === "success" ? "text-emerald-700" : "text-rose-700";
  return (
    <Card title="Webbplatsen och automatiken">
      {failed || (runs && !runs.length) ? (
        <p className="text-sm">Statusen kunde inte hämtas. <a className="underline" href={`${GITHUB_URL}/actions`} target="_blank" rel="noopener noreferrer">Se GitHub Actions</a>.</p>
      ) : !runs ? <p className="text-sm text-slate-500">Hämtar …</p> : (
        <ul className="space-y-1.5 text-sm">
          {runs.map(r => (
            <li key={r.name} className="flex flex-wrap gap-x-2">
              <span className="font-medium">{r.name}:</span>
              <a href={r.url} target="_blank" rel="noopener noreferrer" className={`underline ${style(r)}`}>{word(r)}</a>
              <span className="text-slate-500">{formatStockholm(new Date(r.at))}</span>
            </li>
          ))}
          <li className="pt-1"><a className="underline text-slate-500" href={`${GITHUB_URL}/actions`} target="_blank" rel="noopener noreferrer">Alla körningar</a></li>
        </ul>
      )}
    </Card>
  );
}

function Content({ posts, now, uid, write }: {
  posts: AdminPost[]; now: Date; uid: string; write: (p: AdminPost, f: PublicationFields, done: string) => Promise<void>;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("alla");
  const [preview, setPreview] = useState<AdminPost | null>(null);
  const [planning, setPlanning] = useState<string | null>(null);
  const [when, setWhen] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const shown = useMemo(() => ordered(posts, now).filter(p => matches(p, query, filter, now)), [posts, now, query, filter]);

  const run = async (p: AdminPost, make: () => PublicationFields, done: string, ask?: string) => {
    setError(null);
    let fields: PublicationFields;
    try { fields = make(); } catch (e) { setError(e instanceof Error ? e.message : String(e)); return; }
    if (ask && !window.confirm(ask)) return;
    setBusy(p.id);
    await write(p, fields, done);
    setBusy(null);
    setPlanning(null);
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Sök titel, adress eller etikett"
               className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2" aria-label="Sök" />
        <div className="flex flex-wrap gap-1.5">
          {FILTERS.map(([k, label]) => (
            <button key={k} onClick={() => setFilter(k)} aria-pressed={filter === k}
                    className={`px-3 py-1.5 rounded-full text-sm border ${filter === k ? "bg-[#b7410e] border-[#b7410e] text-white" : "bg-white border-slate-300 text-slate-700"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>
      {error && <div role="alert" className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-800">{error}</div>}
      <p className="text-sm text-slate-500 mb-2">{shown.length} av {posts.length}. Tider i svensk tid.</p>
      <ul className="space-y-2">
        {shown.map(p => {
          const s = status(p, now);
          return (
            <li key={p.id} className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-start gap-2 justify-between">
                <div className="min-w-0">
                  <div className="font-medium break-words">{p.title}</div>
                  <div className="text-xs text-slate-500 break-all">/{p.slug}{(p.labels ?? []).length ? ` · ${(p.labels ?? []).join(", ")}` : ""}</div>
                </div>
                <div className="text-right shrink-0">
                  <span className={`inline-block text-xs px-2 py-0.5 rounded-full ${STATUS_STYLE[s]}`}>{STATUS_LABEL[s]}</span>
                  {p.publishedAt && <div className="text-xs text-slate-500 mt-1">{formatStockholm(p.publishedAt)}</div>}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-3 text-sm">
                <button onClick={() => setPreview(p)} className="px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-50">Förhandsgranska</button>
                <button disabled={busy === p.id}
                        onClick={() => { setPlanning(planning === p.id ? null : p.id); setWhen(toStockholmInput(s === "schemalagd" && p.publishedAt ? p.publishedAt : new Date(now.getTime() + 86_400_000))); }}
                        className="px-3 py-1.5 rounded border border-[#b7410e]/40 text-[#9a350b] hover:bg-[#b7410e]/5">Schemalägg</button>
                {s !== "publicerad" && (
                  <button disabled={busy === p.id} className="px-3 py-1.5 rounded text-white disabled:opacity-50" style={{ background: RUST }}
                          onClick={() => run(p, () => publishNow(p, new Date(), uid), `"${p.title}" är publicerad.`, `Publicera "${p.title}" nu?`)}>
                    Publicera nu
                  </button>
                )}
                {s !== "utkast" && (
                  <button disabled={busy === p.id} className="px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-50 disabled:opacity-50"
                          onClick={() => run(p, () => unpublish(uid), `"${p.title}" är ett utkast igen.`,
                            `Avpublicera "${p.title}"? ${s === "publicerad" ? "Den försvinner från webbplatsen vid nästa export." : "Schemaläggningen tas bort."}`)}>
                    Avpublicera
                  </button>
                )}
              </div>
              {planning === p.id && (
                <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                  <label className="flex items-center gap-2">Publiceras
                    <input type="datetime-local" value={when} onChange={e => setWhen(e.target.value)}
                           className="rounded border border-slate-300 px-2 py-1" />
                  </label>
                  <span className="text-slate-500">svensk tid</span>
                  <button disabled={busy === p.id} className="px-3 py-1.5 rounded text-white disabled:opacity-50" style={{ background: RUST }}
                          onClick={() => run(p, () => schedule(fromStockholm(when), new Date(), uid), `"${p.title}" är schemalagd till ${when.replace("T", " ")}.`)}>
                    Spara tiden
                  </button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
      {preview && <Preview post={preview} now={now} onClose={() => setPreview(null)} />}
    </div>
  );
}

function Preview({ post, now, onClose }: { post: AdminPost; now: Date; onClose: () => void }) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);
  const live = status(post, now) === "publicerad";
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-stretch sm:items-center justify-center sm:p-6" onClick={onClose} role="dialog" aria-modal="true" aria-label="Förhandsgranskning">
      <div className="bg-[#f6f4f1] w-full max-w-3xl sm:rounded-xl overflow-y-auto max-h-full" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
          <span className="text-sm text-slate-500 flex-1">Förhandsgranskning{live ? "" : " – inte publicerad"}</span>
          {live && <a className="text-sm underline" style={{ color: RUST }} href={isReport(post) ? reportPath(post.slug) : postPath(post.slug)} target="_blank" rel="noopener noreferrer">Öppna på webbplatsen</a>}
          <button onClick={onClose} className="px-3 py-1 rounded border border-slate-300">Stäng</button>
        </div>
        <article className="px-5 sm:px-8 py-6">
          <h1 className="text-3xl font-serif font-bold mb-3">{post.title}</h1>
          {post.summary && <p className="text-lg text-slate-600 mb-6">{post.summary}</p>}
          <BlogBody text={post.body ?? ""} />
          <p className="mt-8 text-xs text-slate-500">R-figurer som ännu inte finns på webbplatsen visas bara i den lokala appen.</p>
        </article>
      </div>
    </div>
  );
}
