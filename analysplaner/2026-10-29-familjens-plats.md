# Analysplan: Familjens plats – var stod stengrupperna, och vad säger de?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-familjens-plats.sha256`.
Kod `utdata/familjens_plats/` (`data.py` bygger tabellen, `analys.R` prövar), resultat `resultat.md` där.

## Bakgrund
Runstenar på sin plats står klumpade på 100–1 000 m (analysplaner/2026-10-28-avstand-mellan-stenar.md med tillägg),
och grannstenar inom 500 m delar personnamn 7,9 gånger oftare än stenar 2–10 km bort (analysplaner/2026-10-29-
grannstenarna.md): grupperna är familjernas platser. Nu: var låg de platserna i landskapet, och vad skiljer stenar i
grupp från stenar som står ensamma? Sett före låsningen: ortnamnslistan ger omkring 8 600 gamla och 20 000 unga
bebyggelsenamn med ändelserna nedan; inga avstånd eller samband med stenarna har räknats.

## Material
Svenska runstenar på sin plats (`moved = 0`, `lost = 0`) med koordinater, alla landskap, korpus 3f58e9339191761e.
- **I grupp:** minst en annan sten på plats 25–500 m bort. **Ensam:** närmaste sten på plats mer än 1 000 m bort.
  Stenar däremellan ingår inte.
- **Kontroller i varje modell:** landskap (faktor), tidsskikt (som r/people.R) och lokal täthet = log(1 + antal
  runstenar, också flyttade, inom 5 km). Logistisk regression (glm); oddskvot för ”i grupp” mot ”ensam”.

## Utfall (en per test)
**Landskapet**
1. Gravfält inom 500 m (Kulturmiljöregistret).
2. Gravhög inom 500 m.
3. Färdväg inom 500 m.
4. Gränsmärke inom 500 m (Kulturmiljöregistret).
5. Medeltida kyrka (före 1350) inom 2 km.
6. **Gammalt bebyggelsenamn** inom 1 km: namn på -sta, -stad, -by, -inge, -inga, -vin, -hem, -lösa, -tuna
   (ortnamnslistan, platstyperna village, hamlet, farm, isolated_dwelling, locality).
7. **Ungt bebyggelsenamn** inom 1 km: -torp, -torpet, -ryd, -hult, -boda.
8. Teoforiskt eller sakralt ortnamn inom 2 km (kultnamnen, nivå A eller B).
9. Centralortsnamn (Husby, -tuna utan gudanamn) inom 5 km.

**Stenen och texten**
10. Texten nämner en plats eller gård (entitetsmodellens platser).
11. Budskapet arv eller gård (`cat_arv` eller `msg_gard`).
12. Hög sten: minst 1,6 m (mätta hela stenar).
13. Signerad (`pm_signatur`).

**Inom grupperna**
14. **Tidsdjup:** grupper (sammanhängande stenar inom 500 m, minst två stildaterade) spänner över fler stilgrupper än
    lika stora slumpvisa urval ur samma landskap. Statistik: medelantalet olika stilgrupper per grupp; 9 999
    omblandningar av stilgrupperna inom landskapet; ensidigt (fler).
15. **Kristet och icke-kristet sida vid sida:** andelen nära par (25–500 m, båda med känd kristen markör) där precis
    den ena stenen har kristen markör (`cat_kristen`), mot omblandning av markören inom landskapet (9 999); tvåsidigt.

## Test och tolkning
Holm över de 15 testen, α = 0,05. **Håller:** Holm-p < 0,05 och samma riktning med p < 0,05 i båda halvorna
(socken för socken som i change.R; för test 14–15 halvorna av grupperna/paren efter samma sockenindelning).
**Antydan:** Holm-p < 0,05 men inte båda halvorna, eller okorrigerat p < 0,05. Annars ingen skillnad påvisad.

## Robusthet (redovisas)
Gränsen för ”ensam” 2 km i stället för 1 km; bara Uppland och Södermanland; avståndsgränserna halverade (250 m,
500 m för namnen, 1 km för kyrkor).

## Förbehåll
Ortnamnen är dagens namn ur OpenStreetMap; ändelserna är en grov datering (gamla namn är i regel förhistoriska, unga
oftast medeltida eller yngre) och en del namn har bytt plats eller form. Gränsmärken och färdvägar är oftast yngre än
stenarna. Medeltida kyrkor är bara de med årtal i Wikidata. Stenar på sin plats är en tredjedel av alla.
