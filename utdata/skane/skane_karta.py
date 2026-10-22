"""Kartan till Skåneartikeln: Skånes vikingatida runstenar (utdata/skane/skane.json) på rikenas ungefärliga gränser omkring
1025 (web/public/geo/riken.geojson, ODbL/public domain), Hällestad och Lund utpekade. Skriver utdata/skane/skane_karta.png.
    .venv/bin/python utdata/skane/skane_karta.py"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
S = json.load(open(os.path.join(ROOT, "utdata", "skane", "skane.json"), encoding="utf-8"))
G = json.load(open(os.path.join(ROOT, "web", "public", "geo", "riken.geojson"), encoding="utf-8"))
COLOURS = {"danmark": "#f3d9c9", "gotar": "#e3ecd9", "svear": "#ead9c6", "norge": "#e6dff0", "bornholm": "#f3d9c9"}

fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=170)
for f in G["features"]:
    if f["properties"].get("epoch") != "1025":  # the realms as they stood when most of the stones were raised
        continue
    col = COLOURS.get(f["properties"].get("realm"), "#eeeeee")
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        ax.add_patch(Polygon(poly[0], closed=True, facecolor=col, edgecolor="#8a8a8a", linewidth=0.5))
xs = [s["lon"] for s in S["skane"] if s["lon"] is not None]
ys = [s["lat"] for s in S["skane"] if s["lat"] is not None]
ax.scatter(xs, ys, s=22, color="#1c5cab", edgecolor="white", linewidth=0.5, zorder=5, label="Vikingatida runsten i Skåne")
LABELS = {"DR 295": ("Hällestad", (6, -3)), "DR 314": ("Lund", (-30, -11)), "DR 279": ("Sjörup", (4, -11)), "DR 330": ("Gårdstånga", (5, 5)), "DR 262": ("Fosie", (-30, -3))}
for s in S["skane"]:
    if s["signum"] in LABELS:
        text, off = LABELS[s["signum"]]
        ax.annotate(text, (s["lon"], s["lat"]), xytext=off, textcoords="offset points", fontsize=8, color="#222222", zorder=6)
ax.set_xlim(12.3, 14.6); ax.set_ylim(55.25, 56.55)
ax.set_aspect(1 / 0.56)
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_title(f"{len(xs)} vikingatida runstenar i Skåne. Danskt område i rött, götarnas i grönt (omkring 1025)", fontsize=9)
ax.legend(loc="lower right", fontsize=8, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(ROOT, "utdata", "skane", "skane_karta.png"))
print("karta sparad", len(xs))
