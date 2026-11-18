"""Karta: Sveriges fristående gravhögar i Kulturmiljöregistret, de minst 20 m breda framhävda. Grå prickar: ISOF:s
socknar. Sparar karta_sverige_<sv|en>.png.
    .venv/bin/python utdata/hogar/karta_sverige.py"""
import csv
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DIAM = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\s*(?:i\s*)?diam", re.I)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def main():
    H = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", encoding="utf-8")))
    par = [p for p in json.load(open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/parishes.json", encoding="utf-8")) if p.get("latitude")]
    big, small = [], []
    for r in H:
        m = DIAM.search(re.sub(r"\s+", " ", r["beskrivning"] or ""))
        d = float(m.group(1).replace(",", ".")) if m else None
        (big if d is not None and d >= 20 else small).append((float(r["lon"]), float(r["lat"])))
    for lang in ("sv", "en"):
        sv = lang == "sv"
        fig, ax = plt.subplots(figsize=(6, 9), dpi=200)
        ax.scatter([p["longitude"] for p in par], [p["latitude"] for p in par], s=1.5, c="#d5dbe3", linewidths=0, zorder=1)
        ax.scatter([p[0] for p in small], [p[1] for p in small], s=0.8, c="#64748b", linewidths=0, alpha=0.6, zorder=2,
                   label=(f"högar ({len(small):,})" if sv else f"mounds ({len(small):,})").replace(",", " " if sv else ","))
        ax.scatter([p[0] for p in big], [p[1] for p in big], s=6, c="#b7410e", linewidths=0, zorder=3,
                   label=(f"minst 20 m breda ({len(big):,})" if sv else f"at least 20 m across ({len(big):,})").replace(",", " " if sv else ","))
        ax.set_xlim(10.8, 24.5); ax.set_ylim(55.2, 69.2); ax.set_aspect(2); ax.axis("off")
        ax.legend(loc="upper left", frameon=False, fontsize=8.5, markerscale=3)
        ax.set_title("Sveriges fristående gravhögar" if sv else "Sweden's free-standing burial mounds", loc="left", fontsize=12)
        fig.text(0.02, 0.02, ("Källa: Riksantikvarieämbetet, Kulturmiljöregistret (lämningstyp Hög; högar i gravfält ingår inte). "
                              "Bild: Vitki.") if sv else
                 ("Source: Swedish National Heritage Board, Kulturmiljöregistret (type Hög; mounds inside grave fields not "
                  "included). Image: Vitki."), fontsize=7, color="#475569")
        fig.savefig(os.path.join(HERE, f"karta_sverige_{lang}.png"), facecolor="white", bbox_inches="tight")
        plt.close(fig)
    print(len(big), "stora,", len(small), "övriga")


if __name__ == "__main__":
    main()
