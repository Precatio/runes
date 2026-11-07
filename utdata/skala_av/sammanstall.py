"""Sammanställning av prova.py-körningarna: resultat.md (mått per skanning) och kontaktkarta.png (de avskalade bilderna
bredvid varandra, nedskalade).
    .venv/bin/python utdata/skala_av/sammanstall.py"""
import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(HERE, "*.json")))]
rows.sort(key=lambda r: (r["series"], r["signum"]))
lines = ["# Skala av vittringen provad på skanningar (utdata/skala_av/prova.py)", "",
         "Samma inställningar som dialogen på 3D-sidan (src/peel.py): mätningens referensyta (stängning 20 mm), djup vinkelrätt "
         "mot ytan, vittringsnivå = 70:e percentilen per 60 mm-ruta. Antal spår (rostrött) och gropar (grått) vid fyra "
         "reglagelägen; *kvar* = andel av ytan som ligger djupare än nivån plus reglaget. Bilderna: <stem>.png (dagens "
         "djupbild överst, den avskalade under).", "",
         "| Sten | Serie | mm/cell | Vittringsnivå mm (min–median–max) | −0,5 mm | 0 mm | +0,5 mm | +1 mm | Kvar vid 0 mm | Tid s |",
         "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L = r["layers"]
    cell = lambda k: f"{L[k]['spar']} / {L[k]['grop']}"  # noqa: E731
    lv = r["level_mm"]
    lines.append(f"| {r['signum']} | {r['series']} | {r['resolution_mm']:.2f} | {lv['min']:.1f}–{lv['median']:.1f}–{lv['max']:.1f} | "
                 f"{cell('-0.5')} | {cell('0.0')} | {cell('0.5')} | {cell('1.0')} | {100 * L['0.0']['left_share']:.0f} % | {r['seconds']['total']:.0f} |")
lines += ["", "Spår / gropar per reglageläge.", "",
          "## Bedömning (2026-11-07, efter bilderna)", "",
          "- **Mycket bra:** Gs 11 (runor och ornamentik nästan som en ritning), Sö 113, Vg 103, M 3 (korset och slingorna).",
          "- **Bra men brusigt:** Sö 206 och Sö 162 – runorna tydliga, men vittringsfläckar i fälten mellan slingorna blir röda.",
          "- **Fel att notera:** på Sö 128 blir en hel ramslinga grå – ett stort sammanväxt nät räknas som grop; i dialogen går "
          "det bara att klicka bort, inte att göra en grå fläck till spår.",
          "- **Svagare:** U 1144 (splittrat) och gravhällen Ög 2 (ett tätt nät av ornamentik).",
          "- **Fungerar inte:** Hs 14 (grovkornig yta, stavlösa runor) – som väntat.",
          "- Bedömningen är gjord med ögat. Om bilden hjälper vid läsning är inte mätt; nästa steg är ett prov med kända runor.",
          "", "## Skanningarna", ""]
for r in rows:
    lines.append(f"- {r['signum']} ({r['file']}): {r['credit']}")
open(os.path.join(HERE, "resultat.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
# contact sheet: the lower (peeled) half of each picture
thumbs = []
for r in rows:
    im = Image.open(os.path.join(HERE, r["stem"] + ".png")).convert("RGB")
    lower = im.crop((0, im.height // 2, im.width, im.height - 20))
    lower.thumbnail((640, 420))
    canvas = Image.new("RGB", (660, 450), "white")
    canvas.paste(lower, (10, 28))
    try:  # the default bitmap font has no Ö
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(canvas).text((10, 4), r["signum"], fill=(15, 23, 42), font=font)
    thumbs.append(canvas)
cols = 2
sheet = Image.new("RGB", (cols * 660, ((len(thumbs) + cols - 1) // cols) * 450), "white")
for i, t in enumerate(thumbs):
    sheet.paste(t, ((i % cols) * 660, (i // cols) * 450))
sheet.save(os.path.join(HERE, "kontaktkarta.png"))
print("\n".join(lines[:len(rows) + 6]))
