# Analysplan: vad de öppna 3D-skanningarna kan säga – fyra studier

Låst 2026-10-24, innan något av testerna nedan har körts. Planens SHA-256 står i
`analysplaner/2026-10-24-skanningarna.sha256`. Planen ändras inte efter låsningen; avvikelser redovisas i
`utdata/forskningsplan/resultat.md` under rubriken *Avvikelser från planen*.

Före låsningen har bara följande gjorts:
- De sex öppna skanningsserierna (`src/scan_sources.py`) har laddats ned och kontrollerats mot Zenodos md5, och varje fil
  har mätts med Vitki-protokollet (`scripts/batch_scans.py`, groove-5, bara runor, känslighet 3).
- Rundatas uppgifter (objekt, material, datering, ristare, runtyp, antal luckmarkeringar) har listats för stenarna.
- En beskrivande kontroll (steg 0b nedan) har körts: runfiltret känner igen median 20 % av textens runor på de tio
  stenarna med stavlösa runor mot 81 % på övriga (`utdata/forskningsplan/s0_stavlosa_filter.txt`). Inga jämförelser
  mellan grupper har gjorts.

## Material
- **P-data:** protokollmätningen, `utdata/automatisk_korning/<serie>/<fil>.json` (bara snitt på streck som känns igen
  som runor).
- **A-data:** samma skanningar mätta en gång till med alla spår (`runes_only = false`, rutnät 0,6 mm, känslighet 3,
  samma normal), `utdata/automatisk_korning_alla/`. Varje godkänt snitt har sin streckklass (`feature`: rune, ornament,
  isolated, irregular).
- **Objekt:** runsten = Rundatas objekt innehåller "runsten" (även fragment). Gravmonument = objektet innehåller
  "gravhäll", eller filen tillhör serien gravmonument_og_sm, eller filen är en västgötafil utan signum vars namn har
  Ljungs eller Lundbergs nummer, GVMV eller ATA (Ljung 2016:s gravmonument). Övriga och stenar som saknas i Rundata
  (Sö 137A/B) räknas inte i studie 1–3.
- **Bergartsfamilj** ur Rundatas material: kristallin (granit, gnejs, gråsten, diabas, gnejsgranit, granatådergnejs,
  sedimentgnejs), sandsten (även gävlesandsten), kalksten (även lersten), okänd (inget material angivet).
- **Skanner:** ATOS (Södermanland, Åsmund, Västergötland, Ög/Sm) eller HandySCAN (Hälsingland, Medelpad).
- **Huvudmått:** V-vinkel (`apex_vinkel_deg`), spårdjup, spårbredd och bottenradie. Mått per objekt är medianen över
  dess godkända snitt.

## Steg 0 – grunden
- **0a Upplösning.** Hs 14 och M 14 finns i två filer var. Skillnaden i objektmedian mellan filerna anges för de fyra
  huvudmåtten, jämförd med standardavvikelsen mellan stenarna i samma serie. Ett mått där skillnaden är större än halva
  den standardavvikelsen märks *upplösningskänsligt*; i studie 3 tas då upplösningen (`mesh_point_spacing_mm`) med som
  förklarande variabel.
- **0b Stavlösa runor** (redan körd, se ovan). Följd: stavlösa inskrifter mäts i A-data, inte i P-data, och de tio
  stenarna med stavlösa runor tas inte med i studie 3.
- **0c Spårläsaren utanför Södermanland** (förutsättning för studie 4): se studie 4.

## Studie 1 – samma händer eller nytt hantverk?
**Fråga:** följer gravmonumenten omkring 1100 runstenarnas hantverk, eller är de huggna på ett annat sätt?
**Upplägg:** jämförelse inom varje objekt, så att bergarten tar ut sig. För varje objekt med minst 10 godkända snitt
i både runor (`rune`) och ornamentik (`ornament`) i A-data räknas Δ = median(runor) − median(ornamentik).
- **Huvudtest:** skillnaden i median-Δ för V-vinkeln mellan gravmonument och runstenar, permutationstest med 10 000
  omflyttningar av objekttypen, tvåsidigt. Kräver minst 8 objekt i varje grupp; annars redovisas resultatet bara
  beskrivande.
- **Sidotest:** samma för spårdjup, spårbredd och bottenradie, Benjamini–Hochberg-justerade (q < 0,05).
- **Tolkningsregel:** p < 0,05 → "mönstret skiljer sig". Ligger 90 %-bootstrapintervallet (2 000 dragningar) för
  skillnaden inom ±5° → "samma mönster". Annars "obestämt".
- **Robusthet:** (i) bara runstenar i sandsten och kalksten som jämförelse; (ii) en serie i taget utelämnad;
  (iii) bara objekt skannade med ATOS.
- **Giltighetskontroll före testet:** streckklassningen granskas visuellt på tre gravmonuments och tre runstenars
  granskningsbilder. Om ornamentiken på gravmonumenten mestadels klassas som något annat än ornamentik görs inget test,
  och det redovisas.

## Studie 2 – stavlösa runor på sten
**Fråga:** höggs stavlösa runor annorlunda (grundare, smalare) än vanliga runor?
- **2a (idag, mellan stenar):** Hälsinglands stavlösa stenar (Hs 10, Hs 12, Hs 14, Hs 15) mot Hälsinglands övriga
  (Hs 1, 2, 3, 4, 6, 9, 11, 16, 21). Samma skanner och region. Inskriftens streck = snitt i klasserna `rune` och
  `isolated` i A-data. **Huvudmått:** spårdjup; sidomått: spårbredd, V-vinkel, bottenradie. Permutationstest på
  stenmedianer, tvåsidigt; redovisas som pilot med effektstorlek, eftersom grupperna är små. Robusthet: bara kristallin
  bergart.
- **2b (senare, inom sten):** M 3, M 4, M 7, M 8 och Sö 164 har både stavlösa och vanliga runor. Runorna märks för
  hand på ristningskartan; testet (parvis inom sten, stavlösa mot vanliga runor) körs först när märkningen är granskad,
  och märkningen görs utan att måtten visas.

## Studie 3 – hur mycket av ristaren syns i spåret?
**Underlag:** P-data. Runstenar med exakt en säker ristare (`certain_carvers`, signerad eller attribuerad, inte
osäker), ristare med minst två sådana stenar; stenar med stavlösa runor utesluts.
**Modell:** för vart och ett av de fyra huvudmåtten, `lmer(mått ~ skanner + (1|bergartsfamilj) + (1|ristare) +
(1|sten))` med snitten som enheter. Varianssandelar med 95 % parametriskt bootstrapintervall (500 simuleringar).
**Huvudfråga:** ristarens andel mot bergartens andel för V-vinkeln. Skannern sammanfaller nästan helt med region och
redovisas som en begränsning.
**Fallstudier (beskrivande, inget test):** Åsmund (Gs 11, Gs 13 i sandsten, U 1144 i granit; Gs 13 och U 1144 har
också en medristare): ligger U 1144 närmare Åsmunds sandstensstenar eller andra granitstenar (standardiserat
avstånd på de fyra huvudmåtten)? Medelpad: vilka osignerade stenar ligger närmast Fartägns M 1 – märkt som förslag,
eftersom attribueringen bara är kalibrerad i Mälardalen.

## Studie 4 – vad skannern ser i de skadade partierna
**Förutsättning (0c):** spårläsaren är kalibrerad i Södermanland. Den prövas först på Hälsinglands, Medelpads och
Åsmunds stenar med ett blindprov av samma slag som 2026-10-17: läsbara runor döljs (3 per sten, slumpfrö 1) och
modellen fyller dem med och utan skannerns spår. Spåren används för de nya stenarna bara om träffandelen med spår
inte är lägre än utan; annars redovisas modellens läsning utan spår.
**Resultat:** för varje sten med förlorade runor: modellens förslag per lucka med kalibrerad sannolikhet, det
skannern ser vid luckan och om de stämmer. Bara förslag med kalibrerad sannolikhet ≥ 80 % lyfts fram. Allt märks som
förslag att pröva på stenen; ingenting skickas till utgivare eller myndigheter utan grundarens beslut.

## Vad som redovisas oavsett utfall
Alla tester ovan, även de som inte ger något, med antal objekt, effektstorlek, p eller q och intervall. Antalet
objekt som föll bort i varje steg och varför.
