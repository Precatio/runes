# Analysplan: runornas form – hur många ljud varje runa bar, prickarna och tiden efter 1066

Skriven och låst 2026-11-17, innan något nedan har räknats. Underlag för artikeln "Varför ser runorna ut som de gör?"
(Viktor 2026-11-17: "påbörja … och väv helst in något från vår app som gör perspektivet unikt"). Allt är beskrivande;
inga prov och inga p-värden. Litteraturen (ursprung, former, spridning) tas ur källor med sidhänvisningar.

## Känt före låsningen
- Rundatas fält `rune_types` är tomt för 2 240 av 2 321 svenska runstenar; det anger bara undantag (kortkvist omkring
  30 stenar, stavlösa omkring 10). Runformerna kan därför inte räknas i hela korpusen och redovisas bara som Rundatas
  noteringar.
- Rundata har 284 urnordiska inskrifter (flaggan `proto_norse`), skrivna med den äldre futharken.
- Utkastet "Prickarna, åsrunan och tiden" (opublicerat) räknade andelen e-ljud skrivna med stungen e mot
  `normalization_ows`. Det används inte här; måttet D2 nedan är räknat på nytt, med Rundatas runsvenska normalisering.

## Data
- **Yngre futharken:** svenska vikingatida runstenar (`nordic.is_runestone`, land Sverige).
- **Äldre futharken:** Rundatas urnordiska inskrifter (`flags.proto_norse`), alla föremål (stenar, brakteater, spännen
  m.m.), eftersom de är få. Redovisas för sig.
- **Ordparen:** varje avsnitt (§A, §B …) delas i ord. Translittereringen delas vid blanksteg och Rundatas skiljetecken
  (`: · ÷ + × | ¶ '`); normaliseringen (`normalization`, Rundatas runsvenska respektive urnordiska form) vid blanksteg och
  skiljetecken. Bara avsnitt där antalet ord är lika används. Ord med osäkra eller kompletterade runor
  (`[ ] ( ) - ? …` eller versaler utom R) räknas bort, liksom personnamn (ord som börjar med `"` i normaliseringen). Antalet
  ord som används och som faller bort redovisas.
- **Ljuden:** normaliseringens bokstäver förs till ljudklasser: a/á → a, æ → æ, e/é → e, i/í → i, j → j, o/ó/ô/ǫ → o,
  u/ú → u, y/ý → y, ø/œ/ǿ → ø, ð → ð, þ → þ, R/ʀ → R, w/v → v; övriga konsonanter som de står (g, k, d, t, b, p, f, h, l,
  m, n, r, s). Långa och korta vokaler slås ihop.
- **Paren runa–ljud:** för varje ordpar jämförs translittereringens bokstäver med normaliseringens ljudklasser
  (difflib.SequenceMatcher). Bara block där båda sidor har lika många tecken används (lika och utbytta bokstäver, ett
  mot ett); ojämna block räknas bort.

## Måtten
**D1 Ljudbördan.** För varje runa (translittereringens bokstav) i den yngre futharken: hur ofta den står för varje
ljudklass, och antalet ljud som har minst 5 % av runans förekomster. Samma för den äldre futharken (D1b). Redovisas
som andelar per runa, med antalet par.
**D2 Prickarna över tiden.** Bland svenska runstenar med säker stilgrupp (`has_style`): andelen e-ljud (klass e)
skrivna med stungen e-runa (translittererad e) i stället för i-runan, andelen g-ljud skrivna med g i stället för k, och
andelen y-ljud skrivna med y i stället för u – per stilgrupp (RAK, Fp, Pr1–Pr5).
**D3 Efter 1066.** Bland svenska runstenar med säker stilgrupp: andelen i Pr4 och Pr5 (i appens år efter 1066) och, för
sig, i Pr3 (1050–1080, som går över gränsen).

## Tolkning (bestämd nu)
- D1 beskriver hur mycket varje runa fick bära efter övergången till 16 runor; jämförelsen med den äldre futharken
  visar om bördan verkligen ökade. Inga slutsatser om varför – de tas ur litteraturen.
- D2 visar när prickarna kom in i bruket; litteraturens dateringar av de stungna runorna jämförs med kurvan.
- D3 visar hur stor del av de svenska "vikingatida" runstenarna som ristades efter den engelska slutpunkten 1066.
- Svagheter som redovisas: normaliseringen är utgivarnas tolkning av ljuden, inte ett oberoende mått; ordparningen
  faller bort där orden inte kan räknas lika; stilgruppernas år är ungefärliga.
