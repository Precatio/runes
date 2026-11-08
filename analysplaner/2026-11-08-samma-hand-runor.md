# Analysplan: ser ristarmodellen samma hand som runologerna? Ett externt prov mot Runor 2020

Skriven och låst 2026-11-08, innan modellens förslag för grupperna nedan har tagits fram. Viktor 2026-11-08: "Kör vidare
på att göra rapporten gångbar" – en forskningsrapport om ristarmodellens starkaste förslag, som håller för forskare.

## Varför
Ristarmodellen (`r/attribution.R`, modell K0: textdrag, kors och korsformer, koordinater; kalibrerad, METHODS 1;
metodrapporten *Statistiska ristarförslag ur runtexterna*, DOI hos Zenodo) är prövad mot Rundatas ristare, som till stor
del bygger på Axelson 1993 och samma slags drag – inte mot ett oberoende facit. Bland de 93 förslagen för stenar utan
ristare med kalibrerad sannolikhet minst 0,8 går 49 till Öpir, och Runor 2020 namnger ingen ristare för någon av dem.
Runor 2020 (Riksantikvarieämbetet) har däremot runologernas egna bedömningar av formen "samma som gjort X" – ofta för
stenar vars ristare inte har något namn. De är ett facit som modellen aldrig har tränats på.

## Känt före låsningen
132 noteringar i Runor 2020 (hämtat 2026-10-26, `data/cache/runor/`) med "samma" eller "imitation" i ristarfältet; 76 av
dem gäller stenar i Vitkis korpus (48 i Uppland). Modellens förslag för grupperna har inte tagits fram.

## Data
- **Grupperna:** noteringar i Runor 2020:s ristarfält som säger att två stenar är gjorda av samma hand: *Samma som gjort*,
  *Samma ristare som*, *Troligen/Antagligen/Förmodligen/Eventuellt samma som*. De nämnda stenarna läses ur noteringen
  (signumprefixet ärvs: "U 1015, 1017-1024" = U 1015, U 1017 … U 1024). *Imitation av* och *tillsammans med* räknas inte.
  En grupp = stenar som hänger ihop genom sådana länkar, bland korpusens stenar med koordinater och modellförslag.
- **Modellen:** korpus 510ebfb3 (modell K0, oförändrad, inte omtränad). För en sten med ristare i Rundata används
  förslaget från den korsvalidering där stenen inte var med (`attribution_oof.csv`), för en sten utan ristare förslaget i
  `attribution.json`. Förslaget = modellens mest sannolika ristare.
- **Avstånd:** fågelvägen mellan stenarnas koordinater.

## Måttet
**Samstämmighet** i en grupp = andelen stenpar i gruppen där modellen föreslår samma ristare för båda stenarna.
**Kontroll:** för varje par (A, B) på avståndet d dras en kontrollsten C bland korpusens stenar med förslag, utanför
gruppen, på avståndet d ± 25 % (minst ± 1 km) från A; kontrollens samstämmighet är andelen par (A, C) med samma förslag.
Medelvärdet över 999 dragningar per grupp. Kontrollen behövs eftersom modellen använder koordinaterna: grannstenar får
lätt samma förslag oavsett hand.

## Prov
**H1 (huvudprov).** I runologernas grupper där minst en sten saknar säker ristare i Rundata ("onämnda händer"): gruppens
samstämmighet minus kontrollens, med grupperna som enheter. Wilcoxons teckenrangtest, ensidigt. **Håller** om p < 0,05 och
medianen av skillnaden är positiv.
**Känslighet (beskrivande):** alla grupper; bara noteringar som Runor anger som säkra; kontroll på d ± 10 %.
**H2 (beskrivande).** Per grupp: stenarna, Runor-noteringen, Rundatas ristare, modellens förslag och kalibrerade
sannolikhet – underlaget för rapportens prövbara frågor. Hur ofta förslaget är Öpir redovisas.

## Beslut (bestämt nu)
Håller H1 ser modellen något av det runologerna ser som samma hand, utöver geografin, och rapporten lägger fram modellens
förslag för grupperna och de starkaste enskilda förslagen som prövbara frågor, med det här provet som det oberoende
stödet och Öpir-snedvridningen redovisad. Håller H1 inte skrivs ingen rapport om förslagen; metodrapportens
begränsningar får en rad om utfallet.

## Redovisning
`utdata/samma_hand/`: `prov.py` (grupperna, förslagen, kontrollen, H1–H2), `resultat.json`, `resultat.md`.
