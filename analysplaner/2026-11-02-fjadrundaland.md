# Analysplan: Fjädrundaland (del 3 i serien De gamla landen)

Skriven och låst 2026-11-02, innan något av proven nedan har körts. Viktor 2026-11-02: "gå vidare till nästa land".
Bakgrund (landprofilen, plan eb59f631, alla håller): r för ʀ 52 mot 16 %, plustecken som skiljetecken 17 mot 4 %, ræisti 9
mot 3 %, stungen y 36 mot 20 %, känd ristare 90 mot 60 %, kors 35 mot 61 %, stenar i grupp 15 mot 34 %, flera resare 44 mot
63 % – mot resten av Uppland. Förväntad svaghet: Fjädrundalands stenar är systematiskt attribuerade (Stille 1999), så
"känd ristare" mäter forskningen, inte seden; draget prövas inte vidare.

## Data
Upplands runstenar i dragtabellen (`utdata/upptackt_v3/drag.csv`), region ur `src/regions.old_region`, `moved`/`lost`/
`carvers_all` ur korpusen 7b9061c9, tidsskikt som i häradsskannern.

## Prov
**T1 Robusthet** för sex drag – pm_kors, r_for_R, skilj_plus, ræisti (ord_ræisti), i_grupp, flera_resare – Fjädrundaland mot
resten av Uppland, logistisk regression med tidsskikt: a) ristaren som slumpeffekt; b) bara stenar på ursprunglig plats;
c) bara daterade; d) utan förlorade; e) utan stenar av någon ristare med minst 5 stenar i Fjädrundaland. Håller i ett steg
om p < 0,05 och samma riktning. Rapporteras steg för steg.
**T2 Ristaren eller landet?** För Balle (flitigaste ristaren): andelen kors och r för ʀ på hans stenar i Fjädrundaland mot
hans stenar utanför (Fishers exakta test, tvåsidigt). Samma för alla ristare med minst 5 stenar både i och utanför
Fjädrundaland. Holm över T2-proven.
**T3 Bergarten** redovisas inte som sed (granit 93 mot 80 %).

## Beskrivning (inga prov)
Hällristningarnas andel i fornlämningsregistret (naringar.json), gravskick och ortnamn ur landprofilen, ristarna.

## Redovisning
`utdata/fjadrundaland/fjadrundaland.py`, `.R`, `.json`, `resultat.md`. Artikeln i seriens form v3 (atmosfär, berättad
statistik, efterordet "Så vet vi det"), med karta.
