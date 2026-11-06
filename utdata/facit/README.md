# Facit för runigenkänningen och Runa för runa

Här ligger handmärkta facit, en JSON-fil per sten (och märkare). Ett facit görs av en människa i appen; inget
program skriver hit. Mappen läses av:

* `scripts/evaluate_rune_detection.py` – hur träffsäker runigenkänningen är (IMPLEMENTATIONSPLAN 1.1, PROTOCOL P7);
* `scripts/sparlasare_blind.py` – spårläsarens blinda prov (analysplaner/2026-11-06-sparlasare-blind.md), som kräver
  minst åtta facit av version 2 på stenar som klarar led F:s ordkontroll, utöver Sö 113 och Sö 128;
* `src/tei_export.py` – utgåvan i TEI/EpiDoc med ett 3D-ankare per runa.

## Så hamnar en fil här

1. Läs in skanningen på 3D-sidan (*Mäta huggspår*, fliken *Automatiskt*) och skriv stenens signum, till exempel
   `Sö 134`. Vänd den ristade sidan mot dig (*Vänd ristade sidan mot mig*).
2. Kryssa i **Facit-läge** och kör analysen. Alla spår mäts och inget är förmärkt.
3. Märk punkterna med rutor: *Runa*, *Ornamentik* (slinglinjer och ornament) eller *Utesluten* (sprickor, vittring).
4. **Runa för runa**: klicka på *Runa för runa* och sedan en gång mitt på varje runa, i läsordning. Remsan med
   translittereringen visar vilken runa nästa klick gäller; skiljetecken hoppas över av sig själva. *Hoppa över
   (syns inte)* för en runa som inte syns, *Bindruna* före klicket när ett klick täcker två runor, *Ångra senaste*.
5. **Spara facit (JSON)**. Filen laddas ned till din dator, med namnet `<signum>_facit.json`.
6. Flytta filen hit, till `utdata/facit/`, utan att ändra den. Byt gärna namn så att signum och märkare syns,
   till exempel `Sö_134_facit_VK.json`.

Filerna är data för publicerade prov och läggs till i git med `git add -f utdata/facit/<fil>` (mappen `utdata/` är
annars ignorerad).

## Regler

* Märk efter reliefen, inte efter färgerna, och utan att titta på analysens förslag (facit-läget visar inga).
* Sö 113 och Sö 128 är utvecklingsstenar: reglerna justerades på dem. Deras facit får ligga här men redovisas för sig.
* Runigenkänningens regler är låsta (`RULES_SHA256` i `scripts/evaluate_rune_detection.py`, testet i
  `tests/test_auto_grooves.py`). De justeras inte efter facitstenarna; facitstenarnas ritade slingor ritas inte om
  efter att resultatet setts.
* Ett facit ändras inte i efterhand. En ny märkning blir en ny fil.

## Formatet (version 2)

`type: "vitki-rune-facit"`, `version: 2`. Som version 1 (`signum`, `labeller`, `created`, `mesh` med filnamn och
SHA-256, `method_version`, `parameters`, `labels`, `rune_marks`, `image_width`, `image_height`) och dessutom:

* `image_frame` – var granskningsbilden ligger på modellen (pixlar ↔ mm, src/rune_links.py);
* `transliteration` – `{text, source}`: Rundatas sträng ordagrant och källan (Samnordisk runtextdatabas, version
  2014 med RUNDATA.xls uppdaterad 2018, ODbL);
* `tokens` – translittereringen som token (index, tecken, sort, ordnummer, sektion, plats i textmodellens text);
* `rune_links` – ett element per klick: `mark` (klickets nummer, från 0), `token_index`, `tokens` (en eller två,
  två för en bindruna), `char`, `image_xy` (pixlar), `point_mm` (punkt i 3D-modellen centrerad på sin omslutande
  lådas mitt), `normal_or_view` (normal och kameravy);
* `skipped_tokens` – runor som hoppades över för att de inte syns.

Version 1 läses som förut (utan kopplingar). Kontrollera en fil med
`.venv/bin/python -c "import json, sys; from src.rune_links import read_facit; read_facit(json.load(open(sys.argv[1])))" <fil>`.
