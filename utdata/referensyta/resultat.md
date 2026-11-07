# Referensytan: fyrkantig stängning mot rullande paraboloid – resultat

Plan `analysplaner/2026-11-07-referensyta-paraboloid.md` (sha 5f64ffe4), kört 2026-11-07.

**S1 Riktningsberoende (konstgjort, `s1_riktning.py` → `s1.json`) – håller inte.** V-spår 8 mm breda och 2 mm djupa i
riktningarna 0°, 22,5°, 45° och 67,5° (0,5 mm per cell, brus 0,03 mm):
- fyrkantig: djup 2,08 / 1,96 / 1,93 / 1,96 mm, skillnad mellan riktningarna 0,15 mm, största fel mot 2 mm 0,08 mm;
  maskbredd 7,1–7,3 mm.
- paraboloid: djup 1,88 / 1,75 / 1,71 / 1,75 mm, skillnad 0,17 mm, största fel 0,29 mm; maskbredd 6,5–6,7 mm.
Paraboloiden doppar ner i spåret (pilhöjden 4²/(2·50) = 0,16 mm plus utjämningen) och underskattar djupet, och den är
inte mindre riktningsberoende: fönstret om 20 mm är så mycket bredare än ett runspår att det fylls i alla riktningar.

**Beslut enligt planen:** S1 håller inte, så den fyrkantiga stängningen förblir standard (`groove-7`), paraboloiden finns
kvar som val. S2 och S3 (de 37 KÅ-filerna) kördes inte: ett underkänt delprov avgör redan beslutet.

**Följd:** *Skala av vittringen* (src/peel.py) använder från och med nu samma referensyta som mätningen i stället för
paraboloiden; på Sö 206 är bilden lika tydlig (123 spår, 866 gropar; vittringsnivå 0,6–1,2 mm). Mitt tidigare påstående att
den fyrkantiga stängningen inte följer en välvd sten var fel: en stängning bevarar en kupig yta exakt.
