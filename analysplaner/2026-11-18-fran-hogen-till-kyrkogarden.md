# Analysplan: från högen till kyrkogården – när och var syns skiftet i runstenarna?

Skriven och låst 2026-11-18, innan något av proven nedan har räknats. Underlag för en möjlig del 2 till artikeln
"Kullarna vid skogens rand". Viktor 2026-11-18 frågade om avsnittet "Varför ändrades det?" är en väg till en del 2;
svaret var att *varför* inte kan mätas, men *när och var* skiftet syns kan det, i tre prov. Viktor: "ok".

## Känt före låsningen
- **Planen "Tog kyrkan över efter gravfältet?"** (2026-10-29, 1eac97d): inget av fyra prov höll för hela landet. Kristna
  stenar vid gravfält, hela landet: oddskvot 0,92 (p 0,71). **Bara i Uppland**, som robusthetsprov: 0,43 (p 0,003) –
  kristna stenar står mer sällan vid gravfält. Det står där som ett tecken att pröva i en egen plan. Det är alltså sett;
  prov D1 nedan är en förregistrerad prövning av en känd ledtråd på samma stenar, med striktare jämförelse (inom
  härad) och en replikering i Södermanland, som inte har räknats för sig.
- **Rapporten om storhögarna** (planerna 089fcfb5 och 53f11fa6): runstenar på sin plats står oftare vid högar som är
  minst 20 m breda (oddskvot ≈ 3, Uppland, Medelpad och Södermanland bär mönstret). Stenarnas stil eller tid vid
  högarna är inte räknad.
- Ordet *kumbl* (minnesmärke) är inte räknat i korpusen. Att böner blir vanligare mot slutet av runstenstiden är känt
  från projektets tidigare mätningar.

## Data
Korpus `510ebfb3acc9a229` (Rundatas svenska vikingatida runstenar, 2 321). **På sin plats:** inte flyttad, inte
försvunnen, med läge. **Kristen:** korpusens kategori för kristna formuleringar (`cat_kristen`), samma mått som i planen
1eac97d. **Tid:** stilgruppens mittår (projektets tabell: RAK 980–1015, Fp 1010–1050, Pr1 1010–1050, Pr2 1020–1050, Pr3
1045–1075, Pr4 1070–1100, Pr5 1100–1130; KB och osäkra stilar räknas inte i D2–D3). **Gravfält:** kulturmiljöregistrets
gravfält inom 500 m. **Stor hög:** fristående hög minst 20 m enligt beskrivningen, som i 089fcfb5. **kumbl:** ordet
börjar på *kumbl* i normaliseringen.

## Tre prov (tvåsidiga, Holm över de tre, α = 0,05; slumpfrö ur planens kontrollsumma)
- **D1. Kristna stenar och gravfälten, Uppland.** Stenar på sin plats i Uppland: Mantel–Haenszel-oddskvoten för gravfält
  inom 500 m, kristen mot inte kristen, över häraderna; p ur omblandning av kristen/inte kristen inom häradet, 10 000
  varv. Väntat: oddskvot < 1. **Replikering:** samma prov i Södermanland, som ska ge samma riktning (p < 0,05 om minst 30
  kristna stenar, annars bara riktningen).
- **D2. Stenarna vid storhögarna är äldre.** Daterade stenar på sin plats: medelmittåret för stenar inom 500 m från en
  stor hög minus medelmittåret för övriga stenar, med jämförelsen inom landskap (omblandning av närheten inom
  landskapet, 10 000 varv). Bara landskap med minst en daterad sten vid en stor hög. Väntat: negativ skillnad.
- **D3. Ordet kumbl försvinner.** Alla daterade stenar (platsen spelar ingen roll för texten): korrelationen mellan
  *kumbl* (ja/nej) och mittåret, med omblandning av *kumbl* inom landskapet, 10 000 varv. Väntat: negativ.

Ett prov **håller** när Holm-justerat p < 0,05 och riktningen är densamma i båda halvorna (socknarna växelvis A/B i
namnordning inom landskapet; p < 0,05 i båda, eller samma riktning när en halva har färre än 30 fall av utfallet), och för
D1 när Södermanland ger samma riktning.

## Beskrivande (utan prov)
Andelen kristna stenar vid gravfält per stilgrupp i Uppland; stenarna vid storhögar per stilgrupp; andelen stenar med
*kumbl* och med bön per stilgrupp; exempel.

## Vad som inte skrivs
Proven säger när och var stenarna ändrades, inte varför. Att kristna stenar står mer sällan vid gravfält visar inte att
de döda begravdes vid kyrkan. Håller inget prov skrivs ingen del 2; avsnittet i del 1 står kvar som en öppen fråga.

## Utdata
`utdata/hogar/del2.py` → `utdata/hogar/resultat_del2.json`.
