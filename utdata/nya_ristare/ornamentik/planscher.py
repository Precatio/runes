"""Ornamentik steg 1: knyt SRI-planschernas sidor till stenar (bildtexterna i textlagret) och rendera sidorna.

Planscherna (RAÄ, Digitala Sveriges runinskrifter) är upphovsrättsligt skyddade: de läses och räknas bara, och både PDF:erna
och de renderade sidorna ligger utanför git (downloads/sri_plansch och data/cache/hander/plansch).

    .venv/bin/python utdata/nya_ristare/ornamentik/planscher.py [--render]
Skriver data/cache/hander/plansch/sidor.json  {signum: [[pdf, sida], ...]}; med --render även img300/<pdf>_p<sida>.jpg (300 dpi, skannernas upplösning).
"""
import glob
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import load  # noqa: E402

SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_plansch"
OUT = os.path.join(ROOT, "data", "cache", "hander", "plansch")
PREFIX = {"gastrikland": "Gs", "narke": "Nä", "oland": "Öl", "ostergotland": "Ög", "smaland": "Sm", "sodermanland": "Sö",
          "uppland": "U", "varmland": "Vr", "vastergotland": "Vg", "vastmanland": "Vs"}
FIX = str.maketrans({"l": "1", "I": "1", "O": "0", "o": "0", "S": "5", "B": "8"})


def pattern(pref):
    letters = r"\s?".join(re.escape(c) for c in pref)
    # signum = prefix, siffror (OCR kan sätta mellanslag och läsa 1 som l/I), valfri bokstav, sedan punkt/komma/och
    # äldre band: "Ög. 8." och intervall "Ög. 27—28."
    return re.compile(rf"(?<![A-Za-zÅÄÖåäö]){letters}\.?\s?([0-9lIO][0-9lIO ]{{0,4}}?)([A-Za-z]?)"
                      rf"(?:\s?[—–-]\s?([0-9lIO]{{1,4}}))?\s*(?=[.,:]|\soch\b)")


def main(render):
    known = set(load().sig)
    pages = defaultdict(list)
    for pdf in sorted(glob.glob(os.path.join(SRC, "*.pdf"))):
        stem = os.path.basename(pdf)[:-4]
        prov = stem.split("_")[1]
        if prov not in PREFIX:
            continue
        pref = PREFIX[prov]
        pat = pattern(pref)
        n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
        for p in range(1, n + 1):
            txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True,
                                 text=True).stdout
            found = set()
            for m in pat.finditer(txt):
                num = m.group(1).replace(" ", "").translate(FIX)
                if not num.isdigit():
                    continue
                nums = [int(num)]
                if m.group(3) and m.group(3).translate(FIX).isdigit():
                    hi = int(m.group(3).translate(FIX))
                    if 0 < hi - int(num) <= 5:
                        nums = list(range(int(num), hi + 1))
                for k in nums:
                    s = f"{pref} {k}{m.group(2) if m.group(2).islower() or m.group(2) in 'ABC' else ''}".strip()
                    if s in known:
                        found.add(s)
                    elif f"{pref} {k}" in known:
                        found.add(f"{pref} {k}")
            for s in found:
                pages[s].append([stem, p])
        print(stem, n, "sidor", sum(1 for v in pages.values() for x in v if x[0] == stem), "sten-sidor", flush=True)
    os.makedirs(os.path.join(OUT, "img300"), exist_ok=True)
    json.dump(dict(sorted(pages.items())), open(os.path.join(OUT, "sidor.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=0)
    print(len(pages), "stenar med minst en planschsida av", len(known))
    if render:
        need = sorted({tuple(x) for v in pages.values() for x in v})
        for stem, p in need:
            f = os.path.join(OUT, "img300", f"{stem}_p{p:04d}")
            if not os.path.exists(f + ".jpg"):
                subprocess.run(["pdftoppm", "-r", "300", "-jpeg", "-jpegopt", "quality=85", "-singlefile", "-f", str(p),
                                "-l", str(p), os.path.join(SRC, stem + ".pdf"), f], check=True)
        print(len(need), "sidor renderade")


if __name__ == "__main__":
    main("--render" in sys.argv)
