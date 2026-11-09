# Litteraturgenomgången – status och plan (uppdateras under arbetet)

Viktor 2026-11-09: gå igenom all Fornvännen och Futhark; hela runforskningen och närliggande discipliner; jämför mot all
data i rundatabaserna (Rundata, Runor 2020, danska, brittiska) och all geologi och geografi; se var Vitki har missat att
forska; hitta nya artiklar och rapporter. "Låt allt köra på."

**Huvudfrågan (Viktor, samma dag): vad har den svenska runforskningen missat – vilka perspektiv, antaganden, urval, metoder och källor?** Fältet `field_blindspots` i varje läsning; avsnittet ”Vad den svenska runforskningen har missat” i sammanställningen. Futhark 017–020 och andra läsningen av 001–002 fick tillägget medan de kördes; allt som startas därefter har det från början.

## Steg
1. **Hämtning** – `scripts/hamta_tidskrifter.py` → `/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/`.
   Futhark klar (180 poster, vol. 1–15). Fornvännen pågår (3 499 poster i Arkivsök, 1906 – april 2023; logg
   `/Volumes/2TB/Antigrvity/Runes/logs/tidskrifter.log`; återupptas med samma kommando om den avbryts).
2. **Urval** – `urval.py` (runsignum och runord; `--prefix fv --tidskrift fornvannen` för Fornvännen; hoppar över lästa).
   TODO: bredda Fornvännens urval till närliggande discipliner (vikingatid, yngre järnålder, gravfält, kristnande, kyrkor,
   skattfynd, ortnamn, ornamentik, Birka, Sigtuna …) – en andra nivå efter runtexterna.
3. **Läsning** – en läsare (Sonnet) per omgång om ~10 texter mot `UNDERLAG.md`; resultat per omgång som JSON Lines.
   - `fynd/` = första läsningen (smalare underlag): Futhark omgång 001–016.
   - `fynd2/` = läsning med det breda underlaget (hela runforskningen, närliggande discipliner, alla databasfält,
     `discipline`, `data_needed`, `consequence`, `vitki_missing`): Futhark 017–020, därefter **andra läsning av 001–016**
     (läsaren får första läsningen som utgångspunkt), därefter Fornvännen (`fv_NNN`).
   - Citaten kontrolleras ordagrant mot texten av läsaren.
4. **Sammanställning** – `sammanstall.py` → `sammanstallning.md` och `pastaenden.jsonl` (fynd2 vinner över fynd; status per
   påstående: "ej prövat" → "plan låst" → "mätt").
5. **Sökindex** – `sokindex.py bygg` (byggs om när Fornvännen är klar): fulltext per sida + signum per text.
6. **Därefter** – rangordna, gruppera per tema, välj de starkaste för låsta analysplaner; litteraturkontroll per tema;
   förslag på artiklar och rapporter till Viktor.
