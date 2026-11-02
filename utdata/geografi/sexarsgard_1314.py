"""Sexårsgärden 1314 (SDHK 2593, DS 1946; Riksarkivets SDHK, CC BY 4.0): Uppsala stifts kyrkor per folkland och hundare,
ur den latinska texten. Skriver sexarsgard_1314.json: folkland → hundare → [kyrkor/socknar i textens form].
    .venv/bin/python utdata/geografi/sexarsgard_1314.py"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/sdhk/sdhk_2593.txt"
t = " ".join(open(SRC, encoding="utf-8").read().split())
FOLK = [("Tiundaland", "colligebatur in tiundia", "Summa de tiundia"), ("Attundaland", "attundia", "Summa de attundia"),
        ("Fjädrundaland", "fiædhrundia", "Summa de fiædrundia")]
out = {}
for name, start, end in FOLK:
    seg = t[t.index(start):t.index(end)]
    parts = re.split(r"(Prouincia \w+|Habohundæri|Rodhin)", seg)
    sec, cur = {}, None
    for p in parts:
        if re.fullmatch(r"Prouincia \w+|Habohundæri|Rodhin", p):
            cur = p.replace("Prouincia ", ""); sec[cur] = []
        elif cur:
            sec[cur] += [m for m in re.findall(r"\bDe (?:ecclesia [\w ]+? |monasterio )?([a-zæøåþ]{3,})", p) if m not in ("prebenda", "bonis")]
    out[name] = sec
json.dump({"source": "SDHK 2593 (1314), Riksarkivet SDHK CC BY 4.0", "folkland": out}, open(os.path.join(HERE, "sexarsgard_1314.json"), "w"),
          ensure_ascii=False, indent=1)
for f, sec in out.items():
    print(f, {h: len(v) for h, v in sec.items()})
