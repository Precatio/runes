# Publicerings- och forskningsplan 2026–2029

Omskriven 11 november 2026. Viktor: ”vi kör på detta upplägg, då sprider vi de tyngre akademiska rapporterna under längre
tid … Fokus blir istället en bra blandning” och ”varva rapporter för akademiker med populärvetenskapligt innehåll. Det
finns ett värde att nå folk med innehåll som bildar dem också, även om det inte är nytt för akademikerna.”

Planen bygger på litteraturgenomgången (`utdata/litteraturgenomgang/SYNTES.md`) och på **frågelistan**
`utdata/litteraturgenomgang/Forskningsfrågor_Fornvännen_Futhark.xlsx`, som är ett internt styrdokument. Rapport 0
publiceras inte (Viktor 11 nov); utkastet kgZ9FeICLh8TrrntAfD1 ligger kvar opublicerat. Frågelistan har 301 frågor, bedömda
efter hur relevant Vitkis bidrag skulle vara för forskningen: 22 avgörande, 65 betydande, 193 användbara och 21 begränsade.
Kolumnen ”Studie i planen” kopplar varje fråga till en studie här (`artikelkandidater/bygg_fragelista.py`, `STUDIER`);
den som flyttar en studie ändrar på båda ställena.

## Två spår

**Spår P – populärvetenskapen, hög takt.** Två artiklar i veckan, tisdag och fredag, ungefär 8–9 i månaden. Uppehåll över
jul och nyår, och en artikel i veckan i juli. Artiklarna bildar läsaren även när ämnet inte är nytt för forskarna.
- **Underlag:**
  - de användbara och begränsade frågorna i frågelistan, som ofta går att besvara beskrivande med det vi har;
  - serierna (De gamla landen, Hundra år av runfrågor, en runa i taget);
  - utkasten i avsnitt 4;
  - en eller två artiklar ur varje forskningsstudie.
- **Lättare arbetsgång:**
  - en beskrivande artikel (räknar och förklarar) behöver ingen låst plan;
  - en artikel som prövar en hypotes mot slumpen får en kort låst plan först;
  - varje siffra kommer ur våra data, och varje källa och varje citat kontrolleras mot originaltexten;
  - artikeln skrivs på svenska och engelska och får korthetsruta och Bluesky-inlägg.
- **Blandning varje vecka:**
  - tisdag: människor och tro;
  - fredag: platser, språk, föremål eller forskningshistoria;
  - i båda fallen ibland en del ur en serie.

**Spår F – forskningen, lägre takt.** En låst studie ungefär varannan månad, alltså fem till sex om året, fördelade på
2027–2029.
- **Arbetsgång:**
  1. låst plan, som läggs på Zenodo med datum när studien startar;
  2. kontroll av de påståenden studien bygger på mot originaltexten;
  3. körning;
  4. rapport, i rapportserien och på Zenodo med DOI, med PDF på webbplatsen och data som eget dataset;
  5. en eller två populärartiklar ur resultatet till spår P.
- **Om studien inte håller:** rapporten skrivs ändå och nollresultatet redovisas. Spår P fylls ur reservlistan.

**Korpus**, fyra nummer om året (mars, juni, september, december), väljer det bästa ur båda spåren. Varje nummer har tre
artiklar, Verkstaden, Metodhörnan, ”Ett påstående från förr, prövat” och **I appen**.

**Veckorutin (Viktor 11 nov: ”när varje vecka ska jag godkänna?”):**
- **Varje måndag, ungefär 20 minuter:** veckans två artiklar ligger färdiga senast söndag kväll, genomlästa och
  kontrollerade, med engelska Bluesky-inlägg. Viktor läser dem och klickar *Godkänn veckans publiceringar*, antingen
  från mobilen på vitkirunor.se/redaktion (fliken Veckan) eller överst under Artiklar i den lokala Admin. Det
  schemalägger dem (tisdag och fredag kl. 07.00) och lägger inläggen i Bluesky-kön samma dag kl. 18. Från webben går
  inlägget via en förfrågan som GitHub Actions lägger i kön inom ungefär en halvtimme. Planen står i
  `data/publiceringsschema.json`, och nya veckor fylls i där. Efter varje ändring körs
  `.venv/bin/python scripts/publiceringsschema_sync.py --skriv`, så att /redaktion ser samma plan. GitHub Actions
  publicerar artiklarna och postar Bluesky-kön, så datorn behöver inte vara igång.
- **Närmast:** mån 16 nov – Freja (tis 17) och De gamla landen: Skåne (fre 20); mån 23 nov – lerkanten (tis 24) och
  Fyra stenar för två barn (fre 27); mån 7 dec – första stora genomgången (på dagordningen: **byt nyckeln för tjänstekontot vitki-publicera**, som hamnade i chatten 11 nov – Google Cloud → Keys → ny JSON-nyckel → uppdatera GitHub-hemligheten FIREBASE_SERVICE_ACCOUNT → radera filerna).

**Genomgång med Viktor första måndagen i varje månad, ungefär 45 minuter.**
- Viktor godkänner allt som är klart på en gång: artiklar att publicera, rapporter, Zenodo och licensfrågor.
- Utkasten ska ligga minst fyra veckor före publiceringen.
- Blir takten för hög sänks spår P till tre artiklar på två veckor.

**Synlighet, en sak per kvartal** (avsnitt 3).

**Regler som gäller allt:**
- data före tolkning;
- runstenar i Sverige som standard, och andra föremål alltid redovisade för sig;
- planen låses (sha256 + commit) innan något prövas;
- varje statistiskt tal förklaras i klartext;
- Viktor publicerar, och publicerade artiklar ändras bara efter hans besked, via Firestore;
- varje synlig nyhet får en notis;
- **språkmodellerna nämns som Anthropics Claude**, kort, i metodstycket, aldrig som ”AI”;
- **det vi behåller** (Viktor 10 nov): hur varje fråga prövas, påståendedatabasen och relevansmotiveringarna stannar hos oss
  tills studien eller huvudrapporten är publicerad;
- **varje forskningsrapport** får Google Scholar-taggar, PDF på webbplatsen (`scripts/rapport_pdf_webb.py`) och data som
  dataset på Zenodo (`scripts/zenodo_dataset/`).

## 1. Forskningsspåret

Status per rad: planerad → plan låst → körd → rapport → publicerad.

| Period | Studie | Frågor | Data | Rapport | Status |
|---|---|---|---|---|---|
| nov 2026 | **Lerkanten**: kontrollerna K1–K6 | – | har | ingår i självkontrollrapporten | körd 10 nov, K1–K5 håller |
| dec 2026 | **B. Självkontroller**: österled utan Ingvar, gravfälten, lerkanten, vägen | 3 avgörande | har | **15 dec:** ”Fyra runstensfynd prövade mot hundra års invändningar” (utkast wgzazW4ZpKk7OVtuT32w; lerkanten och Ingvar publiceras först; sätt TODAY till publiceringsdagen) | Ingvar försvagat (58 %, 49–67), tillägget i den publicerade artikeln är gjort. Gravfälten står sig (OR 2,3–2,6). Vägen: punkttestet föll, linjetestet K/L0/L1 håller (gamla vägars linjer 32 %, p 0,023). **L2 väntar på Viktors kartritning;** vägrapportens version 5 görs först efter L2. |
| jan–feb 2027 | **A1. Flyttade och försvunna stenar** | 4 avgörande | har (D4 klar) | mars | plan låst 11 nov (4eef7f6) |
| mar–apr 2027 | **A2. Registret och nämnaren** | 4 avgörande | D4 klar; SDHK 1314; ISOF | maj | plan låst 11 nov (4eef7f6); före körningen ett låst tillägg om fältdatum efter 2003 och om första/andra inventeringsomgången |
| maj–jun 2027 | **D. Platserna mot slumpen**: gravar, vägar eller gränser (Klos 2009 – Larsson 2010); bron och vadet; gudarnas platser; tinget; Husby, Tuna och Hov; äldre monument; vägen med Häradsekonomiska kartan (L2) | 4 avgörande + 5 betydande | KMR; ISOF-namn (D3); D13 | juli | planerad |
| aug–sep 2027 | **C. Dateringen**: dateringens ankare; Ingvars år; stil mot språk; prickarna och åsrunan som klocka; tid, trakt eller hand | 4 avgörande | har | oktober | planerad |
| okt–nov 2027 | **F. Människorna**: arv och lagarna; hur stor del av de döda som fick en sten; var det de rika (Malmer); kvinnorna som reste stenar; trälarna | 3 avgörande + 8 betydande | har | december | planerad |
| dec 2027 | **Huvudrapporten v1**: genomgången och 2027 års studier, med påståendedatabasen som dataset | – | – | december | planerad |
| jan–feb 2028 | **E. Korset och bönen**: bekännelse eller prydnad; kristnandets karta; österifrån eller västerifrån; uppifrån eller underifrån | 1 avgörande + 6 betydande | har | mars | planerad |
| mar–apr 2028 | **R. Ristarna**: kännarskap mot slumpen; fingeravtryck; Åsmund och Öpir; hur långt ristarna reste | 1 avgörande + 6 betydande | har | maj | planerad |
| maj–jun 2028 | **V. Vattnet och landhöjningen**: vilket vatten, landhöjningen som klocka, gårdsnamnens ålder | 1 avgörande + 3 betydande | **höjdmodell (D2)** | juli | planerad |
| aug–sep 2028 | **S. Stenen och silvret**: vad en sten kostade, varifrån stenen kom, silvret, odlingen | betydande | **berggrund (D1), skattfynd (D5)**, lagarnas priser (D11), pollen (D7) | oktober | planerad |
| okt–nov 2028 | **K. Kyrkorna**: inmurade stenar dateras av kyrkan; gravhällarna; träkyrkorna | betydande | **kyrkornas byggår (D6)** | december | planerad |
| dec 2028 | **Huvudrapporten v2** | – | – | december | planerad |
| jan–feb 2029 | **G. Gränserna**: götar och svear, Kolmården, folkland och hundare, samma karta eller olika | betydande | har | mars | planerad |
| mar–apr 2029 | **Språkets klockor**: ʀ och r, monoftongeringen, epentesen, stavningen, skiljetecknen | betydande | har | maj | planerad |
| maj–jun 2029 | **Namn och släkt**: kvinnorna som flyttade, samma man på två stenar, namn i bygden | betydande | har | juli | planerad |
| aug–sep 2029 | **När stenarna tystnade**: gravhällarna, städernas runor, medeltiden (andra föremål redovisas för sig) | betydande | Runor 2020 | oktober | planerad |
| okt–nov 2029 | **Vers och skrivkonst**: stavrim mot slumpen, läsuppmaningar, texttyper | betydande | har | december | planerad |
| dec 2029 | **Huvudrapporten v3** | – | – | december | planerad |

**Färdiga rapportutkast att lägga in i luckorna** (Viktor granskar först):

| Utkast | Förslag |
|---|---|
| ”Skrivmiljöer utan namn” (vjDfELe4xiHBZmDIMrfw) | jan 2027 |
| ”Samma släkt på flera runstenar” (4zloUTTKPEaevSXCjGWz) | feb 2027 |
| ”En upptäcktsmotor som inte lurar sig själv” (HnnsXBY4zhbwPZqNEuj0) | apr 2027 |

## 2. Populärspåret

**Första kalendern, november 2026 – februari 2027.** ”Utkast” betyder klar text i appen. ”Ny” skrivs fyra veckor före och
är beskrivande, ur frågelistans reservdel; den som prövar mot slumpen får en kort låst plan.

| Datum | Artikel | Läge |
|---|---|---|
| tis 17 nov | Ingen på runstenarna hette Freja – i dag heter 7 000 svenskar det | utkast, litteraturkontrollerat |
| fre 20 nov | De gamla landen: Skåne – slätten där kungen byggde nytt | utkast |
| tis 24 nov | Varför står runstenarna vid lerans kant? | utkast, kontrollerna håller |
| fre 27 nov | Fyra stenar för två barn – släkterna som går att följa över runstenarna | utkast |
| tis 1 dec | De gamla landen: Gotland – ett eget land mitt i havet | utkast |
| fre 4 dec | Döda i vita kläder: stenarna över dem som dog döpta | ny |
| tis 8 dec | Vikingarnas österled – eller bara Ingvars? | utkast |
| fre 11 dec | De gamla landen: Värend – sjöbygden mitt i skogen | utkast |
| tis 15 dec | Kunde folk läsa runstenarna? (samma dag som självkontrollrapporten) | ny |
| fre 18 dec | De gamla landen: Möre – kusten vid sundet | utkast |
| tis 22 dec | Mö, dotter eller flicka? Ordet som kunde betyda ogift | ny |
| 25 dec – 1 jan | juluppehåll | – |
| tis 5 jan | De gamla landen: Finnveden – landet längs Lagan | utkast |
| fre 8 jan | Var ”norr” nordost? Väderstrecken på runstenarna | ny |
| tis 12 jan | Änkorna som reste stenarna – och männen som aldrig kom hem | ny |
| fre 15 jan | De gamla landen: Fjädrundaland – folklandet längst in i havsviken | utkast |
| tis 19 jan | Hundra år av runfrågor I: Grundläggarna | utkast |
| fre 22 jan | Väringarna: hur många stenar nämner Grekland – och när tystnade de? | ny |
| tis 26 jan | Dräpt, fallen eller död hemma? Så dog männen på runstenarna | ny |
| fre 29 jan | De gamla landen: Attundaland – där man gjorde sina tingsplatser | utkast |
| tis 2 feb | Hundra år av runfrågor II: När forskarna började räkna (lägg sedan länk framåt i del I) | utkast |
| fre 5 feb | Kumbl, stæin, kross – vad kallade man stenen? | ny |
| tis 9 feb | Tegnar i söder, böner i norr | utkast, kontrollera Gräslund 2001 först |
| fre 12 feb | Eddan på stenarna – vilka gudar nämns egentligen? | ny |
| tis 16 feb | Bron som själaverk: brobygge och bön | ny |
| fre 19 feb | Hette sonen som fadern? Släktens namnregler | ny |
| tis 23 feb | Hushållet som stenarna glömde: tjänstefolk, ofria och barn | ny |
| fre 26 feb | Vem står först i texten? Namnordningen som släktkarta | ny |

**Från mars 2027:** studie A1 ger artiklarna ”Hur långt flyttades runstenarna?” och ”Stenarna som plogen och grustaget
tog”. Därefter fortsätter reservlistan i samma blandning, till exempel:
- *människor och tro:* Kvinnorna som ägde jord; Fick kvinnor sten bara om de var förnäma?; Bröder, väringar och gillen;
  Utan kors – hedning?; Böner i sten; Mot plundrare eller mot de döda?;
- *platser och föremål:* Hassmyra, Balsten och Lönnånger; Högar, gravfält och tingsplatser; Varför Östergötland? 363
  gravhällar; Urnesstilen – svenskt eller engelskt?; Bautastenarna före runstenarna;
- *språk:* Reste, satte eller högg?; Skrift som bild; Den tysta nasalen; Vilken sorts text är en runsten?;
- *forskningshistoria:* Rökstenen och alla andra – vilka stenar skriver forskarna om?

Kalendern för nästa period skrivs vid månadsgenomgången i februari.

## 3. Korpus och synlighet

| Nummer | Tema | Innehåll | I appen |
|---|---|---|---|
| Nr 2, mars 2027 | *Det vi inte ser* | Hur långt flyttades runstenarna?; Hundra år av runfrågor (sammandrag); Vikingarnas österled – eller bara Ingvars? Metodhörnan: vad är fångst–återfångst? | Luckor i texten |
| Nr 3, juni 2027 | *Platserna* | Gravar, vägar eller gränser?; Varför står runstenarna vid lerans kant?; De gamla landen. Metodhörnan: slumpen inom bygden | Kartan med de gamla landen, strandlinjen och jordarterna |
| Nr 4, september 2027 | *Hur gamla är runstenarna?* | Dateringens ankare; Prickarna, åsrunan och tiden; Döda i vita kläder. Metodhörnan: varför vi låser planen | Ristarna, en i taget |
| Nr 5, december 2027 | *Människorna* | Var det de rika?; Hur många stenar reste kvinnor?; Änkorna. Verkstaden: huvudrapporten | Pröva en egen fråga |

Fler funktioner att förklara: 3D-huggspårsanalysen, Namn och släkt, Runbiblioteket, Stenanalys och Jämför stenar.
Numren byggs med `utdata/tidskrift/bygg_tidskrift.py` (sv + en) och läggs upp på /tidskrift.

**Synlighet, en sak per kvartal:**

| Kvartal | Insats |
|---|---|
| Q1 2027 | be om ett seminarium på Runforum, Uppsala (självkontrollerna och A1) |
| Q2–Q3 2027 | debattartikel i Fornvännen efter studie D (gravar, vägar eller gränser) |
| Q3 2027 | bidrag till DHNB 2028 |
| Q4 2027 | korta mejl till forskare vars påståenden vi prövat (en forskare, ett påstående, tre rader) |
| 2028–2029 | samma rytm: en debattartikel om året, konferensbidrag (DHNB, runsymposiet) |

## 4. Dataplan

| # | Data | Källa och tillgång | Behövs till | Hämtas | Arbete |
|---|---|---|---|---|---|
| D1 | Berggrundskarta | SGU, öppna data (vektor) | S (2028) | våren 2028 | litet |
| D2 | Höjdmodell och vattendrag | Lantmäteriets markhöjdmodell; SMHI:s vattendragsregister | V (2028) | vintern 2028 | medel |
| D3 | Centralorts- och tingsnamn | ISOF (CC BY), platser.csv | D (2027) | mars 2027 | litet |
| D4 | Fornminnesregistrets inventeringsår | **Klar 11 nov 2026.** Fornsöks fältdatum: huvudår för alla 636 runstenssocknar. utdata/d4_inventering/D4_RESULTAT.md | A1, A2 | klar | – |
| D5 | Skattfynd med fyndplats | SHM och Myntkabinettet via K-samsök; CNS och Hårdh som kontroll | S (2028) | hösten 2027 – våren 2028 | stort (TLS-fel = Viktors VPN) |
| D6 | Kyrkornas byggår och dendro | RAÄ:s bebyggelseregister, *Sveriges kyrkor*, Lunds dendrolaboratorium, Wase 1995 | K (2028) | våren–sommaren 2028 | stort |
| D7 | Pollenserier | Neotoma (har) | S | har | litet |
| D8 | 1600-talets bykartor | Lantmäteriets historiska kartor (inventerade: 133 stenar har geometriska kartor) | vägar, gårdar | 2029 (valfritt) | mycket stort |
| D9 | Isotoper och aDNA | publicerade tabeller | namn och släkt (2029) | 2028 | medel |
| D10 | Runor 2020:s fält | har | A, C, E | klar | – |
| D11 | Landskapslagarnas priser | utgåvor av lagarna | S | 2028 | litet |
| D12 | 1314 års sexårsgärd | kontrollerad 10 nov 2026 | A2 | klar | – |
| D13 | Häradsekonomiska kartan | Historiska kartor, utan inloggning; 116 blad runt 201 stenar; ej georefererade | vägen (L2), D | när Viktor ritar | medel |

## 5. Utkast som väntar (läge 11 nov 2026, kontrollerat i Firestore)

- **Populärspåret:**
  - Freja; lerkanten; Ingvar; Fyra stenar för två barn; De gamla landen (Skåne, Gotland, Värend, Möre, Finnveden,
    Fjädrundaland, Attundaland); Hundra år av runfrågor I–II; Tegnar i söder (Gräslund-referensen först);
  - Prickarna, åsrunan och tiden – kopplas till studie C (aug–sep 2027), med utgivarkontroll.
- **Vänta:** Vem höll i mejseln? och Möjliga ristare utan namn – efter attributionsspåret (studie R); Så gör du: mät runorna,
  inte ormen – serien är pausad.
- **Forskningsspåret:** självkontrollrapporten (15 dec) och de tre rapportutkasten i avsnitt 1.
- **Publicerade artiklar med väntande ändringar:** Norge (8 nov) har litteraturtillägg klara i `build_norge.py` och väntar
  på Viktors besked.

## 6. Risker

- **Viktors tid** är flaskhalsen: läsning, publicering, kartritning. Den hanteras med månadsgenomgången och fyra veckors
  buffert.
- **Obestämda resultat** i spår F blir rapporter, inte artiklar; spår P fylls ur reservlistan.
- **Data dröjer** (skattfynd, kyrkor): studierna S och K kan byta plats med G och Språkets klockor.
- **Källfel:** varje påstående kontrolleras mot originaltexten; läsarkontrollen visade att ungefär fyra av fem var rätt
  återgivna.
- **Ett tungt jobb i taget** (16 GB-Macen).
