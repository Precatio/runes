# Analysplan: Spårläsaren blind – hjälper skannerspåren när parningen inte ser svaret?

Skriven och låst 2026-11-06, innan något facit med Runa för runa finns och innan något av provet är kört. Viktor
2026-11-06: "kan du börja utan mig?" om Runa för runa, facit för runigenkänningen och det blinda provet av spårläsaren. Kod: `scripts/sparlasare_blind.py` (stubbe; vägrar köra
med färre än åtta facit, se nedan). Resultat i `utdata/sparlasare/blind/`.

## Bakgrund
Rapporten *Skanningen som ledtråd* (spårläsaren, led F i `utdata/sparlasare`): på 157 maskerade helord på 17 skannade
stenar lyfte skannerspåren andelen rätt ord från 53,5 till 59,9 procent (parat Wilcoxon på P(facit), p = 3,7e-6), och
slumpvis omflyttade spår gav ingen vinst. Svagheten, redovisad i rapportens version 3: de upptäckta runorna paras med
textens positioner med dynamisk programmering (`_gap_align` i `src/trace_reader.py`, `align_pos` i led F) över hela
texten, också det maskerade ordet. Parningen belönar alltså lägen där spårmängden innehåller den sanna runan, och
provet läcker. Med Runa för runa (`src/rune_links.py`, METHODS 2c) kopplar en människa varje klick till en bestämd runa
i translittereringen. Paras skanningens runor med texten genom de klicken i stället, ser parningen aldrig spårens
mängder, och läckan försvinner.

## Vad som är känt före låsningen
Led F:s resultat ovan och dess filer (`led_f_*.json`, `led_f_summering.json`). Att Rundatas ord bara går att jämföra
på stenar där translittereringens ord täcker texten (led F:s `gold`); bland skanningarna i `skanningar/` gäller det
Sö 112, 113, 128, 129, 131, 134, 143, 149, 160, 163, 165, 184, 319, 52, 75, Fv1948;282 och Fv1973;189, men inte
Sö 137, 161, 207, 211 och 367 (förlorade eller osäkra runor). Inga facit med Runa för runa finns; inget av provet är
kört.

## 1. Fråga
Ger skannerspåren fortfarande fler rätt ifyllda dolda ord när skanningens runor paras med texten genom forskarens
klick i stället för genom en parning som ser svaret? Ja: villkoren i punkt 3 håller. Nej: de håller inte trots minst
50 ord med spår.

## 2. Underlag
* **Facit:** filer av version 2 i `utdata/facit/` (`type: vitki-rune-facit`, `rune_links` ej tom), gjorda i facit-läget
  av en människa. Ett facit per sten; finns flera används det med tidigast `created`.
* **Stenar:** vikingatida runstenar vars facit inte är utvecklingsstenarna Sö 113 och Sö 128 (reglerna och spårläsarens
  parametrar justerades på dem; de redovisas för sig, som i led F) och som klarar led F:s `gold` (punkten ovan).
* **Minst åtta sådana stenar.** Med färre körs inget (skriptet vägrar). Rundata 2014 (RUNDATA.xls uppdaterad 2018).
* **Skanningen** hittas genom facitets filnamn och kontrolleras mot dess SHA-256; den läses in centrerad som i appen.

## 3. Primärt mått och test
**Design som led F.** Varje helt ord på 2–6 runor maskeras i tur och ordning, och modellen – tränad utan stenen
(`Model(..., aligned=True, lam_name=0.05)`, Edda-ord som i led F) – fyller i det med `restore(window=2, n_cands=60)`
under tre villkor: **utan** spår, med **skanner**ns spårmängder (mjuka, `trace_eps = 0,2`) och med samma mängder
**omflyttade** slumpvis mellan stenens parade positioner (seed 23, som i led F).

**Parningen (det enda som ändras).** Analysen körs om med facitets normal och uppåtriktning, rutnät 0,6 mm,
`keep_arrays=True` och skanningens SHA-256 (som appen, så att de ritade slingorna används). Spårläsarens blobbar,
mallar och marginalmängder är oförändrade (`weighted_blobs`, `rune_probs`, `margin_set`: TAU 0,25, PRIOR 0,08,
EPS 0,10, MARGIN 0,75). Varje upptäckt runa får en mittpunkt i stenytans plan (medel av strecken ändpunkter), och varje
klick sin punkt i samma plan (`point_mm`, annars `image_xy` genom analysens `image_frame`). Klick och upptäckt runa
paras när de är varandras närmaste och avståndet är högst 1,5 gånger mediandistansen mellan två på varandra följande
klick (samma räckvidd som Markera runorna i appen). Bara klick som gäller en runa används; bindrunor (två runor, ett
klick) får inga spår, liksom överhoppade runor. Positionen i texten är tokenens `pos` (textmodellens text, densamma
som led F:s på stenar som klarar `gold`). Ingenting i parningen ser texten eller spårmängderna.

**Primärt mått:** per maskerat ord med minst en spårad position, P(facit) under skanner minus P(facit) utan.
**Test:** ensidigt Wilcoxon-teckenrangtest på de skillnader som inte är noll (skanner > utan), alla ord på
facitstenarna samlade.

**Beslutsregel. Spåren hjälper blint om alla tre gäller:**
1. skanner > utan: p < 0,05 (ensidigt Wilcoxon, P(facit));
2. skanner > omflyttad: p < 0,05 (ensidigt Wilcoxon, P(facit)) – spåren hjälper för att de läser stenen, inte för att
   mängderna krymper sökrymden;
3. andelen rätt ord (samma lemma som Rundatas normalisering, `word_ok`) är högre med skanner än utan.

**Underlag för ett nej:** minst 50 maskerade ord med spår. Med färre redovisas provet som *ej avgörbart* (för få ord),
inte som ett nej. Håller 1 men inte 2, redovisas det som att mängderna hjälper utan att läsa stenen.

## 4. Nollmodeller och kontroller
* Villkoret *omflyttad* (ovan) är provets egen nollmodell.
* Omflyttad mot utan, tvåsidigt Wilcoxon: beskrivande; ska inte vara signifikant.
* Parningens kvalitet per sten, beskrivande: andel klick som fick en upptäckt runa, och hur ofta den sanna runan ligger
  i den parade runans marginalmängd, mot 20 omkastade texter (som led F:s `coverage`/`null`). Den används inte för
  att välja stenar.
* Jämförelse med led F på samma stenar och ord: samma tre villkor med DP-parningen, beskrivande (hur stor del av
  led F:s vinst som var läcka).
* Artefakter: refränger och formler (ett vanligt ord fylls rätt utan spår, då ändras P(facit) lite – ingen fördel åt
  något villkor); Rundatas stavning (gäller alla villkor lika); bergart och vittring (redovisas per bergart).

## 5. Känslighet
Körs och redovisas bredvid, ändrar inte beslutet:
* räckvidd 1,0 i stället för 1,5 gånger klickavståndet;
* bara ord där alla positioner har spår;
* per sten: andel stenar där medelskillnaden skanner − utan är positiv (teckentest);
* utan klick på osäkra runor (inom parentes i Rundata).

## 6. Vad som INTE får göras
Spårläsarens parametrar (TAU, PRIOR, EPS, MARGIN, TRACE_EPS), runigenkänningens regler (fingeravtrycket
`RULES_SHA256` i `scripts/evaluate_rune_detection.py`), modellens inställningar, räckvidden 1,5, ordlängderna 2–6 och
gränserna 0,05 och 50 ord ändras inte efter körningen. Inga facit läggs till eller tas bort efter att resultatet
setts; facitstenarnas ritade slingor ritas inte om. Ingen egen läsning av inskrifterna: facit kopplar klick till
Rundatas translitterering, och det ifyllda ordet bedöms mot Rundatas normalisering.

## 7. Redovisning
`utdata/sparlasare/blind/` (`resultat.json`, `resultat.md`), och i rapporten *Skanningen som ledtråd* som en ny
version med ändringslogg – också om svaret blir nej eller ej avgörbart. METHODS 2c (Runa för runa) och spårläsarens
avsnitt får en mening om utfallet.
