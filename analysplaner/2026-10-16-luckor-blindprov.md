# Analysplan: att fylla i förlorade runor – blindprov och okända luckor

Låst 2026-10-16, innan något av provet nedan har körts. Planen committas i det publika arkivet och dess SHA-256 står i
commit-meddelandet. Ändringar efter låsningen redovisas som avvikelser i artikeln.

## Syfte
Visa hur Vitkis sannolikhetsmodell fyller i förlorade runor på vikingatida runstenar:
- **Del 1, blindprov:** ett känt svar som hålls dolt för modellen.
- **Del 2, okända luckor:** samma metod på luckor som ingen utgivare har fyllt.

Resultaten ska ge underlag för en artikelserie på vitkirunor.se.

## Material och programvara
- **Rundata 3.1 (2018)**, svenska vikingatida inskrifter (`scripts/runlm_gaps.py`: SW).
- **Modellen:** `src/runlm.py` och `src/textmodel.py`, version `textmodel-5`, programkod enligt commit `e1f8e5c`.
  - Läsningen görs med den av fem modeller som inte är tränad på stenen (crc32(signum) mod 5), som i appens panel
    "Läsning och luckor".
  - Fyllningsinställningar: `textmodel.FILL`.
  - Luckor som ligger nära varandra fylls tillsammans (`merge_runs`).
- **Luckorna** definieras med `gaps_of` i `scripts/runlm_gaps.py`: 1–4 förlorade runor (Rundatas `-`) i ett ord vars
  övriga runor är bevarade.
  - En lucka är *återställd* om Rundatas normalisering har ordet med hakparentes, till exempel `st[æi]n`.
  - En lucka är *öppen* om normaliseringen har `...` eller saknar ord.
- **Formelord** är de 50 vanligaste orden (efter `key`) i normaliseringarna av SW, till exempel *ok, sin, æftiR, stæin,
  faður, letu, sun, þenna, guð*. Alla andra ord, också namn, räknas som *innehållsord*.

## Del 1 – blindprov på skannade stenar
- **Urval:** alla stenar i de sex öppna 3D-datamängderna (`src/scan_sources.py`) som har återställda luckor. Före
  låsningen räknades 20 stenar med 28 luckor, varav 8 i innehållsord. Inga svar från modellen var granskade per sten.
- **Utförande:** varje sten läses av panelens modell utan spår. Rundatas återställning syns inte för modellen.
- **Primärt utfall:**
  - Andel luckor där modellens ord är samma ord som Rundatas (`same_word`), för alla 28 och för innehållsorden.
  - Modellens säkerhet mot hur ofta den stämmer.
- **Stenen som visas i detalj** väljs efter regeln:
  1. flest förlorade runor i luckor med innehållsord;
  2. därefter flest sådana luckor;
  3. därefter alfabetiskt efter signum.

  Stenen visas med hela läsningen, alla förslag och sannolikheter, och därefter facit.
- **Sekundärt, valfritt: spår ur 3D.**
  - För den valda stenen tas reliefbilder av luckorna fram ur skanningen.
  - Spåren läses av Viktor Kvant på ett blad utan text, innan han ser modellens svar.
  - Läsningen görs om med spåren som mjuka spår. Båda resultaten redovisas.

## Del 2 – öppna luckor
- **Urval:** alla öppna luckor i SW, läsning som i del 1.
- **Kandidater:** luckor där modellens bästa ord är ett känt innehållsord (inte `<unk>`) med sannolikhet minst 0,90.
- **Stenen som visas i detalj** väljs efter regeln:
  1. flest förlorade runor i kandidatluckor;
  2. därefter flest kandidatluckor;
  3. därefter högst medelsannolikhet;
  4. därefter alfabetiskt.
- **Alla kandidater redovisas** i en tabell, inte bara den valda stenen.
- **Nyhetskontroll:** för varje kandidat i artikeln kontrolleras om ordet redan är föreslaget. Följande gås igenom:
  - Rundatas kommentarer och översättning;
  - Runor 2020 (Riksantikvarieämbetet), läsningar och tolkningar;
  - en sökning i litteraturen.

  Ett förslag som redan finns redovisas som en bekräftelse, inte som nytt.

## Redovisning
- Alla luckor i båda delarna redovisas, också de där modellen har fel eller säger "okänt ord".
- Siffrorna förklaras i klartext.
- Svagheterna anges:
  - Rundatas återställningar bygger ofta på äldre teckningar och är själva tolkningar.
  - Namn är svåra utan spår.
  - Luckor över fyra runor lämnas öppna.
- Tidigare valideringar anges som jämförelse: verkliga luckor 79,5 % samma ord, 98 % rätt vid minst 95 % säkerhet
  (luckrapporten 2026-10-16).
