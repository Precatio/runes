# Samlad datering: resultat

Utfallen i de tre låsta planerna står som de kördes. Avsnitten märkta **granskning 2026-10-27** lades till efteråt. De
rättar förklaringar och visar var vinsten ligger, men ändrar inget av de tre utfallen (alla tre är fortfarande inte
godkända).

## Version 1 (plan bb06d292…, låst 2026-10-27): inte godkänd

Kvantilregressionsskog på språkdrag, innehåll, kors, runtyp, seriation och plats, prövad med femfaldig korsvalidering
grupperad per socken (3 upprepningar), 1 008 daterade runstenar (`validering.json`).

| Mått | M1 | Gräns | Utfall |
|---|---|---|---|
| Medelabsolutfel | 15,1 år (landskapets median 20,2) | ≤ 0,85 × 20,2 = 17,2 | klarat |
| Täckning, 80 %-intervall | 0,957 | 0,75–0,88 | **inte klarat** (gränserna sammanfaller med facit) |
| Uppland mot seriationen (de 501 upplandsstenar som har seriationsdatering) | 16,4 mot 20,6 år | ≤ 20,6 + 2 = 22,6 | klarat |

M2 (med språkdateringen) gav 14,5 år och täckningen 0,961. Räknat över alla 1 008 stenar är punktskattningen alltså
bättre än landskapets median och, i Uppland, bättre än seriationen. Hur ojämnt vinsten är fördelad framgår under
"Var vinsten ligger" nedan. Enligt planen förs ingenting in i appen. En ny plan (version 2) kalibrerar intervallen och
låstes före den körningen.

**Varför täckningen blev för hög (granskning 2026-10-27, rättar den första förklaringen).** Först stod här att
intervallen var för vida eftersom skogens kvantiler tar med variationen inom stilgruppernas egna spann. Det var fel:
facit är stilgruppens mittår, så ingen variation inom spannet når modellen. Orsaken är att facit bara har sex värden
(997,5, 1030, 1035, 1065, 1085, 1115). Av intervallens nedre gränser ligger 98,9 % exakt på något av de sex värdena,
och av de övre 98,8 %. 57,4 % av stenarna har sitt rätta mittår exakt på en gräns, och bara 4,3 % hamnar utanför
intervallet. Räknas gränserna som utanför sjunker täckningen från 0,957 till 0,383. På så grov skala säger
80 %-kravet alltså inte om intervallen är för breda eller för smala; det kan varken klaras eller fällas på ett
meningsfullt sätt. Det är samma diagnos som i v2.

## Version 2 (plan 84256b0f…): inte godkänd

Den konforma korrektionen blev exakt 0 i alla vecken, och täckningen 0,957 som i v1 (`validering_v2.json` som den
kördes, i commit 284bd60; filen i arbetskatalogen innehåller nu den rättade körningen, se nedan).
Diagnos: facit, stilgruppens mittår, har bara sex värden. Kvantilerna hamnar på dessa värden, avvikelsen
max(q10 − y, y − q90) är 0 för de flesta stenar, och ett intervall som omfattar sina gränsgrupper täcker mer än
nominellt. Ett 80 %-intervall går inte att kalibrera på en så grov skala. Medelfelet klarade gränsen (15,2 år mot
20,3 för landskapets median), med samma ojämna fördelning som i v1.

**Rättelse i skriptet i efterhand (granskning 2026-10-27).** Planen och konform kvantilregression kräver att q10 och
q90 för teststenarna tas ur samma skog som korrektionen Q kalibrerades på, alltså skogen tränad på träningshalvan;
bara medianen ska komma ur skogen tränad på hela träningsdelen. Skriptet tog i stället q10 och q90 ur
helträningsskogen och lade på Q från halvskogen. `datering_v2.R` är rättat så att intervallen tas ur halvskogen
(veckindelning och punktskattningar är oförändrade). Efter rättelsen: Q är fortfarande exakt 0 i alla 15 veck, för
bara 35–48 % av kalibreringsstenarna ligger strikt inne i sitt intervall medan 93–98 % ligger inne eller på en gräns,
så avvikelsens 80-percentil kan inte bli negativ. Täckningen blir 0,956 i stället för 0,957 (M2 0,962, avrundat
oförändrat), medelfelet 15,2 mot 20,3 och Uppland 16,4 mot 20,6 år som förut. Det är den körningen som
`validering_v2.json` nu innehåller. Utfallet ändras inte: v2 är inte godkänd.

## Version 3 (plan 45df1d5c…): inte godkänd – enligt planen avslutas arbetet tills nya data finns

Sannolikhetsskog över de sex tidsskikten (`validering_v3.json`): kalibreringsfelet för den mest sannolika klassens
sannolikhet 0,046 (gräns 0,05, klarat), Uppland 18,6 mot seriationens 20,6 år (klarat), men medelfelet för det
förväntade året 18,1 år mot gränsen 17,2 (0,85 × 20,2): **inte klarat**. Den mest sannolika klassen är rätt i 54 %;
mängden av de mest sannolika klasserna upp till 0,8 täcker 90 %.

**Vad kalibreringskravet visar (granskning 2026-10-27).** Planen prövade bara den mest sannolika klassens
sannolikhet, och den klarade gränsen. Det betyder inte att hela fördelningen över tidsskikten är kalibrerad.
Sannolikheterna är något för försiktiga: i de fyra mellersta facken (angiven sannolikhet 0,4–0,8, 1 761 av 3 024
förutsägelser) är träffsäkerheten 6–10 procentenheter högre än den angivna sannolikheten (till exempel 0,51 rätt när
modellen säger 0,45, och 0,84 när den säger 0,75). Felet stannar under 0,05 för att facken 0,2–0,4 (1 074
förutsägelser) stämmer nästan exakt och drar ned genomsnittet. Mängden upp till 0,8 rymmer i genomsnitt 2,9 av de sex
tidsskikten.

**Varför medelfelet föll (granskning 2026-10-27).** Planen skrev in det förväntade året, Σ p × mittår, som
punktskattning. Väntevärdet är den skattning som minimerar kvadratfel, inte absolutfel. När sannolikheterna är utspridda
drar det mot mitten av skalan: det förväntade årets spridning (standardavvikelse) är 24,7 år mot 35,6 för facit. Samma
sannolikheter sammanfattade med fördelningens median (det tidsskikt där summan når 0,5) ger medelfelet 15,4 år (15,7,
15,2 och 15,4 i de tre upprepningarna), under gränsen 17,2; den mest sannolika klassen ger 16,6. Med medianen blir
Uppland 16,7 mot seriationens 20,6, och kalibreringen påverkas inte. v3 föll alltså på den punktskattning planen
valde, inte på att sannolikheterna saknar tidssignal. Att byta till medianen nu vore att ändra planen efter att ha
sett utfallet, och v3 förblir inte godkänd. Medianen går inte heller att pröva i en ny plan på samma 1 008 stenar:
utfallet (15,4 år) är redan känt, så en sådan plan vore inte skriven före resultatet och vore ingen förregistrering.
Även med medianen är medelfelet utanför Uppland 12,7 år mot 12,6 för landskapets median, alltså ingen vinst där.

## Var vinsten ligger (granskning 2026-10-27, efter de låsta körningarna)

Siffrorna nedan kommer ur v1:s korsvalidering (samma förutsägelser som `validering.json`). De ändrar inget utfall men
avgör hur "25 % bättre" ska läsas.

**Uppland bär nästan hela vinsten.** Uppland har 560 av de 1 008 daterade stenarna, och där är landskapets median ett
svagt jämförelsemått (26,3 år fel i genomsnitt, eftersom upplandsstenarna spänner över alla stilgrupper). Modellen
ger 17,4 år där, 34 % bättre. (Tabellens 16,4 år gäller bara de 501 upplandsstenar som har seriationsdatering,
eftersom jämförelsen med seriationen kräver en sådan; 17,4 gäller alla 560.) Av hela minskningen i fel kommer 95,8 %
från Uppland. På de övriga 448 stenarna är
modellen bara 4 % bättre än landskapets median (12,1 mot 12,6 år), och i fem landskap är den sämre: Sö 11,5 mot
11,3 år (168 stenar), Öl 36,5 mot 28,9 (22), G 20,0 mot 15,2 (9), Vr 16,3 mot 12,5 (2) och J 35 mot 30 (1). Bättre
är den i Ög 11,2 mot 12,2 (98), Vg 7,9 mot 8,7 (82), Vs 12,7 mot 30,4 (11), Gs 16,3 mot 17,5 (10), Nä 11,7 mot
27,9 (6), Hs 22,5 mot 23,8 (5) och M 13,9 mot 16,4 (3); i Sm lika (5,5, 31 stenar).

**Utanför Uppland bär språk och innehåll ingen egen signal.** Prövat genom att ta bort variabler (samma korsvalidering,
seed 2026): med bara språkdrag, innehåll och landskap blir felet utanför Uppland 16,2 år, och utan koordinaterna 15,5
år, båda sämre än landskapets median (12,6). Med bara landskap och koordinater blir det 13,4, också sämre. Först
tillsammans når modellen 12,1, alltså den lilla vinst som finns kommer ur platsen, det vill säga ur närliggande
daterade stenar, i samspel med texten. I Uppland är signalen verklig: bara språkdrag, innehåll och landskap ger 17,7
år mot 26,3. Seriationens poäng läcker inte facit (utan den blir felet 14,9 i stället för 15,1).

**Korta texter, som de flesta odaterade stenar har, dateras sämst.** Bland de daterade stenarna med högst tre ord
(146 stenar) är modellen bara 7 % bättre än landskapets median (20,9 mot 22,5 år); med 4–7 ord (333) 25 % (13,3 mot
17,7) och med åtta ord eller fler (529) 31 % (14,6 mot 21,1). De 1 313 odaterade stenarna, som arbetet gällde, ser
annorlunda ut än de daterade: medianen är 2 ord mot 8, 56,5 % har högst tre ord mot 14,5 %, och 73,6 % av
språkdragsfälten saknas mot 44,1 %. Vägs korsvalideringens fel om efter de odaterade stenarnas textlängd blir
modellen 15 % bättre än landskapets median (17,9 mot 21,1 år), precis på planens gräns, och då är varken de saknade
fälten eller landskapsfördelningen omvägda.

## Sammanfattning av de tre försöken

Ingen av de tre låsta versionerna klarade alla krav, och enligt planerna förs ingen samlad datering in i appen; de
odaterade stenarna räknas som förut inte i tidsfrågorna.

Det finns en verklig tidssignal, men den är smalare än "25 % bättre" låter. Räknat över alla daterade stenar daterar
kvantilskogens median 25 % bättre än landskapets median (15,1 mot 20,2 år) och, på de 501 upplandsstenar som har
seriationsdatering, bättre än seriationen (16,4 mot 20,6). Nästan hela vinsten ligger i Uppland: på alla 560
upplandsstenar 17,4 år mot landskapets median 26,3, 34 % bättre. Utanför Uppland är modellen bara
4 % bättre (12,1 mot 12,6), där i första hand genom platsen; språkdrag och innehåll ensamma slår inte landskapets
median där. För korta texter, som de flesta odaterade stenar har, krymper vinsten till 7 %.

Osäkerheten gick inte att mäta på ett meningsfullt sätt med årsintervall: facit har bara sex värden, intervallens
gränser hamnar på dem, och 80 %-kravet blir därför varken klarat eller fällt på riktigt (v1, v2). Sannolikheterna per
tidsskikt i v3 klarade kalibreringskravet för den mest sannolika klassen men är något för försiktiga, och v3 föll på
att planen valde det förväntade året som punktskattning. Sannolikheternas median hade klarat felgränsen (15,4 mot
17,2 år).

Enligt plan v3 avslutas arbetet med samlad datering tills nya data finns. Med nya data menas finare facit
(dendro- eller arkeologiska dateringar, eller Gräslunds stilgrupper uppdelade), som behövs för att intervall och
sannolikheter ska gå att pröva på en finare skala, eller nydaterade stenar som ingen av de tre körningarna har sett.
Någon ny plan på de 1 008 daterade stenarna är inte en väg framåt: sannolikheternas median (15,4 år) och omvägningen
efter textlängd (15 % bättre) är redan räknade på dem, så en plan som byggde på dem och prövades där vore inte låst
före resultatet. Det de har visat får bara användas som hypotes i en plan som prövas på nya data, och även då pekar
siffrorna ovan på att vinsten i första hand gäller Uppland; för de korta texterna och landskapen utanför Uppland är
den liten.
