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
   Fornvännen i två nivåer: `--niva run --prefix fv` (runtexterna) och `--niva grann --prefix fvg` (närliggande
   discipliner: minst fem periodord och fem ämnesord – vikingatid, yngre järnålder, gravfält, kristnande, skattfynd,
   ortnamn, ornamentik, Birka, Sigtuna …; ~12 % av texterna i ett prov på 620, uppskattat ~400 texter).
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

## Drift
- Datorn somnade 09–10 den 9 november och stoppade körningarna; `caffeinate -dims -t 43200` håller den vaken (startad 10:05). Omgång 012 (andra läsningen) startades om.
- Fornvännens första urval (de ~620 hämtade): `fva_001–007` (runtexter) och `fvga_001–006` (närliggande); resten tas med `--prefix fvb`/`fvgb` när hämtningen är klar.

## Läget 9 november kväll
- Viktor 17:05: **allt i Fornvännen läses fullt**, också de närliggande disciplinerna (valt framför sortering).
- Användningsgränsen nåddes 10:30–12:30; avbrutna läsare återupptogs med SendMessage.
- Kön: `python3 nasta.py N --starta` ger de N nästa omgångarna och markerar dem i `startade.txt`; läsaren startas med en kort prompt: läs `LASARE_RUN.md` (fva/fvb/fvc) eller `LASARE_GRANN.md` (fvga/fvgb/fvgc) och utför den för omgången.
- Om en session dör: omgångar i startade.txt utan fynd2-fil har inte blivit klara – ta bort dem ur startade.txt och starta om.

## Idéerna
- `FORSKNINGSIDEER.md` = alla idéer ur läsningarna per tema (skrivs om av `ideer.py` efter varje läsfönster; huvudspåren för hand i `IDEER_HUVUDSPAR.md`).
- Kör `python3 sammanstall.py && python3 ideer.py` efter varje fönster.

## Nästa fönster
Viktor 2026-11-09: fortsätt när användningen återställs (22:00). 88 grannomgångar kvar, från fvgc_007.
- Kontroll efteråt: korta runnotiser som ligger i samma OCR-fil som en annan text (t.ex. 'Nyfunnen runsten vid Alsike kyrka', Jansson 1948 s. 168, i filen 1948_166) kan ha fallit mellan stolarna – sök i sok.sqlite efter signum/runord per sida i texter som inte lästs som runtexter.
