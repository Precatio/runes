# Analysplan: Vikingarnas omvärld – öster och väster i runstenar, Edda och sagor

Låst 2026-10-28, innan något test nedan har körts. Planens SHA-256 står i
`analysplaner/2026-10-28-vikingarnas-omvarld.sha256`. Avvikelser redovisas i `utdata/varlden/resultat.md` under
*Avvikelser från planen*.

Före låsningen har följande gjorts (`utdata/varlden/`, se README.md där): korpusarna har hämtats, ortnamnslistan
`platser.csv` har byggts och rensats från falska träffar efter kontroll i `kwic.txt`, och `rakna_platser.py` har räknat
träffar per text. Vi har sett korpusernas östandel räknad på alla träffar (svenska runstenar 68 %, fornaldarsagor
58 %, Heimskringla prosa 43 %, Heimskringla vers 38 %, islänningasagor 23 %) och antalet stenar och strofer med någon
plats. Ingen jämförelse mellan korpusar har prövats, och måttet nedan (olika platser per text) har inte räknats.

## Material
- **Korpusar:** svenska, danska och norska runstenar (Rundata, en sten per text); Eddadikterna; islänningasagorna,
  Heimskringla och fornaldarsagorna, var och en delad i prosa (en saga per text) och vers (en strof per text, med
  sagan som kluster). Källor och avgränsning som i `utdata/varlden/README.md`.
- **Platser:** de 23 raderna i `platser.csv` som de ser ut vid låsningen. Regionerna öster och väster ingår i
  huvudmåttet; söder och Nordatlanten redovisas för sig.
- Ortnamnslistan ändras inte efter låsningen. Hittas fler falska träffar, rättas de, och båda resultaten redovisas som
  en avvikelse.

## Mått
- För varje text: **Ö** = antal olika östliga platser som nämns och **V** = antal olika västliga platser. Raderna
  ”Österled (allmänt)” och ”Västerled (allmänt)” räknas som en plats var.
- **Östandel** för en korpus = ΣÖ / Σ(Ö + V) över texterna. Texter utan östlig eller västlig plats bidrar inte.
- **Osäkerhet:** klusterbootstrap med 10 000 dragningar av texter (för vers: av sagor, med alla deras strofer),
  95 %-intervall med percentilmetoden.

## Huvudtest (tre prov, Holm-korrigerade, tvåsidiga, α = 0,05)
1. **Ämnet.** Fornaldarsagor mot islänningasagor, båda prosa. De skrevs på Island under samma tid men handlar om
   olika tider. Test: skillnaden i östandel, permutationstest med 10 000 omflyttningar av korpustillhörigheten
   mellan de 78 sagorna.
2. **Tiden.** Skaldeverserna i Heimskringla mot Snorres prosa i samma sagor. Verserna diktades till stor del omkring
   år 1000, prosan skrevs omkring 1230. Test: skillnaden i östandel, parad klusterbootstrap över de 16 sagorna (vers
   och prosa ur samma saga dras tillsammans). p = andelen dragningar på andra sidan noll × 2. Kräver minst 20
   platsträffar (Σ(Ö + V)) i verserna; annars redovisas provet som ”för få träffar”.
3. **Platsen.** Svenska mot danska och norska runstenar, alla från vikingatiden. Bland stenar som nämner en plats
   utanför Norden: andelen som nämner en östlig plats. Test: Fishers exakta test. Dessutom andelen stenar som nämner
   någon plats utanför Norden alls, med tiden konstant (Mantel–Haenszel över de tre perioderna i `src/nordic.py`).

## Tolkningsregler
- Holm-korrigerat p < 0,05 och 95 %-intervallet utanför noll → ”skillnaden håller”.
- 95 %-intervall helt inom ±15 procentenheter → ”ingen skillnad av betydelse”.
- Annars ”obestämt”.
- Test 3 med färre än 10 danska och norska stenar med en plats redovisas som en antydan oavsett p.

## Robusthet (redovisas, ändrar inte huvudresultatet)
1. Utan raderna ”Österled/Västerled (allmänt)”.
2. Träffar i stället för olika platser (måttet som sågs före låsningen).
3. Utan den största texten i varje korpus, en i taget (lämna-en-ute).
4. Utan Yngvars saga víðförla, som handlar om ett österledståg.
5. Nordatlanten räknad som väster.
6. Islänningasagornas vers mot deras prosa, som test 2.

## Beskrivande (inga test)
- Östandel med intervall för alla korpusar, i ett diagram.
- De vanligaste platserna per korpus, och platser som bara finns i ett källslag (t.ex. Serkland, Vinland).
- En karta per korpus.

## Vad som redovisas oavsett utfall
Alla test ovan med antal texter, Σ(Ö + V), östandel, skillnad, intervall och p (okorrigerat och Holm), robusthetsproven
och en lista över de texter som bär mest av varje skillnad. Förbehåll som ska stå i en artikel: att en plats nämns
betyder inte att någon reste dit; sagorna är litteratur; runstenarna minns främst dem som dog borta;
versavskiljningen är maskinell (följder av korta rader i strofer om åtta) och kan ta med enstaka korta prosarader;
fornaldarsagornas utgåva (1943–44) används bara för räkning.
