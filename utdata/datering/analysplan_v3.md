# Analysplan v3: datering som sannolikheter per tidsskikt (låst 2026-10-27, efter v1 och v2)

**Motivering (ny, inte en justering av gränser).** v1 och v2 föll på intervallens täckning, och v2 visade varför:
stilgruppernas mittår har bara sex värden, så ett årsintervall på den skalan kan inte kalibreras. Osäkerheten anges
därför som sannolikheter för tidsskikten, och prövas med kalibrering i stället för intervalltäckning.

**Utfall.** Tidsskiktet = stilgruppens mittår som klass (sex klasser: 997,5, 1030, 1035, 1065, 1085, 1115).
**Modell.** Sannolikhetsskog (ranger, probability = TRUE, 500 träd, seed 2026), samma variabler som v1 (M1).
**Skattning.** Förväntat år = Σ p(klass) × klassens mittår. Prövning som v1: femfaldig korsvalidering grupperad per
socken, 3 upprepningar.

**Godkänt om alla tre gäller:**
1. Medelabsolutfelet för det förväntade året ≤ 0,85 × landskapets median (B1).
2. Kalibrering: förväntat kalibreringsfel (ECE) för den mest sannolika klassens sannolikhet ≤ 0,05 (10 lika breda
   sannolikhetsintervall).
3. Uppland: medelabsolutfelet högst 2 år större än seriationens.

Prediktionsmängdens täckning (de mest sannolika klasserna tills summan når 0,8) redovisas men avgör inte.
**Om godkänt:** skogen tränas på alla daterade stenar och ger sannolikheter och förväntat år för de odaterade; appen
visar förväntat år och de mest sannolika tidsskikten. **Om inte:** negativt, och arbetet med samlad datering avslutas
tills nya data finns.
