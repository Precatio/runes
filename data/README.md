# data/

`rundata.json` är en härledd version av **Samnordisk runtextdatabas** (Institutionen för nordiska språk,
Uppsala universitet), skapad med `python -m scripts.build_rundata`.

* Licens: Open Database License (ODbL 1.0) för databasen, Database Contents License (DbCL 1.0) för innehållet.
  Den härledda filen omfattas av samma licens.
* Källan ska anges vid användning: Samnordisk runtextdatabas, www.nordiska.uu.se/forskn/samnord.htm.
* Ändringar jämfört med originalet: tabellerna har slagits ihop per signum, alias har lösts upp, ristarfältet
  har strukturerats (S/A/P/L, osäkerhet, negerade namn borttagna) och svenska koordinater (RT90) har räknats
  om till WGS 84. Se `scripts/build_rundata.py`.

## cache/

`cache/geology.json` innehåller svar från Sveriges geologiska undersöknings (SGU) berggrundskarta
1:50 000–1:250 000, hämtade vid behov (se METHODS.md, avsnitt 10). Mappen ingår inte i repot.

## raa/ – fornminnesinventeringens år (D4)

Git-ignorerade tabeller ur Kulturmiljöregistret (Riksantikvarieämbetet, CC0), byggda med
`scripts/fetch_kmr_faltdatum.py` (hämtar fältdatum ur Fornsöks öppna API till
`/Volumes/2TB/Antigrvity/Runes/downloads/kmr_faltdatum/faltdatum.jsonl`) och `scripts/d4_inventeringsar.py`
(`text` läser beskrivningarna i GeoPackagen, `build` bygger tabellerna):

* `d4_inventeringsar_socken.csv` – per socken (län + socken): huvudår för senaste fältbesök i ett slumpurval av
  oförändrade FMIS-poster, spridning, årtal ur beskrivningstexten (förstagångs-/revideringsinventering) och en
  osäkerhetskolumn.
* `d4_inventeringsar_lan.csv` – per län: fördelningen av socknarnas huvudår.
* `d4_inventering_text.csv` – varje årtal som texten knyter till en inventering, med utdrag.
* `d4_forstagang_landskap.csv` – förstagångsinventeringens ordning per landskap enligt Hyenstrand 1978
  (Fornvännen 73, CC BY 4.0).

Metod, täckning och förbehåll: `utdata/d4_inventering/D4_RESULTAT.md`.
