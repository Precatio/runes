# Ändringslogg

Versionsnumren följer [semantisk versionering](https://semver.org/lang/sv/). Mätmetodens version (`groove-N`)
anges separat, eftersom den avgör vilka mätningar som är jämförbara (METHODS.md, avsnitt 1).

## [Ej släppt]

### Multipel imputation av odaterade stenar: prövad, inte införd
- Om de 1 313 runstenarna utan säker stilgrupp kunde tas med i tidsfrågorna genom multipel imputation (R-paketet
  mice, med och utan sannolikhetsmodellens språkdatering) prövades enligt en låst analysplan. Svaret blev nej:
  intervallen höll inte (täckning 0,87–0,89 mot kravet 0,90) och skattningarna blev sämre än med bara de daterade
  stenarna. Appen räknar som förut på daterade stenar. Ny bristpost `undated`, METHODS.md 1n, `utdata/mi/`.

### Nyheter på webbplatsen
- vitkirunor.se har en nyhetsmodul: rutan **Nytt i Vitki** på startsidan med de senaste notiserna och sidan
  **/nyheter** med alla, länkad från sidhuvudet och sidfoten och med i sajtkartan. Notiserna skrivs i
  `web/content/news.json` (status *nytt* eller *på gång*). De första handlar om Pröva en egen fråga och Spara som fynd.

### Fynd vi redan skrivit om
- R-mönster som det finns en artikel eller ett utkast om märks **Artikel ✓** (länk till artikeln) eller **Utkast
  skrivet** på Statistik och i Forskningsluckor, och knappen *Dölj de vi skrivit om* tar bort dem ur listorna med ett
  klick; valet gäller båda sidorna. Kopplingen är artikelns ämne (som Månadens fynd sparar det) eller
  `data/article_patterns.json` (`GET /api/r/pattern-articles`).

### Pröva en egen fråga
- Statistik (R) har kortet **Pröva en egen fråga**: välj ett drag (tro, skrift, innehåll, ristare) och jämför med ett
  annat drag, ett landskap, en tidsgräns eller en bergart. Svaret är justerat för landskap och tid (Mantel–Haenszel),
  räknas som ett mönster bara om det håller i båda halvorna av socknarna, prövas utan de flitigaste ristarna, och
  besökets frågor justeras tillsammans (Benjamini–Hochberg). Ingen fri text och ingen AI. Kartans Upptäck länkar hit.
  Nollfallet: omblandade drag höll i båda halvorna i 0 av 1 000 frågor (METHODS.md 1y).
- **Spara som fynd**: ett svar sparas med en anteckning och visas i Forskningsluckor → Våra resultat under *Egna
  frågor*, med belägg som högst måttliga och bara om halvprovet höll. *Räkna om* prövar frågan på korpusen som den är nu.

## [3.0.0] – 2026-10-20

Ett nytt huvudnummer därför att gränssnittet och API:t inte längre är bakåtkompatibla med 2.x: Vitki läser inte runor
och bedömer inte stilgrupp med AI, sidorna Språk & Fonetik, 2D-bildanalys, Stilgrupper och Kunskap är borta (gamla
adresser leder vidare), `styles` i `/api/research/findings` och `style_check` i syntesen finns inte längre, och AI-text
är ett tillval i stället för standard. Allt som räknas fram har fått redovisad träffsäkerhet mot en nollnivå, och
sannolikhetsmodellen har gått från textmodel-14 till textmodel-19 med låsta analysplaner.

### Sannolikhetsmodellen textmodel-15 → textmodel-19
- `textmodel-15`: varje sten läses med ristarens egen skiljeteckentäthet (ordgränser 95,1 → 95,4 procent), och
  kalibreringen skattas på utgivarnas, maskerade och dokumenterade luckor tillsammans (kalibreringsfel 2,5
  procentenheter på de dokumenterade). `VALIDATION` räknas på runstenar.
- `textmodel-16`: alternativen i en lucka får högst sin egen sannolikhet, aldrig mer än förstavalet förlorade.
- `textmodel-17`: alla förslag i en lucka kalibreras tillsammans (softmax över förslagen och "inget av dem"), och
  valet följer den kalibrerade procenten. Förregistrerat blindtest på 21 aldrig granskade stenar: 16 rätt inom det
  låsta intervallet, 13 av 13 svar ≥ 95 procent rätt.
- `textmodel-18`: namnkandidaterna får en egen kvot (`name_cands` 40), så att sällsynta namn når poängsättningen:
  8 luckor vunna, ingen förlorad; dokumenterade luckor 248 → 249 av 361.
- `textmodel-19`: toleranslagret – belagda stavningar utökas med regelgenererade varianter (slut-R, h-, obetonad
  vokal, i/e/a, nasal, svarabhakti) till ett straff per regel, efter en analysplan som låstes innan resultaten fanns.
  Dokumenterade luckor 252 av 361 med 2 fel bland 158 svar ≥ 95 procent (förut 249 och 4). Spår ur skanningen
  ("Vad skannern ser") kan tas in mjukt i luckorna; maskering med spår ger 84 procent hela ord.
- Forskningsluckor har fliken **Luckor i texten**: de öppna luckor där modellen fyller i ett känt ord med minst 80
  procent (27 på 21 stenar), med en rad som anger vilket underlag och vilken modellversion sidan bygger på.

### Statistik i R prövad mot nollnivåer
- **Vem ristade?** redovisar bergartens eget bidrag: en delmodell med bara bergart träffar 19 procent (= att gissa
  den vanligaste ristaren), och tabellen *Kommer träffen från bergarten?* visar hela modellens träff per
  bergartsfamilj. Huggspårens tillförlitlighet räknas mot bergartsgissningen i stället för mot slumpen.
- **Okända ristare**: grupperna prövas där ristare är kända – strängare prov med tre slumpdelar och 30 upprepningar
  ger 85 mot 69 procent för närliggande stenar (+16 procentenheter) – och en kolumn *utan tidsdragen* visar vilka
  grupper som består när stilgrupp, kors, stungna runor, böner och signaturer tas bort. Sidan varnar för att 25 av 35
  kända ristare finns i Uppland medan kandidaterna ligger i landskap där nästan inga ristare är kända.
- **Ordförrådet**: vilka ord som skiljer landskapen åt när tid och textlängd räknats bort (logistisk modell med
  ristaren som slumpeffekt, prövad i sockenhalvor) och vilka som ändras över tid; korrespondensanalys av landskapens
  ordval.
- Mätkorpusen är fylld med Kitzler Åhfeldts 37 öppna skanningar, så att huggspår kan jämföras mot något.

### Artiklarna organiserade: etiketter och Så gör du-serien
- Varje artikel har etiketter (typ och ämnen ur en fast lista), som filter på artikellistan (`?etikett=`) och i
  Admin. Serien **Så gör du** går igenom appen vy för vy med skärmbilder ur den körande appen: huggspårsanalys,
  inskrifter och luckor, forskningsluckorna och statistiken i R (utkast).
- Startsidan visar sex vyer ur appen – mönsterkartan, inskrifterna, sannolikhetsmodellen, statistiken, forsknings-
  luckorna och stenöversikten – tagna med ett skript så att de kan tas om när appen ändras.

### Runor 2020 bredvid Rundata
- Inskriftssidan visar Riksantikvarieämbetets Runor (2020) bredvid Rundata 3.1 (2018) där utgåvorna skiljer sig
  (plats, status, läsning). Beräkningarna bygger ännu på Rundata; bytet kräver en egen analysplan.

### Metod och reproducerbarhet
- Analysplaner låses med hash innan resultat tas fram (`ANALYSPLAN.md`, METHODS.md 1x); toleranslagret var det
  första. `tests/test_methods_numbers.py` kontrollerar att talen i METHODS stämmer med koden.
- Exempelpaketet `examples/so128/` visar vägen från öppen skanning till färdig stenrapport.
- `IMPLEMENTATIONSPLAN.md` samlar det som återstår, med status.

### Admin
- Besöksstatistiken: ett klick på en dag i stapeldiagrammet visar sidor, länder, sökord och klick för den dagen
  ensam.

### AI-läsningen och Språk & Fonetik borttagna; 2D blev en flik på 3D-sidan
- Vitki läser inte längre runor med AI. Sidan Språk & Fonetik (blind läsning, normalisering, IPA, uppläsning) är
  borttagen efter två prov: läsningar ur minnet (Sö 113 gav Jellingstenens text) och, med strikt instruktion, nästan
  bara streck (träff 0 mot Rundata). Jämförelsen mot Rundata, ordformerna, ortografin och valideringen står kvar som
  beräkning (`POST /api/phonetics/compare`) och i rapporterna (METHODS.md 8). OpenAI-nyckeln (bara uppläsningen) är borta.
- 2D-bildanalysen är fliken **Bilder och runformer** på 3D-sidan: foton, RTI-vyer, reliefer och ristningskartan,
  runutsnitt jämförda efter form, och Rundatas stilgrupp bredvid bilden. AI-markeringen av runor i foton
  (`/api/2d/detect_runes`) är borttagen; automatiska utsnitt finns bara för ristningskartan. Gamla adresser (/2d,
  /phonetics) leder till 3D-sidan.
- AI-bedömningen av stilgrupp ur bild är borttagen: prövad på 57 stenar med säker stilgrupp träffade den exakta
  gruppen i 35 % av fallen (grov klass 71 %, Pr5 blev Pr4 i 7 av 8). Rundata har stilgruppen för 1 038 stenar.
  Syntesens stilkontroll mot AI, stenanalysens steg och rapportens avsnitt följer med. AI används nu bara för löptext,
  som tillval; utan nyckel räknas texterna fram.

### Ordklasser i ordföljden
- Modellen lär sig ordklasser ur texterna själva och väger in vilken klass som brukar följa på vilken. Rätt ord i
  maskeringsprovet steg något (inne i ord 72 → 73 procent, hela ord 56 → 57), luckprovet är oförändrat. Panelens
  version är `textmodel-14`.

### Färdiga bibliotek som kontroll
- Ordföljdens utjämning ger exakt samma sannolikheter som NLTK:s Kneser–Ney, och den valda rabatten var bäst av de
  prövade. Kalibreringen görs med scikit-learn (samma resultat som den egna koden). Namnbyggarens korta efterled är
  begränsade till -ví/-vé, och felaktigt delade namn lär inte längre ut stavningar. Panelens version är `textmodel-12`.

### Namnen byggs med stenarnas egna stavningar
- Namn som modellen inte känner byggs av namnled, och leden stavas nu som ristarna stavade dem i namnen på stenarna
  (Ragn- som *rahn*, *rakn* eller *ragn*). Kvinnonamn på *-ví/-vé* (Ragnví, Kætilví) kan nu byggas. Rätt namn i
  återställda luckor steg från 75,7 till 78,4 procent. Panelens version är `textmodel-11`.

### Ordet i en lucka kalibreras per ordklass
- Modellen var för säker på namn och ovanliga ord i luckor men inte på formelord. Förstavalet kalibreras nu per
  ordklass (formelord, namn, andra ord), prövat med korsvalidering på 631 luckor som utgivarna har fyllt.
  Kalibreringsfelet sjönk från 5,9 till 1,5 procentenheter. Panelen visar den kalibrerade procenten, och modellens
  egen sparas bredvid. Panelens version är `textmodel-10`.

### Ordgränsen syns i panelen
- När en lucka står i en text utan skiljetecken och modellen delar orden annorlunda än utgivarna, läser panelen om
  texten med utgivarnas ordgränser, både Rundatas huvudläsning och dess alternativa läsning. Ändras förslaget visas
  båda, under rubriken "Ordgränsen avgör förslaget". Panelens version är `textmodel-9`.

### Läsningsraden följer spåren
- När flera förslag vägs mot varandra i hela texten räknas nu de mjuka spåren och namnen från närliggande stenar
  in, som i varje lucka. Tidigare kunde panelens läsningsrad visa ett ord som spåren talade emot, medan luckans
  ordlista gav ett annat. Panelens version är `textmodel-8`.

### Sökmotoroptimering av startsidan och artiklarna
- Startsidans och artikellistans beskrivningar ryms i en sökträff (155 och 141 tecken).
- Startsidan beskriver Vitki som organisation, med logotyp och grundare (schema.org Organization), och förladdar inte
  längre artikelfotot under första skärmen.
- Miniatyrerna i artikellistan har fotots alt-text, till exempel "Runstenen U 489".
- Varje artikel slutar med tre andra artiklar ("Fler artiklar"), så att läsare och sökmotorer hittar vidare.
- Kontaktsidans adress slutar med / som sajtens andra sidor.

### Kontaktsida och nya källor på webbplatsen
- `/kontakt` har ett formulär som skickas med e-post till grundaren via FormSubmit. Webbplatsen är statisk och har
  ingen egen server.
- Startsidans källista tar med:
  - alla sex öppna 3D-datamängderna;
  - Danske Runeindskrifter;
  - källorna bakom kartans rikesgränser;
  - Wikimedia Commons.

### Fler öppna 3D-skanningar och rätt skannare
- Två nya datamängder (CC BY 4.0) i `src/scan_sources.py`:
  - Runstenar i Medelpad (Kitzler Åhfeldt & Zedig 2024, 14 stenar);
  - Tidigkristna gravmonument i Östergötland och Småland (Kitzler Åhfeldt 2025, 11 föremål).
- Stenarna i Hälsingland och Medelpad är skannade av Henrik Zedig (Länsstyrelsen Västra Götaland). Rapporterna angav
  tidigare Laila Kitzler Åhfeldt som skannare; hon är medförfattare till datamängderna.

### Hela Runor 2020
- `scripts/fetch_runor.py` hämtar hela Riksantikvarieämbetets utgåva 2020 av runtextdatabasen via dess öppna API.
- `scripts/runor_compare.py` jämför den med appens Rundata från 2018:
  - inskrifter som saknas;
  - försvunna stenar och stenar på sin ursprungliga plats;
  - anteckningar om skador;
  - ändrade läsningar.

### Statistik i R räknas om av sig själv
- När data eller analyskoden har ändrats startar analysmotorn korpusanalyserna själv, tio minuter efter start. Tidigare
  krävdes ett knapptryck. Väntan gör att en serie kodändringar inte startar en körning per ändring. Funktionen stängs
  av med `R_AUTORUN=0`.

### Namn från systerstenar och skadade texter
- Namn på närliggande stenar hämtas ur hela korpusen, utom stenen som läses (`near_sites`). Tidigare kom de bara från
  stenarna som stenens modell lärt sig av. Då försvann en sten som av en slump låg i samma femtedel: Sö 208, där namnet
  *Guðlaug* på dubbelmonumentet Sö 206/208 är helt bevarat.
- Namnen i en skadad text paras med de huggna orden genom `align` och inte bara när ordantalen är lika. Sö 208 ger nu
  Guðlaug, Hjalmlaug, Torsten, Fröslunda och Ännebrant.
- Textmodellens cache är ny (`textmodel-7`). Blindprovet i analysplanen kördes med den tidigare versionen.

### Bild i hög upplösning från 3D-verktyget
- En ny knapp i 3D-verktyget sparar den aktuella vyn som PNG i 2, 4 eller 8 gånger skärmens upplösning, högst 8192
  bildpunkter på längden. Vinkel, ljusriktning, ljushöjd och kontrast blir desamma som på skärmen.
- Bilden används för att läsa spår eller som figur. Meddelandet påminner om att ange vem som skannat stenen.

### Mjuka spår i panelen
- I ett prov där vart femte spår är felläst gav hårda spår 44 % rätta helord. Det är sämre än utan spår (56 %), och av
  modellens "minst 95 % säkra" svar stämde bara 62 %. Med mjuka spår (`trace_eps` 0,05) blev det 73 % rätta helord och
  96 % rätt bland de säkra. Med rätt lästa spår blir mjuka spår 81 % mot hårda 85 %.
- Panelen använder nu mjuka spår. Bevarade runor inne i en sammanslagen lucka är alltid låsta (`hard`), och när en
  sådan lucka har ett felläst spår prövas också runorna som spåret utesluter.
- Textmodellens cache är ny (`textmodel-5`).

### Luckor som fylls tillsammans
- Flera förlorade runor i samma ord fylls som en lucka (`merge_runs`). Bevarade runor mellan dem låses, så att ett
  ord inte ser säkrare ut än det är.
- När en sådan lucka täcker två ord får varje position sitt eget ord (`restore_all(positions=...)`). Före rättelsen
  rapporterades spannets första ord för alla dess delar, och panelen kunde visa nästan 0 % för ett rätt ifyllt ord.
  Textmodellens cache är ny (`textmodel-4`).
- Spår kan vara mjuka (`trace_eps`): en ifyllning som strider mot ett spår prövas ändå, med ett avdrag per runa, så
  att en felläst rest inte stänger ute rätt svar.
- Rapporten över de verkliga luckorna tar flera indatafiler (`--fold` körs parallellt), och okända ord räknas rätt.

### Ifyllning av förlorade runor: spår och ristare
- `restore(allowed=...)`: synliga rester av en förlorad runa begränsar vilka runor som prövas, och när få
  kombinationer återstår prövas alla. Det gör att också namn utanför ordförrådet kan hittas.
- `data/rune_traces.json` (`scripts/rune_traces.py`) anger vilka runor som ser likadana ut i en bevarad halva eller
  tredjedel.
- Simulerat prov, med samma 1 616 luckor som utan spår, där halva runan är synlig:
  - helt ord: 56 → 85 % rätt
  - hela namn: 12 → 66 % rätt

  Med en blandning av inget, en tredjedel och hälften är siffrorna 77 % och 49 %.
- Ristarens stavning (stavningsträdet ner till ristaren) och namnkrets (`carver`, `lam_carver`): ingen mätbar vinst
  på 270 stenar med känd ristare.

### Läsning och luckor på inskriftssidan
- Ny panel med sannolikhetsmodellens läsning ord för ord, förslag för förlorade runor och omräkning med de spår
  användaren markerar. Panelen visar också datering ur språket och översättningsutkast på svenska och engelska.
- En sten läses av en modell som inte har sett den (fem delar).
- `src/textmodel.py`, `api/routers/textmodel.py`, `web/src/components/TextModelPanel.tsx`.

### Svenska översättningsutkast via danska
- Översättningsutkasten (`src/rungloss.py`) kan gå via danska. Danske Runeindskrifter (runer.ku.dk) har danska
  översättningar av 596 inskrifter i Rundata. En andra ordlista lärs mellan dem och Rundatas fornvästnordiska
  standardformer, och ord som den känner väl förs över till svenska med en handgranskad lista (`DA_SV`). Danskan
  skiljer *lät resa* från *reste*, har *sina bröder* och nordiska namnformer (Torbjörn).
- Svensk ordföljd: *sin fader*, *denna sten*, *god dräng* i stället för fornspråkets *fader sin*, *sten denna*,
  *dräng god*.
- Prov på 215 danska inskrifter (`scripts/runlm_gloss_da_test.py`):
  - utkastets ord som stämmer med facit: 41 % → 48 %
  - ordpar i rätt följd: 9 % → 32 %

  Facit är den danska översättningen i svenska ord, vilket gynnar den danska vägen något (METHODS.md, avsnitt 8.1).
- Den danska tabellen ligger lokalt och publiceras inte.

### Publicerade artiklar når webbplatsen igen
- Analysmotorn startar git och Rscript med posix_spawn i stället för att kopiera sin egen process (`src/spawn.py`).
  I den långkörande motorn dog git och R med signal 11, så en publicerad artikel (Maltstenen, 15 oktober) skrevs
  till `web/content/articles.json` men pushades aldrig, och R-modulerna föll på samma sätt.

### Runtextmodellen, steg 2 och 3: fler stenar och epoker
- Fler ordpar: avsnitt där ordantalen skiljer sig radas upp ord för ord (`align`), så att skadade och återställda
  ord inte längre kostar hela avsnittet. 27 218 ordpar från 2 877 inskrifter i stället för 17 341 från 1 479;
  rätt lästa ord +0,84 procentenheter (säkert över slumpen).
- Epoker: stavning och ordföljd efter fas (tidig/sen vikingatid), epok (800-talet, 900-talet, 1000–1070,
  1070–1150), trakt, landskap och ristare. När epoken är okänd vägs läsningarna i de fyra epokerna, vilket också
  daterar texten: rätt epok i 58 % av 2 046 daterade inskrifter (44 % för den vanligaste epoken).
- Namn: namn som ordförrådet saknar sätts ihop av namnled ur träningstexternas namn (`NameModel`). Namn stod för
  59 % av felen; rätt lästa ord +1,42 procentenheter, till 83,5 % (+2,12 mot första versionen).
- Dateringens säkerhet kalibreras med en temperatur skattad på dateringsprovet (`fit_temperature`).
- `scripts/runlm_compare.py` jämför två prov sten för sten; `scripts/runlm_dating.py` prövar dateringen.
- Prövat och inte infört: medeltida inskrifter som stavningsdata och anpassning till den enskilda stenen (ingen
  mätbar vinst). METHODS.md, avsnitt 8.1.

### Sannolikhetsmodell för runtext
- Ny modul `src/runlm.py`: läser en inskrifts huggna grupper utan tolkning och anger för varje ord hur sannolikt
  det är, ur en stavningsmodell skattad på Rundatas ordpar, ett ordbigram över Rundatas normaliserade text och
  Eddans ordförråd. Omstridda runor kan jämföras genom textens totala sannolikhet (METHODS.md, avsnitt 8.1).
- `scripts/runlm_calibrate.py` prövar modellen med femfaldig korsvalidering på 808 inskrifter och kalibrerar dess
  sannolikheter (rätt ord 81 %, rätt ordgränser 92 %, kalibreringsfel 0,003). `scripts/malt_decode.py` läser
  Maltstenen (DR NOR1988;5), som aldrig ingår i träningen.

### Runigenkänningen på en vittrad sten med bildfält: bristen dokumenterad
- Kända brister (version 2026-10-14) och METHODS.md, avsnitt 3: på Sö 164 låg 18 av 67 igenkända runor i bildfältets
  skepp och kors, och de flesta runorna i banden var en enda stav. Stenens medelvärden påverkades inte. Tre
  regeländringar prövades på sju stenar och förkastades, eftersom de hjälpte vittrade stenar men tappade runor på
  välbevarade; reglerna ändras först när handmärkta facit finns.
- Statistik i R: när R avbryts av en signal (minnesbrist, krasch) säger felet vilken, i stället för ett tomt
  meddelande (`src/r_bridge.py`).
- Stenanalys från terminalen (`scripts/full_stone_analysis.py`) följer nu Vitki-protokollet i huvudanalysen och
  mäter bara runor, som sidan Stenanalys; förut fick den varken protokollets fasta rutnät eller runurvalet uttryckligen.

### Läsningar med några få runor räknas inte som bekräftade
- En blind läsning som bara har färre än 12 läsbara runor får statusen *ej prövbar*, inte *bekräftad*
  (`src/reading.py`, `validate`). Upptäckt i stenanalysen av Sö 164: läsningen av hela stenen gav bara ordet *sin*,
  som räknades som 100 % rätt. Korta ord finns i de flesta inskrifter, så att de stämmer säger ingenting om att
  bilden är läst.

### Artiklar: tydligare bilder och månadens artikel direkt i listan
- **Bilderna i artikeln:** Admin visar vilka bilder artikeln har just nu, på svenska och engelska, med tumnagel,
  bildtext och Ta bort. En rad vid publiceringsknapparna säger hur många bilder som följer med och varnar när de
  två språken inte har samma bilder.
- **Flera foton per sten:** Hämta bilder ger upp till sex fritt licensierade bilder per sten, ur Wikidata och stenens
  kategori på Wikimedia Commons (`src/commons.py`, `stone_photos`).
  - Foton står först, äldre teckningar och bokplanscher sist, och ★ märker Wikidatas egen bild.
  - En bild som redan finns i texten märks I artikeln. Finns en annan bild av samma sten blir knappen Byt, så att
    ingenting infogas två gånger.
  - Varje åtgärd säger var bilden hamnade.
  - Urvalet visar små tumnaglar, så att panelen laddar snabbt.
- **Vad som händer vid publiceringen:** en bild kommer in i texten bara genom Infoga eller Byt, på båda språken
  samtidigt. Vid publiceringen behövs inget mer: fotona visas direkt från Commons, och figurerna ur R kopieras till
  webbplatsen av sig själv. Panelen säger det nu.
- **Bildtexter:** fotografens namn rensas från Commons anmärkning om fotografer som inte kan läsas maskinellt. Museernas
  gamla foton med "No restrictions" (Flickr Commons) får tas med, med texten "inga kända upphovsrättsliga
  begränsningar". Signum som `Ög Fv1958;252` och `DR NOR1998;21` hittas också i texten.
- **Månadens artikel i listan:** varje publicerad artikel har knappen Gör till månadens artikel, och den som är det
  har Inte månadens artikel. Bara en åt gången; datum och text ändras inte, och webbplatsen uppdateras om en halv
  minut (`POST /api/admin/blog/featured`).
- **Webbplatsen publiceras säkrare, och Admin visar hur det gick:**
  - Om git är upptaget när appen ska publicera, försöker den igen i upp till en kvarts minut.
  - Varje fel loggas med gits eget meddelande.
  - Det senaste försöket sparas (`data/cache/site_publish.json`, `GET /api/admin/site/publish`). Rutan
    Webbplatsen visar om webbplatsen fick ändringen, om försöket misslyckades och om något väntar på att pushas.
  - Vid start kontrollerar appen att den kan använda git.
- **Bildsökningen tål ett långsamt Wikimedia:**
  - Wikidatas frågetjänst får en ny chans när den inte svarar. Svarar den ändå inte söks bilderna direkt på
    Commons, och bara bilder av runstenar tas med.
  - Felet visas i bildpanelen i stället för högst upp på sidan.

### Kartan: rikenas gränser och jämförelse mellan länderna
- **Rikenas gränser:** alla kartvyer kan visa de ungefärliga gränserna för svear (Svitjod), götar, Danmark, Norge,
  Gotland och Jämtland omkring 890, 1025 och 1200. Varje område har en förklaring med källa (Ottar och Wulfstan, Adam av
  Bremen, runstenarna, landskapslagarna), och kärnområden, lösa och omstridda områden ritas olika
  (`web/src/lib/realms.json`, `src/components/RealmLayer.tsx`, METHODS.md 14g).
- **Geometrin** byggs av `scripts/build_realms.R` ur OpenStreetMaps landskap och Natural Earth
  (`web/public/geo/riken.geojson`).
- **Jämför länder** (ny flik): danska, norska och svenska runstenar ställs mot varandra, per land eller per rike och
  trakt omkring 1025, med andelar, intervall och prov med och utan tiden konstant (`GET /api/research/nordic`,
  `src/nordic.py`, METHODS.md 14f).
  - Mönstren läser Rundatas engelska översättning och translitterationen, som är gjorda lika i alla tre serierna.
  - Kors ingår inte, eftersom Rundata nästan bara beskriver korsen på svenska stenar.
- **Över gränserna:**
  - En modell ger varje dansk och svensk sten en dansk prägel ur ordval och stavning, tränad på samtida stenar
    (970–1050).
  - Prägeln redovisas per trakt, stilgrupp och ristare, med de tidigaste stenarna med dansk prägel hos svear och
    götar.
  - De danska stenar som Rundata kallar svenskgjorda får också låg dansk prägel i modellen, fast den aldrig sett
    anmärkningarna.
  - Rundatas anmärkningar om ett annat lands ristare och texterna som nämner ett annat nordiskt land listas.
- **Dansk prägel bygger på formeln och stavningen:** modellen i *Jämför länder* läser 13 drag i minnesformelns ordval
  och stavningen; tro och resor ingår inte längre (METHODS.md 14f). Samma modell, räknad om i R och prövad i båda
  halvorna, ligger bakom utkastet till artikeln ”Västgötarna satte stenen som danskarna”.
- **Danska fyndplatser och fornlämningar:** `scripts/fetch_dk_remains.py` hämtar hela Fund og Fortidsminder (Slots- og
  Kulturstyrelsen, gratis) och ger 65 av de 66 danska runstenar som saknar koordinater i Rundata en plats: registrets
  runsten, sockenkyrkan eller orten. Kartan visar nu 238 av 239 danska stenar.
- **Rättat:** METHODS.md 14e räknade Sö 102 som hednisk; den läser salu (själen), inte alu.
- **Rättat samma dag:** jämförelsens ristarsignatur räknade beställaren som ”lät hugga runorna” som ristare. Nu
  räknas bara den som ristade, högg, målade eller märkte: 13 danska stenar i stället för 20, och 266 svenska i
  stället för 326.

### Röstning på webbplatsen: Vitki i webbläsaren?
- **Röstrutan:** startsidan frågar besökarna om de hellre skulle använda Vitki direkt i webbläsaren, utan att
  installera något. De kan svara "Ja, gärna" eller "Nej, jag installerar själv" (`web/src/components/SiteVote.tsx`).
- **Hur rösten sparas:**
  - Rösten skrivs direkt till Firestore via REST, utan Firebase-paket och utan nyckel.
  - Säkerhetsreglerna (`web/firestore.rules`, samlingen `site_votes`) tillåter bara att en röst skapas, med exakt
    fälten fråga, val och språk.
  - Ingen kan läsa, ändra eller ta bort röster utifrån.
  - En röst per webbläsare (localStorage), och den är anonym.
- **Resultatet:** grundaren ser det i Admin under "Röstning på webbplatsen" (`GET /api/admin/site/votes`), läst med
  serverns egen behörighet.
- **Den publika webbplatsen** laddar inte längre Firebase Auth, eftersom den inte har någon inloggning.

### Den publika webbplatsen på GitHub Pages
- vitkirunor.se byggs av GitHub (`.github/workflows/site.yml`) som en statisk webbplats med startsidan och artiklarna.
  Appens sidor ingår inte, eftersom appen körs på den egna datorn.
- **Artiklarna:**
  - De artiklar som har gått live exporteras med sina figurer till `web/content/articles.json` och
    `web/public/figurer/` (`src/site_export.py`).
  - Schemalagda artiklar läggs aldrig i det publika repot i förväg.
- **Automatisk uppdatering från den lokala appen:**
  - En halv minut efter att en artikel har publicerats, ändrats eller tagits bort.
  - När en schemalagd artikels tid kommer, och om appen var avstängd då, när den startar nästa gång.
  - Knappen "Publicera webbplatsen" i Admin publicerar direkt. `SITE_PUBLISH=0` stänger av den automatiska uppdateringen.
- **Gemensam artikelkälla för sidorna (`web/src/lib/articles.ts`):** den lokala appen läser från analysmotorn, och
  webbplatsen läser från den exporterade filen.
- **Delningsbilderna:** de heter `delningsbild.png`, med filändelse, så att också den statiska webbplatsen visar dem
  när en länk delas.
- **Lokalt provbygge:** `scripts/build_site.sh` bygger webbplatsen i en egen kopia utan att röra den körande appen.

### Startsidan visar appen, och artiklarna lyfter fram författaren
- **Ny sektion "Så ser Vitki ut":** skärmbilder av Mönsterkartan, Inskrifterna, Stilgrupperna, Statistiken i R,
  Forskningsluckorna och Stenöversikten, var och en med en förklaring.
- **Ny del om 3D-analysen:** bilder ur vår studie av Sö 113, med djupkartan, släpljus, mätpunkterna och 254 tvärsnitt.
  Skanningen är Laila Kitzler Åhfeldts (2024), CC BY 4.0, och anges med källa. Bilderna ligger i `web/public/bilder`.
- **Inledningen:** den är utförligare, och statistikrutan under den är borttagen.
- **Versionsmärket och citeringsrutan:** de läser versionen ur CITATION.cff och följer därmed varje release.
- **"Verifierbara källor":** säger nu att mönster och ristarförslag räknas fram med statistiska modeller.
- **Sidhuvudet:** har en länk till GitHub i stället för två.
- **Artiklarna:**
  - Författaren står tydligt under ingressen, med länk till LinkedIn.
  - En ruta "Om författaren" avslutar artikeln.
  - Sökmotorerna får samma länk.
- **Inledningscitatet:** ett citat eller en runtext i början av en artikel sätts som citat, kursivt och indraget.
- **Bilderna i artiklarna:** de går att klicka upp i större storlek.

### Webbplatsen länkar inte in i appen
Den publika webbplatsen har bara startsidan och artiklarna. Appen körs på den egna datorn och laddas ner från GitHub.
- **Artiklarna:** "Se själv" visar bilder i stället för länkar in i appen. Det gäller kartverktygets vy före och efter
  omkring 1050, en karta över enskilda stenar för sällsynta mönster och förändringsmodellens kurvor. Alla ritas i R
  (`r/blogfig.R`, `src/blog_maps.py`) på svenska och engelska och fryses som artikelns egna figurer.
- **Länkar till metoden:** de går till METHODS.md på GitHub.
- **De publicerade artiklarna:** de är uppdaterade, och nya utkast från R-analyserna får samma bilder automatiskt.
- **Spärr i artiklarna:** en länk in i appen i en artikeltext visas som vanlig text, och SEO-kontrollen i Admin varnar
  för den. Tidigare bad SEO-kontrollen om sådana länkar.
- **Startsidan och artiklarnas sidhuvud och sidfot:**
  - "Öppna appen" heter nu "Ladda ner Vitki" och går till GitHub.
  - "Analysera en sten" och "Sök i Rundata" har ersatts av "Läs artiklarna" och "Metoden".
  - "Dokumentation" går till README på GitHub.
  - Den sista uppmaningen heter nu "Kör Vitki på din egen dator".
  - En streckad länk "Appen (lokalt)" syns bara när appen körs lokalt med `next dev`.
- **Publik byggläge:** `NEXT_PUBLIC_SITE_MODE=public` bygger den publika webbplatsen. Appens sidor leder då till
  startsidan och tas bort ur webbplatskartan.

### Rättat: alu räknades i själsbönen
- Mönstret "Hedniska eller rituella markörer" räknade Sö 102 som hednisk, eftersom ordet *alu* hittades i `(s)alu`, alltså
  *salu* (själen) i bönen *Guð hialpi hans salu* med en osäker första runa. Nu räknas *alu* bara som ett eget ord. Sex
  svenska runstenar har hedniska markörer, inte sju. Siffran ändras på kartan när korpusanalysen räknas om nästa gång.

### Artiklarna datumstämplas och kan schemaläggas
- Artiklarna publiceras inte längre per månad. De får datumet när de publiceras, och datumet visas i artikeln, listan,
  på startsidan och i delningsbilden, till exempel "12 oktober 2026" (svensk tid). Äldre artiklar utan tid visar sin månad.
- I Admin ersätts månadsfältet av en valfri publiceringstid och knapparna Spara utkast, Publicera nu och Schemalägg. En
  schemalagd artikel syns varken i listan eller på sin adress förrän tiden är nådd, och går sedan live av sig själv inom
  ett par minuter. I Admin märks den "schemalagd" med tid. När den går live anmäls den till sökmotorerna (IndexNow), om
  det är påslaget.
- En artikel som redan var publicerad behåller sitt datum när den redigeras. Nya utkast får adresser utan månad
  (`/artiklar/bonen-tystnade-…`), medan de publicerade artiklarna behåller sina adresser.
- Startsidan och artikelsidorna hämtas om varje minut, RSS och webbplatskartan var femte minut.

### Artiklar i stället för blogg, artiklarna högt upp på startsidan och "Vad är R?"
- Bloggen heter nu Artiklar och ligger på `/artiklar` (gamla länkar till `/blogg` leds dit), i menyer, metadata, RSS,
  delningsbilder och Admin.
- Startsidan behåller sin form men lyfter artiklarna: ett avsnitt direkt efter inledningen med den senaste artikeln
  (med foto) och fler artiklar, "Läs artiklarna" i inledningen och längst ner, och "Artiklar" först i menyn. Den
  gamla rutan om Månadens fynd är borttagen. Nytt avsnitt "Vad är R?" som förklarar R för humanister, med en rad R
  förklarad. Siffrorna om gravfälten (66 mot 24 %) och antalet R-analyser (elva) är uppdaterade.
- "Båda halvorna" förklaras: i artiklarna och utkasten ("två oberoende halvor"), i ordlistan med verktygstips på
  statistiksidan och kartan, och i "Så arbetar vi".

### Statistiken förklarad i klartext i bloggutkasten
- Utkasten förklarar vad siffrorna betyder i stället för att bara rada upp dem: det justerade p- eller q-värdet med en
  korrekt läsning (efter Holm: hur sällan ett så tydligt mönster skulle uppstå av en slump; efter Benjamini–Hochberg:
  hur stor andel slumpfynd som väntas bland så starka mönster), Morans I ("0 betyder ingen samling"), varför båda
  halvorna spelar roll och intervall som "troligen mellan". Förbehållen rensas från ren statistik, som förklaras i
  "Så säkra är vi".

### GitHub-statistik i Admin
- Admin visar repots statistik på GitHub: stjärnor, forkar, bevakare och nedladdningar av releaser, och med en
  `GITHUB_TOKEN` (i miljön eller i `.env`, aldrig i koden) kloner och besök per dag, varifrån besökarna kommer och
  de mest besökta sidorna. GitHub sparar trafiken i 14 dagar; appen sparar varje hämtning i `data/github/history.json`,
  så att historiken växer (`src/github_stats.py`, `GET /api/admin/github`).

### Bloggen uppdateras direkt vid publicering
- Bloggens sidor, delningsbilder, sitemap och RSS cachas med taggen `blog`, och Admin tömmer cachen när ett inlägg
  sparas, publiceras, avpubliceras eller tas bort (`/api/revalidate-blog`, bara för grundaren). Tidigare kunde ett
  nypublicerat inlägg dröja upp till fem minuter innan det syntes i listan.
- Ett utkasts adress följer med när månaden ändras (2026-09-…), så länge adressen inte är ändrad för hand.

### Bloggutkast i formen från ”Bönen tystnade”, med kartbilder ur R
- Utkasten från ett valt ämne följer det publicerade inläggets form: ett citat ur en sten med mönstret som krok (vald
  automatiskt, med foto från Wikimedia Commons), ingress, "Kort sagt", mönstret med siffror och diagram, en kartbild ur
  R-analyserna, "Så säkra är vi", hypotesen med vad som är nytt, en första prövning som räknas fram ur datan (ristarna
  bakom ett kluster, när en förändring slår igenom i olika landskap, skillnaden mellan landskapen med ristaren konstant,
  gravfälten före och efter 1050) med en skärpt hypotes, hur den kan prövas vidare, förbehåll, se själv och källor.
  Rubrikerna får en berättande form ("… breder ut sig", "… – ett kluster i Uppland").
- R ritar kartbilder för kartverktygets analyser: var varje mönster samlas (andel per område, heta och kalla områden,
  kluster) och genomsökningen av landskapet. Figurerna kan infogas i inlägg från Admin ("Figurer ur R-analyserna") och
  sparas som egna kopior, så att publicerade inlägg behåller sina bilder när analysen räknas om.

### Automatisk SEO för bloggen
- Inläggen renderas på servern och får av sig själva, när de publiceras: titel, beskrivning (hela meningar ur
  ingressen, högst 158 tecken), kanonisk adress, nyckelord (bland annat stenarnas signum), Open Graph som artikel med
  publiceringsdatum, Twitter-kort, strukturerade data (schema.org BlogPosting och BreadcrumbList), en egen delningsbild
  med rubriken och första fotot (med fotografens namn och licens), plats i sitemap med ändringsdatum och ett RSS-flöde
  (`/blogg/rss.xml`). Bloggens förstasida får Blog-data. Allt härleds ur inlägget (`web/src/lib/blogSeo.ts`).
- SEO-kontroll i Admin: förhandsvisning av sökträffen och tio punkter (rubrikens och beskrivningens längd, ämnesord,
  adress, mellanrubriker, bilder med alt-text, längd, länkar till appen, källor, engelsk version).
- Vid första publiceringen meddelas sökmotorer som använder IndexNow (Bing, Yandex m.fl.), bara när `INDEXNOW_KEY` och
  en publik `SITE_URL` är satta i produktionen.

### Välj ämne för Månadens fynd
- I Admin finns en lista med ämnen: de utmärkande eller dolda mönster som R-analyserna har hittat och som håller i
  båda halvorna (nya mönster att pröva först, högst fyra per område, redan skrivna sist). Ett klick skriver ett utkast
  kring ämnet efter bloggens mall – "Kort sagt", vad vi ser med ett diagram (stilgrupper, landskap eller kluster),
  "Så säkra är vi", hypotesen, hur den kan prövas, förbehåll, se själv och källor – på svenska och engelska, med foton
  av stenarna (`src/blog_topics.py`, `GET /api/admin/blog/topics`, `GET /api/admin/blog/draft?topic=`). Inlägget
  minns sitt ämne.

### Snabbare laddning
- Servern komprimerar svaren (gzip): de stora JSON-svaren blir omkring en tiondel så stora (stenöversikten 525 → 55 kB,
  korpusanalyserna 730 → 104 kB). De stora svaren byggs en gång per dataversion och skickas sedan som färdiga byte
  med ETag, så att ett nytt besök får "oförändrat" (304) utan innehåll (`api/cache.py`); anrop som kommer samtidigt
  väntar på samma bygge. Fynden i Forskningsluckor tar 15 ms i stället för 0,7 s (bergart och språkdrag per sten och
  ristare sparas), kartans inskrifter 3 ms i stället för 0,3 s, och bloggens inlägg läses ur Firestore högst en gång i
  minuten.
- Firebase laddas när det behövs i stället för med varje sida: inloggningen efter att sidan har visats, Firestore bara
  för inloggade. Meddelandena till alla hämtas från servern (`GET /api/messages`). Diagrammen använder Plotlys mindre
  paket (punkt- och stapeldiagram). JavaScript som varje sida laddar direkt har halverats (omkring 400 → 190–230 kB
  komprimerat) och diagrambiblioteket krympt från 1,4 MB till 350 kB.
- Laddningsraden visar verklig andel också för komprimerade svar (`X-Content-Length`).

### Rättelse: flyttade stenar och kristna böner
- Stenar vars plats i Rundata är en kyrka, kyrkogård, prästgård, ett kloster, slott, en skola eller ett museum räknas nu
  som flyttade (`is_moved`, `src/r_bridge.py`). Tidigare prövades bara placeringen, som oftast är tom för stenar vid
  kyrkor, så omkring 420 stenar vid kyrkor räknades som stående på sin ursprungliga plats. Med det rättade urvalet klarar
  ingen kombination i genomsökningen av landskapet justeringen: sambanden mellan kristen bön och kyrkor och mellan kors
  och centralorter var till stor del en följd av felet (METHODS.md 17, "Rättelse 2026-10-12").
- Sökningen efter kristna böner hittar nu också *hiælpi*, *hialpin*, imperativet *hialp* och böner där gudsnamnet är
  skadat; själsbönen hittar *sal*, *sialu* och *sel*.
- Nytt prov i `remains.R`: följer bönen de tidiga kyrkorna (uppförda senast 1200) eller de senare? Visas under
  Statistik och som fynd i Forskningsluckor; med det rättade urvalet en indikation.

### Månadens fynd med bilder, diagram och faktarutor
- Blogginläggen kan ha foton (`![alt](url)` med bildtext), faktarutor (`:::box`) och stapeldiagram (`:::chart`).
- Foton av de stenar en text nämner hämtas automatiskt ur Wikidata och Wikimedia Commons, bara fritt licensierade, med
  fotograf och licens i bildtexten (`src/commons.py`, `POST /api/admin/blog/images`); utkastet från månadens fynd får
  bilder, "Kort sagt" och "Så säkra är vi" av sig självt.

### Export av tabeller
- Alla tabeller i appen kan laddas ner som CSV eller Excel, och Inskrifter kan exportera hela sökurvalet. Filerna har
  alltid källan: data och licens (Rundata ODbL, Kulturmiljöregistret, OpenStreetMap, Wikidata, mätkorpusen CC BY 4.0),
  adressen de exporterades från, datum och upphovsangivelsen för Vitki.

### Laddning, karta och dokumentation
- En laddningsrad överst visar förloppet när sidor och data laddas, med verklig andel när storleken är känd.
- Mönsterkartans tidsläge kan dela stenarna omkring 1020, 1050 eller 1075 (stilgruppernas gränser) i stället för alltid
  1050, med en förklaring om att kristnandet pågick under hela runstenstiden.
- Stenöversikten säger till när attribueringsmodellen i R inte ingår och visar "Ingen" i stället för en ensam nolla.
- Om Vitki är omskriven: alla funktioner, datakällor med licenser och den aktuella licensmodellen (GPL-3.0-only med
  tilläggsvillkoren i NOTICE).

### Mönsterkartan omgjord för att hitta samband
- Kartan är ordnad efter frågan i stället för verktygen: *Upptäck* överst med de starkaste fynden som kort (ett klick
  ställer in kartan), en sidopanel i tre steg – mönster, jämför med (tid, platser eller kluster), svaret i ord – och
  kartan i full storlek. Platslagret för den valda jämförelsen visas av sig självt; områdets storlek och fler lager
  ligger under "Fler inställningar", och rutnätet med alla samband är hopfällt under kartan.

### Hot spots och kluster (R: spdep, smerc)
- Ny korpusanalys `hotspots.R`: Morans I (klustrar mönstret alls?), Getis-Ord Gi* (heta och kalla områden) och
  Kulldorffs rumsliga scanstatistik (kluster där mönstret är ovanligt vanligt), varje kluster prövat i båda halvorna och
  justerat över mönstren. Kluster och heta stenar visas på kartan under "Jämför med → Kluster" och kluster som håller blir
  mönster i Forskningsluckor (METHODS.md 17). R-paketen spdep och smerc läggs till i `r/install.R`.

### Dolda mönster i landskapet (R)
- En genomsökning i R prövar varje mönster på kartan mot avståndet till varje sorts plats (ortnamn, kyrkor,
  fornlämningar) utan vald radie, med landskapet konstant, alla kombinationer justerade tillsammans och varje träff
  prövad i båda halvorna och med tiden konstant (METHODS.md 17).
- På mönsterkartan visas resultatet som ett rutnät – varmt där mönstret är vanligare nära platserna, kallt där det är
  ovanligare, ✓ där det håller i båda halvorna. Ett klick visar kombinationen på kartan.
- Första resultaten (kristna markörer och kors nära centralorter, kristen bön nära medeltida kyrkor) höll inte när
  flyttade stenar räknades bort på rätt sätt; se rättelsen ovan.

### Platser på kartan och i stenprofilen
- Mönsterkartan kan visa platser över sexkanterna: teofora och sakrala ortnamn, centralortsnamn, medeltida kyrkor,
  gravfält, högar, färdvägar, broar och fornborgar, med namn och uppgift när man håller muspekaren över dem.
- "Nära en plats" jämför det valda mönstret nära en sorts plats (1–5 km) med övriga stenar, med landskapet konstant,
  och kan begränsa kartan till stenarna nära platserna. Provet märks som utforskande; det fullständiga ligger i
  Statistik.
- Stenöversikten har ett kort "Landskapet runt stenen": närmaste ortnamn, kyrka och fornlämning av varje slag med
  avstånd och länk, och en markering om stenen är flyttad (METHODS.md 13c, 13e).
- Rättat: områdeskontrollen sa "koordinater saknas" när ristaren inte hade några andra stenar att jämföra med.

### Förkristna kultnamn och stenarnas budskap
- Ortnamn som tyder på förkristen kult – teofora namn som Torsvi, Odensala, Ullevi och Frösö, sakrala namn som Vi, Harg
  och Hov – ur OpenStreetMap (Lantmäteriets ortnamn), med Husby och -tuna som jämförelse, och medeltida kyrkor ur
  Wikidata (`scripts/fetch_place_names.py`).
- Kristen bön är vanligare på stenar inom 2 km från ett teoforiskt namn (28 % mot 15 %, oddskvot 2,2), håller i båda
  halvorna och när stenarna vid ett namn i taget utelämnas, men inte vid centralortsnamn utan kult. Resultatet hänger
  delvis på radien och redovisas som mönster att pröva. Teofora namn ligger oftare nära en medeltida kyrka (indikation).
- Visas under Geografi i Statistik och som mönster i Forskningsluckor; METHODS.md 17.

### Stenarna i sitt landskap: nya källor
- Lämningar ur Kulturmiljöregistret (Riksantikvarieämbetet, via K-samsök): gravfält, högar, färdvägar, broar,
  fornborgar och hamnanläggningar, omkring 53 000 poster (`scripts/fetch_raa_remains.py`). Den nya korpusanalysen
  `remains.R` jämför stenarnas avstånd till lämningarna med slumpvisa punkter i samma trakter och prövar om närheten
  skiftar med tiden, med kristna markörer och för brostenar, i båda halvorna av korpusen. Flyttade stenar (vid kyrkor, i
  museer) räknas inte. Resultaten visas under Geografi i Statistik och som mönster i Forskningsluckor: 61 % av stenarna
  står inom 500 m från ett gravfält mot 21 % av slumppunkterna, lika ofta före som efter 1050 och för kristna stenar.
  Att brostenar står nära färdvägar håller inte i båda halvorna och är en indikation.
- Dåtidens strand: avståndet till vatten prövas också mot en modellerad strandlinje omkring år 1000 (dagens höjd under
  landskapets landhöjning, terrängmodell med omkring 300 m upplösning), med samma slumppunkter som för dagens vatten.
  Närheten blir tydligare (3,6 mot 5,3 km; i Uppland kvoten 0,64 → 0,53) och redovisas som mönster att pröva.
- Helhetsbilden i Statistik har ett stycke om landskapet, och själsbönen på brostenar räknas inte längre som nytt
  mönster när den inte håller i båda halvorna.
- Landningssidan har ett nytt avsnitt om de nya källorna och vad de tillför.

### Månadens fynd (blogg)
- En blogg på /blogg med ett inlägg i månaden om de mest intressanta mönstren och fynden. Inläggen skrivs och
  publiceras för hand i Admin; knappen "Utkast från månadens fynd" fyller i ett utkast med de mönster som är nya eller
  har ändrat status sedan förra publicerade inlägget, månadens största förskjutning i mönsterkartan och en engelsk
  version ur ordlistan. Inläggen kan ha en egen engelsk version.
- Inläggen ligger i Firestore-samlingen `posts`, som bara servern läser och skriver; regeln för webbläsarna är
  oförändrad (stängd), så ingen ändrad regel behöver driftsättas.

### Mönsterkarta
- Kartan öppnar med en mönsterkarta: sexkanter färgade efter hur stor andel av stenarna i området som har ett mönster –
  tro (kristna, hedniska eller rituella markörer, utan religiösa markörer, bön, själsbön, kors), skrift (stungna runor,
  monoftong, o-runan, r för ʀ, signatur) eller innehåll (bro, utlandsfärd, arv). Mönstret väljs med knappar, kartan kan
  delas i före och efter omkring 1050 och andelarna per landskap finns som tabell (METHODS.md 13e).
- Inskrifterna med filter ligger under fliken Punkter, med filtren fällda tills de behövs.
- Hedniska markörer är få: 7 av 2 318 runstenar (Torsåkallan, vígi-formler, förbannelser, alu, Tormotiv). Den stora
  gruppen är stenar utan religiösa markörer (1 203).

### Försiktiga påståenden, djärva hypoteser
- Varje mönster i Forskningsluckor och Statistik har nu tre delar: vad vi ser, en hypotes om vad det kan betyda och hur
  hypotesen kan prövas. Förbehållen ligger i en fällbar ruta.
- Upptäckt med Benjamini–Hochberg, bekräftelse med Holm och prövning i två halvor av korpusen (uppdelad per socken, alla
  stilgrupper i båda). Märket "Håller i båda halvorna" visar tydliga mönster. Signerade stenar används inte som facit,
  eftersom signaturerna är sena.
- Mindre stränga regler där de var för hårda: generationsskifte i stället för krav på trend inom ristare, utan ändgrupper
  som information, textlängd utan bro- och bönefraser, landskap utanför U/Sö när förskjutna dateringar håller, små
  effekter som mönster. Ny grupp "Indikationer" för idéer med förbehåll.
- Rune granskar som en kritisk vän: fel, för säkra ord och hypoteser hålls isär.

### Engelsk version
- Hela appen finns på engelska: språkknappen (i menyn och på landningssidan) översätter allt som visas –
  gränssnittet, forskningstexterna, fynd, mönster, tolkningar och tabeller – mot en ordlista med drygt 4 600
  meningsmallar. Siffror, ristare och orter hålls utanför mallarna och språkdrag och bergarter översätts var för
  sig, så att samma mall räcker för alla stenar. Svenskan är originalet; runtext och källtext översätts aldrig.
- Rapporterna (stenrapporten i alla publiceringsformer och beslutsunderlaget) skrivs på engelska när språket är
  engelska. Rune svarar på det valda språket. Språkvalet sparas.
- Verktyg för att hålla ordlistan aktuell när texter ändras (METHODS.md 14g, scripts/README.md).

### Gränssnitt
- Snabbknappen "Generera akademisk rapport för aktuellt arbetspass" i toppraden är borttagen, liksom avsnittet
  "Arbetsgång" på landningssidan. Kontoinställningarna har ett fält för e-post (förvalt kontots adress), och
  författarnamnet är inte längre förifyllt med grundarens namn för nya användare.
- Rättat: Rune-uppslaget tolkade andelar som "Vg 84 %" som signum (Vg 84).

### Beslutsunderlag om attribuering
- Förslaget till omprövning i Stenöversikt är nu ett fullständigt beslutsunderlag: slutsats och rekommendation först,
  varje metod förklarad (vad den jämför, vilka data, vad talen betyder och hur ofta den har rätt – t.ex. hur ofta en
  ristare med modellens sannolikhet var den rätta i korsvalideringen), den prövade ristaren mot Rundatas, språkdrag drag
  för drag, andra kandidater, vad som skulle avgöra frågan, källkritik, ordlista och bilaga (METHODS.md 14f).
- Ärlig rekommendation: *starkt* ger förslag, *måttligt* granskning, *svagt* ingen ändring; en signerad sten får
  aldrig ett förslag om en annan ristare (tidigare kunde t.ex. U 287, signerad av Öpir, få ett förslag om Fot 2 med
  sannolikheten 0,19).
- Rättat: bedömningen i beslutsunderlaget räknade modellen och ortografin två gånger (i styrkan och som andra belägg)
  och område och stilgrupp som oberoende fast de ingår i modellen; *starkt* kräver nu att modellen och ortografin
  (statistiskt säkerställd) båda pekar på ristaren och att inget talar emot (51 → 4 av 1 003 alternativ).
- Tydligare text: hur beläggen hänger ihop, stenar med flera ristare, träffsäkerheten också när hela socknar hålls
  utanför, att sannolikheten för stenar utan ristare inte är korsvaliderad, och bergartens jämförelse ("inte tydligt
  vanligare" i stället för "lika vanlig").
- Granskning av U 735 (Rune): ett svagt underlag är ett internt arbetsunderlag, inte ett förslag att skicka; när
  jämförelsen talar för Rundatas ristare heter dokumentet "Prövning av … : Rundatas attribuering till … stöds".
  Det som talar för Rundatas ristare framför den prövade räknas och redovisas (modellen föredrar den, språkdragen
  stöder den signifikant, den har stenar mycket närmare, stenens stilgrupp hör till dess kärna). Runor 2020 räknas
  inte som oberoende belägg när den anger samma ristare som Rundata. Hypotesens ursprung anges. Den samlade styrkan
  kallas inte stark när modellen inte stöder förslaget eller stavningslikheten inte är signifikant. Jämförelsestenarna
  är stenar där ristaren är ensam ristare och som finns kvar; närmare stenar med flera ristare eller som är försvunna
  nämns med skäl. Bara de begränsningar som gäller dokumentet. Kontaktraden får e-post ur kontoinställningarna.
- Ortografins förstaval räknas fullt i Stenöversiktens styrka bara när det leder tvåan med minst 0,05 i likhet
  (U 735: Öpir 1 0,66 mot Balle 0,64 räknas som oavgjort). En stilgrupp stämmer med ristaren bara om den hör till
  kärnan (minst en tiondel av stenarna); en ovanlig stilgrupp inom kärnans tidsram avgör inte. Tidsramen för en
  ristares stilgrupper är kärnans, i alla avsnitt. Språkdragen redovisas som för, emot och neutrala, och andelar på
  färre än tio inskrifter markeras som osäkra. En ristare som nämns två gånger i samma inskrift räknas en gång.
  Kontrollen på signerade stenar: falsklarmen (alternativ ≥ 0,4 för en signerad sten) minskar från 57 till 33 av 246;
  *omstridd* 49 → 26, *kan vara felbedömd* 15 → 9.

### Granskning av R-fynden (Rune, 2026-10-11)
- Tredje omgången: "Säkerställt" heter nu "Signifikant" i hela appen, och p-värdet förklaras som hur ovanligt ett så
  tydligt resultat vore utan ett verkligt samband – inte som sannolikheten att resultatet är sant. Landskap med färre
  än tio stenar från mittperioden (stenar vars stilgrupp omfattar år 1050) får ingen skattning utan redovisas som
  otillräckligt underlag. Formelvalets CA-dimension beskrivs i klartext (stenar utan bön mot stenar med bön).
  Sambandet själsbön–brostenar märks efter det kontrolltest som inte håller (textlängden), inte efter huvudmodellen.
  Avståndet till vatten får förbehåll för vikingatidens högre strandlinje och för parstenar.
- Andra granskningsomgången (stavning, runor, böner, broar, geografi, seriation, formelval): ordbaserade mått och
  rätt nämnare i stället för "minst en på stenen" (monoftongen per æi-ord och lexem, stungna runor per runa bland ord
  där de kan förväntas, ʀ och omvänd stavning, åsrunan för /o/ och för ą, 'och' som auk/uk/ok/ak, æftiʀ för sig);
  kontroller med bara signerade stenar, inom ristare, utan ändgrupperna, med textlängd, bevarade inskriftsslut och för
  Uppland och Södermanland var för sig; toppar vars intervall når periodens kant tolkas inte; flera toppar samma år
  märks som möjlig artefakt; landskapsjämförelser bara mellan landskap med tillräckligt underlag, alla landskap med
  intervall och märket för det visade paret; ristarnas koncentration också mot samma stilgrupp, samma härad och på
  signerade stenar (inte mer lokala än häradet); seriationen utan kors, utlandsfärder och föränderliga drag, inom
  härad och inom ristare; formelvalet med signerade stenar, utan själsbönen och på bevarade slut; stavningsavståndet
  inom Uppland, på stenar utan ristare och med tiden konstant. Själsbönen räknar inte längre brostenarnas avsiktsfras
  (fyrir and hans).
- Märket "Säkerställt men osäkert" när ett säkerställt test hör till en indikation, en svag effekt, ett cirkulärt
  resultat eller en måttlig/svag tolkning. Språkdragstabellen visar landskapets andel och vilka drag som inte räknas.
- Landskapsjämförelserna: q justerat med Holm över alla drag (tidigare p), observerade andelar i stenar från
  mittperioden bredvid modellens skattning, antal attribuerade ristare per landskap och samma test utan ristareffekten.
  Spridningsförlopp anges bara för drag som stadigt ökar eller minskar; annars är jämförelsen en ögonblicksbild.
  Jämförelser utanför Uppland och Södermanland, med få ristare eller få stenar, är *indikationer*. Kristen bön skiljer
  sig inte säkerställt mellan landskapen efter justeringen.
- Förbehållen följer dragets typ (stavning, ordval, runformer, formler, ornamentik) i stället för samma text för alla;
  förbehållet om ristarna nämner formulärbruk och ornamentik och att justeringen kan snedvrida åt båda hållen.
- Toppår anges med 95 % intervall (koefficientdragningar och omräkningar med nya årtal), aldrig som ett exakt år.
- Avstånd till vatten prövas mot en lokal nollmodell: slumpvisa punkter inom 5 km från runstenar (där folk bodde och
  rörde sig); jämförelsen mot hela landskapet finns kvar som kontroll. Resultatet håller (4,2 mot 5,3 km).
- Mönster som är kända i forskningen (stungna runor, signaturer, åsrunan, kristna formler, monoftongeringens geografi,
  brostenarnas själsböner, vattennärhet) märks *bekräftar*; säkerställda men små förändringar (under 10
  procentenheter) blir *svag effekt*, och förändringar som inte håller i minst 8 av 10 omräkningar *indikation*.
  Kors är en del av ornamentiken och därmed inte oberoende av dateringen (*begränsning*).
- Klustringens silhuett prövas mot omblandade data och ristarnas sammanhållning mäts direkt (i stället för bara
  justerat Rand-index).
- Korpusdimensionerna prövas mot tiden icke-linjärt (eta² mot stilgrupp, daterade stenar) och ristarens eta² mot
  omblandade etiketter: dimension 1 följer ristaren (27 %, slumpnivå 6 %) mer än tiden (6 %).
- Släktrelationerna före och efter 1050 prövas inom landskapen (Cochran–Mantel–Haenszel): skillnaden för 'broder'
  och 'partner/kamrat' försvinner – de sena stenarna är till 94 % uppländska.
- De okända ristargrupperna prövas utan tidsberoende drag (renhet 69 % även då; grupperna återkommer till 58 %), och
  texten anger entydigt att arbetsnamnen är appens etiketter för nya grupper.

### Konton, admin och säkerhet inför publicering
- Servern kontrollerar Firebase-inloggningen (ID-token, avstängda och återkallade konton) med Firebase Admin SDK
  (`api/auth.py`). Grundaren anges på servern med `ADMIN_UIDS` eller `ADMIN_EMAILS` – ingen inloggning står i koden.
- Admin-sidan (bara för grundaren): antal registrerade, nya och aktiva konton, registreringar per månad, avstängning
  och återöppning av konton, och meddelanden i appen till alla eller till ett konto (klockan i sidhuvudet).
- Avstängda konton kan inte logga in, deras inloggningar återkallas och Firestore-reglerna nekar dem direkt
  (`banned/{uid}`); meddelanden kan bara skrivas av servern.
- Rapporter: Stenrapport (fullständig) är öppen för alla; korpusrapporten och de övriga publiceringsformerna är bara
  för grundaren, också på servern.
- Serverns egna AI-nycklar används bara med `ALLOW_SERVER_AI_KEYS=1` (lokal utveckling); på en publik server använder
  varje användare sin egen nyckel. `.env` skriver inte längre över serverns miljövariabler.

### Mobil och surfplatta
- Sidomenyn är en utfällbar meny under 1024 px, öppnas med menyknappen i sidhuvudet och stängs när man väljer en
  sida; sidhuvudet, chatten, marginalerna och kartans filter är anpassade för små skärmar. Alla sidor är kontrollerade
  i 390 och 820 px bredd utan sidledsskroll.

### Karta
- Nya filter: fritext i inskriften (translitterering, normalisering, översättning, plats), landskap, innehåll (de nio
  kategorierna), ristarstatus, material, kors, språkdrag med värde, status i Stenöversikt och bara svenska
  vikingatida runstenar.
- Färg efter ristarstatus, material, innehåll, språkdrag eller status i Stenöversikt, utöver stilgrupp och period.
- Aktiva filter som etiketter, fördelning per landskap, kartan zoomar till det som syns, filtren sparas i adressen
  (delbar länk) och det som syns kan laddas ner som CSV.

### Mätmetod `groove-5`
- Den automatiska spåranalysen mäter bara spår som känns igen som runor; slinglinjer, ornamentik och möjliga
  sprickor sorteras bort med skäl (METHODS.md 1c, steg 5).
- Rättat: slingband som stängdes av runstavar fylldes och räknades som en enda för bred yta.
- Stenens medelvärden med runan som enhet (ICC); riktvärden 10 runor för att beskriva en sten och 20 för att
  jämföra stenar (`scripts/rune_sample_size.py`).

### Rapporter
- Elva publiceringsformer för stenrapporten: tidskriftsartikel, uppsats, avhandlingskapitel, runologisk utgåva,
  konferensabstract, poster, blogginlägg, pressmeddelande, antikvarisk rapport och dataartikel (METHODS.md 14e).

### Validering av huggspårsanalysen
- Facit-läge i 3D-vyn: alla spår mäts, inget förmärks, forskaren märker runor; `scripts/evaluate_rune_detection.py`
  mäter runigenkänningens precision och träffsäkerhet mot facit.
- `scripts/groove_robustness.py`: samma skanning mätt med ändrat rutnät, lutad normal, annan känslighet och
  förenklad skanning (METHODS.md 1e).
- Antalet igenkända runor jämfört med Rundatas translitterering (METHODS.md 1c).

### Statistik
- Attribueringsmodellen i R korsvalideras också grupperat per socken och härad (rätt ristare 72 % slumpvis,
  68 % på ny socken, 57 % i nytt härad), visat på sidan Statistik (R) och i fynden.
- Ny R-modul `change.R` och fliken Förändring: hur tio språkdrag, skriftdrag och kristna drag förändras över tid och
  skiljer sig mellan landskap, med plats och ristare konstanta (utjämnad tidskurva, rumslig utjämning, ristaren som
  slumpeffekt, omräkning med årtal dragna inom stilgruppens intervall), och om bro- och vägstenar oftare har
  kristna drag (METHODS.md 17).
- Ny R-modul `anonymous.R` och fliken Okända ristare: grupper av stenar utan ristare som liknar varandra lika mycket
  som en ristares stenar, validerade på stenar med känd ristare, jämförda med kända ristare i närheten och med
  arbetsnamn efter typstenens socken för grupper som inte liknar någon känd ristare; stenarna blir fynd i
  Forskningsluckor (METHODS.md 17).
- Nio nya språkdrag: ai i alla ord, ʀ skrivet med r, o-runan för o-ljud, stungen i, u och k var för sig, æftiR eller
  at, skiljetecken och bindrunor (METHODS.md 8). De ingår i attribueringsmodellen, klustringen och seriationen.
- Statistik (R) omgjord för den som inte kan terminologin: varje analys är en fråga med svaret i korthet, ett
  nyckeltal, säkerhetsnivå (säkert, troligt, osäkert), ett förslag till tolkning och vad resultatet inte säger
  (`src/r_explain.py`); översikten sammanfattar och tolkar alla frågor i en helhetsbild med förslag på nästa steg;
  detaljtabeller är hopfällbara, förändringstabellen har en minikurva per drag, och en ordlista samlar alla termer.
- Statistik (R): alla figurer kan förstoras (klick, full storlek, egen flik) och har en förklaring av hur de ska läsas;
  kolumnrubriker, nyckeltal, statusmärken och facktermer (q, Cramérs V, silhuettbredd, oddskvot …) förklaras när man
  hovrar eller trycker; Förändringens stora figurer visas i full bredd.
- Korpusanalyserna återanvänder resultaten från moduler som inte ändrats sedan en tidigare körning, så att en ändring
  i ett skript bara räknar om den modulen och de som bygger på den.
- Kristen bön känns igen även i osäkra läsningar (hakparenteser), som Kristr hjalpi, Guð biargi, Guð lætti och
  Guðs móðir (249 runstenar i stället för 214).

### Statistisk signifikans
- Statistiska modellens förslag har ett signifikanstest (max-statistik mot de sannolikheter felaktiga ristare får
  i korsvalideringen, Benjamini–Hochberg); *starkt* kräver q under 0,05 (METHODS.md 13d).
- Rättat: avstämningen mot Runor 2020 upprepade samma text i skälen varje gång Forskningsluckor laddades.
- Mönstren i hela korpusen visas som kort i två kolumner med filter (att pröva, bekräftar, begränsningar,
  säkerställda) och förklaring per mönster.
- Varje mönster och fynd anger om det är statistiskt säkerställt (q eller p under 0,05, med test), inte säkerställt
  eller inte prövat med signifikanstest; märks tydligt på Statistik (R) – med en egen sektion för säkerställda
  upptäckter (25 av 30 prövade mönster) och en ruta per fråga – och i Forskningsluckor, där fynden kan filtreras.
- Ortografins justering för att den bästa av alla ristare valts görs med max-statistik i stället för Bonferroni,
  som med 459 inskrifter i nollfördelningen aldrig kunde gå under 0,05; nu är 66 av 182 bekräftelser, 20 av 53 nya
  förslag och 3 av 15 motsägelser säkerställda.
- Förklaringskomponenterna (förklaring vid hovring, hopfällbara detaljer, säkerhets- och signifikansmärken,
  förstoringsbara figurer) och ordlistan är gemensamma (`components/Explain.tsx`, `lib/glossary.ts`).

### Forskningsluckor för den som inte kan terminologin
- Samma upplägg som Statistik (R): inledning på vardagsspråk med "Så läser du sidan" och ordlista, frågekort i stället
  för flikar (ny fråga: var saknas uppgifter?), och för varje fråga svaret i korthet, nyckeltal, förslag till tolkning
  och vad resultatet inte säger – framräknat ur data. Alla kolumnrubriker har förklaringar (ⓘ).
- Gemensamma komponenter för sidinledning, frågekort och svar (`components/Explain.tsx`).
- Stenöversikt, Jämför stenar, Syntes och Mätkorpus: inledning på vardagsspråk med läsanvisning och ordlista,
  förklaringar på mått och kolumner; Stenöversikt får en svarsruta med tolkning och kontrollen mot signerade stenar,
  Jämför stenar ett märke för om skillnaden i huggspår är statistiskt säkerställd.
- Tolkningens slutsats (starkt, måttligt, svagt, bekräftelse, redan känt, metodfel) syns direkt i fyndlistan, med
  filter per nivå; tidigare bara när raden öppnades.
- Fyndtabellen har fyra kolumner i stället för tretton (Sten, Fynd, Tolkning, Uppskattning) och skrollar inte i
  sidled; nyare källor, bergart och språkdrag visas som etiketter under fyndet, belägg, nyhet och relevans under
  uppskattningen, och en meny sorterar efter alla de tidigare kolumnerna.

### Granskning av U 1026: sluten modell, namnlösa ristare och bergart
- Modellens förslag: plats, stil och språkdrag ingår i modellen och räknas inte som oberoende stöd; träffsäkerheten
  anges med antal stenar och 95 % konfidensintervall; *starkt* kräver en väl underbyggd träffsäkerhet och inget emot.
- Rundatas "Samma som gjort …" läses in (namnlösa ristarpar); sådana stenar får högst *måttligt*, och modellens förslag
  för de kopplade stenarna och stenens typikalitet för ristaren vägs in.
- Fynd från R-analyserna visar Rundatas material (tidigare "Rundata anger inget material"); en bergart som är lika
  vanlig i landskapet som hos ristaren räknas som neutral.
- Språkdragen räknar bara oberoende drag, listar alla avvikelser och visar både ristarens och landskapets andel.

### 2D-analys
- Automatiska runutsnitt ("Hitta runorna"): runorna som 3D-analysen känt igen klipps ut ur ristningskartan, och i
  andra bilder markerar AI varje runa med ruta och läsning för granskning; de valda sparas som runutsnitt med
  formbeskrivning (METHODS.md 11).

### Granskning av U 92: stil, språkdrag och signifikans
- Stilkontrollen jämför stenens stilgrupp med ristarens kärna (stilgrupper på minst 10 % av stenarna) och anger
  glappet i år enligt Gräslund; minst 25 år gör förslaget kronologiskt problematiskt och slutsatsen högst *svagt*.
- Språkdragen vägs mot övriga stenar i landskapet (sannolikhetskvot per drag) och prövas med ett empiriskt p-värde
  (andel av landskapets stenar som passar ristarens profil minst lika bra); när ristaren föreslagits av en metod
  som bygger på stavningen räknas de inte som oberoende stöd, och ett resultat som inte avgör visas med sin text.
- Ortografins belägg sänks när likheten inte håller efter justering för urvalet, och tolkningen säger då att
  stavningen ensam inte räcker; produktiva ristare får en notering om att de drar till sig förslag.
- Skiljetecken kodas som blandat när inget tecken står för tre fjärdedelar; brøðr räknas inte till o-ljudsorden.

### Jämför stenar
- Huggspåren jämförs runa mot runa (permutation av hela runor) i stället för snitt mot snitt; det samlade testet
  använder de stabila måtten. Referensskala ur mätkorpusen (par med samma och olika ristare), kontroll av
  jämförbarheten och, med signum, ristare, stil, avstånd, stavning och språkdrag (METHODS.md 3).
- 2D-bildsökets miniatyrer fungerar med arkivens TIFF-bilder.

### AI-analyser
- 2D-analysen, den fonetiska analysen och rapporternas AI-avsnitt fungerar med Claude Opus 5.5: strukturerade
  svar via `output_config` i stället för tvingat verktygsval (som modellen avvisar). För stora bilder skalas
  ned före anropet, och ett avklippt eller avböjt svar ger ett tydligt felmeddelande.

### Stenöversikt
- Ny sida Stenöversikt: varje runsten som en punkt efter hur väl sex metoder stöder Rundatas ristare och hur
  starkt det bästa alternativet är (kan vara felbedömd, omstridd, stöds, svagt underlag; nytt eller möjligt
  förslag för stenar utan ristare), med kontroll mot signerade stenar och en profil per sten (METHODS.md 13c).
- Reservationerna på korpussidorna flyttade till dokumentationen.
- Tolkning av varje fynd i Forskningsluckor: belägg, p-värde, språkdrag, bergart, nyare källor och de andra
  metodernas besked vägs samman i ett resonemang med en slutsats (METHODS.md 13d).
- Runologiskt arkiv ombyggt: runornas namn enligt runedikterna, ristare, syften och kända stenar ur data.
- Snabbare: R-kontrollen och Stenöversikten sparas på disk, och servern värmer de långsamma svaren vid start.
- Attribueringsförslag från stenprofilen: ett dokument med alla argument för en ristare att skicka till
  runtextdatabasen, avstämt mot Runor 2020 och Wikidata (METHODS.md 14f).

### Stenens storlek
- Mått (höjd, bredd, tjocklek, runhöjd) för 1 384 vikingatida runstenar ur Kulturmiljöregistret via Runor och
  K-samsök (CC0; `data/stone_dimensions.json`, `scripts/build_stone_dimensions.py`), visade i Inskrifter och
  stenrapporten med stenens plats bland landskapets stenar.
- Storlek mot syfte, statusord, antal personer, textens längd och ristare, prövat inom landskap
  (Forskningsluckor → Storlek och syfte; METHODS.md 9b).

### Protokoll och dokumentation
- Vitki-protokollet för automatisk huggspårsmätning (`PROTOCOL.md`, `src/protocol.py`), utkast: fasta parametrar,
  krav på skanningen, arbetsgång, minsta redovisning; varje automatisk analys kontrolleras mot protokollet.
- Webbsidan Metodik och beräkningar (Dokumentation → Metodik) visar METHODS.md, protokollet och alla moduler,
  skript och R-moduler direkt från koden (`/api/docs`).
- Landningssidan uppdaterad: arbetsgången i Fullständig stenanalys, Statistik i R, Stenöversikt och tolkningarna i
  Forskningsluckor, principerna om validering, signifikans och regional baslinje, Claude som standard för AI-stegen
  (egen nyckel), fler källor och upphovsangivelsen i licensen.
- Appen heter Vitki, utan "AI": AI är ett valfritt hjälpmedel för bilder och löptext, inte kärnan (mätning,
  statistik och validering görs utan AI). Firebase-projektets tekniska id (`vitki-ai`) är oförändrat.
- Appens adress är https://vitkirunor.se: rapporterna, korpusexporten och CITATION.cff hänvisar dit och till
  källkoden på GitHub (`src/about.py`).

### Transparens
- Förteckning över metodens kända brister som visas under varje analyssida, står i varje rapport och sparas i
  proveniensen för varje mätning (METHODS.md 18).

## [2.0.0] – 2026-10-04
- Första versionen under namnet Vitki: 3D-huggspårsanalys, Rundata, ortografisk stilometri, syntes och
  attribuering, mätkorpus, statistik i R, forskningsluckor och rapporter. Mätmetoden har sedan ändrats
  (`groove-2` till `groove-4`, se METHODS.md 1).
