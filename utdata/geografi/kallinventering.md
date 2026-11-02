# Dåtidens geografi – inventering av öppna källor (2026-11-02)

Viktor 2026-11-02: "dåtidens geografi blir ett stort nytt fokus för oss" … "hämta in allt du kan kring detta".
Inventeringen gjordes av en forskningsagent 2026-11-02; alla adresser prövades samma dag utom de märkta (O = overifierad).
Nedladdade filer: `/Volumes/2TB/Antigrvity/Runes/geografi_kallor/` (skript `hamta.sh`, logg `logs/geografi_hamta.log`).

## Indelningar före ca 1350
- **ISOF PlaceNameService** (CC BY, JSON): `https://placenameservice.isof.se/v1/geo-reference/parishes` (2 538 socknar
  med härad, ATA-kod, Lantmäteriets kod, koordinat), `/districts` (296 härader, skeppslag, tingslag), `/provinces`.
  Kontroll av vår Wikidata-koppling. Häraderna är 1800–1900-talets.
- **Lantmäteriet Socken och stad** (CC0, GeoPackage): sockenpolygoner 1976–95; beställs via Geotorget (inloggning). Ger
  gränspolygoner och avstånd till närmaste folklandsgräns per sten.
- **Riksarkivets historiska GIS via R-paketet histmaps** (`junkka/histmaps`, CC0-data): socken, härad, stift från 1634.
- **SDHK** (CC BY 4.0): `https://filer.riksarkivet.se/registerdata/SDHK/csv/sdhk_2411.csv`. **SDHK 2593 = sexårsgärden
  1314** (latinsk text per hundare och folkland, Uppsala stift); SDHK 2849 (1318) nämner Tiundaland och Attundaland.
- **Det medeltida Sverige (DMS)**, skannade PDF: `https://filer.riksarkivet.se/dms/` (Uppland 1:1–1:12, Södermanland,
  Östergötland); hundaren, socknar, medeltida namnformer, kungsgårdar.
- **Rosenbergs geografiska lexikon 1882–83** (allmän egendom, CSV): `https://filer.riksarkivet.se/registerdata/Rosenberg/csv/Rosenberg.csv`.
- **TORA** (Riksarkivet, 1630–1800, O för öppna data).
- Svenska Wikipedia: Gotlands socknar anger ting, setting och treding (används för tredingarna); Lagsaga, Hundare,
  Uppsala öd, Sexårsgärd. Västergötlands fjärdingar och bygder: SRI Vg-bandens inledningar per härad.
- Stiften: Möre, Tjust, Aspeland och Handbörd hörde till Linköpings stift (O).

## Centralplatser
ISOF ortnamn (Husby 374 poster, Tuna, Husaby, Gudhem; ofta sockenns mittpunkt som läge); KMR fritext "kungsgård"
(239); Riksarkivets ortnamn ur de geometriska kartorna 1630–55 (CC BY 4.0, Zenodo 10.5281/zenodo.13305098).

## Tingsplatser
Ingen lämningstyp "tingsplats" i KMR: typen *Samlingsplats* (307 i vår samlingsplats.csv) och fritext "tingsplats" (130).
Sanmark 2009 (Södermanland), Sanmark 2017 (inte öppen).

## Kommunikationer och strandlinje
- **SGU:s strandförskjutningsmodell** (CC BY 4.0, GeoPackage): skikten `issjohav_900` (= 1050) och `issjohav_1000`
  (= 950); osäkerhet upp till ca 500 år. Ersätter den grova strandlinjen i r/geography.R.
- **RAÄ Kulturmiljöregistret, hela GeoPackage** (allmän egendom): `https://pub.raa.se/nedladdning/datauttag/lamningar_v1/`
  – linjer för färdvägar och hålvägar, fältet socken, hamnanläggningar, båtlänningar.
- Lantmäteriets höjdmodell Grid 50+ (Geotorget).
- Litteratur: Göthberg 2018 (vägar i järnålderns landskap), Ekholm 1950 (var restes runstenarna).

## Ortnamn
ISOF Ortnamnsregistret (CC BY; äldsta belägg, tolkning; många saknar belägg). Lantmäteriets Ortnamn (CC BY 4.0,
Geotorget).

## Litteratur (öppen)
Palm 1992 *Runor och regionalitet* (har); **P. Larsson 2002 *Yrrunan*** (DiVA, direkt relevant för r för ʀ); Lagman
1990; Källström 2007; **Källström 2025, slutrapport Runsvenska skrifttraditioner (RAÄ)** – visar dialektgränser i
runortografin i Västmanland (Källström 2014g); Mats G. Larsson 1993 "Kung Eriks nyordning" (hundaren); Brink-kapitel
(Tjust, Ärlinghundra). Inte öppna: Williams 1990, Zachrisson 1998, Brink 1990, Sawyer 2000, Bianchi 2010 (fulltext 404).

## Först att använda
1 ISOF socknar/härader → kontroll av sten→land; 2 sockenpolygoner (Viktor behöver logga in på Geotorget) → avstånd till
gräns; 3 histmaps 1634; 4 SDHK 2593 → 1314 års hundaren; 5 SGU-strandlinjen; 6 KMR-paketet (vägar, samlingsplatser);
7 DMS-volymerna (OCR); 8 ISOF-ortnamn med äldsta belägg; 9 Larsson 2002 och Källström 2025 mot våra gränsfynd;
10 Rosenberg och kartnamnen 1630–55.
