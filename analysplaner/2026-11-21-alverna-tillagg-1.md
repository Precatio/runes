# Tillägg 1 till analysplanen "Alverna" – ett missat mönster och en oberoende kontroll

Skrivet och låst 2026-11-21, efter insamlingen och under handklassningen, innan något mått eller test har räknats.
Huvudplanen är analysplaner/2026-11-21-alverna.md (låst 5d305b6, sha256 529f2940…).

## Det missade mönstret
Mönstret för stor bokstav, `\b(?:Ljós|Dökk|Svart)?[AÁ]lf\w*`, kräver stor bokstav på *Á* efter förleden. Snorres
*Ljósálfar* och *Dökkálfar* (Gylfaginning) och liknande sammansättningar skrivs med liten bokstav efter förleden, och de
fångades därför inte. Mått A4 i planen förutsätter att de finns med. Därför läggs ett mönster till:
`\b(?:Ljós|Dökk|Døkk|Svart|Myrk)[aá]lf\w*`. De nya träffarna klassas för hand på samma sätt som de övriga. Inget annat
ändras.

## Den blinda kontrollen görs av en oberoende läsare
Planen säger att 40 slumpade träffar ska klassas om blint. Samma läsare kan inte vara blind för sin egen klassning.
Därför görs omklassningen av en separat instans av samma språkmodell (Claude Opus). Den får bara klassdefinitionerna
ur planen och textutdragen, inte den första klassningen. Kravet är oförändrat: minst 85 % överensstämmelse, och
oenigheterna redovisas.

## Vad som redan syns i klassningen (inget mått räknat)
Alla träffar med stor bokstav utom de tvetydiga är personnamn. Undantaget är *Alföðr*/*Alföður* (Oden, "allfadern",
förleden *al-*), som klassas som *annat*. Bland träffarna med liten bokstav finns också ord med förleden *al-*
(*alfari*, *alfarið*, *alfeigum*) och *álfrek* (avträde, Eyrbyggja saga), och de klassas som *annat*.
