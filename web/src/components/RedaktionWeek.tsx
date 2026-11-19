"use client";

// "Veckans publiceringar" on /redaktion: the Monday routine from the phone. It mirrors the local Admin's WeekApproval
// (api/routers/blog_week.py), but works straight in Firestore: the plan is read from publiceringsschema (copied there
// from data/publiceringsschema.json by scripts/publiceringsschema_sync.py), each approved article is scheduled with the
// same fields as "Schemalägg" (lib/redaktion.ts schedule()), and its English Bluesky post is asked for in
// bluesky_forfragningar. The export in GitHub Actions puts the request into data/bluesky/ko.json within about half an
// hour (scripts/ci_publicera.py). Whether a row is approved is read from the article itself: scheduled or published.
import { useCallback, useEffect, useMemo, useState } from "react";
import { ErrorConfirmation, QueueNotice, type Review, ReviewChip, ReviewList } from "@/components/ArticleReview";
import { type LinkTarget, lintArticle, lintSummary } from "@/lib/articleLint";
import { checkLabels } from "@/lib/labels";
import { firestoreLib } from "@/firebase/config";
import {
  type AdminPost, BLUESKY_LIMIT, blueskyRequest, composedLength, explainError, formatStockholm, inWeek, isoWeek,
  type PlanRow, planTime, type PublicationFields, queueEnd, schedule, shiftDay, todayStockholm, weekOf, weekRefusal,
  weekState, type WeekState,
} from "@/lib/redaktion";

const RUST = "#b7410e";
const TRACK: Record<string, string> = { P: "Populärspåret", F: "Forskningsspåret" };
const chip = "inline-block text-[11px] font-semibold rounded-md px-1.5 py-0.5 border";
const good = `${chip} border-emerald-300 bg-emerald-50 text-emerald-800`;
const warn = `${chip} border-amber-300 bg-amber-50 text-amber-800`;
const plain = `${chip} border-slate-300 bg-slate-50 text-slate-600`;
const rust = `${chip} border-[#b7410e]/40 bg-[#fbf3ee] text-[#9a350b]`;
const STATE: Record<WeekState, string> = {
  utkast: plain, schemalagd: rust, publicerad: good, saknas: `${chip} border-red-300 bg-red-50 text-red-700`,
};

interface Result { key: string; ok: boolean; titel: string; text: string; bluesky?: string }

const dayLabel = (day: string) =>
  new Date(`${day}T12:00:00Z`).toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
const capital = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const rowKey = (r: PlanRow) => `${r.datum}_${r.id}`;
const message = (e: unknown) => explainError(e && typeof e === "object" && "code" in e ? String((e as { code: unknown }).code) : undefined)?.text
  ?? (e instanceof Error ? e.message : String(e));

function toRow(x: Record<string, unknown>): PlanRow {
  const b = x.bluesky as { text?: unknown; tags?: unknown } | null | undefined;
  return {
    datum: String(x.datum ?? ""), tid: String(x.tid ?? ""), id: String(x.id ?? ""), titel: String(x.titel ?? ""),
    spar: String(x.spar ?? ""), godkand: typeof x.godkand === "string" ? x.godkand : null,
    bluesky: b && typeof b.text === "string" ? { text: b.text, tags: Array.isArray(b.tags) ? b.tags.map(String) : [] } : null,
  };
}

function toPost(id: string, x: Record<string, unknown>): AdminPost {
  const at = x.publishedAt as { toDate?: () => Date } | string | null | undefined;
  return {
    id, slug: String(x.slug ?? ""), title: String(x.title ?? ""), published: !!x.published,
    publishedAt: at && typeof at === "object" && typeof at.toDate === "function" ? at.toDate() : typeof at === "string" && at ? new Date(at) : null,
    updatedAt: null, labels: Array.isArray(x.labels) ? x.labels.map(String) : [], titleEn: !!x.title_en, bodyEn: !!x.body_en,
  };
}

/** The review before approval (lib/articleLint.ts, the same rules as src/article_lint.py), apart from the journal page
 *  check, which needs the local journal database: that one runs in the local Admin. */
function reviewOf(post: AdminPost, posts: AdminPost[], at: Date, now: Date): Review {
  const targets: LinkTarget[] = posts.map(p => ({ slug: p.slug, published: p.published, publishedAt: p.publishedAt, hasEnglish: !!p.bodyEn }));
  const fynd = lintArticle({
    slug: post.slug, title: post.title, summary: post.summary, body: post.body, title_en: post.titleEnText,
    summary_en: post.summaryEn, body_en: post.bodyEnText, seo_title: post.seoTitle, seo_title_en: post.seoTitleEn,
    labels: post.labels, published: post.published, publishedAt: post.publishedAt,
  }, targets, Number.isNaN(at.getTime()) ? null : at, now);
  return { ...lintSummary(fynd), fynd };
}

/** The plan (publiceringsschema) as Firestore has it, or null until it has been read. */
export function usePlan(): PlanRow[] | null {
  const [plan, setPlan] = useState<PlanRow[] | null>(null);
  useEffect(() => {
    let alive = true;
    firestoreLib().then(async ({ db, collection, getDocs }) => {
      const rows = await getDocs(collection(db, "publiceringsschema"));
      if (alive) setPlan(rows.docs.map(d => toRow(d.data())));
    }).catch(() => { /* the week tab shows the error */ });
    return () => { alive = false; };
  }, []);
  return plan;
}

/** "Kön räcker till …" from the plan and the scheduled articles, with an alarm under three weeks. */
export function QueueStatus({ plan, posts, now }: { plan: PlanRow[]; posts: AdminPost[]; now: Date }) {
  const q = queueEnd(plan, posts, now);
  return <QueueNotice until={q.until} daysLeft={q.daysLeft} alarm={q.alarm} />;
}

/** posts: the articles as /redaktion has read them; save: the same write as "Schemalägg"; reload: read the articles again. */
export default function RedaktionWeek({ posts, now, uid, save, reload }: {
  posts: AdminPost[]; now: Date; uid: string;
  save: (id: string, fields: PublicationFields) => Promise<void>;
  reload: () => Promise<void>;
}) {
  const [start, setStart] = useState<string | null>(null);
  const [plan, setPlan] = useState<PlanRow[] | null>(null);
  const [requested, setRequested] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [checked, setChecked] = useState<Set<string> | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<Result[] | null>(null);
  const [errorsConfirmed, setErrorsConfirmed] = useState(false);

  const loadPlan = useCallback(async () => {
    try {
      const { db, collection, getDocs } = await firestoreLib();
      const [rows, reqs] = await Promise.all([
        getDocs(collection(db, "publiceringsschema")), getDocs(collection(db, "bluesky_forfragningar")),
      ]);
      setPlan(rows.docs.map(d => toRow(d.data())));
      setRequested(new Set(reqs.docs.map(d => d.id)));
      setError(null);
    } catch (e) {
      setError(`Publiceringsschemat kunde inte läsas. ${message(e)}`);
    }
  }, []);
  useEffect(() => { loadPlan(); }, [loadPlan]); // eslint-disable-line react-hooks/set-state-in-effect

  const week = weekOf(start, todayStockholm(now));
  const byId = useMemo(() => new Map(posts.map(p => [p.id, p])), [posts]);
  const rows = useMemo(() => (plan ? inWeek(plan, week.from, week.to) : []).map(r => {
    const post = byId.get(r.id) ?? null;
    const labelsProblem = post ? checkLabels(post.labels ?? []) : null;
    const review = post ? reviewOf(post, posts, planTime(r), now) : null;
    return { row: r, post, labelsProblem, review, state: weekState(post, now), reason: weekRefusal(r, post, now, labelsProblem) };
  }), [plan, week.from, week.to, byId, posts, now]);
  // By default every row that can be approved is ticked; the editor's own choice wins once made
  const isChecked = (key: string, can: boolean) => can && (checked ? checked.has(key) : true);
  const chosen = rows.filter(x => isChecked(rowKey(x.row), x.reason === null));
  const withErrors = chosen.filter(x => (x.review?.fel ?? 0) > 0);

  const go = (days: number) => {
    setStart(shiftDay(week.from, days)); setChecked(null); setResults(null); setConfirming(false); setErrorsConfirmed(false);
  };
  const toggle = (key: string) => setChecked(() => {
    const next = new Set(rows.filter(x => isChecked(rowKey(x.row), x.reason === null)).map(x => rowKey(x.row)));
    if (next.has(key)) next.delete(key); else next.add(key);
    return next;
  });

  /** Each chosen row is checked again against Firestore as it is now (the plan row and the article), then scheduled
   *  and its Bluesky post asked for. A row that fails does not stop the others. */
  const approve = async () => {
    setBusy(true); setError(null);
    const out: Result[] = [];
    const { db, doc, getDoc, setDoc, serverTimestamp } = await firestoreLib();
    for (const { row } of chosen) {
      const key = rowKey(row);
      const res: Result = { key, ok: false, titel: row.titel, text: "" };
      out.push(res);
      try {
        const planDoc = await getDoc(doc(db, "publiceringsschema", key));
        if (!planDoc.exists()) { res.text = "Står inte i veckans publiceringsschema."; continue; }
        const fresh = toRow(planDoc.data());
        if (fresh.datum < week.from || fresh.datum > week.to) { res.text = "Står inte i veckans publiceringsschema."; continue; }
        const snap = await getDoc(doc(db, "posts", fresh.id));
        const post = snap.exists() ? toPost(snap.id, snap.data()) : null;
        const at = new Date();
        const why = weekRefusal(fresh, post, at, post ? checkLabels(post.labels ?? []) : null);
        if (why || !post) { res.text = why ?? "Artikeln finns inte."; continue; }
        // The review again, on the article as Firestore has it now: errors need the editor's confirmation
        const d = snap.data()!;
        const review = reviewOf({
          ...post, summary: d.summary ?? "", body: d.body ?? "", titleEnText: d.title_en ?? "", summaryEn: d.summary_en ?? "",
          bodyEnText: d.body_en ?? "", seoTitle: d.seo_title ?? "", seoTitleEn: d.seo_title_en ?? "",
        }, posts, planTime(fresh), at);
        if (review.fel && !errorsConfirmed) {
          res.text = `Granskningen hittade ${review.fel} fel; läs dem och bekräfta godkännandet (eller rätta artikeln först).`;
          continue;
        }
        res.titel = post.title || fresh.titel;
        await save(post.id, schedule(planTime(fresh), at, uid));
        res.ok = true;
        res.text = `schemalagd ${formatStockholm(planTime(fresh))}`;
        if (!fresh.bluesky) continue;
        if (!post.bodyEn) { res.bluesky = "inget inlägg: artikeln har ingen engelsk utgåva"; continue; }
        try {
          const reqRef = doc(db, "bluesky_forfragningar", post.slug);
          if ((await getDoc(reqRef)).exists()) {
            res.bluesky = "förfrågan fanns redan (inlägget läggs inte i kön två gånger)";
          } else {
            await setDoc(reqRef, { ...blueskyRequest(fresh, post.slug, uid), created: serverTimestamp() });
            res.bluesky = `i kön ${fresh.datum} kl. 13 – läggs in vid nästa export, inom ungefär en halvtimme`;
          }
        } catch (e) {
          res.bluesky = `förfrågan kunde inte skapas (${message(e)}); lägg inlägget i data/bluesky/ko.json för hand`;
        }
      } catch (e) {
        res.text = message(e);
      }
    }
    setResults(out);
    setConfirming(false);
    setErrorsConfirmed(false);
    setChecked(null);
    await Promise.all([reload(), loadPlan()]);
    setBusy(false);
  };

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 space-y-4">
      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-serif font-bold">Veckans publiceringar (vecka {isoWeek(week.from)})</h2>
          <p className="text-sm text-slate-500">
            {capital(dayLabel(week.from))} – {dayLabel(week.to)}. Godkända artiklar schemaläggs till sin tid, och deras
            engelska inlägg läggs i Bluesky-kön och går ut samma dag kl. 13 (kön postar tisdagar och fredagar).
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => go(-7)} disabled={busy}
            className="px-3 py-2.5 rounded-lg border border-slate-300 bg-white text-sm font-semibold disabled:opacity-40">← Förra veckan</button>
          <button onClick={() => go(7)} disabled={busy}
            className="px-3 py-2.5 rounded-lg border border-slate-300 bg-white text-sm font-semibold disabled:opacity-40">Nästa vecka →</button>
        </div>
      </div>

      {plan && <QueueStatus plan={plan} posts={posts} now={now} />}
      {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</div>}
      {!plan && !error && <p className="text-sm text-slate-500">Hämtar …</p>}
      {plan && rows.length === 0 && (
        <p className="text-sm text-slate-500">
          Inget planerat den här veckan. Lägg till rader i data/publiceringsschema.json och kör
          scripts/publiceringsschema_sync.py --skriv på datorn.
        </p>
      )}

      {rows.length > 0 && (
        <ul className="divide-y divide-slate-100">
          {rows.map(({ row, post, labelsProblem, review, state, reason }) => {
            const key = rowKey(row);
            const n = composedLength(row.bluesky);
            const english = !!(post?.titleEn && post?.bodyEn);
            return (
              <li key={key} className="py-3 flex gap-3">
                <input type="checkbox" checked={isChecked(key, reason === null)} disabled={reason !== null || busy}
                  onChange={() => toggle(key)} aria-label={`Godkänn ${row.titel}`}
                  className="mt-1 h-5 w-5 shrink-0 accent-[#b7410e]" />
                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="text-xs font-semibold" style={{ color: RUST }}>{capital(dayLabel(row.datum))} kl. {row.tid || "07:00"}</div>
                  <div className="font-medium break-words" translate="no">{post?.title || row.titel}</div>
                  <div className="flex flex-wrap gap-1.5">
                    <span className={plain}>{TRACK[row.spar] ?? row.spar}</span>
                    {(state === "schemalagd" || state === "publicerad") && <span className={rust}>godkänd</span>}
                    <span className={STATE[state]}>
                      {state === "schemalagd" && post?.publishedAt ? `schemalagd ${formatStockholm(post.publishedAt)}` : state}
                    </span>
                    {post && <span className={english ? good : warn}>{english ? "engelska" : "engelska saknas"}</span>}
                    {post && <span className={labelsProblem ? warn : good} title={(post.labels ?? []).join(", ")}>{labelsProblem ? "etiketter: fel" : "etiketter"}</span>}
                    {n !== null
                      ? <span className={n > BLUESKY_LIMIT ? warn : good}>Bluesky {n}/{BLUESKY_LIMIT}</span>
                      : <span className={plain}>inget Bluesky-inlägg</span>}
                    {post?.slug && requested.has(post.slug) && <span className={good}>Bluesky-förfrågan skickad</span>}
                    <ReviewChip review={review} />
                  </div>
                  <ReviewList review={review} />
                  {post?.slug && <div className="text-xs text-slate-400 break-all" translate="no">/artiklar/{post.slug}</div>}
                  {reason && <p className="text-xs text-slate-600">{reason}</p>}
                  {row.bluesky && (
                    <details className="text-sm text-slate-600">
                      <summary className="cursor-pointer py-1 font-semibold">Bluesky-inlägget</summary>
                      <p className="mt-1 whitespace-pre-wrap break-words rounded-lg border border-slate-200 bg-[#f6f4f1] p-2" lang="en" translate="no">
                        {row.bluesky.text}{row.bluesky.tags.length ? "\n\n" + row.bluesky.tags.map(t => `#${t}`).join(" ") : ""}
                      </p>
                    </details>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {rows.length > 0 && !confirming && (
        <button onClick={() => { setConfirming(true); setResults(null); setErrorsConfirmed(false); }} disabled={chosen.length === 0 || busy}
          className="w-full sm:w-auto px-4 py-3 rounded-xl text-white font-semibold disabled:opacity-40" style={{ background: RUST }}>
          Godkänn veckans publiceringar{chosen.length ? ` (${chosen.length})` : ""}
        </button>
      )}

      {confirming && (
        <div className="rounded-xl border border-[#b7410e]/40 bg-[#fbf3ee] p-3 space-y-3 text-sm">
          <p className="font-semibold">Det här schemaläggs:</p>
          <ul className="list-disc pl-5 space-y-1">
            {chosen.map(({ row, post }) => (
              <li key={rowKey(row)}>
                {capital(dayLabel(row.datum))} kl. {row.tid || "07:00"}: <span translate="no">{post?.title || row.titel}</span>
                {row.bluesky ? (post?.bodyEn ? " – och Bluesky-inlägget samma dag kl. 13" : " – inget Bluesky-inlägg (ingen engelsk utgåva)") : ""}
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-600">
            Texterna ändras inte. Artiklarna går ut på webbplatsen inom ungefär en halvtimme efter sin tid. Sidhänvisningarna
            till Fornvännen och Futhark prövas bara i den lokala Admin, som har tidskrifterna.
          </p>
          <ErrorConfirmation titles={withErrors.map(x => x.post?.title || x.row.titel)} confirmed={errorsConfirmed} onChange={setErrorsConfirmed} />
          <div className="grid grid-cols-2 sm:flex gap-2">
            <button onClick={approve} disabled={busy || (withErrors.length > 0 && !errorsConfirmed)} className="px-4 py-2.5 rounded-xl text-white font-semibold disabled:opacity-40" style={{ background: RUST }}>
              {busy ? "Schemalägger …" : "Ja, schemalägg"}
            </button>
            <button onClick={() => setConfirming(false)} disabled={busy} className="px-4 py-2.5 rounded-xl border border-slate-300 bg-white font-semibold disabled:opacity-40">
              Avbryt
            </button>
          </div>
        </div>
      )}

      {results && (
        <ul className="space-y-1.5 text-sm" role="status">
          {results.map(r => (
            <li key={r.key} className={r.ok ? "text-emerald-800" : "text-rose-800"}>
              <span className="font-semibold" translate="no">{r.titel}</span>:{" "}
              {r.ok ? <>{r.text}{r.bluesky ? `; Bluesky: ${r.bluesky}` : ""}.</> : <>inte schemalagd – {r.text}</>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
