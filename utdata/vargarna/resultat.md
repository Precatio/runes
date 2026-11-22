# Vargarna – resultat

Fördjupning 7 i serien Fornnordiska väsen. Låst plan: `analysplaner/2026-11-22-vargarna.md` (sha256 ea7c37c0…, commit 6e4e192).
Skript: `utdata/vargarna/analys.py`. Siffror: `matt.json`. Blind kontroll: `kontroll_resultat.json`.
Texterna och klassningen med utdrag ligger utanför git (`data/cache/vargarna/`).

## Träffarna och klassningen
- **158 vargträffar** (mönstret i planen): dikten 76, prosan 56, Snorres Edda 26.
- Alla klassade för hand med Anthropics språkmodell Claude (Claude Opus).
- **Blind kontroll:** 40 stratifierade träffar klassades av en separat instans av samma modell utan att se den första klassningen.
  **34 av 40 lika (85,0 %)**. Kravet var ≥ 85 % och nås precis. De sex oenigheterna gällde gränsfall:
  - tre i skaldevers mellan *kenning*, *fredlös* och *djur* (”varga myrðir”, ”óþyrmir varga”, ”meinrennir … varga”);
  - fredlösformeln ”sem menn víðast varga reka” (vi: *djur*, eftersom ordet där betyder de jagade djuren; kontrollen: *fredlös*);
  - Hávamáls ordspråk ”sjaldan liggjandi ulfr lær of getr” (vi: *djur*; kontrollen: *annat*);
  - ett vargheiti i Skáldskaparmál (vi: *annat*; kontrollen: *djur*).
- **Utforskande, inte låst:** med kontrollens klass på de sex blir T1 16,9 mot 6,7 % (skillnad 10,3 pe, intervall −9,1 till 24,1,
  p = 0,26). Slutsatsen ändras inte.

## V1 – vad vargen är i de olika texterna
| Grupp | n | djur | myt | förvandling | fredlös | kenning | annat |
|---|---|---|---|---|---|---|---|
| Dikten (eddadikter + all skaldevers) | 76 | 47 (62 %) | 12 (16 %) | 2 (3 %) | 5 (7 %) | 5 (7 %) | 5 (7 %) |
| Prosan (sagorna) | 56 | 15 (27 %) | 1 (2 %) | 28 (50 %) | 3 (5 %) | 0 | 9 (16 %) |
| Snorres Edda | 26 | 8 (31 %) | 14 (54 %) | 0 | 0 | 2 (8 %) | 2 (8 %) |

- **I dikten är vargen ett djur på slagfältet**, oftast som den som äter de fallna.
- **I sagornas prosa är vargen oftast en dröm:** hälften av träffarna är vargar som står för människor – vargfylgjor i drömmar
  (Njála, Gísla, Harðar, Hávarðar, Heiðarvíga, Þórðar saga hreðu, Hrólfs saga Gautrekssonar, Hrómundar, Hálfdanar Brönufóstra,
  Þorsteins saga Víkingssonar) och Völsunga sagas ylgr som var Siggeirs mor i vargskepnad.
- **Täthet per 10 000 ord** (djur + myt + förvandling): Heimskringlas vers 10,5; islänningasagornas vers 6,2; Gylfaginning 6,7;
  eddadikterna 5,4; Skáldskaparmál 4,6; fornaldarsagornas vers 2,5; fornaldarsagornas prosa 0,50; Heimskringlas prosa 0,29;
  islänningasagornas prosa 0,23; samtidssagorna 0. Vargen är ett versord.

## V2 – de namngivna vargarna
- Eddadikterna: Garmr 5, Fenrir/Fenris/Fenrisúlfr 8, Hati 4 (Hati/Hata), Geri/Gera 3, Freka 2 (den ena är jarlen i en vers i Gautreks saga), Sköll 1.
  ”Dikten” räknar här också skaldeversen i sagorna.
- Snorres Edda: Fenrisúlfr med former 11, Garmr 2, Geri/Gera 3, Freki/Freka 3, Hati 1 (+ ”Skoll” utan accent, som mönstret missar).
- **Sagornas prosa: i praktiken inga.** De 37 träffarna på Gera/Geri i prosan är verbet *gera/geri* (”göra”), och Freka är en jarl
  i Gautreks saga. Mönstret är alltså oprecist utanför Eddan; vi läste varje träff.
- Skaldeversen i sagorna har Fenrir i omskrivningar (”Fenris varra”, ”hjálm-Fenrir”) och en gång själv: Eyvindr skáldaspillirs
  Hákonarmál i Heimskringla, ”Mun úbundinn á ýta sjöt Fenrisúlfr fara …”.

## V3 – berserkarna och ulfhednarna
- Ord på *berserk-* / *ulfheð-*, per 10 000 ord: **fornaldarsagorna 3,92** (134 träffar; Hrólfs saga kraka 40, Hrólfs saga
  Gautrekssonar 17, Göngu-Hrólfs saga 12, Hervarar saga 12, Egils saga einhenda 11); **islänningasagorna 1,25** (110; Heiðarvíga 28,
  Eyrbyggja 22, Grettis 17); Heimskringla 0,33 (8); eddadikterna 0,63 (3); samtidssagorna 0,21 (1).
- **Ulfhednarna:** mönstret `[uú]lfheð` fångar inte accentformen *úlfhéðnar*, så V3 är i praktiken bärsärkarna. En utforskande
  sökning `[uúUÚ]lfh[eé]ð\w*` (inte låst) ger 19 träffar, varav 16 är personnamnet Úlfheðinn (bl.a. tio i Vatnsdæla saga och
  runstenen Sö 307, ”Ulfheðinn ok … reistu stein þenna at Þorstein, fôður sinn”). **Ordet för krigarna står bara tre gånger, och
  alla tre gäller slaget i Hafrsfjord:** Vatnsdæla saga (”þeir berserkir er úlfhéðnar voru kallaðir. Þeir höfðu vargstakka fyrir
  brynjur”), Grettis saga (”Þeir voru kallaðir úlfhéðnar en á þá bitu engi járn”) och Torbjörn hornklofes dikt i Haralds saga
  hárfagra (”Grenjuðu berserkir, … emjuðu úlfhéðnar”).
- Vargskinnet i övrigt: Völsunga sagas *úlfahamir* (Sigmundr och Sinfjötli) och tillnamnet *Heiðrekr úlfhamr* (Hervarar saga,
  Sörla þáttr, Þorsteins þáttr bæjarmagns).

## V4 – runstenarna
- **Ordet för varg i runstenstexterna:** två träffar, båda namnfragment (”…ulfr” på Öl Köping 40 och U 324). Runstenarna
  talar aldrig om vargen som djur.
- **Vargnamnen** (ur björnstudien): 189 av 2 321 runstenar har ett namn med varg (Ulfr, -ulfr). Uppland 109 (9,3 %),
  Södermanland 43 (11,8 %), Västergötland 9 (6,9 %), Småland 6 (5,0 %), Östergötland 10 (4,5 %), Öland 3 (1,9 %). Beskrivande.

## T1 – vargen och korpen (låst)
Andelen vargar (djur + myt) med ett korpord inom ± 25 ord.

| | Dikten | Prosan | Skillnad | 95 % intervall | p | Håller |
|---|---|---|---|---|---|---|
| **Huvud** | 10/59 = 16,9 % (30 texter) | 1/16 = 6,2 % (12 texter) | 10,7 pe | −8,6 till 24,8 | 0,24 | **nej** |
| Känslighet: korp eller örn | 30,5 % | 6,2 % | 24,3 pe | 4,8 till 39,3 | 0,017 | (ingen egen slutsats) |
| Känslighet: ± 10 ord | 10,2 % | 6,2 % | 3,9 pe | −13,7 till 15,3 | 0,61 | (ingen egen slutsats) |

- **T1 håller inte.** Korpen står oftare bredvid vargen i dikten, men prosan har för få djurvargar (16) för att skillnaden ska gå
  att visa. Prosans enda korp: Óláfs saga helga, ”munu vargar draga þik … ok hrafnar slíta”.
- Med örnen räknad som slagfältsfågel är skillnaden större och intervallet utesluter noll. Enligt planen drar vi ingen egen
  slutsats av känsligheten.

## Korpen
Huginn och Muninn finns i Grímnismál, Gylfaginning, Skáldskaparmáls korpheiti och Eddubrot. I skaldeversen blir de
omskrivningar för korpen som äter de fallna (”Hugin gladdi”, ”Munins teiti”). Korpen har ingen egen fördjupning: den följer
vargen till slagfältet och Oden.

## Vad det betyder och inte betyder
- Ett ord i en text är inte en tro. Sagorna skrevs på 1200-talet.
- Vargfylgjan i sagorna är ett berättargrepp: en dröm före ett överfall. Det säger något om hur sagaförfattarna berättade, inte
  säkert om vikingatidens tro.
