# Peterson 1996 – läst 2026-11-07

**Referens (rättad):** Peterson, Lena 1996. "Aft/æft, at och æftiR på de nordiska runstenarna – regional variation eller
vad?" I: Maj Reinhammar m.fl. (red.), *Mål i sikte. Studier i dialektologi tillägnade Lennart Elmevik*. Uppsala:
Dialekt- och folkminnesarkivet, s. 239–252. Samma sats i *Svenska landsmål och svenskt folkliv* 1995 (årg. 118), H. 321,
s. [239]–252. Fri PDF av hela årgången hos Kungl. Gustav Adolfs Akademien:
https://kgaa.bokorder.se/sv-SE/article/5541/svenska-landsmal-och-svenskt-folkliv-1995 (lokalt
/Volumes/2TB/Antigrvity/Runes/downloads/peterson1996_slfl1995/slfl1995.pdf, PDF-sidorna 249–262). Läst i sin helhet,
inklusive den engelska sammanfattningen.
Obs: titeln har *æftiR* (med ʀ), inte *æftir*, och festskriften är tillägnad Lennart Elmevik.

## Vad hon säger

- **Utgångspunkt: Palm 1992.** Hon återger Palms "dialektal gräns som löper i sydlig-nordlig riktning" i Uppland och
  Södermanland (Palm s. 232), med Palms förbehåll att valet "någon gång kan vara bundet till ristaren eller till
  »monumentmarkören»" (s. 239).
- **aft/æft är äldst, inte regionalt.** De säkra beläggen i Sverige hör till "tiden från 800-talets början till
  1000-talets början" (s. 244). Att aft/æft har tyngdpunkt i Danmark beror på att runstensresandet där "upphörde långt
  tidigare" (s. 244). Palms bild är på den punkten "alltför förenklad" (s. 242).
- **at mot æftiR i tid: svag skillnad.** Efter Herschend 1994: at dominerar i Gräslunds stil "fågelperspektiv"
  (Ingvarsstenarna), æftiR i Pr 3 och Pr 4. "Det tycks alltså som om det skulle finnas en viss kronologisk skillnad mellan
  at och æftiR i Mälarområdet. Tendenserna är dock svaga" (s. 245).
- **Ingen betydelseskillnad.** 70 svenska inskrifter har både at och æftiR; "I bara åtta av dem står at före æftiR"
  (s. 246). Ordningen följer familjens rangordning, inte ordet: hennes tabell 2 över formeln *at … (ok) at* (s. 247)
  motsäger Herschends tanke att at gäller en vidare krets. "Palms enkla konstaterande att at var en kort och praktisk
  variant till æftiR tycks [...] komma sanningen närmast. Till sitt innehåll är formerna synonyma." (s. 247)
- **Vers förklarar inte.** Av Hüblers 17 versifierade inskrifter med minnesformel har bara två æft (Vg 59, U 323), åtta
  at och åtta æftiR (s. 245). Södermanlands höga andel at kanske hör ihop med textkonsten där, men det är "en öppen fråga"
  (s. 247 f.).
- **Svaret (s. 249):** "Regional variation? – Nej och ja. Kronologisk? – Ja och nej. Stilistisk? – Nej(?). Semantisk? –
  Nej."

## Vad det betyder för folklandsgränsen

1. **Gränsen är inte beskriven där.** Peterson delar inte upp Uppland och prövar ingen gräns. Hennes enda tal för
   Uppland är Palms landskapssumma (at 167 av 665, 25,1 %, tabell 1 s. 243). Ristarna behandlar hon inte, utöver Palms
   förbehåll. Det vi har lagt till (skärpan i tio kilometers bandet, samma ristare på båda sidor, de formella
   kontrollerna) står alltså kvar som vårt, men byggt på Palm 1992.
2. **Tid.** Herschends svaga skillnad mellan stilgrupperna är skälet till att tiden hålls konstant i proven. Det ska stå i
   rapporten med hänvisning till Peterson s. 245.
3. **Antalet namn.** Att fler namn på stenen ger mer at (OR 1,6 per namn i trappan) är det kända mönstret med at som andra
   preposition (Palm 1992 s. 232, Peterson 1996 s. 246). Det är inte ett eget fynd och ska anges som känt.
4. **Betydelse.** Petersons slutsats att formerna är synonymer stöder läsningen att gränsen gäller ett val mellan två
   likvärdiga ord, det vill säga en vana i bygden, inte olika innebörd. Herschend 1997 (*Arkiv för nordisk filologi*
   112, s. 113–123) svarade och försvarade betydelseskillnaden. Den är inte läst.
5. **Vers.** Ingen av Hüblers versifierade upplandsstenar ligger i gränszonen. Vers kan inte förklara gränsen.

## Kodningsproblemet som läsningen ledde till (kontroll utanför planerna)

Draget `prep_at` (src/language_profile.py, regeln `preposition`) räknar at bara när ett namn följer direkt efter. Det
missar minnesformelns at framför släktord, alltså just at som andra preposition: "æftiR "Æist, faður sinn, ok "Fastlaug
**at** bonda sinn" (U 461). Bland de 517 stenarna i gränsprovet gäller det 15, varav 12 i Attundaland: U 48, 200, 225,
287, 323, 461, 462, 463, 485, 512, 565, 578 (Attundaland) och U 906, 977, 999 (Tiundaland). Den korta formen aft/æft
räknas dessutom som æftiR (7 stenar).

`at_kodkontroll.py` kör de låsta skripten oförändrade på rättade rader (kodkontroll/A och B, sammanfattning.json):

| | Kodning som i appen | A: at före släktord räknas | B: A utan stenar med bara aft/æft |
|---|---|---|---|
| Gränszonen, ristare som slumpeffekt | OR 5,9, p 0,0014 | OR 3,4, p 0,017 | OR 3,2, p 0,020 |
| Hela Tiundaland mot Attundaland | OR 3,1 | OR 2,2 | OR 2,2 |
| Öpir, Tiundaland mot Attundaland | 21/39 mot 4/23 | 22/39 mot 7/23 | 22/39 mot 7/23 |
| Socken som slumpeffekt | OR 5,9 | OR 3,4, p 0,013 | OR 3,2, p 0,015 |
| Bara oflyttade stenar | OR 6,8, p 0,018 | OR 3,0, p 0,053 | OR 2,8, p 0,061 |
| Hela trappan håller | ja | nej (oflyttade faller) | nej |

**Läsning:** gränsen för at finns kvar med rättad kodning, men den är ungefär hälften så stark, och den håller inte längre
varje steg i trappan. Det tidigare "fullt prövat inom planerna" gäller kodningen som den var. Rättas regeln i appen
ändras korpusens fingeravtryck, och folklandsprovet, gränsskannern och robusthetstrappan måste köras om. Till dess ska
folklandsrapporten (utkast YRM1lY3VZT5U4k5xtfnR) inte publiceras med de nuvarande talen för at.
