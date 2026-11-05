# Granskning av rapportutkasten inför Zenodo (2026-11-05)

Fyra rapporter är opublicerade utkast och ska rättas innan de publiceras och arkiveras. Granskningen gjordes av
oberoende läsare mot resultatfilerna, planerna och litteraturen; inget här är ännu åtgärdat. De publicerade
rapporterna rättades samma dag i nya rapportversioner med ändringslogg.

## Gemensamt för alla
- Ersätt "Någon release med DOI finns ännu inte; när den görs …" med kodläget (commit i Precatio/runes) – en arkiverad PDF
  kan inte uppdateras. Absoluta länkar (https://vitkirunor.se/…), länk till ordlistan (/forskningsrapporter/begrepp),
  "Diagram: Vitki, efter Rundata (ODbL)" i diagramtexterna, Rundatas version (3.1, 2018) och korpusens fingeravtryck.

## Skrivmiljöer utan namn (build_rapport_skrivmiljoer.py)
1. FEL: titeln blandar två mätningar. 85 % är medelrenheten i grupper av stenar MED kända ristare (validering), inte
   grupperna utan ristare. Ny titel: "… en gruppering efter handens drag samlar i medel 85 procent av samma ristare när
   den prövas på kända ristare den inte sett, mot 69 procent för närliggande stenar".
2. FEL: planens förutbestämda tolkning redovisas inte: utfallet betyder enligt planen "familjens beställningar möjliga"
   (delade namn håller); den positiva kontrollen visade att också kända ristares stenar delar namn.
3. FEL: plan 2 del 3 (mästarmodellen, mastare_resultat.md / mastare_modell.json, 912 kalibreringsgrupper) saknas och
   motsäger diskussionen: delad bergart markerar INTE en hand (koefficient −3,7), ovanliga stavningar gör det;
   sannolikhet att gruppen är en hand: Konungsund 8 %, Vetlanda 42 %, Kölaby 45 %, Leksberg 59 %, Husaby 62 %. Detta är
   också mallens kalibreringsavsnitt 5.3. Avvikelser finns (data.py sammanslaget med analys.py; kontrollantalet 26).
4. FEL: sammanfattningen generaliserar från fem stabila grupper till åtta.
5. FEL: bergart och höjd kommer delvis ur Kulturmiljöregistret (data/stone_dimensions.json, data/raa/kmr_runstenar.json),
   inte bara Rundata – ange källa och licens (CC0 via K-samsök).
6. RISK: "osäkerhet 15–17" är spridning över 30 slumpindelningar, inte ett konfidensintervall.
7. RISK: grupperna tar 33–44 % av bygdens samtida stenar mot median 12 % för kända ristare – en lokal skrivsed kan inte
   skiljas från en ristare; nämn som svaghet.
8. FORM: proven kördes på korpus 3f58e9339191761e; "i dag 13,6" → datera; p = 1,0·10⁻⁴ är golvet → "p ≤ 0,0001".

## Samma släkt på flera runstenar (build_rapport_slaktlankar.py)
1. FEL: odeklarerad avvikelse – båda planerna sade att appen behåller den tidigare modellen om provet inte håller; M2
   infördes ändå samma dag (27df5b3, 2026-11-01), 14 minuter efter "M2 införs inte" (b0b7ef5). Redovisa i 4.5.
2. RISK: "97 procent av länkarna inom en mil" är cirkulärt (modellen kan knappt göra en länk över 10 km säker); oberoende:
   84 % av Williams säkra par inom en mil (median 2,6 km) – lägg in med assert.
3. RISK: flyttade stenar: utan dem 836 av 2 320 stenar, 19 säkra länkar, täckning 36,7 %, precision 94,7 % – redovisa.
4. RISK: rubriksiffrorna (40 %, 92 %) kommer från en modell vald i efterhand – avgränsa titeln ("vald i efterhand");
   40 % är en andel av stenarna (80 av 202), inte av sambanden.
5. RISK: "61 mot 23" blandar körningar – "59 mot 23 på samma material".
6. RISK: domaren är författaren, inte en runolog – säg det. FORM: "facit"-jargong, "p = 0.0036" i svensk text,
   diagramtaket "329 av 323 par", datans version (data/links.json 2026-11-01) och Rundatas SHA.

## Upptäcktsmotorn (build_rapport_upptackt.py)
1. FEL: räknefel – i version 2 har paret skilj_kryss × ord_ræisa or2 = null men räknas som "höll inte". Rätt: version 2
   2 bekräftade, 1 mönster, 1 höll inte, 1 ej skattat; totalt 42 prövade, 17 bekräftade, 8 mönster, 17 höll inte (16
   distinkta samband). Rätta diagrammet, avsnitt 6 och "arton träffar" → "sjutton".
2. FEL: "den andra hälften hade varit falska fynd" överdriver: av 28 höll 14, 6 var signifikanta i halva B men klarade
   inte Benjamini–Hochberg, 8 höll inte.
3. RISK: "fäderna dog hemma, och en död hemma var inget att berätta" är en tolkning; rel_foralder är förälder.
4. FORM: korpus 3f58e9339191761e; urvalet för lokala skanningen (på plats eller vid kyrka, inte museum, koordinater).

## Upplands folkland (build_rapport_folkland.py)
1. FEL: 39 uppländska stenar faller tyst bort eftersom deras socknar saknar folkland i web/public/geo/sten_land.json:
   Färingö tingslag 24 (Sånga 6, Lovö 6, Hilleshög 4, Skå 4, Munsö 2, Färentuna 2), Adelsö 6, Ekerö 5, och U 53, U 54,
   U 419, U 871. Enligt DMS 1:7 hörde Färingö tingslag till Bro härad i Attundaland och Adelsö till Trögd i
   Fjädrundaland. Attundalands *at* går från 12,0 % till 14,6 %. Huvudtestet (360 mot 95:e percentilen 259) vänder
   knappast men ska köras om; gränsskanningen Attundaland–Fjädrundaland blir prövbar (7–14 stenar per sida) och är inte
   skarp. Rätta landindelningen först (historiska_land.json / assign_historiska_land.py) – det påverkar fler analyser.
2. FEL: "Attundaland 9 härader" – den nionde är ISOF:s "Ingår i Stockholms stad" (13 stenar, de flesta Spånga =
   Sollentuna härad).
3. FEL: draglistan tar upp "hednisk markör" och "kumbl", som föll bort för få fall.
4. FEL: Larsson 2002 s. 170 handlar om Upplands sammantagna andel, inte variation inom Uppland.
5. FEL: Peterson 1996 har en påhittad titel; rätt: "Aft/æft, at och æftir på de nordiska runstenarna – regional
   variation eller vad?" I: Mål i sikte (Uppsala), s. 239–252 – inte läst; den handlar om just *at*.
6. RISK: sammanfattningsrutan går längre än avsnitt 6; "beror inte på berggrunden" → "bärs inte av bergarten granit";
   "sex drag" är sex kombinationer av fem drag; hypotesen citeras avkortad. FORM: datans versioner, ISOF-registret med
   licens, SDHK 2593 (CC BY 4.0), DMS 1:7, Larsson 1993 s. 105 f.
