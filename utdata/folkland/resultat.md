# Upplands folkland och deras runstenar – resultat

Låst plan `analysplaner/2026-11-01-upplands-folkland.md` (sha 48346775). Kört 2026-11-01 med `utdata/folkland/folkland.py`;
alla tal i `folkland.json`. Stenar i dragtabellen: Tiundaland 319, Attundaland 340, Fjädrundaland 123, Roden 60.

## Steg 1 – 13 av 27 drag skiljer mellan folklanden (q < 0,05, tiden konstant)
Kors, kristna markörer, död borta, beröm, flera resare, stenar efter barn och efter föräldrar, *drengr*, granit, stungna
runor, monoftong (*stin*), r för ʀ och prepositionen *at*.

## Steg 2 – tre håller i båda halvorna
Alla tre är språk- och stavningsdrag:
- **Prepositionen *at*** (i stället för *æftiR*): Fjädrundaland 40 %, Tiundaland 32 %, Roden 23 %, Attundaland 12 %
  (p 0,0002 i båda halvorna).
- **r för ʀ**: Fjädrundaland 51 %, Tiundaland 19 %, Roden 15 %, Attundaland 12 % (p 0,03 och 0,0006).
- **Monoftong** (*stin* för *stæin*): Fjädrundaland 66 %, Tiundaland 55 %, Attundaland 43 %, Roden 24 % (p 0,02 och 0,0001).
Korsen skiljer starkt i båda halvorna (p < 0,001) men olika folkland har högst andel i halvorna (Tiundaland 65 och
Attundaland 61 % ligger för nära), så de håller inte enligt planen. Övriga tio skiljer i bara den ena halvan.

## Steg 3 – gränsprovet
- **Prepositionen *at* skiljer ända fram till gränsen mellan Tiundaland och Attundaland:** av stenarna inom 10 km från
  gränsen har 23 av 60 *at* på Tiundalands sida (38 %) och 5 av 49 på Attundalands (10 %), p 0,0007. Längre in: 30 mot
  12 %. Skillnaden är alltså lika skarp vid gränsen som inne i landen – den följer gränsen, den är ingen gradient.
- **r för ʀ** (Fjädrundaland mot Tiundaland): 39 mot 24 % vid gränsen, p 0,20 – en gradient, inte en gräns.
- **Monoftong** (Attundaland mot Roden, grannarna med störst skillnad): 42 mot 24 % vid gränsen, p 0,08 – inte vid gränsen.

## Vad det betyder
De gamla folklanden skiljer sig mest i **hur** stenarna skrevs, inte i vad de säger eller vilka som reste dem. Och för
ett drag – om man skrev *at* eller *æftiR* – går skillnaden rakt över gränsen mellan Tiundaland och Attundaland, som om
gränsen var en verklig skiljelinje för språket eller för ristarnas verkstäder 200–300 år innan den första gången skrivs
ned. Det är det tydligaste tecknet hittills på att en vikingatida indelning syns i runstenarna.

## Svagheter
- Ristarna hålls inte konstanta. Om ristare arbetade inom ett folkland kan gränsen vara deras verksamhetsområden snarare
  än en språkgräns – det vore i sig ett fynd, men ett annat. Nästa steg: samma gränsprov med ristaren som slumpeffekt.
- Folklandens gränser är ritade efter 1900-talets härader och socknar, och häradernas sammansättning är delvis osäker
  (Tiundaland enligt listan 1314).
- Att *at* är vanligare i norra Uppland kan vara känt i litteraturen; vi har inte kontrollerat om gränsen redan är
  beskriven.
- Bara steg 1–3 är prövade; robusthetstrappan (ett landskap i taget, parish- och ristareffekter) är inte körd.

## Omkörning 2026-11-05 med rättad landindelning (deklarerad avvikelse)

Granskningen inför arkiveringen (utdata/rapporter/granskning_2026-11-05_utkast.md) fann att 39 uppländska stenar i
dragtabellen tyst föll bort, eftersom deras socknar saknade folkland: Färingö tingslag 24 (Sånga 6, Lovö 6, Hilleshög 4,
Skå 4, Munsö 2, Färentuna 2), Adelsö 6, Ekerö 5 och U 53, U 54, U 419, U 871. Rättelsen (web/src/lib/historiska_land.json
→ parish_medieval, scripts/assign_sten_land.py; Det medeltida Sverige 1:7, s. 19, 44, 114, 237): Färingö tingslag var Bro
härads andra halva → Attundaland; Adelsö hörde till Trögds härad till 1540 → Fjädrundaland; Ekerö hörde till Svartlösa
härad i Södermanland → inget folkland; U 419 och U 871 står på Skansen och knyts till sina socknar (Norrsunda → Attundaland,
Gryta → Tiundaland); U 53 och U 54 står i Stockholms stad (inget hundare, ursprunglig plats okänd) → inget folkland.
Rundatas "(nu …)" stryks ur sockennamnet, vilket flyttar U 77 (Spånga) från Roden till Attundaland. Kvar utan folkland: 7.
Stenar i dragtabellen: Tiundaland 319 → 320, Attundaland 340 → 366, Fjädrundaland 122 → 128, Roden 60 → 59
(landrattelse.json). Samma kod och planens regler; bara indelningen och sockenpunkternas namnregel (parish_point) är ändrade.
Den första körningen ligger i folkland_v1.json.

Rättelse av v1-texten ovan: steg 1 hade **12** drag med q < 0,05, inte 13 – kristna markörer hade q 0,053 (folkland_v1.json).

**Steg 1:** 14 av 27 drag skiljer (v1 12); nya är kristna markörer (q 0,035) och kvinna bland resarna (q 0,031).
**Steg 2:** 5 håller i båda halvorna (v1 3): *at* (Fjädrundaland 39 %, Tiundaland 32 %, Roden 23 %, Attundaland 14 %, v1 12 %;
halvorna p 0,003 och 0,0007), r för ʀ (Fjädrundaland 50 %; p 0,0005 och 0,02), monoftong (Fjädrundaland 67 %, Roden 25 %;
p < 0,0001 och 0,0005), och nu också korset (Tiundaland 65 %, Attundaland 61 %, Fjädrundaland 35 %; samma land högst i båda
halvorna) och beröm (Fjädrundaland 18 % mot 5–10 %; p 0,018 och 0,013).
**Steg 3 (planens kod):** *at* skiljer fortfarande ända fram till gränsen Tiundaland–Attundaland: 23 av 59 mot 5 av 49
(p 0,0005; v1 23/60 mot 5/49, p 0,0007). Längre in: 57 av 189 mot 34 av 220 (v1 25 av 201) – Färingöstenarna står inte i
gränszonen mot Tiundaland men har ofta *at* (9 av 17 med prepositionen känd). Korset (Tiundaland mot Fjädrundaland, 45/74 mot
13/34, p 0,024) och beröm (Fjädrundaland mot Tiundaland, 5/34 mot 2/74, p 0,031) finns vid gränsen; r för ʀ (p 0,18) och
monoftong (Attundaland mot Roden, p 0,11) är gradienter. U 899 ("Bondkyrka sn (nu Uppsala)") hamnar nu i Bondkyrka och
inte i Uppsala-Näs och ligger inte längre i gränszonen.

**Grannregeln och gränsen Attundaland–Fjädrundaland.** folkland.py prövar grannskap på varannan sockenpunkt (land_pts[::2]);
med den gallringen gränsar Attundaland och Fjädrundaland fortfarande inte, så planens steg 3 prövar *at* vid gränsen
Tiundaland–Attundaland som förut. Med alla punkter gränsar de (Adelsö–Munsö), och då skulle planens regel välja
Fjädrundaland–Attundaland för *at* och r för ʀ. Det är prövat EXPLORATIVT i folkland_grans_af.py / folkland_grans_af.json:
*at* 1 av 4 på Fjädrundalands sida mot 4 av 7 på Attundalands (p 0,95), r för ʀ 0 av 2 mot 2 av 7 – ingen skillnad vid
gränsen och för få stenar för att pröva den. Med alla punkter gränsar också Tiundaland och Roden; monoftongen prövas då där
(1 sten per sida).

**Planens dom:** oförändrad i sak – *at* är den skarpa gränsen mellan Tiundaland och Attundaland; i övrigt syns skillnaderna
i stavningen (r för ʀ, monoftong) som gradienter.
