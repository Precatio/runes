# Resultat: Vitkis säkraste ristarförslag för runstenar utan ristare

Enligt `analysplan_forslag.md` (låst 2026-10-21, SHA-256 `5ed0b2f3b147aad4be11b9c377ceb5502b7daf92de01f0bcaa9fba8cc9ab14c7`).
Korpusversion 5fdfd1e095bfb6fb, Samnordisk runtextdatabas 3.1, bara runstenar. Siffrorna kommer ur `blindprov.json`
(`blindprov.py`) och `nya_forslag.json` (`forslagslista.py`); `kontroll.py` räknar om 60 slumpvis valda stenar på ett
oberoende sätt (djupkopia av korpusen utan stenens ristare och ett nybyggt sammanhang) och fick exakt samma status,
förslag och styrka för alla 60.

## 1. Svaret på frågan: ja

I blindprovet hade *nytt förslag* rätt klart oftare än regeln *närmaste ristare* på samma stenar:

| Urval | Stenar | Vitki rätt | Närmaste ristare rätt | Bara Vitki | Bara regeln | McNemar p |
|---|---|---|---|---|---|---|
| Nytt förslag | 302 | 248 (82 %, 77–86) | 133 (44 %, 39–50) | 132 | 17 | 3,1 · 10⁻²³ |
| Nytt förslag, signerade | 100 | 72 (72 %, 63–80) | 42 (42 %) | 38 | 8 | 9,2 · 10⁻⁶ |
| Nytt förslag, modellen ger ett namn | 254 | 213 (84 %) | 116 (46 %) | 110 | 13 | 2,6 · 10⁻²⁰ |
| Nytt förslag, kanske någon annan | 48 | 35 (73 %) | 17 (35 %) | 22 | 4 | 0,0005 |
| Nytt förslag, utan modell | 0 | – | – | – | – | – |
| Möjligt förslag | 195 | 108 (55 %, 48–62) | 66 (34 %) | 71 | 29 | 3,2 · 10⁻⁵ |

Intervallen är Wilsons 95 %. Status för de 769 stenarna med säker ristare: 302 nytt förslag, 195 möjligt, 272 inget.
636 har en ristare som Vitki kan föreslå (28 ristare: modellens 18 och ortografins 27); 133 har det inte, och 23 av dem
fick ändå ett nytt förslag (fel med nödvändighet, medräknade ovan).

Efter styrka (nytt förslag): 0,5–0,6: 50 av 72 (69 %); 0,6–0,7: 56 av 65 (86 %); ≥ 0,7: 142 av 165 (86 %).

## 2. Utöver planen (beskrivande)

* Per landskap: Uppland 227 av 270 (84 %) mot 117 (43 %) för regeln, p = 1,2 · 10⁻²³; Södermanland 17 av 28 (61 %)
  mot 13 (46 %), p = 0,39 – ingen säker skillnad; Gästrikland 3 av 3; Västmanland 1 av 1.
* Per föreslagen ristare (nytt förslag): Öpir 1 68 av 104 (65 %, lägst bland ristare med fler än tre förslag),
  Åsmund 37 av 39, Balle 34 av 37, Fot 2 30 av 35, Gunnar 21 av 22, Traen 11 av 15, Erik 14 av 14, Livsten 10 av 10.
  De fyra Traen-missarna (Sö 46, Sö 159, Sö 160, Sö 296) är alla signerade av andra ristare i Södermanland.

## 3. Externt prov mot Runor 2020

19 runstenar har en namngiven ristare i Runor 2020 men ingen i Rundata 3.1; åtta av dem har en ristare som Vitki kan
föreslå. Ingen fick nytt förslag; tre fick möjligt förslag, och ett stämde (U 494, Åsmund). För litet för slutsatser,
som planen väntade.

## 4. Förslagen för stenar utan ristare

Av 1 550 runstenar utan ristare i Rundata får 86 nytt förslag, 292 möjligt och 1 172 inget. Av de 86: Öpir 1 30, Fot 2
18, Traen 15, Balle 14, Halvdan 3, Gunnar 2, Arbjörn 2, Visäte 1, Amunde 1; Uppland 65, Södermanland 20, Västmanland 1;
18 försvunna stenar; modellen säger *kanske någon annan* om 17.

De tio starkaste där modellen inte säger *kanske någon annan* (U 854 och U 957, styrka 0,76, hoppas över):

| | Sten | Förslag | Styrka | Modell | Ortografi | Kontroller (område, stil, språkdrag, bergart; ✓ klarar, – kan inte prövas) | Runor 2020 |
|---|---|---|---|---|---|---|---|
| 1 | Sö 62 Hässlö | Traen | 0,88 | 0,52 | 0,75 | ✓ ✓ – – | ingen ristare |
| 2 | Sö 158 Österberga | Traen | 0,87 | 0,68 | 0,58 | ✓ ✓ – – | nämner Traen: "Tidigare tolkad som signerad av Traen" (Fv 1981:196) |
| 3 | U 1026 Lena kyrka | Öpir 1 | 0,85 | 0,85 | – | ✓ ✓ – – | samma ristare som U 1027 |
| 4 | U 843 Hässle (försvunnen) | Fot 2 | 0,84 | 0,72 | 0,45 | ✓ – – – | ingen ristare |
| 5 | Sö 72 Kesäter (försvunnen) | Traen | 0,83 | – | 0,83 | ✓ ✓ – – | ingen ristare |
| 6 | U 482 Kasby | Fot 2 | 0,82 | 0,67 | 0,45 | ✓ – – – | ingen ristare |
| 7 | Sö 70 Hedenlunda | Traen | 0,79 | 0,49 | 0,58 | ✓ – – – | ingen ristare |
| 8 | Sö 137 Aspa | Traen | 0,79 | 0,41 | 0,63 | ✓ ✓ – – | ingen ristare |
| 9 | U 136 Broby | Fot 2 | 0,78 | 0,39 | 0,64 | ✓ – – – | samma ristare som U 135 |
| 10 | Sö 335 Ärja ödekyrka | Traen | 0,75 | 0,40 | 0,58 | ✓ ✓ – – | ingen ristare |

Avstämningen mot Runor 2020 och Wikidata för alla 86: 75 saknas, 9 "samma som", 1 nämns (Sö 158), 1 finns redan
(U 1015, Öpir 1 – samma som Vitkis förslag), ingen annan ristare. I de tre par där Runor anger samma (namnlösa) ristare
och båda stenarna får nytt förslag ger Vitki samma namn: U 1026/U 1027 (Öpir 1), U 135/U 136 (Fot 2), U 297/U Fv1979;245
(Fot 2).

Att märka för de fem: Sö 158:s granne Sö 159 (Österberga, 1 km, signerad av Gunnlev 1, Rörik och Gudmund) fick i
blindprovet Traen – Vitki kan inte skilja Traen-gruppen från dem. Sö 72 vilar på ortografin ensam (stenen står mer än
25 km från modellens träningsstenar; närmaste Traen-sten 46 km bort), en sorts förslag som blindprovet inte prövade.

## 5. Avvikelser från planen

1. **Korpusversion.** Planen anger 5ebd6df1627127fd. Där kortade `r/attribution.R` listan över modellens förslag till
   de 400 första, så att stenar utan ristare längre ned saknade modellvärde. Felet rättades efter den första körningen
   av blindprovet (ny korpusversion 5fdfd1e095bfb6fb, i övrigt identisk; de 400 första förslagen oförändrade).
   Första körningen: nytt förslag 247 av 300 (82 %), närmaste ristare 122 (41 %, strikt regel), p = 3,6 · 10⁻²⁶;
   sex stenar med nytt förslag utan modellvärde, 4 av 6 rätt. Stenöversiktens antal ändrades från 79/254 till 86/292
   nya/möjliga förslag.
2. **Regeln närmaste ristare** gjordes generös efter den första körningen: står flera stenar med säker ristare på exakt
   samma avstånd (ofta samma kyrka) räknas alla deras ristare. Det höjde regelns träff från 41 till 44 % och gör
   jämförelsen svårare för Vitki.
3. **Urvalet i artikeln.** Planen säger att de tio starkaste visas med alla belägg. På Viktors begäran visas de fem
   starkaste i detalj och de fem följande i en tabell med modell, ortografi och Runor; alla belägg finns i
   `nya_forslag.json` och i appen.
4. Träffsäkerheten per landskap och per föreslagen ristare (avsnitt 2) är tillägg utöver planen.

## 6. Redovisning

Artikeln "Fem runstenar söker sin ristare" (`utdata/blogg/build/build_forslag.py`, slug `fem-runstenar-soker-sin-ristare`),
METHODS.md 14c och skärmbilderna i `utdata/blogg/forslag/` (`forslag_bilder.py`).
