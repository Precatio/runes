# Analysplan: textmodel-24 – en böjningsmodell (stam och ändelse) för ordformer modellen aldrig har sett

Skriven och låst 2026-11-27, innan böjningslagret är byggt eller prövat. Fortsätter sannolikhetsmodellen (`src/runlm.py`,
appens inställning textmodel-19). tm22 (litteraturlexikon) och tm23 (Petersons namn) föll båda. Lärdomen var att det som
saknas är böjning och sammansättning, inte fler uppslagsord (`utdata/runlm_forfining/tm22_resultat.md`).

## Idén (från dechiffreringen)
Modellen känner bara de normaliserade ordformer som finns i träningen. Ett okänt ord blir `<unk>`: det får sannolikhet
från teckenmodellen men ingen identitet, så modellen kan aldrig föreslå en ny böjningsform av ett känt ord. Ett exempel är
Malts *uifrþuR* av *Vífrøðr*, som bara är belagt som *uifrþaR*.

Böjningslagret gör som modellerna för utdöda skriftsystem (stam och ändelse, Snyder m.fl. 2010):
1. **Ändelseväxlingar** lärs ur träningens egna ordformer. För former som modellen redan räknar som samma ord (samma
   lemma) räknas växlingen ändelse → ändelse efter den gemensamma stammen, till exempel -r → -ar och -i → -a. Det ger
   P(ändelse′ | ändelse) med utjämning.
2. **Nya former** skapas för varje känd form w = stam + ändelse som stam + ändelse′ med P(ändelse′ | ändelse) ≥ en tröskel,
   om formen inte redan finns. Stavningsmodellen ger deras runstavningar på samma sätt som för kända former.
3. **Sannolikheten:** P(w′ | föregående ord) = λ_böj · P(w | föregående ord) · P(ändelse′ | ändelse) / Z. Formen ärver
   alltså sitt ords plats i ordföljden. Massan tas från samma pott som `<unk>` och de övriga tilläggen.
4. **Valfritt:** en teckenmodell (Kneser–Ney, ordning 5) över normaliserade former väger in hur rimlig den nya formen är,
   med vikten μ (0 = av).
- **Läckspärr:** ändelseväxlingar och former byggs per veck ur veckets träningsstenar. Provstenarnas egna former får inte
  läcka in.

## Val av inställning (veck 0, innan provet)
- **Rutnät:** λ_böj ∈ {0,003, 0,01, 0,03}, tröskel ∈ {0,02, 0,05} och μ ∈ {0, 0,5}, alltså tolv kombinationer.
- **Körning:** maskeringsprovet med appens flaggor (`APP=…` i `utdata/runlm_forfining/tm23/tm23_kor.sh`) och det nya
  lagret, på veck 0, mot `app_f0`.
- **Valet:** den kombination som ger flest vunna minus förlorade luckor bland huvudmåttets luckor (se nedan), utan nya
  säkra fel (svar ≥ 95 %). Vid lika väljs minsta λ_böj. Om ingen kombination ger fler vunna än förlorade på veck 0 stoppas
  arbetet, och det redovisas som negativt.
- **Valet skrivs och committas** innan veck 1–4 körs.

## Provet (veck 1–4, med den valda inställningen)
- **Huvudmått:** luckor där det rätta ordet inte finns i veckets träningsordförråd, men dess lemma eller stam finns där
  (böjningsluckor). Båda slagen av luckor (inne i ord, helt ord) räknas, och bara runstenar. Vunna och förlorade jämförs
  parvis per lucka mot `app_f1–f4`.
- **Håller** när alla fyra gäller, som i tm23:
  1. fler vunna än förlorade böjningsluckor över veck 1–4;
  2. alla luckor, båda slagen: vunna minus förlorade ≥ 0;
  3. svar ≥ 95 % (tm19:s kalibrering): inte fler fel än i app;
  4. korta luckor (1–2 runor): inte fler nya fel än nya rätt.
- **Därefter dokumenterade luckor:** håller provet körs dok5 (361 luckor) med lagret. Det får inte ge färre än 252 rätt
  eller fler än 2 fel bland svar ≥ 95 %.
- **Först sedan** kan lagret slås på i appen som textmodel-24. Håller provet inte förblir lagret av och redovisas som
  negativt.

## Beskrivande (oavsett utfall)
- Antalet böjningsluckor per veck, och hur många modellen nådde (rätt form bland förslagen).
- **Malt:** läser modellen *uifrþuR* som Vífrøðr med lagret? Bara beskrivande, eftersom Malt inte är provsten.
- Öppna luckor på runstenar (`data/textmodel_candidates.json`): hur många som får en ny böjningsform bland förslagen
  ≥ 0,5. Inget facit, bara antal och exempel.

## Vad som inte får göras
- Ingen inställning väljs på veck 1–4.
- Lagret slås inte på i appen förrän både provet och dok5 har hållit.
- Inga former byggs från provstenar.

## Utdata
- **Kod:** `src/runlm.py` (lagret, av som standard), en flagga i `scripts/runlm_restore_test.py` och tester.
- **Körningar:** `utdata/runlm_forfining/tm24/` med körskript, jämförelseskript, val på veck 0 och `tm24_resultat.md`.
