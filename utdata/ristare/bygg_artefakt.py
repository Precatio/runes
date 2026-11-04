"""Bygger artefakten "Ristarna en i taget" av samma delar som appens sida: utdata/ristare/artefakt_mall.html,
web/src/app/ristarna/ristare.css, web/src/lib/ristare/draw.js och den senaste korpuskörningens ristare.json
(src/carver_pages.latest()).
    .venv/bin/python utdata/ristare/bygg_artefakt.py UT.html
"""
import os
import re
import sys

ROOT = __file__.rsplit("/utdata/", 1)[0]


def _latest():
    sys.path.insert(0, ROOT)
    from src.carver_pages import latest
    return latest()


read = lambda p: open(f"{ROOT}/{p}", encoding="utf-8").read()  # noqa: E731
draw = re.sub(r"^export ", "", read("web/src/lib/ristare/draw.js"), flags=re.M)
html = (read("utdata/ristare/artefakt_mall.html")
        .replace("__CSS__", read("web/src/app/ristarna/ristare.css"))
        .replace("__DRAW__", draw)
        .replace("__DATA__", open(_latest(), encoding="utf-8").read()))
open(sys.argv[1], "w", encoding="utf-8").write(html)
print(sys.argv[1], len(html) // 1024, "kB")
