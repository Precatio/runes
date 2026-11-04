"""Bygger artefakten "Ristarna en i taget" av samma delar som appens sida: utdata/ristare/artefakt_mall.html,
web/src/app/(app)/ristare/ristare.css, web/src/lib/ristare/draw.js och web/public/geo/ristare.json.
    python3 utdata/ristare/bygg_artefakt.py UT.html
"""
import re
import sys

ROOT = __file__.rsplit("/utdata/", 1)[0]
read = lambda p: open(f"{ROOT}/{p}", encoding="utf-8").read()  # noqa: E731
draw = re.sub(r"^export ", "", read("web/src/lib/ristare/draw.js"), flags=re.M)
html = (read("utdata/ristare/artefakt_mall.html")
        .replace("__CSS__", read("web/src/app/(app)/ristare/ristare.css"))
        .replace("__DRAW__", draw)
        .replace("__DATA__", read("web/public/geo/ristare.json")))
open(sys.argv[1], "w", encoding="utf-8").write(html)
print(sys.argv[1], len(html) // 1024, "kB")
