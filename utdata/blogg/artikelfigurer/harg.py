"""Schema till artikeln om släkterna: vem som står på vilken av de fyra stenarna vid Harg (U 312–315, Skånela sn), efter
inskrifternas egen ordalydelse i Rundatas normalisering (varje namn kontrolleras mot texten). Svenska och engelska.
    .venv/bin/python utdata/blogg/artikelfigurer/harg.py"""
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
ins = {x["signum"]: x for x in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
INK, MUTED, GRID, ACCENT = "#1e293b", "#64748b", "#e2e8f0", "#b7410e"
STONES = ["U 312", "U 313", "U 314", "U 315"]
# (namn sv, namn en, normaliserad form att hitta, {sten: roll})
ROWS = [("Gunnar", "Gunnarr", "Gunnarr", {"U 312": "R", "U 313": "R", "U 315": "R"}),
        ("Holmdis", "Holmdís", "Holmdis", {"U 312": "N", "U 313": "R", "U 314": "R", "U 315": "R"}),
        ("Jofurfast", "Jôfurfast", "Iufurfast", {"U 312": "M", "U 313": "M", "U 314": "M"}),
        ("Tord", "Þórðr", "Þorð", {"U 315": "M"}),
        ("Farulv", "Farulfr", "Farulfs", {"U 312": "N", "U 315": "N"}),
        ("Öpir", "Œpir", "ØpiR", {"U 315": "K"})]
for _, _, form, cells in ROWS:
    for s in cells:
        assert form in (ins[s].get("normalization") or ""), (form, s)
LAB = {"sv": {"R": "reser", "M": "minns", "N": "nämns", "K": "ristar"}, "en": {"R": "raises", "M": "remembered", "N": "named", "K": "carves"}}
COL = {"R": INK, "M": ACCENT, "N": MUTED, "K": MUTED}
NOTE = {"sv": ["Gunnars son med Holmdis", "Holmdis dotter, Gunnars styvdotter", "Gunnars far", "ristaren"],
        "en": ["Gunnarr and Holmdís's son", "Holmdís's daughter, Gunnarr's stepdaughter", "Gunnarr's father", "the carver"]}
SUB = {"Jofurfast": 1, "Tord": 0, "Farulv": 2, "Öpir": 3}
for lang in ("sv", "en"):
    fig = plt.figure(figsize=(9.5, 5.2))
    ax = fig.add_axes([0.02, 0.1, 0.96, 0.72]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(len(ROWS) + 0.2, -1.1)
    fig.text(0.01, 0.96, "Vid Harg: fyra stenar, samma föräldrar" if lang == "sv" else "At Harg: four stones, the same parents",
             fontsize=14, fontweight="bold", va="top", color=INK)
    fig.text(0.01, 0.905, ("Vem som står på vilken sten, efter inskrifterna U 312–315 i Skånela socken, Uppland. Stilgrupp under signum."
                           if lang == "sv" else "Who stands on which stone, after the inscriptions U 312–315 in Skånela parish, Uppland. Style group under the signum."),
             fontsize=9, color=MUTED, va="top")
    xs = [4.2, 5.65, 7.1, 8.55]
    for x, s in zip(xs, STONES):
        ax.text(x, -0.75, s, ha="center", fontsize=11, fontweight="bold", color=INK)
        ax.text(x, -0.35, re.sub(r"\s.*", "", ins[s].get("style") or ""), ha="center", fontsize=8.5, color=MUTED)
    for i, (sv, en, _, cells) in enumerate(ROWS):
        y = i + 0.35
        ax.plot([0, 10], [i - 0.12, i - 0.12], color=GRID, linewidth=1)
        name = sv if lang == "sv" else en
        ax.text(0.05, y - 0.05, name, fontsize=11.5, fontweight="bold", color=INK, va="center")
        if name in ("Jofurfast", "Jôfurfast", "Tord", "Þórðr", "Farulv", "Farulfr", "Öpir", "Œpir"):
            k = SUB["Jofurfast" if name in ("Jofurfast", "Jôfurfast") else "Tord" if name in ("Tord", "Þórðr") else "Farulv" if name in ("Farulv", "Farulfr") else "Öpir"]
            ax.text(0.05, y + 0.28, NOTE[lang][k], fontsize=8, color=MUTED, va="center")
        for x, s in zip(xs, STONES):
            r = cells.get(s)
            if not r:
                continue
            c = COL[r]
            ax.add_patch(FancyBboxPatch((x - 0.6, y - 0.27), 1.2, 0.5, boxstyle="round,pad=0.02,rounding_size=0.18",
                                        facecolor=c if r in ("R", "M") else "white", edgecolor=c, linewidth=1.2))
            ax.text(x, y - 0.02, LAB[lang][r], ha="center", va="center", fontsize=9.5, color="white" if r in ("R", "M") else c, fontweight="bold")
    fig.text(0.01, 0.015, "Illustration: Vitki, efter Samnordisk runtextdatabas." if lang == "sv" else "Illustration: Vitki, after the Scandinavian Runic-text Database.",
             fontsize=7.5, color=MUTED)
    fig.savefig(os.path.join(OUT, f"harg_{lang}.png"), dpi=200, facecolor="white")
    plt.close(fig)
print("klar")
