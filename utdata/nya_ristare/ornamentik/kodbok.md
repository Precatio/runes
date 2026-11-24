# Kodbok: ornamentiken på runstenar (läses från SRI:s planscher)

Version 2, 2026-11-24 (efter piloten med 12 stenar: fältet `upplagg` delat i två, inzoomning obligatorisk). Varje sten kodas av två läsare oberoende av varandra (Anthropics språkmodell Claude, Claude
Opus, som läser planschbilderna). Läsaren ser bara bilderna och stenens signum (för att hitta rätt bild på sidan). Koda
**bara det som syns**. Använd inte kunskap om stenen, ristaren eller litteraturen. Kan du inte se draget säkert: `osäkert`.

**Zooma alltid.** Sidorna är skannade i 300 dpi men visas förminskade. Beskär först stenens bild och sedan varje
rundjurshuvud och varje svans- och bandände i full upplösning (python3 med PIL), och titta på utsnitten innan du kodar
huvud-, flik-, svans- och fotfälten. Ett drag som syns tydligt i ett utsnitt räknas som säkert.

## Fält

1. `bild` – syns stenens ristade yta tillräckligt för att bedöma ornamentiken?
   `god` / `delvis` (fragment, skuggigt, bara en del av ytan) / `ingen` (ingen bild av stenen, eller bara en detalj).
   Vid `ingen` lämnas resten `osäkert`.
2. `djurhuvud` – slutar något runband i ett djurhuvud (huvud sett i profil eller ovanifrån)? `ja` / `nej`.
2b. `antal_djur` – antal rundjur (runband med djurhuvud): `0` / `1` / `2` / `3+`.
3. `huvud_vy` – rundjurets huvud: `profil` / `uppifran` (huvudet sett ovanifrån, som en mask med två ögon) / `inget_huvud`.
4. `oga` – ögats form: `rund` / `mandel` (spetsigt åt ett håll eller båda) / `inget_synligt`.
5. `nackflik` – flik från nacken: `ingen` / `kort` / `lang` (minst halva huvudets längd) / `spiral` (rullar upp sig).
6. `lappflik` – flik från läpparna: `ingen` / `en` (på ena läppen) / `bada` (på båda läpparna) / `spiral`.
7. `mun` – `biter` (biter i bandet, i svansen eller i ett annat djur) / `oppen` / `stangd`.
8. `svans` – hur rundjurets svans slutar: `rak` (avslutas rakt eller tunnas ut) / `spiral` / `ogla` / `kluven` (delar sig) /
   `flatad` (flätas in i eget band) / `ingen_svans`.
9. `fotter` – `inga` / `spiral` / `ogla` / `taer` (tydliga klor eller tår).
10. `huvud_svans` – hur huvud och svans möts: `ataskilda` / `huvudet_biter_svansen` / `sammanflatade` (knutna eller flätade
    ihop) / `bara_ett_slut` (bandet har bara huvud eller bara svans).
11. `kontur` – bandets kantlinjer: `enkel` (bandet är bara en ristad kontur) / `dubbel` (en extra linje innanför kanten) /
    `oklart`.
12. `koppel` – finns en ögla eller ett band (koppel, unionsknut) som binder ihop två djur eller djur och band? `ja` / `nej`.
13. `flatverk` – utöver bandets egen form: `inget` / `enkel_ogla` / `attor` (en eller flera åttor eller korsande öglor) /
    `tat` (tät fläta med många korsningar).
14. `fyrfota` – finns ett fyrfota djur (inte rundjuret)? `ja` / `nej`.
15. `orm_extra` – finns en extra orm eller ett extra band utan runor? `ja` / `nej`.
16. `manniska_mask` – människa eller ansiktsmask? `ja` / `nej`.
17. `kors` – finns ett kors? `ja` / `nej`.
18. `stil` – läsarens bedömning av Gräslunds stilgrupp: `RAK` / `Fp` / `Pr1` / `Pr2` / `Pr3` / `Pr4` / `Pr5` / `KB` /
    `osaker`. (Används bara för att kontrollera läsarna mot Rundata, inte som belägg.)

Varje fält kan också vara `osäkert`. Om stenen har flera ytor: koda den yta som bär det största rundjuret.
