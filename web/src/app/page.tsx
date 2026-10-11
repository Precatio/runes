/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vitki – öppen forskningsplattform för runinskrifter",
  description:
    "Från 3D-skanning till artikel: huggspårsanalys, Samnordisk runtextdatabas, statistiska modeller i R, ortografisk " +
    "stilometri, tolkade fynd mot befintlig forskning och en delad mätkorpus – med redovisad osäkerhet och statistisk " +
    "signifikans. Öppen källkod under GPL-3.0.",
};

const GITHUB = "https://github.com/Precatio/runes";

const STATS = [
  { value: "6 753", label: "inskrifter ur Samnordisk runtextdatabas" },
  { value: "2 321", label: "svenska vikingatida runstenar i nio statistiska analyser i R" },
  { value: "±0,6°", label: "vinkelfel på syntetiska stenar med kända spår" },
  { value: "60 %", label: "rätt ristare först i ortografiskt test (slump 4 %)" },
];

// The full stone analysis (/stenanalys), step by step
const WORKFLOW = [
  { step: "Skanningen", text: "STL, OBJ eller PLY laddas upp; signum hämtas ur filnamnet och stenen ur Rundata." },
  { step: "Bilder", text: "Relief, djupkarta och strykljus ur fyra riktningar räknas ur skanningen." },
  { step: "Huggspåren", text: "Bara spår som känns igen som runor mäts, enligt Vitki-protokollet, med känslighetsanalys." },
  { step: "Bild och läsning", text: "Stilgrupp ur bilden och blinda läsningar i flera orienteringar, prövade mot Rundata." },
  { step: "Syntes", text: "Rundata, ortografi, huggteknik och modellen vägs samman; motsägelser redovisas." },
  { step: "Statistik i R", text: "Stenen mot korpusen: modell, grupp, seriation, landskap och sikt." },
  { step: "Rapporten", text: "En artikel med figurer ur skanningen och en bilaga om hur analysen gjordes." },
];

const FEATURE_GROUPS = [
  {
    title: "Mäta",
    items: [
      {
        name: "Fullständig stenanalys",
        href: "/stenanalys",
        text: "En skanning och ett signum in, en artikel ut. Alla steg nedan körs i följd med samma metoder som de enskilda verktygen, och varje steg redovisas – också det som misslyckades.",
      },
      {
        name: "3D-huggspårsanalys",
        href: "/3d",
        text: "V-vinkel, asymmetri, djup, bredd, bottenradie och ytråhet i STL-, OBJ- och PLY-skanningar – manuellt, med ett klick per snitt eller automatiskt. Den automatiska analysen mäter bara runor (mätmetod groove-5) och anger om stenen har tillräckligt många: 10 runor för att beskriva en sten, 20 för att jämföra. Full proveniens och export till CSV eller JSON.",
      },
      {
        name: "Strykljus och RTI",
        href: "/rti",
        text: "Flytta ljuset fritt över 3D-modellen eller över en PTM-fil, med \"diffuse gain\"-förstärkning för att få fram svaga och vittrade ristningar.",
      },
      {
        name: "Språk och läsning",
        href: "/phonetics",
        text: "Blind AI-läsning av runorna från foto, RTI-vy eller relief, prövad mot Rundata utan AI: vad som stämmer, vad som skiljer, vilka ordformer som är belagda och om läsningen bara återger en känd text.",
      },
      {
        name: "2D-paleografi",
        href: "/2d",
        text: "AI-stöd för stilgrupp och runformer, märkt som okalibrerad bedömning. Runorna klipps ut automatiskt, jämförs med samma runa på andra stenar och kopplas till spårmåtten.",
      },
    ],
  },
  {
    title: "Söka och jämföra",
    items: [
      {
        name: "Inskrifter (Rundata)",
        href: "/inskrifter",
        text: "Hela Samnordisk runtextdatabas inbyggd: translitterering, normalisering, översättning, datering, stilgrupp, ristare och plats för varje inskrift.",
      },
      {
        name: "Ortografisk stilometri",
        href: "/inskrifter?signum=U%20729",
        text: "Stavning, skiljetecken och bindrunor jämförs med alla vikingatida inskrifter. Ger mest lika inskrifter och ristare, med p-värde justerat för att den bästa av alla ristare valts och metodens träffsäkerhet.",
      },
      {
        name: "Språkdrag och inskrifternas syfte",
        href: "/luckor",
        text: "Tjugo drag i ljud, stavning, språkbruk och skrift per ristare, jämförda med landskapets övriga stenar – och vad inskrifterna handlar om: minne, bro, bön, utlandsfärd, magiska formler.",
      },
      {
        name: "Bergart och berggrund",
        href: "/inskrifter?signum=%C3%96l%201",
        text: "Stenens material jämförs med SGU:s berggrundskarta där den står och med bergarterna på ristarens stenar – en ledtråd om flyttblock och transport.",
      },
      {
        name: "Jämför stenar",
        href: "/jamfor",
        text: "Huggspåren runa mot runa, permutationstest för varje mått och alla samtidigt, effektstorlek och om skillnaden är statistiskt säkerställd – och ristare, stil, stavning och språkdrag när stenarna har signum.",
      },
      {
        name: "Karta och stilgrupper",
        href: "/karta",
        text: "Geografisk spridning efter period, stilgrupp, ristare och innehåll. Gräslunds stilkronologi med fördelningen i Rundata.",
      },
    ],
  },
  {
    title: "Statistik och tolkning",
    items: [
      {
        name: "Statistik i R",
        href: "/statistik",
        text: "Nio analyser av alla svenska vikingatida runstenar: en attribueringsmodell prövad på socknar den aldrig sett, ristarnas områden, stavning och avstånd, seriation mot Gräslunds kronologi, förändring i tid och rum, ordnätverk och grupper av stenar som kan vara namnlösa ristare. Varje svar med fråga, tolkning och vad det inte säger.",
      },
      {
        name: "Forskningsluckor",
        href: "/luckor",
        text: "Appens resultat mot Rundata – stämmer, nytt eller motsäger – med en tolkning för varje fynd (starkt, måttligt, svagt) som väger alla belägg och stäms av mot Runor 2020 och Wikidata. Och var uppgifter saknas och vilka stenar som behöver mätas.",
      },
      {
        name: "Stenöversikt",
        href: "/oversikt",
        text: "Varje runsten med stödet för Rundatas ristare, det starkaste alternativet och en status, kontrollerad mot de signerade stenarna så att man ser hur ofta markeringarna slår fel.",
      },
      {
        name: "Syntes och attribuering",
        href: "/synthesis",
        text: "Väger samman Rundata, ortografi, huggteknik och R-modellen efter metodernas träffsäkerhet och prövar varje kandidat mot geografi, stilgrupper, bergart, språkdrag och sten mot sten. Motsägelser redovisas.",
      },
    ],
  },
  {
    title: "Samarbeta och publicera",
    items: [
      {
        name: "Delad mätkorpus",
        href: "/korpus",
        text: "Forskare publicerar sina huggspårsmätningar under CC BY 4.0. Korpusen blir referens för attribuering, ristarprofiler och klustring, och varje mätning anger sin kvalitet.",
      },
      {
        name: "Rapporter",
        href: "/rapporter",
        text: "Stenrapporten i elva publiceringsformer – tidskriftsartikel, uppsats, avhandlingskapitel, runologisk utgåva, poster, blogginlägg och fler – med figurer ur skanningen, läsning och attribuering. Export till Word, LaTeX och Markdown.",
      },
    ],
  },
];

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
    text: "Uppgifter om inskrifter hämtas ur Samnordisk runtextdatabas och anges med källa – AI:n får inte gissa signum, texter eller ristare.",
  },
  {
    title: "Prövat mot det modellen inte sett",
    text: "Varje statistisk modell valideras med korsvalidering, också på socknar och härader den aldrig sett, och dess sannolikheter kontrolleras mot hur ofta den har rätt.",
  },
  {
    title: "Osäkerhet och signifikans redovisas",
    text: "Mätvärden visas med spridning, andelar med konfidensintervall. P-värden justeras för många test och för hur hypotesen valdes, och det som är statistiskt säkerställt märks tydligt.",
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
    href: "https://app.raa.se/open/runor/",
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
    name: "Kitzler Åhfeldt, L. 2024",
    detail: "3D-data Runstenar i Södermanland och andra serier [Dataset]. Riksantikvarieämbetet. Zenodo, CC BY 4.0.",
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

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#f6f4f1] text-slate-900 overflow-x-hidden">
      {/* Navigation */}
      <header className="sticky top-0 z-50 bg-[#f6f4f1]/85 backdrop-blur-md border-b border-slate-900/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/vitki_logo.png" alt="" className="w-9 h-9" />
            <span className="text-xl font-bold tracking-tight">Vitki</span>
          </Link>
          <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
            <a href="#arbetsgang" className="hover:text-slate-900">Arbetsgång</a>
            <a href="#funktioner" className="hover:text-slate-900">Funktioner</a>
            <a href="#forskning" className="hover:text-slate-900">För forskningen</a>
            <a href="#nytt" className="hover:text-slate-900">Vad är nytt</a>
            <a href="#kallor" className="hover:text-slate-900">Källor</a>
            <a href="#oppen" className="hover:text-slate-900">Öppen källkod</a>
          </nav>
          <div className="flex items-center gap-3">
            <a href={GITHUB} target="_blank" rel="noopener noreferrer" className="hidden sm:inline text-sm font-semibold text-slate-600 hover:text-slate-900">GitHub</a>
            <Link href="/start" className="px-4 py-2 rounded-full bg-slate-900 text-white text-sm font-bold hover:bg-black">Öppna appen</Link>
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
          <div className="inline-flex items-center gap-2 rounded-full border border-[#b7410e]/30 bg-white/60 px-3 py-1 text-xs font-bold text-[#b7410e] mb-8">
            Version 2.0 · Öppen källkod
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-serif font-bold tracking-tight leading-[1.05] max-w-4xl hyphens-auto break-words" lang="sv">
            En öppen forskningsplattform för runinskrifter
          </h1>
          <p className="mt-6 text-xl text-slate-600 leading-relaxed max-w-2xl">
            Vitki samlar 3D-mätning av huggspår, Samnordisk runtextdatabas, statistiska modeller i R och en delad
            mätkorpus i ett och samma verktyg – från skanning till artikel, med redovisad osäkerhet, statistisk
            signifikans och verifierbara källor.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/start" className="px-7 py-3.5 rounded-full bg-[#b7410e] text-white font-bold hover:bg-[#9a350b] shadow-lg shadow-[#b7410e]/20">
              Öppna appen
            </Link>
            <Link href="/stenanalys" className="px-7 py-3.5 rounded-full bg-white border border-slate-300 font-bold hover:border-slate-900">
              Analysera en sten
            </Link>
          </div>

          <dl className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-900/10 rounded-2xl overflow-hidden border border-slate-900/10">
            {STATS.map(s => (
              <div key={s.label} className="bg-white/80 p-6">
                <dt className="sr-only">{s.label}</dt>
                <dd className="text-2xl sm:text-3xl font-serif font-bold text-slate-900 whitespace-nowrap">{s.value}</dd>
                <dd className="mt-1 text-sm text-slate-600 leading-snug">{s.label}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 text-xs text-slate-500">
            Ortografisk träffsäkerhet: lämna-en-ute-test på 135 signerade vikingatida inskrifter i Rundata, 27 ristare.
            Vinkelfelet: syntetiska V-spår med öppningsvinkel 50–110° (METHODS.md, avsnitt 1).
          </p>
        </div>
      </section>

      {/* Workflow: the full stone analysis */}
      <section id="arbetsgang" className="scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 pb-24">
          <SectionTitle
            eyebrow="Arbetsgång"
            title="En skanning in, en artikel ut"
            intro="Fullständig stenanalys kör hela kedjan i följd. Varje steg använder samma metod som det enskilda verktyget, och rapporten får en bilaga om hur analysen gjordes."
          />
          <ol className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-px bg-slate-900/10 rounded-2xl overflow-hidden border border-slate-900/10">
            {WORKFLOW.map((w, i) => (
              <li key={w.step} className="bg-white/80 p-5">
                <div className="text-3xl font-serif font-bold text-[#b7410e]/40">{i + 1}</div>
                <div className="mt-1 font-bold text-slate-900">{w.step}</div>
                <p className="mt-1.5 text-sm text-slate-600 leading-snug">{w.text}</p>
              </li>
            ))}
          </ol>
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <Link href="/stenanalys" className="px-6 py-3 rounded-full bg-slate-900 text-white font-bold hover:bg-black">Starta en stenanalys</Link>
            <span className="text-sm text-slate-500">AI-stegen använder din egen API-nyckel; resten fungerar utan.</span>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="funktioner" className="bg-white border-y border-slate-900/5 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <SectionTitle
            eyebrow="Funktioner"
            title="Från skanning till publicerbart resultat"
            intro="Verktygen hänger ihop: en mätning i 3D kan jämföras med korpusen, vägas mot Rundata och ortografin och bli en rapport med källor och metod."
          />
          <div className="space-y-14">
            {FEATURE_GROUPS.map(group => (
              <div key={group.title}>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-5">{group.title}</h3>
                <div className={`grid grid-cols-1 md:grid-cols-2 gap-5 ${group.items.length % 3 === 0 ? "lg:grid-cols-3" : ""}`}>
                  {group.items.map(f => (
                    <Link key={f.name} href={f.href} className="group rounded-2xl border border-slate-200 bg-[#fbfaf8] p-6 hover:border-[#b7410e]/50 hover:shadow-lg transition-all">
                      <div className="flex items-center justify-between">
                        <h4 className="text-lg font-bold text-slate-900">{f.name}</h4>
                        <span className="text-[#b7410e] opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                      </div>
                      <p className="mt-2 text-[15px] text-slate-600 leading-relaxed">{f.text}</p>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
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
      <section id="nytt" className="bg-white border-y border-slate-900/5 scroll-mt-16">
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
(version 2.0.0). https://vitkirunor.se

Samnordisk runtextdatabas. Institutionen för nordiska
språk, Uppsala universitet.`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl font-serif font-bold">Börja med en inskrift, en skanning eller en fråga</h2>
        <p className="mt-3 text-slate-600">Rundata, kartan och stilgrupperna är öppna direkt. Logga in för att spara projekt och använda korpusen.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link href="/start" className="px-7 py-3.5 rounded-full bg-[#b7410e] text-white font-bold hover:bg-[#9a350b]">Öppna appen</Link>
          <Link href="/inskrifter" className="px-7 py-3.5 rounded-full bg-white border border-slate-300 font-bold hover:border-slate-900">Sök i Rundata</Link>
        </div>
      </section>

      <footer className="border-t border-slate-900/10">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row gap-4 justify-between text-sm text-slate-500">
          <div>
            Vitki · Grundat av{" "}
            <a href="https://www.linkedin.com/in/viktor-kvant-555180108/" target="_blank" rel="noopener noreferrer" className="font-semibold text-slate-700 hover:text-[#b7410e]">Viktor Kvant</a>
          </div>
          <div className="flex gap-5">
            <Link href="/docs" className="hover:text-slate-900">Dokumentation</Link>
            <a href={GITHUB} target="_blank" rel="noopener noreferrer" className="hover:text-slate-900">GitHub</a>
            <span>GPL-3.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
