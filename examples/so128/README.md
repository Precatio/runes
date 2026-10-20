# Exempel: Sö 128 på tio minuter

Ett helt genomfört exempel, från öppen skanning till färdig stenrapport, så att du kan pröva Vitki utan egen skanning
och se vad resultatet ser ut som innan du läser METHODS.md.

## Underlaget

- **Sten:** Sö 128, Lids kyrka, Södermanland. Sandstenshäll, stilgrupp Pr2 enligt Rundata.
- **Skanning:** Laila Kitzler Åhfeldt, Riksantikvarieämbetet, i den öppna serien *3D-skanningar av Södermanlands
  runstenar*, Zenodo, DOI [10.5281/zenodo.11951255](https://doi.org/10.5281/zenodo.11951255), licens CC BY 4.0.
  Filen heter `So 128_1_4 thin closed holes.stl` (73 MB). Den ligger inte i det här förrådet – hämta den från Zenodo.
- **Appen:** analysmotorn måste köras lokalt (`README.md`, Kom igång).

## Kör

```bash
# från projektroten, med analysmotorn igång på localhost:8000
.venv/bin/python scripts/full_stone_analysis.py "So 128_1_4 thin closed holes.stl" \
  --signum "Sö 128" --out examples/so128/ut --no-ai \
  --author "Ditt namn" --institution "Din institution" \
  --device "Laila Kitzler Åhfeldt, RAÄ (Zenodo 10.5281/zenodo.11951255)" --scan-license "CC BY 4.0"
```

Det tar några minuter: bilderna räknas ur skanningen, huggspåren mäts automatiskt med Vitki-protokollet (groove-5,
bara runor) i två känsligheter, syntesen väger beläggen, R-analyserna ställer stenen mot hela korpusen och rapporten
skrivs som Markdown, Word, HTML och LaTeX med tolv figurer. `--no-ai` betyder att all text är framräknad; ingen
API-nyckel behövs.

## Resultatet

[rapport.md](rapport.md) är rapporten exakt som skriptet skrev den 2026-10-20 (figurerna nedskalade till jpg här;
originalen i full upplösning hamnar i `ut/artikel/figurer/`). Läs den som ett exempel på formen, inte som ett
forskningsresultat: Sö 128 har ingen ristare i Rundata, skanningens punktavstånd (1,1 mm) är glesare än protokollet
rekommenderar, och huggspårsmåtten är inte visade att skilja ristare åt (METHODS.md 13, bristlistan i rapportens sista
avsnitt).

Vad du ser i rapporten, i ordning: stenen och inskriften ur Rundata, berggrunden på platsen (SGU), bilderna ur
skanningen (strykljus, djupkarta, relief), mätningen med figurer, jämförelsen med mätkorpusen, syntesen, stenen i
R-analyserna, och bilagorna med alla tvärsnitt och arbetsgången.

## Samma sak i appen

Öppna **3D-huggspårsanalys**, ladda upp filen, välj **Automatiskt** och **Kör automatisk analys**; steg för steg i
artikeln *Så gör du en huggspårsanalys i Vitki* på vitkirunor.se. **Stenanalys** gör hela kedjan ovan med ett klick.
