/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import type { Metadata } from "next";
import LanguageToggle from "@/components/LanguageToggle";
import LocalAppLink from "@/components/LocalAppLink";
import StatsNote from "@/components/StatsNote";
import SiteVote from "@/components/SiteVote";
import ZoomImage from "@/components/ZoomImage";
import { VERSION } from "@/lib/version";
import ArticleTeasers from "@/components/ArticleTeasers";
import type { BlogPost } from "@/components/BlogBody";
import { getPost, listPosts } from "@/lib/articles";
import { featuredFirst } from "@/lib/featured";
import { pictures } from "@/lib/blogSeo";
import { AUTHORS, CONTACT_PATH, DOCS_URL, DOWNLOAD_URL, GITHUB_URL, METHODS_URL, SITE_DESCRIPTION, SITE_URL } from "@/lib/site";

// The newest articles are fetched again at most every five minutes, and at once when one is published (tag "blog")
export const revalidate = 60;

async function latestArticles(): Promise<{ posts: BlogPost[]; photo: { src: string; alt: string; credit: string | null } | null }> {
  const { posts } = await listPosts();
  if (!posts.length) return { posts, photo: null };
  // The photo of the article shown large: the article of the month, or the latest
  const body = (await getPost(featuredFirst(posts)[0].slug))?.body ?? "";
  return { posts, photo: pictures(body).find(p => /wikimedia\.org/.test(p.src)) ?? null };
}

export const metadata: Metadata = {
  title: { absolute: "Vitki – runstenar, runinskrifter och runforskning med öppna data" },
  description: SITE_DESCRIPTION,
  alternates: { canonical: "/" },
};

// Structured data (schema.org): the site and the research software, which is downloaded from GitHub
const FOUNDER = { "@type": "Person", name: "Viktor Kvant", url: AUTHORS["Viktor Kvant"].url, sameAs: [AUTHORS["Viktor Kvant"].url],
                  jobTitle: AUTHORS["Viktor Kvant"].role };
const JSON_LD = [
  {
    "@context": "https://schema.org", "@type": "Organization", "@id": `${SITE_URL}/#organization`, name: "Vitki", url: SITE_URL,
    logo: { "@type": "ImageObject", url: `${SITE_URL}/vitki_logo.png` }, founder: FOUNDER, sameAs: [GITHUB_URL],
    description: SITE_DESCRIPTION,
  },
  {
    "@context": "https://schema.org", "@type": "WebSite", name: "Vitki", url: SITE_URL, inLanguage: ["sv", "en"],
    description: SITE_DESCRIPTION, publisher: { "@id": `${SITE_URL}/#organization` },
  },
  {
    "@context": "https://schema.org", "@type": "SoftwareApplication", name: "Vitki", url: SITE_URL, downloadUrl: GITHUB_URL,
    applicationCategory: "ResearchApplication", operatingSystem: "macOS, Linux, Windows", isAccessibleForFree: true,
    offers: { "@type": "Offer", price: "0", priceCurrency: "SEK" },
    license: "https://www.gnu.org/licenses/gpl-3.0.html", author: FOUNDER, publisher: { "@id": `${SITE_URL}/#organization` },
    description: SITE_DESCRIPTION,
    about: ["Runstenar", "Runinskrifter", "Runologi", "Vikingatiden", "Samnordisk runtextdatabas"],
  },
];

const GITHUB = "https://github.com/Precatio/runes";

// What R is, for readers from the humanities: the articles rest on analyses in R
const R_POINTS = [
  {
    title: "Ett fritt verktyg för statistik",
    text: "R är ett fritt och öppet program för statistik och diagram. Det skapades på 1990-talet av statistikerna Ross Ihaka och Robert Gentleman i Nya Zeeland och används i dag av forskare över hela världen – också inom språkvetenskap, arkeologi och historia.",
  },
  {
    title: "Ett recept som vem som helst kan följa",
    text: "En analys i R är ett skript: en text som steg för steg beskriver vad datorn ska göra med materialet. Den som har skriptet och samma data får exakt samma resultat. Därför kan andra granska varje siffra i artiklarna – och pröva om de håller.",
  },
  {
    title: "Verktyg från hela forskarvärlden",
    text: "Över 20 000 tilläggspaket, skrivna av forskare, gör R till ett gemensamt verktygsförråd. Vitki använder bland annat paket för kartor (sf), för kurvor över tid (mgcv) och för att hitta platser där ett mönster samlas (spdep och smerc).",
  },
  {
    title: "Vad R gör med runstenarna",
    text: "R räknar och jämför: hur vanligt ett drag är före och efter en viss tid, om stenarna står närmare vatten än slumpen skulle ge, om ett mönster samlas på en plats. Framför allt prövar R om ett mönster är tydligare än vad slumpen brukar ge – det är det som skiljer ett fynd från en tillfällighet.",
  },
];

// The app in pictures: what each view does, for readers who will never open it (the app runs on the researcher's own
// computer; screenshots in public/bilder, taken from the running app)
const APP_VIEWS = [
  {
    src: "/bilder/app-karta.webp", title: "Mönsterkartan",
    text: "Välj ett drag – ett kors, en bön, en stavning – och se var det är vanligt och hur det förändras. Här kristen bön före och efter omkring 1050. Kartan visar andelen stenar med draget, så att Upplands många stenar inte döljer mönstret.",
  },
  {
    src: "/bilder/app-inskrifter.webp", title: "Inskrifterna",
    text: "Alla 6 753 inskrifter i Samnordisk runtextdatabas, sökbara på text, plats, period, stilgrupp och ristare. Varje sökning kan laddas ner som tabell, med källan angiven.",
  },
  {
    src: "/bilder/app-stilgrupper.webp", title: "Stilgrupperna",
    text: "Anne-Sofie Gräslunds stilgrupper, som daterar runstenarna efter ornamentiken, och hur Rundatas stenar fördelar sig mellan dem. Det är grunden för tidslinjerna i artiklarna.",
  },
  {
    src: "/bilder/app-statistik.webp", title: "Statistiken i R",
    text: "Elva statistiska analyser i R: kluster, dialekter, datering, förändring över tid, fornlämningar och ortnamn. Varje resultat redovisar hur säkert det är och kan laddas ner som ett paket med skript och data.",
  },
  {
    src: "/bilder/app-luckor.webp", title: "Forskningsluckorna",
    text: "De mönster som klarar de statistiska proven, vart och ett med en hypotes och ett förslag på hur den kan prövas. Härifrån kommer ämnena till artiklarna.",
  },
  {
    src: "/bilder/app-stenoversikt.webp", title: "Stenöversikten",
    text: "Varje runsten vägd mot Rundatas ristare med sex metoder – statistisk modell, ortografi, område, stilgrupp, språkdrag och bergart. Var stöder metoderna attribueringen, och var finns nya förslag?",
  },
];

// 3D scans from our own studies: Sö 113, scanned by Laila Kitzler Åhfeldt (CC BY 4.0), measured in Vitki
const SCANS = [
  {
    src: "/bilder/skanning-so113-strykljus.webp", title: "Släpljus från fyra håll",
    text: "Så som runologer granskar en sten i fält – men i datorn, utan att vänta på rätt ljus.",
  },
  {
    src: "/bilder/skanning-so113-vinklar.webp", title: "Mätpunkterna",
    text: "Vitki lägger tvärsnitt genom spåren och mäter vinkel, djup och bredd. Färgen visar huggspårets vinkel i varje snitt.",
  },
  {
    src: "/bilder/skanning-so113-profiler.webp", title: "254 tvärsnitt",
    text: "Tvärsnitten genom runorna lagda på varandra. Den röda linjen är den typiska profilen – ristarens handlag i millimeter, som kan jämföras mellan stenar.",
  },
];
const SCAN_CREDIT = "https://doi.org/10.5281/zenodo.11951255";

const USE_CASES = [
  {
    title: "Ristarattribuering",
    text: "Pröva en attribuering mot Rundata, inskriftens ortografi, den uppmätta huggtekniken och en statistisk modell – och kontrollera geografi, stilgrupp, bergart och språkdrag mot landskapets övriga stenar.",
  },
  {
    title: "Läsning av skadade inskrifter",
    text: "Strykljus och relief ur 3D-skanningen och RTI-förstärkning gör grunda eller vittrade ristningar läsbara; en blind läsning kan jämföras med Rundata ord för ord.",
  },
  {
    title: "Datering och stil",
    text: "Se en inskrifts stilgrupp i Gräslunds kronologi, och var den hamnar i en seriation byggd på språk och innehåll i stället för ornamentik.",
  },
  {
    title: "Nya hypoteser ur korpusen",
    text: "Statistiken pekar ut det som är värt en runologs tid: grupper av stenar utan ristare, förändringar i stavning och tro, och attribueringar som bör prövas igen.",
  },
  {
    title: "Reproducerbara mätningar",
    text: "Samma fil och samma parametrar ger samma resultat, och varje mätning som delas i korpusen gör jämförelserna säkrare för alla. Bidragsgivare anges alltid.",
  },
  {
    title: "Undervisning",
    text: "Studenter kan utforska Rundata, kartor, stilgrupper och statistiken, se hur kvantitativa metoder fungerar – och var deras gränser går.",
  },
];

const PRINCIPLES = [
  {
    title: "Verifierbara källor",
    text: "Uppgifter om inskrifter hämtas ur Samnordisk runtextdatabas och anges med källa. Mönster och ristarförslag räknas fram med statistiska modeller ur de belagda uppgifterna – inget signum, ingen text och ingen ristare gissas fram.",
  },
  {
    title: "Prövat mot det modellen inte sett",
    text: "Varje statistisk modell valideras med korsvalidering, också på socknar och härader den aldrig sett. Varje mönster prövas dessutom i två oberoende halvor: stenarna delas socken för socken i två grupper med samma trakter och samma tid, analysen görs om i varje grupp, och mönstret räknas bara om det syns i båda – då beror det inte på några enskilda socknar eller ristare.",
  },
  {
    title: "Osäkerhet och signifikans redovisas",
    text: "Mätvärden visas med spridning, andelar med konfidensintervall. P-värden justeras för många test och för hur hypotesen valdes, och det som är statistiskt signifikant märks tydligt.",
  },
  {
    title: "Landskapet som jämförelse",
    text: "Ett drag talar för en ristare bara om det är ovanligare på andra stenar i samma landskap – inte bara i hela korpusen.",
  },
  {
    title: "Ingen AI-statistik",
    text: "Kandidater räknas fram ur beläggen med öppna vikter. AI läser bilder och skriver löptext, anger aldrig sannolikheter, och dess bedömningar märks som okalibrerade.",
  },
  {
    title: "Det som inte håller redovisas",
    text: "Negativa resultat och kända brister redovisas öppet, och tumregler som verktygsklassningen kallas tumregler.",
  },
];

const NEW_THINGS = [
  {
    title: "Öppen, webbaserad huggspårsmätning",
    text: "Tidigare 3D-analyser av huggteknik har gjorts i proprietär programvara. Här är hela mätkedjan öppen källkod, körs i webbläsaren och redovisar varje snitt med spridning och full proveniens.",
  },
  {
    title: "Ortografisk stilometri med redovisad träffsäkerhet",
    text: "Stavningsmönster jämförs över hela Rundatas vikingatida korpus. Egennamn räknas inte, så att signaturer inte avslöjar svaret, och metoden utvärderas separat på signerade inskrifter.",
  },
  {
    title: "Runologiska antaganden prövade med öppna modeller",
    text: "Om ristarna arbetade lokalt, om stavningen följer avståndet och om språket följer ornamentikens kronologi prövas i R med uttalade kriterier, osäkerhet och beroendet av tidigare forskning angivet.",
  },
  {
    title: "Flera oberoende belägg i samma analys",
    text: "Litteraturens attribuering, ortografi, huggteknik och statistik vägs samman öppet, och kandidaterna prövas mot geografi, stil, bergart och språkdrag. Varje kandidat visar vilka belägg som stöder eller talar emot den.",
  },
  {
    title: "En tolkning för varje fynd",
    text: "Appen väger metodernas besked mot varandra och mot nyare källor, säger hur starkt fyndet är och vad som skulle kunna avgöra frågan – i stället för att lämna en lista med sannolikheter.",
  },
  {
    title: "En delad, öppen mätkorpus",
    text: "Mätningar från olika forskare samlas med licens och bidragsgivare, och ristare kopplas automatiskt via Rundata. Det gör jämförelser möjliga mellan projekt och regioner.",
  },
];

// The newer open sources and the questions they make possible
const LANDSCAPE = [
  {
    source: "Kulturmiljöregistret (Riksantikvarieämbetet)",
    title: "Gravfält, vägar och broar",
    text: "Gravfält, gravhögar, forna färdvägar, broar, fornborgar och hamnar ur RAÄ:s register över lämningar. 61 % av runstenarna står inom 500 m från ett gravfält, mot 21 % av slumpvisa platser – lika ofta efter 1050 som före, och lika ofta för kristna stenar. Gravfälten tycks ha förblivit släktens minnesplatser genom kristnandet.",
  },
  {
    source: "Höjdmodell och landhöjning",
    title: "Dåtidens strand",
    text: "I Mälardalen låg stranden omkring fem meter högre omkring år 1000. Med en terrängmodell och landhöjningen per landskap jämförs stenarnas lägen med dåtidens vatten i stället för dagens – och stenarnas närhet till vatten blir tydligare, mest i Uppland.",
  },
  {
    source: "Samnordisk runtextdatabas",
    title: "Mönsterkartan",
    text: "Var finns de kristna bönerna, de stungna runorna och monoftongerna – och de få uttryckligt hedniska stenarna? Kartan visar andelen per område före och efter 1050, så att Upplands täthet inte döljer mönstret.",
  },
  {
    source: "Runor 2020 och Wikidata",
    title: "Avstämning mot nyare källor",
    text: "Appens förslag om ristare stäms av mot Riksantikvarieämbetets utgåva 2020 och Wikidata. Ett förslag som redan finns där bekräftar metoden; ett som motsägs granskas.",
  },
];

const RELATED = [
  "Laila Kitzler Åhfeldts 3D-baserade analyser av huggteknik (Stockholms universitet), som vår metod för separata spårtyper, medelvärden per sten och Ward-klustring följer, och hennes öppet publicerade skanningar, som krediteras när de används.",
  "Samnordisk runtextdatabas och Rundata-net, samt Riksantikvarieämbetets och Uppsala universitets plattform Runor.",
  "Projektet ”AI i runologins tjänst” (Stockholms universitet, 2024–2026), som utvecklar AI-sökning i Rundata-net.",
];

const SOURCES = [
  {
    name: "Samnordisk runtextdatabas",
    detail: "Institutionen för nordiska språk, Uppsala universitet. Version 2014 (RUNDATA.xls 2018). Open Database License / Database Contents License.",
    href: "https://www.uu.se/institution/nordiska/forskning/projekt/samnordisk-runtextdatabas",
  },
  {
    name: "Runor och Wikidata",
    detail: "Riksantikvarieämbetets utgåva 2020 av runtextdatabasen och Wikidata (CC0), för avstämningen av appens förslag mot nyare källor.",
    href: "https://runor.raa.se/",
  },
  {
    name: "Danske Runeindskrifter",
    detail: "Nationalmuseet och Københavns Universitet. De danska översättningarna är ett stöd när appen gör svenska utkast till översättningar av danska inskrifter.",
    href: "https://runer.ku.dk/",
  },
  {
    name: "Gräslund, A.-S. 1998",
    detail: "Ornamentiken som dateringsgrund för Upplands runstenar. I: Innskrifter og datering / Dating inscriptions. Trondheim, s. 73–91.",
  },
  {
    name: "Kitzler Åhfeldt, L. 2002",
    detail: "Work and Worship. Laser Scanner Analysis of Viking Age Rune Stones. Stockholms universitet.",
  },
  {
    name: "Öppna 3D-skanningar (Zenodo, CC BY 4.0)",
    detail: "Kitzler Åhfeldt, L. 2024: Runstenar i Södermanland, Runstenar signerade av Åsmund Kåresson och Runstenar och tidigkristna gravmonument i Västergötland. Kitzler Åhfeldt, L. & Zedig, H. 2024 och 2025: Runstenar i Medelpad och i Hälsingland, skannade av Henrik Zedig. Kitzler Åhfeldt, L. 2025: Tidigkristna gravmonument i Östergötland och Småland. Riksantikvarieämbetet.",
    href: "https://doi.org/10.5281/zenodo.11951255",
  },
  {
    name: "Kitzler Åhfeldt, L. & Imer, L. M. 2019",
    detail: "Rune Carvers and Sponsor Families on Bornholm. Danish Journal of Archaeology 8.",
    href: "https://doi.org/10.7146/dja.v8i0.113226",
  },
  {
    name: "Axelson, J. 1993",
    detail: "Mellansvenska runristare (Runrön 5). Källa för många ristarattribueringar i Rundata.",
  },
  {
    name: "Lager, L. 2002",
    detail: "Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige. Korsformerna i Rundata.",
  },
  {
    name: "R Core Team",
    detail: "R: A Language and Environment for Statistical Computing. R Foundation for Statistical Computing, Wien. Paketen anges i METHODS.md.",
    href: "https://www.r-project.org/",
  },
  {
    name: "Malzbender, T., Gelb, D. & Wolters, H. 2001",
    detail: "Polynomial Texture Maps. SIGGRAPH ’01. Grunden för RTI-visaren och diffuse gain.",
  },
  {
    name: "SGU och Natural Earth",
    detail: "Berggrund 1:50 000–1:250 000 (Sveriges geologiska undersökning) och kustlinjer, sjöar och vattendrag 1:10 miljoner (public domain).",
    href: "https://www.sgu.se/",
  },
  {
    name: "Rikenas gränser",
    detail: "Kartans gränslager omkring 890, 1025 och 1200 bygger på Ottars och Wulfstans berättelser (omkring 890), Adam av Bremen (omkring 1075), Jellingstenen och Frösöstenen, Gutasagan och Äldre Västgötalagen. Gränserna är ungefärliga.",
  },
  {
    name: "Wikimedia Commons",
    detail: "Fotografier av stenarna i artiklarna. Fotograf och licens anges vid varje bild.",
    href: "https://commons.wikimedia.org/",
  },
  {
    name: "Kulturmiljöregistret",
    detail: "Riksantikvarieämbetets register över lämningar (gravfält, gravhögar, färdvägar, broar, fornborgar, hamnar), hämtat via K-samsök.",
    href: "https://www.raa.se/hitta-information/kulturmiljoregistret/",
  },
  {
    name: "Terrain Tiles",
    detail: "Höjddata från Tilezen/Mapzen (Registry of Open Data on AWS), för landskapet kring en sten och den modellerade strandlinjen omkring år 1000.",
    href: "https://registry.opendata.aws/terrain-tiles/",
  },
  {
    name: "K-samsök och OpenStreetMap",
    detail: "Bilder och metadata från svenska kulturarvsinstitutioner (Riksantikvarieämbetet); kartunderlag © OpenStreetMap-bidragsgivare.",
    href: "https://www.openstreetmap.org/copyright",
  },
];

const LICENSES = [
  {
    what: "Programkoden",
    license: "GNU GPL v3",
    text: "Fri att använda, studera, ändra och sprida. Ändrade versioner som sprids ska också vara öppna, märkas som ändrade och bevara upphovsangivelsen (NOTICE, enligt GPL-3.0 § 7).",
  },
  {
    what: "Rundata-uppgifter",
    license: "ODbL / DbCL",
    text: "Får användas fritt med angivande av Samnordisk runtextdatabas som källa. Härledda databaser delas under samma licens.",
  },
  {
    what: "Mätkorpusen",
    license: "CC BY 4.0",
    text: "Mätningarna får användas fritt, även i publikationer, med bidragsgivaren angiven.",
  },
];

function SectionTitle({ eyebrow, title, intro }: { eyebrow: string; title: string; intro?: string }) {
  return (
    <div className="max-w-3xl mb-12">
      <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">{eyebrow}</div>
      <h2 className="text-3xl md:text-4xl font-serif font-bold text-slate-900 tracking-tight">{title}</h2>
      {intro && <p className="mt-4 text-lg text-slate-600 leading-relaxed">{intro}</p>}
    </div>
  );
}

export default async function LandingPage() {
  const articles = await latestArticles();
  return (
    <div className="min-h-screen bg-[#f6f4f1] text-slate-900 overflow-x-hidden">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }} />
      {/* Navigation */}
      <header className="sticky top-0 z-50 bg-[#f6f4f1]/85 backdrop-blur-md border-b border-slate-900/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/vitki_logo.png" alt="" className="w-9 h-9" />
            <span className="text-xl font-bold tracking-tight">Vitki</span>
          </Link>
          <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
            <a href="#artiklar" className="hover:text-slate-900">Artiklar</a>
            <a href="#forskning" className="hover:text-slate-900">För forskningen</a>
            <a href="#appen" className="hover:text-slate-900">Appen</a>
            <a href="#nytt" className="hover:text-slate-900">Vad är nytt</a>
            <a href="#landskap" className="hover:text-slate-900">Nya källor</a>
            <a href="#kallor" className="hover:text-slate-900">Källor</a>
            <a href="#oppen" className="hover:text-slate-900">Öppen källkod</a>
            <Link href={CONTACT_PATH} className="hover:text-slate-900">Kontakt</Link>
          </nav>
          <div className="flex items-center gap-3">
            <LanguageToggle className="px-2.5 py-1 rounded-full border border-slate-300 text-[11px] font-bold tracking-wider text-slate-600 hover:border-slate-900 hover:text-slate-900" />
            <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="px-4 py-2 rounded-full bg-slate-900 text-white text-sm font-bold hover:bg-black">Ladda ner Vitki</a>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div aria-hidden className="absolute inset-0 pointer-events-none select-none">
          <div className="absolute -right-24 -top-10 text-[22rem] leading-none font-serif text-[#b7410e]/[0.06]">ᚱ</div>
          <div className="absolute -left-10 bottom-0 text-[14rem] leading-none font-serif text-slate-900/[0.04]">ᚦ</div>
        </div>
        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#b7410e]/30 bg-white/60 px-3 py-1 text-xs font-bold text-[#b7410e] mb-5">
            Version {VERSION} · Öppen källkod
          </div>
          <p className="mb-8 max-w-2xl font-serif italic text-lg text-slate-600 leading-relaxed">
            Namnet Vitki är fornnordiska och betyder ungefär ”den vise, den kunnige” – i de gamla texterna också den som
            kunde trolldom. Ordet hör ihop med vita, ”veta”.
          </p>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-serif font-bold tracking-tight leading-[1.05] max-w-4xl hyphens-auto break-words" lang="sv">
            En öppen forskningsplattform för runinskrifter
          </h1>
          <p className="mt-6 text-xl text-slate-600 leading-relaxed max-w-3xl">
            Vitki är ett öppet forskningsverktyg för runinskrifter. Det samlar Samnordisk runtextdatabas, statistiska
            modeller i R, 3D-mätning av huggspår och en delad mätkorpus i ett och samma arbetsflöde – från skanningen och
            sökningen till kartan och statistiken.
          </p>
          <p className="mt-4 text-lg text-slate-600 leading-relaxed max-w-3xl">
            Med verktyget kan du följa ett drag – en bön, ett kors, en stavning – genom alla Sveriges vikingatida runstenar,
            se var och när det förekommer, mäta hur djupt och i vilken vinkel runorna är huggna, och pröva vem som ristade
            en sten. Varje resultat redovisas med sin osäkerhet och sin statistiska signifikans, och varje uppgift om en
            inskrift går att spåra till sin källa. Vitki körs på din egen dator och är fritt att ladda ner.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/artiklar" className="px-7 py-3.5 rounded-full bg-[#b7410e] text-white font-bold hover:bg-[#9a350b] shadow-lg shadow-[#b7410e]/20">
              Läs artiklarna
            </Link>
            <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="px-7 py-3.5 rounded-full bg-white border border-slate-300 font-bold hover:border-slate-900">
              Ladda ner Vitki
            </a>
            <a href={METHODS_URL} target="_blank" rel="noopener noreferrer" className="px-7 py-3.5 rounded-full bg-white border border-slate-300 font-bold hover:border-slate-900">
              Metoden
            </a>
          </div>

        </div>
      </section>

      {/* Articles: what the analyses find, told for everyone interested in runestones */}
      <section id="artiklar" className="bg-white border-y border-slate-900/5 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <SectionTitle
            eyebrow="Artiklar"
            title="Runstenarnas dolda mönster"
            intro="Mönster som syns först när man ser alla Sveriges vikingatida runstenar på en gång – vad vi ser, vad det kan betyda och hur det kan prövas."
          />
          <ArticleTeasers posts={articles.posts} photo={articles.photo} />
        </div>
      </section>

      {/* What R is, for readers from the humanities */}
      <section id="r" className="scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <SectionTitle
            eyebrow="Vad är R?"
            title="Statistikverktyget bakom artiklarna"
            intro="Artiklarna bygger på beräkningar i R. Du behöver inte kunna R för att läsa dem – siffrorna förklaras i texten – men så här fungerar det."
          />
          <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-10 items-start">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-8">
              {R_POINTS.map(r => (
                <div key={r.title} className="border-t-2 border-[#b7410e] pt-4">
                  <h3 className="text-lg font-bold">{r.title}</h3>
                  <p className="mt-2 text-slate-600 leading-relaxed">{r.text}</p>
                </div>
              ))}
            </div>
            <div className="rounded-2xl bg-slate-900 text-white p-6">
              <div className="text-xs font-bold uppercase tracking-wider text-[#f0a37f]">Så ser R ut</div>
              <pre className="mt-3 whitespace-pre overflow-x-auto text-sm leading-relaxed font-mono text-slate-100" translate="no">
{`# Andelen stenar med en bön,
# stilgrupp för stilgrupp
andel <- tapply(stenar$bon,
                stenar$stilgrupp,
                mean)`}
              </pre>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                Raden säger: ta uppgiften om bön för varje sten (1 för ja, 0 för nej), dela upp stenarna efter stilgrupp och
                räkna medelvärdet i varje grupp – det blir andelen stenar med en bön. Raderna som börjar med # är
                kommentarer för människor; datorn hoppar över dem.
              </p>
              <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                Alla Vitkis R-skript finns öppet på{" "}
                <a href={GITHUB} target="_blank" rel="noopener noreferrer" className="underline hover:text-white">GitHub</a>,
                och i appen kan varje analys laddas ner som ett paket med skript och data.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Research value */}
      <section id="forskning" className="scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <SectionTitle
            eyebrow="För forskningen"
            title="Vad plattformen kan hjälpa till med"
            intro="Vitki ersätter inte runologens bedömning. Den ger mätbara, granskningsbara underlag att pröva hypoteser mot."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-10 gap-y-10">
            {USE_CASES.map(u => (
              <div key={u.title} className="border-t-2 border-[#b7410e] pt-5">
                <h3 className="text-lg font-bold">{u.title}</h3>
                <p className="mt-2 text-slate-600 leading-relaxed">{u.text}</p>
              </div>
            ))}
          </div>

          <div className="mt-20 rounded-3xl bg-slate-900 text-white p-10 md:p-12">
            <h3 className="text-2xl font-serif font-bold">Så arbetar vi</h3>
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">
              {PRINCIPLES.map(p => (
                <div key={p.title}>
                  <div className="font-bold text-[#f0a37f]">{p.title}</div>
                  <p className="mt-1.5 text-slate-300 leading-relaxed">{p.text}</p>
                </div>
              ))}
            </div>
            <p className="mt-8 text-sm text-slate-400">
              Alla beräkningar beskrivs i{" "}
              <a href={`${GITHUB}/blob/main/METHODS.md`} target="_blank" rel="noopener noreferrer" className="underline hover:text-white">METHODS.md</a>.
            </p>
          </div>
        </div>
      </section>

      {/* What is new */}
      {/* The app in pictures, and the 3D scans */}
      <section id="appen" className="bg-white border-y border-slate-900/5 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <SectionTitle
            eyebrow="Appen"
            title="Så ser Vitki ut"
            intro="Vitki körs på din egen dator. Här är några av vyerna – och vad de gör."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-14">
            {APP_VIEWS.map(v => (
              <figure key={v.src}>
                <ZoomImage src={v.src} alt={`Skärmbild från Vitki: ${v.title.toLowerCase()}`} width={1600} height={1000} className="w-full h-auto"
                  frameClassName="rounded-2xl overflow-hidden border border-slate-900/10 shadow-lg shadow-slate-900/5 hover:shadow-xl transition-shadow bg-[#eef0f3]" />
                <figcaption className="mt-4">
                  <h3 className="text-lg font-bold">{v.title}</h3>
                  <p className="mt-1.5 text-slate-600 leading-relaxed">{v.text}</p>
                </figcaption>
              </figure>
            ))}
          </div>

          <div className="mt-24">
            <div className="max-w-3xl mb-10">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">3D-analys</div>
              <h3 className="text-2xl md:text-3xl font-serif font-bold text-slate-900 tracking-tight">Runorna i millimeter</h3>
              <p className="mt-4 text-lg text-slate-600 leading-relaxed">
                Vitki mäter huggspåren i 3D-skanningar av runstenar. Exemplen kommer från Sö 113 i Södermanland, som vi har
                analyserat i en av våra studier.
              </p>
            </div>
            <figure>
              <ZoomImage src="/bilder/skanning-so113-djupkarta.webp" alt="Djupkarta över runstenen Sö 113: runorna framträder i rött och violett mot den ljusa stenytan"
                width={1393} height={769} className="w-full h-auto" frameClassName="rounded-2xl overflow-hidden border border-slate-900/10 bg-white" />
              <figcaption className="mt-4 max-w-3xl">
                <h4 className="text-lg font-bold">Djupkartan</h4>
                <p className="mt-1.5 text-slate-600 leading-relaxed">
                  Varje punkt på stenen färgad efter hur djupt den ligger under stenytan, från ljust vid ytan till mörkt fem
                  millimeter ner. Runorna träder fram som en värmekarta – också där de är svåra att se med blotta ögat.
                </p>
              </figcaption>
            </figure>
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
              {SCANS.map(sc => (
                <figure key={sc.src}>
                  <ZoomImage src={sc.src} alt={`Sö 113: ${sc.title.toLowerCase()}`} className="w-full h-auto"
                    frameClassName="rounded-xl overflow-hidden border border-slate-900/10 bg-white" />
                  <figcaption className="mt-3">
                    <h4 className="font-bold">{sc.title}</h4>
                    <p className="mt-1 text-sm text-slate-600 leading-relaxed">{sc.text}</p>
                  </figcaption>
                </figure>
              ))}
            </div>
            <p className="mt-10 text-xs text-slate-500 leading-relaxed">
              3D-skanning av Sö 113: Laila Kitzler Åhfeldt (2024), <em>3D-data Runstenar i Södermanland</em>, Zenodo,{" "}
              <a href={SCAN_CREDIT} target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-900">doi:10.5281/zenodo.11951255</a>,
              CC BY 4.0. Bearbetning och mätning: Vitki.
            </p>
          </div>
        </div>
      </section>

      <section id="nytt" className="scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <SectionTitle
            eyebrow="Vad är nytt"
            title="Det här tillför Vitki"
            intro="Plattformen står på axlarna av flera decenniers runologisk forskning. Det nya är framför allt öppenheten och att metoderna kombineras i samma verktyg."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {NEW_THINGS.map((n, i) => (
              <div key={n.title} className="rounded-2xl bg-[#fbfaf8] border border-slate-200 p-7">
                <div className="text-4xl font-serif font-bold text-[#b7410e]/30">{String(i + 1).padStart(2, "0")}</div>
                <h3 className="mt-2 text-xl font-bold">{n.title}</h3>
                <p className="mt-2 text-slate-600 leading-relaxed">{n.text}</p>
              </div>
            ))}
          </div>
          <div className="mt-12 max-w-3xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">Vi bygger vidare på</h3>
            <ul className="space-y-2 text-slate-600 leading-relaxed list-disc pl-5">
              {RELATED.map(r => <li key={r}>{r}</li>)}
            </ul>
          </div>
        </div>
      </section>

      {/* New sources: the stones in their landscape */}
      <section id="landskap" className="bg-white border-y border-slate-900/5 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <SectionTitle
            eyebrow="Nya källor"
            title="Stenarna i sitt landskap"
            intro="Runtexterna säger vem som reste stenen och varför. Öppna data om fornlämningar, terräng och strandlinjer visar var – och gör det möjligt att se mönster som ingen kunnat räkna på förut."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {LANDSCAPE.map(l => (
              <div key={l.title} className="rounded-2xl bg-white border border-slate-200 p-7">
                <div className="text-xs font-bold uppercase tracking-wider text-[#b7410e]">{l.source}</div>
                <h3 className="mt-2 text-xl font-bold">{l.title}</h3>
                <p className="mt-2 text-slate-600 leading-relaxed">{l.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sources */}
      <section id="kallor" className="scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <SectionTitle
            eyebrow="Källor"
            title="Vad vi lutar oss mot"
            intro="Data och metoder har namngivna källor. När uppgifter ur Rundata används i plattformen anges källan, och den ska anges även i publikationer."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {SOURCES.map(s => (
              <div key={s.name} className="rounded-2xl bg-white border border-slate-200 p-5">
                <div className="font-bold text-slate-900">
                  {s.href ? (
                    <a href={s.href} target="_blank" rel="noopener noreferrer" className="hover:text-[#b7410e]">{s.name} ↗</a>
                  ) : s.name}
                </div>
                <p className="mt-1.5 text-sm text-slate-600 leading-relaxed">{s.detail}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-sm text-slate-500 max-w-3xl">
            AI-funktionerna använder som standard Claude (Anthropic); Google Gemini kan väljas under Inställningar. Du
            använder din egen API-nyckel, som sparas i din webbläsare. AI läser bilder och skriver löptext; texten märks
            och ska granskas, och den används aldrig som källa till mätvärden, statistik eller sannolikheter.
          </p>
        </div>
      </section>

      {/* Open source */}
      <section id="oppen" className="bg-slate-900 text-white scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <div className="max-w-3xl mb-12">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#f0a37f] mb-3">Öppen källkod</div>
            <h2 className="text-3xl md:text-4xl font-serif font-bold tracking-tight">Fri att använda, granska och vidareutveckla</h2>
            <p className="mt-4 text-lg text-slate-300 leading-relaxed">
              Forskning mår bäst av öppenhet. Hela källkoden finns på GitHub, och du får bygga vidare på den för egna
              forskningsfrågor – så länge förbättringarna förblir lika öppna för nästa forskare.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {LICENSES.map(l => (
              <div key={l.what} className="rounded-2xl border border-white/15 bg-white/5 p-6">
                <div className="text-sm text-slate-400 font-semibold">{l.what}</div>
                <div className="mt-1 text-2xl font-serif font-bold">{l.license}</div>
                <p className="mt-3 text-slate-300 leading-relaxed text-[15px]">{l.text}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-bold">Bidra</h3>
              <ul className="mt-3 space-y-2 text-slate-300 leading-relaxed list-disc pl-5">
                <li>Dela mätningar i den gemensamma korpusen direkt från 3D-analysen.</li>
                <li>Rapportera fel och önskemål som issues på GitHub.</li>
                <li>Föreslå förbättringar av kod eller metod med en pull request – metoderna dokumenteras i METHODS.md och testas automatiskt.</li>
              </ul>
              <a href={GITHUB} target="_blank" rel="noopener noreferrer"
                className="mt-6 inline-block px-6 py-3 rounded-full bg-white text-slate-900 font-bold hover:bg-slate-100">
                Källkoden på GitHub
              </a>
            </div>
            <div>
              <h3 className="text-lg font-bold">Citera</h3>
              <p className="mt-3 text-slate-300">Använder du plattformen i forskning, citera programvaran och de datakällor du använt:</p>
              <pre className="mt-3 whitespace-pre-wrap rounded-xl bg-black/30 border border-white/10 p-4 text-sm text-slate-200 font-mono">
{`Kvant, V. (2026). Vitki:
öppen plattform för analys av runinskrifter
(version ${VERSION}). https://vitkirunor.se

Samnordisk runtextdatabas. Institutionen för nordiska
språk, Uppsala universitet.`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* The founder and the licence */}
      <section id="om" className="bg-white border-b border-slate-900/5 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-20 grid grid-cols-1 md:grid-cols-2 gap-12">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Om grundaren</div>
            <h2 className="text-2xl md:text-3xl font-serif font-bold text-slate-900 tracking-tight">Viktor Kvant</h2>
            <p className="mt-4 text-slate-600 leading-relaxed">
              Projektet är grundat av{" "}
              <a href="https://www.linkedin.com/in/viktor-kvant-555180108/" target="_blank" rel="noopener noreferrer" className="font-semibold text-slate-800 hover:text-[#b7410e]">Viktor Kvant</a>.
              Till vardags arbetar Viktor som digital analytiker, men ser dataanalys som ett övergripande yrkesfält där samma
              analytiska metoder, AI-modeller och tekniker kan appliceras för att driva gränserna framåt även inom humaniora
              och arkeologi.
            </p>
            <p className="mt-4 text-slate-600 leading-relaxed">
              Frågor, rättelser eller idéer om samarbete?{" "}
              <Link href={CONTACT_PATH} className="font-semibold text-[#b7410e] hover:underline">Skriv till Viktor</Link>.
            </p>
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e] mb-3">Licens</div>
            <h2 className="text-2xl md:text-3xl font-serif font-bold text-slate-900 tracking-tight">GPL-3.0 med tilläggsvillkor</h2>
            <p className="mt-4 text-slate-600 leading-relaxed">Copyright © 2026 Viktor Kvant.</p>
            <p className="mt-3 text-slate-600 leading-relaxed">
              Detta projekt är släppt under GNU General Public License v3.0 (GPL-3.0) med tilläggsvillkor enligt licensens § 7,
              se <a href={`${GITHUB}/blob/main/NOTICE`} target="_blank" rel="noopener noreferrer" className="underline hover:text-[#b7410e]">NOTICE</a>.
              Du är fri att använda, ändra och distribuera koden, förutsatt att ändringar också släpps under samma licens och att
            </p>
            <ul className="mt-3 space-y-2 text-slate-600 leading-relaxed list-disc pl-5">
              <li>upphovsangivelsen <q translate="no">Bygger på Vitki, ursprungligen utvecklad av Viktor Kvant (https://github.com/Precatio/runes)</q> bevaras i källkoden och syns i användargränssnittet (§ 7 b),</li>
              <li>ingen framställer kodbasen eller grunden för den som sitt eget verk, och ändrade versioner märks som ändrade (§ 7 c), och</li>
              <li>en ändrad version inte ges ut under namnet Vitki, utan som <q translate="no">baserad på Vitki</q> (§ 7 e).</li>
            </ul>
            <p className="mt-3 text-slate-600 leading-relaxed">
              Se <a href={`${GITHUB}/blob/main/LICENSE`} target="_blank" rel="noopener noreferrer" className="underline hover:text-[#b7410e]">LICENSE</a> för
              licenstexten och <a href={`${GITHUB}/blob/main/NOTICE`} target="_blank" rel="noopener noreferrer" className="underline hover:text-[#b7410e]">NOTICE</a> för
              tilläggsvillkoren. Använder du programmet i forskning, citera det enligt{" "}
              <a href={`${GITHUB}/blob/main/CITATION.cff`} target="_blank" rel="noopener noreferrer" className="underline hover:text-[#b7410e]">CITATION.cff</a>.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section id="kom-igang" className="max-w-6xl mx-auto px-6 py-20 text-center scroll-mt-16">
        <h2 className="text-3xl font-serif font-bold">Kör Vitki på din egen dator</h2>
        <p className="mt-3 text-slate-600 max-w-2xl mx-auto">
          Vitki är öppen källkod. Ladda ner den från GitHub och gör om analyserna i artiklarna – mönsterkartan, R-modellerna,
          Rundata och 3D-mätningen – med samma data, eller pröva dina egna frågor.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <a href={DOWNLOAD_URL} target="_blank" rel="noopener noreferrer" className="px-7 py-3.5 rounded-full bg-[#b7410e] text-white font-bold hover:bg-[#9a350b]">Ladda ner från GitHub</a>
          <a href={METHODS_URL} target="_blank" rel="noopener noreferrer" className="px-7 py-3.5 rounded-full bg-white border border-slate-300 font-bold hover:border-slate-900">Läs metoden</a>
          <Link href="/artiklar" className="px-7 py-3.5 rounded-full bg-white border border-[#b7410e]/40 text-[#9a350b] font-bold hover:border-[#b7410e]">Läs artiklarna</Link>
        </div>
        <SiteVote />
      </section>

      <footer className="border-t border-slate-900/10">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row gap-4 justify-between text-sm text-slate-500">
          <div>
            Vitki · Grundat av{" "}
            <a href="https://www.linkedin.com/in/viktor-kvant-555180108/" target="_blank" rel="noopener noreferrer" className="font-semibold text-slate-700 hover:text-[#b7410e]">Viktor Kvant</a>
          </div>
          <div className="flex flex-wrap items-center gap-5">
            <Link href={CONTACT_PATH} className="hover:text-slate-900">Kontakt</Link>
            <a href={DOCS_URL} target="_blank" rel="noopener noreferrer" className="hover:text-slate-900">Dokumentation</a>
            <a href={GITHUB} target="_blank" rel="noopener noreferrer" className="hover:text-slate-900">GitHub</a>
            <span>GPL-3.0</span>
            <StatsNote />
          </div>
        </div>
      </footer>
      <LocalAppLink className="fixed bottom-4 right-4 z-50 inline shadow-lg bg-white" />
    </div>
  );
}
