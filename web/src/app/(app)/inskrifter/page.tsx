"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { GeologyBox, LanguageTraits } from "@/components/StoneContext";
import { SIMILARITY_HELP, fmtP } from "@/lib/significance";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CARVER_KIND,
  PERIOD_LABEL,
  rundata,
  type CarverRanking,
  type Inscription,
  type OrthographyProfile,
  type RundataMeta,
  type SimilarInscription,
} from "@/lib/rundata";

const PROVINCES = ["U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Vs", "Nä", "Gs", "Hs", "M", "Ån", "J", "D", "Bo", "DR", "N"];
const STYLES = ["RAK", "Fp", "KB", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"];
const PAGE = 30;

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  if (!children) return null;
  return (
    <div>
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-0.5">{label}</div>
      <div className="text-sm text-slate-800 font-medium leading-relaxed">{children}</div>
    </div>
  );
}

function Attribution({ meta }: { meta: RundataMeta | null }) {
  if (!meta) return null;
  return (
    <p className="text-[11px] text-slate-500 leading-relaxed">
      Uppgifter ur {meta.source}. {meta.attribution} {meta.note}
    </p>
  );
}

function InscriptionDetail({ signum, meta }: { signum: string; meta: RundataMeta | null }) {
  const [rec, setRec] = useState<Inscription | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<OrthographyProfile | null>(null);
  const [ranking, setRanking] = useState<CarverRanking | null>(null);
  const [similar, setSimilar] = useState<SimilarInscription[] | null>(null);
  const [orthoNote, setOrthoNote] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await rundata.inscription(signum);
        if (cancelled) return;
        setRec(r);
        try {
          const [p, rk, sim] = await Promise.all([
            rundata.orthographyProfile(r.signum),
            rundata.carverRanking(r.signum, 6),
            rundata.similar(r.signum, 8),
          ]);
          if (cancelled) return;
          setProfile(p); setRanking(rk); setSimilar(sim);
        } catch (e) {
          if (!cancelled) setOrthoNote(e instanceof Error ? e.message : "Ortografisk analys ej tillgänglig.");
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Kunde inte hämta inskriften.");
      }
    })();
    return () => { cancelled = true; };
  }, [signum]);

  if (error) return <div className="liquid-glass-island rounded-[32px] p-8 text-red-700 font-semibold">{error}</div>;
  if (!rec) return <div className="liquid-glass-island rounded-[32px] p-8 text-slate-500">Hämtar {signum}...</div>;

  const flags = [
    rec.flags.lost && "försvunnen",
    rec.flags.new_reading && "nyläsning",
    rec.flags.medieval && "medeltida",
    rec.flags.proto_norse && "urnordisk",
  ].filter(Boolean);

  return (
    <div className="space-y-6">
      <div className="liquid-glass-island rounded-[32px] p-8 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900">{rec.signum}</h2>
            <p className="text-slate-600 font-medium">{[rec.place, rec.parish, rec.district].filter(Boolean).join(", ")}</p>
            {flags.length > 0 && (
              <div className="flex gap-2 mt-2">
                {flags.map(f => <span key={String(f)} className="text-[10px] font-bold uppercase bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">{f}</span>)}
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {rec.lat !== null && (
              <Link href={`/karta?signum=${encodeURIComponent(rec.signum)}`} className="px-3 py-2 text-xs font-bold rounded-xl bg-white border border-slate-300 hover:border-slate-900">Visa på karta</Link>
            )}
            {rec.image_link && (
              <a href={rec.image_link} target="_blank" rel="noopener noreferrer" className="px-3 py-2 text-xs font-bold rounded-xl bg-white border border-slate-300 hover:border-slate-900">Bilder (extern länk)</a>
            )}
            <Link href={`/3d?signum=${encodeURIComponent(rec.signum)}`} className="px-3 py-2 text-xs font-bold rounded-xl bg-slate-900 text-white hover:bg-black">Analysera i 3D</Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Field label="Datering">{rec.dating || (rec.period ? PERIOD_LABEL[rec.period] : "")}</Field>
          <Field label="Stilgrupp">
            {rec.style && <Link href={`/stilgrupper#${rec.style}`} className="text-[#b7410e] hover:underline">{rec.style}{rec.style_uncertain ? " (osäker)" : ""}</Link>}
          </Field>
          <Field label="Ristare">
            {rec.carvers.length > 0 ? rec.carvers.map((c, i) => (
              <span key={c.name}>
                {i > 0 && ", "}
                <Link href={`/inskrifter?carver=${encodeURIComponent(c.name)}`} className="text-[#b7410e] hover:underline">{c.name}</Link>
                <span className="text-slate-500"> ({CARVER_KIND[c.kind]}{c.uncertain ? ", osäker" : ""})</span>
              </span>
            )) : rec.carver_raw}
          </Field>
          <Field label="Material">{[rec.material_type, rec.material].filter(Boolean).join(" – ")}</Field>
          <Field label="Mått (Kulturmiljöregistret)">
            {rec.dimensions && (
              <span title={rec.dimensions.description}>
                {[rec.dimensions.height_m && `${rec.dimensions.height_m.toFixed(2).replace(".", ",")} m hög`,
                  rec.dimensions.width_m && `${rec.dimensions.width_m.toFixed(2).replace(".", ",")} m bred`,
                  rec.dimensions.rune_height_cm && `runhöjd ${rec.dimensions.rune_height_cm.toFixed(1).replace(".", ",")} cm`]
                  .filter(Boolean).join(", ")}
                {rec.dimensions.fragment && " (fragment)"}
                {rec.dimensions.in_province && (
                  <span className="text-slate-500"> · högre än {rec.dimensions.in_province.percentile} % i {rec.dimensions.in_province.province}</span>
                )}{" "}
                <a href={rec.dimensions.kmr_url} target="_blank" rel="noopener noreferrer" className="text-[#b7410e] hover:underline text-xs">källa</a>
              </span>
            )}
          </Field>
          <Field label="Föremål">{rec.object}</Field>
          <Field label="Placering">{rec.placement}</Field>
          <Field label="Runtyper">{rec.rune_types}</Field>
          <Field label="Korsform (Lager)">{rec.cross_form}</Field>
          <Field label="Alternativt signum">{rec.alt_signum}</Field>
        </div>

        <div className="space-y-4">
          <Field label="Translitterering"><span className="font-mono">{rec.transliteration}</span></Field>
          <Field label="Normalisering (runsvenska/rundanska/fornvästnordiska)"><em>{rec.normalization}</em></Field>
          <Field label="Fornvästnordisk normalisering"><em>{rec.normalization_ows}</em></Field>
          <Field label="Översättning (engelska)">{rec.translation_en}</Field>
          <Field label="Övrigt">{rec.other}</Field>
          <Field label="Referenser">{rec.references}</Field>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2 border-t border-slate-900/5">
          <div className="space-y-2">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Bergart och berggrund</div>
            {rec.lat != null && rec.material ? <GeologyBox signum={rec.signum} /> : <p className="text-xs text-slate-500">Material eller koordinater saknas i Rundata.</p>}
          </div>
          <div className="space-y-2">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Språkdrag (fonetisk stil och språkbruk)</div>
            <LanguageTraits signum={rec.signum} />
          </div>
        </div>
        <Attribution meta={meta} />
      </div>

      <div className="liquid-glass-island rounded-[32px] p-8 space-y-6">
        <div>
          <h3 className="text-xl font-bold text-slate-900">Ortografisk profil</h3>
          <p className="text-xs text-slate-500 font-medium mt-1">
            Stavning, skiljetecken och bindrunor jämförda med Rundatas vikingatida inskrifter. Egennamn räknas inte, så att
            signaturer inte avslöjar ristaren.
          </p>
        </div>
        {orthoNote && <p className="text-sm text-slate-600 bg-white/60 rounded-xl p-3">{orthoNote}</p>}
        {profile && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-3">
              <Field label="Läsbara ord">{profile.n_words}</Field>
              <Field label="Skiljetecken">
                {Object.entries(profile.separators).filter(([, n]) => n > 0).map(([k, n]) => `${k} ${n}`).join(" · ") || "inga"}
                {" "}(täthet {profile.separator_density.toFixed(2)} per ord)
              </Field>
              <Field label="Bindrunor per ord">{profile.bindrune_rate.toFixed(2)}</Field>
              {Object.keys(profile.spellings).length > 0 && (
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Stavningar (normaliserat → runtext)</div>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(profile.spellings).slice(0, 40).map(([n, w]) => (
                      <span key={n} className="text-xs bg-white/70 border border-slate-200 rounded-lg px-2 py-0.5">
                        <em>{n}</em> → <span className="font-mono">{w}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {ranking && (
              <div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">Mest lika ristare (ortografiskt)</div>
                <div className="space-y-1.5">
                  {ranking.ranking.map((r, i) => (
                    <div key={r.carver} className="flex justify-between items-center bg-white/60 rounded-xl px-3 py-2 text-sm">
                      <Link href={`/inskrifter?carver=${encodeURIComponent(r.carver)}`} className="font-semibold text-slate-800 hover:text-[#b7410e]">{i + 1}. {r.carver}</Link>
                      <span className="text-xs font-mono text-slate-500" title={SIMILARITY_HELP}>
                        likhet {r.similarity.toFixed(2).replace(".", ",")}
                        {r.significance && <> · p {fmtP(r.significance.p_value)} (just. {fmtP(r.significance.p_adjusted)})</>}
                        {" "}· {r.n_inscriptions} inskr.
                      </span>
                    </div>
                  ))}
                </div>
                <p className="text-[11px] text-slate-500 mt-3 leading-relaxed">
                  Metodens träffsäkerhet (lämna-en-ute): rätt ristare först i {(ranking.evaluation.top1_accuracy * 100).toFixed(0)} %
                  {ranking.evaluation.signed_only.top1_accuracy !== null && <> ({(ranking.evaluation.signed_only.top1_accuracy * 100).toFixed(0)} % för enbart signerade)</>}
                  {" "}bland {ranking.evaluation.n_carvers} ristare; slumpnivå {(ranking.evaluation.chance_top1 * 100).toFixed(0)} %.
                  {ranking.n_words < 10 && " Kort text – tolka med extra försiktighet."}
                  {" "}{SIMILARITY_HELP}
                </p>
              </div>
            )}
          </div>
        )}
        {similar && similar.length > 0 && (
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">Ortografiskt mest lika inskrifter</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {similar.map(s => (
                <Link key={s.signum} href={`/inskrifter?signum=${encodeURIComponent(s.signum)}`}
                  className="bg-white/60 hover:bg-white rounded-xl px-3 py-2 text-sm block">
                  <div className="flex justify-between">
                    <span className="font-semibold text-slate-800">{s.signum} <span className="text-slate-500 font-normal">{s.place}</span></span>
                    <span className="text-xs font-mono text-slate-500">{s.similarity.toFixed(2)}</span>
                  </div>
                  <div className="text-xs text-slate-500">
                    {s.carvers.map(c => `${c.name} (${c.kind})`).join(", ") || "ingen ristare angiven"}
                    {s.style && ` · ${s.style}`}
                    {Object.keys(s.shared_spellings).length > 0 && ` · delar ${Object.keys(s.shared_spellings).length} stavningar`}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Filters from the research-gaps overview (same definitions as there)
const GAP_LABEL: Record<string, string> = {
  runestone: "vikingatida runstenar",
  carver: "runstenar med ristare",
  no_carver: "runstenar utan ristare",
  style: "runstenar med säker stilgrupp",
  no_style: "runstenar utan säker stilgrupp",
  dated: "runstenar daterade med årtal",
  uncertain_interpretation: "osäkert tolkade runstenar",
  lost: "försvunna runstenar",
};

const CATEGORY_LABEL: Record<string, string> = {
  minne: "minnesinskrift", sjalvminne: "självminne", bro_vag: "bro- och vägbygge", kristen: "kristen bön eller formel",
  fard: "utlandsfärd", arv: "arv och ägande", ting: "ting och offentlighet", magisk: "magisk eller rituell", grans: "gränsmärke",
};

function InscriptionsContent() {
  const params = useSearchParams();
  const router = useRouter();
  const signum = params.get("signum");
  const [meta, setMeta] = useState<RundataMeta | null>(null);
  const [q, setQ] = useState(params.get("q") ?? "");
  const [province, setProvince] = useState(params.get("province") ?? "");
  const [period, setPeriod] = useState(params.get("period") ?? "");
  const [style, setStyle] = useState(params.get("style") ?? "");
  const [carver, setCarver] = useState(params.get("carver") ?? "");
  const [gap, setGap] = useState(params.get("gap") ?? "");
  const [signa, setSigna] = useState(params.get("signa") ?? "");
  const [category, setCategory] = useState(params.get("category") ?? "");
  const [certain, setCertain] = useState(params.get("certain") === "1");
  const [carvers, setCarvers] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [response, setResponse] = useState<{ key: string; total: number; results: Inscription[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryKey = JSON.stringify({ q, province, period, style, carver, gap, signa, category, certain, offset });
  const results = response;
  const loading = response?.key !== queryKey;

  // Keep filters in sync when the URL changes (e.g. clicking a carver link)
  const urlKey = params.toString();
  const [prevUrlKey, setPrevUrlKey] = useState(urlKey);
  if (urlKey !== prevUrlKey) {
    setPrevUrlKey(urlKey);
    setQ(params.get("q") ?? "");
    setProvince(params.get("province") ?? "");
    setPeriod(params.get("period") ?? "");
    setStyle(params.get("style") ?? "");
    setCarver(params.get("carver") ?? "");
    setGap(params.get("gap") ?? "");
    setSigna(params.get("signa") ?? "");
    setCategory(params.get("category") ?? "");
    setCertain(params.get("certain") === "1");
    setOffset(0);
  }

  useEffect(() => {
    rundata.meta().then(setMeta).catch(() => setMeta(null));
    rundata.carvers().then(cs => setCarvers(cs.filter(c => c.signed + c.attributed >= 3).map(c => c.name))).catch(() => {});
  }, []);

  useEffect(() => {
    if (signum) return;
    let cancelled = false;
    rundata.search({ q, province, period, style, carver, gap: gap || undefined, signa: signa || undefined, category: category || undefined, certain: certain || undefined, limit: PAGE, offset })
      .then(r => { if (!cancelled) { setResponse({ key: queryKey, ...r }); setError(null); } })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Sökningen misslyckades."); });
    return () => { cancelled = true; };
  }, [queryKey, q, province, period, style, carver, gap, signa, category, certain, offset, signum]);

  const select = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-slate-900 text-sm font-semibold outline-none";

  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Inskrifter</h2>
          <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
            Sök bland {meta ? meta.count.toLocaleString("sv-SE") : "alla"} inskrifter i Samnordisk runtextdatabas.
          </p>
        </div>
        {signum && (
          <button onClick={() => router.push("/inskrifter")} className="px-4 py-2 text-xs font-bold rounded-xl bg-white border border-slate-300 hover:border-slate-900">
            ← Till sökningen
          </button>
        )}
      </div>

      {signum ? (
        <InscriptionDetail key={signum} signum={signum} meta={meta} />
      ) : (
        <>
          <div className="liquid-glass-island rounded-[32px] p-6 grid grid-cols-1 md:grid-cols-6 gap-3">
            <input value={q} onChange={e => { setQ(e.target.value); setOffset(0); }}
              placeholder="Signum, plats, runtext, normalisering eller översättning"
              className={`${select} md:col-span-2`} />
            <select value={province} onChange={e => { setProvince(e.target.value); setOffset(0); }} className={select}>
              <option value="">Alla landskap</option>
              {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select value={period} onChange={e => { setPeriod(e.target.value); setOffset(0); }} className={select}>
              <option value="">Alla perioder</option>
              {Object.entries(PERIOD_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <select value={style} onChange={e => { setStyle(e.target.value); setOffset(0); }} className={select}>
              <option value="">Alla stilgrupper</option>
              {STYLES.map(st => <option key={st} value={st}>{st}</option>)}
            </select>
            <select value={carver} onChange={e => { setCarver(e.target.value); setOffset(0); }} className={select}>
              <option value="">Alla ristare</option>
              {carvers.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {(gap || signa || category) && (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="px-3 py-1.5 rounded-xl bg-slate-900 text-white font-semibold">
                Urval: {[gap ? GAP_LABEL[gap] ?? gap : "", signa ? `uppmätta stenar (${signa.split(",").filter(Boolean).length})` : "",
                  category ? `inskriftstyp: ${CATEGORY_LABEL[category] ?? category}` : ""].filter(Boolean).join(", ")}
                {carver && ` av ${carver}`}{certain && " (säker ensam ristare, runstenar)"}
                {province && ` i ${province}`}
              </span>
              <span className="text-xs text-slate-500">från Forskningsluckor</span>
              <button onClick={() => { setGap(""); setSigna(""); setCategory(""); setCertain(false); setOffset(0); router.push("/inskrifter" + (province ? `?province=${encodeURIComponent(province)}` : "")); }}
                className="px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-bold hover:border-slate-900">Ta bort urvalet</button>
            </div>
          )}
          {error && <p className="text-red-700 font-semibold">{error}</p>}
          {results && (
            <div className="liquid-glass-island rounded-[32px] p-4">
              <div className="flex justify-between items-center px-2 pb-3 text-sm text-slate-600 font-semibold">
                <span>{results.total.toLocaleString("sv-SE")} träffar{loading && " · söker..."}</span>
                <div className="flex gap-2">
                  <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}
                    className="px-3 py-1 rounded-lg bg-white border border-slate-300 disabled:opacity-40">←</button>
                  <span>{results.total ? offset + 1 : 0}–{Math.min(offset + PAGE, results.total)}</span>
                  <button disabled={offset + PAGE >= results.total} onClick={() => setOffset(offset + PAGE)}
                    className="px-3 py-1 rounded-lg bg-white border border-slate-300 disabled:opacity-40">→</button>
                </div>
              </div>
              <div className="divide-y divide-slate-900/5">
                {results.results.map(r => (
                  <Link key={r.signum} href={`/inskrifter?signum=${encodeURIComponent(r.signum)}`}
                    className="block px-3 py-3 hover:bg-white/60 rounded-xl">
                    <div className="flex justify-between gap-4">
                      <span className="font-bold text-slate-900">{r.signum} <span className="font-medium text-slate-500">{r.place}{r.parish && `, ${r.parish}`}</span></span>
                      <span className="text-xs text-slate-500 whitespace-nowrap">
                        {[r.dating, r.style, r.carvers.filter(c => c.kind === "S" || c.kind === "A").map(c => c.name).join(", ")].filter(Boolean).join(" · ")}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 font-mono truncate mt-0.5">{r.transliteration}</div>
                  </Link>
                ))}
              </div>
            </div>
          )}
          <Attribution meta={meta} />
        </>
      )}
    </div>
  );
}

export default function InscriptionsPage() {
  return (
    <Suspense fallback={null}>
      <InscriptionsContent />
    </Suspense>
  );
}
