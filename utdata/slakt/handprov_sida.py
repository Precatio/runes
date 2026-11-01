"""Gör det blinda handprovet (handprov_formular.md) till en webbsida för bedömningen, med samma 25 par i samma ordning och
utan signum. Läser bara formuläret, aldrig nyckeln. Svaren sparas i sidans databas (samlingen "svar", ett dokument per par).
    .venv/bin/python utdata/slakt/handprov_sida.py <utfil.html>"""
import html
import json
import os
import re
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
md = open(os.path.join(OUT, "handprov_formular.md"), encoding="utf-8").read()
pairs = []
for block in re.split(r"^## Par ", md, flags=re.M)[1:]:
    n = int(block.split("\n", 1)[0])
    dist = re.search(r"Avstånd mellan stenarna: (.+)", block).group(1).strip()
    stones = []
    for m in re.finditer(r"\*\*Sten (\d)\*\* – ([^,]+), ([^;]+); stilgrupp (.+)\n\n> (.*)\n>\n> \*(.*)\*", block):
        stones.append({"landskap": m.group(2), "socken": m.group(3), "stil": m.group(4).strip(), "text": m.group(5), "en": m.group(6)})
    assert len(stones) == 2, n
    pairs.append({"par": n, "avstand": dist, "stenar": stones})
assert [p["par"] for p in pairs] == list(range(1, 26))
assert not re.search(r"\b(U|Sö|Ög|Vg|Sm|Öl|Vs|Gs|Hs) (Fv)?\d+", json.dumps(pairs, ensure_ascii=False))   # inga signum

DATA = json.dumps(pairs, ensure_ascii=False).replace("</", "<\\/")
page = open(os.path.join(OUT, "handprov_sida_mall.html"), encoding="utf-8").read().replace("/*DATA*/[]", DATA)
open(sys.argv[1], "w", encoding="utf-8").write(page)
print(sys.argv[1], len(pairs), "par")
