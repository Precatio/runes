# Analysplan: nya ristare – facit, utvecklingsdel och provdel för allt arbete med onämnda händer

Skriven och låst 2026-11-23, innan facit nedan har tagits fram eller använts. Viktor 2026-11-23: "fokusera på att bättra vår
förmåga att se mönster efter nya ristare. Använd alla medel vi har".

## Varför
- **Tre försök har fallerat mot runologernas grupper:**
  - täta kärnor (plan 15c2f757);
  - den öppna modellen (plan 091e6cba);
  - stenar som hör ihop (plan 0297bcbd).
- **Facit har varit för litet:** Runor 2020 gav 8–16 jämförbara grupper.
- **Risken med mer arbete:** varje nytt försök som prövas mot samma lilla facit ökar risken att metoden till slut passar
  facit av en slump.

Den här planen bestämmer därför en gång för alla:
1. hur facit byggs;
2. hur det delas i en utvecklingsdel och en provdel;
3. att provdelen bara används i låsta slutprov.

## Facit
- **Källor:**
  - **Runor 2020:** "samma som gjort X", tolkat som i `utdata/samma_hand/prov.py`.
  - **Sveriges runinskrifter (SRI), textbanden:** varje ställe där utgivaren säger att stenar är gjorda av samma ristare
    eller hand (sökmönstret i `data/cache/hander/sri_kontexter.json`, 225 ställen).
- **Utläsningen ur SRI:** varje ställe läses av Anthropics språkmodell Claude (Claude Opus), i två separata instanser för
  var sin halva. Ut kommer:
  - stenen och de andra stenarna (signum);
  - styrkan: *säker* ("är", "av samme ristare"), *trolig* ("torde", "sannolikt", "förmodligen") eller *möjlig* ("möjligen",
    "kanske");
  - om utgivaren **avvisar** samma hand ("knappast", "ej");
  - om den gemensamma ristaren har ett namn.
- **Kontrollen:** en tredje instans läser om 40 slumpvis valda ställen (frö 20261123) utan att se de första svaren. Kravet är
  ≥ 85 % samma stenpar och samma styrka. Når kontrollen inte kravet, läses alla ställen om av en ny instans och oenigheterna
  avgörs för hand innan facit används.
- **Facit är:**
  - grupper av stenar som utgivaren eller Runor säger har samma hand (säker eller trolig; möjlig redovisas för sig);
  - som en sammanhängande graf;
  - bara stenar som finns i Rundata.
- **Avvisningarna** sparas som ett facit för olika händer.
- **Upphovsrätt:** SRI läses och räknas. Bara stenpar, styrka och sidhänvisning sparas, inga citat utöver korta utdrag i
  resultatet.

## Delningen
- **Enheten:** grupperna i facit, slumpvis delade (frö 20261123):
  - hälften till **utveckling (U)**;
  - hälften till **prov (P)**.

  En grupp och alla dess stenar hamnar i samma del.
- **Utvecklingsdelen** får användas fritt för att bygga och välja metoder, mått och gränser.
- **Provdelen** används bara i ett slutprov under en egen låst plan. Där anges metoden, alla gränser och provets mått
  innan provdelen öppnas. Varje gång provdelen används noteras det i `utdata/nya_ristare/provdelen_logg.md`. Efter tre
  använda slutprov byggs ett nytt facit innan fler görs.
- **Namngivna ristare i Rundata** (säkra stenar) får användas i båda delarna som träning, men inte som provdelens mått.

## Medlen (beskrivs här, prövas i egna planer)
1. **Fler belägg per sten:**
   - stilgrupp;
   - korsform enligt Lagers typologi (Runor 2020);
   - kortkvist och stavlösa runor;
   - runhöjd ur SRI;
   - ornament- och runformsord ur SRI;
   - textdragen.
2. **En inlärd parmodell för samma hand** på par inom 30 km. Den tränas på säkra stenar och väljs på utvecklingsdelen.
3. **Grupperingen** med parmodellens sannolikheter.
4. **3D-skanningarna** (huggteknik) som extra belägg för de skannade stenarna, med bergarten som kontroll.
5. **Ornamentik kodad ur SRI:s planscher**, i ett pilotförsök.

## Utdata
- `data/cache/hander/` (utanför git): kontexter, utläsningar, facit med sidhänvisningar.
- `utdata/nya_ristare/`: delningen, endast signum, i `delning.json`; kontrollresultatet; provdelens logg.
