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
              Detta ramverk löser problemet genom att fullständigt automatisera den matematiska extraktionen av verktygsspår (via linjär regression) och kombinera detta med generativ AI (LLM) som väger in metadata som stensort och vittringsgrad för att bistå i en mer objektiv och probabilistisk ristningsidentifiering.
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
            
            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">1. Ladda upp 3D-Data</h3>
            <p>
              Navigera till <strong>3D-Analys</strong>. Ladda upp din 3D-modell (filformat <code>.obj</code> eller <code>.stl</code>). Om du saknar egen data kan du slå på &quot;Använd simulerad test-data&quot; för att se hur analysen fungerar.
            </p>
            
            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">2. Sätt ut din vektor</h3>
            <p>
              I den interaktiva 3D-vyn, navigera runt stenen:
            </p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li><strong>Vänsterklick + dra:</strong> Rotera kameran</li>
                <li><strong>Högerklick + dra:</strong> Panorera</li>
                <li><strong>Dubbelklicka:</strong> Sätt ut startpunkten för ditt snitt, dubbelklicka därefter igen för att sätta slutpunkten.</li>
              </ul>
              <div className="bg-[#b7410e]/5 border border-[#b7410e]/20 rounded-xl p-4 my-4">
                <p className="text-sm text-[#b7410e] font-bold mb-1">
                  💡 Visste du?
                </p>
                <p className="text-sm text-slate-700 leading-relaxed">
                  Att klicka ut en vektor innebär enbart att du bestämmer <em>var</em> på runstenen provet (snittet) ska tas. Den kritiska och tidigare felbenägna uppgiften – att hitta spårets exakta bottenpunkt och mäta in de mikroskopiska vinklarna – görs inte längre genom att användaren manuellt försöker dra linjer längs spårets väggar, utan sköts nu helt matematiskt av 3D-motorns regressionsanalys.
                </p>
              </div>
              <p>
                Appen räknar utifrån dina klickningar automatiskt fram Origin- och Direction-vektorerna för snittet. Du kan även justera &quot;Flera snitt (Medelvärde)&quot; för högre precision vid skrovliga ytor.
              </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">3. Analysera</h3>
            <p>
              Klicka på <strong>Analysera</strong>. Algoritmen skär stenen utifrån din vektor, rensar bort plan yta, och beräknar den optimala V-vinkeln och asymmetrin i spåret. Resultaten sparas i den globala kontexten.
            </p>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">4. AI-Runologen</h3>
            <p>
              Nere i högra hörnet finns den inbyggda AI-assistenten. Du kan när som helst öppna chatten och ställa frågor om dina mätvärden (t.ex. <em>&quot;Jag fick en asymmetri på 3 grader, vad tyder det på?&quot;</em>). Assistenten har automatisk tillgång till din senast körda 3D-analys.
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
            
            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">1. Google Gemini (Bildanalys & Chatt)</h3>
            <p>
              Gemini används som huvudmotor för att läsa runstenar, tolka ornamentik och driva AI-assistenten Rune.
            </p>
            <ol className="list-decimal pl-5 mt-2 space-y-2">
              <li>Gå till <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-[#b7410e] hover:underline">Google AI Studio</a> och logga in med ett Google-konto.</li>
              <li>Klicka på knappen <strong>Get API key</strong> (eller <em>Create API key</em>).</li>
              <li>Välj att skapa en nyckel i ett nytt eller befintligt projekt.</li>
              <li>Kopiera textsträngen som skapas (börjar ofta med <code>AIzaSy...</code>) och klistra in den i Vitki AI:s inställningsmeny.</li>
            </ol>

            <h3 className="text-lg font-bold text-slate-900 mt-6 mb-2">2. OpenAI (Röstuppläsning av fornnordiska)</h3>
            <p>
              OpenAI används specifikt för text-till-tal (TTS) när du klickar på &quot;Spela Upp&quot; under den fonetiska rekonstruktionen.
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
                Nycklarna lagras endast lokalt i din webbläsare (localStorage). De skickas aldrig till någon central databas, utan går direkt från din dator till Google och OpenAI vid analys. Om du rensar webbläsarens cache kommer du behöva klistra in nycklarna igen.
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
              (nu <code>groove-2</code>), filens SHA-256 och alla parametrar, och kan exporteras som CSV eller JSON.
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Osäkerhet:</strong> mätvärden redovisas med standardavvikelse, antal snitt och 95 % konfidensintervall.</li>
              <li><strong>Attribuering:</strong> kandidater räknas fram ur Rundata, ortografisk jämförelse och uppmätt huggteknik. Metodernas träffsäkerhet redovisas med korsvalidering. AI:n skriver bara text och anger inga sannolikheter.</li>
              <li><strong>Verktygsklassning:</strong> pik-/bredmejsel med tröskel 85° är en tumregel, inte ett kalibrerat mått.</li>
              <li><strong>Mätkorpus:</strong> bidrag publiceras under CC BY 4.0 med bidragsgivaren angiven. Bilder och 3D-filer delas inte.</li>
              <li><strong>Stilgrupper:</strong> enligt Gräslund (1998); dateringarna är ungefärliga.</li>
            </ul>
            <p>
              Citera programvaran enligt <code>CITATION.cff</code>. Använder du uppgifter ur Rundata ska även
              Samnordisk runtextdatabas anges som källa.
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
