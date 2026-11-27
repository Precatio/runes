"""Artikeln om korset på runstenarna (sv + en): de stenar som försvann efter att de tecknats på 1600- och 1700-talen
hade mer sällan kors än de som står kvar, och korset varierar mellan härader utöver stil och landskap.

Bygger på två låsta studier från 2026-11-26:
- "Vad försvann?" – analysplaner/2026-11-26-vad-forsvann.md, utdata/vad_forsvann/resultat.json (+ data.csv);
- "Lokala ornamenttraditioner" – analysplaner/2026-11-26-lokala-ornamenttraditioner.md,
  utdata/lokala_traditioner/resultat.json (+ data.csv).
Bakgrund: ornamentregistret (utdata/nya_ristare/resultat.md §§ 10–14, ornamentik/kodbok.md, kallkontroll.json,
m2_utveckling.json) och det bekräftande provet i utdata/graslund/skrev_ritade.md (budskap_bild.json).
Varje tal räknas här ur utfallsfilerna och låses med assert. "Extra orm" är ett modellfel och redovisas inte som fynd.

Figurer (ritas här, sv + en, i utdata/blogg/figurer/korset/):
1. Bautils träsnitt nr 496 (U 1038, Altomta, Tensta sn – förlorad, med kors) utskuret ur sidbilden i Umeå
   universitetsbiblioteks exemplar ("fritt från kända upphovsrättsliga restriktioner") med registrets koder bredvid.
   OBS: cachens utsnitt data/cache/hander/plansch/teckningar/U_1038_bautil_496.jpg visar grannträsnitten nr 493–494,
   inte nr 496, så här skärs nr 496 ut direkt ur sidan 0168.jpg (kontrollerat för ögat 2026-11-27).
2. Diagram: andelarna kors, rundjur och utarbetad ornamentik bland förlorade och bevarade stenar (Vitki).
3. :::chart med korsandelen i de härader som avviker mest.
SRI:s planscher är skyddade och visas aldrig.
    ../../../.venv/bin/python build_korset.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import math
import os
import re
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402

J = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))  # noqa: E731
T = lambda *p: re.sub(r"\s+", " ", open(os.path.join(*p), encoding="utf-8").read())  # noqa: E731  (radbrytningar → mellanslag)


def pc(x):
    """Procent avrundat (halvor uppåt)."""
    return int(100 * x + 0.5)


def kv(x, sv=True, d=2):
    s = f"{x:.{d}f}".replace("-", "−")
    return s.replace(".", ",") if sv else s


# ---- studie 1: vad försvann? -----------------------------------------------------------------------------------------
VF = J(ROOT, "utdata", "vad_forsvann", "resultat.json")
assert VF["plan"] == "2026-11-26-vad-forsvann.md"
H = VF["huvudprov"]
U1, U2, U3 = H["U1"], H["U2"], H["U3"]
assert all(H[k]["metod"] == "glmer" for k in H)
assert (pc(U2["andel_forlorade"]), pc(U2["andel_bevarade"]), U2["n_forlorade"], U2["n_bevarade"]) == (44, 62, 157, 114)
assert (kv(U2["or"]), kv(U2["ci"][0]), kv(U2["ci"][1]), round(U2["p_holm"], 3)) == ("0,39", "0,21", "0,73", 0.009)
assert U2["skiljer"] and U2["p_holm"] < 0.01  # "färre än en gång på hundra"
assert (pc(U1["andel_forlorade"]), pc(U1["andel_bevarade"]), pc(U3["andel_forlorade"]), pc(U3["andel_bevarade"])) == (56, 73, 41, 57)
assert round(U1["p_holm"], 3) == round(U3["p_holm"], 3) == 0.054 and not U1["skiljer"] and not U3["skiljer"]
UP = VF["uppland"]["U2"]
assert (pc(UP["andel_forlorade"]), pc(UP["andel_bevarade"])) == (45, 65)
BF = VF["beskrivande_foto"]["U2"]
assert (pc(BF["forlorade_teckning"]), pc(BF["bevarade_foto"])) == (44, 65)
# per tecknare (kors), räknat på nytt ur data.csv och jämfört med per_typ i resultat.json
VD = pd.read_csv(os.path.join(ROOT, "utdata", "vad_forsvann", "data.csv"))
N_LOST, N_KEPT = int((VD.forlorad == 1).sum()), int((VD.forlorad == 0).sum())
assert (N_LOST, N_KEPT) == (185, 125)
KT = VD[VD.U2.notna()].groupby(["typ", "forlorad"]).U2.agg(["mean", "count"])
for typ, idx in (("Bautil", "Bautil"), ("Peringskiöld", "Peringskiöld"), ("Rhezelius", "Rhezelius"), ("övrig", "övrig")):
    assert abs(KT.loc[(idx, 1), "mean"] - VF["per_typ"][typ][0][1]) < 1e-4 and abs(KT.loc[(idx, 0), "mean"] - VF["per_typ"][typ][1][1]) < 1e-4
BAU = (pc(KT.loc[("Bautil", 1), "mean"]), pc(KT.loc[("Bautil", 0), "mean"]), int(KT.loc[("Bautil", 1), "count"]), int(KT.loc[("Bautil", 0), "count"]))
PER = (pc(KT.loc[("Peringskiöld", 1), "mean"]), pc(KT.loc[("Peringskiöld", 0), "mean"]))
RHE = (pc(KT.loc[("Rhezelius", 1), "mean"]), pc(KT.loc[("Rhezelius", 0), "mean"]))
OVR = (pc(KT.loc[("övrig", 1), "mean"]), pc(KT.loc[("övrig", 0), "mean"]))
assert BAU == (41, 76, 116, 34) and PER == (48, 59) and RHE == (55, 53) and OVR == (56, 57)
VF_MD = T(ROOT, "utdata", "vad_forsvann", "resultat.md")
assert "Tiden kunde inte hållas konstant" in VF_MD and "Varför stenarna försvann vet vi inte" in VF_MD
assert "byggnadssten" in VF_MD and "teckningarna själva kan vara ett urval" in VF_MD
VF_PLAN = T(ROOT, "analysplaner", "2026-11-26-vad-forsvann.md")
assert "Skriven och låst 2026-11-26" in VF_PLAN and "(1 | socken)" in VF_PLAN and "Holm-justerat över U1–U3" in VF_PLAN

CORP = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"),
                   low_memory=False).drop_duplicates("signum").set_index("signum")
N_FORLORADE_KORPUS = int((CORP["lost"] == 1).sum())
assert N_FORLORADE_KORPUS == 415
FL = J(ROOT, "data", "cache", "hander", "ornamentik", "orn_koder_forlorade.json")
assert len(FL) == 185 and sum(1 for v in FL.values() if v["källa"] == "Bautil") == 135
N_UTAN_STIL = int(CORP.loc[list(FL), "style"].isna().sum())
assert N_UTAN_STIL == 135

# ---- studie 2: lokala ornamenttraditioner ---------------------------------------------------------------------------
LT = J(ROOT, "utdata", "lokala_traditioner", "resultat.json")
assert LT["plan"] == "2026-11-26-lokala-ornamenttraditioner.md" and (LT["stenar"], LT["harader"]) == (620, 98)
O = LT["ornamentik"]
D6 = O["D6"]
assert D6["lokal_tradition"] and (D6["n"], D6["harader"]) == (534, 95) and kv(D6["icc"]) == "0,11"
assert round(D6["p_holm"], 4) == 0.0045 and D6["p_holm"] < 1 / 200  # "färre än en gång på 200"
assert D6["icc_95"][0] < 0.01 and kv(D6["icc_95"][1]) == "0,18"
AV = D6["avvikande_harader"]
assert list(AV) == ["Trögds hd", "Åsunda hd", "Norunda hd", "Lyhundra hd", "Håbo hd"]
assert [round(math.exp(AV[h]), 2) for h in ("Trögds hd", "Norunda hd", "Håbo hd")] == [0.26, 2.39, 2.08]  # "en fjärdedel", "mer än dubbelt", "ungefär dubbelt"
# ordinarie modell: D5 (extra orm) är degenererad enligt resultat.md och redovisas inte som fynd
LT_MD = T(ROOT, "utdata", "lokala_traditioner", "resultat.md")
assert "**Modellen är dock degenererad**" in LT_MD and "Det formella utslaget är en effekt av modellen och räknas inte." in LT_MD
assert "Kors:** häradets varians 0,41 i båda modellformerna" in LT_MD
D1 = O["D1"]
assert kv(D1["icc"]) == "0,30" and not D1["lokal_tradition"] and round(D1["p_holm"], 2) == 0.10
assert all(O[k]["provad"] for k in O) and [k for k in O if O[k]["lokal_tradition"]] == ["D5", "D6"]
assert O["D2"]["icc"] < 0.001 and O["D7"]["icc"] < 0.001 and kv(O["D3"]["icc"]) == "0,02"  # vy, antal djur, öga
assert not O["D4"]["lokal_tradition"] and not O["D8"]["lokal_tradition"]
SP = LT["sprakdrag_jamforelse"]
assert len(SP) == 6 and min(v["icc"] for v in SP.values()) < 0.001 and kv(max(v["icc"] for v in SP.values())) == "0,07"
# häradernas råa andelar (beskrivande), ur data.csv
LD = pd.read_csv(os.path.join(ROOT, "utdata", "lokala_traditioner", "data.csv"))
LK = LD[LD.D6.notna()]
assert len(LK) == D6["n"] and LK.harad.nunique() == D6["harader"] and pc(LK.D6.mean()) == 59
HR = {h: (int(LK[LK.harad == h].D6.sum()), int((LK.harad == h).sum())) for h in AV}
assert HR == {"Trögds hd": (4, 17), "Åsunda hd": (7, 17), "Norunda hd": (19, 21), "Lyhundra hd": (3, 10), "Håbo hd": (19, 21)}
assert all(set(LK[LK.harad == h].landskap) == {"U"} for h in AV)  # alla i Uppland: skillnaden ligger inom landskapet
LT_PLAN = T(ROOT, "analysplaner", "2026-11-26-lokala-ornamenttraditioner.md")
assert "Skriven och låst 2026-11-26" in LT_PLAN and "En lokal tradition betyder inte en enda verkstad" in LT_PLAN

# ---- ornamentregistret: korset som kod --------------------------------------------------------------------------------
ORN = os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik")
KODBOK = T(ORN, "kodbok.md")
assert "`kors` – finns ett kors? `ja` / `nej`." in KODBOK and "koda den yta som bär det största rundjuret" in KODBOK
M2 = J(ORN, "m2_utveckling.json")
assert kv(M2["fält"]["kors"]["kappa"]) == "0,99"
KK = J(ORN, "kallkontroll.json")
KTP = KK["teckning_mot_plansch"]
assert (KTP["alla"]["kors"]["jämförbara"], pc(KTP["alla"]["kors"]["lika"]), kv(KTP["alla"]["kors"]["kappa"])) == (103, 91, "0,81")
assert (KTP["bautil"]["kors"]["jämförbara"], round(KTP["bautil"]["kors"]["lika"] * 30), kv(KTP["bautil"]["kors"]["kappa"])) == (30, 29, "0,90")
assert all("kors" in v for v in KK["fält_som_får_läsas"].values())
RES = T(ROOT, "utdata", "nya_ristare", "resultat.md")
assert "två oberoende läsare per sten (Claude Opus)" in RES and "1 170 stenar som är avbildade på SRI:s planscher" in RES
# bekräftande provet (Gräslundsspåret)
BB = J(ROOT, "utdata", "graslund", "budskap_bild.json")
assert BB["stenar"] == 442 and BB["B1"]["håller"] and round(BB["B1"]["rho"], 3) == 0.227
SR = T(ROOT, "utdata", "graslund", "skrev_ritade.md")
assert "Ornamentiken utan fältet \"kors\":** budskapet ger ρ = 0,062" in SR
assert "En text med religiösa (kristna) markörer går ihop med ett kors i bilden" in SR
assert 0.062 / BB["B1"]["rho"] < 0.3  # "föll till ungefär en fjärdedel"

# ---- U 1038: stenen i träsnittet -------------------------------------------------------------------------------------
TECK = J(ROOT, "data", "cache", "hander", "plansch", "teckningar.json")
B496 = [x for x in TECK["U 1038"] if x.get("återgiven_i") == "Bautil (Umeå UB)"][0]
assert B496["bautil_nr"] == 496 and B496["förlorad"] and B496["bautil_sida"] == 168
assert B496["sidbild"].endswith("bautil_umu/0168.jpg")
R1038 = CORP.loc["U 1038"]
assert (R1038["lost"], R1038["cross"], R1038["place"], R1038["parish"], R1038["district"]) == (1, 1, "Altomta", "Tensta sn", "Norunda hd")
NORM = R1038["normalization"].replace('"', "")
assert NORM == "Heðinbiorn let ræisa stæin at Ala/Alla, broður sinn ... <hia>"
QUOTE = "Heðinbiorn let ræisa stæin at Ala/Alla, broður sinn …"
C1038 = FL["U 1038"]
assert C1038["källa"] == "Bautil" and C1038["koder"]["kors"] == "ja"
assert C1038["koder"] == {"djurhuvud": "ja", "antal_djur": "1", "huvud_vy": "profil", "oga": "mandel", "flatverk": "attor",
                          "fyrfota": "nej", "kors": "ja"}
assert int(VD[VD.signum == "U 1038"].U2.iloc[0]) == 1  # stenen ingår i huvudprovet, med kors

# ---- figurerna -----------------------------------------------------------------------------------------------------------
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

RUST, BLUE, INK, MUTED = "#b7410e", "#0a7fa8", "#1f1d1a", "#77706a"  # paletten prövad med dataviz-validatorn (ljust läge)
FIGDIR = os.path.join(ROOT, "utdata", "blogg", "figurer", "korset")
FIELD = {"djurhuvud": ("Djurhuvud", "Animal head"), "antal_djur": ("Antal djur", "Number of animals"),
         "huvud_vy": ("Huvudets vy", "Head view"), "oga": ("Öga", "Eye"), "flatverk": ("Flätverk", "Interlace"),
         "fyrfota": ("Fyrfota djur", "Quadruped"), "kors": ("Kors", "Cross")}
VAL = {"ja": ("ja", "yes"), "nej": ("nej", "no"), "profil": ("profil", "profile"), "mandel": ("mandel", "almond"),
       "attor": ("åttor", "figures of eight"), "1": ("1", "1")}
CROP = (40, 2632, 1160, 4180)  # nr 496 på sidan 139 (bildfil 0168.jpg), utan rubriken "Norunda Hundari" ovanför


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, metadata={"Software": None})
    plt.close(fig)
    return buf.getvalue()


def fig_altomta(sv):
    i = 0 if sv else 1
    page = Image.open(B496["sidbild"]).convert("RGB")
    assert page.size == (3270, 4725)
    im = page.crop(CROP)
    fig = plt.figure(figsize=(13, 10.2), facecolor="white")
    a0 = fig.add_axes([0.01, 0.12, 0.54, 0.84])
    a0.imshow(im)
    a0.set_axis_off()
    a0.set_title("Bautil nr 496 – U 1038, Altomta" if sv else "Bautil no. 496 – U 1038, Altomta", fontsize=14, color=INK, loc="left")
    at = fig.add_axes([0.58, 0.12, 0.41, 0.84])
    at.set_axis_off()
    at.set_xlim(0, 1), at.set_ylim(0, 1)
    y = 0.95
    at.text(0, y, "Vitkis ornamentregister" if sv else "Vitki's ornament register", fontsize=15, fontweight="bold", color=INK, va="top")
    y -= 0.06
    at.text(0, y, ("U 1038, Tensta socken, Norunda härad.\nStenen är förlorad; koderna kommer ur träsnittet." if sv else
                   "U 1038, Tensta parish, Norunda hundred.\nThe stone is lost; the codes come from the woodcut."),
            fontsize=12, color=MUTED, va="top", linespacing=1.4)
    y -= 0.15
    at.plot([0, 1], [y + 0.02, y + 0.02], color=INK, lw=1)
    for f in ("djurhuvud", "antal_djur", "huvud_vy", "oga", "flatverk", "fyrfota", "kors"):
        hit = f == "kors"
        col = RUST if hit else INK
        at.text(0, y, FIELD[f][i], fontsize=13.5, color=col, va="top", fontweight="bold" if hit else "normal")
        at.text(0.55, y, VAL[C1038["koder"][f]][i], fontsize=13.5, color=col, va="top", fontweight="bold" if hit else "normal")
        y -= 0.058
    at.plot([0, 1], [y + 0.02, y + 0.02], color=INK, lw=1)
    y -= 0.02
    at.text(0, y, ("Ett värde står bara där två oberoende läsare\ngav samma svar. Läppflik och fötter läses\naldrig ur teckningar."
                   if sv else "A value is given only where two independent\nreaders gave the same answer. Lip lappet and\nfeet are never read from drawings."),
            fontsize=11.5, color=MUTED, va="top", linespacing=1.4)
    fig.text(0.01, 0.025, ("Figur: Vitki. Koderna ur Vitkis ornamentregister, lästa av två oberoende läsare (Anthropics språkmodell Claude, Claude Opus).\n"
                           "Träsnitt: J. Göransson, Bautil (1750) nr 496, Umeå universitetsbiblioteks exemplar, fritt från kända upphovsrättsliga restriktioner.")
             if sv else
             ("Figure: Vitki. Codes from Vitki's ornament register, read by two independent readers (Anthropic's language model Claude, Claude Opus).\n"
              "Woodcut: J. Göransson, Bautil (1750) no. 496, Umeå University Library copy, free of known copyright restrictions."),
             fontsize=10, color=MUTED, va="bottom")
    return _png(fig)


def fig_andelar(sv):
    rows = [("U2", ("Kors", "Cross"), True), ("U1", ("Rundjur (djurhuvud)", "Rune animal (animal head)"), False),
            ("U3", ("Utarbetad ornamentik", "Elaborate ornament"), False)]
    fig, ax = plt.subplots(figsize=(12, 5.6), facecolor="white")
    fig.subplots_adjust(left=0.25, right=0.80, top=0.80, bottom=0.25)
    for k, (key, lab, sure) in enumerate(rows):
        yy = len(rows) - 1 - k
        a, b = 100 * H[key]["andel_forlorade"], 100 * H[key]["andel_bevarade"]
        ax.plot([a, b], [yy, yy], color="#c9c4bd", lw=2, zorder=1)
        ax.scatter([a], [yy], s=170, color=RUST, zorder=3, edgecolor="white", linewidth=2)
        ax.scatter([b], [yy], s=170, color=BLUE, zorder=3, edgecolor="white", linewidth=2)
        ax.text(a - 2.2, yy + 0.2, f"{pc(H[key]['andel_forlorade'])} %", ha="right", va="bottom", fontsize=12, color=INK)
        ax.text(b + 2.2, yy + 0.2, f"{pc(H[key]['andel_bevarade'])} %", ha="left", va="bottom", fontsize=12, color=INK)
        ax.text(-3, yy, lab[0 if sv else 1], ha="right", va="center", fontsize=13, color=INK,
                fontweight="bold" if sure else "normal", transform=ax.transData, clip_on=False)
        note = (("säker skillnad", "certain difference") if sure else ("inte säker efter\njusteringen", "not certain after\nthe adjustment"))
        ax.text(101, yy, note[0 if sv else 1], ha="left", va="center", fontsize=11.5, color=RUST if sure else MUTED, clip_on=False)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels([f"{t} %" for t in (0, 25, 50, 75, 100)], fontsize=11, color=MUTED)
    ax.grid(axis="x", color="#ebe7e2", lw=1)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c4bd")
    fig.text(0.02, 0.95, ("Andel stenar med draget: förlorade och bevarade, båda kodade ur gamla teckningar" if sv else
                          "Share of stones with the feature: lost and surviving, both coded from old drawings"),
             fontsize=14, color=INK, fontweight="bold", va="top")
    ax.scatter([], [], s=120, color=RUST, label=(f"Förlorade ({N_LOST} stenar)" if sv else f"Lost ({N_LOST} stones)"))
    ax.scatter([], [], s=120, color=BLUE, label=(f"Bevarade ({N_KEPT} stenar)" if sv else f"Surviving ({N_KEPT} stones)"))
    fig.legend(loc="upper left", bbox_to_anchor=(0.015, 0.90), ncol=2, frameon=False, fontsize=12)
    fig.text(0.02, 0.03, ("Diagram: Vitki, ur Vitkis ornamentregister (koder ur gamla teckningar, samma godkända fält på båda sidor) och Rundata 3.1.\n"
                          "Antalet stenar per drag varierar, eftersom ett drag bara räknas där två läsare gav samma svar. Låst plan 2026-11-26.")
             if sv else
             ("Chart: Vitki, from Vitki's ornament register (codes from old drawings, the same approved fields on both sides) and Rundata 3.1.\n"
              "The number of stones per feature varies, since a feature counts only where two readers gave the same answer. Plan locked 2026-11-26."),
             fontsize=10, color=MUTED, va="bottom")
    return _png(fig)


os.makedirs(FIGDIR, exist_ok=True)
FIG = {}
for name, fn in (("altomta_u1038", fig_altomta), ("andelar_forlorade", fig_andelar)):
    for lang, sv in (("sv", True), ("en", False)):
        data = fn(sv)
        open(os.path.join(FIGDIR, f"{name}_{lang}.png"), "wb").write(data)
        FIG[f"{name}_{lang}"] = blog_figures.freeze(data)

HNAMN = {"Trögds hd": "Trögd", "Åsunda hd": "Åsunda", "Norunda hd": "Norunda", "Lyhundra hd": "Lyhundra", "Håbo hd": "Håbo"}


def chart(sv):
    rows = [":::chart Andel stenar med kors i de härader som avviker mest, procent" if sv
            else ":::chart Share of stones with a cross in the hundreds that differ most, percent"]
    rows.append("# Färre kors än stilen förklarar" if sv else "# Fewer crosses than the style explains")
    for h in ("Trögds hd", "Lyhundra hd", "Åsunda hd"):
        rows.append(f"{HNAMN[h]} | {pc(HR[h][0] / HR[h][1])} | {HR[h][1]} {'stenar' if sv else 'stones'}")
    rows.append("# Fler kors än stilen förklarar" if sv else "# More crosses than the style explains")
    for h in ("Norunda hd", "Håbo hd"):
        rows.append(f"+{HNAMN[h]} | {pc(HR[h][0] / HR[h][1])} | {HR[h][1]} {'stenar' if sv else 'stones'}")
    rows.append("# Alla härader" if sv else "# All hundreds")
    rows.append(f"{'Alla ' + str(D6['harader']) + ' härader' if sv else 'All ' + str(D6['harader']) + ' hundreds'} | {pc(LK.D6.mean())} | "
                f"{D6['n']} {'stenar' if sv else 'stones'}")
    rows.append("Källa: bevarade stenar med stilgrupp, kodade ur planschfotona i Sveriges runinskrifter; råa andelar. Vilka härader som "
                "avviker mest avgjordes av modellen, med stilgrupp och landskap hållna konstanta. Diagram: Vitki, ur Vitkis ornamentregister "
                "och Rundata 3.1." if sv else
                "Source: surviving stones with a style group, coded from the plate photos in Sveriges runinskrifter; raw shares. Which "
                "hundreds differ most was decided by the model, with style group and province held constant. Chart: Vitki, from Vitki's "
                "ornament register and Rundata 3.1.")
    return "\n".join(rows) + "\n:::"


BAUTIL_SV = "Umeå universitetsbiblioteks exemplar (Digitala samlingar), fritt från kända upphovsrättsliga restriktioner"
BAUTIL_EN = "Umeå University Library copy (Digital collections), free of known copyright restrictions"
TR, AS, NO, LY, HA = (HR[h] for h in ("Trögds hd", "Åsunda hd", "Norunda hd", "Lyhundra hd", "Håbo hd"))

SLUG = "stenarna-som-forsvann-hade-farre-kors"
title = "Stenarna som försvann hade färre kors"
title_en = "The stones that vanished had fewer crosses"
summary = ("Runstenar som tecknades på 1600- och 1700-talen och sedan gick förlorade hade mer sällan ett kors än de som står kvar. "
           "Bilden av hur vanligt korset var bygger alltså troligen på ett urval som lutar åt korset. Och korset följde bygden: "
           "i vissa härader ristades det oftare än stilen förklarar, i andra mer sällan.")
summary_en = ("Runestones that were drawn in the seventeenth and eighteenth centuries and then lost more seldom had a cross than "
              "those still standing. Our picture of how common the cross was therefore probably rests on a sample tilted towards "
              "it. And the cross followed the district: in some hundreds it was carved more often than the style explains, in "
              "others less often.")

body = f"""Någon gång under 1600-talet avbildades en runsten vid Altomta i Tensta socken, norr om Uppsala. Bilden skars i trä och trycktes först 1750, som nummer {B496['bautil_nr']} i Johan Göranssons *Bautil*. Stenen finns inte längre. Det vi vet om den vet vi från träsnittet och från runorna som tecknaren skrev av:

> {QUOTE}

”Hedinbjörn lät resa sten efter Ale (eller Alle), sin bror …” Resten är borta. Men överst, innanför ringen av runor, står ett kors.

![Bautils träsnitt av U 1038 vid Altomta, med registrets koder]({FIG['altomta_u1038_sv']})
Figur: Vitki. U 1038 vid Altomta i Tensta socken, Norunda härad, i träsnittet i *Bautil* och med de koder stenen har i Vitkis ornamentregister. Koderna är lästa ur träsnittet av två oberoende läsare (Anthropics språkmodell Claude, Claude Opus). Träsnitt nummer {B496['bautil_nr']} i Johan Göranssons *Bautil* (1750), {BAUTIL_SV}.

Den som i dag räknar kors på runstenar räknar på de stenar som finns kvar. Det är lätt att glömma att de är ett urval. Av de runstenar som Rundata, den samnordiska runtextdatabasen, räknar till Sverige är {N_FORLORADE_KORPUS} förlorade. Några sprängdes, några murades in, några försvann utan att någon skrev upp hur. Frågan här är enkel att ställa och svår att besvara: var de stenar som försvann likadana som de som står kvar?

Vi har prövat det, och ställt ytterligare en fråga om korset, i två undersökningar som båda låstes i förväg den 26 november 2026. Planerna skrevs innan vi såg utfallen, och det som står i dem gäller också där resultatet blev svagare än vi hade hoppats.

## Ett kors går att räkna

Korset är kanske det mest omskrivna tecknet på runstenarna. Det har länge lästs som ett spår av kristnandet, bland annat i Linn Lagers avhandling *Den synliga tron* (2002) om runstenskorsen. Men för att jämföra hundratals stenar måste korset bli en kod: ja eller nej.

I Vitkis ornamentregister har varje bild lästs av två läsare oberoende av varandra, två separata körningar av Anthropics språkmodell Claude (Claude Opus), med en fast kodbok. Frågan om korset är kort: finns ett kors? Ett värde räknas bara när båda läsarna svarar samma sak. Hur läsningen går till och hur den prövas beskriver vi i metodartikeln *Så läser vi rundjuren* och i rapporten *Ornamentiken som mätbar källa*. Här räcker tre saker.

- **Läsarna är nästan alltid eniga om korset.** På fotona i *Sveriges runinskrifter* var kappa {kv(M2['fält']['kors']['kappa'])}. Kappa är ett mått på enighet där slumpens bidrag är borträknat: 1 betyder att läsarna alltid är eniga, 0 att de inte är eniga oftare än om de hade gissat.
- **De gamla teckningarna återger korset troget.** På {KTP['alla']['kors']['jämförbara']} bevarade stenar som finns både på ett foto och i en gammal teckning gav teckningen och fotot samma svar om korset i {pc(KTP['alla']['kors']['lika'])} procent av fallen (kappa {kv(KTP['alla']['kors']['kappa'])}). Bautils träsnitt stämde med fotot på 29 av {KTP['bautil']['kors']['jämförbara']} stenar. Det är det som gör det möjligt att räkna kors också på stenar som bara finns kvar på papper.
- **Koderna fångar det som borde finnas.** I ett eget prov på {BB['stenar']} stenar som inte hade använts tidigare gick texter med kristna markörer ihop med ett kors i bildkoderna, trots att läsarna aldrig såg texten. När korset togs ur koderna föll sambandet till ungefär en fjärdedel. Det är inget nytt fynd utan det väntade: tro och kors hör ihop. Men det visar att koderna mäter det de ska.

## Vad försvann?

{len(FL)} av de förlorade stenarna har vi kunnat koda ur en gammal teckning, de flesta ur *Bautil*, andra ur Johannes Rhezelius teckningar från 1630-talet och Johan Peringskiölds kring år 1700. Att jämföra dem med fotona av de bevarade stenarna vore orättvist, eftersom en teckning är en annan sorts bild än ett foto. Därför jämförde vi med {N_KEPT} bevarade stenar som också kodats ur sina gamla teckningar, med samma regler för vilka drag som får läsas. Samma slags källa på båda sidor.

Planen bestämde tre drag i förväg: korset, rundjuret (slutar runbandet i ett djurhuvud?) och en utarbetad ornamentik (flera djur, ett koppel som binder ihop dem eller en tät fläta). Den statistiska modellen tog hänsyn till socknen stenen stod i, till vilken tecknare som gjorde bilden och till om stenen är uppländsk.

Korset skilde. Bland de förlorade stenarna hade {pc(U2['andel_forlorade'])} procent ett kors, bland de bevarade {pc(U2['andel_bevarade'])} procent. Uttryckt i odds, chansen för ett kors mot chansen för inget kors, hade de förlorade stenarna ungefär två femtedelar av de bevarades odds: oddskvoten var {kv(U2['or'])}, sannolikt någonstans mellan {kv(U2['ci'][0])} och {kv(U2['ci'][1])}. Ett så tydligt mönster skulle uppstå av en slump färre än en gång på hundra, också när vi räknar med att tre drag prövades på en gång.

Rundjuret och den utarbetade ornamentiken pekade åt samma håll: {pc(U1['andel_forlorade'])} mot {pc(U1['andel_bevarade'])} procent och {pc(U3['andel_forlorade'])} mot {pc(U3['andel_bevarade'])} procent. Men där räckte det inte hela vägen. Efter justeringen för de tre proven hamnade båda strax över den gräns vi satte i förväg, och de räknas därför inte som visade. De antyder att de förlorade stenarna överlag var enklare. Mer än en antydan är det inte.

![Andelen kors, rundjur och utarbetad ornamentik bland förlorade och bevarade stenar]({FIG['andelar_forlorade_sv']})
Diagram: Vitki, ur Vitkis ornamentregister och Rundata 3.1. De förlorade och de bevarade stenarna är kodade ur samma slags källa, gamla teckningar, de flesta från 1600- och 1700-talen, med samma godkända drag på båda sidor.

Två kontroller pekar åt samma håll. Bara i Uppland, där de flesta stenarna finns, var andelarna {pc(UP['andel_forlorade'])} mot {pc(UP['andel_bevarade'])} procent. Och ställer man de förlorade stenarnas teckningar mot fotona av alla bevarade stenar i samma socknar blir det {pc(BF['forlorade_teckning'])} mot {pc(BF['bevarade_foto'])} procent. Det är en jämförelse mellan olika slags bilder, men riktningen är densamma.

## Vad det betyder för den som räknar kors

Följden är lätt att säga. Andelen runstenar med kors bland dem som står kvar är troligen högre än den var bland alla som restes. Den som räknar kors, eller använder korset som ett mått på hur kristen en bygd eller en tid var, räknar på ett urval som lutar åt korset.

Hur mycket det lutar kan vi inte säga ännu. Långt ifrån alla förlorade stenar har avbildats, och de vi har kodat är ett litet urval. Det vore också att gå för långt att säga att vikingatiden var mindre kristen än stenarna låter påskina. Ett kors är ett tecken på en sten, inte en folkräkning.

Varför stenarna försvann vet vi inte. Tre förklaringar ligger nära till hands, och ingen av dem är prövad:

- **Tiden.** Om stenar utan kors i genomsnitt är äldre har de haft längre tid på sig att gå förlorade. Det kunde vi inte hålla konstant: {N_UTAN_STIL} av de {len(FL)} förlorade stenarna saknar stilgrupp i Rundata, så deras ålder är okänd.
- **Platsen.** Stenar som stod på olika slags platser kan ha fått olika öden.
- **Bruket.** Stenar utan kors kan oftare ha blivit byggnadssten.

Teckningarna själva kan också vara ett urval. Tecknarna avbildade de stenar de hittade och fann värda att teckna. Skillnaden är dessutom störst i *Bautil*, som står för de flesta förlorade stenarna: {BAU[0]} mot {BAU[1]} procent kors. Hos Peringskiöld var det {PER[0]} mot {PER[1]} procent, hos Rhezelius och de övriga tecknarna ungefär lika, men där är stenarna få. Skillnaden kan alltså gälla främst de stenar som *Bautils* tecknare såg. Däremot glömde träsnitten inte korsen: i källkontrollen stämde de med fotot på 29 stenar av {KTP['bautil']['kors']['jämförbara']}.

## Korset följde bygden

Den andra undersökningen frågade något annat. Om två ristare i olika bygder högg samma slags djur vid ungefär samma tid, satte de då kors lika ofta?

Underlaget är {LT['stenar']} bevarade stenar med en stilgrupp i Rundata, fördelade på {LT['harader']} härader. Häradet var den gamla bygdeindelningen, i Uppland kallad hundare, med eget ting och egna gränser. Modellen höll stilgruppen och landskapet konstanta och mätte sedan hur mycket av det som återstod som skilde mellan häraderna, och mellan socknarna inom dem. Åtta drag prövades, alla bestämda i förväg.

Korset var det tydligaste. Ungefär en tiondel av den variation i korset som stilgrupp och landskap inte förklarar låg mellan häraderna (måttet heter ICC och var {kv(D6['icc'])}). Ett så tydligt mönster skulle uppstå av en slump färre än en gång på 200, också med hänsyn till att åtta drag prövades. Hur stor andelen är vet vi mindre säkert: sannolikt någonstans mellan nära noll och knappt en femtedel. Men att häraderna skiljer sig åt håller.

{chart(True)}

I Trögd hade {TR[0]} av {TR[1]} stenar ett kors, i Åsunda {AS[0]} av {AS[1]} och i Lyhundra {LY[0]} av {LY[1]}. I Norunda och Håbo hade {NO[0]} av {NO[1]} det, i båda. Alla fem ligger i Uppland, så skillnaden finns inom ett och samma landskap. När modellen räknat bort stilgruppen har Trögd ungefär en fjärdedel av oddsen för ett kors i ett genomsnittligt härad, Norunda mer än dubbelt så höga och Håbo ungefär dubbelt. Altomta, där träsnittets sten stod, ligger i Norunda.

Vad det betyder kan undersökningen inte avgöra. Kanske kom korset till stenarna i olika takt i olika bygder. Kanske satte några ristare kors på nästan allt de högg, och det gjorde skillnad i ett litet härad. Ett härad är en grov enhet, och en ristare kan ha arbetat i flera. Det vi kan säga är att korset inte bara följde stilen och tiden. Det följde också bygden.

## Det som följde stilen

Lika talande är det som inte skilde. Huvudets vy, ögats form och antalet djur varierade i stort sett inte alls mellan häraderna när stilgruppen var hållen konstant. De följer stilen, inte bygden, och det är vad man kan vänta sig om Anne-Sofie Gräslunds stilgrupper fångar något verkligt. Flätverket och svansen skilde lite, men inte så att det håller.

Två drag behöver en kommentar. Kopplet, öglan som binder ihop två djur, skilde mer än något annat mellan häraderna (ICC {kv(D1['icc'])}) men klarade inte justeringen för de åtta proven. Det är en antydan som behöver en egen låst plan innan vi säger mer. Den extra ormen gav formellt ett utslag, men det berodde på modellen och inte på stenarna: draget finns nästan bara i enstaka socknar, och modellen kunde inte skatta variationen. Vi räknar det inte.

Skriften ger en jämförelse. Samma modell för sex språkliga drag, som skiljetecken, prepositioner och stungna runor, gav en andel mellan häraderna på mellan noll och {kv(max(v['icc'] for v in SP.values()))}. Korset skilde alltså mer mellan bygderna än skrivsätten gjorde.

## Det vi inte vet

- **Urvalen är små.** Korset jämfördes på {U2['n_forlorade']} förlorade och {U2['n_bevarade']} bevarade stenar, och häraderna ovan har {LY[1]} till {NO[1]} stenar var.
- **Uppland dominerar** båda undersökningarna.
- **Koden gäller en sida.** Kodboken säger att läsaren ska koda den sida som bär det största rundjuret, så ett kors på en annan sida kan missas. Det gäller förlorade och bevarade stenar lika.
- **Läsarna är samma modell.** De läser oberoende av varandra men kan dela blinda fläckar. Därför prövas varje sorts bild mot en annan innan den används.

## Pröva själv

*Bautil* finns digitaliserad och fri att använda i Umeå universitetsbiblioteks digitala samlingar. Träsnitten är ordnade efter härad och socken. Slå upp din egen bygd, räkna korsen på träsnitten och jämför med de stenar som står kvar. Tänk på regeln som gäller för läsarna: svara ”osäkert” när du inte ser säkert.

:::box Det viktigaste i korthet
- De runstenar som har försvunnit sedan 1600-talet hade mer sällan kors än de som står kvar. Bilden av hur vanligt korset var bygger alltså troligen på ett urval som lutar åt korset.
- Fyndet säger vad som saknas, inte varför. Tiden kunde inte hållas konstant, och teckningarna kan själva vara ett urval.
- Korset var också en fråga om bygd: i vissa härader ristades det oftare än stilen förklarar, medan rundjurets drag följde stilen.
- Gamla teckningar går att räkna på för korset, eftersom tecknarna återgav det troget.
:::

## Källor

Göransson, J. 1750. *Bautil*. Stockholm; {BAUTIL_SV}. Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139. Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige*. Occasional Papers in Archaeology 31. Uppsala: Uppsala universitet. Samnordisk runtextdatabas (Rundata) 3.1, Uppsala universitet. *Sveriges runinskrifter*, Riksantikvarieämbetet (planscher och textband med Rhezelius och Peringskiölds teckningar, lästa men inte återgivna). De låsta analysplanerna (2026-11-26), kodboken och resultaten finns i Vitkis öppna kodförråd."""

body_en = f"""At some point in the seventeenth century a runestone at Altomta in Tensta parish, north of Uppsala, was drawn. The drawing was cut in wood and not printed until 1750, as number {B496['bautil_nr']} in Johan Göransson's *Bautil*. The stone no longer exists. What we know of it we know from the woodcut and from the runes the draughtsman copied:

> {QUOTE}

"Heðinbjörn had a stone raised after Áli (or Alli), his brother …" The rest is gone. But at the top, inside the ring of runes, stands a cross.

![Bautil's woodcut of U 1038 at Altomta, with the register's codes]({FIG['altomta_u1038_en']})
Figure: Vitki. U 1038 at Altomta in Tensta parish, Norunda hundred, in the woodcut in *Bautil* and with the codes the stone has in Vitki's ornament register. The codes were read from the woodcut by two independent readers (Anthropic's language model Claude, Claude Opus). Woodcut number {B496['bautil_nr']} in Johan Göransson's *Bautil* (1750), {BAUTIL_EN}.

Anyone who counts crosses on runestones today counts on the stones that remain. It is easy to forget that they are a sample. Of the runestones that Rundata, the Scandinavian Runic-text Database, assigns to Sweden, {N_FORLORADE_KORPUS} are lost. Some were blasted, some walled in, some vanished without anyone noting how. The question here is easy to ask and hard to answer: were the stones that vanished like the ones still standing?

We tested it, and asked one more question about the cross, in two studies, both locked in advance on 26 November 2026. The plans were written before we saw the outcomes, and what they say holds also where the result turned out weaker than we had hoped.

## A cross can be counted

The cross is perhaps the most discussed sign on the runestones. It has long been read as a trace of the conversion, among other places in Linn Lager's dissertation *Den synliga tron* ("The visible faith", 2002) on runestone crosses. But to compare hundreds of stones the cross has to become a code: yes or no.

In Vitki's ornament register every picture was read by two readers independently of each other, two separate runs of Anthropic's language model Claude (Claude Opus), with a fixed codebook. The question about the cross is short: is there a cross? A value counts only when both readers give the same answer. How the reading is done and how it is tested we describe in the method article *How we read the rune animals* and in the report *Ornamentiken som mätbar källa* (The ornament as a measurable source). Three things suffice here.

- **The readers almost always agree about the cross.** On the photographs in *Sveriges runinskrifter* kappa was {kv(M2['fält']['kors']['kappa'], False)}. Kappa is a measure of agreement from which the contribution of chance is removed: 1 means the readers always agree, 0 that they agree no more often than if they had guessed.
- **The old drawings render the cross faithfully.** On {KTP['alla']['kors']['jämförbara']} surviving stones that exist both in a photograph and in an old drawing, drawing and photograph gave the same answer about the cross in {pc(KTP['alla']['kors']['lika'])} percent of cases (kappa {kv(KTP['alla']['kors']['kappa'], False)}). Bautil's woodcuts agreed with the photograph on 29 of {KTP['bautil']['kors']['jämförbara']} stones. That is what makes it possible to count crosses also on stones that survive only on paper.
- **The codes capture what ought to be there.** In a separate test on {BB['stenar']} stones not used before, texts with Christian markers went together with a cross in the image codes, although the readers never saw the text. When the cross was taken out of the codes, the link fell to about a quarter. That is no new finding but the expected one: faith and cross belong together. But it shows that the codes measure what they should.

## What vanished?

{len(FL)} of the lost stones we have been able to code from an old drawing, most of them from *Bautil*, others from Johannes Rhezelius's drawings of the 1630s and Johan Peringskiöld's from around 1700. Comparing them with the photographs of the surviving stones would be unfair, since a drawing is a different kind of picture from a photograph. So we compared them with {N_KEPT} surviving stones that were also coded from their old drawings, with the same rules for which features may be read. The same kind of source on both sides.

The plan fixed three features in advance: the cross, the rune animal (does the rune band end in an animal head?) and elaborate ornament (several animals, a koppel binding them together or dense interlace). The statistical model took account of the parish the stone stood in, of which draughtsman made the picture and of whether the stone is from Uppland.

The cross differed. Among the lost stones {pc(U2['andel_forlorade'])} percent had a cross, among the surviving {pc(U2['andel_bevarade'])} percent. Expressed in odds, the chance of a cross against the chance of none, the lost stones had about two fifths of the surviving stones' odds: the odds ratio was {kv(U2['or'], False)}, probably somewhere between {kv(U2['ci'][0], False)} and {kv(U2['ci'][1], False)}. A pattern this clear would arise by chance fewer than one time in a hundred, even allowing for the fact that three features were tested at once.

The rune animal and the elaborate ornament pointed the same way: {pc(U1['andel_forlorade'])} against {pc(U1['andel_bevarade'])} percent and {pc(U3['andel_forlorade'])} against {pc(U3['andel_bevarade'])} percent. But there it did not go all the way. After the adjustment for the three tests, both landed just above the threshold we set in advance, so they do not count as shown. They suggest that the lost stones were simpler overall. It is no more than a suggestion.

![The share of cross, rune animal and elaborate ornament among lost and surviving stones]({FIG['andelar_forlorade_en']})
Chart: Vitki, from Vitki's ornament register and Rundata 3.1. The lost and the surviving stones are coded from the same kind of source, old drawings, most of them from the seventeenth and eighteenth centuries, with the same approved features on both sides.

Two checks point the same way. In Uppland alone, where most of the stones are, the shares were {pc(UP['andel_forlorade'])} against {pc(UP['andel_bevarade'])} percent. And setting the lost stones' drawings against the photographs of all surviving stones in the same parishes gives {pc(BF['forlorade_teckning'])} against {pc(BF['bevarade_foto'])} percent. That compares different kinds of picture, but the direction is the same.

## What it means for anyone counting crosses

The consequence is easy to state. The share of runestones with a cross among those still standing is probably higher than it was among all that were raised. Anyone who counts crosses, or uses the cross as a measure of how Christian a district or a period was, is counting on a sample tilted towards the cross.

How far it tilts we cannot yet say. Far from all lost stones were ever drawn, and those we have coded are a small sample. It would also go too far to say that the Viking Age was less Christian than the stones make it seem. A cross is a sign on a stone, not a census.

Why the stones vanished we do not know. Three explanations come to mind, and none of them has been tested:

- **Time.** If stones without a cross are older on average, they have had longer to be lost. We could not hold that constant: {N_UTAN_STIL} of the {len(FL)} lost stones have no style group in Rundata, so their age is unknown.
- **Place.** Stones that stood in different kinds of places may have met different fates.
- **Use.** Stones without a cross may more often have become building stone.

The drawings may themselves be a sample. The draughtsmen drew the stones they found and thought worth drawing. The difference is also largest in *Bautil*, which accounts for most of the lost stones: {BAU[0]} against {BAU[1]} percent with a cross. With Peringskiöld it was {PER[0]} against {PER[1]} percent, with Rhezelius and the other draughtsmen about equal, but there the stones are few. The difference may thus concern mainly the stones that *Bautil*'s draughtsmen saw. The woodcuts did not, however, forget the crosses: in the source check they agreed with the photograph on 29 stones of {KTP['bautil']['kors']['jämförbara']}.

## The cross followed the district

The second study asked something else. If two carvers in different districts cut the same kind of animal at about the same time, did they add a cross equally often?

The material is {LT['stenar']} surviving stones with a style group in Rundata, spread over {LT['harader']} hundreds (härader). The hundred was the old district division, in Uppland called *hundare*, with its own assembly and its own borders. The model held style group and province constant and then measured how much of what remained differed between the hundreds, and between the parishes within them. Eight features were tested, all fixed in advance.

The cross was the clearest. About a tenth of the variation in the cross that style group and province do not explain lay between the hundreds (the measure is called the ICC and was {kv(D6['icc'], False)}). A pattern this clear would arise by chance fewer than one time in 200, even allowing for the eight features tested. How large the share is we know less surely: probably somewhere between close to zero and just under a fifth. But that the hundreds differ holds.

{chart(False)}

In Trögd {TR[0]} of {TR[1]} stones had a cross, in Åsunda {AS[0]} of {AS[1]} and in Lyhundra {LY[0]} of {LY[1]}. In Norunda and Håbo {NO[0]} of {NO[1]} had one, in both. All five lie in Uppland, so the difference exists within one and the same province. With the style group accounted for, the model gives Trögd about a quarter of the odds of a cross in an average hundred, Norunda more than twice as high and Håbo about twice. Altomta, where the woodcut's stone stood, lies in Norunda.

What this means the study cannot decide. Perhaps the cross reached the stones at different paces in different districts. Perhaps a few carvers put a cross on nearly everything they cut, and that made a difference in a small hundred. A hundred is a coarse unit, and a carver may have worked in several. What we can say is that the cross did not only follow style and time. It also followed the district.

## What followed the style

Just as telling is what did not differ. The view of the head, the shape of the eye and the number of animals hardly varied at all between the hundreds once the style group was held constant. They follow the style, not the district, which is what one would expect if Anne-Sofie Gräslund's style groups capture something real. The interlace and the tail differed a little, but not enough to hold.

Two features need a comment. The koppel, the loop that binds two animals together, differed more than anything else between the hundreds (ICC {kv(D1['icc'], False)}) but did not pass the adjustment for the eight tests. It is a hint that needs its own locked plan before we say more. The extra serpent gave a formal result, but it came from the model and not from the stones: the feature occurs almost only in a handful of parishes, and the model could not estimate the variation. We do not count it.

The writing gives a comparison. The same model for six linguistic features, such as word dividers, prepositions and dotted runes, gave a share between the hundreds of between zero and {kv(max(v['icc'] for v in SP.values()), False)}. The cross thus differed more between districts than the ways of writing did.

## What we do not know

- **The samples are small.** The cross was compared on {U2['n_forlorade']} lost and {U2['n_bevarade']} surviving stones, and the hundreds above have {LY[1]} to {NO[1]} stones each.
- **Uppland dominates** both studies.
- **The code covers one face.** The codebook tells the reader to code the face that carries the largest rune animal, so a cross on another face can be missed. That applies to lost and surviving stones alike.
- **The readers are the same model.** They read independently of each other but may share blind spots. That is why every kind of picture is tested against another before it is used.

## Try it yourself

*Bautil* is digitised and free to use in Umeå University Library's digital collections. The woodcuts are ordered by hundred and parish. Look up your own district, count the crosses in the woodcuts and compare with the stones still standing. Keep the readers' rule in mind: answer "uncertain" when you cannot see for sure.

:::box The essentials in brief
- The runestones that have vanished since the seventeenth century more seldom had a cross than those still standing. Our picture of how common the cross was therefore probably rests on a sample tilted towards it.
- The finding says what is missing, not why. Time could not be held constant, and the drawings may themselves be a sample.
- The cross was also a matter of district: in some hundreds it was carved more often than the style explains, while the rune animal's features followed the style.
- Old drawings can be counted on for the cross, because the draughtsmen rendered it faithfully.
:::

## Sources

Göransson, J. 1750. *Bautil*. Stockholm; {BAUTIL_EN}. Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139. Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige* [The visible faith]. Occasional Papers in Archaeology 31. Uppsala: Uppsala University. Scandinavian Runic-text Database (Rundata) 3.1, Uppsala University. *Sveriges runinskrifter*, Swedish National Heritage Board (plates and text volumes with Rhezelius's and Peringskiöld's drawings, read but not reproduced). The locked analysis plans (2026-11-26), the codebook and the results are in Vitki's open code repository."""

# ---- kontroller ---------------------------------------------------------------------------------------------------------
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
PRONOUN = re.compile(r"\b(han|hon|hans|hennes|honom|he|she|his|him|her|hers)\b", re.I)
labels = ["Forskning", "Tro och magi", "Geografi", "Datering och stil"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\s*\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)) == 2
    assert "{" not in b and "}" not in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    lines = b.splitlines()
    caps = [lines[i + 1] for i, ln in enumerate(lines) if ln.startswith("![")]
    assert len(caps) == 2  # + ett :::chart = tre figurer
    assert caps[0].startswith("Figur: Vitki." if lang == "sv" else "Figure: Vitki.") and "Bautil" in caps[0] and "Umeå" in caps[0]
    assert caps[1].startswith("Diagram: Vitki" if lang == "sv" else "Chart: Vitki")
    assert re.search(r"^(Källa|Source):.*(Diagram|Chart): Vitki", b, re.M)
    assert "Claude Opus" in caps[0] and b.count("Claude") == 4  # bildtexten + metoddelen
    assert "](/" not in b.replace("](/api/blog/figures/", "")  # inga länkar till appen eller till opublicerade utkast
    assert "/artiklar/" not in b and "http" not in b
    box = b[b.index(":::box"):b.index(":::", b.index(":::box") + 3)]
    assert "Claude" not in box and "insikt" not in box.lower() and "nyhet" not in box.lower()
    assert "orm" not in box.lower() and "serpent" not in box.lower()
    # inga könade pronomen; undantaget är "his brother" i översättningen av inskriften (stenresaren, ingen ristare)
    hits = [m.group(0).lower() for m in PRONOUN.finditer(b)]
    assert hits == ([] if lang == "sv" else ["his"]), (lang, hits)
assert "Vi räknar det inte." in body and "We do not count it." in body_en  # extra orm: inget fynd
OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "korset.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord sv,", len(body_en.split()), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    TOPIC = "Tro och magi|korset förlorade härader"
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published") and old.get("slug") == SLUG, "Bara det opublicerade utkastet skrivs över härifrån"
        ref.set({**OUT, "topic": TOPIC, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc, SLUG)
    else:
        assert not [p for p in blog._all() if p.get("slug") == SLUG], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**OUT, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": TOPIC, "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
