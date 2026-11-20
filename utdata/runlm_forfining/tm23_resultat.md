# Resultat: textmodel-23, Petersons namnlexikon nyinläst (plan analysplaner/2026-11-20-petersons-namn-i-textmodellen.md, sha 321c3a6d)

Kört 2026-11-20 08:44–10:20 (`tm23/tm23_kor.sh`). Kontrollen (veck 0 utan namnen) gav samma val som app_f0.

## Provet (veck 0–4, runstenar, parvis mot app_f0–4)
- namnluckor: 281; rätt 110 → 110 (vunna 0, förlorade 0)
- alla luckor: 1 396; vunna 0, förlorade 0
- svar ≥ 95 %: 342 med 15 fel → 342 med 15 fel
- korta luckor (1–2 runor): nya rätt 0, nya fel 0

**Enligt planen: HÅLLER INTE** (villkor 1 kräver fler vunna än förlorade namnluckor). Namnen förblir av; dok5 körs inte.

## Beskrivande
- Namnen var verksamma: av 1 616 rader (alla föremål) fick 695 en annan sannolikhet för ordet och 16 ett annat ordval,
  men inget av ordvalen på runstenarna gick från fel till rätt eller tvärtom.
- 1 690 olika namnformer ur Peterson (tm22: 1 673); 915 av dem står inte som namn i Rundatas vikingatida
  normaliseringar i samma form. Läckspärren tar bort varje namn vars artikel citerar en provsten, och namn som står på
  provstenen och på andra stenar finns redan i modellen genom träningsstenarna – så som planen sade före provet kan
  Peterson bara tillföra namn som inte står på provstenen, och sådana namn är inte de som saknas i luckorna.

## Slutsats
Negativ, som tm22. En bättre inläsning av namnlexikonet ändrar inget i modellens luckor. Namnen som modellen missar är
inte okända för den; den väljer fel bland namn den redan känner (namnluckor med namnet på minst tre andra runstenar:
50 % rätt, mot 78 % för andra ord).
