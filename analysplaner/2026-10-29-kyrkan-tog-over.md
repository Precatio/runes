# Analysplan: Tog kyrkan över efter gravfältet?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-kyrkan-tog-over.sha256`.
Kod `utdata/familjens_plats/kyrkan.R` (tabell från `kyrkan_data.py`), resultat `utdata/familjens_plats/kyrkan_resultat.md`.

## Bakgrund
Familjernas stengrupper står vid gravfälten (OR 2,4, analysplaner/2026-10-29-familjens-plats.md) och restes inom en
generation (analysplaner/2026-10-29-en-generation.md). Frågan: slutade skedet när begravningarna flyttade till
kyrkogården? Kyrkornas byggår kan inte användas – nästan alla med årtal i Wikidata är från 1200–1300-talen, efter
runstenarna. I stället prövas om stenarna själva visar flytten: senare och kristna stenar står mer sällan vid
gravfälten och oftare vid kyrkan. Sett före låsningen: 1 008 stildaterade svenska runstenar, varav 329 vid en kyrka
enligt Rundata och 576 på sin plats; inga samband har räknats.

## Material och definitioner
Svenska runstenar, korpus 3f58e9339191761e.
- **På sin plats:** `moved = 0`, `lost = 0`, med koordinater. **Gravfält:** registrerat gravfält inom 500 m.
- **Vid kyrkan:** Rundatas plats matchar `kyrka\b|kyrkan\b|kyrkogård|kyrkoruin|ödekyrk` eller placeringen matchar
  `kyrk|vapenhus|\btorn|bogård|stiglucka|koret|sakristi|gravkor|inmurad`; ej försvunnen.
- **Tid:** stilgruppens mitt, t = (år − 1050)/50; tidsskikt som r/people.R. **Kristen:** `cat_kristen`.

## Test (Holm över de fyra, α = 0,05)
1. **Gravfältet över tid:** stildaterade stenar på sin plats; logistisk regression gravfält ~ t + landskap + lokal
   täthet (log(1 + runstenar inom 5 km), som Familjens plats). Förväntat: oddskvot per 50 år under 1.
2. **Kristna stenar och gravfältet:** stenar på sin plats med känd `cat_kristen`; gravfält ~ kristen + tidsskikt +
   landskap + lokal täthet. Förväntat: oddskvot under 1.
3. **Kyrkans stenar är senare:** stildaterade stenar vid kyrkan mot stildaterade stenar på sin plats i **samma
   socken** (bara socknar med båda). Statistik: medelskillnaden i år (kyrka minus fält), vägd per socken med antal
   stenar; 9 999 omblandningar av etiketten kyrka/fält inom socknen; tvåsidigt. Förväntat: kyrkans stenar senare.
4. **Kyrkans stenar är oftare kristna:** stenar vid kyrkan mot stenar på sin plats med känd `cat_kristen`;
   kristen ~ vid kyrkan + tidsskikt + landskap (logistisk). Förväntat: oddskvot över 1.

**Håller:** Holm-p < 0,05 och samma riktning med p < 0,05 i båda halvorna (socken för socken som i change.R).
**Antydan:** Holm-p < 0,05 men inte båda halvorna, eller okorrigerat p < 0,05. Annars ingen skillnad påvisad.
Svarar testen åt motsatt håll mot det förväntade redovisas det som motsatt riktning, inte som stöd.

## Robusthet (redovisas)
Bara Uppland; gravfält inom 250 m (test 1–2); test 3–4 bara med stenar vars *placering* nämner kyrkan (inte bara
platsnamnet); test 3 med stilgrupp som ordnad skala (RAK = 1 … Pr5 = 7) i stället för år.

## Beskrivning (prövas inte)
Stilgruppsfördelningen för stenar inmurade i kyrkan, vid kyrkan i övrigt och på sin plats (ett inmurat fältmonument
bör vara en sten som togs från gravfältet när kyrkan byggdes).

## Förbehåll
Många stenar flyttades till kyrkan långt senare (1600–1900-talen) av samlare och präster, vilket späder ut men inte
gör kyrkans stenar senare – utom om man valde vackra sena stenar. Stenar inmurade på 1100–1200-talen var redan
fältmonument då. Kristen markör kommer av texten och korset och hänger ihop med tid; därför tidsskikt i 2 och 4.
