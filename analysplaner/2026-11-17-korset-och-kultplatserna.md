# Analysplan: när korset kom till gudarnas platser – runstenarna i kultplatssocknarna

Skriven och låst 2026-11-17, innan någon runsten har knutits till en kultplatssocken. Del två till artikeln "Asatron i
landskapet" (Viktor 2026-11-17: "kan vi hitta en vinkel där vi presenterar något nytt? Kombinerar annan data vi samlat
in? Jag vill inte upprepa oss mot tidigare forskning"; "ja" till frågorna 1–3).

## Frågan
Kultplatsnamnen visar var den gamla tron hade sina platser (tillägg 1 till "Gudarna på kartan", f7b339ef). Runstenarna
är kristendomens första monument i landskapet. Hur möttes de? Restes fler kristna minnesstenar där de gamla gudarna
hade sina platser, talar stenarna där mer kristet, och kom de dit senare?

## Känt före låsningen
- Kultplatsnamnen: 128 i SOL enligt två blinda läsare (tillägg 1), med socken enligt huvudplanens regler; antalet per
  landsdel är känt (Mälarlanden 39, Östra Götaland 26 …). Fyra samiska heliga platser i Lappland räknas inte här (de
  ligger utanför runstensbygderna och är inte fornnordiska).
- Runstenarna: 2 321 svenska vikingatida enligt `nordic.is_runestone`, antal per landskap kända. Andelen med kristen
  text och bön, och tidsskikten, är kända för hela materialet (artiklarna "Bönen tystnade …" och "Den goda döden").
- **Inte gjort:** ingen runsten har räknats per kultplatssocken. Litteratursökningen (Fornvännen, Futhark, Namn och
  bygd) fann inga systematiska jämförelser av runstenar och sakrala ortnamn, bara enskilda platser (Harg i Odensala).

## Data
- **Kultplatssocken:** en ISOF-socken som har minst ett kultplatsnamn (säkert eller osäkert) enligt tillägg 1, med
  läge enligt huvudplanen (en sockens eget namn, eller den socken SOL anger för en by, gård, sjö eller ö). Övriga socknar
  i samma landskap är jämförelsen.
- **Runstenarna:** `nordic.is_runestone`, land `sverige`. Stenens socken är Rundatas fält `parish`, matchad mot ISOF:s
  socknar i stenens landskap (signumets prefix) på namn, med samma genitivregel som huvudplanen. Stenar vars socken inte
  kan matchas räknas bort, och antalet redovisas.
- **Landskapen i proven:** landskap med minst 30 runstenar och minst tre kultplatssocknar. Listan räknas fram ur data
  innan proven och redovisas.
- **Kristen text och bön:** `nordic.patterns` (kristen, bon). **Tid:** `nordic.year_of`, `nordic.bin_of`; "sen" är 1050
  och senare.

## Tre prov (tvåsidiga, Holm över de tre, α = 0,05)
- **K1. Fler runstenar?** Enhet: ISOF-socken i provlandskapen. Teststorhet: kvoten mellan medelantalet runstenar per
  kultplatssocken och per övrig socken, räknad inom varje landskap och vägd samman (Mantel–Haenszel-liknande: summan av
  stenar i kultplatssocknar delad med summan av förväntat antal om kultplatssocknarna hade landskapets medel). Omblandning
  av kultplatsetiketten mellan socknarna inom varje landskap, 10 000 gånger, slumpfrö ur planens kontrollsumma.
- **K2. Mer kristen text?** Enhet: runsten med läsbar text och år. Utfall: kristen text (`kristen`). Jämförelse:
  kultplatssocken mot övriga. Mantel–Haenszel över skikten landskap × tidsskikt (`nordic.mantel_haenszel`).
- **K3. Senare?** Enhet: runsten med år. Utfall: sen (1050 och senare). Jämförelse som i K2. Mantel–Haenszel över
  landskapen.

Ett prov **håller** när Holm-justerat p < 0,05, riktningen är densamma i båda halvorna av socknarna (`question.halves`,
med p < 0,05 i båda, eller samma riktning när en halva har färre än 10 stenar med utfallet; för K1 delas socknarna i
samma halvor) och riktningen är densamma när bara socknar med ett *säkert* kultplatsnamn räknas som kultplatssocknar.

## Beskrivande
- Bön (`bon`) som K2, utan prov.
- De sju stenarna med hedniska markörer: om deras socken är en kultplatssocken, en och en.
- Kultplatssocknar med flest runstenar, med namnen.

## Vad som inte prövas och inte skrivs
Orsaker. Ett samband mellan kultplatssocken och runstenar säger inte att någon reste en sten *för att* platsen var
helig; kultplatserna kan ha legat i de rikaste bygderna, där också runstenarna restes. Det skrivs som en möjlig
förklaring. Ett kultnamns äldsta belägg säger inget om när platsen användes.

## Utdata
`utdata/asatro/korset.py` → `utdata/asatro/resultat_korset.json`.
