# Analysplan: appens egen inställning i maskeringsprovet, och trigrammen (textmodel-21-kandidat)

Skriven och låst 2026-10-30 innan några resultat tagits fram (METHODS.md 1x, ANALYSPLAN.md). Hash i
`analysis_plan_tm21.sha256`. Viktor bad om ett arbete som kan gå hela dagen utan honom.

## 0. Varför
Diagnos före planen (inga nya körningar, bara befintliga filer): textmodel-19:s maskeringsprov (tol02_f*) körs med
en enklare inställning än appen. Appen fyller luckor med `textmodel.FILL` (hela texten som fönster, 100 kandidater
vägda efter orden före och efter, ordet före stavningen, namn från stenar inom 10 km, 40 namnkandidater) och bygger
modellen med `textmodel.MODEL` (contexts, lam_class 0,2). Provet använde fönster 2, 60 kandidater utan sammanhang och
modell utan contexts och lam_class. Siffrorna appen visar (`textmodel.VALIDATION`: inne i ord 0,764, hela ord 0,592,
säkra 0,954) är alltså mätta på en annan inställning än den som används. På dok5 (appens inställning) var 41 av 109
missar rätt ord bland de fem bästa men inte först, oftast ett namnval eller en kort tvetydig lucka (*su-*: sun/sinn).

## 1. Frågor
- **A (mätning, ingen prövning):** hur träffsäker är appens egen inställning i maskeringsprovet, på samma luckor som
  textmodel-19 (tol02_f0–4)?
- **B (prövning):** blir appens inställning bättre om kandidaterna också bedöms efter följder om tre ord (`--trigram`,
  formler som *ræisti stæin þannsi*)?

## 2. Underlag
Samma provstenar, delning (fem veck, frö 2026/15) och dolda runor som mask4/tol02 (scripts/runlm_restore_test.py).
Jämförelsen är parvis per lucka, bara runstenar (som tm19_ab.py). Ingen sten tas bort.

**Appens inställning ("app"):** `--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15
--context_cands --n_cands 100 --by_word --near 0.1 --near_km 10 --own_d --name_cands 40`.
**Kandidaten ("app3"):** samma plus `--trigram`.
Inga kodändringar; båda finns redan i koden.

## 3. Mått och gränser
- **A:** andel ord rätt inne i ord och hela ord, runan rätt, och fel bland svar ≥ 95 % (tm19:s kalibrering) – för
  app mot tol02, parvis. Ingen gräns: det är en mätning. Är app sämre än tol02 i båda slagen redovisas det som ett
  problem med appens inställning (inte rättat här).
- **B:** app3 mot app, parvis per lucka, veck 0–4 (ingen parameter väljs, så alla fem veck räknas): fler vunna än
  förlorade ord i båda slagen (inne i ord, hela ord) OCH fel bland svar ≥ 95 % inte fler. Sekundärt: runan rätt.

## 4. Vad som INTE får göras
Inga andra flaggor än de i punkt 2. Inga ändringar av luckorna. Ingen omkörning med annan inställning efter att
resultaten setts. `textmodel.VERSION`, `FILL`, `MODEL` och `VALIDATION` ändras inte i detta steg.

## 5. Redovisning
Utfallet skrivs i `tm21_resultat.md` (siffror ur `tm21_sammanfattning.json`, byggd av `tm21_jamfor.py`). Håller B
körs valideringståget (dok5 med trigram) som ett nytt steg med egen plan innan något ändras i appen. Visar A att
appens inställning är sämre än provets, eller bara annorlunda, föreslås att `VALIDATION` mäts om på appens inställning.
