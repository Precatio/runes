// The archive's written part: runic alphabets, rune names as the sources give them, what is known about runes and
// magic, and further reading. Carvers, purposes and well-known stones are generated from the data (/api/research/archive).

export interface RunologySection {
  id: string;
  title: string;
  category: "alfabet" | "namn" | "magi" | "kallor";
  content: string;
  keywords: string[];
}

// The sixteen runes of the younger futhark with the names and meanings of the Norwegian (c. 1200s) and Icelandic
// (c. 1400s) rune poems
export const YOUNGER_FUTHARK: { rune: string; translit: string; name: string; meaning: string }[] = [
  { rune: "ᚠ", translit: "f", name: "fé", meaning: "boskap, rikedom" },
  { rune: "ᚢ", translit: "u", name: "úr", meaning: "slagg (norska runedikten), duggregn (isländska)" },
  { rune: "ᚦ", translit: "þ", name: "þurs", meaning: "turs, jätte" },
  { rune: "ᚬ", translit: "ą / o", name: "óss / áss", meaning: "flodmynning (norska), ås, gud (isländska)" },
  { rune: "ᚱ", translit: "r", name: "reið", meaning: "ritt, färd" },
  { rune: "ᚴ", translit: "k", name: "kaun", meaning: "böld, sår" },
  { rune: "ᚼ", translit: "h", name: "hagall", meaning: "hagel" },
  { rune: "ᚾ", translit: "n", name: "nauðr", meaning: "nöd, tvång" },
  { rune: "ᛁ", translit: "i", name: "íss", meaning: "is" },
  { rune: "ᛅ", translit: "a", name: "ár", meaning: "(gott) år, skörd" },
  { rune: "ᛋ", translit: "s", name: "sól", meaning: "sol" },
  { rune: "ᛏ", translit: "t", name: "týr", meaning: "guden Tyr" },
  { rune: "ᛒ", translit: "b", name: "bjarkan", meaning: "björk, björkris" },
  { rune: "ᛘ", translit: "m", name: "maðr", meaning: "man, människa" },
  { rune: "ᛚ", translit: "l", name: "lögr", meaning: "vatten, sjö" },
  { rune: "ᛦ", translit: "R", name: "ýr", meaning: "idegran (båge)" },
];

export const runologyData: RunologySection[] = [
  // --- RUNRADERNA ---
  {
    id: "aldre-futharken",
    title: "Den äldre futharken",
    category: "alfabet",
    content: "Den äldsta runraden har 24 tecken och användes från 100-talet e.Kr. till omkring 700-talet i hela det germanska området. Namnet futhark kommer av radens sex första runor. De flesta inskrifterna står på lösa föremål – vapen, smycken, kammar och guldbrakteater – och är ofta korta; bara ett fåtal står på sten. En av de äldsta kompletta runraderna finns på Kylverstenen på Gotland, och guldhornen från Gallehus i Danmark bär en av de mest kända urnordiska inskrifterna.",
    keywords: ["futhark", "urnordiska", "24 runor", "kylverstenen", "gallehus", "brakteat", "lösföremål"]
  },
  {
    id: "yngre-futharken-langkvist",
    title: "Den yngre futharken: långkvistrunor",
    category: "alfabet",
    content: "Under 700-talet ersattes den äldre runraden i Skandinavien av en yngre med bara 16 tecken – samtidigt som språket fick fler ljud. En runa fick därför stå för flera ljud: u-runan för u, o, y, ö och w, k-runan för både k och g. Långkvistrunorna (tidigare kallade danska runor eller normalrunor) har långa huvudstavar och bistavar och är den vanligaste formen på de vikingatida runstenarna, inte minst på 1000-talets stenar i Mälardalen.",
    keywords: ["vikingatid", "16 runor", "långkvist", "danska runor", "normalrunor"]
  },
  {
    id: "yngre-futharken-kortkvist",
    title: "Den yngre futharken: kortkvistrunor",
    category: "alfabet",
    content: "Kortkvistrunorna (tidigare kallade svensk-norska runor eller rökrunor) är en förenklad variant av den yngre runraden, med korta bistavar och för några runor utan huvudstav. De användes främst i Sverige och Norge och har tolkats som en bruksskrift för trä och ben, men står också på runstenar. Rökstenen (Ög 136) är huvudsakligen ristad med kortkvistrunor, kompletterade med chiffer och äldre runor.",
    keywords: ["kortkvist", "svensk-norska", "rökrunor", "rökstenen", "vikingatid"]
  },
  {
    id: "stavlosa-runor",
    title: "Stavlösa runor (hälsingerunor)",
    category: "alfabet",
    content: "En ytterligare förenklad form där huvudstavarna utelämnas och bara bistavarna ristas. Skriften blev snabb att rista men svår att läsa. Namnet hälsingerunor kommer av att den först uppmärksammades på runstenar i Hälsingland, där flest belägg finns.",
    keywords: ["stavlösa", "hälsingerunor", "hälsingland", "utan stav"]
  },
  {
    id: "medeltida-runor",
    title: "Stungna runor och medeltida runor",
    category: "alfabet",
    content: "För att skilja ljud som den yngre runraden slog samman började man sätta en prick, ett sting, i vissa runor: stungen i blev e, stungen k blev g och stungen u blev y. Stungna runor förekommer redan på senvikingatida runstenar och byggdes under medeltiden ut till ett fullständigt runalfabet som motsvarade det latinska. Medeltida runor användes på gravhällar, i kyrkor, på föremål och på träpinnar för vardagliga meddelanden, som de många runpinnarna från Bryggen i Bergen.",
    keywords: ["stungna runor", "medeltid", "runalfabet", "bryggen", "gravhäll"]
  },
  {
    id: "dalrunor",
    title: "Dalrunor",
    category: "alfabet",
    content: "I delar av Dalarna, särskilt i Älvdalen, levde en form av runskrift kvar långt efter medeltiden, påverkad av det latinska alfabetet och anpassad till det lokala språket. Dalrunor ristades på föremål av trä, på byggnader och i almanackor och användes in på 1900-talet.",
    keywords: ["dalrunor", "dalarna", "älvdalen", "1900-tal", "eftermedeltid"]
  },

  // --- RUNORNAS NAMN ---
  {
    id: "namn-yngre",
    title: "Runornas namn i den yngre futharken",
    category: "namn",
    content: "Varje runa hade ett namn, som i regel börjar med runans ljud. Namnen och deras betydelse är kända genom de medeltida runedikterna – den norska från omkring 1200-talet och den isländska från omkring 1400-talet – där varje runa får en kort strof. Namnen och betydelserna i tabellen nedan kommer därifrån. Vad runornas namn betydde för vikingatidens ristare utöver att vara ett hjälpmedel för att minnas runraden vet vi inte.",
    keywords: ["runnamn", "runedikt", "fé", "úr", "þurs", "óss", "reið", "kaun", "hagall", "nauðr", "íss", "ár", "sól", "týr", "bjarkan", "maðr", "lögr", "ýr"]
  },
  {
    id: "namn-aldre",
    title: "Runornas namn i den äldre futharken",
    category: "namn",
    content: "Den äldre runradens namn är inte nedskrivna under den tid den användes. De rekonstrueras ur de senare traditionerna – de nordiska runedikterna, den fornengelska runedikten och gotiska bokstavsnamn – till former som *fehu (boskap), *ūruz (uroxe), *þurisaz (jätte), *ansuz (gud), *raidō (ritt), *hagalaz (hagel), *naudiz (nöd), *īsaz (is), *jēra (år), *sōwilō (sol), *tīwaz (guden Tyr), *berkanan (björk), *mannaz (människa), *laguz (vatten), *dagaz (dag) och *ōþalan (arvegods). Flera namn är osäkra, och stjärnan markerar att de är rekonstruerade.",
    keywords: ["fehu", "uruz", "thurisaz", "ansuz", "raidho", "rekonstruerad", "äldre futhark", "runnamn"]
  },

  // --- RUNOR OCH MAGI ---
  {
    id: "magi-kallor",
    title: "Runor och magi – vad källorna visar",
    category: "magi",
    content: "Några inskrifter har en uppenbart rituell eller magisk sida: ord som alu och laþu på guldbrakteater och andra lösföremål från järnåldern, förbannelser över den som förstör ett monument (som på Björketorps- och Stentoftenstenarna i Blekinge), formler som 'Tor vige' på vikingatida stenar och chiffer som på Rökstenen. Men de allra flesta runinskrifter är vardaglig eller monumental skrift: minnesinskrifter, ägaranteckningar och meddelanden. Uppfattningen att varje runa har en egen magisk kraft eller 'energi' kommer från 1900-talets esoterik och har inget stöd i de historiska källorna. Appen redovisar magiska och rituella formler som en av inskrifternas syften (se Inskrifternas syfte).",
    keywords: ["magi", "alu", "laþu", "förbannelse", "björketorp", "stentoften", "tor vige", "esoterik", "chiffer"]
  },

  // --- KÄLLOR ---
  {
    id: "kallor",
    title: "Källor och vidare läsning",
    category: "kallor",
    content: "**Samnordisk runtextdatabas** (Uppsala universitet) – alla inskrifter, translitterering, normalisering, ristare och stilgrupp; appens ristare och kända stenar kommer därifrån. **Runor** (Riksantikvarieämbetet) – den senaste utgåvan av databasen, med bilder och litteratur. **Sveriges runinskrifter** – den vetenskapliga utgåvan landskap för landskap. **Gräslund 1998** – stilgrupperna och deras datering. **Axelson 1993** – attribueringarna i Mälardalen. **Källström 2007, Mästare och minnesmärken** – runristarna och deras signaturer. **Åhlén 1997, Runristaren Öpir**. **Kitzler Åhfeldt 2002** och senare – huggteknik i 3D-skanningar. Fullständiga referenser och hur appen använder källorna står i dokumentationen.",
    keywords: ["källor", "litteratur", "rundata", "runor", "sveriges runinskrifter", "gräslund", "axelson", "källström", "åhlén"]
  },
];
