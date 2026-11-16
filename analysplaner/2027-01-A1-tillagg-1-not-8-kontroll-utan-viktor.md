# A1, tillägg 1, not 8: kontrollen av de återstående enheterna görs utan Viktor

Skriven och låst 2026-11-16. Gäller tillägg 1 och noterna 1–7. Viktor bestämde 2026-11-16: "gör alla bedömningar
du, jag har inte tid".

## Vad som ändras
Tillägget (punkt 2) och not 2 säger att Viktor själv kontrollerar 10 lottade stenar per enhet och att hans bedömning
går före granskarens. För Östergötland (runda 1), Öland (runda 2) och de små mellansvenska banden (runda 1), och för
Gotland och Västergötland runda 2 när de är granskade, ersätts hans kontroll så här:

1. **Samma 10 stenar.** Det är de stenar som redan lottats för Viktor (slumpfröna i not 5 och not 7). Inget lottas om.
2. **Blind kontrolläsning.** En Opus-läsare som inte ser granskarens bedömning läser SRI-artiklarna och bedömer de fem
   fält som Viktor skulle ha bedömt (läget, `ursprunglig_plats_text`, `inmurad`, `forsvunnen`, `aterfunnen`), med
   reglerna 1–13 och samma rätt/fel/saknat som på Viktors kontrollsida. Utdata: `granskning/<enhet>_kontroll3.jsonl`.
3. **Utslag.** Där den blinda läsaren och granskaren är oense läser Claude (Opus, i huvudsessionen) SRI-stället och
   avgör. Där de är eniga gäller deras bedömning. Det avgjorda resultatet, `granskning/<enhet>_kontroll3_avgjord.jsonl`,
   går före granskaren på samma sätt som Viktors bedömning.
4. **Regeln om en för snäll granskare (not 2) gäller oförändrad**: har det avgjorda resultatet fel eller saknat i minst
   två fält som granskaren bedömt som rätt, räknas granskaren som för snäll.
5. **Viktors egna kontroller står kvar** för Södermanland, Uppland och Småland. Vill Viktor senare kontrollera en
   enhet själv går hans bedömning före den avgjorda.

## Första utfallen (2026-11-16)
- **Öland runda 2:** den blinda läsaren fann 0 fel i 50 fält. En oenighet (Öl 45, läget "okänt") avgjordes för den
  blinda läsaren: SRI återger bara Rhezelius 1600-talsuppgift och säger inte var stenen var när bandet skrevs.
- **Östergötland runda 1:** den blinda läsaren fann 9 fel i fält som granskaren bedömt som rätt, och Claude höll med i
  alla nio. Fyra första fynd står som återfynd, tre stenar som hittades i en kyrkvägg har läget "okänt" i stället för
  "flyttad", och en stenmur och en kyrkogårdsmur har räknats som inmurning i byggnad. Östergötland lästes före
  reglerna 12 och 13. Granskaren räknas som för snäll (not 2), och Östergötland går därför **runda 2**: hela bandet
  läses om med reglerna 1–13, stickprovet om 100 stenar lottas med slumpfrö 2054 bland de 126 stenar som inte låg i
  runda 1, och kontrollens 10 med 2055. Runda 2 är Östergötlands sista.
- **De mellansvenska banden runda 1:** den blinda läsaren fann 4 fel; två av dem hade granskaren också funnit (Gs 9,
  Nä 9). Claude avgjorde de två oenigheterna mot granskaren: Nä 27 är "inlagd i östra bogårdsmuren", alltså en
  kyrkogårdsmur och ingen byggnad, och Gs 6:s ursprungliga plats ("lär ha stått på … vid gravfältet") är Humblas
  hörsägen i en skrivelse från 1934 som utgivaren citerar, inte utgivarens egna ord (regel 5; ett gränsfall). Med
  utslagen är andelarna 97,1 % (läget), 99,4 % (försvunnen och återfunnen) och 97,5 % (samma sten), men granskaren
  räknas som för snäll. Enheten har bara 81 artiklar, och alla låg i runda 1:s stickprov. **Runda 2** blir därför en ny
  granskning av samma 81 stenar och samma utplockning (den gjordes redan med reglerna 1–13), med nya granskare och 10
  nya kontrollstenar lottade med slumpfrö 2057. Att stenarna inte är nya är en svaghet, som för Öland, och den
  redovisas.
- **Gotland runda 1 och Västergötland runda 2** kontrolleras på samma sätt. Deras utfall, och utfallen av
  Östergötlands och de mellansvenska bandens runda 2, skrivs i en not 9.

## Svagheten
Ingen människa har kontrollerat dessa enheter. Utplockningen (Sonnet), granskningen (Opus) och kontrollen (Opus) görs
alla av Claude-modeller, så gemensamma blinda fläckar fångas inte. Det mildras men tas inte bort av att den blinda
läsaren inte ser granskarens bedömning. Rapporten anger för varje enhet vem som kontrollerade.
