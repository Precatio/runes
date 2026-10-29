import { DocsNote } from "@/components/KnownLimitations";
import { Details, LEVEL_STYLE, Md, SigBadge, Tip } from "@/components/Explain";
import { PatternBadges, PatternBody, type Pattern, HideWrittenToggle } from "@/components/PatternCard";
import { GLOSSARY } from "@/lib/glossary";
import Link from "next/link";
import ExportTable from "@/components/ExportTable";
import { useWrittenFilter } from "@/lib/patternArticles";
import type { Corpus, Tab } from "./typer";
import { PATTERN_TOPICS, TOPIC, Th, patternsFor } from "./gemensamt";

const STATUS_STYLE: Record<string, string> = {
  "bekräftar": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "mönster att pröva": "bg-amber-50 text-amber-900 border-amber-200",
  "begränsning": "bg-slate-100 text-slate-700 border-slate-300", "svagt": "bg-slate-100 text-slate-700 border-slate-300",
  "svag effekt": "bg-slate-100 text-slate-700 border-slate-300", "indikation": "bg-slate-100 text-slate-700 border-slate-300",
};

export const sectionOf = (data: Corpus, key: Tab) => (data.sections ?? []).find(x => x.key === key);

// The statistically significant results, so that they stand out from the descriptive ones
function SignificantBox({ patterns, onOpen, robust }: { patterns: Pattern[]; onOpen: (t: Tab) => void; robust?: Corpus["robustness"] }) {
  const tested = patterns.filter(p => p.significance && p.significance.significant !== null);
  const sig = tested.filter(p => p.significance?.significant);
  const untested = patterns.filter(p => p.significance && p.significance.significant === null);
  if (!patterns.some(p => p.significance)) return null;
  const sectionOfTopic = (topic: string) => (Object.entries(PATTERN_TOPICS).find(([, ts]) => ts.includes(topic))?.[0] ?? "overview") as Tab;
  const topics = Array.from(new Set(sig.map(p => p.topic)));
  return (
    <section className="rounded-3xl border border-emerald-200 bg-emerald-50/60 p-6 md:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">Statistiskt signifikant</div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-900">Upptäckter som klarar signifikanstestet</h3>
        </div>
        <div className="text-sm text-slate-700"><span className="text-3xl font-bold text-emerald-800">{sig.length}</span> av {tested.length} prövade resultat</div>
      </div>
      <p className="text-sm text-slate-700 mt-2 max-w-4xl">
        Ett resultat är <strong>statistiskt signifikant</strong> när p-värdet – eller q, som tar hänsyn till att många saker prövats
        samtidigt – är under 0,05: ett så tydligt mönster vore ovanligt om det inte fanns något verkligt samband. Det är inte sannolikheten att mönstret är verkligt, och det säger inte att tolkningen av det är rätt.
        {untested.length > 0 && ` ${untested.length} resultat är inte prövade med signifikanstest (t.ex. attribueringsmodellen, som i stället prövats med korsvalidering).`}
      </p>
      {robust?.available ? (
        <p className="text-sm text-slate-700 mt-2 max-w-4xl">
          <strong>Alla mönster samtidigt:</strong> med en gemensam justering (Benjamini–Hochberg) över alla {robust.n_fdr} mönster
          med ett p-värde klarar {robust.fdr_ok} q under 0,05. {robust.n_ladder} mönster går att räkna om sten för sten i
          robusthetstrappan – samma kontroller för alla: ristaren och socknen som slumpeffekter, platsen som yta, båda halvorna,
          utan ett landskap i taget och utan flyttade stenar – och {robust.all_rungs} av dem håller i varje steg.
          {" "}{robust.confirmed} mönster är bekräftade (båda halvorna och den gemensamma justeringen); bara de märks <em>Nytt</em> när de dyker upp.
        </p>
      ) : robust && (
        <p className="text-xs text-slate-500 mt-2">Robusthetstrappan räknas i bakgrunden och visas här när den är klar.</p>
      )}
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {topics.map(topic => (
          <div key={topic} className="rounded-2xl bg-white border border-emerald-100 p-4">
            <button type="button" onClick={() => onOpen(sectionOfTopic(topic))} className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e] hover:underline">
              {topic} →
            </button>
            <ul className="mt-2 space-y-2 text-sm">
              {sig.filter(p => p.topic === topic).map((p, i) => (
                <li key={i} className="flex flex-col gap-1">
                  <div className="flex flex-wrap gap-1.5"><SigBadge sig={p.significance} /><PatternBadges pt={p} /></div>
                  <span className="text-slate-700">{p.text}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Overview({ data, onOpen }: { data: Corpus; onOpen: (t: Tab) => void }) {
  const s = data.findings_summary;
  // The patterns we have already written an article or draft about can be hidden with one click (PatternCard.tsx)
  const { shown: patterns, written, hide } = useWrittenFilter(data.patterns);
  const top = data.findings.filter(f => f.verdict !== "stämmer").slice(0, 25);
  const groups: [string, string, string[]][] = [
    ["Stämmer med det forskningen redan utgår från", "Ett tecken på att metoderna fungerar.", ["bekräftar"]],
    ["Nya mönster att pröva", "Mönster som appen inte kan förklara med det den känner till och som håller i båda halvorna av korpusen – kanske ny kunskap, kanske redan beskrivet i litteratur som appen inte har.", ["mönster att pröva"]],
    ["Indikationer", "Mönster som syns i hela korpusen men inte håller i alla kontroller eller i båda halvorna – idéer att pröva, med förbehåll.", ["indikation"]],
    ["Begränsningar", "Cirkulära jämförelser och resultat som visar gränserna för data och metod.", ["begränsning", "svagt", "svag effekt"]],
  ];
  return (
    <div className="space-y-8">
      {data.overview && (
        <section className="rounded-3xl bg-white border border-slate-200 p-6 md:p-8">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">Helhetsbilden</div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-900 mb-4">Vad statistiken säger sammantaget</h3>
          <div className="space-y-4 text-slate-700 leading-relaxed max-w-4xl">
            {data.overview.paragraphs.map((t, i) => <p key={i}><Md text={t} /></p>)}
          </div>
        </section>
      )}

      {written > 0 && (
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <HideWrittenToggle written={written} />
          <span>{hide ? `${written} mönster som vi redan skrivit artiklar eller utkast om är dolda.` : "Mönster som vi redan skrivit om är märkta Artikel ✓ eller Utkast skrivet."}</span>
        </div>
      )}

      <SignificantBox patterns={patterns} onOpen={onOpen} robust={data.robustness} />

      <section>
        <h3 className="text-xl font-bold text-slate-900 mb-1">Frågorna i korthet</h3>
        <p className="text-sm text-slate-600 mb-4">Svaret, nyckeltalet och den viktigaste tolkningen för varje fråga. Klicka för att läsa mer.</p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {(data.sections ?? []).map(x => (
            <button key={x.key} type="button" onClick={() => onOpen(x.key)}
              className="text-left rounded-2xl bg-white border border-slate-200 p-5 hover:border-[#b7410e]/40 hover:shadow-md transition-shadow flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">{TOPIC[x.key]}</div>
                  <div className="font-bold text-slate-900 leading-snug">{x.question}</div>
                </div>
                <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${LEVEL_STYLE[x.confidence]}`}>{x.confidence}</span>
              </div>
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold tracking-tight text-slate-900">{x.headline.value}</span>
                <span className="text-xs text-slate-500 leading-snug">{x.headline.label}</span>
              </div>
              <p className="text-sm text-slate-800">{x.short}</p>
              {x.interpretation[0] && <p className="text-sm text-slate-600"><span className="font-semibold text-slate-700">Tolkning: </span>{x.interpretation[0]}</p>}
              {(() => {
                const ts = patternsFor(data.patterns, x.key), k = ts.filter(t => t.significance?.significant).length;
                return ts.length > 0 ? (
                  <span className={`text-xs font-semibold ${k ? "text-emerald-800" : "text-slate-500"}`}>
                    {k ? `✓ ${k} av ${ts.length} resultat statistiskt signifikanta` : `Inget av ${ts.length} resultat statistiskt signifikant`}
                  </span>
                ) : null;
              })()}
              <span className="text-xs font-bold text-[#b7410e] mt-auto">Läs mer →</span>
            </button>
          ))}
        </div>
      </section>

      {data.overview && data.overview.next_steps.length > 0 && (
        <section className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900 mb-2">Förslag på nästa steg för forskningen</h3>
          <ol className="list-decimal pl-5 space-y-1.5 text-sm text-slate-700">
            {data.overview.next_steps.map((t, i) => <li key={i}>{t}</li>)}
          </ol>
        </section>
      )}

      <section>
        <h3 className="text-xl font-bold text-slate-900 mb-1">Alla mönster i korpusen</h3>
        <p className="text-sm text-slate-600 mb-4">De enskilda resultaten bakom sammanfattningen, sorterade efter vad de betyder för forskningen.</p>
        <div className="space-y-5">
          {groups.map(([title, help, statuses]) => {
            const items = patterns.filter(pt => statuses.includes(pt.status));
            if (!items.length) return null;
            return (
              <div key={title}>
                <h4 className="font-semibold text-slate-900">{title} <span className="text-slate-400 font-normal">({items.length})</span></h4>
                <p className="text-xs text-slate-500 mb-2">{help}</p>
                <ul className="space-y-2 text-sm">
                  {items.map((pt, i) => (
                    <li key={i} className="flex gap-3 rounded-xl bg-white border border-slate-200 p-3">
                      <div className="flex flex-col gap-1 shrink-0">
                        <span className={`h-fit w-fit px-2 py-0.5 rounded-lg border text-[11px] font-bold ${STATUS_STYLE[pt.status] ?? ""}`}><Tip text={GLOSSARY[pt.status]}>{pt.status}</Tip></span>
                        <SigBadge sig={pt.significance} compact />
                        <PatternBadges pt={pt} />
                      </div>
                      <div className="min-w-0">
                        <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">{pt.topic}</div>
                        <PatternBody pt={pt} />
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
        <div className="mt-3"><DocsNote anchor="1l-begränsningar-och-tolkning-av-mönstren">Hur mönstren ska tolkas och vilka reservationer som gäller står i avsnitt 1l.</DocsNote></div>
      </section>

      <Details title={`Fynd per sten (${s.n})`}>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[["Fynd per sten", s.n], ["Nya mot Rundata", s.new], ["Motsäger Rundata", s.contradicts],
            ["Finns redan i nyare källa", s.already_known], ["Nya även mot Runor 2020", s.still_new]].map(([l, v]) => (
            <div key={l as string} className="rounded-2xl bg-white border border-slate-200 p-4">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500"><Tip text={GLOSSARY[l as string]}>{l}</Tip></div>
              <div className="text-2xl font-bold text-slate-900">{v}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500">
          De starkaste nya och motsägande resultaten för enskilda stenar. Utöver ristare och datering ingår förlorade runor som
          sannolikhetsmodellen fyller i med minst 80 % säkerhet (kandidater att granska mot stenen), uppgifter i Runor 2020
          som saknas i eller motsäger Rundata (flyttade stenar, nyare läsningar), släktlänkar mellan stenar som delar namn
          (varje länk står på båda stenarna) och egna fynd från artiklar och analyser. &quot;Nyare källor&quot; visar avstämningen mot Runor 2020 och
          Wikidata (görs i <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>, där varje fynd också
          får en tolkning). Ett förslag är en hypotes för en runolog att pröva, inte en attribuering.
        </p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Sten</Th><Th>Metod</Th><Th>Mot Rundata</Th><Th>Resultat</Th>
              <Th>Rundata</Th><Th>Nyare källor</Th><Th>Bedömning</Th></tr></thead>
            <tbody>
              {top.map(f => (
                <tr key={`${f.signum}|${f.method}|${f.suggested ?? ""}|${f.ours}`} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold"><Link href={`/inskrifter/${encodeURIComponent(f.signum)}`} className="hover:underline">{f.signum}</Link>
                    <div className="text-[11px] text-slate-500 font-normal" translate="no">{f.place}</div></td>
                  <td className="p-2 text-xs">{f.method}</td>
                  <td className="p-2 text-xs font-bold">{f.verdict}</td>
                  <td className="p-2 text-xs max-w-[280px]">{f.ours}</td>
                  <td className="p-2 text-xs">{f.existing}</td>
                  <td className="p-2 text-xs" title={f.crosscheck?.runor?.text}>{f.crosscheck?.status ?? "–"}</td>
                  <td className="p-2 text-xs font-semibold">{f.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table></ExportTable>
        </div>
      </Details>
    </div>
  );
}
