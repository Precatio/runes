# Tillägg 1 till analysplanen "Väsen som inte är gudar" – kvalitetsgrinden och en kodrättelse

Skrivet och låst 2026-11-21, efter kvalitetsgrinden och innan något mått eller test har räknats. Huvudplanen är
analysplaner/2026-11-21-vasen.md (låst 2076615, sha256 8b29a176…).

## Grinden (första omgången)
Stratifierat stickprov, 135 träffar, bedömt för hand i sammanhanget (`data/cache/vasen/grind.csv`). Riktiga per klass:
jättar 15/15, dvärgar 15/15, alver 13/15, vättar 10/15, diser och nornor 14/15, de döda 12/15, nattväsen 6/15,
odjur 12/15, kristna väsen 14/15. Viktat efter klassernas antal träffar blir det 94 % riktiga (krav ≥ 90 %): **klarat**.
**Två klasser med minst 20 träffar ligger under 80 %:**
- **Vättar (67 %)**: verbet *vætta* (förvänta sig, tro) i "nú vættir mig", "mig vættir að", "en ek vætta".
- **Nattväsen (40 %)**: *mara* är oftast genitiv plural av *marr* (häst), och *myrkrið* (mörkret) fångades av
  *myrkriða*.

Övriga fel, som inte leder till någon ändring:
- *álfur* i betydelsen världsdel och *álfr* i en kenning för man;
- *draugr* i kenningar för krigare, bland annat på Karlevistenen (Öl 1);
- *dís* för en kvinna i Atlamál;
- *Fáfnisbana* som Sigurds tillnamn;
- *Munins* i en kenning för korp;
- *djöful* som skällsord.

Odjuren ligger precis på 80 % och revideras inte.

## Revisionen (ordlista v2, `utdata/vasen/ordlista_v2.csv`)
- **vættr**: som förut, men inte när ordet står intill ett personligt pronomen eller efter *nú*, alltså verbet.
- **mara**: bara när nästa ord är ett verb för att rida, trampa eller plåga (trað, tróð, treðr, kvaldi, kvelr, reið,
  ríðr), som i "mara trað hann".
- **kveldriða, túnriða, myrkriða**: bara substantivets ändelser (-a, -u, -ur, -um, -urnar, -unnar), alltså inte
  *myrkrið*.

Ett nytt stickprov, högst 15 träffar per reviderad klass (seed 20261122), bedöms. En klass under 80 % redovisas bara
som antal och tas bort ur testerna, enligt huvudplanen.

## Kodrättelse
Eddans CSV-fil har Gylfaginning och Skáldskaparmál som egna rader. Skriptet uteslöt dem inte, så Snorres Edda räknades
också bland "eddadikterna". Planen säger 34 dikter, och nu utesluts de två. Det upptäcktes i grindens stickprov.
Fyra dikter ur fornaldarsagorna (Hervararkviða, Hlöðskviða, Heiðreksgátur, Hálfsrekkaljóð) står både bland
eddadikterna, enligt Eddakartans urval, och i fornaldarsagornas vers. Det redovisas, men ändras inte.
