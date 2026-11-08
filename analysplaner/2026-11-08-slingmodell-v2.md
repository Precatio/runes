# Analysplan: blir slingmodellen bättre av nya granskade slingor? (slingmodell v2)

Skriven och låst 2026-11-08, innan någon ny slinga har ritats med den nya vägen. Viktor 2026-11-08: "gör 1,2,3", där 2
var: rätta slingorna direkt från bilden *Runor och ornamentik*, rättelserna sparas som ritade slingor och blir mer
träningsdata, och provet är överlappet före och efter omträning på stenar som modellen inte tränats på.

## Känt före låsningen
Slingmodell v1 (`data/runmodell/slingmodell.pt`, sha256 92a8913b…, `scripts/runmodell_slingor_train.py`, 150 epoker,
frö 1) är tränad på 71 av Viktors 95 granskade stenar; 24 hölls utanför (en fjärdedel per serie). De 24 är frysta i
`data/runmodell/slingmodell_provstenar.json` (gjord 2026-11-08 med samma uppdelning som träningen), så att nya stenar
inte ändrar vilka som prövas. v1:s överlapp med de ritade slingorna på de 24 (IoU vid sannolikhet 0,5): median 0,59,
från 0,10 till 0,83. På Sö 128 överlappar v1 och de ritade slingorna till 0,60.

## När provet körs
När minst **10 nya granskade stenar** finns, utöver v1:s 95 (ritade på ritsidan, från bilden *Runor och ornamentik*
eller för uppladdade skanningar som gjorts ritbara). Underlaget görs om med `scripts/runmodell_slingdata.py`.

## Modellerna
- **v1:** den driftsatta filen, oförändrad.
- **Kontroll v1′:** omtränad med samma inställningar på bara v1:s 71 träningsstenar
  (`--provstenar data/runmodell/slingmodell_provstenar.json --bara-v1`). Visar hur mycket en omträning ändrar utan nya data.
- **v2:** samma inställningar på v1:s 71 träningsstenar och alla nya granskade stenar (`--provstenar …`). De 24
  prövstenarna är aldrig med i träningen.

## Prov
Överlappet (IoU vid 0,5) mellan modellens och de ritade slingorna på var och en av de 24 frysta prövstenarna
(`scripts/runmodell_slingor_jamfor.py`).
**P1.** v2 mot v1, parvis per prövsten: Wilcoxons teckenrangtest, ensidigt (v2 högre). **Håller** om p < 0,05 och
medianen av skillnaden är positiv.
**P2.** Medianen av v2 − v1′ är positiv (förbättringen kommer av de nya stenarna, inte av omträningen).
Beskrivande: median per serie, och antalet prövstenar där v2 är bättre.

## Beslut (bestämt nu)
Håller P1 och P2 ersätter v2 `data/runmodell/slingmodell.pt`. Eftersom slingorna avgör vad huggspårsanalysen räknar som
runor på skanningar utan ritade slingor blir det en ny metodversion (`api/config.py` METHOD_VERSION, METHODS,
ändringslogg, nyhet), och modellens fingeravtryck skrivs i analysens parametrar. Håller någon av dem inte förblir v1,
och utfallet redovisas.

## Redovisning
`utdata/slingmodell_v2/` med träningsloggarna och `resultat.json` från jämförelsen.
