# Analysplan: Upptäcktsmotorn, version 5 – hur dragen spreds i tid och rum

Låst 2026-11-04, innan något modelleras. SHA-256 i `analysplaner/2026-11-04-upptacktsmotorn-v5-spridning.sha256`.
Kod: `r/discovery_v5.R`. Data: `utdata/upptackt_v5/drag.csv` (src/discovery_v2.py på korpus 7b9061c9a1c12c73, samma
drag som version 2). Resultat i `utdata/upptackt_v5/`.

## Bakgrund
Version 1–2 (parskanning) är uttömda på den här korpusen, och version 3 (samspel) och 4 (bayesiska nätverk) gav inget
som höll i halva B. De frågade alla *vilka drag som hör ihop*. Version 5 frågar något annat: **ändrades ett drag i
olika takt på olika håll** – kom det tidigare på ett ställe och senare på ett annat, eller försvann det fortare i en
bygd än i en annan? Det är en rums-tidsmodell (mgcv, tensorsamspel mellan plats och tid) över hela den daterade
korpusen. Sett före låsningen: antalet daterade stenar per landskap (U 533, Sö 160, Ög 94, Vg 81, Sm 31, övriga ≤ 20)
och mittåren (1000, 1030, 1040, 1060, 1080, 1120); inga modeller, inga drag mot tid.

## Material
Stenarna i drag.csv med stildatering (style_from och style_to; spannet är högst 60 år på alla), 962 stenar. Tid
t = (style_from + style_to)/2. Plats: lat/lon omräknade till km (x = lon · 111,32 · cos 59°, y = lat · 110,57).
Stenar utan koordinater tas bort. Halvorna som i version 2: socken för socken, växelvis inom varje landskap i
sockenmedeldateringens ordning (A upptäcker, B bekräftar).

## Dragen
Alla binära drag i drag.csv utom metadata. Ett drag prövas om det finns på minst 30 och saknas på minst 30 av de
daterade stenarna i halva A.

## Steg 1 (halva A): vilka drag ändras olika fort på olika håll
För varje drag, binomial gam (REML):
- M0: b ~ s(t, k = 4) + s(x, y, k = 30) + log1p(ord)
- M1: M0 + ti(x, y, t, d = c(2, 1), k = c(20, 4))

Prövning: anova(M0, M1, test = "Chisq"). BH över dragen. **Kandidat** vid q < 0,05, högst 20 (minsta p först).
Kandidatlistan och för varje kandidat A-modellens **lokala förändring** fryses (SHA-256 i `kandidater.sha256`) innan
halva B läses. Lokal förändring på en plats: logit p̂(1100) − logit p̂(1010) i M1, med medelordlängd, centrerad så att
medelvärdet över de daterade stenarna är 0 (z_A).

## Steg 2 (halva B): bekräftelse
För varje kandidat, z_A beräknat på B-stenarnas platser ur den frysta A-modellen, och
b ~ s(t, k = 4) + s(x, y, k = 30) + log1p(ord) + t:z_A + s(ristare, bs = "re")
(ristare som i version 2; osignerade får socknen som egen nivå). Hypotesen är riktad: där A säger att draget ökade mer
ökar det mer också i B, alltså koefficienten för t:z_A > 0. Ensidigt p. **Bekräftad** vid Holm-p < 0,05 över
kandidaterna; **mönster att pröva** vid BH-q < 0,05.

## Stegpinne för bekräftade (beskrivande, avgör inte)
1. Bara stenar på sin plats (pa_plats = 1).
2. Bara Uppland (draget ska gå åt samma håll inom Uppland ensamt).
3. Utan Uppland (om minst 30 stenar med och utan draget finns kvar i B).
4. Halvorna bytta (B upptäcker, A bekräftar), samma regler.

## Vad som rapporteras
För varje bekräftat drag: karta över p̂ omkring 1010 och omkring 1100 (A+B, M1 på hela datan, bara där stenar finns
inom 20 km), var draget var vanligast tidigt, var det ökade eller minskade mest, och koefficienten i B. Som
rimlighetskontroll redovisas hur kända tidsförändringar (pm_kors, pm_bon, pm_sjal, ord_hialpi) ser ut, oavsett om de
blir kandidater. Ett bekräftat drag är en **hypotes om spridning**, inte ett bevis på var något uppstod: stildateringen
är grov (sex mittår), Uppland väger tyngst, och en ristare som var verksam på ett ställe vid en tid kan ge samma bild
(därför ristaren som slumpeffekt). Litteraturen kontrolleras innan något kallas nytt.

## Stoppregel
Bekräftas inget: version 5 är negativ och körs inte om på samma data.
