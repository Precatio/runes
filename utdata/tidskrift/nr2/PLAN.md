# Korpus nr 2 – mars 2027 – *Det vi inte ser*

20 sidor (häftas i ark om fyra), svenska och engelska. Bara den svenska utgåvan trycks.

**Löftet.** Sidan 19 i nr 1, också i de tryckta exemplaren, lovar fyra delar och "I appen: Luckor i texten".
Löftet hålls (Viktor 2026-11-13). Där står också "resultaten – också de som inte håller – kommer i nästa nummer".
Alla fyra delarna levereras alltså, även om ett resultat blir negativt.

**Regeln för att skriva i förväg.** Färdigt skrivs bara det som vilar på resultat vi redan har. För A1-delarna
förbereds bakgrund, metod och källor, men inga slutsatser före körningen (januari–februari 2027).

## Sidplan

| Sida | Innehåll | Underlag | Läge |
|---|---|---|---|
| 1 | Omslag | bild väljs (förslag: en försvunnen sten i Bautil eller en flyttad sten vid en kyrka) | – |
| 2 | Innehåll + Från redaktören | Viktors svar på tre frågor (nedan) | frågor skickade 13 nov |
| 3 | Det vi inte ser i siffror | korpusfakta: försvunna 415, flyttade enligt `is_moved` 1 223, odaterade, nummer utan SRI-artikel m.m. | räknas vid bygget |
| 4–7 | **Stenarna som flyttades** | A1 P1 + SRI:s fyndhistorik (läget) | bakgrund kan skrivas nu; resultat efter A1 |
| 8–10 | **Stenarna som försvann** | A1 P2–P3 (jordarterna, upptäcktskurvan, fångst–återfångst) | bakgrund nu; resultat efter A1 |
| 11–13 | **När restes stenen?** | beskrivande: stilgruppernas sex värden, de fasta punkterna (Ingvars- och Englandsstenarna), vad som händer när dateringen är osäker (`utdata/datering/resultat.md`, MI-försöket, robusthetstrappan) | kan skrivas nu, med data vi har |
| 14–16 | **Ingvarsstenarna** | utkastet `utdata/blogg/ingvar.json` (publiceras 8 dec) + självkontrollrapporten (15 dec) | finns, kortas till tidskriftsform |
| 17 | Metodhörnan: vad är fångst–återfångst? | `nr2/innehall_nr2.py` METOD | utkast klart 13 nov |
| 18 | I appen: Luckor i texten | `nr2/innehall_nr2.py` APP; skärmbilder sv+en tas ur den lokala appen | text klar 13 nov; bilder saknas |
| 19 | Nästa nummer: nr 3, juni 2027, *Platserna* | PUBLICERINGSPLAN.md §3: Gravar, vägar eller gränser?; lerans kant; De gamla landen; Norgeartikeln | skrivs när nr 3:s planer är låsta |
| 20 | Baksida | samma upplägg som nr 1, ny bild | – |

Verkstaden (litteraturen) får ingen egen sida i nr 2. *Hundra år av runfrågor* publiceras som artiklar 19 jan och
2 feb 2027 och kan få en ruta i "Det vi inte ser i siffror" om det finns plats.

## Från redaktören: frågorna till Viktor (13 nov)
1. Varför ville du att andra numret skulle handla om det vi *inte* ser? Var det något som fick dig att tänka på de
   flyttade och försvunna stenarna?
2. Vad har du själv lärt dig av att arbeta med de gamla källorna, Bautil, Peringskiöld och SRI, den här hösten?
3. Nr 1 är tryckt och skickat till institutionerna. Hur har mottagandet varit, och vad vill du säga till de nya
   läsarna?

## Bygget
`utdata/tidskrift/bygg_tidskrift.py` är skrivet för nr 1 (ARTIKLAR, REDAKTOR, APP och texterna i T).
Före bygget av nr 2 görs det nummerstyrt (`--nr 2` läser `nr2/innehall_nr2.py`). Det görs när artiklarna finns,
tidigast i februari, så att arbetet inte görs två gånger.
