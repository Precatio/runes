# Att släppa en version (med DOI i Zenodo)

En version släpps först när utvecklingen är klar för att citeras i forskning. Då låses koden: artiklar och
rapporter hänvisar till exakt den versionen, och Zenodo arkiverar den med en permanent DOI.

## En gång: koppla Zenodo till GitHub
1. Logga in på https://zenodo.org med GitHub-kontot.
2. Under *GitHub* i Zenodo: slå på repot `Precatio/runes`.

## Varje version
1. Kör alla tester: `.venv/bin/python -m pytest` och `cd web && npx tsc --noEmit && npx eslint`.
2. Bestäm versionsnummer (t.ex. 2.1.0) och skriv in det i:
   - `api/config.py` (`APP_VERSION`)
   - `.zenodo.json` (`version`)
   - `CITATION.cff` (`version`, `date-released`)
3. Flytta posterna under "Ej släppt" i `CHANGELOG.md` till den nya versionen med datum.
4. Kontrollera att `src/limitations.py` (kända brister) och METHODS.md stämmer med koden.
5. Committa, märk och pusha: `git tag -a v2.1.0 -m "Vitki 2.1.0"` och `git push --tags`.
6. Skapa en release från märkningen på GitHub (Releases → Draft a new release). Zenodo arkiverar den och skapar
   en DOI inom några minuter.
7. Lägg in DOI:n i `README.md`, `CITATION.cff` (`doi`) och stenrapportens referens till Vitki
   (`src/stone_report.py`), och nämn den i `src/limitations.py` (bristen "Programvaran är under utveckling").

Mätningar som ska publiceras görs med den släppta versionen; metodversionen (`groove-N`) står i varje analys.
