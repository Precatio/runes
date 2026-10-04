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
