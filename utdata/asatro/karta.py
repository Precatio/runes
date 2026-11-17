"""Kartan till artikeln om asatron i landskapet: kultplatsnamnen och tingsnamnen (tillägg 1) och gudanamnen (huvudplanen)
ur Svenskt ortnamnslexikon, på ISOF:s sockenmittpunkter. Grå prickar: alla ISOF:s socknar, så att landets form och
var namn alls kan finnas syns. Sparar utdata/asatro/karta_<sv|en>.png.
    .venv/bin/python utdata/asatro/karta.py"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ISOF = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/parishes.json"
# Sami sacred names are pre-Christian but not Norse; left out of the map and the article's counts (noted in the text)
SAMI = {"Áhkká", "Nammásj", "Unna Sájvva", "Tarradalen"}
RUST, SLATE, TEAL, OCHRE, GREY = "#b7410e", "#334155", "#0f766e", "#b8860b", "#a8b3c2"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def load():
    t1 = json.load(open(os.path.join(HERE, "resultat_tillagg1.json"), encoding="utf-8"))
    main = json.load(open(os.path.join(HERE, "resultat.json"), encoding="utf-8"))
    kult = [x for x in t1["namn"] if x["kategori"] == "kultplats" and x["pt"] and x["namn"] not in SAMI]
    ting = [x for x in t1["namn"] if x["kategori"] == "ting" and x["pt"]]
    gods = [x for x in main["namn"] if x["gud"] in ("Tor", "Oden", "Frö", "Ull", "Njärd", "Fröja", "Frigg")]
    return kult, ting, gods


def draw(lang):
    kult, ting, gods = load()
    par = [p for p in json.load(open(ISOF, encoding="utf-8")) if p.get("latitude")]
    sv = lang == "sv"
    fig, axes = plt.subplots(1, 2, figsize=(10, 8.6), dpi=200)
    for ax in axes:
        ax.scatter([p["longitude"] for p in par], [p["latitude"] for p in par], s=2.2, c=GREY, linewidths=0, zorder=1)
        ax.set_xlim(10.8, 24.5)
        ax.set_ylim(55.2, 69.2)
        ax.set_aspect(1 / 0.5)  # rough correction for latitude around 60°
        ax.axis("off")
    a = axes[0]
    for x in kult:
        sure = x["grad"] == "säker"
        a.scatter(x["pt"][1], x["pt"][0], s=34, marker="o", facecolors=RUST if sure else "white", edgecolors=RUST,
                  linewidths=1.2, zorder=3)
    a.scatter([x["pt"][1] for x in ting], [x["pt"][0] for x in ting], s=22, marker="s", c=SLATE, zorder=2)
    a.set_title("Kultplatser och ting" if sv else "Cult places and things", fontsize=12, loc="left", color="#0f172a")
    h = [plt.Line2D([], [], marker="o", ls="", mfc=RUST, mec=RUST, ms=7),
         plt.Line2D([], [], marker="o", ls="", mfc="white", mec=RUST, ms=7),
         plt.Line2D([], [], marker="s", ls="", mfc=SLATE, mec=SLATE, ms=6)]
    a.legend(h, ["kultplats, säker tolkning", "kultplats, osäker tolkning", "ting"] if sv else
             ["cult place, secure reading", "cult place, uncertain reading", "thing (assembly)"],
             loc="upper left", frameon=False, fontsize=8.5)
    b = axes[1]
    col = {"Tor": RUST, "Oden": SLATE, "Frö": TEAL}
    for g in ("Tor", "Oden", "Frö"):
        xs = [x for x in gods if x["gud"] == g]
        b.scatter([x["pt"][1] for x in xs], [x["pt"][0] for x in xs], s=40, c=col[g], edgecolors="white", linewidths=0.6,
                  zorder=3, label=g)
    rest = [x for x in gods if x["gud"] not in col]
    b.scatter([x["pt"][1] for x in rest], [x["pt"][0] for x in rest], s=40, marker="D", c=OCHRE, edgecolors="white",
              linewidths=0.6, zorder=3, label=("Ull, Njärd, Fröja, Frigg" if sv else "Ull, Njärd, Freyja, Frigg"))
    b.set_title("Gudanamnen" if sv else "The god names", fontsize=12, loc="left", color="#0f172a")
    b.legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.text(0.02, 0.015, ("Källa: Svenskt ortnamnslexikon (2016), tolkningarna; lägen: ISOF:s sockenmittpunkter. Grå prickar: "
                           "alla socknar. Bild: Vitki.") if sv else
             ("Source: Svenskt ortnamnslexikon (2016), the interpretations; positions: ISOF parish centroids. Grey dots: "
              "all parishes. Image: Vitki."), fontsize=7.5, color="#475569")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = os.path.join(HERE, f"karta_{lang}.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path, len(kult), len(ting), len(gods)


if __name__ == "__main__":
    for lang in ("sv", "en"):
        print(draw(lang))
