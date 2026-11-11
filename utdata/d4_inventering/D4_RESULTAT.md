# D4 – Fornminnesinventeringens år per socken (KMR/FMIS)

Datauppgift D4 i `PUBLICERINGSPLAN.md` (avsnitt 3), underlag för A1 (jan 2027) och A2 (feb 2027).
Byggd 2026-11-11. **Inget är räknat mot runstenarnas placering**; runstenssocknarna används bara för att mäta
täckningen.

## Kort svar

- **Det finns ingen öppen tabell eller karta** över vilket år varje socken eller län inventerades, varken hos RAÄ,
  Riksarkivet eller på dataportal.se. RAÄ:s egna texter ger bara ramarna: förstagångsinventeringen 1938–1977
  och revideringsinventeringen 1974–2002/2003 (HAIK-förstudien 2020). Fornvännen 1978 ger ordningen per landskap i
  decennier.
- **GeoPackagen saknar inventeringsår.** `publiceringsdatum` är migreringen till KMR (2018) eller senare ändringar.
  `egenskap` har bara sakegenskaper: typ, form, konstruktion, verksamhet, fyndmaterial, figurtyp, material,
  bytesdjur, profil, fyllning, belägenhet, framdrivning, användning, terräng, byggnadsteknik och teknik.
  `lägesosäkerhet` säger bara att 96 % av lägena kommer från ”analog insamling” (Dålig, ≥10 m), utan år.
  `ingaendelamning` har bara antal och typ.
- **Men registret har ett fältdatum per lämning.** Fornsöks öppna API
  (`https://app.raa.se/open/fornsok/api/lamning/lamning/<uuid>`) ger `faltdatum`: senaste fältbesöket enligt FMIS.
  Fältet finns inte i GeoPackagen och inte i K-samsök. Det blev huvudkällan: 14 651 lämningar hämtade, upp till 6 per
  socken, ur poster som inte ändrats sedan migreringen 2018.
- **Täckning:** alla **636 av 636 runstenssocknar** har ett huvudår. **601 (94 %)** har låg eller medelhög osäkerhet
  (474 låg, 127 medel, 35 hög). I hela landet har 2 470 av 2 481 socknar ett huvudår. Där har 2 332 (94 %) låg
  eller medelhög osäkerhet.
- **Vad huvudåret mäter:** i 83 % av socknarna (2 059) ligger det i revideringsinventeringen (1978–2003). I 7 % (162)
  ligger det i överlappet 1974–77, i 8 % (192) efter 2003 och i 2 % (57) i förstagångsinventeringen. Fältdatumet
  skrivs alltså över när en lämning besöks igen. Huvudåret visar därför **när socknen senast inventerades
  systematiskt**, inte när den först inventerades.
- **Förstagångsåret** syns bara i beskrivningstexten (”inv 1939”, ”Förstagångsinventeringen 1952”, ”1953 års
  inventering”). Det finns ett årtal ≤ 1977 i texten för 387 av 636 runstenssocknar (61 %). Ett uttryckligen
  förstagångsmärkt år finns bara för 67 (11 %). Resten får klara sig med Hyenstrands landskapsdecennier.

## Filer

| Fil | Innehåll |
|---|---|
| `data/raa/d4_inventeringsar_socken.csv` | 2 481 socknar (län + socken som i KMR). Se kolumnerna nedan. |
| `data/raa/d4_inventeringsar_lan.csv` | per län: socknarnas huvudår (p10/median/p90), andel per period, förstagångsår i texten (median), runstenssocknar med huvudår |
| `data/raa/d4_inventering_text.csv` | 20 765 årtal som texten knyter till en inventering (18 761 lämningar), med slag och utdrag |
| `data/raa/d4_forstagang_landskap.csv` | förstagångsinventeringens ordning per landskap enligt Hyenstrand 1978, med citat |
| `/Volumes/2TB/Antigrvity/Runes/downloads/kmr_faltdatum/faltdatum.jsonl` | rådata: 14 651 lämningar med fältdatum, RAÄ-nr, FMIS-id, typ, bedömning och åtgärd (inga geometrier) |

Skript: `scripts/fetch_kmr_faltdatum.py` hämtar data. Det går att avbryta och starta om och gör ett anrop i taget
med paus. `scripts/d4_inventeringsar.py` har tre steg: `text` läser beskrivningarna i GeoPackagen, `build` bygger
tabellerna och `check` kör tillförlitlighetskontrollerna. Allt är git-ignorerat (`data/raa/`, `utdata/`) och ingenting
är incheckat.

Kolumner i socken-tabellen:
- `huvudar`: året med flest fältbesök inom ±1 år, eftersom en inventering kunde gå över två fältsäsonger.
- `andel_huvudar`: andelen av urvalets fältdatum som ligger inom ±1 år från huvudåret.
- `period`: förstagång 1938–73, överlapp 1974–77, revidering 1978–2003 eller efter 2003. Perioden bestäms bara av
  året, inte av någon uppgift om vilken omgång det var.
- `tidigaste_faltdatum`, `senaste_faltdatum`, `median_faltdatum` och `faltdatum_ar`: hela urvalets fältdatum.
- `n_bara_ar`: antal datum av typen ÅÅÅÅ-01-01, där bara året är känt.
- `text_forsta`, `text_revidering`, `text_ovrigt` och `text_tidigaste`: årtal ur beskrivningstexten.
- `osakerhet`, enligt reglerna nedan.
- `anmarkning`.

Osäkerhetsreglerna:
- **låg**: minst 5 fältdatum och minst 60 % inom ±1 år från huvudåret.
- **medel**: minst 3 fältdatum och minst 40 % inom ±1 år. Hit förs också socknar med låg osäkerhet om huvudåret
  ligger efter 2003.
- **hög**: färre fältdatum eller större spridning.
- **saknas**: inga fältdatum (11 socknar).

## Metod

1. **Universum:** alla lämningar i KMR med en enda socken och ett enda län. Det ger 2 481 socknar. Lämningar som
   ligger i flera socknar, 4 513 stycken, lämnas utanför urvalet.
2. **Urval:** bara poster med publiceringsdatum 2018. De är oförändrade sedan FMIS-migreringen och speglar alltså
   FMIS-läget (659 800 av 766 011). Ordningen inom varje socken är en fast slumpordning (seed = sha256 av län|socken).
   Upp till 6 lämningar per socken hämtades, alla typer och bedömningar. Runstenssocknarna hämtades först. Alla
   socknar fick samma k = 6, så runsten och icke-runsten har samma precision; andelen med 6 fältdatum är 68 % och
   69 %.
3. **Runstenssocknar:** socknarna för Runors 2 383 vikingatida svenska runristningar i KMR
   (`data/raa/kmr_runstenar.json`). Alla 2 383 finns i GeoPackagen. Det ger 636 par av län och socken.
4. **Text:** reguljära uttryck över `beskrivning` och `antikvariskbedomning_motivering`. Årtal får bara räknas när
   de står direkt efter eller före ett inventeringsord, till exempel ”inv 1946”, ”revideringsinventeringen 1984”,
   ”(Förstagångsinventeringen 1952 och revideringsinventeringen 2012)” eller ”1979 års inventering”. Varje träff
   klassas som förstagång, revidering, fornminnesinventering, Skog och historia eller allmän.

## Tillförlitlighet

Ingen av kontrollerna använder runstenar.

- **Delat urval:** i de 1 710 socknar som har 6 fältdatum jämfördes huvudåret ur post 1–3 med huvudåret ur post 4–6.
  Det stämde inom ±1 år i **85 %** av socknarna, och mediandifferensen är 0 år.
- **Mot texten:** i de 632 socknar som har både ett huvudår och ett revideringsår i texten stämmer de inom ±1 år i
  **81 %** och inom ±3 år i 84 %.
- **Mot litteraturen:**
  - På Gotland har 78 av de 87 socknar som har textårtal sitt tidigaste årtal 1938–1942. Hyenstrand skriver ”åren
    omkring 1940”.
  - Gotlands huvudår (median 1977, p10–p90 1976–78) stämmer med att revideringen började på Gotland 1974.
  - Kronobergs huvudår (median 2000) stämmer med RAÄ:s uppgift att revideringen i Kronoberg avslutades 2002.
  - Förstagångsåren i texten följer Hyenstrands ordning: Östergötland 1948, Kronoberg 1949, Stockholm 1951, Uppsala
    1952, Jönköping 1953 och Södermanland 1957.
- **Brister:**
  - 1 104 av 14 651 lämningar (7,5 %) har inget fältdatum.
  - För 5 427 (37 %) är bara året känt (ÅÅÅÅ-01-01).
  - Fältdatumet är senaste besöket. En lämning som besökts för ett uppdrag, av Skog och historia (1995–2007) eller vid
    en kvalitetshöjning före 2018 ger ett senare år. Det syns som spridning och som perioden ”efter 2003” (192
    socknar).
  - Blekinge (median 2008), Gävleborg, Örebro, Jämtland och Västerbotten har breda fördelningar. Där har
    länsstyrelserna inventerat om efter 2003, eller så har socknarna bara inventerats delvis.
  - Ett huvudår betyder inte att hela socknen har inventerats. Fjällen och det inre av Norrland räknas delvis som
    oinventerade (enligt Västernorrlands och RAÄ:s rapporter), men har ändå enstaka fältdatum. Detta påverkar knappt
    runstenssocknarna, men det påverkar ”tomma” områden i A2.
  - Socknarna är KMR:s sockenindelning (`socken` i GeoPackagen). De behöver nycklas mot SDHK och historiska socknar i
    A2.

## Vad som undersöktes och föll bort

1. **GeoPackagen:** inga datumfält utöver publicering och uttag. Se ”Kort svar”.
2. **Beskrivningstexten:**
   - Bara 2,4 % av posterna har ett inventeringsårtal. Andelen per län går från 0,4 % (Jönköping) till 5,7 % (Uppsala).
   - Per socken har däremot 69 % minst ett årtal. Andelen per län går från 43 % (Jönköping) till 95 % (Gotland och
     Kalmar).
   - Texten används som komplement för förstagångsåret, inte som huvudkälla.
3. **RAÄ:s dokumentation:** det finns ingen öppen tabell. Hyenstrand 1978 är den bästa översikten och ligger kodad i
   `d4_forstagang_landskap.csv`; han nämner inte Halland, Värmland, Närke och Dalsland uttryckligen. RAÄ:s rapporter
   per län, till exempel rapp2003:1 om Kronoberg och länsstyrelsernas revideringsrapporter, ger bara enstaka områden.
4. **Annan väg som inte prövades fullt ut:** RAÄ Arkivsök. Inventeringsböckerna är skannade per sockenuppslag. Serien
   heter till exempel ”Inventeringsböcker, revideringsinventeringen för den ekonomiska kartan”, och
   `https://arkivsok.raa.se/api/dokumentation/filter?attribute=kontext_uri&value=<lämnings-URI>` visar vilken serie en
   lämning står i. Böckerna saknar datum (`tillkomstdatum` är tomt), men serienamnet skulle kunna visa vilka socknar som
   har både en förstagångsbok och en revideringsbok. Det är en möjlig påbyggnad om A1/A2 behöver omgången och inte bara
   året.

## Förslag till de låsta studierna (inte beslutat här)

- **”Senast systematiskt inventerad”:** använd `huvudar`, eller `period`, och filtrera bort socknar med `osakerhet` =
  hög eller saknas.
- **”Först inventerad”:** använd `text_tidigaste` när det är ≤ 1977. Annars används landskapsdecenniet ur
  `d4_forstagang_landskap.csv`, och det ska anges som grovt.
- Lås i analysplanen hur fältdatumen efter 2003 ska hanteras innan något räknas.

## Källor och licens

- Kulturmiljöregistret, Riksantikvarieämbetet: GeoPackage `lamningar_sverige.gpkg` (uttag 2026-11-02) och Fornsöks
  öppna API (hämtat 2026-11-11). Licens CC0.
- Hyenstrand, Å. 1978. Fornminnesinventering, kulturminnesvård och arkeologisk samhällsforskning. *Fornvännen* 73,
  s. 69–71. CC BY 4.0. Lokal text: `downloads/tidskrifter/fornvannen/text/1978_069.txt`.
- Riksantikvarieämbetet 2020. *HAIK – Hållbar arkeologisk inventeringskompetens. Förstudierapport*: förstagångsinventering
  till 1977, revidering 1974–2003, regionalisering från 1997. Lokal kopia:
  `/Volumes/2TB/Antigrvity/Runes/downloads/d4_docs/HAIK_forstudie_2020.pdf`.
- Riksantikvarieämbetet, rapport 2003:1 (Kronoberg: revideringen avslutad 2002). https://www.raa.se/publicerat/rapp2003_1_low.pdf
- Ange källan så här: ”Fältdatum ur Kulturmiljöregistret (RAÄ, CC0) via Fornsök, urval och sammanställning: Vitki”.
