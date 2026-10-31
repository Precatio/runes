# Analysplan: seriationen i Upplands halvor och i Södermanland

Skriven och låst 2026-10-31, innan någon seriation av Södermanlands stenar för sig eller av Upplands två halvor var för
sig har gjorts. Viktor 2026-10-31, om listan över fynd som kan kvala efter en ny prövning: ”Gör den prövningen.”

## Varför
Seriationen (`r/chronology.R`) ordnar Upplands runstenar efter språkdrag, formler, kors, kortkvistrunor och innehåll,
utan stilgruppen, i nästan samma följd som Gräslunds stilkronologi: Spearmans rho 0,543 mot stilgruppens mittår
(501 daterade stenar), 0,539 med latituden konstant (korpus `e83202e01a5e6d27`). Resultatet var inte förregistrerat och
har inte prövats i materialets två halvor. Mallen för forskningsrapporter (version 2) kräver att ett fynd håller i båda
halvorna och efter justering för många test. Södermanland har aldrig seriationsprövats för sig. Hela korpusen har det
(första dimensionen följer där regionala skillnader, inte tiden); Södermanlands stenar ingick i den körningen men gav
inget eget resultat.

## Data
Korpus `e83202e01a5e6d27` (`corpus.csv`, `text_features.csv`), samma som `chronology.json`.
- **Uppland:** samma urval som `r/chronology.R`.
- **Södermanland:** alla runstenar i Sö med samma urvalsregler; 363 stenar, varav 168 med stilgrupp, före regeln om
  minsta antal drag per sten.

## Metod (exakt som `r/chronology.R`, inga nya val)
- Incidensmatris av språkdrag, formler, kors, kortkvistrunor och innehållskategorier; drag på minst 15 stenar, stenar
  med minst 4 drag. Stilgruppen ingår inte.
- Korrespondensanalys (paketet ca), första dimensionen. Spearmans rho mot stilgruppens mittår bland daterade stenar.
  Axelns tecken är godtyckligt, så riktningen vänds så att rho blir positiv; testet är `cor.test` tvåsidigt.
- Partiell korrelation med latituden konstant (rangresidualer), som i `r/chronology.R`.
- Rho inom härad (härader med minst 5 daterade stenar), beskrivande.

## Prövningarna
1. **Upplands halvor.** Seriationen görs om var för sig i halva A och halva B. Halvorna delas socken för socken med
   samma regel som `r/change.R` (socknarna ordnade efter medeldatering inom landskapet, varannan till A och B),
   räknad på alla Upplands stenar.
2. **Södermanland**, replikering på data som inte har seriationsprövats.
3. **Holm** över de tre testen (halva A, halva B, Södermanland).

## Vad som avgör
- **Halvorna:** håller när Holm-p < 0,05 och rho ≥ 0,3 i båda halvorna. Då når seriationen golvet i mallen version 2
  (båda halvorna; justeringen för alla samband i projektet är redan q < 0,001) och kan bli ett Delvis prövat fynd.
  Seriationen har ingen robusthetstrappa (den är inte ett samband mellan två drag), så den kan inte bli Fullt prövad.
- **Södermanland:** *replikerat* när Holm-p < 0,05 och rho ≥ 0,3; *delvis replikerat* när Holm-p < 0,05 men rho < 0,3;
  *inte replikerat* annars. Är den partiella korrelationen med latituden konstant under 0,3 när rho är över, sägs att
  sambandet kan vara geografiskt. Faller Södermanland gäller en rapport bara Uppland, och det sägs.
- Inga parametrar ändras efter körningen. En provkörning som återger Upplands kända rho 0,543 på hela Uppland får göras
  för att hitta kodfel; den styr inget val och redovisas.

## Redovisning
`utdata/seriation/replikering.R`, `utdata/seriation/replikering.json`, `utdata/seriation/replikering_resultat.md`.
