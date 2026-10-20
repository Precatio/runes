# Toleranslagret: diagnos av æftiR-fallen och rank-null-missarna (2026-10-19)

## Vad som undersökts

Misstanken från namnspåret (2026-10-18): tre æftiR-missar i maskeringsutvärderingen där stenen
har **iftiR** hugget - "suspicious, maybe another bug". Genomgång av mask4/mask4bas (textmodel-18,
fem veck, 808 helt maskerade ord).

## Diagnos: inte en kodbugg - ett täckningshål

æftiR-missarna faller i två klasser:

1. **Kontextförluster** (U 304, U 460): rätt form finns som kandidat med rimlig sannolikhet men
   rankas tvåa efter ett kontextuellt rimligt alternativ (suniR, kuþan). Inget fel i matchningen.
2. **Rank-null** (U 1023 *etiR*, Ög 122/186 + U 227 *ifti*, Sm 96 *hftR*, Vg 13 *fti*, U 207
   *eftR* svagt): ristaren högg en variantstavning som inte är attesterad för ordet i
   träningsvecken, och kandidatgeneratorn kan då inte nå ordet alls - sanningens p blir exakt 0.

Mönstret gäller inte bara æftiR. Över hela mask4: 454/808 rätt (56,2 %); av 354 missar är
**194 rank-null (55 %)**, 92 svagt rankade, 68 kontextförluster. Rank-null-orden är spridda
(æftiR 5, ræisti/ræisa, gærðu, haggva, lagði, byggi, þennsa, namn ...) men mekanismen är en
och samma: **oattesterad variantstavning av känt ord ⇒ onåbart**.

Slutsatsen binder ihop två hävstänger ur namnspåret till en: namntoleranserna (h-bortfall,
vokalbortfall, svarabhakti) och "æftiR-buggen" är samma problem och löses av samma lager.

## Åtgärdsdesign (textmodel-19-kandidat)

Variantexpansion i kandidatgenereringen: attesterade huggningar av ett ord utökas med
regelgenererade varianter till regelstraff (λ per regeltillämpning, trimmas på vecken):

- slut-R-bortfall (*ifti* ← iftiR)
- h-protes/-bortfall (*hftR*; namnen: *ulfR*/*hulfR*)
- obetonad vokal eliderad eller skiftad i/e/a (*etiR*, *eftR*, *fti*; æ-platsens a/e/i)
- nasal utelämnad före klusil (kikR = gengr-mönstret)
- svarabhaktivokal (namnen: *þurkil*/*þurikil*)

Varianterna ska mata samma poängsättning som exakta träffar, med straffet som prior - inte en
efterhandsreparation. Risk: kandidatexplosion och falska träffar (en kort följd som *fti* kan
nå flera ord); därför straff per regel, tak på antal regler per form, och trimning mot vecken.

## Valideringskrav innan VERSION flyttas

Som för tm18: fem vecks mask-utvärdering (A/B mot mask4), dok5 får inte backa, kalibreringen
räknas om, säkra fel får inte öka. Ingen del av lagret får aktiveras i skarp drift före det.
Potential: rank-null är 194/808 ≈ 24 procentenheter av alla maskerade ord; även en partiell
täckning är den största enskilda förbättringsytan som återstår.

## Utfall 2026-10-20: λ-valet på veck 0 (analysplan_tm19.md, punkt 5)

Lagret byggt i `runlm.Model(tolerance=λ)` (regler a–f, högst två per variant, varianter från stavningar med
P(runor | ord) ≥ 0,05). Samma luckor som mask4 (textmodel-18), parvis per lucka, veck 0 (139 + 139 luckor):

| λ | inne i ord vunna/förlorade | helt ord vunna/förlorade | runan rätt | fel bland ≥ 95 % |
|---|---|---|---|---|
| 0,02 | 0 / 0 | 1 / 0 | +1 / −0 | 4 → 4 |
| 0,05 | 0 / 2 | 2 / 2 | +3 / −2 | 4 → 4 |
| 0,1 | 0 / 4 | 2 / 3 | +3 / −4 | 4 → 4 |

Vunnet: U 1018 *sinn* (hugget *sn*, vokalbortfall), U 1087 *syni* (*suni*, y/u). Förlorat vid högre λ: varianter av
vanligare ord tränger undan rätt ord (*bofi* → *tofi*, *bonda* → *faður*, *satti* → *retti*, *let* → *retta*).
Enligt planen väljs 0,02 (enda λ över noll) och prövas på veck 1–4. Förväntan: nära noll. Räckvidden är mycket
mindre än rank-null-andelen (≈ 39 missar per veck) antydde – varianterna når sällan kandidatgränsen (n_cands = 100,
rankade på P(runor | ord) × ordfrekvens, där λ-straffet läggs ovanpå) och konkurrerar i poängsättningen med
<unk>-teckenmodellen. Det är en mekanikfråga, inte en λ-fråga, och ligger utanför den låsta planen: en ny plan
krävs för att pröva t.ex. egen kvot för varianter (som namnkvoten i tm18) eller straff först i poängsättningen.

## Utfall 2026-10-20: veck 1–4 med λ = 0,02 (planens punkt 3)

559 + 559 luckor, parvis mot mask4 (textmodel-18): inne i ord 8 vunna / 2 förlorade (netto +6), hela ord 5 / 3
(netto +2), runan rätt +9 / −5, fel bland svar ≥ 95 %: 16 → 15. Vunnet är lagrets avsedda fall – *sigmundr* ur
*…r*, *hakonaR* ur *aR*, *felaga* ur *aka*, *þessaR*, *þennsa*, *sten* ur *stn*, *ræistu* ur *ristu* – förlorat är
fyra ordbyten till vanligare ord (*broður* → *faður*, *halfdan* → *lifstæinn*, *es* → *ok*) och en böjning.
Punkt 3 håller (båda slagen över noll, säkra fel inte fler). Effekten är liten: +8 av 1 118 luckor. Nästa steg
enligt punkt 7: kalibreringens underlag regenereras med lagret, listkalibreringen skattas om och dok5 körs om;
VERSION flyttas bara om dok5 ≥ 249 av 361 och ≥ 95 %-felen inte ökar.
