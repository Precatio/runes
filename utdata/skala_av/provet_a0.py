"""Fyller i djupbildens origo (a0, b0) i djupbildscachens metadata för provets filer som saknar det, med samma funktion
som studie 1b (utdata/forskningsplan/s1b_klassning.grid_origin, som kontrollerar att rutnätet blir djupbildens).
Utan a0 kan rune_bands.drawn_labels inte föra över slingorna, och filen hoppas över i provet.
    PYTHONPATH=. .venv/bin/python utdata/skala_av/provet_a0.py SERIE STEM"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.forskningsplan.s1b_klassning import grid_origin  # noqa: E402

series, stem = sys.argv[1], sys.argv[2]
path = os.path.join("/Volumes/2TB/cache/runmodell/djup", series, stem + ".json")
meta = json.load(open(path, encoding="utf-8"))
if "a0" in meta:
    print(stem, "har redan a0")
else:
    a0, b0 = grid_origin(series, meta)
    json.dump(meta, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(stem, round(a0, 3), round(b0, 3))
