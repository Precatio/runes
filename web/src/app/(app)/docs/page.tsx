"use client";

import Link from "next/link";
import type { ReactNode } from "react";

const REPO = "https://github.com/Precatio/runes";
const A = "text-[#b7410e] hover:underline";

function Section({ id, title, icon, children }: { id: string; title: string; icon?: string; children: ReactNode }) {
  return (
    <section id={id} className="liquid-glass-island rounded-[32px] p-6 md:p-8 border border-white/50 shadow-sm scroll-mt-6">
      <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
        {icon && (
          <span className="w-8 h-8 shrink-0 rounded-full bg-[#b7410e]/10 text-[#b7410e] flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
            </svg>
          </span>
        )}
        {title}
      </h2>
      <div className="text-slate-700 text-[15px] leading-relaxed space-y-4">{children}</div>
    </section>
  );
}

const H3 = ({ children }: { children: ReactNode }) => <h3 className="text-lg font-bold text-slate-900 pt-2">{children}</h3>;

// The app's pages, in the groups of the side menu (components/Sidebar.tsx)
const FEATURES: { group: string; items: { href: string; name: string; text: string }[] }[] = [
  {
    group: "Analys av en sten",
    items: [
      { href: "/stenanalys", name: "Stenanalys (allt i ett)", text: "Kör hela kedjan för en skanning och ett signum och ger en färdig artikel med figurer och en bilaga om hur analysen gjordes." },
      { href: "/3d", name: "3D-huggspårsanalys", text: "Mäter huggspårens vinkel, djup och bredd i en 3D-skanning – automatiskt, med ett klick eller manuellt. Den automatiska analysen mäter bara runorna (mätmetod groove-5)." },
      { href: "/2d", name: "2D-bildanalys", text: "Bedömer stilgrupp och runformer ur ett foto, strykljus eller en relief räknad ur skanningen." },
      { href: "/phonetics", name: "Språk & fonetik", text: "Läser runorna blint ur en bild och prövar läsningen mot Rundata; en obekräftad läsning visas med varning. Ger också en ungefärlig uppläsning." },
      { href: "/3d?verktyg=rti", name: "RTI-släpljus", text: "Flytta ljuset över en RTI- eller PTM-fil för att se grunda ristningar – ett verktyg på 3D-sidan." },
      { href: "/synthesis", name: "Syntes & attribuering", text: "Väger samman Rundata, ortografi, huggteknik, geografi, stilgrupper, bergart och språkdrag efter hur träffsäkra metoderna är, och redovisar motsägelser." },
    ],
  },
  {
    group: "Forskning i hela korpusen",
    items: [
      { href: "/inskrifter", name: "Inskrifter (Rundata)", text: "Sök och filtrera alla inskrifter i Samnordisk runtextdatabas, med text, översättning, ristare, stilgrupp och läge." },
      { href: "/karta", name: "Mönsterkartan", text: "Välj ett mönster – kors, böner, stavning, brobyggen – och jämför andelen per område, över tid, med avståndet till ortnamn, medeltida kyrkor och fornlämningar eller med statistiska kluster. Upptäck visar de starkaste mönstren." },
      { href: "/korpus", name: "Mätkorpus", text: "Den delade korpusen av huggspårsmätningar från inloggade forskare, publicerad under CC BY 4.0." },
      { href: "/jamfor", name: "Jämför stenar", text: "Ställer två stenars mätningar mot varandra; först prövas om mätningarna alls går att jämföra." },
      { href: "/oversikt", name: "Stenöversikt", text: "Var beläggen stöder Rundatas ristare och var en annan ristare får stöd, och landskapet runt varje sten." },
      { href: "/luckor", name: "Forskningsluckor", text: "Var uppgifter saknas, vad appens resultat säger mot befintlig forskning och vilka hypoteser som kan prövas – avstämt mot Runor och Wikidata." },
      { href: "/statistik", name: "Statistik (R)", text: "Korpusanalyser i R: geografi och vikingatida strandlinje, kluster, formler, dialekter, attribuering, datering, nätverk, förändring i tid och rum, fornlämningar och ortnamn runt stenarna samt hot spots. Allt kan laddas ner som reproducerbarhetspaket." },
      { href: "/rapporter", name: "Rapporter", text: "Stenrapport och korpusrapport i artikelform, i elva publiceringsformer, som Word, LaTeX eller Markdown." },
    ],
  },
  {
    group: "Resurser",
    items: [
      { href: "/start", name: "Start", text: "Dina projekt och analyser, sparade i ditt konto." },
      { href: "/artiklar", name: "Artiklar", text: "Artiklar om de mest intressanta mönstren i runstenarna, skrivna för en bred publik och med statistiken förklarad." },
      { href: "/account", name: "Konto och inställningar", text: "Logga in för att spara projekt och bidra till mätkorpusen, och lägg in dina API-nycklar." },
    ],
  },
];

// Data the app uses, with source and licence (scripts/, src/, r/)
const SOURCES: { name: string; href: string; use: string; licence: string }[] = [
  { name: "Samnordisk runtextdatabas (Rundata), Uppsala universitet", href: "https://www.runforum.nordiska.uu.se/", use: "Inskrifterna: text, översättning, ristare, stilgrupp, plats och läge.", licence: "Open Database License (ODbL 1.0); källan ska anges" },
  { name: "Kulturmiljöregistret, Riksantikvarieämbetet (via K-samsök)", href: "https://kulturarvsdata.se/", use: "Fornlämningar runt stenarna: gravfält, högar, färdvägar, broar, fornborgar och hamnar.", licence: "Öppna data från Riksantikvarieämbetet; källan anges" },
  { name: "OpenStreetMap", href: "https://www.openstreetmap.org/copyright", use: "Ortnamn (med Lantmäteriets namn från terrängkartan) och bakgrundskartan.", licence: "© OpenStreetMap-bidragsgivare, ODbL" },
  { name: "Wikidata", href: "https://www.wikidata.org/", use: "Medeltida kyrkor med uppförandeår, och vilka bilder som visar en runsten.", licence: "CC0" },
  { name: "Wikimedia Commons", href: "https://commons.wikimedia.org/", use: "Fotona i artiklarna.", licence: "Varje bilds egen licens, med fotograf och licens i bildtexten" },
  { name: "Natural Earth", href: "https://www.naturalearthdata.com/", use: "Kustlinje, sjöar och vattendrag.", licence: "Public domain" },
  { name: "Tilezen Terrain Tiles (AWS Open Data)", href: "https://registry.opendata.aws/terrain-tiles/", use: "Höjddata för sikt, strandlinjen under vikingatiden och bästa vägar.", licence: "Öppna data; källorna anges enligt tjänstens villkor" },
  { name: "Sveriges geologiska undersökning (SGU)", href: "https://www.sgu.se/", use: "Berggrunden där stenen står.", licence: "Öppna data från SGU; källan anges" },
  { name: "Öppna 3D-skanningar på Zenodo", href: "https://zenodo.org/", use: "Referensmätningar av huggspår (bl.a. Kitzler Åhfeldt 2024); skaparna krediteras i rapporterna.", licence: "CC BY 4.0" },
];

const TOC: [string, string][] = [
  ["bakgrund", "Bakgrund"], ["funktioner", "Funktioner"], ["kom-igang", "Kom igång"], ["nycklar", "API-nycklar"],
  ["data", "Data och källor"], ["metod", "Metod och citering"], ["licens", "Licens"], ["om", "Vem står bakom"],
];

export default function DocsPage() {
  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
      <div className="mb-8 mt-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Om Vitki</h1>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Vitki är en öppen plattform för analys av runinskrifter. Här finns bakgrunden, en översikt över funktionerna,
          en manual, datakällorna och licensvillkoren.
        </p>
        <nav aria-label="Innehåll" className="mt-4 flex flex-wrap gap-2">
          {TOC.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="rounded-full border border-slate-900/10 bg-white/70 px-3 py-1 text-sm font-semibold text-slate-700 hover:border-[#b7410e] hover:text-[#b7410e]">
              {label}
            </a>
          ))}
        </nav>
      </div>

      <div className="space-y-8 pb-12">
        <Link href="/docs/metod" className="block liquid-glass-island rounded-[24px] p-6 border border-[#b7410e]/30 hover:border-[#b7410e] transition-colors">
          <p className="text-lg font-bold text-slate-900">Metodik och beräkningar →</p>
          <p className="text-sm text-slate-600 mt-1">
            Hur huggspåren mäts steg för steg, hur statistiken räknas, valideringar och robusthet, alla skript och
            R-moduler – och metodens kända brister. Hämtas direkt från koden, så det är alltid aktuellt.
          </p>
        </Link>

        <Section id="bakgrund" title="Bakgrund och syfte" icon="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25">
          <p>
            Runologin har länge byggt på kvalitativa tolkningar och okulära bedömningar. När forskare har försökt
            identifiera enskilda ristare har de förlitat sig på stil och språkdrag, bedömda med ögat. 3D-skanningar har
            öppnat för mätningar, men tvärsnitt och vinklar har mätts för hand, vilket för tillbaka den mänskliga
            felkällan.
          </p>
          <p>
            Vitki automatiserar mätningen av huggspår och ställer den bredvid andra oberoende belägg: Rundatas uppgifter,
            ortografi, språkdrag, inskrifternas innehåll, stilgrupper, bergart och landskapet runt stenen. Samma verktyg
            används på hela korpusen, där statistiken i R letar efter mönster i tid och rum – och prövar dem.
          </p>
          <p>
            Allt som räknas fram redovisas med metod och osäkerhet. Ett mönster räknas bara om det klarar justeringen
            för många test och håller i båda halvorna av materialet. Språkmodeller används för att läsa bilder och skriva
            löptext, aldrig för att hitta på sannolikheter, och deras bedömningar märks som okalibrerade.
          </p>
        </Section>

        <Section id="funktioner" title="Funktioner" icon="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6Zm0 9.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6Zm0 9.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z">
          {FEATURES.map(g => (
            <div key={g.group} className="space-y-2">
              <H3>{g.group}</H3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {g.items.map(f => (
                  <Link key={f.href} href={f.href} className="block rounded-2xl border border-slate-900/10 bg-white/60 p-4 hover:border-[#b7410e]/60 transition-colors">
                    <p className="font-bold text-slate-900">{f.name} <span className="text-[#b7410e]" aria-hidden="true">→</span></p>
                    <p className="text-sm text-slate-600 mt-1">{f.text}</p>
                  </Link>
                ))}
              </div>
            </div>
          ))}
          <p className="text-sm text-slate-600">
            Nere i högra hörnet finns <strong>AI-assistenten</strong>, som har tillgång till Rundata och din senaste
            analys. Appen finns på svenska och engelska; byt språk högst upp i sidomenyn.
          </p>
        </Section>

        <Section id="kom-igang" title="Kom igång" icon="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z">
          <div className="bg-[#b7410e]/5 border border-[#b7410e]/20 rounded-xl p-4">
            <p className="text-sm text-slate-800 leading-relaxed">
              <strong>Snabbast:</strong> sidan <strong>Stenanalys</strong> kör stegen 1–3 för en skanning och ett signum och ger
              en färdig artikel med alla figurer och en bilaga om hur analysen gjordes.
            </p>
          </div>

          <H3>1. Mät huggspår i 3D</H3>
          <p>
            Öppna <strong>3D-huggspårsanalys</strong> och ladda upp en skanning (<code>.stl</code>, <code>.obj</code> eller{" "}
            <code>.ply</code>). Skriver du stenens signum hämtas uppgifterna ur Rundata. Välj sedan mätsätt:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Automatiskt:</strong> vrid den ristade sidan mot dig och starta analysen. Spåren i runorna hittas och mäts; ornamentiken räknas inte. Granska resultatet och välj vilket urval som blir resultatet.</li>
            <li><strong>Ett klick:</strong> håll Shift och klicka mitt i ett spår – varje klick mäter ett snitt.</li>
            <li><strong>Manuellt:</strong> håll Shift och klicka två punkter tvärs över ett spår, eller flera längs spåret.</li>
          </ul>
          <p>
            Spara analysen i ett projekt. Under <strong>Bilder ur skanningen</strong> skickar du strykljus, relief och djup
            till 2D-analysen eller till Språk &amp; fonetik. Mätningen kan också publiceras i den delade mätkorpusen.
          </p>

          <H3>2. Läs och tolka inskriften</H3>
          <p>
            I <strong>Språk &amp; fonetik</strong> läser AI:n runorna blint från en bild. Med ett signum jämförs läsningen med
            Rundata utan AI: hur stor del som stämmer, hur mycket av texten den täcker och vilka ord som skiljer sig.
            Språkmodeller kan inte läsa runor tillförlitligt och återger ibland kända inskrifter ur minnet; därför
            valideras varje läsning. <strong>2D-bildanalys</strong> bedömer stilgrupp och runformer.
          </p>

          <H3>3. Väg samman beläggen</H3>
          <p>
            <strong>Syntes &amp; attribuering</strong> väger samman Rundata, ortografi och huggteknik efter hur träffsäkra
            metoderna är i just det fallet. Varje kandidat prövas mot litteraturen, geografi, stilgrupper, bergart, språkdrag
            och – om ristarens stenar är uppmätta – sten mot sten.
          </p>

          <H3>4. Utforska mönster i korpusen</H3>
          <p>
            På <strong>Mönsterkartan</strong> väljer du ett mönster och vad det ska jämföras med. Börja gärna under
            <em> Upptäck</em>, där de starkaste mönstren ligger. <strong>Statistik (R)</strong> visar korpusanalyserna med
            metod, effektstorlek och osäkerhet, och <strong>Forskningsluckor</strong> samlar de mönster som håller med
            hypoteser och förslag på hur de kan prövas.
          </p>

          <H3>5. Skriv</H3>
          <p>
            Under <strong>Rapporter</strong> skapar du en stenrapport i artikelform eller en rapport över flera stenar och
            laddar ner den som Word, LaTeX eller Markdown. Reproducerbarhetspaketen innehåller R-skript och data, så att
            andra kan räkna om resultaten.
          </p>
        </Section>

        <Section id="nycklar" title="API-nycklar" icon="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z">
          <p>
            Bildanalys, läsning, texterna i syntesen och rapporterna, assistenten och uppläsningen kräver API-nycklar. Vitki
            använder en <em>bring your own key</em>-modell: du skapar egna nycklar och klistrar in dem under{" "}
            <Link href="/account" className={A}>Inställningar</Link>. Mätningarna, statistiken och kartan fungerar utan nycklar.
          </p>
          <H3>Claude (Anthropic) – rekommenderas</H3>
          <p>
            Claude är standardmodell. Ett Claude-abonnemang (Pro/Max) kan inte användas av appen; den behöver en API-nyckel,
            som faktureras separat efter användning.
          </p>
          <ol className="list-decimal pl-5 space-y-1">
            <li>Gå till <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" className={A}>console.anthropic.com</a> och logga in.</li>
            <li>Lägg in betalning under <em>Billing</em> och skapa en nyckel under <em>API keys</em>.</li>
            <li>Kopiera nyckeln (börjar med <code>sk-ant-</code>) och klistra in den under Inställningar.</li>
          </ol>
          <H3>Google Gemini (alternativ)</H3>
          <p>
            Gemini kan väljas i stället för Claude. Skapa en nyckel i{" "}
            <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className={A}>Google AI Studio</a>{" "}
            (<em>Get API key</em>) och klistra in den under Inställningar.
          </p>
          <H3>OpenAI (ungefärlig uppläsning)</H3>
          <p>
            OpenAI används bara för den ungefärliga uppläsningen i Språk &amp; fonetik, en modern talsyntes och inte en
            rekonstruktion av uttalet. Skapa en nyckel på{" "}
            <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" className={A}>OpenAI Developer Platform</a>;
            kontot kan behöva laddas med en liten summa.
          </p>
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
            <p className="text-sm text-slate-800 font-semibold mb-1">Var sparas nycklarna?</p>
            <p className="text-sm text-slate-600 leading-relaxed">
              Bara i din webbläsare (localStorage), aldrig i någon databas. De skickas med varje analys till analysmotorn,
              som vidarebefordrar dem till Anthropic, Google eller OpenAI. Rensar du webbläsarens data behöver du klistra in
              dem igen.
            </p>
          </div>
        </Section>

        <Section id="data" title="Data och källor" icon="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 5.625c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125">
          <p>
            Vitki bygger på öppna data. Använder du resultat som bygger på dem ska källorna anges enligt sina licenser.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="p-2 font-semibold">Källa</th><th className="p-2 font-semibold">Används till</th><th className="p-2 font-semibold">Licens</th>
                </tr>
              </thead>
              <tbody>
                {SOURCES.map(s => (
                  <tr key={s.name} className="border-t border-slate-900/5 align-top">
                    <td className="p-2 font-semibold text-slate-900"><a href={s.href} target="_blank" rel="noreferrer" className={A}>{s.name}</a></td>
                    <td className="p-2">{s.use}</td>
                    <td className="p-2 text-slate-600">{s.licence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <H3>Fler källor för runforskning</H3>
          <ul className="list-disc pl-5 space-y-2">
            <li><a href="https://sketchfab.com/raa" target="_blank" rel="noreferrer" className={A}>Riksantikvarieämbetet på Sketchfab</a> och <a href="https://sketchfab.com/statenshistoriskamuseer" target="_blank" rel="noreferrer" className={A}>Statens historiska museer</a> – 3D-modeller av runstenar och fynd.</li>
            <li><a href="https://www.shfa.se/" target="_blank" rel="noreferrer" className={A}>Svenskt HällristningsForskningsArkiv (SHFA)</a> – digital dokumentation av ristningar.</li>
            <li><a href="https://www.alvin-portal.org/" target="_blank" rel="noreferrer" className={A}>Alvin</a> – högupplösta bilder och historiska avteckningar av runstenar.</li>
            <li><a href="https://app.raa.se/open/fornsok/" target="_blank" rel="noreferrer" className={A}>Fornsök</a> – Riksantikvarieämbetets register över fornlämningar.</li>
            <li><a href="https://skaldic.org/m.php?p=skaldic" target="_blank" rel="noreferrer" className={A}>Skaldic Poetry of the Scandinavian Middle Ages</a> – runinskrifternas språk och poesi.</li>
          </ul>
        </Section>

        <Section id="metod" title="Metod, data och citering" icon="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z">
          <p>
            Alla beräkningar beskrivs i <Link href="/docs/metod" className={A}>Metodik och beräkningar</Link> (filen{" "}
            <code>METHODS.md</code>). Varje 3D-analys sparar programversion, mätmetodens version (nu <code>groove-5</code>),
            filens SHA-256, alla parametrar och varje snitts position och råprofil, och kan exporteras som CSV eller JSON.
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Osäkerhet:</strong> mätvärden redovisas med standardavvikelse, antal snitt och 95 % konfidensintervall; effekter med oddskvot och intervall.</li>
            <li><strong>Många test:</strong> när många samband prövas samtidigt justeras p-värdena (Benjamini–Hochberg eller Holm), och ett mönster räknas bara om det håller i båda halvorna av korpusen, uppdelad socken för socken.</li>
            <li><strong>Flyttade stenar:</strong> stenar som enligt Rundata står vid en kyrka, i ett museum eller en samling räknas inte där stenens omgivning prövas.</li>
            <li><strong>Attribuering:</strong> kandidater räknas fram ur Rundata, ortografi och huggteknik, vägda efter korsvaliderad träffsäkerhet. AI:n skriver bara text och anger inga sannolikheter.</li>
            <li><strong>Bergart:</strong> jämförs med SGU:s berggrundskarta. Runstenar är ofta flyttblock, så en avvikelse är en ledtråd, inte ett fel.</li>
            <li><strong>Stilgrupper:</strong> enligt Gräslund; dateringarna är ungefärliga.</li>
          </ul>
          <p>
            Citera programvaran enligt <a href={`${REPO}/blob/main/CITATION.cff`} target="_blank" rel="noreferrer" className={A}>CITATION.cff</a>.
            Använder du uppgifter ur Rundata ska även Samnordisk runtextdatabas anges som källa, och övriga källor enligt
            tabellen ovan.
          </p>
        </Section>

        <Section id="licens" title="Licens" icon="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z">
          <p>
            Vitki är fri programvara under <strong>GNU General Public License version 3</strong> (GPL-3.0-only) med
            tilläggsvillkor enligt licensens § 7. Copyright © 2026 Viktor Kvant.
          </p>
          <H3>Det här får du göra</H3>
          <ul className="list-disc pl-5 space-y-1">
            <li>Använda programmet för alla ändamål, i forskning, undervisning och privat.</li>
            <li>Studera och ändra koden för nya frågor.</li>
            <li>Sprida kopior och ändrade versioner, även mot betalning – så länge mottagarna får samma friheter: källkoden följer med och licensen är densamma (copyleft).</li>
          </ul>
          <H3>Tilläggsvillkoren (filen NOTICE)</H3>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Upphovsangivelse (§ 7 b).</strong> Raden <em>”Bygger på Vitki, ursprungligen utvecklad av Viktor Kvant
              (https://github.com/Precatio/runes)”</em> ska bevaras i källkoden, synas i användargränssnittet och stå i
              dokumentation och rapporter där programmet anger sitt ursprung.
            </li>
            <li>
              <strong>Inget felaktigt ursprung (§ 7 c).</strong> Ingen får framställa kodbasen eller grunden för den som sitt
              eget verk. Ändrade versioner märks som ändrade: vad som ändrats, av vem och när.
            </li>
            <li>
              <strong>Namnet (§ 7 e).</strong> En ändrad version får kallas ”baserad på Vitki” men inte ges ut under namnet Vitki.
            </li>
          </ul>
          <H3>Data och resultat</H3>
          <p>
            Bidrag till mätkorpusen publiceras under CC BY 4.0 med bidragsgivaren angiven; bilder och 3D-filer delas inte.
            Uppgifter ur Rundata och de andra källorna lyder under källornas egna licenser. Att citera Vitki enligt
            CITATION.cff är en uppmaning, inte ett licensvillkor.
          </p>
          <p className="text-sm text-slate-500">
            Programmet tillhandahålls i befintligt skick, utan garantier (GPL-3.0 §§ 15–16). Läs hela villkoren i{" "}
            <a href={`${REPO}/blob/main/LICENSE`} target="_blank" rel="noreferrer" className={A}>LICENSE</a> och{" "}
            <a href={`${REPO}/blob/main/NOTICE`} target="_blank" rel="noreferrer" className={A}>NOTICE</a>.
          </p>
        </Section>

        <Section id="om" title="Vem står bakom" icon="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z">
          <p>
            Vitki är grundat och utvecklat av <strong>Viktor Kvant</strong>, som till vardags arbetar som digital analytiker
            och har en bakgrund i humaniora och konstforskning. Projektet bygger på tanken att samma analytiska metoder kan
            föras över mellan fält: Vitki vill inte ersätta runologernas arbete, utan erbjuda nya perspektiv och metoder att
            pröva.
          </p>
          <p>
            Källkoden finns på <a href={REPO} target="_blank" rel="noreferrer" className={A}>GitHub</a>, där du också kan
            rapportera fel och föreslå förbättringar.
          </p>
        </Section>
      </div>
    </div>
  );
}
