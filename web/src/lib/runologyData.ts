export interface RunologySection {
  id: string;
  title: string;
  category: "alfabet" | "betydelse" | "syfte" | "ristare" | "oattribuerad";
  content: string;
  keywords: string[];
}

export const runologyData: RunologySection[] = [
  // --- RUNALFABET (FUTHARKEN) ---
  {
    id: "aldre-futharken",
    title: "Den Äldre Futharken",
    category: "alfabet",
    content: "Den äldre futharken är det äldsta kända runalfabetet och bestod av 24 tecken. Den var i bruk från cirka 150 e.Kr. till 800 e.Kr. över hela det urgermanska språkområdet. På grund av det stora antalet tecken fanns det en specifik runa för de allra flesta ljud i språket. Få runstenar är ristade med denna runrad i Skandinavien; den återfinns oftast på lösa föremål som vapen, kammar, amuletter och brakteater (t.ex. Kylverstenen och Gallehushornen). Omkring 800 e.Kr., när språket genomgick stora ljudförändringar (synkope), blev ironiskt nog denna 24-typiga runrad omodern, vilket ledde till skapandet av den yngre futharken.",
    keywords: ["futhark", "urgermanska", "urnordiska", "kylverstenen", "24 runor"]
  },
  {
    id: "yngre-futharken-normal",
    title: "Yngre Futharken (Normalrunor / Danska runor)",
    category: "alfabet",
    content: "Under vikingatiden (ca 800 - 1100 e.Kr.) reducerades runraden från 24 till 16 tecken, känd som den Yngre Futharken. Denna förenkling skedde samtidigt som språket fick *fler* ljud, vilket innebar att en och samma runa fick representera flera olika fonem (t.ex. representerade ᚢ /u/ både ljuden u, o, y och ö). Normalrunorna, även kallade 'danska runor' på grund av deras dominans i sydvästra Skandinavien, kännetecknas av långa och tydliga huvudstavar och är den vanligaste formen på vikingatida monumentala runstenar, speciellt under 1000-talet i Mälardalen.",
    keywords: ["vikingatid", "16 runor", "danska runor", "normalrunor"]
  },
  {
    id: "yngre-futharken-kortkvist",
    title: "Yngre Futharken (Kortkvistrunor)",
    category: "alfabet",
    content: "Kortkvistrunor, även kända som 'svensk-norska runor', är en variant av den 16-typiga yngre futharken. Precis som namnet antyder har dessa runor förkortade bistavar och vissa runor saknar helt huvudstav. Detta var med stor sannolikhet en snabbskrift utvecklad för vardagligt bruk, särskilt för att rista meddelanden i trä (t.ex. på träpinnar från Bryggen i Bergen). Även om de var vardagsrunor, återfinns de också på ett flertal runstenar (bl.a. Rökstenen använder till stor del kortkvistrunor).",
    keywords: ["vikingatid", "svensk-norska", "snabbskrift", "trä", "rökstenen"]
  },
  {
    id: "stavlosa-runor",
    title: "Stavlösa Runor (Hälsingerunor)",
    category: "alfabet",
    content: "En extrem form av den yngre futharken där huvudstavarna har utelämnats helt – man ristar endast bistavarna (kvistarna). Detta gjorde skriften mycket snabb att rista men också svårare att läsa, och fungerade ibland nästan som ett stenografiskt system. De kallas ofta Hälsingerunor eftersom de först dokumenterades på runstenar i Hälsingland, men de har hittats även i Medelpad, Södermanland och Bergen.",
    keywords: ["hälsingerunor", "stenografi", "utan stav", "vikingatid"]
  },
  {
    id: "medeltida-runor",
    title: "Medeltida Runor & Stungna runor",
    category: "alfabet",
    content: "Efter vikingatiden, in i medeltiden (ca 1100-talet till 1500-talet), fortsatte runorna att användas parallellt med det latinska alfabetet. För att lösa problemet med att den yngre futharkens 16 tecken inte räckte till för att skriva ljudenlig latin eller sentida fornsvenska, infördes 'stungna runor'. Genom att sätta en prick (ett sting) i en runa förändrades dess ljudvärde. Till exempel blev en stungen ᛁ (i) till ett 'e', en stungen ᚴ (k) till ett 'g', och en stungen ᛒ (b) till ett 'p'.",
    keywords: ["medeltid", "stungna runor", "fonetisk", "latin"]
  },
  {
    id: "dalrunor",
    title: "Dalrunor",
    category: "alfabet",
    content: "Dalrunorna är en fascinerande överlevnad. I delar av Dalarna, särskilt i Älvdalen, fortsatte bönderna att använda en egenutvecklad form av runor fram till början av 1900-talet. Alfabetet påverkades kraftigt av det latinska alfabetet och anpassades till det lokala språket (älvdalska). De ristades oftast på träföremål, möbler, skålar och budkavlar, och visar att runorna i Sverige inte 'dog ut' på medeltiden, utan var ett levande skriftspråk långt in i modern tid.",
    keywords: ["dalarna", "älvdalen", "1900-tal", "trä", "överlevnad"]
  },

  // --- RUNORNAS BETYDELSE ---
  {
    id: "betydelse-fehu",
    title: "F-runan (Fehu / Fé)",
    category: "betydelse",
    content: "**Urnordiskt namn:** *Fehu* | **Fornnordiskt namn:** *Fé* | **Ljud:** [f]\n\nRunan betyder 'boskap' eller 'rikedom' (ordet fä). Eftersom boskap var den främsta bytesvaran och värdemätaren i det forntida samhället representerar den rörlig egendom, överflöd, finansiell styrka och framgång. I magiska sammanhang användes den troligen för att dra till sig materiell rikedom.",
    keywords: ["fehu", "fé", "rikedom", "boskap", "f"]
  },
  {
    id: "betydelse-uruz",
    title: "U-runan (Uruz / Úr)",
    category: "betydelse",
    content: "**Urnordiskt namn:** *Uruz* | **Fornnordiskt namn:** *Úr* | **Ljud:** [u, o, y, ö, w]\n\nRunan betyder 'uroxe' (uruz) eller i yngre tid 'slagg' (úr). Uroxen var ett kraftfull, numera utdöt vilddjur. Runan symboliserar urkraft, rå styrka, obändig uthållighet och maskulin hälsa. På grund av den yngre futharkens få tecken representerar u-runan på vikingatida runstenar en mängd olika vokaler (u, o, y, ö).",
    keywords: ["uruz", "úr", "uroxe", "styrka", "u"]
  },
  {
    id: "betydelse-thurisaz",
    title: "TH-runan (Thurisaz / Thurs)",
    category: "betydelse",
    content: "**Urnordiskt namn:** *Thurisaz* | **Fornnordiskt namn:** *Thurs* | **Ljud:** [θ, ð]\n\nBetyder 'turs' (jätte/troll) och är starkt förknippad med åskguden Tor (även om hans eget namn ironiskt nog inte användes för runan). Det är en mycket kraftfull, potentiellt destruktiv och aggressiv runa som representerar kaoskrafter, naturkrafter och konflikt. På runstenar transkriberas den oftast som 'þ' och uttalas som engelskans 'th'.",
    keywords: ["thurisaz", "thurs", "jätte", "troll", "tor", "þ"]
  },
  {
    id: "betydelse-ansuz",
    title: "A-runan (Ansuz / Áss)",
    category: "betydelse",
    content: "**Urnordiskt namn:** *Ansuz* | **Fornnordiskt namn:** *Áss* (Óss) | **Ljud:** [a, o]\n\nBetyder 'Asa-gud' (främst förknippad med Oden). Runan står för gudomlig inspiration, ordets makt, visdom, kommunikation och poesi (Oden var ju magins och diktkonstens gud). I den yngre futharken ändrade a-runan form (till kvistrunan ᛅ) medan den gamla formen ᚬ fick namnet óss (å-ljudet / näsljudet a).",
    keywords: ["ansuz", "áss", "óss", "gud", "oden", "a"]
  },
  {
    id: "betydelse-raidho",
    title: "R-runan (Raidho / Reið)",
    category: "betydelse",
    content: "**Urnordiskt namn:** *Raidho* | **Fornnordiskt namn:** *Reið* | **Ljud:** [r]\n\nBetyder 'ritt' eller 'vagn/resa'. Den symboliserar rörelse, resor (både fysiska och andliga/magiska), rättvisa, moralisk ordning (att följa 'rätt' väg) och universella cykler. Visuellt påminner runan mycket om det latinska 'R'.",
    keywords: ["raidho", "reið", "resa", "ritt", "r"]
  },

  // --- STENARNAS SYFTE & KLASSIFICERING ---
  {
    id: "syfte-minnesmarke",
    title: "Minnesstenar",
    category: "syfte",
    content: "Den absolut vanligaste formen av runstenar (uppskattningsvis över 90% av de vikingatida stenarna). Syftet var att hedra en avliden familjemedlem eller frände. Den klassiska standardformeln lyder: 'X lät resa denna sten efter Y, sin fader/broder/maka. Gud hjälpe hans själ'. De restes vanligtvis vid välbesökta platser som vägar, broar och tingsplatser för att säkerställa att så många som möjligt såg monumentet och mindes den döde.",
    keywords: ["minne", "minnesmärke", "hedrande", "familj", "standardformel"]
  },
  {
    id: "syfte-odal",
    title: "Odalstenar (Arvsrätt & Juridik)",
    category: "syfte",
    content: "Vissa runstenar fungerade som offentliga juridiska dokument som slog fast arvsrätt (odal) och ägande till mark. Eftersom man saknade ett utbyggt skriftligt system på papper, höggs viktiga ägandeförhållanden i sten. Det mest kända exemplet är Hillersjöstenen i Uppland, vars extremt långa inskrift i detalj redogör för ett komplicerat arvsförlopp där en kvinna vid namn Gerlög till slut ärvde hela egendomen genom att överleva flera makar och barn.",
    keywords: ["odal", "arv", "juridik", "äganderätt", "hillersjöstenen"]
  },
  {
    id: "syfte-infrastruktur",
    title: "Brostenar & Infrastruktur",
    category: "syfte",
    content: "Under övergångsperioden till kristendomen i Sverige (1000-talet) var ett vanligt syfte att resa stenar i anslutning till ett brobygge eller röjning av en väg. Att underlätta för resenärer ansågs vara en särskilt god, kristen barmhärtighetsgärning som hjälpte den avlidnes själ i skärselden. Formeln inkluderar ofta frasen: 'Han gjorde bron för (hans) själ'. Många av dessa stenar har hittats vid gamla vadställen där träbroar tidigare funnits.",
    keywords: ["bro", "infrastruktur", "kristendom", "skärseld", "själavård"]
  },
  {
    id: "syfte-självberömmelse",
    title: "Självberömmelsestenar",
    category: "syfte",
    content: "Ett mer ovanligt, men fascinerande, syfte är monument resta av personer över sig själva medan de fortfarande levde. Syftet var politiskt och statusdrivande – att markera makt, ägande och inflytande. Stormannen Jarlabanke är den kändaste: han lät uppföra flera stenar och en bro över sig själv med texten 'Jarlabanke lät resa dessa stenar efter sig själv, medan han levde, och han ägde hela Täby'.",
    keywords: ["status", "makt", "självberömmelse", "jarlabanke", "täby", "politik"]
  },
  {
    id: "syfte-magi",
    title: "Magiska & Rituella Stenar",
    category: "syfte",
    content: "En mindre andel stenar (särskilt äldre, folkvandringstida) restes i magiskt syfte. Dessa innehåller ofta lönnrunor (kryptografiska runor), sejd-formler, välsignelser för beskydd eller uttalade förbannelser mot den som förstör monumentet. Ett berömt exempel är Björketorpsstenen i Blekinge som varnar: 'Den som bryter detta monument ska drabbas av perversitet och smygande död'. Magiska stenar markerar ofta makt över andevärlden eller sakrala gränser.",
    keywords: ["magi", "rituell", "förbannelse", "björketorp", "amulett", "sejd", "lönnrunor"]
  },

  // --- KÄNDA RUNRISTARE ---
  {
    id: "ristare-opir",
    title: "Öpir (Øpiʀ)",
    category: "ristare",
    content: "**Aktiv:** Sent 1000-tal | **Område:** Uppland | **Kända stenar:** Ca 80 (varav 45 signerade)\n\nÖpir är den mest produktiva kända runristaren i Sverige. Hans namn betyder 'Skrikaren' (troligen ett öknamn). Han revolutionerade runstenskonsten genom sin distinkta 'Upplandsstil' (Urnesstil) med extremt eleganta, åttformiga bandslingor, svällande drakkroppar, mandelformade ögon på djuren och frånvaro av kors på många stenar (trots att han opererade under kristen tid). Linguistiskt är hans texter kända för att vara lite 'slarviga' med borttappade runor, men hans artistiska linjeföring och komposition i stenen är oöverträffad. Ofta signerade han med orden 'Öpir risti' (Öpir ristade).",
    keywords: ["öpir", "uppland", "urnesstil", "slarvig stavning", "produktiv", "skrikaren"]
  },
  {
    id: "ristare-asmund",
    title: "Asmund Kåresson (Ásmundr Kárason)",
    category: "ristare",
    content: "**Aktiv:** Tidigt/mitten av 1000-talet | **Område:** Uppland, Gästrikland | **Kända stenar:** Ca 20 signerade\n\nAsmund var en banbrytare och anses av vissa forskare vara mannen som introducerade den äkta runstensdekoren i Uppland. Han är starkt kopplad till det lokala hovet och mäktiga släkter (t.ex. Jarlabanke-släkten). Han uppfann en stilren runstensdekor där drakens huvud visas från sidan (i profil). Asmunds verk är också berömda för sina tekniskt perfekta, djupt U-formade huggspår, vilket tyder på en mästerlig stenhuggare, troligen med skolning i engelsk stenhuggarkonst. En vanlig signatur lyder 'Asmund risti rätta runor'.",
    keywords: ["asmund", "kåresson", "profilhuvud", "jarlabanke", "huggspår", "uppland"]
  },
  {
    id: "ristare-balle",
    title: "Balle (Balli)",
    category: "ristare",
    content: "**Aktiv:** 1050 - 1080-talet | **Område:** Södermanland, Sydvästra Uppland | **Kända stenar:** Ca 35 signerade\n\nBalle kallas ibland 'Södermanlands store runmästare'. Hans ornamentik är stramare, mer strukturerad och symmetrisk än Öpirs vilda åttor. Balle arbetade ofta i Ringerikestil, med välformade runor (och föredrog ofta att vända runorna utåt istället för inåt runbandet). En unik egenskap hos Balles stenar är hans frekventa användning av allittererande poesi (stavrim) i sina runtexter, vilket tyder på att han inte bara var stenhuggare, utan en tränad skald. Han samarbetade ibland med andra ristare, som Frösten.",
    keywords: ["balle", "södermanland", "poesi", "ringerikestil", "symmetri"]
  },
  {
    id: "ristare-fot",
    title: "Fot (Fótr)",
    category: "ristare",
    content: "**Aktiv:** Mitten av 1000-talet | **Område:** Södra Uppland (Roslagen) | **Kända stenar:** Ca 8 signerade (många fler osignerade)\n\nFot kallas ofta för den klassiska Upplandsstilens mästare före Öpir. Trots att han signerat färre stenar anses hans verk vara de mest konstnärligt fulländade. Hans djur har stor grace med mjuka svängar, rundade ögon, och han behärskade stenens relief på ett sätt få andra gjorde. Korset i mitten av hans stenar är ofta extremt välformaterat. Han uppvisar också en oerhört jämn och ortografiskt korrekt stavning, vilket skiljer honom från många samtida. Han anses ha varit lärare till den senare runristaren Torgöt (som signerar sig som 'Fots arvinge').",
    keywords: ["fot", "mästare", "ortografi", "roslagen", "torgöt", "perfektion"]
  },
  {
    id: "ristare-visate",
    title: "Visäte (Víseti)",
    category: "ristare",
    content: "**Aktiv:** 1060 - 1080-talet | **Område:** Uppland | **Kända stenar:** Ca 25 (varav 6 signerade)\n\nVisäte var samtida med Öpir men hade en helt egen, kraftfull och kantig stil. Medan Öpir ritade smala, böljande ormar ritade Visäte breda, 'muskulösa' rundjur. Hans textband bildar ofta raka linjer och vinklar (kvadratisk form), snarare än runda slingor. Känd för Granbystenen (U 337), som har en enormt lång och historiskt viktig text. Visäte stavade dessutom oerhört konsekvent och korrekt, vilket gjort hans stenar till guldgruvor för språkforskare.",
    keywords: ["visäte", "granbystenen", "kantig", "bred", "korrekt stavning"]
  },

  // --- OATTRIBUERADE STENAR ---
  {
    id: "oattribuerad-gripsholm",
    title: "Gripsholmsstenen (Sö 179)",
    category: "oattribuerad",
    content: "**Plats:** Mariefred, Södermanland | **Datering:** 1000-talets första hälft\n\nEn av de mest berömda Ingvarsstenarna, rest över Ingvars bror Harald som dog i Särkland (Särklandståget). Trots sin magnifika poesi (stavrim) och otroligt vackra, jämna ormslinga som kröns av ett stort kors, saknar stenen helt signatur. Dess stil påminner om Äskil eller Balle, men den exakta upphovsmannen till detta mästerverk förblir en av runologins obesvarade frågor.",
    keywords: ["gripsholm", "sö 179", "ingvarståget", "särkland", "anonym", "poesi"]
  },
  {
    id: "oattribuerad-karlevi",
    title: "Karlevistenen (Öl 1)",
    category: "oattribuerad",
    content: "**Plats:** Öland | **Datering:** Sent 900-tal\n\nKarlevistenen är unik eftersom den innehåller den äldsta kända strofen av *dróttkvætt* (drottkvätt), ett avancerat fornnordiskt versmått. Den är rest efter en dansk hövding (Sibbe). Inskriften är gjord med danska runor och uppvisar en oerhörd grammatisk och poetisk briljans. Trots detta vet vi inte vem denna högt skolade skald och stenhuggare var.",
    keywords: ["karlevistenen", "öl 1", "drottkvätt", "poesi", "öland", "anonym"]
  },
  {
    id: "oattribuerad-sparlosa",
    title: "Sparlösastenen (Vg 119)",
    category: "oattribuerad",
    content: "**Plats:** Västergötland | **Datering:** 800-tal\n\nEn av Sveriges mest gåtfulla runstenar. Den är huggen med en blandning av normalrunor, kortkvistrunor och en mängd svårtolkade bildframställningar (ryttare, skepp, vilddjur). Språket är dunkelt och handlar om maktkamper, gudarna och gåvor. Den som högg stenen hade stor makt och insikt i tidens mytologi, men förblev anonym.",
    keywords: ["sparlösa", "vg 119", "västergötland", "anonym", "bildsten", "gåta"]
  }
];
