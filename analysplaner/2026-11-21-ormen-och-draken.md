# Analysplan: ormen och draken – fördjupning 5 i serien "Nordiska väsen under vikingatiden"

Skriven och låst 2026-11-21, innan något nedan har räknats per textgrupp eller betydelse. Viktor 2026-11-21: "kör vidare
på ormen och draken. Se också om vi kan hitta hur den kom in i det nordiska."

## Känt före låsningen
- **Antal:** för att välja metod räknades bara totalerna. Formerna av *dreki* gav 278 träffar och formerna av *ormr*
  (liten bokstav, också *linormr*) 134 träffar i hela korpusen. Inget är uppdelat efter textgrupp eller betydelse.
- **Allmänt känt, inte mätt här:**
  - *dreki* är ett lånord från latinets *draco* (via fornengelskan och fornsaxiskan), medan *ormr* och *linnormr* är
    inhemska ord;
  - *dreki* betyder i kungasagorna ofta ett skepp med drakhuvud;
  - Fáfnir kallas *ormr* i eddadikterna.

  Det sista är skälet till T1. Hur ofta det gäller är inte räknat.
- **Den första väsenstudien** räknade inte *dreki* och *ormr*, bara namngivna odjur (Fáfnir, Midgårdsormen, Nidhögg,
  med flera).

## Träffarna och handklassningen
- **Mönster** (skiftlägeskänsliga, liten bokstav):
  - `\bdrek(?:i|a|ar|um|inn|ann|ans|anum|arnir|ana|anna|unum)\b` och `\bdrekahöf\w*`;
  - `\b(?:lin)?orm(?:r|ur|s|i|inn|ar|a|um|arnir|ana|anna|unum|inum|sins)\b`.
- **Alla träffar klassas för hand** i sammanhanget (± 90 tecken, mer vid behov) i en av klasserna:
  - *drake* – det mytiska odjuret, också en orm av drakens slag som Fáfnir och Midgårdsormen;
  - *orm* – ormen som vanligt djur;
  - *skepp* – ett skepp eller dess drakhuvud;
  - *bild* – en drake som märke, fana eller utsmyckning;
  - *kenning* – en skaldisk omskrivning där ordet står för något annat (till exempel guld, svärd eller skepp i en
    kenning);
  - *annat* – allt annat.
- **Klassningen** görs med Anthropics språkmodell Claude (Claude Opus).
- **Oberoende kontroll:** 50 träffar, stratifierade efter ord och textgrupp (seed 20261121), klassas blint av en
  separat instans av samma modell. Krav: ≥ 85 % överensstämmelse, och oenigheterna redovisas. Under 85 % betyder att
  gränsfallsreglerna skrivs ned och klassningen görs om, i ett låst tillägg.

## Grupper
- **Eddadikterna** (34 dikter).
- **Prosan** = Snorres Edda, alla sagors prosa (fornaldarsagor, islänningasagor, Heimskringla, samtidssagor).
- **Sagornas vers** redovisas för sig och ingår inte i T1.

## Test T1 – tar lånordet över? (låst)
- **Måttet:** bland träffarna i klassen *drake* är det andelen som är ordet *dreki* (resten är *ormr*). Eddadikterna
  jämförs med prosan.
- **Utfall:** skillnad i procentenheter med 95 % intervall (bootstrap över texterna, 10 000 dragningar, seed
  20261121), tvåsidigt p. Testet håller om p < 0,05 och intervallet inte täcker 0.
- **Minsta underlag:** ≥ 10 draketräffar i vardera gruppen, fördelade på ≥ 3 texter. Annars obestämt.
- **Känslighet** (utan egen slutsats):
  - bara Fáfnirsberättelsen: eddadikterna Reginsmál, Fáfnismál och Sigrdrífumál mot prosans Völsunga saga, Norna-Gests
    þáttr och Snorres Edda;
  - utan Snorres Edda i prosan.

## Mått (beskrivande)
- **O1:** klasserna per textgrupp och ord. Det visar hur ofta *dreki* är ett skepp, en drake eller en bild i varje slags
  text.
- **O2:** de namngivna ormarna och drakarna (Fáfnir, Miðgarðsormr, Jörmungandr, Níðhöggr, Góinn, Móinn) per textgrupp.
- **O3:** runstenarna:
  - ord för drake eller orm i texterna (Rundatas västnordiska normalisering, samma mönster);
  - ormslingan, alltså andelen stenar med ormhuvud (stilgrupp Fp eller Pr1–Pr5) bland stenar med säker stilgrupp, per
    landskap.

  **Förbehåll:** stilgruppen definieras av ormslingan själv, så måttet säger var ormstenarna står, inte när de kom.
- **O4:** Ramsundsberget och andra stenar med Sigurdsbilden (Rundata *other* och litteraturen), som exempel.

## Vad som redovisas
Allt ovan, oavsett utfall, i `utdata/draken/resultat.md`. Varifrån draken kom till Norden besvaras inte av räkningen.
Lånordet och bildernas historia redovisas ur litteraturen och skiljs tydligt från det vi har mätt. Korta citat med
källa. Texter och klassning med utdrag stannar utanför git.
