# Samlad datering: resultat

## Version 1 (plan bb06d292…, låst 2026-10-27): inte godkänd

Kvantilregressionsskog på språkdrag, innehåll, kors, runtyp, seriation och plats, prövad med femfaldig korsvalidering
grupperad per socken (3 upprepningar), 1 008 daterade runstenar (`validering.json`).

| Mått | M1 | Gräns | Utfall |
|---|---|---|---|
| Medelabsolutfel | 15,1 år (landskapets median 20,2) | ≤ 0,85 × 20,2 = 17,2 | klarat |
| Täckning, 80 %-intervall | 0,957 | 0,75–0,88 | **inte klarat** (för breda) |
| Uppland mot seriationen | 16,4 mot 20,6 år | ≤ 22,6 | klarat |

M2 (med språkdateringen) gav 14,5 år och täckningen 0,961. Punktskattningen är alltså bättre än både landskapets median
och seriationen, men intervallen är för vida: skogens kvantiler tar med variationen inom stilgruppernas egna spann.
Enligt planen förs ingenting in i appen. En ny plan (version 2) kalibrerar intervallen och låses före den körningen.

## Version 2 (plan 84256b0f…): inte godkänd

Den konforma korrektionen blev exakt 0 i alla vecken, och täckningen 0,957 som i v1 (`validering_v2.json`).
Diagnos: facit, stilgruppens mittår, har bara sex värden (997,5, 1030, 1035, 1065, 1085, 1115). Kvantilerna hamnar på
dessa värden, avvikelsen max(q10 − y, y − q90) är 0 för de flesta stenar, och ett intervall som omfattar sina
gränsgrupper täcker mer än nominellt. Ett 80 %-intervall går inte att kalibrera på en så grov skala; felet ligger i
måttet på osäkerheten, inte i punktskattningen (medelfel 15,2 år mot 20,3 för landskapets median).
