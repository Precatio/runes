/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vitki AI – öppen forskningsplattform för runinskrifter",
  description:
    "3D-huggspårsanalys med redovisad osäkerhet, Samnordisk runtextdatabas, ortografisk stilometri, delad mätkorpus, " +
    "jämförelse av stenar, kartor, stilgrupper och RTI – öppen källkod under GPL-3.0.",
};

const GITHUB = "https://github.com/Precatio/runes";

const STATS = [
  { value: "6 753", label: "inskrifter ur Samnordisk runtextdatabas" },
  { value: "±0,6°", label: "vinkelfel på syntetiska stenar med kända spår" },
  { value: "60 %", label: "rätt ristare först i ortografisk test (slump 4 %)" },
  { value: "GPL-3.0", label: "fri och öppen källkod" },
];

const FEATURE_GROUPS = [
  {
    title: "Mäta",
    items: [
      {
        name: "3D-huggspårsanalys",
        href: "/3d",
        text: "V-vinkel, asymmetri, djup, bredd, bottenradie och ytråhet i STL-, OBJ- och PLY-skanningar – manuellt, med ett klick per snitt eller helt automatiskt med granskning. Runor och ornamentik mäts separat, med spridning per snitt. Strykljus, relief och djup räknas direkt ur skanningen. Full proveniens (filens SHA-256, parametrar, metodversion) och export till CSV eller JSON.",
      },
      {
        name: "Strykljus och RTI",
        href: "/rti",
        text: "Flytta ljuset fritt över 3D-modellen eller över en PTM-fil, med \"diffuse gain\"-förstärkning för att få fram svaga och vittrade ristningar.",
      },
      {
        name: "Språk och läsning",
        href: "/phonetics",
        text: "Blind AI-läsning av runorna från foto, RTI-vy eller relief, jämförd med Rundata utan AI: vad som stämmer, vad som skiljer och vilka ordformer som är belagda.",
      },
      {
        name: "2D-paleografi",
        href: "/2d",
        text: "AI-stöd för stilgrupp och runformer – märkt som okalibrerad bedömning. Runutsnitt jämförs med samma runa på andra stenar och kopplas till spårmåtten.",
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
        text: "Stavning, skiljetecken och bindrunor jämförs med alla vikingatida inskrifter. Ger mest lika inskrifter och ristare – med p-värde och metodens träffsäkerhet redovisade.",
      },
      {
        name: "Språkdrag och inskrifternas syfte",
        href: "/luckor",
        text: "Fonetisk stil och språkbruk per ristare, och vad inskrifterna handlar om – minne, bro, bön, utlandsfärd, magiska formler – med test mot genomsnittet.",
      },
      {
        name: "Bergart och berggrund",
        href: "/inskrifter?signum=%C3%96l%201",
        text: "Stenens material jämförs med SGU:s berggrundskarta där den står och med bergarterna på ristarens stenar – en ledtråd om flyttblock och transport.",
      },
      {
        name: "Jämför stenar",
        href: "/jamfor",
        text: "Permutationstest mått för mått och för alla mått samtidigt, effektstorlek och överlagrade tvärsnittsprofiler.",
      },
      {
        name: "Karta och stilgrupper",
        href: "/karta",
        text: "Geografisk spridning efter period, stilgrupp och ristare. Gräslunds stilkronologi med fördelningen i Rundata.",
      },
    ],
  },
  {
    title: "Samarbeta och publicera",
    items: [
      {
        name: "Delad mätkorpus",
        href: "/korpus",
        text: "Forskare publicerar sina huggspårsmätningar under CC BY 4.0. Korpusen blir referens för attribuering, ristarprofiler och klustring.",
      },
      {
        name: "Syntes och attribuering",
        href: "/synthesis",
        text: "Väger samman Rundata, ortografi och huggteknik efter metodernas träffsäkerhet och prövar varje kandidat mot geografi, stilgrupper, bergart, språkdrag och sten mot sten. Motsägelser redovisas.",
      },
      {
        name: "Forskningsluckor",
        href: "/luckor",
        text: "Var saknas uppgifter, vad säger appens resultat jämfört med befintlig forskning – stämmer, nytt eller motsäger – och vilka stenar behöver mätas?",
      },
      {
        name: "Rapporter",
        href: "/rapporter",
        text: "Stenrapport i artikelform enligt runologisk praxis, med figurer räknade ur skanningen, läsning och attribuering. Export till Word, LaTeX och Markdown.",
      },
    ],
  },
];

const USE_CASES = [
  {
    title: "Ristarattribuering",
    text: "Pröva en attribuering mot litteraturens uppgifter i Rundata, inskriftens ortografi och den uppmätta huggtekniken – och kontrollera geografi, stilgrupp, bergart, språkdrag och inskriftstyp.",
  },
  {
    title: "Läsning av skadade inskrifter",
    text: "Strykljus och relief ur 3D-skanningen och RTI-förstärkning gör grunda eller vittrade ristningar läsbara; en blind läsning kan jämföras med Rundata ord för ord.",
  },
  {
    title: "Datering och stil",
    text: "Se en inskrifts stilgrupp i relation till Gräslunds kronologi och hur stilen fördelar sig geografiskt och mellan ristare.",
  },
  {
    title: "Reproducerbara mätningar",
    text: "Samma fil och samma parametrar ger samma resultat. Proveniensen gör att en annan forskare kan upprepa och granska mätningen.",
  },
  {
    title: "Gemensamt referensmaterial",
    text: "Varje mätning som delas gör attribueringen säkrare för alla. Bidragsgivare anges alltid.",
  },
  {
    title: "Undervisning",
    text: "Studenter kan utforska Rundata, kartor och stilgrupper och se hur kvantitativa metoder fungerar – och var deras gränser går.",
  },
];

const PRINCIPLES = [
  {
    title: "Verifierbara källor",
    text: "Uppgifter om inskrifter hämtas ur Samnordisk runtextdatabas och anges med källa – AI:n får inte gissa signum, texter eller ristare.",
  },
  {
    title: "Osäkerhet redovisas",
    text: "Mätvärden visas med spridning och antal snitt. Statistiska metoder redovisar korsvaliderad träffsäkerhet och p-värden, justerade för många test.",
  },
  {
    title: "Ingen AI-statistik",
    text: "Kandidater räknas fram ur beläggen med öppna vikter. AI skriver löptext och läser bilder, anger aldrig sannolikheter, och dess bedömningar märks som okalibrerade.",
  },
  {
    title: "Tumregler kallas tumregler",
    text: "Verktygsklassningen och vittringsjusteringen är inte kalibrerade och märks tydligt som heuristik.",
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
    title: "En delad, öppen mätkorpus",
    text: "Mätningar från olika forskare samlas med licens och bidragsgivare, och ristare kopplas automatiskt via Rundata. Det gör jämförelser möjliga mellan projekt och regioner.",
  },
  {
    title: "Flera oberoende belägg i samma analys",
    text: "Litteraturens attribuering, ortografi och huggteknik vägs samman öppet, och kandidaterna prövas mot geografi, stil, bergart och språkdrag. Varje kandidat visar exakt vilka belägg som stöder eller talar emot den.",
  },
];

const RELATED = [
  "Laila Kitzler Åhfeldts 3D-baserade analyser av huggteknik (Stockholms universitet), som vår metod för separata spårtyper, medelvärden per sten och Ward-klustring följer.",
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
    name: "Gräslund, A.-S. 1998",
    detail: "Ornamentiken som dateringsgrund för Upplands runstenar. I: Innskrifter og datering / Dating inscriptions. Trondheim, s. 73–91.",
  },
  {
    name: "Kitzler Åhfeldt, L. 2002",
    detail: "Work and Worship. Laser Scanner Analysis of Viking Age Rune Stones. Stockholms universitet.",
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
    name: "Malzbender, T., Gelb, D. & Wolters, H. 2001",
    detail: "Polynomial Texture Maps. SIGGRAPH ’01. Grunden för RTI-visaren och diffuse gain.",
  },
  {
    name: "K-samsök (Riksantikvarieämbetet)",
    detail: "Bilder och metadata från svenska kulturarvsinstitutioner.",
    href: "https://www.raa.se/hitta-information/k-samsok/",
  },
  {
    name: "OpenStreetMap",
    detail: "Kartunderlag © OpenStreetMap-bidragsgivare.",
    href: "https://www.openstreetmap.org/copyright",
  },
];

const LICENSES = [
  {
    what: "Programkoden",
    license: "GNU GPL v3",
    text: "Fri att använda, studera, ändra och sprida. Ändrade versioner som sprids ska också vara öppna under GPL-3.0.",
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
            <span className="text-xl font-bold tracking-tight">Vitki <span className="text-slate-400 font-normal">AI</span></span>
          </Link>
          <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
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
            Vitki AI samlar 3D-mätning av huggspår, Samnordisk runtextdatabas, ortografisk jämförelse och en delad
            mätkorpus i ett och samma verktyg – med redovisad osäkerhet, verifierbara källor och full spårbarhet.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/start" className="px-7 py-3.5 rounded-full bg-[#b7410e] text-white font-bold hover:bg-[#9a350b] shadow-lg shadow-[#b7410e]/20">
              Öppna appen
            </Link>
            <a href="#funktioner" className="px-7 py-3.5 rounded-full bg-white border border-slate-300 font-bold hover:border-slate-900">
              Se funktionerna
            </a>
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
          </p>
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
            intro="Vitki AI ersätter inte runologens bedömning. Den ger mätbara, granskningsbara underlag att pröva hypoteser mot."
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
            title="Det här tillför Vitki AI"
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
            AI-funktionerna använder Google Gemini för löptext, bildbeskrivning och samtal. AI-text märks som sådan och ska
            granskas; den används aldrig som källa till mätvärden eller sannolikheter.
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
{`Kvant, V. (2026). Runforskning (Aagaard Research):
öppen plattform för analys av runinskrifter
(version 2.0.0). ${GITHUB}

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
            Vitki AI · Aagaard Research · Grundat av{" "}
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
