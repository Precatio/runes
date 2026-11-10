"""Beskrivande tidskurva (planens P2): östandel per stilgrupp med och utan Ingvarsstenarna → tidskurva.png.
    ../../../.venv/bin/python kurva.py"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, "resultat.json"), encoding="utf-8"))["kurva"]
INK, MUTED, GRID, SURF = "#222222", "#6b6b6b", "#e6e6e3", "#fcfcfb"
SERIES = [("med_ingvar", "Alla stenar", "#b7410e", -0.12, "o"), ("utan_ingvar", "Utan Ingvarsstenarna", "#1f74a8", 0.12, "s")]

fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
fig.patch.set_facecolor(SURF)
ax.set_facecolor(SURF)
groups = [g["stil"] for g in res["med_ingvar"]]
for key, label, col, dx, mk in SERIES:
    for i, g in enumerate(res[key]):
        if g["ostandel"] is None:
            continue
        x = i + dx
        if g["ci"]:
            ax.plot([x, x], [100 * g["ci"][0], 100 * g["ci"][1]], color=col, lw=2, solid_capstyle="round", alpha=0.55)
        ax.plot(x, 100 * g["ostandel"], mk, color=col, ms=8, mec=SURF, mew=2,
                label=label if i == 0 else None)
ax.axhline(50, color=MUTED, lw=1, ls=(0, (3, 3)))
ax.text(len(groups) - 0.5, 51, "hälften", color=MUTED, fontsize=8, ha="right", va="bottom")
ticks = [f"{g['stil']}\n{g['ar'][0]}–{g['ar'][1]}\n{g['stenar']} st." for g in res["med_ingvar"]]
ax.set_xticks(range(len(groups)), ticks, fontsize=8, color=INK)
ax.set_ylim(0, 105)
ax.set_ylabel("Östandel av platserna (%)", color=INK, fontsize=9)
ax.grid(axis="y", color=GRID, lw=0.8)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(GRID)
ax.tick_params(colors=MUTED, labelsize=8)
ax.legend(frameon=False, fontsize=8, loc="lower right", labelcolor=INK)
ax.set_title("Östandel per stilgrupp (svenska runstenar, säker stilgrupp)", color=INK, fontsize=10, loc="left")
fig.text(0.01, 0.01, "Linje = 95 %-intervall (bara grupper med minst 10 platser). Antal stenar avser alla stenar. "
         "Diagram: Vitki, efter Rundata och Gräslunds stildatering.", fontsize=7, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(os.path.join(HERE, "tidskurva.png"), facecolor=SURF)
print("tidskurva.png")
