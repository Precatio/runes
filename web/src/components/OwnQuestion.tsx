"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import { GLOSSARY } from "@/lib/glossary";
import { Tip } from "@/components/Explain";
import { db } from "@/lib/db";

// Pröva en egen fråga (POST /api/research/question, src/question.py; METHODS.md 1y): a trait A against another trait,
// a province, a time limit or a rock family, adjusted for province and time, tested in both halves of the parishes and
// without the most prolific carvers. No free text and no AI. The questions of the visit are kept in sessionStorage so
// that their p-values can be adjusted together.
interface Variable { key: string; label: string; group: string; help: string; n: number; k: number }
interface Choice { key: string; label: string; n: number }
interface Options {
  variables: Variable[]; provinces: Choice[]; families: Choice[];
  splits: { year: number; n_before: number; n_after: number }[]; n_stones: number;
}
interface Share { n: number; k: number; share: number | null; ci: [number, number] }
interface MH { or: number | null; ci: [number, number] | null; p: number | null; direction: number; strata: number }
interface Half extends MH { n: number; share_with_b: number | null; share_without_b: number | null }
interface Answer {
  a: { key: string; label: string; help: string };
  b: { kind: Kind; key: string | number; label: string; help: string; yes: string; no: string; adjusted: string };
  verdict: "håller" | "håller men inte justerat" | "beror på ristarna" | "kan vara platsen" | "bara i hela" | "ingen skillnad" | "för få" | "kopplade" | "samma";
  reason?: string; n?: number; missing?: number; with_b?: Share; without_b?: Share;
  difference?: { value: number; ci: [number, number] }; adjusted?: MH;
  halves?: { A: Half; B: Half; replicated: boolean };
  carver_check?: { carver: string; n: number; or: number | null; p: number; holds: boolean } | null;
  province_check?: { without: string; n: number; or: number | null; p: number; holds: boolean; all_hold: boolean; n_provinces: number; flips: string[] } | null;
  q?: number; n_questions?: number; corpus?: string;
  r_checks?: { available: boolean; carver?: RCheck; place?: RCheck; parish?: RCheck; carver_holds?: boolean | null; place_holds?: boolean | null; parish_holds?: boolean | null };
}
// A check in R (r/question.R): the odds ratio with the carver as a random effect (lme4) or the place as a surface (mgcv)
// shares: the share with A without and with B, other things as in the data (marginaleffects); check: DHARMa's model checks
interface RCheck { or?: number; ci?: [number, number]; p?: number; direction?: number; n?: number; groups?: number; skipped?: string; error?: string;
  shares?: { without?: number; with?: number; error?: string } | null;
  check?: { uniformity_p?: number; dispersion_p?: number; spatial_p?: number; ok?: boolean; error?: string } | null }
type Kind = "drag" | "landskap" | "tid" | "bergart";
interface Asked { a: string; b: string; verdict: Answer["verdict"]; p: number }

const KINDS: [Kind, string][] = [["landskap", "ett landskap"], ["tid", "en tidsgräns"], ["drag", "ett annat drag"], ["bergart", "en bergart"]];
const STORE = "vitki-egna-fragor";
export const pct = (x: number | null | undefined) => (x == null ? "–" : `${Math.round(x * 100)} %`);
const num = (x: number | null | undefined, d = 2) => (x == null ? "–" : x.toFixed(d).replace(".", ","));
export const pText = (p: number | null | undefined) =>
  p == null ? "–" : p < 0.0001 ? "under 0,0001" : p < 0.001 ? "under 0,001" : num(p, p < 0.01 ? 3 : 2);
// "p under 0,001" or "p = 0,03"
export const pIs = (p: number | null | undefined) => (p != null && p < 0.001 ? pText(p) : `= ${pText(p)}`);
// What was held constant, in the definite form the sentences need
const HELD: Record<string, string> = { tid: "tiden", landskap: "landskapet", "landskap och tid": "landskap och tid" };
// "fewer than 1 in N": a p-value in plain words, rounded down to a readable 1-in-N
const oneIn = (p: number) => {
  for (const n of [1_000_000, 100_000, 10_000, 1000, 100, 20]) if (p < 1 / n) return n.toLocaleString("sv-SE");
  return null;
};

export const VERDICT: Record<Answer["verdict"], { label: string; style: string }> = {
  "håller": { label: "Håller", style: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  "håller men inte justerat": { label: "Håller, men inte efter alla frågor", style: "bg-amber-50 text-amber-900 border-amber-200" },
  "beror på ristarna": { label: "Beror på ristarna", style: "bg-amber-50 text-amber-900 border-amber-200" },
  "kan vara platsen": { label: "Kan vara platsen", style: "bg-amber-50 text-amber-900 border-amber-200" },
  "bara i hela": { label: "Bara i hela korpusen", style: "bg-amber-50 text-amber-900 border-amber-200" },
  "ingen skillnad": { label: "Ingen säker skillnad", style: "bg-slate-100 text-slate-700 border-slate-300" },
  "för få": { label: "För få stenar", style: "bg-slate-100 text-slate-700 border-slate-300" },
  "kopplade": { label: "Samma sak per definition", style: "bg-slate-100 text-slate-700 border-slate-300" },
  "samma": { label: "Samma drag", style: "bg-slate-100 text-slate-700 border-slate-300" },
};

function loadAsked(): Asked[] {
  try { return JSON.parse(sessionStorage.getItem(STORE) || "[]"); } catch { return []; }
}
function saveAsked(list: Asked[]) {
  try { sessionStorage.setItem(STORE, JSON.stringify(list)); } catch { /* private window: the list lives in memory */ }
}

// A question opened from a saved finding (Forskningsluckor): /statistik?a=…&jamfor=…&varde=…#egen-fraga
function fromUrl(name: string): string | null {
  try { return new URLSearchParams(window.location.search).get(name); } catch { return null; }
}

export default function OwnQuestion() {
  const [opts, setOpts] = useState<Options | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [a, setA] = useState(() => fromUrl("a") ?? "stungna");
  const [kind, setKind] = useState<Kind>(() => (fromUrl("jamfor") as Kind | null) ?? "tid");
  const [key, setKey] = useState(() => fromUrl("varde") ?? "1075");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [busy, setBusy] = useState(false);
  const [asked, setAsked] = useState<Asked[]>(loadAsked);

  useEffect(() => {
    fetch(`${API_URL}/api/research/question/options`).then(r => r.json()).then(setOpts)
      .catch(() => setError("Kunde inte nå analysmotorn."));
  }, []);

  const groups = useMemo(() => {
    const out: Record<string, Variable[]> = {};
    for (const v of opts?.variables ?? []) (out[v.group] ??= []).push(v);
    return out;
  }, [opts]);

  const keyChoices: { key: string; label: string }[] = !opts ? [] : kind === "landskap"
    ? opts.provinces.map(p => ({ key: p.key, label: `${p.label} (${p.n})` }))
    : kind === "tid" ? opts.splits.map(s => ({ key: String(s.year), label: `före och från ${s.year} (${s.n_before} mot ${s.n_after})` }))
    : kind === "bergart" ? opts.families.map(f => ({ key: f.key, label: `${f.label} (${f.n})` }))
    : opts.variables.filter(v => v.key !== a).map(v => ({ key: v.key, label: `${v.label} (${v.k} av ${v.n})` }));

  const chooseKind = (k: Kind) => {
    setKind(k);
    setKey(k === "landskap" ? "U" : k === "tid" ? "1050" : k === "bergart" ? "granitoid" : a === "bon" ? "bro" : "bon");
  };

  const ask = async () => {
    setBusy(true); setError(null);
    try {
      const res = await fetch(`${API_URL}/api/research/question`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ a, kind, key, earlier: asked.map(x => x.p) }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
      const d: Answer = await res.json();
      setAnswer(d);
      if (d.adjusted?.p != null) {
        const list = [...asked, { a: d.a.label, b: d.b.yes, verdict: d.verdict, p: d.adjusted.p }];
        setAsked(list); saveAsked(list);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Frågan kunde inte prövas.");
    } finally {
      setBusy(false);
    }
  };
  const clear = () => { setAsked([]); saveAsked([]); };

  const field = "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
  return (
    <div className="space-y-5" id="egen-fraga">
      <div className="max-w-3xl">
        <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">Egen fråga</div>
        <h3 className="text-2xl font-bold tracking-tight text-slate-900">Pröva en egen fråga</h3>
        <p className="text-slate-600 mt-1">
          Välj ett drag och vad det ska jämföras med. Svaret räknas på samma {opts?.n_stones.toLocaleString("sv-SE") ?? ""} runstenar
          som analyserna ovan, <Tip text={GLOSSARY["Justerat för landskap och tid"]}>justerat för landskap och tid</Tip>,
          och räknas som ett mönster bara om det håller i <Tip text={GLOSSARY["Båda halvorna"]}>båda halvorna</Tip> av
          socknarna. Ingen fri text och ingen AI – bara frågor som går att räkna ärligt.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr_auto] gap-3 items-end">
        <label className="text-xs font-semibold text-slate-600 space-y-1">
          <span>Är draget</span>
          <select value={a} onChange={e => { setA(e.target.value); if (kind === "drag" && key === e.target.value) setKey(e.target.value === "bon" ? "bro" : "bon"); }} className={field}>
            {Object.entries(groups).map(([g, vs]) => (
              <optgroup key={g} label={g}>
                {vs.map(v => <option key={v.key} value={v.key}>{v.label} ({v.k} av {v.n})</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-600 space-y-1">
          <span>vanligare eller ovanligare i</span>
          <select value={kind} onChange={e => chooseKind(e.target.value as Kind)} className={field}>
            {KINDS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-600 space-y-1">
          <span>{kind === "drag" ? "nämligen stenar med" : "nämligen"}</span>
          <select value={key} onChange={e => setKey(e.target.value)} className={field}>
            {keyChoices.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
          </select>
        </label>
        <button type="button" onClick={ask} disabled={busy || !opts}
          className="px-5 py-2 rounded-xl bg-slate-900 text-white text-sm font-bold disabled:opacity-50">
          {busy ? "Räknar … (några sekunder)" : "Pröva"}
        </button>
      </div>
      {opts && <p className="text-xs text-slate-500">{opts.variables.find(v => v.key === a)?.help} Talen i listan är stenar med draget av de stenar där det går att avgöra.</p>}
      {error && <p className="text-sm font-semibold text-red-700">{error}</p>}

      {answer && <Result key={`${answer.a.key}|${answer.b.kind}|${answer.b.key}|${answer.n_questions}`} d={answer} />}

      {asked.length > 0 && (
        <div className="rounded-2xl bg-white border border-slate-200 p-4">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-bold text-slate-900 text-sm">
              <Tip text={GLOSSARY["Frågor under besöket"]}>Frågor under besöket</Tip> ({asked.length})
            </h4>
            <button type="button" onClick={clear} className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white text-xs font-bold">Börja om</button>
          </div>
          <ol className="mt-2 space-y-1 text-sm text-slate-700 list-decimal pl-5">
            {asked.map((x, i) => (
              <li key={i}><strong>{x.a}</strong> <span className="text-slate-500">{x.b}</span> – {VERDICT[x.verdict]?.label ?? x.verdict} <span className="text-xs text-slate-500">(p {pIs(x.p)})</span></li>
            ))}
          </ol>
          <p className="mt-2 text-xs text-slate-500">
            Listan finns bara i den här fliken. &quot;Börja om&quot; nollställer justeringen – gör det när du byter till en ny, i förväg bestämd fråga,
            inte för att få ett bättre q.
          </p>
        </div>
      )}
    </div>
  );
}

function Result({ d }: { d: Answer }) {
  const v = VERDICT[d.verdict];
  const w = d.with_b, wo = d.without_b, ad = d.adjusted, h = d.halves, cc = d.carver_check;
  if (!w || !wo || !ad || ad.p == null) {
    return (
      <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5 space-y-2">
        <span className={`inline-block text-xs font-bold px-2 py-1 rounded-lg border ${v.style}`}>{v.label}</span>
        <p className="text-slate-800">{d.reason}</p>
        {w && wo && <p className="text-sm text-slate-600"><strong>{d.a.label}</strong>: {pct(w.share)} av {w.n} stenar <strong>{d.b.yes}</strong>, {pct(wo.share)} av {wo.n} <strong>{d.b.no}</strong>.</p>}
      </div>
    );
  }
  const more = ad.direction > 0;
  const odds = ad.or == null ? null : more ? ad.or : 1 / ad.or;
  const once = oneIn(ad.p);
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-4">
        <div className="rounded-2xl bg-slate-900 text-white p-5 flex flex-col justify-center">
          <div className="text-4xl font-bold tracking-tight"><span className="whitespace-nowrap">{pct(w.share)}</span> <span className="text-white/60 text-2xl">mot</span> <span className="whitespace-nowrap">{pct(wo.share)}</span></div>
          <div className="text-sm text-white/80 mt-1 leading-snug">
            av stenarna <strong>{d.b.yes}</strong> mot <strong>{d.b.no}</strong> har <strong>{d.a.label.toLowerCase()}</strong>
          </div>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-5 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Svaret i korthet</div>
            <span className={`text-xs font-bold px-2 py-0.5 rounded-lg border ${v.style}`}>{v.label}</span>
          </div>
          <p className="text-slate-800 leading-relaxed">
            {d.verdict === "håller" && <>Ja. <strong>{d.a.label}</strong> är {more ? "vanligare" : "ovanligare"} <strong>{d.b.yes}</strong> än <strong>{d.b.no}</strong>, också när {HELD[d.b.adjusted] ?? d.b.adjusted} räknats bort, och mönstret håller i båda halvorna av socknarna.</>}
            {d.verdict === "håller men inte justerat" && <>Mönstret håller i båda halvorna av socknarna, men inte när de {d.n_questions} frågor du prövat under besöket räknas in. Behandla det som en ny hypotes att pröva på ett annat underlag.</>}
            {d.verdict === "beror på ristarna" && <>Mönstret håller i båda halvorna av socknarna, men inte när ristaren räknas som slumpeffekt. Det bärs av några ristares vanor snarare än av något som gäller stenarna i stort.</>}
            {d.verdict === "kan vara platsen" && <>Mönstret håller i båda halvorna av socknarna, men försvinner när stenarnas läge får forma en egen yta på kartan. Draget och jämförelsen hör hemma i samma trakter, och det kan vara trakten som gör skillnaden.</>}
            {d.verdict === "bara i hela" && <>Skillnaden syns i hela korpusen men inte i båda halvorna av socknarna. Den kan bero på några få socknar eller ristare och räknas inte som ett mönster.</>}
            {d.verdict === "ingen skillnad" && <>Ingen säker skillnad: när {HELD[d.b.adjusted] ?? d.b.adjusted} räknats bort skiljer sig andelarna inte mer än slumpen väl kan ge. Det betyder inte att draget är lika vanligt – bara att stenarna inte visar en skillnad.</>}
          </p>
          <p className="text-sm text-slate-600">
            Skillnaden är {num(Math.abs(d.difference!.value) * 100, 0)} procentenheter (95 %: {num(d.difference!.ci[0] * 100, 0)} till {num(d.difference!.ci[1] * 100, 0)}),
            räknat på {d.n} stenar{d.missing ? `; ${d.missing} stenar där draget eller jämförelsen inte går att avgöra är inte med` : ""}.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-2">Hur säkert är det?</h4>
          <ul className="space-y-2 text-sm text-slate-700 list-disc pl-5">
            <li>
              <Tip text={GLOSSARY["Justerat för landskap och tid"]}>Justerat för {d.b.adjusted}</Tip>:{" "}
              {odds == null ? "oddskvoten går inte att räkna (draget saknas helt på ena sidan i varje skikt)" : (
                <>oddsen för draget är {num(odds, odds >= 10 ? 0 : 1)} gånger så {more ? "höga" : "låga"} <strong>{d.b.yes}</strong> (<Tip text={GLOSSARY["Oddskvot"]}>oddskvot</Tip> {num(ad.or)}, 95 %: {num(ad.ci?.[0])}–{num(ad.ci?.[1])}; {ad.strata} skikt).</>
              )}
            </li>
            <li>
              <Tip text={GLOSSARY["p"]}>p</Tip> {pIs(ad.p)}:{" "}
              {once ? <>om draget inte hängde ihop med jämförelsen skulle en så tydlig skillnad uppstå av en slump i färre än 1 fall på {once}.</>
                : <>en så stor skillnad uppstår lätt av en slump.</>}
            </li>
            {h && (
              <li>
                <Tip text={GLOSSARY["Båda halvorna"]}>Halvorna</Tip>: i den ena halvan av socknarna {pct(h.A.share_with_b)} mot {pct(h.A.share_without_b)} (p {pIs(h.A.p)}),
                i den andra {pct(h.B.share_with_b)} mot {pct(h.B.share_without_b)} (p {pIs(h.B.p)}) – {h.replicated ? "samma riktning och under 0,05 i båda." : "inte under 0,05 med samma riktning i båda."}
              </li>
            )}
            {cc && (
              <li>
                <Tip text={GLOSSARY["Ristarprovet"]}>Ristarprovet</Tip>: utan <strong>{cc.carver}</strong> ({cc.n} stenar i underlaget), den ristare som påverkar mest,
                {cc.holds ? " håller skillnaden fortfarande" : " håller skillnaden inte"} (p {pIs(cc.p)}).
              </li>
            )}
            {d.province_check && (
              <li>
                <Tip text="Frågan räknas om utan ett landskap i taget (landskap med minst 30 stenar). Riktningen ska hålla utan vart och ett; p under 0,05 krävs bara där minst två tredjedelar av stenarna är kvar – samma regel som robusthetstrappan i Statistik (R).">Utan ett landskap i taget</Tip>:{" "}
                sämst utan <strong>{d.province_check.without}</strong> ({d.province_check.n} stenar kvar): oddskvot {num(d.province_check.or)}, p {pIs(d.province_check.p)} –{" "}
                {d.province_check.all_hold ? "håller utan vart och ett av landskapen." : <strong>håller inte utan alla landskap.</strong>}
                {d.province_check.flips.length > 0 && <> Riktningen vänder utan {d.province_check.flips.join(", ")}.</>}
                {d.province_check.or != null && d.adjusted?.or != null && Math.abs(Math.log(d.province_check.or)) < Math.abs(Math.log(d.adjusted.or)) / 3 && (
                  <span className="block text-amber-700">Utan {d.province_check.without} är sambandet nästan borta: det bärs till stor del av ett landskap.</span>
                )}
              </li>
            )}
            <RCheckLine label="Ristaren som slumpeffekt" tip={GLOSSARY["Ristaren som slumpeffekt"]} c={d.r_checks?.carver}
              holds={d.r_checks?.carver_holds} available={d.r_checks?.available} more={more} />
            <RCheckLine label="Socknen som slumpeffekt" tip="Samma modell med socknen som slumpeffekt i stället för ristaren: håller sambandet när socknarna får skilja sig sinsemellan, eller är det några socknars egenhet?" c={d.r_checks?.parish}
              holds={d.r_checks?.parish_holds} available={d.r_checks?.available} more={more} />
            <RCheckLine label="Platsen som yta" tip={GLOSSARY["Platsen som yta"]} c={d.r_checks?.place}
              holds={d.r_checks?.place_holds} available={d.r_checks?.available} more={more} />
            {d.q != null && d.n_questions != null && d.n_questions > 1 && (
              <li>
                <Tip text={GLOSSARY["Frågor under besöket"]}>Frågor under besöket</Tip>: det här är fråga {d.n_questions}; justerat för dem är q {pIs(d.q)}.
              </li>
            )}
          </ul>
        </div>
        <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-2">Det här säger resultatet inte</h4>
          <ul className="space-y-2 text-sm text-slate-600 list-disc pl-5">
            <li>Varför. Ett samband mellan två drag säger inte vilket som orsakade vilket, eller om något tredje – en verkstad, en beställarkrets – ligger bakom båda.</li>
            {d.b.kind !== "tid" && <li>Något om tiden utöver det som stilgruppen säger. Hälften av stenarna saknar säker stilgrupp och jämförs bara inom sitt landskap.</li>}
            <li>Något om andra föremål än runstenar, eller om stenar Rundata inte har.</li>
            <li>Något om det draget missar: dragen läses ur Rundatas translitterering och normalisering, och en skadad text kan sakna ett drag som fanns.</li>
            <li>Att frågan är ny. Pröva den mot litteraturen; ett resultat som ska användas i en text behöver en <Link href="/docs" className="text-[#b7410e] hover:underline">analysplan</Link> som skrivs innan frågan ställs.</li>
          </ul>
        </div>
      </div>
      <SaveFinding d={d} />
      <p className="text-xs text-slate-500">
        Mantel–Haenszel över landskap och tidsskikt, halvprovet och ristarprovet beskrivs i metoddokumentationen, avsnitt 1y.
        Draget och jämförelsen kan också visas på <Link href="/karta" className="text-[#b7410e] hover:underline">kartan</Link>.
      </p>
    </div>
  );
}

// One of the two checks in R, in plain words: the odds ratio, the interval, p, and whether it holds
function RCheckLine({ label, tip, c, holds, available, more }: { label: string; tip?: string; c?: RCheck; holds?: boolean | null; available?: boolean; more: boolean }) {
  if (available === false) {
    return <li><Tip text={tip}>{label}</Tip>: kunde inte räknas (R saknas på datorn eller modellen gick inte att skatta).</li>;
  }
  if (!c) return null;
  if (c.skipped) return <li><Tip text={tip}>{label}</Tip>: räknas inte för landskap, där platsen är själva jämförelsen.</li>;
  if (c.error || c.or == null) return <li><Tip text={tip}>{label}</Tip>: modellen gick inte att skatta för den här frågan.</li>;
  return (
    <li>
      <Tip text={tip}>{label}</Tip>: oddskvot {num(c.or)} (95 %: {num(c.ci?.[0])}–{num(c.ci?.[1])}), p {pIs(c.p)} –{" "}
      {holds ? <>samma riktning, {more ? "vanligare" : "ovanligare"}, och under 0,05: håller.</> : <strong>håller inte.</strong>}
      {c.shares?.without != null && c.shares?.with != null && (
        <span className="block text-slate-600">{`Med övrigt lika: ${pct(c.shares.with)} med B mot ${pct(c.shares.without)} utan.`}</span>
      )}
      {c.check && !c.check.error && (
        <span className={`block ${c.check.ok ? "text-slate-500" : "text-amber-700"}`}>
          {c.check.ok ? "Modellkontrollen (simulerade residualer) visar inget som talar emot modellen."
            : `Modellkontrollen varnar: ${[
              (c.check.uniformity_p ?? 1) < 0.05 && "residualerna är inte jämnt fördelade",
              (c.check.dispersion_p ?? 1) < 0.05 && "spridningen är större eller mindre än modellen väntar",
              (c.check.spatial_p ?? 1) < 0.05 && "det finns ett rumsligt mönster kvar",
            ].filter(Boolean).join(", ")}. Läs resultatet med försiktighet.`}
        </span>
      )}
    </li>
  );
}

// Spara som fynd: the answer as it is now, with how many questions came before it, into Forskningsluckor → Våra resultat
function SaveFinding({ d }: { d: Answer }) {
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const ad = d.adjusted!, w = d.with_b!, wo = d.without_b!;
  const save = async () => {
    setBusy(true);
    await db.saveQuestion({
      a: { key: d.a.key, label: d.a.label },
      b: { kind: d.b.kind, key: String(d.b.key), label: d.b.label, yes: d.b.yes, no: d.b.no, adjusted: d.b.adjusted },
      verdict: d.verdict, n: d.n ?? 0,
      withB: { n: w.n, k: w.k, share: w.share ?? 0 }, withoutB: { n: wo.n, k: wo.k, share: wo.share ?? 0 },
      or: ad.or, orCi: ad.ci, p: ad.p ?? 1,
      halves: { pA: d.halves?.A.p ?? null, pB: d.halves?.B.p ?? null, replicated: !!d.halves?.replicated },
      carver: d.carver_check ? { name: d.carver_check.carver, n: d.carver_check.n, p: d.carver_check.p, holds: d.carver_check.holds } : null,
      q: d.q ?? ad.p ?? 1, nQuestions: d.n_questions ?? 1, corpus: d.corpus ?? "", note: note.trim(),
    });
    setSaved(true); setBusy(false);
  };
  if (saved) {
    return (
      <p className="rounded-2xl bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-900">
        Sparad. Den finns under <Link href="/luckor" className="font-semibold underline">Forskningsluckor → Våra resultat</Link>, med siffrorna som de är nu.
      </p>
    );
  }
  return (
    <div className="rounded-2xl bg-white border border-slate-200 p-4 flex flex-col sm:flex-row gap-3 sm:items-end">
      <label className="flex-1 text-xs font-semibold text-slate-600 space-y-1">
        <span>Anteckning (valfri): vilken hypotes prövade du, och varför?</span>
        <input value={note} onChange={e => setNote(e.target.value)} maxLength={500}
          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
      </label>
      <button type="button" onClick={save} disabled={busy}
        className="px-4 py-2 rounded-xl border border-slate-900 bg-white text-sm font-bold text-slate-900 hover:bg-slate-50 disabled:opacity-50">
        {busy ? "Sparar …" : "Spara som fynd"}
      </button>
    </div>
  );
}
