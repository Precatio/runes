# A1, tillägg 1, not 3: Uppland, runda 2

Skriven och låst 2026-11-14, innan runda 2 körs. Gäller `2027-01-A1-tillagg-1-sri-fyndhistorik.md` och noterna 1–2.
Viktor sade ja 2026-11-14.

## Runda 1 (Uppland VI–IX, 1 040 artiklar, 4 843 uppgifter, inga citat strukna)
Stickprovet omfattade 100 stenar (slumpfrö 2030) och granskades av Claude Opus. Utfallet:

| Fältgrupp | Rätt | Wilson 95 % | Klarar kravet? |
|---|---|---|---|
| Läget | 97,7 % (293/300) | 0,95–0,99 | ja |
| Flyttningarna | 84,0 % (84/100) | 0,76–0,90 | nej |
| Försvunnen och återfunnen | 97,5 % (195/200) | 0,94–0,99 | ja |
| Samma sten | 100 % (100/100) | 0,96–1,00 | ja |

Felen i flyttningarna var systematiska och skilde sig från Södermanlands:
1. **Inmurningar räknades inte som flyttningar.** Det gällde stenar som murades in eller lades in i en kyrka eller
   annan byggnad: i en vägg eller mur, som tröskel, i en grund eller i ett golv (till exempel U 62, U 433, U 846,
   U 882, U 979 och U 981).
2. **Källans år blev händelsens år.** När en utgivare eller inventerare beskrev läget, till exempel Dybeck 1864 eller
   ett inventarium 1829, fördes det året in som flyttningsår (U 978, U 1052 och U 637).

Viktors kontroll av runda 1 gjordes inte. Runda 2 ersätter runda 1.

## Runda 2
- **Instruktionen** är densamma som i runda 1, med två nya regler:
  - **6. En inmurning är en flyttning.** Murades stenen in eller lades den in i en kyrka eller annan byggnad (i en
    vägg eller mur, som tröskel, i en grund eller i ett golv), är det en post i `flyttningar`. Fältet `till` är
    byggnaden och platsen. Orsaken är "kyrkbygge eller restaurering" om det gällde en kyrka eller utgivaren säger att
    det skedde vid ett bygge, annars "annat". Att stenen senare togs ut är en egen post.
  - **7. Källans år är inte händelsens år.** Fältet `ar` fylls bara med det år då flyttningen skedde. Ett år då
    någon beskrev, ritade, inventerade eller rapporterade läget ger `ar = null`, om inte texten säger att
    flyttningen skedde det året.
- **Stickprovet** omfattar 100 nya stenar, lottade med slumpfrö 2040 bland Upplands stenar som inte låg i runda 1:s
  stickprov. Viktors 10 stenar lottas ur det med slumpfrö 2041. Kraven och regeln om en för snäll granskare är
  desamma som i not 2.
- Runda 2 är **den sista för Uppland**. En fältgrupp som inte klarar kravet används inte i A1.
- **Reglerna 6 och 7 gäller också de band som ännu inte är utplockade.** Det är Öland, Gotland I–II, Gotland III,
  Västmanland, Närke, Värmland och Gästrikland. För dem är det deras runda 1.
- Runda 1:s utfall sparas (`upp_r1.jsonl`, `utdata/sri_fakta/upp_kontroll_r1.json`) och redovisas i rapporten.
