"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { DocsNote } from "@/components/KnownLimitations";
import Link from "next/link";
import { API_URL } from "@/lib/api";

interface Status {
  r: { available: boolean; version: string | null; missing: string[]; note: string | null };
  corpus?: {
    fingerprint: string; n_stones: number; ready: boolean; computed_at: string | null; running: boolean;
    module: string | null; done_modules: string[]; error: string | null; errors: Record<string, string> | null;
    modules: { key: string; label: string }[];
  };
}

type Dict = Record<string, unknown>;
interface ChangeFeature {
  key: string; label: string; group: string; n: number; share: number;
  time: {
    tested: boolean; n: number; n_yes: number; p?: number; q?: number | null; shape?: string; peak_year?: number | null;
    year_first?: number; year_last?: number; first?: number; last?: number; change_lo?: number; change_hi?: number;
    draws?: { n: number; share_sig: number | null; share_same_shape: number | null };
  };
  provinces: { p_differ: number; rows: { province: string; n: number; share1050: number; lo1050: number; hi1050: number; cross_year: number | null; cross_lo: number | null; cross_hi: number | null }[] } | null;
  space: { n: number; p: number; high: string[]; low: string[] } | null;
}
interface AnonGroup {
  id: number; name?: string | null; status: "candidate" | "known"; type_stone: string; n: number; spread_km: number;
  stones: string[]; parishes: string[]; styles: { style: string; n: number }[] | null; stability: number;
  marks: { feature: string; share_group: number; share_area: number }[] | null;
  nearest_carver: { carver: string; n: number; dist: number; km: number; as_close_as_same_carver: boolean } | null;
  model: { n: number; carver: string; share: number; mean_p: number } | null;
}
interface ChangeAssoc {
  key: string; label: string; n: number; n_x: number; share_x: number; share_other: number;
  all: { or: number; lo: number; hi: number; p: number; q: number | null } | null;
  dated: { n: number; or?: number; lo?: number; hi?: number; p?: number } | null;
}
interface Pattern { topic: string; status: string; text: string; note?: string | null }
interface Finding {
  signum: string; place: string; method: string; verdict: string; ours: string; existing: string; score: number;
  assessment: string; suggested?: string; crosscheck?: { status: string; runor?: { text: string; url?: string | null } };
}
interface Corpus {
  computed_at: string; r_version: string; errors: Record<string, string>;
  figure_urls: Record<string, Record<string, string>>;
  patterns: Pattern[]; findings: Finding[];
  findings_summary: { n: number; new: number; contradicts: number; crosschecked: number; already_known: number; still_new: number };
  html_map_url: string | null;
  geography: Dict & { carvers: { carver: string; n: number; median_km: number; random_median_km: number; compact_ratio: number; compact_q: number; provinces: string; hull_area_km2: number }[]; method: string; water: Dict & { note?: string } };
  clusters: Dict & { k: number; best_silhouette: number; structure: string; n_stones: number; method: string; carvers: { ari: number };
    clusters: { cluster: number; n: number; stability: number; silhouette: number; features: { level: string; share_in_cluster: number; share_overall: number }[]; styles: { style: string; n: number }[]; provinces: { province: string; n: number }[] }[] };
  text: Dict & { method: string; lemmas: { lemma: string; n: number; cramers_v: number; q: number }[];
    formulas: { tests: { label: string; cramers_v: number; q: number }[] } };
  attribution: Dict & { method: string; caveat: string; n_train: number; carvers: string[]; majority_baseline: number;
    ablation: { features: string; accuracy: number; top3: number; log_loss: number }[];
    grouped_cv?: Record<string, { level: string; n_groups: number; ablation: { features: string; accuracy: number | null; top3: number | null }[] }>;
    calibration: { ece: number; reliability: { threshold: number; n: number; accuracy: number }[] };
    per_carver: { carver: string; n: number; recall: number; precision: number | null }[] };
  chronology: Dict & { method: string; region: string; validation: { rho: number; partial_rho: number; usable: boolean; mae_loo_years: number; mae_naive_years: number };
    corpus_dimensions: { dim: number; inertia_pct: number; rho_time: number; rho_lat: number; eta2_province: number; eta2_carver: number; positive: string[]; negative: string[]; unexplained: boolean; explained_by: string[] }[] };
  dialect: Dict & { method: string; caveat: string; mantel: { r: number; p: number }; n_districts: number;
    groups: { group: number; n: number; provinces: string }[]; group_forms: { group: number; forms: { lemma: string; form: string; share_in_group: number; share_all: number }[] }[] };
  network: Dict & { method: string; modularity: number; communities: { community: number; size: number; words: { word: string }[] }[];
    kinship: { relation: string; n: number; early: number; late: number; q_period: number; share_christian: number; share_other: number; q_christian: number }[] };
  change?: Dict & { method: string; n_dated: number; draws: number; features: ChangeFeature[]; assoc: ChangeAssoc[] };
  anonymous?: Dict & { method: string; n_unattributed: number; n_candidates: number;
    calibration: { link_km: number; lr_min: number; tpr: number; fpr: number; precision: number; max_spread_km: number };
    validation: { n_groups: number; n_stones: number; purity: number; purity_geography: number; share_pure: number };
    groups: AnonGroup[] };
}

type Tab = "overview" | "geography" | "clusters" | "text" | "attribution" | "anonymous" | "chronology" | "change" | "network";
const TABS: [Tab, string][] = [
  ["overview", "Översikt"], ["geography", "Geografi"], ["clusters", "Grupper"], ["text", "Språk och dialekter"],
  ["attribution", "Attribueringsmodell"], ["anonymous", "Okända ristare"], ["chronology", "Seriation"], ["change", "Förändring"], ["network", "Formelnätverk"],
];

const d2 = (v: number | null | undefined, k = 2) => v == null ? "–" : v.toFixed(k).replace(".", ",");
const pc = (v: number | null | undefined) => v == null ? "–" : `${Math.round(v * 100)} %`;
const TH = "text-left text-[11px] uppercase tracking-wider text-slate-500 p-2";

// What the measures and columns mean, shown on hover (or tap) – plain language, see METHODS.md 17 for the details
const GLOSSARY: Record<string, string> = {
  "q": "p-värde justerat för att många test görs samtidigt (Holm eller Benjamini–Hochberg). Under 0,05 räknas som säkerställt; ju lägre, desto starkare.",
  "p": "Sannolikheten att få ett minst lika tydligt resultat om det inte fanns något samband. Under 0,05 brukar räknas som statistiskt signifikant.",
  "Fynd per sten": "Antal resultat från R-analyserna som gäller en enskild sten: attribueringsmodellen, seriationen och okända ristare.",
  "Nya mot Rundata": "Fynd som säger något Rundata inte anger, t.ex. en ristare för en sten som saknar ristare.",
  "Motsäger Rundata": "Fynd som pekar på något annat än Rundata, t.ex. en annan ristare än den attribuerade.",
  "Finns redan i nyare källa": "Fyndet står redan i Runor 2020 eller Wikidata – en bekräftelse av metoden snarare än ny kunskap.",
  "Nya även mot Runor 2020": "Nya fynd som inte heller finns i Runor 2020 eller Wikidata (bland dem som stämts av).",
  "bekräftar": "Resultatet stämmer med något forskningen redan utgår från – ett tecken på att metoden fungerar.",
  "mönster att pröva": "Ett statistiskt mönster som appen inte kan förklara med det den känner till. Det kan vara nytt, eller beskrivet i litteratur som appen inte har.",
  "begränsning": "Resultatet visar främst en begränsning i data eller metod, inte något om runstenarna.",
  "svagt": "Mönstret är svagt eller osäkert.",
  "Sten": "Stenens signum i Rundata.",
  "Metod": "Vilken analys fyndet kommer från.",
  "Mot Rundata": "nytt = Rundata saknar uppgiften; motsäger = pekar på något annat än Rundata; stämmer = samma som Rundata.",
  "Resultat": "Vad analysen kommer fram till för stenen.",
  "Rundata": "Vad Rundata anger i dag.",
  "Nyare källor": "Avstämning mot Runor 2020 och Wikidata (görs i Forskningsluckor).",
  "Bedömning": "Hur starkt fyndet är sammantaget, vägt efter belägg, nyhet och relevans.",
  "Ristare": "Ristarnamnet i Rundata.",
  "Säkra stenar": "Stenar där Rundata anger ristaren som säker (signerade eller säkert attribuerade).",
  "Median till tyngdpunkt": "Medianavståndet från ristarens stenar till deras gemensamma mittpunkt – hur samlat ristaren arbetade.",
  "Slumpvisa urval": "Samma mått för lika många slumpvis valda stenar ur samma landskap (median av 499 urval).",
  "Kvot": "Ristarens spridning delad med slumpurvalens. Under 1 betyder att ristaren arbetade inom ett mindre område än slumpen ger.",
  "Höljets yta": "Ytan av den minsta konvexa polygon som omsluter ristarens stenar.",
  "Landskap": "Landskap där stenarna står, med Rundatas förkortningar (U = Uppland, Sö = Södermanland, Ög = Östergötland, Vg = Västergötland, Sm = Småland …).",
  "Grupp": "En grupp stenar som liknar varandra (klustringen görs utan ristare och plats).",
  "Stenar": "Antal stenar.",
  "Stabilitet": "Hur ofta gruppen kommer tillbaka när analysen görs om med delvis andra data (0–1). Över 0,75 är stabilt, under 0,5 osäkert.",
  "Utmärks av": "Drag som är vanligare i gruppen än i hela materialet (andel i gruppen mot andel totalt).",
  "Stilgrupper": "Gräslunds stilgrupper på stenarna, från RAK (äldst, omkring 980–1015) till Pr5 (yngst, omkring 1100–1130).",
  "silhuettbredd": "Hur väl stenarna passar i sin grupp jämfört med närmaste andra grupp (−1 till 1). Över 0,5 är tydliga grupper, 0,25–0,5 svag struktur, under 0,25 ingen tydlig struktur.",
  "justerat Rand-index": "Hur väl två indelningar stämmer överens, rensat för slump: 0 = som slumpen, 1 = identiska.",
  "Cramérs V": "Styrkan i sambandet mellan två kategorier (0–1), t.ex. hur ett ord stavas och vem som ristade. Över 0,3 är ett tydligt samband.",
  "Mantel r": "Sambandet mellan två avståndstabeller (−1 till 1), här hur olika häraderna stavar mot hur långt ifrån varandra de ligger.",
  "rho": "Spearmans rangkorrelation (−1 till 1): 0 = inget samband, 1 = samma ordning.",
  "Belägg": "Vilka variabler modellen fick använda: bara geografi, bara stil, bara språk och innehåll, eller alla.",
  "Slumpvis": "Andel rätt vid vanlig korsvalidering, där stenar från samma plats kan finnas både i tränings- och testdata.",
  "Ny socken/härad": "Andel rätt när hela socknar respektive härader hölls utanför träningen – hur väl modellen fungerar på en plats den inte sett.",
  "Hittas (recall)": "Andel av ristarens säkra stenar som modellen pekar ut som ristarens (korsvaliderat).",
  "Rätt när föreslagen (precision)": "När modellen föreslår ristaren: hur ofta det är rätt (korsvaliderat).",
  "Dimension": "En av korrespondensanalysens huvudaxlar – den riktning där stenarna skiljer sig mest åt.",
  "Inerti": "Hur stor del av den totala variationen dimensionen fångar.",
  "Tid (rho)": "Rangkorrelation mellan stenarnas läge på dimensionen och stilgruppens mittår. Över 0,3 (eller under −0,3) betyder att dimensionen följer tiden.",
  "Latitud (rho)": "Rangkorrelation mellan läget på dimensionen och hur nordligt stenen står.",
  "Landskap (eta²)": "Hur stor del av variationen längs dimensionen som förklaras av landskapet (0–1).",
  "Ristare (eta²)": "Hur stor del av variationen längs dimensionen som förklaras av ristaren (0–1), bland ristare med minst åtta stenar.",
  "Förklaras av": "Vad dimensionen följer: tid, geografi eller ristare. Gult = ett oförklarat mönster.",
  "Skiljer": "Dragen i dimensionens två ändar.",
  "Relation": "Släktord i inskrifterna, t.ex. fader, son, broder.",
  "Inskrifter": "Antal inskrifter som nämner relationen.",
  "Före ca 1050": "Andel av de daterade inskrifterna från före omkring 1050 (stilgrupp RAK–Pr2) som nämner relationen.",
  "Efter ca 1050": "Andel av de daterade inskrifterna från efter omkring 1050 (Pr3–Pr5).",
  "q (tid)": "Justerat p-värde för skillnaden före och efter 1050.",
  "Kristna": "Andel av inskrifterna med kristen bön eller kors som nämner relationen.",
  "Övriga": "Andel av övriga inskrifter som nämner relationen.",
  "q (kristen)": "Justerat p-värde för skillnaden mellan kristna och övriga inskrifter.",
  "Drag": "Språkdrag, skriftdrag eller innehåll som följs över tid.",
  "Daterade stenar": "Stenar med stilgrupp (och därmed ungefärlig tid) där draget kan bestämmas.",
  "Förlopp": "Formen på den justerade kurvan: ökar, minskar, vanligast eller ovanligast vid en viss tid, eller oförändrad.",
  "Justerad andel": "Andel stenar med draget i början och i slutet av perioden när plats och ristare hålls konstanta – alla stenar flyttas till samma år, för en typisk ristare.",
  "Omräkningar säkerställda": "Stilgruppen ger ett tidsintervall, inte ett år. Resultatet räknades om med årtal dragna inom intervallen; här andelen omräkningar som också gav ett säkerställt samband.",
  "Vanligast i": "Landskap där draget är vanligast enligt kartmodellen.",
  "Ovanligast i": "Landskap där draget är ovanligast enligt kartmodellen.",
  "Brostenar": "Andel av bro- och vägstenarna som har draget (och hur många brostenar det finns).",
  "Andra stenar": "Andel av övriga stenar med tolkningsbar text som har draget.",
  "Oddskvot (95 % KI)": "Hur mycket större oddsen för draget är på brostenar än på andra stenar, med plats och ristare konstanta. 1 = ingen skillnad. KI = 95 % konfidensintervall; innehåller det 1 är skillnaden osäker.",
  "Daterade, med tid": "Samma oddskvot bland daterade stenar när också tiden hålls konstant.",
  "Nr": "Gruppens nummer på kartan.",
  "Arbetsnamn": "En etikett efter typstenens socken – inte namnet på en person. Typstenen är den sten som i genomsnitt liknar de andra i gruppen mest.",
  "Socknar": "Socknar där gruppens stenar står, de vanligaste först.",
  "Utmärks av (gruppen mot trakten)": "Drag som är vanligare i gruppen än på andra stenar inom 50 km (andel i gruppen mot andel i trakten).",
  "Närmast liknande ristare i Rundata": "Den kända ristare inom 50 km vars stenar mest liknar gruppen – men inte lika mycket som två stenar av samma ristare brukar göra.",
  "Liknar": "Den kända ristare som gruppen liknar.",
  "Attribueringsmodellen": "Vad attribueringsmodellen föreslår för gruppens stenar.",
  "Möjliga okända ristare": "Grupper av stenar utan ristare som liknar varandra lika mycket som en ristares stenar och inte liknar någon känd ristare i närheten.",
  "Liknar en känd ristare": "Grupper som liknar en känd ristare – underlag för attribuering snarare än en ny ristare.",
  "Prövat på kända ristare": "När metoden kördes på stenar med känd ristare, som om ristaren vore okänd: hur stor del av en grupp som i genomsnitt var samma ristare.",
  "Bara närliggande stenar": "Samma mått för grupper av lika många närliggande stenar. Skillnaden mot rutan bredvid är vad handens drag (stavning, språk, formler, stil) tillför utöver platsen.",
};

// How to read each figure (keyed by its alt text)
const FIG_HELP: Record<string, string> = {
  "Ristarnas områden": "Varje panel är en ristare. Blå punkter är ristarens säkra stenar, linjen är det konvexa höljet runt dem och + tyngdpunkten; grått är alla runstenar. Ett litet, samlat hölje betyder att ristaren arbetade lokalt.",
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
  "Grupper av stenar utan ristare": "Röda punkter är grupper som kan vara en okänd ristare eller verkstad, blå är grupper som liknar en känd ristare. Numren hänvisar till tabellerna nedan; grått är övriga stenar med läsbar text.",
};

// A term with an explanation on hover, focus or tap. The box is placed on the page itself (portal), so that tables
// with their own scrolling do not cut it off.
function Tip({ text, children }: { text?: string; children: ReactNode }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [pos, setPos] = useState<{ x: number; y: number; above: boolean } | null>(null);
  if (!text) return <>{children}</>;
  const show = () => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const above = r.bottom + 170 > window.innerHeight;
    setPos({ x: Math.max(8, Math.min(r.left, window.innerWidth - 296)), y: above ? r.top - 6 : r.bottom + 6, above });
  };
  return (
    <span ref={ref} tabIndex={0} role="button" aria-label={text}
      onMouseEnter={show} onMouseLeave={() => setPos(null)} onFocus={show} onBlur={() => setPos(null)}
      onClick={e => { e.stopPropagation(); if (pos) setPos(null); else show(); }}
      className="cursor-help underline decoration-dotted decoration-slate-400 underline-offset-2 outline-none focus-visible:ring-2 focus-visible:ring-[#b7410e]/40 rounded">
      {children}
      {pos && createPortal(
        <span role="tooltip" style={{ left: pos.x, top: pos.y, transform: pos.above ? "translateY(-100%)" : undefined }}
          className="fixed z-[100] w-72 rounded-xl bg-slate-900 px-3 py-2 text-[12px] font-normal normal-case tracking-normal leading-snug text-white shadow-xl pointer-events-none">
          {text}
        </span>, document.body)}
    </span>
  );
}

// A column heading; the explanation is looked up from the heading text unless given
function Th({ children, tip }: { children: ReactNode; tip?: string }) {
  return <th className={TH}><Tip text={tip ?? (typeof children === "string" ? GLOSSARY[children] : undefined)}>{children}</Tip></th>;
}

function Lightbox({ src, alt, help, onClose }: { src: string; alt: string; help?: string; onClose: () => void }) {
  const [full, setFull] = useState(false);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return createPortal(
    <div role="dialog" aria-modal="true" aria-label={alt} onClick={onClose}
      className="fixed inset-0 z-[90] bg-slate-900/80 backdrop-blur-sm flex flex-col items-center p-3 md:p-8">
      <div className="w-full max-w-6xl flex flex-wrap items-center justify-between gap-2 text-white mb-3" onClick={e => e.stopPropagation()}>
        <div className="font-bold">{alt}</div>
        <div className="flex gap-2 text-xs font-bold">
          <button type="button" onClick={() => setFull(f => !f)} className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25">
            {full ? "Anpassa till fönstret" : "Full storlek"}
          </button>
          <a href={src} target="_blank" rel="noreferrer" className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25">Öppna i ny flik</a>
          <button type="button" onClick={onClose} className="px-3 py-1.5 rounded-lg bg-white text-slate-900">Stäng</button>
        </div>
      </div>
      <div className="w-full max-w-6xl flex-1 min-h-0 overflow-auto rounded-2xl bg-white p-2" onClick={e => e.stopPropagation()}>
        {/* eslint-disable-next-line @next/next/no-img-element -- figures are rendered by R on the backend */}
        <img src={src} alt={alt} onClick={() => setFull(f => !f)}
          className={full ? "max-w-none cursor-zoom-out" : "w-full h-auto cursor-zoom-in"} />
      </div>
      {help && <p className="w-full max-w-6xl mt-3 text-sm text-white/90 leading-relaxed" onClick={e => e.stopPropagation()}>{help}</p>}
    </div>, document.body);
}

// An R figure: click to enlarge; "Så läser du figuren" explains it on hover
function Fig({ src, alt, narrow }: { src?: string; alt: string; narrow?: boolean }) {
  const [open, setOpen] = useState(false);
  if (!src) return null;
  const url = `${API_URL}${src}`;
  const help = FIG_HELP[alt];
  return (
    <figure className={`group/fig rounded-2xl bg-white border border-slate-200 p-2 ${narrow ? "max-w-3xl w-full mx-auto" : ""}`}>
      <button type="button" onClick={() => setOpen(true)} className="relative block w-full cursor-zoom-in" aria-label={`Förstora: ${alt}`}>
        {/* eslint-disable-next-line @next/next/no-img-element -- figures are rendered by R on the backend */}
        <img src={url} alt={alt} className="w-full h-auto rounded-xl" loading="lazy" />
        <span className="absolute top-2 right-2 rounded-lg bg-slate-900/75 text-white text-[11px] font-bold px-2 py-1 opacity-0 group-hover/fig:opacity-100 transition-opacity">
          Förstora
        </span>
      </button>
      {help && (
        <figcaption className="px-2 pt-2 pb-1 text-[11px] text-slate-600">
          <Tip text={help}><span className="font-semibold">Så läser du figuren</span></Tip>
          <span className="text-slate-400"> · klicka på figuren för att förstora</span>
        </figcaption>
      )}
      {open && <Lightbox src={url} alt={alt} help={help} onClose={() => setOpen(false)} />}
    </figure>
  );
}

// The method in short; caveats and how to read the results are in the documentation (METHODS.md 17)
function Method({ text }: { text?: string; caveat?: string }) {
  if (!text) return null;
  return (
    <details className="text-xs text-slate-600 rounded-xl bg-slate-50 border border-slate-200 p-3">
      <summary className="cursor-pointer font-semibold">Metod</summary>
      <p className="mt-2">{text}</p>
    </details>
  );
}

// Kept for the rest of the visit, so that returning to the page is instant; the results are refetched only when the
// corpus version (fingerprint) changes
const memo: { status?: Status; data?: Corpus; fingerprint?: string } = {};

export default function StatistikPage() {
  const [status, setStatus] = useState<Status | null>(memo.status ?? null);
  const [data, setData] = useState<Corpus | null>(memo.data ?? null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  const [tick, setTick] = useState(0);

  // Loads the status and, when the corpus analyses are ready, their results; tick reloads
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/r/status`).then(r => r.json()).then(async (st: Status) => {
      if (cancelled) return;
      setStatus(st);
      memo.status = st;
      if (st.corpus?.ready && !(memo.data && memo.fingerprint === st.corpus.fingerprint)) {
        const res = await fetch(`${API_URL}/api/r/corpus`);
        if (res.ok && !cancelled) {
          const d = await res.json();
          memo.data = d;
          memo.fingerprint = st.corpus.fingerprint;
          setData(d);
        }
      }
    }).catch(() => { if (!cancelled) setError("Kunde inte nå analysmotorn."); });
    return () => { cancelled = true; };
  }, [tick]);

  // Poll while the corpus analyses run
  useEffect(() => {
    if (!status?.corpus?.running) return;
    const t = setInterval(() => setTick(x => x + 1), 4000);
    return () => clearInterval(t);
  }, [status?.corpus?.running]);

  const start = async () => {
    setError(null);
    const res = await fetch(`${API_URL}/api/r/corpus/run`, { method: "POST" });
    if (!res.ok) { setError((await res.json().catch(() => null))?.detail || `Fel ${res.status}`); return; }
    setTick(x => x + 1);
  };

  const c = status?.corpus;
  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Statistik (R)</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Hela korpusen av svenska vikingatida runstenar analyserad i R: ristarnas områden, grupper av stil och språk,
          stavning och dialekter, en korsvaliderad attribueringsmodell, seriation mot Gräslunds kronologi, hur språk, skrift
          och kristna drag förändras över tid och mellan landskap, och formelnätverk.
          Samma analyser används för den enskilda stenen i <Link href="/stenanalys" className="text-[#b7410e] hover:underline">Fullständig stenanalys</Link> och
          stenrapporten, och resultaten ställs mot forskningen i <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>.
        </p>
      </div>

      {error && <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-3 text-sm text-red-800">{error}</div>}

      <div className="liquid-glass-island rounded-[24px] p-5 flex flex-wrap items-center gap-4">
        {!status ? <span className="text-slate-500">Hämtar läget …</span> : !status.r.available ? (
          <div className="text-sm text-amber-900">
            <strong>R är inte tillgängligt på servern.</strong> {status.r.note}
            {status.r.missing.length > 0 && <div className="text-xs mt-1">Saknas: {status.r.missing.join(", ")}</div>}
          </div>
        ) : (
          <>
            <div className="text-sm">
              <div className="font-bold text-slate-900">{status.r.version}</div>
              <div className="text-slate-500 text-xs">
                Korpus: {c?.n_stones} runstenar · version {c?.fingerprint}
                {c?.computed_at && ` · beräknad ${new Date(c.computed_at).toLocaleString("sv-SE")}`}
              </div>
            </div>
            {c && !c.ready && !c.running && (
              <button onClick={start} className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-bold">
                Beräkna korpusanalyserna (några minuter)
              </button>
            )}
            {c?.running && (
              <div className="flex flex-wrap gap-2 text-xs">
                {c.modules.map(m => (
                  <span key={m.key} className={`px-2 py-1 rounded-lg border ${c.done_modules.includes(m.key) ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                    : c.module === m.key ? "bg-amber-50 border-amber-300 text-amber-900 animate-pulse" : "bg-white border-slate-200 text-slate-500"}`}>
                    {c.done_modules.includes(m.key) ? "✓ " : ""}{m.label}
                  </span>
                ))}
              </div>
            )}
            {c?.error && !c.running && <span className="text-xs text-red-700">{c.error}</span>}
            {data && (
              <a href={`${API_URL}/api/r/package`} className="ml-auto px-4 py-2 rounded-xl border border-slate-300 bg-white text-sm font-bold hover:bg-slate-50">
                Ladda ner reproducerbarhetspaket (R-skript, data, resultat)
              </a>
            )}
          </>
        )}
      </div>

      {data && (
        <>
          <div className="flex flex-wrap gap-2">
            {TABS.map(([key, label]) => (
              <button key={key} onClick={() => setTab(key)}
                className={`px-4 py-2 rounded-xl text-sm font-bold border ${tab === key ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}>
                {label}
              </button>
            ))}
          </div>
          <div className="liquid-glass-island rounded-[32px] p-5 space-y-5">
            {tab === "overview" && <Overview data={data} />}
            {tab === "geography" && <Geography data={data} />}
            {tab === "clusters" && <Clusters data={data} />}
            {tab === "text" && <TextTab data={data} />}
            {tab === "attribution" && <Attribution data={data} />}
            {tab === "anonymous" && <Anonymous data={data} />}
            {tab === "chronology" && <Chronology data={data} />}
            {tab === "change" && <Change data={data} />}
            {tab === "network" && <Network data={data} />}
          </div>
        </>
      )}
    </div>
  );
}

const STATUS_STYLE: Record<string, string> = {
  "bekräftar": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "mönster att pröva": "bg-amber-50 text-amber-900 border-amber-200",
  "begränsning": "bg-slate-100 text-slate-700 border-slate-300", "svagt": "bg-slate-100 text-slate-700 border-slate-300",
};

function Overview({ data }: { data: Corpus }) {
  const s = data.findings_summary;
  const top = data.findings.filter(f => f.verdict !== "stämmer").slice(0, 25);
  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[["Fynd per sten", s.n], ["Nya mot Rundata", s.new], ["Motsäger Rundata", s.contradicts],
          ["Finns redan i nyare källa", s.already_known], ["Nya även mot Runor 2020", s.still_new]].map(([l, v]) => (
          <div key={l as string} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500"><Tip text={GLOSSARY[l as string]}>{l}</Tip></div>
            <div className="text-2xl font-bold text-slate-900">{v}</div>
          </div>
        ))}
      </div>
      <div>
        <h3 className="font-bold text-slate-900 mb-2">Mönster i korpusen</h3>
        <ul className="space-y-2 text-sm">
          {data.patterns.map((pt, i) => (
            <li key={i} className="flex gap-3">
              <span className={`shrink-0 h-fit px-2 py-0.5 rounded-lg border text-[11px] font-bold ${STATUS_STYLE[pt.status] ?? ""}`}><Tip text={GLOSSARY[pt.status]}>{pt.status}</Tip></span>
              <div><span className="text-[11px] uppercase tracking-wider text-slate-500 mr-2">{pt.topic}</span>{pt.text}</div>
            </li>
          ))}
        </ul>
        <div className="mt-3"><DocsNote anchor="17-statistik-i-r">Hur mönstren ska tolkas och vilka reservationer som gäller står i avsnitt 17.</DocsNote></div>
      </div>
      <div>
        <h3 className="font-bold text-slate-900 mb-1">Starkaste fynden per sten</h3>
        <p className="text-xs text-slate-500 mb-2">
          Nya och motsägande resultat från attribueringsmodellen och seriationen. &quot;Nyare källor&quot; visar avstämningen mot
          Runor 2020 och Wikidata (görs i <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>).
          Ett förslag är en hypotes för en runolog att pröva, inte en attribuering.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr><Th>Sten</Th><Th>Metod</Th><Th>Mot Rundata</Th><Th>Resultat</Th>
              <Th>Rundata</Th><Th>Nyare källor</Th><Th>Bedömning</Th></tr></thead>
            <tbody>
              {top.map(f => (
                <tr key={`${f.signum}|${f.method}`} className="border-t border-slate-900/5">
                  <td className="p-2 font-semibold"><Link href={`/inskrifter/${encodeURIComponent(f.signum)}`} className="hover:underline">{f.signum}</Link>
                    <div className="text-[11px] text-slate-500 font-normal">{f.place}</div></td>
                  <td className="p-2 text-xs">{f.method}</td>
                  <td className="p-2 text-xs font-bold">{f.verdict}</td>
                  <td className="p-2 text-xs max-w-[280px]">{f.ours}</td>
                  <td className="p-2 text-xs">{f.existing}</td>
                  <td className="p-2 text-xs" title={f.crosscheck?.runor?.text}>{f.crosscheck?.status ?? "–"}</td>
                  <td className="p-2 text-xs font-semibold">{f.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function Geography({ data }: { data: Corpus }) {
  const g = data.geography, f = data.figure_urls.geography || {};
  return (
    <>
      <p className="text-sm text-slate-700">
        {String(g.n_compact)} av {g.carvers.length} ristare med minst fem säkra stenar arbetade inom ett mindre område än slumpvisa
        stenar ur samma landskap.{" "}
        {data.html_map_url && <a href={`${API_URL}${data.html_map_url}`} target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Öppna den interaktiva kartan (leaflet)</a>}
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.map} alt="Ristarnas områden" /><Fig src={f.water} alt="Avstånd till vatten" /></div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><Th>Ristare</Th><Th>Säkra stenar</Th><Th>Median till tyngdpunkt</Th>
            <Th>Slumpvisa urval</Th><Th>Kvot</Th><Th>q</Th><Th>Höljets yta</Th><Th>Landskap</Th></tr></thead>
          <tbody>{g.carvers.map(r => (
            <tr key={r.carver} className="border-t border-slate-900/5">
              <td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td><td className="p-2">{d2(r.median_km, 1)} km</td>
              <td className="p-2">{d2(r.random_median_km, 1)} km</td><td className="p-2">{d2(r.compact_ratio)}</td><td className="p-2">{d2(r.compact_q, 3)}</td>
              <td className="p-2">{r.hull_area_km2} km²</td><td className="p-2 text-xs">{r.provinces}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={g.method} />
    </>
  );
}

function Clusters({ data }: { data: Corpus }) {
  const c = data.clusters, f = data.figure_urls.clusters || {};
  return (
    <>
      <p className="text-sm text-slate-700">
        {c.n_stones} stenar i {c.k} grupper; strukturen är {c.structure} (<Tip text={GLOSSARY["silhuettbredd"]}>silhuettbredd</Tip> {d2(c.best_silhouette)}). Grupperna
        sammanfaller inte med ristarna (<Tip text={GLOSSARY["justerat Rand-index"]}>justerat Rand-index</Tip> {d2(c.carvers.ari)}).
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.mca} alt="MCA" /><Fig src={f.variables} alt="Kategorier i MCA" />
        <Fig src={f.silhouette} alt="Silhuettbredd" /><Fig src={f.carvers} alt="Ristare per grupp" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><Th>Grupp</Th><Th>Stenar</Th><Th>Stabilitet</Th><Th>Utmärks av</Th><Th>Stilgrupper</Th><Th>Landskap</Th></tr></thead>
          <tbody>{c.clusters.map(k => (
            <tr key={k.cluster} className="border-t border-slate-900/5 align-top">
              <td className="p-2 font-semibold">{k.cluster}</td><td className="p-2">{k.n}</td><td className="p-2">{d2(k.stability)}</td>
              <td className="p-2 text-xs">{k.features.slice(0, 4).map(x => `${x.level} (${pc(x.share_in_cluster)} mot ${pc(x.share_overall)})`).join("; ")}</td>
              <td className="p-2 text-xs">{k.styles.map(x => `${x.style} ${x.n}`).join(", ")}</td>
              <td className="p-2 text-xs">{k.provinces.map(x => `${x.province} ${x.n}`).join(", ")}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={c.method} />
    </>
  );
}

function TextTab({ data }: { data: Corpus }) {
  const t = data.text, dl = data.dialect, ft = data.figure_urls.text || {}, fd = data.figure_urls.dialect || {};
  return (
    <>
      <h3 className="font-bold text-slate-900">Ristarnas stavning och formler</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={ft.formulas} alt="Formler per ristare" /><Fig src={ft.lemmas} alt="Stavning per ord" /></div>
      <p className="text-sm text-slate-700">
        Formler som skiljer ristarna åt (<Tip text={GLOSSARY["Cramérs V"]}>Cramérs V</Tip>): {t.formulas.tests.map(x => `${x.label} ${d2(x.cramers_v)}`).join(", ")}.
      </p>
      <Method text={t.method} />
      <h3 className="font-bold text-slate-900 pt-3">Stavning och dialekter</h3>
      <p className="text-sm text-slate-700">
        Ortografiskt avstånd mot geografiskt avstånd mellan {dl.n_districts} härader: <Tip text={GLOSSARY["Mantel r"]}>Mantel r</Tip> {d2(dl.mantel.r)}, <Tip text={GLOSSARY["p"]}>p</Tip> {d2(dl.mantel.p, 3)}.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={fd.distance} alt="Stavning mot avstånd" /><Fig src={fd.groups} alt="Härader med likartad stavning" />
        <Fig src={fd.efter} alt="Stavning av efter" /><Fig src={fd.sten} alt="Diftongen i sten" />
      </div>
      <ul className="text-sm space-y-1">
        {dl.group_forms.map(g => (
          <li key={g.group}><strong>Grupp {g.group}</strong> ({dl.groups.find(x => x.group === g.group)?.provinces}):{" "}
            {g.forms.map(x => `${x.lemma} = ${x.form} (${pc(x.share_in_group)} mot ${pc(x.share_all)})`).join("; ")}</li>
        ))}
      </ul>
      <Method text={dl.method} caveat={dl.caveat} />
    </>
  );
}

function Attribution({ data }: { data: Corpus }) {
  const a = data.attribution, f = data.figure_urls.attribution || {};
  return (
    <>
      <p className="text-sm text-slate-700">
        {a.n_train} säkra stenar av {a.carvers.length} ristare. Modellen hittar rätt ristare i{" "}
        {pc(a.ablation.find(x => x.features === "Alla")?.accuracy)} av fallen vid korsvalidering, mot {pc(a.majority_baseline)} om man alltid
        gissar på den vanligaste ristaren. Sannolikheterna är försiktiga:{" "}
        {a.calibration.reliability.map(r => `vid minst ${d2(r.threshold, 1)} är förstavalet rätt i ${pc(r.accuracy)} (${r.n} stenar)`).join("; ")}.
      </p>
      {a.grouped_cv && (
        <div className="overflow-x-auto">
          <p className="text-sm text-slate-700 mb-2">
            <strong>Fungerar modellen på en ny plats?</strong> Vid slumpvis korsvalidering kan stenar från samma plats finnas
            både i tränings- och testdata. Här hålls hela socknar respektive härader utanför träningen; en ristare som bara
            finns i det utelämnade området kan då inte föreslås och räknas som fel.
          </p>
          <table className="w-full text-sm">
            <thead><tr><Th>Belägg</Th><Th>Slumpvis</Th>
              {Object.entries(a.grouped_cv).map(([k, g]) => <Th key={k} tip={GLOSSARY["Ny socken/härad"]}>Ny {k.toLowerCase()} ({g.n_groups} grupper)</Th>)}</tr></thead>
            <tbody>{a.ablation.map(x => (
              <tr key={x.features} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{x.features}</td><td className="p-2">{pc(x.accuracy)}</td>
                {Object.entries(a.grouped_cv!).map(([k, g]) => <td key={k} className="p-2">{pc(g.ablation.find(y => y.features === x.features)?.accuracy ?? undefined)}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.ablation} alt="Delmodeller" /><Fig src={f.calibration} alt="Kalibrering" />
        <Fig src={f.importance} alt="Variabler" /><Fig src={f.confusion} alt="Förväxlingar" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><Th>Ristare</Th><Th>Säkra stenar</Th><Th>Hittas (recall)</Th><Th>Rätt när föreslagen (precision)</Th></tr></thead>
          <tbody>{a.per_carver.map(r => (
            <tr key={r.carver} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td>
              <td className="p-2">{pc(r.recall)}</td><td className="p-2">{pc(r.precision)}</td></tr>))}</tbody>
        </table>
      </div>
      <Method text={a.method} caveat={a.caveat} />
    </>
  );
}

function Chronology({ data }: { data: Corpus }) {
  const ch = data.chronology, f = data.figure_urls.chronology || {}, v = ch.validation;
  return (
    <>
      <p className="text-sm text-slate-700">
        I {ch.region === "U" ? "Uppland" : ch.region} ordnar seriationen av språk och innehåll stenarna i samma följd som Gräslunds stilkronologi
        (<Tip text={GLOSSARY["rho"]}>rho</Tip> {d2(v.rho)}, {d2(v.partial_rho)} med latituden konstant), utan att ornamentiken ingick. Årtalen är osäkra:
        medelfel {v.mae_loo_years} år mot {v.mae_naive_years} år utan modell.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.validation} alt="Seriation mot Gräslund" /><Fig src={f.diagram} alt="Seriationsdiagram" /><Fig src={f.estimates} alt="Skattad tid" />
      </div>
      <h3 className="font-bold text-slate-900">Vad korpusens dimensioner följer</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><Th>Dimension</Th><Th>Inerti</Th><Th>Tid (rho)</Th><Th>Latitud (rho)</Th>
            <Th>Landskap (eta²)</Th><Th>Ristare (eta²)</Th><Th>Förklaras av</Th><Th>Skiljer</Th></tr></thead>
          <tbody>{ch.corpus_dimensions.map(x => (
            <tr key={x.dim} className={`border-t border-slate-900/5 align-top ${x.unexplained ? "bg-amber-50" : ""}`}>
              <td className="p-2 font-semibold">{x.dim}</td><td className="p-2">{d2(x.inertia_pct, 1)} %</td><td className="p-2">{d2(x.rho_time)}</td>
              <td className="p-2">{d2(x.rho_lat)}</td><td className="p-2">{d2(x.eta2_province)}</td><td className="p-2">{d2(x.eta2_carver)}</td>
              <td className="p-2 text-xs font-semibold">{x.unexplained ? "oförklarat mönster" : x.explained_by.join(", ")}</td>
              <td className="p-2 text-xs">{x.positive.slice(0, 3).join(", ")} ↔ {x.negative.slice(0, 3).join(", ")}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={ch.method} />
    </>
  );
}

function Network({ data }: { data: Corpus }) {
  const n = data.network, f = data.figure_urls.network || {};
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.network} alt="Formelnätverk" /><Fig src={f.kinship} alt="Släktrelationer" /></div>
      <ul className="text-sm space-y-1">
        {n.communities.map(c => <li key={c.community}><strong>Grupp {c.community}</strong> ({c.size} ord): {c.words.map(w => w.word).join(", ")}</li>)}
      </ul>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><Th>Relation</Th><Th>Inskrifter</Th><Th>Före ca 1050</Th><Th>Efter ca 1050</Th>
            <Th>q (tid)</Th><Th>Kristna</Th><Th>Övriga</Th><Th>q (kristen)</Th></tr></thead>
          <tbody>{n.kinship.map(k => (
            <tr key={k.relation} className={`border-t border-slate-900/5 ${k.q_period < 0.05 ? "bg-amber-50" : ""}`}>
              <td className="p-2 font-semibold">{k.relation}</td><td className="p-2">{k.n}</td><td className="p-2">{pc(k.early)}</td><td className="p-2">{pc(k.late)}</td>
              <td className="p-2">{d2(k.q_period, 3)}</td><td className="p-2">{pc(k.share_christian)}</td><td className="p-2">{pc(k.share_other)}</td><td className="p-2">{d2(k.q_christian, 3)}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <Method text={n.method} />
    </>
  );
}

const SHAPE: Record<string, string> = {
  rises: "ökar", falls: "minskar", peak: "vanligast omkring", trough: "ovanligast omkring", flat: "oförändrad",
};
const qText = (q: number | null | undefined) => q == null ? "–" : q < 0.001 ? "< 0,001" : d2(q, 3);

function Change({ data }: { data: Corpus }) {
  const c = data.change, f = data.figure_urls.change || {};
  if (!c) return <p className="text-sm text-slate-600">Förändringsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const crossing = c.features.filter(x => (x.provinces?.rows || []).filter(r => r.cross_year).length >= 2);
  return (
    <>
      <p className="text-sm text-slate-700">
        Hur språkdrag, skrift och kristna drag förändras över tid och skiljer sig mellan landskap, med plats och ristare
        konstanta. Tiden kommer från Gräslunds stilgrupper ({c.n_dated} daterade stenar); varje resultat är omräknat {c.draws} gånger
        med årtal dragna inom stilgruppens intervall. Gulmarkerade rader är säkerställda efter Holm-justering (<Tip text={GLOSSARY["q"]}>q</Tip> under 0,05).
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr><Th>Drag</Th><Th>Daterade stenar</Th><Th>Förlopp</Th>
            <Th>Justerad andel</Th><Th>q</Th><Th>Omräkningar säkerställda</Th>
            <Th>Vanligast i</Th><Th>Ovanligast i</Th></tr></thead>
          <tbody>{c.features.map(x => {
            const t = x.time, sig = t.q != null && t.q < 0.05;
            return (
              <tr key={x.key} className={`border-t border-slate-900/5 ${sig ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{x.label}</td>
                <td className="p-2">{t.n}</td>
                <td className="p-2 text-xs">{t.tested ? `${SHAPE[t.shape ?? ""] ?? ""}${t.peak_year ? ` ${t.peak_year}` : ""}` : "för få daterade stenar"}</td>
                <td className="p-2 text-xs">{t.tested ? `${pc(t.first)} (${t.year_first}) → ${pc(t.last)} (${t.year_last})` : "–"}</td>
                <td className="p-2">{qText(t.q)}</td>
                <td className="p-2 text-xs">{t.draws?.n ? pc(t.draws.share_sig) : "–"}</td>
                <td className="p-2 text-xs">{x.space && x.space.p < 0.05 ? x.space.high.join(", ") : "–"}</td>
                <td className="p-2 text-xs">{x.space && x.space.p < 0.05 ? x.space.low.join(", ") : "–"}</td>
              </tr>
            );
          })}</tbody>
        </table>
      </div>
      <Fig src={f.time} alt="Dragen över tid" />
      <Fig src={f.map} alt="Var dragen är vanligast" />
      <Fig src={f.provinces} alt="Landskapen omkring 1050" />
      {crossing.length > 0 && (
        <div>
          <h3 className="font-bold text-slate-900 mb-1">När draget passerar hälften av stenarna</h3>
          <ul className="text-sm space-y-1">
            {crossing.map(x => (
              <li key={x.key}><strong>{x.label}</strong>{" "}
                (skillnad mellan landskapen p {qText(x.provinces!.p_differ)}):{" "}
                {x.provinces!.rows.filter(r => r.cross_year).sort((a, b) => a.cross_year! - b.cross_year!)
                  .map(r => `${r.province} omkring ${r.cross_year} (${r.cross_lo}–${r.cross_hi})`).join(", ")}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="overflow-x-auto">
        <h3 className="font-bold text-slate-900 mb-1">Bro- och vägstenar och kristna drag</h3>
        <table className="w-full text-sm">
          <thead><tr><Th>Drag</Th><Th>Brostenar</Th><Th>Andra stenar</Th>
            <Th>Oddskvot (95 % KI)</Th><Th>q</Th><Th>Daterade, med tid</Th></tr></thead>
          <tbody>{c.assoc.map(a => (
            <tr key={a.key} className={`border-t border-slate-900/5 ${a.all?.q != null && a.all.q < 0.05 ? "bg-amber-50" : ""}`}>
              <td className="p-2 font-semibold">{a.label}</td><td className="p-2">{pc(a.share_x)} av {a.n_x}</td>
              <td className="p-2">{pc(a.share_other)}</td>
              <td className="p-2">{a.all ? `${d2(a.all.or)} (${d2(a.all.lo)}–${d2(a.all.hi)})` : "–"}</td>
              <td className="p-2">{qText(a.all?.q)}</td>
              <td className="p-2 text-xs">{a.dated?.or != null ? `${d2(a.dated.or)} (${d2(a.dated.lo)}–${d2(a.dated.hi)}), p ${qText(a.dated.p)}` : "–"}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <DocsNote anchor="17-statistik-i-r">Hur förändringsanalysen ska läsas och vilka reservationer som gäller står i avsnitt 17.</DocsNote>
      <Method text={c.method} />
    </>
  );
}

function Stones({ list }: { list: string[] }) {
  return (
    <span>
      {list.slice(0, 8).map((sg, i) => (
        <span key={sg}>{i > 0 && ", "}<Link href={`/inskrifter/${encodeURIComponent(sg)}`} className="hover:underline">{sg}</Link></span>
      ))}
      {list.length > 8 && ` och ${list.length - 8} till`}
    </span>
  );
}

function Anonymous({ data }: { data: Corpus }) {
  const a = data.anonymous, f = data.figure_urls.anonymous || {};
  if (!a) return <p className="text-sm text-slate-600">Analysen av okända ristare saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const v = a.validation, cal = a.calibration;
  const cands = a.groups.filter(g => g.status === "candidate"), known = a.groups.filter(g => g.status === "known");
  return (
    <>
      <p className="text-sm text-slate-700">
        Grupper av stenar utan ristare i Rundata som ligger nära varandra och liknar varandra i stavning, språkdrag,
        formler och stil lika mycket som en ristares stenar brukar göra. En grupp som inte liknar någon känd ristare kan
        vara en ristare eller verkstad som ännu saknar namn, och får ett <strong>arbetsnamn</strong> efter typstenens
        socken. Namnet är en etikett för gruppen, inte ett påstående om en person; kontrollera mot litteraturen om gruppen
        redan är beskriven.
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[["Möjliga okända ristare", `${cands.length} grupper`], ["Liknar en känd ristare", `${known.length} grupper`],
          ["Prövat på kända ristare", `${pc(v.purity)} samma ristare`], ["Bara närliggande stenar", `${pc(v.purity_geography)} samma ristare`]].map(([l, val]) => (
          <div key={l} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500"><Tip text={GLOSSARY[l]}>{l}</Tip></div>
            <div className="text-xl font-bold text-slate-900">{val}</div>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500">
        När metoden kördes på {v.n_stones} stenar med känd ristare, som om ristaren vore okänd, bestod en grupp i genomsnitt
        till {pc(v.purity)} av samma ristare ({pc(v.share_pure)} av grupperna till minst tre fjärdedelar), mot {pc(v.purity_geography)} för
        lika många närliggande stenar. Två stenar länkas när de ligger inom {cal.link_km} km och är så lika att paret är minst {cal.lr_min} gånger
        vanligare bland samma ristares stenar än bland olika ristares; {pc(cal.precision)} av sådana par med känd ristare är samma ristare.
      </p>
      <Fig src={f.map} alt="Grupper av stenar utan ristare" narrow />
      <div className="overflow-x-auto">
        <h3 className="font-bold text-slate-900 mb-1"><Tip text={GLOSSARY["Möjliga okända ristare"]}>Möjliga okända ristare</Tip></h3>
        <table className="w-full text-sm">
          <thead><tr><Th>Nr</Th><Th>Arbetsnamn</Th><Th>Stenar</Th><Th>Socknar</Th>
            <Th>Stilgrupper</Th><Th>Utmärks av (gruppen mot trakten)</Th><Th>Stabilitet</Th>
            <Th>Närmast liknande ristare i Rundata</Th></tr></thead>
          <tbody>{cands.map(g => (
            <tr key={g.id} className="border-t border-slate-900/5 align-top">
              <td className="p-2">{g.id}</td>
              <td className="p-2 font-semibold">{g.name}<div className="text-[11px] font-normal text-slate-500">typsten{" "}
                <Link href={`/inskrifter/${encodeURIComponent(g.type_stone)}`} className="hover:underline">{g.type_stone}</Link></div></td>
              <td className="p-2 text-xs">{g.n}: <Stones list={g.stones} /></td>
              <td className="p-2 text-xs">{g.parishes.slice(0, 4).join(", ")}{g.parishes.length > 4 ? " …" : ""}</td>
              <td className="p-2 text-xs">{(g.styles || []).map(x => `${x.style} ${x.n}`).join(", ") || "–"}</td>
              <td className="p-2 text-xs">{(g.marks || []).map(m => `${m.feature} (${pc(m.share_group)} mot ${pc(m.share_area)})`).join("; ") || "–"}</td>
              <td className="p-2">{pc(g.stability)}</td>
              <td className="p-2 text-xs">{g.nearest_carver ? `${g.nearest_carver.carver} (${d2(g.nearest_carver.km, 0)} km bort, inte lika nära som samma ristares stenar)` : "ingen inom 50 km"}</td>
            </tr>))}</tbody>
        </table>
      </div>
      {known.length > 0 && (
        <div className="overflow-x-auto">
          <h3 className="font-bold text-slate-900 mb-1">Grupper som liknar en känd ristare</h3>
          <p className="text-xs text-slate-500 mb-2">Stenar utan ristare i Rundata som kan höra till en känd ristare – underlag för attribuering snarare än en ny ristare.</p>
          <table className="w-full text-sm">
            <thead><tr><Th>Nr</Th><Th>Liknar</Th><Th>Stenar</Th><Th>Attribueringsmodellen</Th><Th>Stabilitet</Th></tr></thead>
            <tbody>{known.map(g => (
              <tr key={g.id} className="border-t border-slate-900/5 align-top">
                <td className="p-2">{g.id}</td>
                <td className="p-2 font-semibold">{g.nearest_carver?.as_close_as_same_carver ? g.nearest_carver.carver : g.model?.carver}</td>
                <td className="p-2 text-xs">{g.n}: <Stones list={g.stones} /></td>
                <td className="p-2 text-xs">{g.model ? `${g.model.carver} för ${pc(g.model.share)} av ${g.model.n} stenar med förslag` : "–"}</td>
                <td className="p-2">{pc(g.stability)}</td>
              </tr>))}</tbody>
          </table>
        </div>
      )}
      <DocsNote anchor="17-statistik-i-r">Hur grupperna ska läsas och vilka reservationer som gäller står i avsnitt 17.</DocsNote>
      <Method text={a.method} />
    </>
  );
}
