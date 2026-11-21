# Väsen som inte är gudar i den fornnordiska litteraturen – resultat

Enligt `analysplaner/2026-11-21-vasen.md` (låst 2076615) och tillägg 1 (c56f36f). Räknat 2026-11-21 med
`utdata/vasen/analys.py` och ordlista v2 (`ordlista_v2.csv`, sha256 7a636ce4…). Alla siffror står i `matt.json`.
Texterna ligger utanför git. Eddan, Snorres Edda, fornaldarsagorna och samtidssagorna är Guðni Jónssons m.fl.
utgåvor och används bara för räkning och korta citat.

## Kvalitetsgrinden
- **Första omgången**, 135 träffar bedömda för hand: viktat 94 % riktiga (krav ≥ 90 %). Riktiga per klass: jättar 15/15,
  dvärgar 15/15, alver 13/15, diser och nornor 14/15, de döda 12/15, odjur 12/15, kristna väsen 14/15. Vättar fick
  10/15 och nattväsen 6/15, så de reviderades (tillägg 1).
- **Efter revisionen** klarade nattväsen 8 av 8. **Vättarna** fick 11 av 15 (73 %) och klarade alltså inte kravet: *vætt*
  är också en viktenhet ("tólf vættir" valfett), och verbet *vætta* (vänta sig) står i vers långt från sitt pronomen.
  **Vättarna redovisas därför bara som antal och ingår inte i testerna.**
- **Kvarvarande kända fel**: kenningar (*draugr*, *álfr* för krigare eller man, *Munins* för korp), *dís* för en kvinna,
  *Fáfnisbana* som Sigurds tillnamn och *djöful* som skällsord. Verserna består till stor del av kenningar, så de har
  fler sådana fel än prosan.
- **Kodrättelse** (tillägg 1): Snorres Edda räknades först också bland eddadikterna. Det är rättat.

## V2 Täthet: väsen per 10 000 ord (95 % intervall, bootstrap över texterna)
- Snorres Edda, Gylfaginning: **121** (en text)
- Snorres Edda, Skáldskaparmál: **88** (en text)
- Eddadikterna (34): **79** (46–123)
- Fornaldarsagornas vers: 28 (17–44)
- Islänningasagornas vers: 24 (19–29)
- Heimskringlas vers: 21 (11–41)
- **Fornaldarsagornas prosa (36): 12,0** (8,9–15,3)
- **Islänningasagornas prosa (42): 2,2** (1,4–3,5)
- Samtidssagornas prosa (6): 1,7 (0,5–4,1)
- **Heimskringlas prosa (16): 0,9** (0,3–2,0)
- Svenska runstenar (2 321): 2 träffar, båda falska (se V4) → **0**

## V1 Vilka väsen (antal träffar; de vanligaste termerna)
- **Eddadikterna**: jättar 216 (namngivna jättar 94, *jötunn* 91, *þurs* 19), odjur 73 (namngivna), diser och nornor 40
  (*norn* 13, *valkyrja* 12, *dís* 11), dvärgar 35, vättar 8, nattväsen 3, de döda 2.
- **Gylfaginning**: jättar 149 (namngivna 90), odjur 45, diser och nornor 12, dvärgar 10, alver 1.
- **Skáldskaparmál**: jättar 114, odjur 38, dvärgar 20, diser och nornor 10, kristna väsen 5 (änglar i Kristuskenningar).
- **Fornaldarsagorna (prosa)**: jättar 252 (*tröll* 119, *jötunn* 67, *risi* 30, *flagð* 16), odjur 74 (namngivna 58, mest
  Fáfnir), dvärgar 25, vättar 18, kristna väsen 15 (*engill* 8), diser och nornor 14, alver 8, de döda 4.
- **Islänningasagorna (prosa)**: jättar 136 (*tröll* 81, *þurs* 17, *jötunn* 14, *risi* 8, *flagð* 8), vättar 24,
  diser och nornor 16 (*fylgja* 13), kristna väsen 7, odjur 5, de döda 4, alver 2, nattväsen 1. **Inga dvärgar.**
- **Heimskringla (prosa)**: jättar 11 (*tröll* 6), vättar 3 (landvättarna), dvärgar 2, diser 2, alv 1, draug 1, mara 1
  (Vanlandi i Ynglinga saga).
- **Samtidssagorna (prosa)**: tröll 3, djöfull 3, vættr 1, fylgja 1.

**Mönstret**: *tröll* är sagornas vanligaste väsensord, i både fornaldarsagorna och islänningasagorna. Myten
(Eddan och Snorre) domineras i stället av namngivna jättar och odjur. Dvärgarna finns i myten och fornaldarsagorna, men
inte en enda gång i islänningasagornas prosa. Fylgjor är islänningasagornas tredje vanligaste väsensord (13), men
per ord lika vanliga i fornaldarsagorna (6 på en tredjedel så mycket text).

## V3 Vers mot prosa
I samma sagor är versen 10–25 gånger tätare än prosan (islänningasagor 24 mot 2,2, Heimskringla 21 mot 0,9,
fornaldarsagor 28 mot 12). En del av skillnaden är kenningarna: versen nämner väsen som bilder för annat.

## V4 Runstenarna
De två träffarna är falska. *draugr* på Karlevistenen (Öl 1) står i en kenning för krigare ("Þrúðar draugr"), och
*risinn* på U 703 betyder rest. **De svenska runstenarnas texter nämner alltså inga väsen ur ordlistan.** Väsen på
runstenar finns i bilderna, till exempel Fáfnir på Ramsundsberget (Sö 101), men bilderna står inte i Rundatas text.

## V5 Tätast (minst 2 000 ord)
Gylfaginning 121, Skáldskaparmál 88, Norna-Gests þáttr 44, Egils saga einhenda ok Ásmundar berserkjabana 39, Ólav
Tryggvasons saga (vers) 34, Illuga saga Gríðarfóstra 32, Ketils saga hængs 31, Bárðar saga Snæfellsáss 31 (den enda
islänningasagan i toppen), Kormáks saga (vers) 30, Gríms saga loðinkinna 29.

## Testerna (Holm över T1–T3; p från bootstrap, 10 000 dragningar)
- **T1 genre: håller.** Fornaldarsagorna nämner väsen **5,9 gånger så ofta** som islänningasagorna (11,5 mot 2,0 per
  10 000 ord, vättarna borträknade; 95 % 3,4–10,2; p < 0,0001). Utan termen *tröll*: 7,8 (4,3–15,1). Utan den största
  sagan: 5,5 (3,1–10,1).
- **T2 de dödas andel: håller inte.** 2,3 % av väsensträffarna i islänningasagorna mot 1,0 % i fornaldarsagorna
  (skillnad +1,3 procentenheter, −2,6 till +6,3; p 0,83). Med bara 4 + 4 träffar går det inte att avgöra.
  **Begränsning:** ordlistan räknar substantiv. Islänningasagornas gengångare beskrivs ofta med verbfrasen "gekk aftur"
  (Glámr i Grettis saga), som inte räknas eftersom *ganga aftur* också betyder att gå tillbaka. De döda är därför
  underskattade, sannolikt mest i islänningasagorna.
- **T3 samtiden: obestämt.** Samtidssagorna har 7 träffar (krav ≥ 20). Beskrivande: 1,7 per 10 000 ord, i nivå med
  islänningasagorna, och hälften är djävulen.

## Vad det betyder och inte betyder
- Väsen hör till myten och till fornaldarsagornas forntid. Islänningasagornas Island har nästan inga väsen, bara troll,
  vättar och fylgjor då och då. Heimskringlas kungar har ännu färre. Skillnaden mellan fornaldarsagor och
  islänningasagor är ungefär sexfaldig, och den håller i alla kontroller.
- Antal ord är inte tro. Att en saga nämner troll visar vad berättaren valde att berätta på 1200–1300-talet, inte vad
  någon på 900-talet trodde.
- Islänningasagornas stavning är nutida (sagadb.org). Ordlistan täcker både den och den fornisländska.
