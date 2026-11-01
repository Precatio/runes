"""Två illustrationer till publicerade artiklar (Viktor 2026-11-01), på svenska och engelska; varje bild säger att Vitki
gjort den. (1) "Hur bra är vår sannolikhetsmodell egentligen?": två ord ur maskeringsprovet med appens inställning
(utdata/runlm_forfining/app_f0–4.json, svenska runstenar, helt ord på minst fyra runor som står en gång i stenens text),
det första säkra rätta svaret och det första där modellens bästa förslag har under 50 procent, i signumordning.
(2) "Hon ärvde efter sitt barn": arvsgången på Hillersjöhällen (U 29), strikt efter Rundatas översättning.
    PYTHONPATH=. .venv/bin/python utdata/blogg/artikelfigurer/artikelfigurer.py"""
import json
import os
import re
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

INK, MUTED, GRID, ACCENT, BLUE = "#1e293b", "#64748b", "#e2e8f0", "#b7410e", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK})
ins = {x["signum"]: x for x in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
RES = {}
T = lambda lang, sv, en: sv if lang == "sv" else en  # noqa: E731
tok = lambda t: re.sub(r"[^\wæøåäöþðǫ]", "", t.lower())  # noqa: E731


def save(fig, name, lang, credit):
    fig.text(0.01, 0.012, credit, ha="left", va="bottom", fontsize=7.5, color=MUTED)
    fig.savefig(os.path.join(OUT, f"{name}_{lang}.png"), dpi=200, facecolor="white")
    plt.close(fig)


# ---- 1. Maskeringsprovet ---------------------------------------------------------------------------------------------
def modell():
    R = tm._records()
    by, G = R["by"], R["G"]
    rows = [x for k in range(5) for x in json.load(open(os.path.join(ROOT, "utdata", "runlm_forfining", f"app_f{k}.json")))["rows"]
            if rl.object_kind(by[x["sig"]]) == "runsten" and x["sig"].split(" ")[0] in SE and x["kind"] == "helt ord"]
    once = lambda x: [tok(t) for t in (ins[x["sig"]].get("normalization") or "").split()].count(x["word"].lower()) == 1  # noqa: E731
    q = lambda x: tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, True)  # noqa: E731
    pool = sorted((x for x in rows if x["n"] >= 4 and once(x)), key=lambda x: x["sig"])
    sure = next(x for x in pool if x["word_ok"] and q(x) >= 0.95)
    unsure = next(x for x in pool if x["words"] and x["words"][0][1] < 0.5)
    assert (sure["sig"], sure["word"], unsure["sig"], unsure["word"]) == ("Sm 134", "æftiR", "Sm 64", "satti")
    RES["modell"] = {k: {"sig": x["sig"], "word": x["word"], "n": x["n"], "ok": x["word_ok"], "q": q(x), "top3": x["words"][:3]}
                     for k, x in (("sure", sure), ("unsure", unsure))}

    def context(x):
        toks = [t.replace('"', "") for t in ins[x["sig"]]["normalization"].split()]
        i = next(k for k, t in enumerate(toks) if tok(t) == x["word"].lower())
        a, b = max(0, i - 5), min(len(toks), i + 6)
        return (("… " if a else "") + " ".join(toks[a:i]), " ".join(toks[i + 1:b]) + (" …" if b < len(toks) else ""))

    for lang in ("sv", "en"):
        fig = plt.figure(figsize=(10, 5.6))
        fig.text(0.01, 0.97, T(lang, "Så mäter vi: ett ord döljs, och modellen gissar utan att ha sett stenen",
                               "How we measure: a word is hidden, and the model guesses without having seen the stone"),
                 fontsize=13, fontweight="bold", va="top")
        fig.text(0.01, 0.915, T(lang, "Två ord ur provet, valda efter en regel: det första säkra svaret och det första där inget förslag når 50 procent.",
                                "Two words from the test, chosen by a rule: the first sure answer and the first where no proposal reaches 50 per cent."),
                 fontsize=9, color=MUTED, va="top")
        for col, (kind, x) in enumerate((("sure", sure), ("unsure", unsure))):
            x0 = 0.03 + col * 0.5
            before, after = context(x)
            head = T(lang, f"{x['sig']}: ett säkert svar", f"{x['sig']}: a sure answer") if kind == "sure" else \
                T(lang, f"{x['sig']}: ett osäkert svar", f"{x['sig']}: an unsure answer")
            fig.text(x0, 0.84, head, fontsize=11.5, fontweight="bold", va="top")
            fig.text(x0, 0.79, T(lang, "Vad modellen ser (Rundatas normaliserade text):", "What the model sees (Rundata's normalized text):"),
                     fontsize=8.5, color=MUTED, va="top")
            line = f"{before} [{'?' * x['n']}] {after}"
            fig.text(x0, 0.75, "\n".join(textwrap.wrap(line, 52)), fontsize=10, va="top", style="italic", linespacing=1.4)
            ax = fig.add_axes([x0 + 0.09, 0.2, 0.33, 0.3])
            top = x["words"][:3][::-1]
            ys = range(len(top))
            ax.barh(ys, [p for _, p, _ in top], color=[ACCENT if ok else "#cbd5e1" for _, _, ok in top], height=0.6)
            ax.set_yticks(list(ys)); ax.set_yticklabels([w for w, _, _ in top], fontsize=10, style="italic")
            ax.set_xlim(0, 1); ax.set_xticks([0, 0.25, 0.5, 0.75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100 %"], fontsize=8)
            for sp in ("top", "right"):
                ax.spines[sp].set_visible(False)
            for y, (w, p, ok) in zip(ys, top):
                pct = (f"{100 * p:.1f}" if p >= 0.995 else f"{round(100 * p)}").replace(".", "," if lang == "sv" else ".")
            ax.text(p + 0.02, y, f"{pct} %" + (T(lang, "  ← rätt ord", "  ← right word") if ok else ""),
                        va="center", fontsize=9, color=ACCENT if ok else MUTED)
            ax.set_title(T(lang, "modellens tre främsta förslag", "the model's three top proposals"), fontsize=9, color=MUTED, loc="left")
            note = (T(lang, f"Efter kalibrering {round(100 * q(x))} %: modellen kallar svaret säkert, och det är rätt.",
                      f"After calibration {round(100 * q(x))} %: the model calls the answer sure, and it is right.") if kind == "sure" else
                    T(lang, "Tre förslag nästan lika: modellen säger själv att den inte vet.",
                      "Three proposals almost equal: the model itself says it does not know."))
            fig.text(x0, 0.1, note, fontsize=9.5, va="top")
        save(fig, "modell_prov", lang, T(lang, "Illustration: Vitki, ur Vitkis maskeringsprov med appens inställning på Samnordisk runtextdatabas; stenen ingår aldrig i den modell som gissar.",
                                         "Illustration: Vitki, from Vitki's masking test with the app's settings on the Scandinavian Runic-text Database; the stone is never part of the model that guesses."))


# ---- 2. Hillersjöhällen ------------------------------------------------------------------------------------------------
def hillersjo():
    r = ins["U 29"]
    en = r["translation_en"]
    for frag in ("Geirmundr got Geirlaug", "before he (= Geirmundr) drowned", "And then the son died", "Then she got Guðríkr",
                 "And one maid lived; she was called Inga", "Ragnfastr of Snotastaðir got her", "Then he died, and thereafter the son",
                 "the mother came to inherit from her son", "Then she got Eiríkr", "Then she died",
                 "Geirlaug came to inherit from Inga, her daughter"):
        assert frag in en, frag      # schemat säger inget som inte står i inskriften
    RES["hillersjo"] = {"translation_en": en}
    N = {"sv": {"GM": "Germund", "GL": "Gerlög", "GU": "Gudrik", "IN": "Inga", "RF": "Ragnfast\ni Snottsta", "ER": "Erik"},
         "en": {"GM": "Geirmundr", "GL": "Geirlaug", "GU": "Guðríkr", "IN": "Inga", "RF": "Ragnfastr\nof Snotastaðir", "ER": "Eiríkr"}}
    for lang in ("sv", "en"):
        n = N[lang]
        fig = plt.figure(figsize=(10, 6.4))
        ax = fig.add_axes([0.02, 0.06, 0.96, 0.8]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6.2)
        fig.text(0.01, 0.97, T(lang, "Hillersjöhällen (U 29): arvet gick från sonen till Inga och från Inga till hennes mor",
                               "The Hillersjö rock (U 29): the inheritance went from the son to Inga and from Inga to her mother"),
                 fontsize=12.5, fontweight="bold", va="top")
        fig.text(0.01, 0.925, T(lang, "Allt i schemat står i inskriften. † = dog enligt inskriften. Röda pilar: den ärvde, med inskriftens egna ord.",
                                "Everything in the chart is in the inscription. † = died according to the inscription. Red arrows: who inherited, in the inscription's own words."),
                 fontsize=9, color=MUTED, va="top")

        def box(x, y, text, w=1.6, h=0.62, strong=False):
            ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                                        facecolor="#fdf3ee" if strong else "#f8fafc", edgecolor=ACCENT if strong else "#94a3b8", linewidth=1.4 if strong else 1))
            ax.text(x, y, text, ha="center", va="center", fontsize=10, fontweight="bold" if strong else "normal")

        def line(x1, y1, x2, y2, **kw):
            ax.plot([x1, x2], [y1, y2], color=kw.pop("color", "#94a3b8"), linewidth=kw.pop("lw", 1.2), **kw)

        # generation 1: Germund – Gerlög – Gudrik
        box(1.5, 5.3, n["GM"] + " †"); box(5.0, 5.3, n["GL"], strong=True); box(8.5, 5.3, n["GU"])
        line(2.3, 5.3, 4.2, 5.3); line(5.8, 5.3, 7.7, 5.3)
        ax.text(3.25, 5.45, T(lang, "1. gift", "1st marriage"), ha="center", fontsize=8.5, color=MUTED)
        ax.text(6.75, 5.45, T(lang, "2. gift", "2nd marriage"), ha="center", fontsize=8.5, color=MUTED)
        ax.text(1.5, 4.72, T(lang, "drunknade", "drowned"), ha="center", fontsize=8.5, color=MUTED, va="top")
        # children
        line(2.7, 5.3, 2.7, 4.25); box(2.7, 3.95, T(lang, "en son †", "a son †"))
        line(6.75, 5.3, 6.75, 4.25)
        ax.text(6.9, 4.55, T(lang, "barn; bara en dotter levde", "children; only one daughter lived"), fontsize=8.5, color=MUTED)
        box(6.75, 3.95, n["IN"] + " †", strong=True)
        # Inga's marriages
        box(4.0, 2.4, n["RF"] + " †", w=2.0, h=0.8); box(9.0, 2.4, n["ER"])
        line(6.0, 3.85, 4.9, 2.6); line(7.55, 3.85, 8.4, 2.6)
        ax.text(5.15, 3.3, T(lang, "gift", "married"), fontsize=8.5, color=MUTED, ha="right")
        ax.text(8.15, 3.3, T(lang, "gift sedan", "married later"), fontsize=8.5, color=MUTED)
        line(4.0, 2.0, 4.0, 1.2); box(4.0, 0.9, T(lang, "en son †", "a son †"))
        ax.text(4.15, 1.55, T(lang, "dog efter fadern", "died after his father"), fontsize=8.5, color=MUTED)
        # the inheritance
        ax.add_patch(FancyArrowPatch((4.85, 0.95), (6.45, 3.6), arrowstyle="-|>", mutation_scale=18, color=ACCENT, linewidth=2.2,
                                     connectionstyle="arc3,rad=0.25"))
        ax.text(6.15, 1.55, T(lang, "”modern kom att\närva efter sin son”", "“the mother came to\ninherit from her son”"),
                fontsize=9.5, color=ACCENT, style="italic")
        ax.add_patch(FancyArrowPatch((6.75, 4.3), (5.25, 4.95), arrowstyle="-|>", mutation_scale=18, color=ACCENT, linewidth=2.2,
                                     connectionstyle="arc3,rad=-0.3"))
        ax.text(5.05, 4.4, T(lang, "”Gerlög kom att ärva\nefter Inga, sin dotter”", "“Geirlaug came to inherit\nfrom Inga, her daughter”"),
                fontsize=9.5, color=ACCENT, style="italic", ha="right")
        save(fig, "hillersjo", lang, T(lang, "Illustration: Vitki, efter inskriften U 29 i Samnordisk runtextdatabas (Rundatas översättning). Ristare: Torbjörn skald.",
                                       "Illustration: Vitki, after the inscription U 29 in the Scandinavian Runic-text Database (Rundata's translation). Carver: Þorbjôrn Skald."))


if __name__ == "__main__":
    modell()
    hillersjo()
    json.dump(RES, open(os.path.join(OUT, "artikelfigurer.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in RES.items() if k == "modell"}, ensure_ascii=False)[:400])
