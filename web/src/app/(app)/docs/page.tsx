"use client";

export default function DocsPage() {

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
      
      <div className="mb-10 mt-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
          Om Vitki AI
        </h1>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Här hittar du bakgrundsinformation, användarmanual och licensvillkor för forskningsverktyget.
        </p>
      </div>

      <div className="space-y-8 pb-12">
        
        {/* Background / Why */}
        <section className="liquid-glass-island rounded-[32px] p-8 border border-white/50 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#b7410e]/10 text-[#b7410e] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
              </svg>
            </div>
            Bakgrund och Syfte
          </h2>
          <div className="prose prose-slate text-slate-700 max-w-none text-[15px] leading-relaxed space-y-4">
            <p>
              Historiskt sett har epigrafik och runologi ofta dominerats av kvalitativa tolkningar och subjektiva okulära bedömningar av ristningstekniker. När forskare försökt identifiera individuella ristare (runmästare) har man förlitat sig på visuella bedömningar av stil eller lingvistiska särdrag, vilket introducerar bias.
            </p>
            <p>
              Huvudsyftet med att utveckla <strong>Vitki AI</strong> är att flytta fältet bort från subjektiva antaganden och mot <em>direkt, verifierbar teknisk data</em>. Även om 3D-skanningar har introducerat en kvantitativ potential, har metodiken hittills krävt att forskare manuellt plottar tvärsnitt och mäter vinklar, vilket återinför den mänskliga felkällan.
            </p>
            <p>
              Vitki AI automatiserar mätningen av huggspår i 3D-skanningar och ställer den bredvid andra oberoende
              belägg: Rundatas uppgifter, ortografi, språkdrag, inskrifternas innehåll, stilgrupper och bergart. Allt
              som räknas fram redovisas med metod, osäkerhet och – där det går – korsvaliderad träffsäkerhet eller
              p-värde. Språkmodeller används för att läsa bilder och skriva löptext, aldrig för att hitta på
              sannolikheter; deras bedömningar märks som okalibrerade.
            </p>
          </div>
        </section>

        {/* Usage / Documentation */}
        <section className="liquid-glass-island rounded-[32px] p-8 border border-white/50 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#b7410e]/10 text-[#b7410e] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            Hur man använder appen (Manual)
          </h2>
          <div className="prose prose-slate text-slate-700 max-w-none text-[15px] leading-relaxed space-y-4">
            
            <div className="bg-[#b7410e]/5 border border-[#b7410e]/20 rounded-xl p-4 my-4">
              <p className="text-sm text-slate-800 leading-relaxed">
                <strong>Snabbast:</strong> sidan <strong>Stenanalys</strong> kör hela kedjan nedan för en skanning och ett signum
                och ger en färdig artikel med alla figurer och en bilaga om hur analysen gjordes.
              </p>
            </div>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">1. Mät huggspår i 3D</h3>
            <p>
              Öppna <strong>3D-Huggspårsanalys</strong> och ladda upp en skanning (<code>.stl</code>, <code>.obj</code> eller{" "}
              <code>.ply</code>). Skriver du stenens signum hämtas uppgifter ur Rundata. Välj sedan mätsätt:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li><strong>Automatiskt:</strong> vrid den ristade sidan mot dig och starta analysen. Alla spår hittas och mäts; granska resultatet, märk områden som runor eller ornamentik och välj vilket urval som blir resultatet.</li>
              <li><strong>Ett klick:</strong> håll Shift och klicka mitt i ett spår – varje klick mäter ett snitt.</li>
              <li><strong>Manuellt:</strong> håll Shift och klicka två punkter tvärs över ett spår, eller flera längs spåret.</li>
            </ul>
            <p>
              Spara analysen i ett projekt. Under <strong>Bilder ur skanningen</strong> skickar du strykljus, relief och djup
              – räknade ur själva skanningen – till 2D-analysen eller till Språk &amp; Fonetik. Mätningen kan också
              publiceras i den delade <strong>mätkorpusen</strong>.
            </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">2. Läs och tolka inskriften</h3>
            <p>
              I <strong>Språk &amp; Fonetik</strong> läser AI:n runorna blint från en bild (foto, RTI-vy eller relief ur 3D).
              Ange signum så jämförs läsningen med Rundata utan AI: hur stor del som stämmer, hur mycket av texten den täcker
              och vilka ord som skiljer sig. Ordformerna kontrolleras mot Rundatas korpus. Språkmodeller kan inte läsa runor
              tillförlitligt och återger ibland kända inskrifter ur minnet; därför valideras varje läsning, och en obekräftad
              läsning visas med en varning i stället för som text. Rätta läsningen vid behov och spara
              den i projektet. <strong>2D-Bildanalys</strong> bedömer stilgrupp och runformer; <strong>RTI-visaren</strong> låter dig
              flytta ljuset över en PTM-fil.
            </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">3. Väg samman beläggen</h3>
            <p>
              <strong>Syntes &amp; Attribuering</strong> väger samman Rundata, ortografi och huggteknik efter hur träffsäkra
              metoderna är i just det fallet. Varje kandidat prövas mot litteraturen, geografi, ristarens stilgrupper, bergart,
              språkdrag, inskriftstyp och – om ristarens stenar är uppmätta – sten mot sten. Motsägelser och saknade belägg
              redovisas. Spara syntesen i projektet.
            </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">4. Hitta luckor och skriv</h3>
            <p>
              <strong>Forskningsluckor</strong> visar var uppgifter saknas (klicka på en siffra för att se stenarna), vad appens
              resultat säger jämfört med befintlig forskning, inskrifternas syfte per ristare och vilka stenar som mest behöver
              mätas. Under <strong>Rapporter</strong> skapar du en stenrapport i artikelform – med figurer ur skanningen, läsningen och
              attribueringen – eller en rapport över flera stenar, och laddar ner den som Word, LaTeX eller Markdown.
            </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">Statistik i R</h3>
            <p>
              På sidan <strong>Statistik (R)</strong> analyseras hela korpusen i R: ristarnas områden och avstånd till vatten,
              grupper av stil och språk, formler och stavning, dialekter, en korsvaliderad attribueringsmodell, seriation mot
              Gräslunds kronologi och formelnätverk. Den fullständiga stenanalysen ställer stenen mot dessa resultat och mot
              landskapet (sikt, strand vid vikingatiden, bästa vägar), och stenrapporten får egna avsnitt om det. I
              Forskningsluckor kan förslagen stämmas av mot Runor 2020 och Wikidata. Allt kan laddas ner som
              reproducerbarhetspaket med R-skript och data.
            </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">5. Fråga AI-assistenten</h3>
            <p>
              Nere i högra hörnet finns assistenten. Den har tillgång till Rundata och din senaste analys, till exempel{" "}
              <em>&quot;Jag fick en asymmetri på 3 grader, vad tyder det på?&quot;</em>
            </p>
          </div>
        </section>
        {/* API Setup */}
        <section className="liquid-glass-island rounded-[32px] p-8 border border-white/50 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#b7410e]/10 text-[#b7410e] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
              </svg>
            </div>
            Skapa och ställ in API-nycklar
          </h2>
          <div className="prose prose-slate text-slate-700 max-w-none text-[15px] leading-relaxed space-y-4">
            <p>
              För att verktyget ska kunna utföra bildanalyser, texttolkningar och röstuppläsning krävs API-nycklar. Verktyget använder en så kallad &quot;Bring Your Own Key&quot;-modell (BYOK), vilket innebär att du enkelt skapar dina egna nycklar och klistrar in dem under <strong>Inställningar & API</strong> i sidomenyn.
            </p>
            
            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">1. Claude (Anthropic) – rekommenderas</h3>
            <p>
              Claude är standardmodell för bildanalys, läsning, syntesens och rapporternas texter och AI-assistenten.
              Välj modell under Inställningar. Ett Claude-abonnemang (Pro/Max) kan inte användas av appen – den behöver en
              API-nyckel, som faktureras separat efter användning.
            </p>
            <ol className="list-decimal pl-5 mt-2 space-y-2">
              <li>Gå till <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">console.anthropic.com</a> och logga in.</li>
              <li>Lägg in betalning under <em>Billing</em> och skapa en nyckel under <em>API keys</em>.</li>
              <li>Kopiera nyckeln (börjar med <code>sk-ant-</code>) och klistra in den under Inställningar.</li>
            </ol>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">2. Google Gemini (alternativ)</h3>
            <p>
              Gemini kan väljas i stället för Claude under Inställningar.
            </p>
            <ol className="list-decimal pl-5 mt-2 space-y-2">
              <li>Gå till <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Google AI Studio</a> och logga in med ett Google-konto.</li>
              <li>Klicka på knappen <strong>Get API key</strong> (eller <em>Create API key</em>).</li>
              <li>Välj att skapa en nyckel i ett nytt eller befintligt projekt.</li>
              <li>Kopiera textsträngen som skapas (börjar ofta med <code>AIzaSy...</code>) och klistra in den i Vitki AI:s inställningsmeny.</li>
            </ol>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">3. OpenAI (ungefärlig uppläsning)</h3>
            <p>
              OpenAI används bara för den ungefärliga uppläsningen i Språk &amp; Fonetik. Det är en modern talsyntes, inte en rekonstruktion av uttalet.
            </p>
            <ol className="list-decimal pl-5 mt-2 space-y-2">
              <li>Gå till <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">OpenAI Developer Platform</a> och logga in (eller skapa ett konto).</li>
              <li>Observera att du kan behöva lägga till ett betalkort och ladda kontot med en liten summa (t.ex. $5) för att röstuppläsningen ska fungera.</li>
              <li>Klicka på <strong>Create new secret key</strong>.</li>
              <li>Ge nyckeln ett valfritt namn (t.ex. &quot;Vitki AI&quot;) och klicka på <em>Create secret key</em>.</li>
              <li>Kopiera textsträngen (börjar oftast med <code>sk-...</code>) och klistra in den i Vitki AI:s inställningsmeny.</li>
            </ol>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 my-4">
              <p className="text-sm text-slate-800 font-medium mb-1">
                🔒 Var sparas nycklarna?
              </p>
              <p className="text-sm text-slate-600 leading-relaxed">
                Nycklarna lagras endast lokalt i din webbläsare (localStorage). De sparas aldrig i någon central databas; de skickas med varje analys till analysmotorn, som vidarebefordrar dem till Anthropic, Google eller OpenAI. Om du rensar webbläsarens cache kommer du behöva klistra in nycklarna igen.
              </p>
            </div>
          </div>
        </section>

        {/* Useful Links */}
        <section className="liquid-glass-island rounded-[32px] p-8 border border-white/50 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#b7410e]/10 text-[#b7410e] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
              </svg>
            </div>
            Nyttiga Länkar för Runologi
          </h2>
          <div className="prose prose-slate text-slate-700 max-w-none text-[15px] leading-relaxed space-y-4">
            <p>
              Här finner du länkar till var man kan hämta in oprocessad referensdata som 3D-modeller och högupplösta bilder för akademiska analyser.
            </p>
            
            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">3D-Scanningar & Modeller</h3>
            <ul className="list-disc pl-5 mt-2 space-y-3">
              <li>
                <strong><a href="https://sketchfab.com/raa" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Riksantikvarieämbetet på Sketchfab</a></strong><br/>
                Flera officiella och högkvalitativa 3D-skanningar av utvalda svenska runstenar publiceras här, lämpliga att ladda ner (.obj / .stl) för vår 3D-analysator.
              </li>
              <li>
                <strong><a href="https://sketchfab.com/statenshistoriskamuseer" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Statens historiska museer på Sketchfab</a></strong><br/>
                Även Historiska museet publicerar många av sina fynd och stenar som 3D-modeller tillgängliga för nedladdning.
              </li>
              <li>
                <strong><a href="https://www.shfa.se/" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Svenskt HällristningsForskningsArkiv (SHFA)</a></strong><br/>
                En plattform som främst samlar in och publicerar digital dokumentation av ristningar. Deras teknik-fokus är väldigt relevant för 3D-analys.
              </li>
            </ul>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">Högupplösta Bilder & Metadata</h3>
            <ul className="list-disc pl-5 mt-2 space-y-3">
              <li>
                <strong><a href="https://www.alvin-portal.org/" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Alvin (Plattform för kulturarvssamlingar)</a></strong><br/>
                Ett nationellt system för digitala samlingar och digitaliserat kulturarv. Innehåller mängder med högupplösta 2D-bilder och historiska avteckningar av runstenar, perfekt för vår paleografiska 2D-analys.
              </li>
              <li>
                <strong><a href="https://app.raa.se/open/fornsok/" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Fornsök (Riksantikvarieämbetet)</a></strong><br/>
                Sveriges officiella register över fornlämningar. Här kan man ofta finna grundläggande metadata om runstenar, koordinater, och inventeringsbilder.
              </li>
            </ul>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">Geologi</h3>
            <ul className="list-disc pl-5 mt-2 space-y-3">
              <li>
                <strong><a href="https://sgu.se/en/products/geological-data/berggrund--geologisk-data/bedrock" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Sveriges geologiska undersökning (SGU) – Berggrund</a></strong><br/>
                Berggrundskartan 1:50 000–1:250 000, som appen använder för att jämföra stenens bergart med berggrunden där den står.
              </li>
            </ul>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">Språk & Forskning</h3>
            <ul className="list-disc pl-5 mt-2 space-y-3">
              <li>
                <strong><a href="https://www.runforum.nordiska.uu.se/" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Samnordisk runtextdatabas (Rundata)</a></strong><br/>
                Uppsala universitets databas över kända runinskrifter. Den är inbyggd i appen (sidan Inskrifter, kartan, syntesen och AI-assistenten) och används under Open Database License med angivande av källan.
              </li>
              <li>
                <strong><a href="https://skaldic.org/m.php?p=skaldic" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Skaldic Poetry of the Scandinavian Middle Ages</a></strong><br/>
                En viktig resurs för runinskrifternas lingvistik, poesin och språkstrukturen under vikingatiden.
              </li>
            </ul>
          </div>
        </section>

        {/* Method, data and citation */}
        <section className="liquid-glass-island rounded-[32px] p-8 border border-white/50 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Metod, data och citering</h2>
          <div className="prose prose-slate text-slate-700 max-w-none text-[15px] leading-relaxed space-y-3">
            <p>
              Alla beräkningar beskrivs i <code>METHODS.md</code>. Varje 3D-analys sparar programversion, mätmetodens version
              (nu <code>groove-3</code>), filens SHA-256, alla parametrar och varje snitts position och råprofil, och kan
              exporteras som CSV eller JSON.
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Osäkerhet:</strong> mätvärden redovisas med standardavvikelse, antal snitt och 95 % konfidensintervall.</li>
              <li><strong>Attribuering:</strong> kandidater räknas fram ur Rundata, ortografi och huggteknik, vägda efter korsvaliderad träffsäkerhet. AI:n skriver bara text och anger inga sannolikheter.</li>
              <li><strong>Ortografisk likhet:</strong> cosinuslikhet mellan inskriftens stavningsprofil och ristarens. p anger hur ovanligt hög likheten är jämfört med andra ristares inskrifter, justerat för att den bästa av alla ristare väljs. En enskild likhet är ett svagt belägg; metodens träffsäkerhet är det bättre måttet.</li>
              <li><strong>Inskrifternas syfte:</strong> regelbaserade kategorier; per ristare testas avvikelser mot genomsnittet med korrektion för många test. För sällsynta typer (t.ex. magiska inskrifter) är frånvaro oftast väntad.</li>
              <li><strong>Bergart:</strong> jämförs med SGU:s berggrundskarta. Runstenar är ofta flyttblock eller transporterade, så en avvikelse är en ledtråd, inte ett fel.</li>
              <li><strong>Verktygsklassning:</strong> pik-/bredmejsel med tröskel 85° är en tumregel, inte ett kalibrerat mått.</li>
              <li><strong>Mätkorpus:</strong> bidrag publiceras under CC BY 4.0 med bidragsgivaren angiven. Bilder och 3D-filer delas inte.</li>
              <li><strong>Stilgrupper:</strong> enligt Gräslund (1998); dateringarna är ungefärliga.</li>
            </ul>
            <p>
              Citera programvaran enligt <code>CITATION.cff</code>. Använder du uppgifter ur Rundata ska även
              Samnordisk runtextdatabas anges som källa, och för berggrunden Sveriges geologiska undersökning (SGU).
            </p>
          </div>
        </section>

        {/* License */}
        <section className="liquid-glass-island rounded-[32px] p-8 border border-white/50 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#b7410e]/10 text-[#b7410e] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
            </div>
            Licensregler (GNU GPLv3)
          </h2>
          <div className="prose prose-slate text-slate-700 max-w-none text-[15px] leading-relaxed space-y-4">
            <p>
              Detta program utgör fri programvara. Det är tillåtet att distribuera och modifiera det i enlighet med villkoren i <strong>GNU General Public License</strong> (version 3 eller senare), så som den publicerats av Free Software Foundation.
            </p>
            <p>
              Mjukvaran distribueras i syfte att främja akademisk forskning och metodologisk transparens. Den tillhandahålls i befintligt skick, utan uttryckliga eller underförstådda garantier avseende systemets funktionalitet eller dess lämplighet för specifika analyser.
            </p>
            <p>
              I korthet innebär licensvillkoren följande:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li>Mjukvaran får användas fritt i både akademiska och privata sammanhang.</li>
              <li>Källkoden får modifieras fritt för att anpassas till nya forskningsfrågor.</li>
              <li>Vid distribution av källkoden, inklusive eventuella vidareutvecklingar eller förbättringar, måste koden ovillkorligen förbli fri och tillhandahållas under samma öppna licens. Det är således inte tillåtet att kommersialisera eller sälja källkoden som en sluten produkt.</li>
            </ul>

            <p className="text-sm text-slate-500 mt-4 italic">
              För hela den legala texten, vänligen läs filen <code>LICENSE</code> i projektets rotkatalog.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}
