# Analysplan A1, tillägg 1: SRI:s fyndhistorik som tredje källa

Skrivet och låst 2026-11-12. Tillägget gäller analysplanen `2027-01-A1-flyttade-och-forsvunna.md` (låst 2026-11-11,
4eef7f6). Planen själv ändras inte. Där de säger olika saker gäller tillägget. Viktor sade ja till tillägget och till en
pilot 2026-11-12.

## Varför
A1 bygger på Rundata, Runor och KMR. Utgåvan Sveriges runinskrifter (SRI) beskriver varje stens fyndhistoria fram till
bandets utgivning: var den stod, när och varför den flyttades, när den försvann eller återfanns, och vem som först
nämnde den. Den kunskapen finns i dag bara som löptext. Tillägget gör den till en tabell, med sida och ordagrant citat
för varje uppgift, och använder den som tredje källa bredvid Rundata och Runor.

## Vad som har gjorts före låsningen
- SRI hämtades från RAÄ 2026-11-12 (`scripts/hamta_sri.py`). Texterna används enligt Vitkis källregel, steg 1–2
  (METHODS §17): de läses och räknas, och de citeras kort med källa. De publiceras inte vidare.
- Banden delas upp i en artikel per sten med `scripts/sri_artiklar.py`. Utdata ligger utanför repot.
- Södermanland (SRI III) gav 354 artiklar. Alla matchar ett signum i Rundata. 28 nummer hittades inte, troligen på grund
  av OCR-fel i rubrikerna.
- Ingen uppgift har plockats ut, och ingenting har jämförts med `is_moved`, Runor eller jordarterna.

## Utplockningen
**Vem som läser.** Anthropics språkmodell Claude (Sonnet) läser artiklarna, ungefär 45 per körning. Den skriver
utgivarens uppgifter i fälten nedan och tar bara med det som står i artikeln. Den gör ingen egen läsning av inskriften,
ingen egen tolkning och ingen gissning av årtal. Varje uppgift ska ha ett ordagrant citat ur artikeln (högst 250
tecken) och den tryckta sidan.

**Fälten per sten** (`/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta/<verk>.jsonl`, utanför repot eftersom citaten
är SRI:s text):

| Fält | Innehåll |
|---|---|
| `lage_vid_utgavan` | `ursprunglig plats` / `flyttad` / `försvunnen` / `okänt` – vad utgivaren säger om stenens läge när bandet skrevs |
| `ursprunglig_plats_text` | utgivarens beskrivning av var stenen ursprungligen stod, om den anges |
| `flyttningar[]` | varje flyttning: `ar` (heltal eller null), `fran`, `till`, `orsak` (se nedan) |
| `forsvunnen` | `forsvann_ar` (heltal eller null) och om stenen var försvunnen när bandet skrevs |
| `aterfunnen[]` | `ar` (heltal eller null) och var den återfanns |
| `inmurad` | om stenen satt eller sitter inmurad i en kyrka eller annan byggnad |
| `fragment` | om utgivaren beskriver stenen som fragment eller delvis förstörd |
| `kallor_i_ordning` | källorna i artikelns litteraturrad, i den ordning de står (till exempel "B. 754", "L. 980", "J. Peringskiöld") |
| `samma_sten_som[]` | signum eller ställen som utgivaren säger är samma sten eller en del av samma sten |
| `datering_text` | utgivarens egen datering eller stilbedömning. Används inte i A1 utan sparas till studie C |

Varje fält har `citat` och `sida`. Ett fält som artikeln inte nämner lämnas tomt (null), och det betyder "nämns inte".

**Orsakskategorier för flyttningar**, bestämda nu:
- kyrkbygge eller restaurering;
- vägbygge;
- odling, dikning eller annat jordbruk;
- samling eller museum;
- återresning på samma plats eller i närheten;
- annat;
- okänd.

## Kontroll innan uppgifterna används
1. **Citaten.** Ett skript letar upp varje citat i artikelns text. Jämförelsen görs efter att blanktecken, sidmarkörer
   och avstavning har normaliserats, och om det behövs utan några mellanslag alls, eftersom OCR:en sprider bokstäver
   ("ä r"). En uppgift vars citat inte hittas stryks, och antalet redovisas.
2. **Stickprovet.** 60 stenar lottas med slumpfrö 2026 bland bandets artiklar. En granskare, Claude (Opus), har inte
   gjort utplockningen. Granskaren jämför varje ifyllt och tomt fält med artikeln och bedömer det som rätt, fel eller
   saknat.
   - **Krav per fältgrupp:** minst 95 % rätt, och den nedre gränsen i Wilsonintervallet på minst 88 %.
   - **Fältgrupperna:** läget, flyttningarna, försvunnen och återfunnen, och samma sten.
   - En fältgrupp som inte klarar kravet används inte i A1, och det skrivs ut.
   - Viktor får 20 av de 60 stenarna att kontrollera själv. Hans bedömning går före granskarens.
3. **Piloten** körs först på Södermanland. Klarar den kraven körs övriga band på samma sätt, med eget stickprov per
   band. Allt ska vara klart före A1-körningen i januari. Ett band som inte hinner bli klart, eller inte klarar kraven,
   lämnas utanför, och det skrivs ut.

## Hur SRI används i A1
SRI beskriver läget **när bandet skrevs** (1900–1981), inte i dag. Det skrivs vid varje resultat.

- **P1c, fjärde skattningen ("SRI"):** andelen bevarade stenar som utgivaren säger står på ursprunglig plats, per
  landskap och med Wilsonintervall. Den är en robusthetsrad bredvid de tre skattningarna i planen, inte en ny
  huvudskattning. Dessutom redovisas överensstämmelsen mellan SRI och `is_moved` och mellan SRI och Runors `original`
  (Cohens kappa och korstabell).
- **P1a, beskrivande:** flyttningar som SRI anger före bandets utgivning, per orsak och per halvsekel. Inga avstånd
  räknas, eftersom SRI:s platser saknar koordinater. Flyttningar före första dokumentationen syns fortfarande inte.
- **P3, första dokumentationen:** E1–E3 bestäms som i planen. Som robusthetsrad används också den äldsta källan i
  `kallor_i_ordning`, översatt till år med en tabell som skrivs i `utdata/flyttade/sri_kallor_ar.csv` innan den läggs
  mot något. Tabellen gäller till exempel Bureus, Rhezelius, Hadorph och Peringskiöld, Bautil och Liljegren. Källor
  som inte finns i tabellen räknas inte.
- **P3c, de märkta (M):** stenar som SRI säger var försvunna när bandet skrevs används som robusthetsrad för M.
  Återfynden m räknas som i planen.
- **P5, positiv kontroll:** par som SRI säger är samma sten och som Rundata inte har slagit ihop läggs till som extra
  positiva kontroller. Regeln och τ ändras inte. Andelen av paren som regeln fångar redovisas.
- **P2 och P4:** oförändrade. Försvunnen-flaggan kommer från Rundata.

## Vad som inte får göras
- `is_moved` ändras inte i A1, inte heller där SRI säger något annat. Oenigheterna listas som ett förslag till Viktor,
  som i planen.
- Inga nya prov, gränser eller delurval på SRI-uppgifterna utöver raderna ovan.
- Utplockningen läses inte mot A1:s utfall innan körningen. Stickprovet jämförs bara med SRI-texten.
- Citaten publiceras bara som korta utdrag med källa och sida (citaträtten). Tabellen kan publiceras som eget dataset
  utan citaten, med fälten, signum, band och sida.

## Redovisning
- `scripts/sri_artiklar.py` och `scripts/sri_fakta_kontroll.py` (citatkontroll, stickprov, träffsäkerhet).
- **Per band:** `utdata/sri_fakta/<verk>_kontroll.json`, med antal artiklar, strukna citat, stickprovets träffsäkerhet
  per fältgrupp och Viktors kontroll.
- **Metodtext:** i rapporten och i METHODS anges modellerna, Claude Sonnet för utplockningen och Claude Opus för
  granskningen, liksom kraven och utfallet av kontrollen.
