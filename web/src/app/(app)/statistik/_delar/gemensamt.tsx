import { type ReactNode } from "react";
import { Confidence, Figure, SigBadge, Tip } from "@/components/Explain";
import { PatternBadges, PatternBody, type Pattern, HideWrittenToggle } from "@/components/PatternCard";
import { GLOSSARY } from "@/lib/glossary";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { useWrittenFilter } from "@/lib/patternArticles";
import type { Corpus, Section, Status } from "./typer";

export const d2 = (v: number | null | undefined, k = 2) => v == null ? "–" : v.toFixed(k).replace(".", ",");
export const pc = (v: number | null | undefined) => v == null ? "–" : `${Math.round(v * 100)} %`;
const TH = "text-left text-[11px] uppercase tracking-wider text-slate-500 p-2";

// How to read each figure (keyed by its alt text)
const FIG_HELP: Record<string, string> = {
  "Ristarnas områden": "Varje panel är en ristare. Blå punkter är ristarens säkra stenar, linjen är det konvexa höljet runt dem och + tyngdpunkten; grått är alla runstenar. Ett litet, samlat hölje betyder att ristaren arbetade lokalt.",
  "Lämningar runt stenarna": "Andelen runstenar (blått) och slumpvisa punkter på land i stenarnas närhet (grått) som ligger inom 500 m från en registrerad lämning av varje slag i Kulturmiljöregistret. En högre blå stapel betyder att stenarna står närmare den sortens lämningar än slumpen ger.",
  "Avstånd till vatten": "Fördelningen av avstånd till närmaste strand, sjö eller vattendrag för runstenarna och för slumpvisa punkter på land (rotskala). Ligger runstenarnas fördelning till vänster står de närmare vatten än slumpen ger.",
  "MCA": "Stenarna i det rum som korrespondensanalysen ger (de två första dimensionerna). Varje panel visar en grupp i blått mot alla stenar i grått; en grupp som ligger samlat skiljer sig tydligt från de andra.",
  "Kategorier i MCA": "De drag som bidrar mest till de två första dimensionerna. Drag som ligger nära varandra förekommer ofta på samma stenar; ju längre från mitten, desto mer skiljer draget stenarna åt.",
  "Silhuettbredd": "Hur tydliga grupperna blir för olika antal grupper (k). Antalet med högst värde väljs; under 0,25 betyder svag struktur.",
  "Ristare per grupp": "Hur varje ristares säkra stenar fördelar sig på grupperna (talen är antal stenar, färgen andel). Om grupperna motsvarade ristare skulle varje rad ha all färg i en enda ruta.",
  "Formler per ristare": "Vilka resarformler (t.ex. lét resa, reste) och ristarsignaturer varje ristare använder, som andel av ristarens säkra inskrifter.",
  "Stavning per ord": "Ord vars stavning bäst skiljer ristarna åt, mätt med Cramérs V. Längre stapel betyder att stavningen av ordet säger mer om vem som ristade.",
  "Stavning mot avstånd": "Varje punkt är ett par härader: hur långt ifrån varandra de ligger mot hur olika de stavar. En stigande linje betyder att stavningen skiljer sig mer ju längre ifrån varandra häraderna ligger.",
  "Härader med likartad stavning": "Härader som stavar likartat har samma färg. Grupperna bildades bara ur stavningen; att de ändå hänger ihop på kartan tyder på regionala skrivtraditioner (eller ristarverkstäder).",
  "Stavning av efter": "Hur æftiR (efter) stavas på stenarna i olika delar av landet.",
  "Diftongen i sten": "Om sten skrivs med diftong (stain) eller monoftong (stin) på olika platser.",
  "Delmodeller": "Hur ofta modellen hittar rätt ristare med bara geografi, bara stil, bara språk och innehåll, eller allt – slumpvis och med hela socknar utelämnade. Den streckade linjen är att alltid gissa på den vanligaste ristaren.",
  "Kalibrering": "Stämmer modellens sannolikheter? Punkterna visar hur ofta förstavalet var rätt vid olika sannolikheter (större punkt = fler stenar). På den streckade diagonalen är sannolikheterna exakta; ovanför är modellen försiktig och har rätt oftare än den säger.",
  "Variabler": "Vilka variabler modellen förlitar sig mest på: hur mycket träffsäkerheten sjunker när variabeln blandas om slumpvis.",
  "Förväxlingar": "Rad = rätt ristare, kolumn = modellens förstaval. En mörk diagonal betyder rätt; mörka rutor utanför diagonalen visar vilka ristare som förväxlas.",
  "Seriation mot Gräslund": "Stenarnas läge i seriationen (som bara bygger på språk och innehåll) för varje stilgrupp. Stiger lådorna från RAK till Pr5 följer seriationen Gräslunds kronologi, utan att ornamentiken ingått.",
  "Seriationsdiagram": "Stenarna ordnade efter seriationen i tio lika stora grupper, från tidigt till sent. Stapelns höjd är hur vanligt draget är i gruppen; drag överst hör till de tidiga stenarna, drag nederst till de sena.",
  "Skattad tid": "Skattat årtal för stenar utan stilgrupp, ur seriationen. Osäkerheten är stor – ordningen är säkrare än årtalet.",
  "Formelnätverk": "Ord som ofta står i samma inskrifter är förbundna (tätare linje = starkare samband, större punkt = fler inskrifter). Ord med samma färg bildar en grupp som hör ihop, t.ex. en formel.",
  "Släktrelationer": "Hur stor andel av runstenarna i varje landskap som nämner en viss släktrelation.",
  "Dragen över tid": "Punkterna är andelen stenar med draget i varje stilgrupp, med 95 % intervall (större punkt = fler stenar). Den blå linjen är den justerade andelen med plats och ristare konstanta: förändringen över tid när man rensat för att olika perioder har stenar från olika trakter och ristare. Rubriken anger förloppet och q-värdet.",
  "Var dragen är vanligast": "Modellens skattade andel stenar med draget för en typisk ristare; mörkare blå = vanligare. Kartan visas bara nära stenar där draget kan bestämmas, och bara för drag där platsen spelar roll.",
  "Landskapen omkring 1050": "Skattad andel stenar med draget omkring år 1050 i varje landskap, med 95 % intervall. Intervall som inte överlappar tyder på en verklig skillnad mellan landskapen.",
  "Grupper av stenar utan ristare": "Röda punkter är grupper som kan vara en skrivmiljö – en verkstad eller en bygds skrivsed, blå är grupper som liknar en känd ristare. Numren hänvisar till tabellerna nedan; grått är övriga stenar med läsbar text.",
};

// A column heading; the explanation is looked up from the heading text unless given
export function Th({ children, tip }: { children: ReactNode; tip?: string }) {
  return <th className={TH}><Tip text={tip ?? (typeof children === "string" ? GLOSSARY[children] : undefined)}>{children}</Tip></th>;
}

// An R figure from the backend, with its reading guide
export function Fig({ src, alt, narrow }: { src?: string; alt: string; narrow?: boolean }) {
  return <Figure src={src ? `${API_URL}${src}` : undefined} alt={alt} help={FIG_HELP[alt]} narrow={narrow} />;
}

export function Method({ text, caveat }: { text?: string; caveat?: string }) {
  if (!text) return null;
  return (
    <details className="text-xs text-slate-600 rounded-xl bg-slate-50 border border-slate-200 p-3">
      <summary className="cursor-pointer font-semibold">Metod och reservationer (för den som vill veta mer)</summary>
      <p className="mt-2">{text}</p>
      {caveat && <p className="mt-2">{caveat}</p>}
    </details>
  );
}

export const PATTERN_TOPICS: Record<string, string[]> = {
  geography: ["Geografi"], attribution: ["Attribuering"], text: ["Språk"], clusters: ["Stil och innehåll"],
  chronology: ["Datering"], network: ["Släkt och formler", "Släkter över stenar"], anonymous: ["Skrivmiljöer", "Okända ristare"], change: ["Förändring", "Regional skillnad", "Samband"],
  messages: ["Budskap"], people: ["Människorna"],
};
export const patternsFor = (patterns: Pattern[], key: string) => patterns.filter(p => (PATTERN_TOPICS[key] ?? []).includes(p.topic));

export const TOPIC: Record<string, string> = {
  attribution: "Vem ristade?", anonymous: "Skrivmiljöer", change: "Förändring", chronology: "Datering",
  geography: "Geografi", text: "Stavning och dialekt", clusters: "Grupper av stenar", network: "Formler och släkt",
  words: "Ordförrådet", messages: "Budskap", people: "Människorna", question: "Egen fråga",
};

// The answer first: question, why it matters, the key number, the answer, a suggested interpretation and its limits
export function SectionIntro({ section, patterns = [] }: { section?: Section; patterns?: Pattern[] }) {
  const { shown, written } = useWrittenFilter(patterns);
  if (!section) return null;
  const tests = patternsFor(shown, section.key);
  const writtenHere = patternsFor(patterns, section.key).length - tests.length;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#b7410e]">{TOPIC[section.key]}</div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-900">{section.question}</h3>
          <p className="text-slate-600 mt-1">{section.why}</p>
        </div>
        <Confidence level={section.confidence} text={section.confidence_text} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-4">
        <div className="rounded-2xl bg-slate-900 text-white p-5 flex flex-col justify-center">
          <div className="text-4xl font-bold tracking-tight">{section.headline.value}</div>
          <div className="text-sm text-white/80 mt-1 leading-snug">{section.headline.label}</div>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Svaret i korthet</div>
          <p className="text-slate-800 leading-relaxed">{section.answer}</p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-2">Förslag till tolkning</h4>
          <ul className="space-y-2 text-sm text-slate-700 list-disc pl-5">{section.interpretation.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
        <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <h4 className="font-bold text-slate-900 mb-2">Det här säger resultatet inte</h4>
          <ul className="space-y-2 text-sm text-slate-600 list-disc pl-5">{section.not_saying.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
      </div>
      {tests.length > 0 && (
        <div className="rounded-2xl bg-white border border-slate-200 p-5">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
            <h4 className="font-bold text-slate-900">Statistiska test i den här delen</h4>
            {written > 0 && <HideWrittenToggle written={written} />}
          </div>
          {writtenHere > 0 && <p className="text-xs text-slate-500 mb-1">{writtenHere} resultat som vi redan skrivit om är dolda.</p>}
          <p className="text-xs text-slate-500 mb-3">
            {tests.filter(t => t.significance?.significant).length} av {tests.length} resultat är statistiskt signifikanta
            (<Tip text={GLOSSARY["Statistiskt signifikant"]}>vad betyder det?</Tip>).
          </p>
          <ul className="space-y-2 text-sm">
            {tests.map((t, i) => (
              <li key={i} className="flex flex-col sm:flex-row sm:items-start gap-2">
                <div className="flex flex-wrap gap-1.5 shrink-0"><SigBadge sig={t.significance} /><PatternBadges pt={t} /></div>
                <div className="min-w-0"><PatternBody pt={t} /></div>
              </li>
            ))}
          </ul>
        </div>
      )}
      <h4 className="font-bold text-slate-900 pt-2">Figurer och siffror</h4>
    </div>
  );
}

// The adjusted share over time as a small line (0–100 %, the same scale in every row)
export function Spark({ curve }: { curve?: { year: number; share: number }[] }) {
  if (!curve || curve.length < 2) return null;
  const W = 96, H = 30, x0 = curve[0].year, x1 = curve[curve.length - 1].year;
  const pts = curve.map(p => [((p.year - x0) / (x1 - x0 || 1)) * (W - 6) + 3, H - 3 - p.share * (H - 6)]);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const last = pts[pts.length - 1];
  const label = `Justerad andel från ${pc(curve[0].share)} (${x0}) till ${pc(curve[curve.length - 1].share)} (${x1})`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} className="shrink-0">
      <title>{label}</title>
      <line x1="3" x2={W - 3} y1={H - 3} y2={H - 3} stroke="#e2e8f0" strokeWidth="1" />
      <line x1="3" x2={W - 3} y1="3" y2="3" stroke="#f1f5f9" strokeWidth="1" />
      <path d={d} fill="none" stroke="#2a78d6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={pts[0][0]} cy={pts[0][1]} r="2.5" fill="#2a78d6" />
      <circle cx={last[0]} cy={last[1]} r="2.5" fill="#2a78d6" />
    </svg>
  );
}

// Kept for the rest of the visit, so that returning to the page is instant; the results are refetched only when the
// corpus version (fingerprint) changes
export const memo: { status?: Status; data?: Corpus; fingerprint?: string } = {};

export const pText = (p: number | null | undefined) => p == null ? "–" : p < 0.001 ? "< 0,001" : d2(p, 3);

export const SHAPE: Record<string, string> = {
  rises: "ökar", falls: "minskar", peak: "vanligast omkring", trough: "ovanligast omkring", flat: "oförändrad",
};
export const qText = (q: number | null | undefined) => q == null ? "–" : q < 0.001 ? "< 0,001" : d2(q, 3);

export function Stones({ list }: { list: string[] }) {
  return (
    <span>
      {list.slice(0, 8).map((sg, i) => (
        <span key={sg}>{i > 0 && ", "}<Link href={`/inskrifter/${encodeURIComponent(sg)}`} className="hover:underline">{sg}</Link></span>
      ))}
      {list.length > 8 && ` och ${list.length - 8} till`}
    </span>
  );
}

export const PROVINCE_NAMES: Record<string, string> = { U: "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", Sm: "Småland", Vg: "Västergötland",
  M: "Medelpad", Vs: "Västmanland", G: "Gotland", "Öl": "Öland", Gs: "Gästrikland", Hs: "Hälsingland", Nä: "Närke", Dr: "Dalarna" };
