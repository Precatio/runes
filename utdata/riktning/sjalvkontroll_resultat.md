# Självkontroll av ristningens riktning – resultat

Plan: `analysplaner/2026-11-10-sjalvkontroll-riktning.md` (låst 2026-11-10, SHA-256 `3ef2c79f…`, commit b3133a0).
Kod: `utdata/riktning/sjalvkontroll.py` (först `--klassa`, som skrev `sjalvkontroll_vagklasser.csv` innan någon bäring
räknades). Siffrorna: `sjalvkontroll.json`; stenarna med flyttregler och bäringar: `sjalvkontroll_stenar.csv`.
Körd 2026-11-10. Måttet är medel-cos mellan ristningens riktning och riktningen till vägen (1 = rakt mot vägen, 0 = åt
sidan), mot 9 999 omblandningar; andelen inom 45 grader ska jämföras med 25 procent om riktningen vore slumpvis.

## Prov

| Prov | Stenar | Inom 45° | Medel-cos (väntat) | p | Utfall |
|---|---|---|---|---|---|
| S0 en rad per sten | 120 | 48 % | 0,352 (0,013) | 0,0001 | håller |
| S1 bara gamla vägar inom 500 m | 40 | 28 % | 0,065 (−0,033) | 0,16 | **håller inte** |
| S2 omblandning inom län | 118 | 49 % | 0,364 (0,017) | 0,0001 | håller |
| S3 utan flyttade och omresta | 75 | 45 % | 0,342 (0,003) | 0,0001 | håller |

- **S0.** De fem dubbletterna ändrar inte H2: publicerat 123 poster, 50 % inom 45°, medel-cos 0,366, p 0,0001; en rad
  per sten 120 stenar, 48 %, 0,352, p 0,0001.
- **S1.** Mot de vägar som troligen är gamla (hålvägar, vägbankar, vadställen, kavelbroar och vägar med förhistorisk
  eller medeltida datering i KMR) vetter 28 procent av ristningarna inom 45 grader – nästan precis den fjärdedel som
  slumpen ger. En så stor lutning uppstår av ren slump ungefär en gång på sex. 40 stenar har en sådan väg inom 500 m
  (planens krav: minst 30).
- **S2.** Inom samma län är sambandet lika starkt som inom landskapet; skillnader mellan länens inventeringar bär det inte.
- **S3.** 45 av de 120 stenarna med väg tas bort som flyttade, lagade, återfunna eller återresta (91 av 214 totalt:
  Runor 2020 original = nej 26, Runor 2020 nuvarande läge 22, korpusens flyttregel 0, ordsökningen 66). Kvar 75
  stenar; nästan hälften vetter fortfarande mot vägen.

## Beskrivande (inga krav)

- S1 och S3 tillsammans, inom län: 26 stenar, 27 % inom 45°, medel-cos 0,104 mot 0,046, p 0,30.
- S1 inom 300 m: 26 stenar, 31 %, p 0,21. Inom 1 km: 65 stenar, 22 %, p 0,51.
- S1 utan vägar vars beskrivning nämner runsten: 32 stenar, 25 %, p 0,18. Bara hålvägar och vägbankar: 39 stenar, 28 %, p 0,09.
- Halvorna: S0, S2 och S3 håller i båda (S3: A p 0,001, B p 0,003); S1 i ingen (A p 0,22, B p 0,44).
- 11 av de 40 stenarna i S1 har också en väg i KMR-texten.

## Tolkning enligt planen

S0, S2 och S3 håller, S1 håller inte. Enligt planen gäller fyndet då **vägen i registret och i dag, inte bevisat den
vikingatida**: rapporten och artikeln ska skriva "mot vägen, som vägarna går i dag" och lägga fram vägarnas ålder som en
öppen fråga. Återresningarna (S3) och länens inventering (S2) förklarar inte sambandet.

Förbehåll som inte ändrar utfallet: bäringen i S1 går till en punkt per KMR-lämning, inte till vägens linje, och redan
den publicerade robusthetsraden "bara registrerade färdvägar och vägmärken" (också punkter) var svag (28 % inom 45°,
p 0,020), medan vägarna ur KMR-texten, där inventeraren angav vägens håll från stenen, gav 62 %. S1 kan alltså inte skilja
mellan att de gamla vägarna gick någon annanstans och att punktbäringen är för grov. Invändning (c), vägar som saknas i
både kartor och register, är oprövad.
