# Resultat: textmodel-21 (analysplan_tm21.md)

## A – appens inställning mot provets (tol02 → app)
- inne i ord: 698 luckor; rätt 76.4% → 76.6%; vunna 14, förlorade 12 (netto +2)
- helt ord: 698 luckor; rätt 59.2% → 59.2%; vunna 21, förlorade 21 (netto +0)
- runan rätt: vunna 26, förlorade 29
- svar ≥ 95 %: 409 med 19 fel → 342 med 15 fel

## B – trigram (app → app3)
- inne i ord: 698 luckor; rätt 76.6% → 76.9%; vunna 8, förlorade 6 (netto +2)
- helt ord: 698 luckor; rätt 59.2% → 58.3%; vunna 16, förlorade 22 (netto -6)
- runan rätt: vunna 22, förlorade 34
- svar ≥ 95 %: 342 med 15 fel → 430 med 17 fel

**B enligt planens punkt 3: HÅLLER INTE.**

## Slutsats (2026-10-30 17:48)
- **A:** appens egen inställning ger samma träffsäkerhet som provets (76,6 mot 76,4 % inne i ord, 59,2 mot 59,2 % hela
  ord) men är försiktigare: 342 svar ≥ 95 % med 15 fel mot 409 med 19. `textmodel.VALIDATION` står sig alltså även för
  appens inställning; ingen omskattning behövs.
- **B – negativ.** Trigrammen vinner 8 och förlorar 6 inne i ord men förlorar netto 6 hela ord, runan rätt −12, och gör
  modellen säkrare på fler svar (430 mot 342 ≥ 95 %) med fler fel (17 mot 15). Punkt 3 kräver netto över noll i båda
  slagen och inte fler säkra fel: båda brister. `--trigram` förblir av; inget ändras i appen.
- Lärdom för nästa plan: sammanhanget hjälper inne i ord men skadar hela ord – fler kandidater når höga sannolikheter
  utan att vara rätt. Kalibreringen skulle behöva skattas om med trigram innan en ny prövning; det är inte gjort.
- Körtid: steg A 40 min, steg B 5 h 55 min (fem veck parallellt). Provskriptet skriver inget förrän vecket är klart;
  en framstegsrad per sten läggs in före nästa tunga körning.
