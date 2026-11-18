"""Karta: gravhögarna kring Ättekulla i Helsingborg ur Kulturmiljöregistret, de som finns kvar och de som är borttagna.
Läser /Volumes/2TB/Antigrvity/Runes/downloads/hogar/attekulla_omgivning.csv; sparar karta_attekulla_<sv|en>.png.
    .venv/bin/python utdata/hogar/karta_attekulla.py"""
import csv
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from pyproj import Transformer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/hogar/attekulla_omgivning.csv"
FARM = (56.0101, 12.7584)  # Ättekulla gård: 250 m SE of the settlement Helsingborg 167:1 ("Ca 250 m NV om Ättekulla gård")
TR = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def gone(r):
    return r["skadestatus"] == "Förstörd" or bool(re.search(r"borttagen", r["beskrivning"] or "", re.I))


def main():
    R = [r for r in csv.DictReader(open(SRC, encoding="utf-8")) if r["lamningstyp"] == "Hög" and float(r["dist_m"]) <= 1500]
    fx, fy = TR.transform(FARM[1], FARM[0])
    pts = [(TR.transform(float(r["lon"]), float(r["lat"])), gone(r)) for r in R]
    for lang in ("sv", "en"):
        sv = lang == "sv"
        fig, ax = plt.subplots(figsize=(7, 7), dpi=200)
        kept = [((x - fx) / 1000, (y - fy) / 1000) for (x, y), g in pts if not g]
        lost = [((x - fx) / 1000, (y - fy) / 1000) for (x, y), g in pts if g]
        ax.scatter([p[0] for p in lost], [p[1] for p in lost], s=55, facecolors="white", edgecolors="#64748b", linewidths=1.2,
                   label=(f"borttagen eller förstörd ({len(lost)})" if sv else f"removed or destroyed ({len(lost)})"), zorder=2)
        ax.scatter([p[0] for p in kept], [p[1] for p in kept], s=60, c="#b7410e", edgecolors="white", linewidths=0.6,
                   label=(f"finns kvar ({len(kept)})" if sv else f"still there ({len(kept)})"), zorder=3)
        ax.scatter([0], [0], marker="*", s=180, c="#0f172a", zorder=4)
        ax.annotate("Ättekulla gård" if sv else "Ättekulla farm", (0, 0), xytext=(8, 6), textcoords="offset points", fontsize=9)
        circ = plt.Circle((0, 0), 1.5, fill=False, ls="--", color="#94a3b8", lw=0.8)
        ax.add_patch(circ)
        ax.plot([0.6, 1.1], [-1.55, -1.55], color="#0f172a", lw=2)
        ax.text(0.85, -1.5, "500 m", ha="center", fontsize=8)
        ax.set_xlim(-1.7, 1.7); ax.set_ylim(-1.7, 1.7); ax.set_aspect("equal"); ax.axis("off")
        ax.legend(loc="upper left", frameon=False, fontsize=9)
        ax.set_title("Gravhögarna kring Ättekulla, Helsingborg" if sv else "The burial mounds around Ättekulla, Helsingborg",
                     loc="left", fontsize=12, color="#0f172a")
        fig.text(0.02, 0.02, ("Källa: Riksantikvarieämbetet, Kulturmiljöregistret; högar inom 1,5 km (streckad cirkel). Norr uppåt. "
                              "Bild: Vitki.") if sv else
                 ("Source: Swedish National Heritage Board, Kulturmiljöregistret; mounds within 1.5 km (dashed circle). North up. "
                  "Image: Vitki."), fontsize=7.5, color="#475569")
        fig.savefig(os.path.join(HERE, f"karta_attekulla_{lang}.png"), facecolor="white", bbox_inches="tight")
        plt.close(fig)
    print(len(R), "högar;", sum(1 for _, g in pts if g), "borttagna")


if __name__ == "__main__":
    main()
