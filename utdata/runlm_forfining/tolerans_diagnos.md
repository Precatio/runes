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
