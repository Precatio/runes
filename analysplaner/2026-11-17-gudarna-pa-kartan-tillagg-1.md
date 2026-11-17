# Tillägg 1 till "Gudarna på kartan": kultplatserna och väsendena

Skrivet och låst 2026-11-17, efter huvudplanen (sha256 e120282a) och dess resultat, men innan något av det nedan har
graderats eller räknats per landsdel. Viktor 2026-11-17, efter att proven med gudanamnen inte höll: "vi borde se till
annat än just gudanamn, det finns säkert ortnamn med fornnordiska referenser som är annat än gudar".

## Känt före låsningen
- Huvudplanens prov (Tor, Oden och Frö mot landsdel och grannar) höll inte, med 32 namn och låg styrka. Det står fast
  och prövas inte om. Tor fanns i alla sju landsdelar.
- En sökning i SOL:s 6 045 uppslag, bara antal och inte område: vi omkring 35 uppslag, harg 18, hov 8, al 17, helig lund
  6, helig/helg- 106 (mest kristna: helgon, Allhelgona), sakral/kult/offer/blot/hednisk 79, troll 12, jätte/jötun/turs
  11, alv/vätte/rå/näck/dis 43 (mest *älv*), ting 84. Sökorden fångar mycket som inte hör hit; graderingen avgör.

## Kategorierna
- **Kultplats:** SOL:s tolkning säger att namnet innehåller ett förkristet sakralt ord eller syftar på en förkristen
  kultplats: vi, harg, hov, al ('helgedom'), en lund, åker, tuna, ö, sjö eller annan plats som SOL kallar helig, helgad,
  sakral eller kultplats i förkristen mening, eller ett gudanamn (huvudplanens säkra och osäkra namn ingår). Kristen
  helighet (helgon, kyrka, kloster, Allhelgona, helig källa med helgonnamn) räknas inte.
- **Väsen:** SOL:s tolkning säger att namnet innehåller troll, jätte (jötun, turs), alv (inte *älv* 'flod'), dis,
  vätte, rå eller näck.
- **Ting:** SOL:s tolkning säger att namnet syftar på ett ting eller en tingsplats. Bara beskrivande.

## Gradering
Varje uppslag med minst ett sökord (huvudplanens gudalista och orden ovan: vi, harg, hov, al, helig, helg, sakral,
kult, offer, blot, hednisk, troll, jätt, jötun, turs, alv, alf, dis, vätte, rå, näck, ting) får sina meningar med
sökorden utdragna ordagrant. **Två oberoende, blinda kodare** (Claude Opus, var för sig, utan varandras svar) ger
varje uppslag en kategori (kultplats, väsen, ting, ingen) och en grad (säker, osäker, avvisad) efter huvudplanens
förbehållsord. Vid oenighet gäller den strängare graden, och vid oenighet om kategorin gäller *ingen*. Oenigheten
redovisas. Meningarna stannar utanför git (källregeln).

## Landsdel
Landskapet i SOL:s huvudrad avgör landsdelen, med huvudplanens indelning. Uppslag utan landskap räknas bort. Socknen
behövs bara för kartan (huvudplanens regler).

## Del C. Två prov (tvåsidiga, Holm över de två, α = 0,05; huvudplanens omblandning och slumpfrö, men ur detta
tilläggs kontrollsumma)
- **C1. Var ligger kultlandskapet?** Bland alla SOL-uppslag med landsdel: andelen kultplatsnamn (säkra och osäkra) per
  landsdel. Teststorhet χ² för tabellen landsdel × kultplats ja/nej. Omblandning: etiketten kultplats blandas om mellan
  alla uppslag med landsdel, 10 000 gånger. Provet jämför alltså mot hur många namn SOL har i varje landsdel.
- **C2. Olika slags kultplatser i olika landsdelar?** Bland kultplatsnamnen: efterledet i SOL:s tolkning, i grupperna vi,
  harg, hov, al, lund, åker, övrigt (gudanamn utan något av dessa efterled räknas till övrigt). Teststorhet χ² för
  efterled × landsdel; omblandning av efterledet mellan namnen.

Ett prov **håller** när Holm-justerat p < 0,05 och teststorheten räknad på bara de säkra namnen ligger över
omblandningarnas median. Ett prov som inte håller skrivs som att det inte gick att se, inte som att det saknas.

## Beskrivande
Antal per kategori, grad och landsdel; en karta med kultplatser, väsen och ting; för väsendena anges om SOL säger att
namnet är medeltida eller yngre (folktro), eftersom ett trollnamn inte behöver vara förkristet.

## Utdata
`utdata/asatro/analys_tillagg1.py` → `utdata/asatro/resultat_tillagg1.json`; meningarna och graderingarna i
`/Volumes/2TB/Antigrvity/Runes/downloads/asatro/` (utanför git).
