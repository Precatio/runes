# Blindtestets utfall (körning 2026-10-17, en gång)

Protokoll: PROTOKOLL.md, registrerat som commit 16e6f19ca6c6d56a6aaabd69edf5f47c97880a9e (pushad till GitHub före
körningen; dragningens frö är commitens SHA). Rådata: resultat.json, committad orörd.

## Utfall mot de låsta kriterierna

| kriterium | låst gräns | utfall | |
|---|---|---|---|
| rätt ord (riktmärkets regel) | 10–18 av 21 | **16 av 21 (76,2 %)** | INOM |
| rätt ord, strikt lemma | redovisas | 16 av 21 (76,2 %) | samma |
| kalibrering | \|medelpåstående − utfall\| ≤ 0,15 | 0,826 mot 0,762 = 0,064 | OK |
| påståenden ≥ 95 % | varje miss allvarligt fynd | **13 rätt av 13** | inga fynd |

## Dragningen

Fjorton stenar, 21 dokumenterade luckor: U 1043, Ög 229, U 1146 (2), U 734 (2), U 608 (2), Vg 51, U 46 (2), Sö 176,
U 970, U 910 (2), U 935, DR 282 (2), Vs 9, Sm 121 (2). Ingen ersättning behövdes; alla luckor fylldes och redovisas.

## De fem missarna

| sten | hugget | påstod | modellen | utgivarna |
|---|---|---|---|---|
| U 1146 | s-aka | 42 % | spaka | malspaka (sammansättningen missad, huvudledet rätt) |
| U 1146 | suan-bu | 14 % | swens | svanaby (ortnamn) |
| U 734 | lisu-- | 14 % | svæinn | liðsvaldr (sällsynt namn) |
| Sö 176 | bas- | 31 % | basi | bæzt |
| Sm 121 | ---ur | 77 % | faður | moðurbroður (släktordet moðurbroður utanför kandidatlistan) |

Fyra av fem missar bar modellens egen varning (under 45 procent). Den enda halvsäkra missen är Sm 121:s *faður* mot
*moðurbroður*, 77 procent – värd att minnas när släktord fylls i, men inom det kalibreringen lovar på den nivån.

## Läsning

Testet är en stickprovskontroll med liten styrka, som protokollet säger: det kan avslöja grova fel i kedjan eller
systematiskt uppblåsta procentsiffror, inte förfina riktmärket. Det visade inget av det: utfallet ligger mitt i det
låsta intervallet, nära riktmärket 68,7 procent, kalibreringen håller inom toleransen, och samtliga tretton
95-procentspåståenden höll. Det strikta lemmamåttet gav exakt samma 16 rätt – `same_word`-regelns generositet
avgjorde ingenting här.
