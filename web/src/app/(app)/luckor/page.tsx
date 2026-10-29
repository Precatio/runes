"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Answer, InfoTip, PageIntro, QuestionCards, type AnswerProps } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import { API_URL } from "@/lib/api";
import { corpus } from "@/lib/corpus";
import { useAuth } from "@/components/AuthContext";
import { DocsNote } from "@/components/KnownLimitations";
import type { Findings, Gaps, Hypothesis, Tab, TextGaps } from "./_delar/typer";
import { gapHref, pct, signaHref } from "./_delar/gemensamt";
import { BriefTable, Freshness, HypothesisTable, PrioritiesPanel, TextGapsPanel } from "./_delar/ovriga";
import { FindingsPanel } from "./_delar/fynd";
import { CategoryPanel, ProvinceTable, SizePanel } from "./_delar/tackning";

export default function GapsPage() {
  // Wait until Firebase has restored the session, so the heavy requests run once with the settled user's corpus
  const { user, loading: authLoading } = useAuth();
  const [data, setData] = useState<Gaps | null>(null);
  const [found, setFound] = useState<Findings | null>(null);
  const [textGaps, setTextGaps] = useState<TextGaps | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/research/gaps/textmodel`).then(r => (r.ok ? r.json() : null)).then(d => setTextGaps(d)).catch(() => setTextGaps(null));
  }, []);
  const [measuredSigna, setMeasuredSigna] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("findings");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    (async () => {
      let entries: Awaited<ReturnType<typeof corpus.list>> = [];
      if (user) {
        try { entries = await corpus.list(); } catch { /* corpus optional */ }
      }
      const post = (path: string, body: unknown) => fetch(`${API_URL}${path}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      }).then(async res => {
        if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
        return res.json();
      });
      try {
        const [gaps, findings] = await Promise.all([
          post("/api/research/gaps", { measured_signa: [...new Set(entries.map(e => e.signum))] }),
          post("/api/research/findings", {
            corpus: entries.map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means })),
          }),
        ]);
        if (!cancelled) { setData(gaps); setFound(findings); setMeasuredSigna([...new Set(entries.map(e => e.signum))]); }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Kunde inte hämta översikten.");
      }
    })();
    return () => { cancelled = true; };
  }, [user, authLoading, reload]);

  if (error) return <div className="max-w-3xl mx-auto p-8 text-red-700 font-semibold">{error}</div>;
  if (!data || !found) return <div className="max-w-3xl mx-auto p-8 text-slate-500">Beräknar översikten …</div>;

  const t = data.coverage.totals;
  const nSig = (rows: Hypothesis[]) => rows.filter(h => h.p_adjusted != null && h.p_adjusted < 0.05).length;
  const cards: { key: Tab; topic: string; question: string; note: string }[] = [
    { key: "findings", topic: "Våra resultat", question: "Vad säger appens analyser jämfört med forskningen?", note: `${found.findings.length} fynd` },
    { key: "coverage", topic: "Luckor", question: "Var saknas uppgifter om runstenarna?", note: `${t.total - t.carver} stenar utan ristare` },
    { key: "hypotheses", topic: "Nya ristare", question: "Vilka stenar utan ristare liknar en känd ristare i stavningen?", note: `${data.hypotheses.new.length} stenar` },
    { key: "reconsider", topic: "Ompröva", question: "Vilka attribueringar kan behöva omprövas?", note: `${data.hypotheses.reconsider.length} stenar` },
    { key: "priorities", topic: "3D-mätning", question: "Vilka stenar vore mest värda att mäta i 3D?", note: `${data.measurement_priorities.length} ristare` },
    { key: "categories", topic: "Syfte", question: "Skiljer sig ristarna i vad inskrifterna handlar om?", note: "9 kategorier" },
    { key: "size", topic: "Storlek", question: "Restes större stenar för större syften?", note: "höjd mot syfte" },
    { key: "uninterpreted", topic: "Tolkning", question: "Vilka inskrifter är osäkert tolkade?", note: `${data.open_questions.uninterpreted.count} inskrifter` },
    { key: "style", topic: "Stilgrupp", question: "Vilka stenar har osäker stilgrupp?", note: `${data.open_questions.uncertain_style.count} stenar` },
    { key: "textgaps", topic: "Luckor i texten", question: "Vilka förlorade runor kan sannolikhetsmodellen fylla i?", note: textGaps?.counts ? (textGaps.counts.runsten ? `${textGaps.counts.runsten.sure ?? 0} luckor ≥ 80 % på runstenar` : `${textGaps.counts.candidates} luckor`) : "beräknas" },
  ];
  const c = found.summary.counts;
  const sigFound = found.findings.filter(f => f.significance?.significant).length;
  const provinces = data.coverage.per_province.filter(r => r.total >= 30);
  const lowest = provinces.length ? provinces.reduce((m, r) => (r.carver / r.total < m.carver / m.total ? r : m)) : null;
  const ev = data.hypotheses.evaluation;
  const answers: Partial<Record<Tab, AnswerProps>> = {
    findings: {
      topic: "Våra resultat", question: "Vad säger appens analyser jämfört med forskningen?",
      why: "Appens metoder – stavning, den statistiska modellen, seriationen, skrivmiljöerna och huggteknik – ställs mot Rundata, som här står för den publicerade forskningen.",
      headline: { value: String(found.summary.likely_new), label: "fynd som sannolikt är ny kunskap enligt uppskattningen (en släktlänk räknas en gång)" },
      answer: <>{c.stämmer} av appens resultat stämmer med Rundata, {c.nytt} säger något som Rundata saknar och {c.motsäger} pekar på något annat. {sigFound} av fynden är <strong>statistiskt signifikanta</strong>.</>,
      interpretation: [
        "Bekräftelserna är ett test av metoderna: att de ofta kommer fram till samma ristare som forskningen talar för att de fungerar.",
        "De nya förslagen är hypoteser. Klicka på ett fynd för en tolkning som väger samman alla belägg och visar vad som talar emot.",
        "Fynd som redan finns i Runor 2020 eller Wikidata är inte ny kunskap, men de stärker förtroendet för metoden.",
      ],
      notSaying: [
        "Rundata (2018) är inte hela forskningen – ett 'nytt' fynd kan finnas i litteratur som appen inte har.",
        "Uppskattningen (belägg × nyhet × relevans) är en tumregel för att prioritera, inte en sannolikhet.",
        "Statistiskt signifikant betyder att en så stor likhet sällan uppstår utan ett verkligt samband (justerat p under 0,05) – inte att attribueringen är rätt.",
      ],
    },
    coverage: {
      topic: "Luckor", question: "Var saknas uppgifter om runstenarna?",
      why: "Där uppgifter saknas kan nya analyser och mätningar göra mest nytta.",
      headline: { value: `${pct(t.total - t.carver, t.total)} %`, label: "av runstenarna saknar ristare i Rundata" },
      answer: <>Av {t.total} svenska vikingatida runstenar saknar {t.total - t.carver} ristare och {t.total - t.style} säker stilgrupp; {t.dated} är daterade med årtal och {t.measured} är uppmätta i 3D.{lowest && <> Lägst andel med ristare bland landskap med minst 30 stenar har {lowest.name} ({pct(lowest.carver, lowest.total)} %).</>}</>,
      interpretation: [
        "Landskap med få attribueringar är där nya ristarförslag och skrivmiljöerna gör mest nytta.",
        "Uppland och Södermanland har flest attribueringar, främst genom Axelsons arbete (1993); i andra landskap kan attribueringar finnas i litteraturen utan att stå i Rundata.",
      ],
      notSaying: ["Att en uppgift saknas i Rundata betyder inte att den saknas i all forskning."],
    },
    hypotheses: {
      topic: "Nya ristare", question: "Vilka stenar utan ristare liknar en känd ristare i stavningen?",
      why: "Ristare hade egna stavningsvanor. En sten utan ristare som stavar som en känd ristare kan vara hans eller hennes.",
      headline: { value: String(data.hypotheses.new.length), label: `stenar utan ristare med tydlig stavningslikhet, varav ${nSig(data.hypotheses.new)} statistiskt signifikanta` },
      answer: <>Ortografin pekar ut en trolig ristare för {data.hypotheses.new.length} stenar utan ristare i Rundata; {nSig(data.hypotheses.new)} av likheterna är statistiskt signifikanta (justerat p under 0,05). Prövad på stenar med känd ristare hamnar rätt ristare först i {Math.round(ev.top1_accuracy * 100)} % av fallen, mot {Math.round(ev.chance_top1 * 100)} % med slumpen.</>,
      interpretation: [
        "Signifikanta likheter inom ristarens område är de bästa kandidaterna att pröva vidare.",
        "Väger tyngre när flera oberoende metoder – t.ex. den statistiska modellen eller huggtekniken – pekar mot samma ristare.",
      ],
      notSaying: [
        "Stavning är bara ett av flera drag; ornamentik, runformer och huggteknik vägs inte in här.",
        "Produktiva ristare som Öpir och Fot drar till sig förslag.",
      ],
    },
    reconsider: {
      topic: "Ompröva", question: "Vilka attribueringar kan behöva omprövas?",
      why: "En attribuerad sten som stavar som en annan ristare kan vara felbedömd – eller visa samarbete.",
      headline: { value: String(data.hypotheses.reconsider.length), label: `attribuerade stenar där stavningen pekar mot någon annan, varav ${nSig(data.hypotheses.reconsider)} signifikanta` },
      answer: <>För {data.hypotheses.reconsider.length} stenar som Rundata attribuerar pekar ortografin mot en annan ristare; {nSig(data.hypotheses.reconsider)} av likheterna är statistiskt signifikanta.</>,
      interpretation: [
        "Det kan vara en felaktig attribuering, men också samarbete, en verkstad eller en ristare som skrev olika vid olika tillfällen.",
        "Signerade stenar ingår inte – där är det metoden som har fel, inte ristaren.",
      ],
      notSaying: ["En stavningslikhet räcker inte för att underkänna en attribuering som bygger på ornamentik och runformer."],
    },
    priorities: {
      topic: "3D-mätning", question: "Vilka stenar vore mest värda att mäta i 3D?",
      why: "Huggtekniken är det enda belägget som inte bygger på tidigare forskares bedömningar, men den kräver flera uppmätta stenar per ristare.",
      answer: <>Listan visar för varje ristare hur många stenar som är uppmätta och vilka som skulle göra mest nytta att mäta – signerade stenar först, eftersom ristaren där är känd.</>,
      interpretation: ["Mät helst flera stenar av samma ristare på samma bergart, eftersom bergarten påverkar huggspåren."],
      notSaying: ["Huggspårsmåtten är ännu inte validerade som spår av ristarens hand."],
    },
    uninterpreted: {
      topic: "Tolkning", question: "Vilka inskrifter är osäkert tolkade?",
      why: "Osäkra läsningar är där nya bilder, RTI och 3D kan ge mest.",
      headline: { value: String(data.open_questions.uninterpreted.count), label: "inskrifter med osäker läsning eller tolkning i Rundata" },
      answer: <>Rundata markerar {data.open_questions.uninterpreted.count} inskrifter som osäkert lästa eller tolkade. Listan visar dem med plats, stil och datering.</>,
      interpretation: ["En ny läsning med strykljus (RTI) eller en 3D-relief kan avgöra oklara runor."],
    },
    style: {
      topic: "Stilgrupp", question: "Vilka stenar har osäker stilgrupp?",
      why: "Stilgruppen är grunden för dateringen; en osäker stilgrupp ger en osäker datering.",
      headline: { value: String(data.open_questions.uncertain_style.count), label: "stenar med osäker stilgrupp i Rundata" },
      answer: <>{data.open_questions.uncertain_style.count} stenar har en osäker stilgrupp. Seriationen i R kan ge ett förslag att pröva mot ornamentiken; appen bedömer inte stilgrupp ur foto.</>,
      notSaying: ["Seriationen bygger på språk och innehåll, inte på ornamentik, och daterar bara relativt."],
    },
  };

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <PageIntro title="Forskningsluckor"
        lead={<>Två saker på en sida: <strong>var kunskapen om runstenarna har luckor</strong> – stenar utan ristare, stilgrupp, datering
          eller mätningar – och <strong>vad appens egna analyser säger jämfört med forskningen</strong>. Varje fråga börjar med svaret i
          korthet och ett förslag till tolkning. Allt är förslag för forskare att pröva, inte färdiga slutsatser.</>}
        howTo={[
          <>Välj en fråga i korten. Under svaret finns tabellerna; klicka på en kolumnrubrik för att sortera.</>,
          <>Märket <strong>✓ Signifikant</strong> betyder att p eller q är under 0,05: ett så tydligt resultat vore ovanligt om det inte fanns något verkligt samband. Det säger inte hur stort eller viktigt resultatet är. Håll muspekaren över ⓘ och prickade ord för förklaringar.</>,
          <>Klicka på ett fynd för en tolkning som väger samman alla belägg och visar vad som talar emot.</>,
          <>Siffrorna i rutorna överst är länkar till inskrifterna bakom dem.</>,
        ]} />

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          ["Runstenar", `${t.total}`, "", gapHref("runestone")],
          ["Med ristare", `${pct(t.carver, t.total)} %`, `${t.total - t.carver} saknar`, gapHref("no_carver")],
          ["Säker stilgrupp", `${pct(t.style, t.total)} %`, `${t.total - t.style} saknar`, gapHref("no_style")],
          ["Datering", `${t.dated}`, `${pct(t.dated, t.total)} % daterade med årtal`, gapHref("dated")],
          ["Uppmätta", `${t.measured}`, user ? "i 3D-korpusen" : "logga in för att se", measuredSigna.length ? signaHref(measuredSigna) : ""],
        ].map(([label, value, sub, href]) => {
          const body = (
            <>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}<InfoTip text={GLOSSARY[label]} /></div>
              <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
              {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
            </>
          );
          return href
            ? <Link key={label} href={href} className="liquid-glass-island rounded-[24px] p-5 hover:ring-2 hover:ring-slate-900/20 transition">{body}</Link>
            : <div key={label} className="liquid-glass-island rounded-[24px] p-5">{body}</div>;
        })}
      </div>

      <Freshness textGaps={textGaps} />
      <QuestionCards items={cards} active={tab} onSelect={k => setTab(k as Tab)} />

      <div className="liquid-glass-island rounded-[32px] p-5 md:p-7 space-y-6">
        {answers[tab] && <Answer {...answers[tab]!} />}
        {tab === "findings" && <FindingsPanel data={found} loggedIn={!!user} onRefresh={() => setReload(r => r + 1)} />}
        {tab === "coverage" && <ProvinceTable rows={data.coverage.per_province} measuredSigna={measuredSigna} />}
        {tab === "categories" && <CategoryPanel />}
        {tab === "size" && <SizePanel />}
        {(tab === "hypotheses" || tab === "reconsider") && (
          <HypothesisTable key={tab} reconsider={tab === "reconsider"} ev={data.hypotheses.evaluation}
            rows={tab === "hypotheses" ? data.hypotheses.new : data.hypotheses.reconsider} />
        )}
        {tab === "priorities" && <PrioritiesPanel rows={data.measurement_priorities} />}
        {tab === "textgaps" && <TextGapsPanel data={textGaps} />}
        {(tab === "uninterpreted" || tab === "style") && (
          <BriefTable key={tab} uninterpreted={tab === "uninterpreted"}
            rows={(tab === "uninterpreted" ? data.open_questions.uninterpreted : data.open_questions.uncertain_style).items} />
        )}
      </div>
      <DocsNote anchor="14-forskningsluckor">Varifrån uppgifterna kommer, hur bedömningarna räknas och vilka reservationer som gäller står i avsnitt 14.</DocsNote>
      <p className="text-[11px] text-slate-500">{data.attribution}</p>
    </div>
  );
}
