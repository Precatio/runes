"""Figurerna till artikeln "Mild i ord och god på mat" (build_dygder.py): en strofkarta över Hávamál – 164 kolumner, en
per strof, en fylld ruta där ett ämne står – och ett punktdiagram över värdeorden per tusen ord i fyra grupper av
eddadikter, med Hávamál i rost och de andra i grått. Ett ämne per rad; ämnena kommer ur utdata/dygder/havamal_teman.csv
och talen ur utdata/dygder/dygder_edda.json.
    .venv/bin/python utdata/blogg/build/dygder_figurer.py   (sparar PNG i utdata/dygder/ för granskning)"""
import csv
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = os.path.join(ROOT, "utdata", "dygder")
INK, MUTED, RUST, GREY, HAIR = "#1e293b", "#64748b", "#b7410e", "#6b6a66", "#e2e8f0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "xtick.color": INK, "ytick.color": INK})

TEMAN = {int(r["nr"]): r["teman"].split(";") for r in csv.DictReader(open(os.path.join(D, "havamal_teman.csv"), encoding="utf-8"))}
DELAR = {int(r["nr"]): r["del"] for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "Edda", "havamal_strofer.csv"), encoding="utf-8"))}
E = json.load(open(os.path.join(D, "dygder_edda.json"), encoding="utf-8"))["grupper"]

ROWS = ["VÄN", "ORD", "VETT", "GÄST", "MÅTTA", "VAR", "LIV", "HEM", "RYKTE", "GÅVA", "MOD", "OMSORG", "KÄRLEK", "MYT", "RUNOR"]
LBL = {"sv": {"VÄN": "vänskap", "ORD": "ord och tystnad", "VETT": "förstånd", "GÄST": "gästfrihet", "MÅTTA": "måtta",
              "VAR": "försiktighet", "LIV": "livets värde", "HEM": "eget hem, flit", "RYKTE": "rykte, eftermäle",
              "GÅVA": "gåvor", "MOD": "mod och strid", "OMSORG": "omsorg om andra", "KÄRLEK": "kärlek", "MYT": "myt, berättelse",
              "RUNOR": "runor och galdrar"},
       "en": {"VÄN": "friendship", "ORD": "speech and silence", "VETT": "understanding", "GÄST": "hospitality", "MÅTTA": "moderation",
              "VAR": "caution", "LIV": "the value of life", "HEM": "own home, diligence", "RYKTE": "reputation, memory",
              "GÅVA": "gifts", "MOD": "courage and fighting", "OMSORG": "care for others", "KÄRLEK": "love", "MYT": "myth, narrative",
              "RUNOR": "runes and spells"}}
PARTS = [("I", 1, 83, {"sv": "I gästvisdomen", "en": "I guest wisdom"}), ("II", 84, 102, {"sv": "II kvinnor", "en": "II women"}),
         ("III", 103, 110, {"sv": "III\nGunnlöð", "en": "III\nGunnlöð"}), ("IV", 111, 137, {"sv": "IV Loddfáfnismál", "en": "IV Loddfáfnismál"}),
         ("V", 138, 145, {"sv": "V\nRúnatal", "en": "V\nRúnatal"}), ("VI", 146, 164, {"sv": "VI Ljóðatal", "en": "VI Ljóðatal"})]
assert all(DELAR[a] == p and DELAR[b] == p for p, a, b, _ in PARTS)

KAT = ["vänskap", "förstånd", "ord_och_tystnad", "gästfrihet", "gåvor_givmildhet", "måtta", "rykte", "mod", "strid", "hämnd"]
KLBL = {"sv": {"vänskap": "vänskap", "förstånd": "förstånd", "ord_och_tystnad": "ord och tystnad", "gästfrihet": "gästfrihet",
               "gåvor_givmildhet": "gåvor, givmildhet", "måtta": "måtta", "rykte": "rykte", "mod": "mod", "strid": "strid", "hämnd": "hämnd"},
        "en": {"vänskap": "friendship", "förstånd": "understanding", "ord_och_tystnad": "speech and silence", "gästfrihet": "hospitality",
               "gåvor_givmildhet": "gifts, generosity", "måtta": "moderation", "rykte": "reputation", "mod": "courage", "strid": "fighting", "hämnd": "revenge"}}
GRP = [("Hávamál", {"sv": "Hávamál", "en": "Hávamál"}, "o", RUST), ("gudadikter", {"sv": "övriga gudadikter", "en": "other mythological poems"}, "s", GREY),
       ("hjältedikter", {"sv": "hjältedikterna", "en": "the heroic poems"}, "^", GREY), ("kristna", {"sv": "de kristna dikterna", "en": "the Christian poems"}, "D", GREY)]


def _png(fig) -> bytes:
    out = io.BytesIO()
    fig.savefig(out, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out.getvalue()


def strofkarta(lang: str = "sv") -> bytes:
    """One column per stanza, one row per theme; a rust cell where the theme occurs. Part boundaries as hairlines."""
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    n = len(ROWS)
    for i, t in enumerate(ROWS):
        y = n - 1 - i
        for nr in range(1, 165):
            if t in TEMAN[nr]:
                ax.add_patch(Rectangle((nr - 0.5 + 0.08, y + 0.1), 0.84, 0.8, color=RUST, lw=0))
        tot = sum(t in TEMAN[nr] for nr in range(1, 165))
        ax.text(166.5, y + 0.5, str(tot), va="center", ha="left", fontsize=9, color=MUTED)
    for _, a, b, name in PARTS:
        if a > 1:
            ax.plot([a - 0.5, a - 0.5], [0, n + 0.9], color=MUTED, lw=1, zorder=0)
        ax.text((a + b) / 2, n + 0.55, name[lang], ha="center", va="center", fontsize=8.5 if b - a > 12 else 7.2, color=MUTED)
    ax.set_xlim(0.5, 172)
    ax.set_ylim(0, n + 1.1)
    ax.set_yticks([n - 1 - i + 0.5 for i in range(n)])
    ax.set_yticklabels([LBL[lang][t] for t in ROWS], fontsize=9.5)
    ax.set_xticks([1, 20, 40, 60, 80, 100, 120, 140, 164])
    ax.tick_params(length=0)
    ax.set_xlabel("strof" if lang == "sv" else "stanza", color=MUTED, fontsize=9.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(HAIR)
    ax.text(166.5, n + 0.55, "strofer" if lang == "sv" else "stanzas", ha="left", va="center", fontsize=8.5, color=MUTED)
    return _png(fig)


def punktdiagram(lang: str = "sv") -> bytes:
    """Value words per thousand words: ten categories, four groups; Hávamál in rust, the rest in grey shapes."""
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    n = len(KAT)
    for i, k in enumerate(KAT):
        y = n - 1 - i
        vals = [E[g][k] for g, _, _, _ in GRP]
        ax.plot([min(vals), max(vals)], [y, y], color=HAIR, lw=1.5, zorder=1, solid_capstyle="round")
        for (g, _, mk, col), v in zip(GRP, vals, strict=True):
            ax.plot(v, y, marker=mk, ms=9 if col == RUST else 7.5, color=col, mec="white", mew=1.6, ls="", zorder=3 if col == RUST else 2)
    # direct labels, sparingly: the three largest Hávamál values and the two where the heroic poems lead
    for k, g, dx in (("förstånd", "Hávamál", 0.25), ("vänskap", "Hávamál", 0.25), ("gästfrihet", "Hávamál", 0.25),
                     ("strid", "hjältedikter", 0.25), ("hämnd", "hjältedikter", 0.25)):
        y = n - 1 - KAT.index(k)
        v = E[g][k]
        ax.text(v + dx, y + 0.02, f"{v:.1f}".replace(".", "," if lang == "sv" else "."), va="center", ha="left", fontsize=9, color=INK)
    ax.set_yticks(range(n))
    ax.set_yticklabels([KLBL[lang][k] for k in reversed(KAT)], fontsize=9.5)
    ax.set_xlim(-0.3, 12.5)
    ax.set_xlabel("per tusen ord" if lang == "sv" else "per thousand words", color=MUTED, fontsize=9.5)
    ax.grid(axis="x", color=HAIR, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(HAIR)
    ax.legend([Line2D([], [], marker=mk, ls="", color=col, mec="white", mew=1.2, ms=9 if col == RUST else 7.5) for _, _, mk, col in GRP],
              [name[lang] for _, name, _, _ in GRP], loc="lower right", frameon=False, fontsize=9, ncol=2)
    return _png(fig)


if __name__ == "__main__":
    for lang in ("sv", "en"):
        open(os.path.join(D, f"fig_strofkarta_{lang}.png"), "wb").write(strofkarta(lang))
        open(os.path.join(D, f"fig_punkter_{lang}.png"), "wb").write(punktdiagram(lang))
    print("sparade fyra figurer i", D)
