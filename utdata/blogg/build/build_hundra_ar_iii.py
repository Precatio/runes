"""Hundra år av runfrågor III: Stenarna som ingen skrev om (sv + en). Viktor 2026-11-20: en sammanställning av all forskning
vi har hemma, årtionde för årtionde, och vad forskningen saknar – som del III i serien.

Del I och II handlar om frågorna; del III räknar stenarna: vilka svenska runstenar som nämns med signum i tidskrifterna
vi har (Fornvännen, Futhark, Namn och bygd, Current Swedish Archaeology) och i avhandlingarna i litteraturregistret.
Plan: analysplaner/2026-11-20-hundra-ar-III.md + tillägg 1 och 2. Siffrorna läses ur utdata/hundra_ar_iii/matt.json,
m4.csv och data/cache/hundra_ar_iii/omnamnanden.csv (utdata/hundra_ar_iii/omnamnanden.py → analys.py → analys_m4.R) och
låses med assert. Titlar och årtal kontrolleras mot sökindexet. Inga citat. Bilderna är fria (Commons, kontrollerade
mot Commons API 2026-11-20).

HOLDBACK (Viktor, som i del I–II): inget om frågelistan, påståendedatabasen eller relevansbedömningarna, och inget om
hur Vitki ska pröva frågorna.

    ../../../.venv/bin/python build_hundra_ar_iii.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, literature  # noqa: E402

TS = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
CON = sqlite3.connect(os.path.join(TS, "sok.sqlite"))
H3 = os.path.join(ROOT, "utdata", "hundra_ar_iii")
M = json.load(open(os.path.join(H3, "matt.json"), encoding="utf-8"))
M4 = {r["term"]: r for r in csv.DictReader(open(os.path.join(H3, "m4.csv"), encoding="utf-8"))}
OM = list(csv.DictReader(open(os.path.join(ROOT, "data", "cache", "hundra_ar_iii", "omnamnanden.csv"), encoding="utf-8")))
J = [x for x in OM if x["source"] != "avhandling"]
sv_n = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731
pc = lambda a, b: round(100 * a / b)  # noqa: E731
dec_sv = lambda x: f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")  # noqa: E731
dec_en = lambda x: f"{x:.2f}".rstrip("0").rstrip(".")  # noqa: E731

# ======================================================================================================================
# 1. Siffrorna (alla ur analysens filer, låsta här)
# ======================================================================================================================
N_ALL, N = M["n_all"], M["n_stones"]
UNMEAS = sum(M["unmeasurable"].values())
assert (N_ALL, N, UNMEAS, M["unmeasurable"]["Öl"]) == (2321, 2128, 193, 101)
OL_ALL = M["land_stones"]["Öl"] + M["unmeasurable"]["Öl"]
assert OL_ALL == 154
assert (M["n_journal_pairs"], M["n_journal_texts"], len(J)) == (1814, 245, 1814)
NEVER = M["m3"]["alla"]["alla"]["never_j"]
NEVER_T = M["m3"]["alla"]["alla"]["never_jt"]
assert (NEVER, NEVER_T, N - NEVER) == (1122, 328, 1006)
assert M["m2"]["named_once"] == 582 and M["m2"]["top5pct_n"] == 106 and round(100 * M["m2"]["top5pct_share"]) == 29
TOP10 = M["m2"]["top10"]
assert [t[0] for t in TOP10] == ["Ög 136", "Vg 119", "U 729", "U 1161", "U 323", "Ög 8", "Öl 1", "Vs 15", "Sö 179", "U 127"]
assert TOP10[0][1] == 24

# per årtionde
D = M["m1"]
DECS = ["1906–1949", "1950-talet", "1960-talet", "1970-talet", "1980-talet", "1990-talet", "2000-talet", "2010-talet", "2020-talet"]
assert sorted(D) == sorted(DECS)
SH = {d: {k: round(100 * v) for k, v in D[d]["share"].items()} for d in DECS}
LAND_PC = {k: 100 * v / N for k, v in M["land_stones"].items()}
assert round(LAND_PC["U"]) == 53 and round(LAND_PC["Ög"]) == 10 and round(LAND_PC["Sö"]) == 16
assert [SH[d]["U"] for d in DECS] == [24, 63, 72, 71, 57, 70, 69, 43, 44]
assert [SH[d]["Ög"] for d in DECS] == [3, 1, 1, 10, 1, 2, 2, 8, 12]
assert SH["1906–1949"]["Sö"] == 60 and SH["1980-talet"]["Sö"] == 28 and SH["2010-talet"]["Sm"] == 14
assert D["2000-talet"]["share"]["Vg"] == 0
PRE2010 = sum(1 for x in J if int(x["year"]) < 2010)
IN2010 = sum(1 for x in J if 2010 <= int(x["year"]) < 2020)
assert (PRE2010, IN2010) == (738, 783) and IN2010 > PRE2010
DT = {d: (D[d]["texts"], D[d]["stones"]) for d in DECS}
assert DT == {"1906–1949": (18, 56), "1950-talet": (12, 76), "1960-talet": (17, 65), "1970-talet": (21, 168),
              "1980-talet": (23, 116), "1990-talet": (18, 120), "2000-talet": (17, 88), "2010-talet": (78, 546),
              "2020-talet": (41, 243)}

# hur många runstenar varje omnämnd text nämner
PER_TEXT = Counter(x["text"] for x in J)
ROK = Counter(int(x["year"]) // 10 * 10 for x in J if x["signum"] == "Ög 136")
assert sum(n for y, n in ROK.items() if y < 2010) == 2 and ROK[2010] == 13 and ROK[2020] == 9
SM = Counter(x["text"] for x in J if x["signum"].startswith("Sm "))
assert sum(SM.values()) == 164 and SM["futhark_5_137_799768"] == 79

# M3
L3 = M["m3"]["langd"]
assert M["m3"]["langd_granser"] == [22, 42, 62]
assert (L3["Q1"]["never_j"], L3["Q1"]["n"], L3["Q4"]["never_j"], L3["Q4"]["n"]) == (426, 550, 144, 524)
assert pc(426, 550) == 77 and pc(144, 524) == 27 and pc(L3["Q1"]["never_jt"], 550) == 44 and L3["Q4"]["never_jt"] == 8
F3 = M["m3"]["forlorad"]
assert (F3["förlorad"]["never_j"], F3["förlorad"]["n"], F3["kvar"]["never_j"], F3["kvar"]["n"]) == (272, 408, 850, 1720)
S3 = M["m3"]["stil"]["ingen säker"]
assert (S3["n"], S3["never_j"]) == (1097, 659) and pc(659, 1097) == 60
R3 = M["m3"]["ristare"]
assert (R3["ristare"]["never_j"], R3["ristare"]["n"], R3["ingen"]["never_j"], R3["ingen"]["n"]) == (328, 767, 794, 1361)
LAND3 = M["m3"]["landskap"]

# M4
f = lambda t: (float(M4[t]["or"]), float(M4[t]["lo"]), float(M4[t]["hi"]))  # noqa: E731
LEN = f("loglen")
DBL = tuple(math.exp(math.log(x) * math.log(2)) for x in LEN)  # dubbelt så lång text
assert [round(x, 1) for x in DBL] == [1.9, 1.7, 2.1], DBL
LOST = f("forlorad")
assert LOST == (0.59, 0.45, 0.77)
CARV = f("ristare")
assert CARV[1] < 1 < CARV[2]
SMO = f("landSm")
assert SMO == (5.57, 3.26, 9.52)
assert all(f(t)[2] >= 1 for t in M4 if t.startswith("land")), "inget landskap tydligt mindre uppmärksammat än Uppland"
assert all(f(t)[1] <= 1 <= f(t)[2] for t in M4 if t.startswith("stil"))
OGO = f("landÖg")
assert OGO[1] < 1 < OGO[2]

# M5
assert M["m5_all"] == 58 and len(M["m5"]) == 1 and M["m5"][0]["harad"] == "Gräsgårds hd" and (M["m5"][0]["n"], M["m5"][0]["never"]) == (10, 9)

# M6: avhandlingarna i registret
TH = [w for w in literature.catalog() if w.get("kind") == "avhandling"]
TH_DEC = Counter(w["year"] // 10 * 10 for w in TH)
assert len(TH) == 21 and TH_DEC == {1970: 1, 1990: 7, 2000: 7, 2010: 4, 2020: 2}
IDX = sorted({x["text"] for x in OM if x["source"] == "avhandling"})
assert len(IDX) == 8

# Vad vi har hemma
DOCS = CON.execute("select key, journal, year from docs").fetchall()
HOME = Counter(j for k, j, y in DOCS if "_hel_" not in k)
assert HOME == {"fornvannen": 3497, "futhark": 166, "csa": 54, "namnochbygd": 16}, HOME
assert max(int(y) for k, j, y in DOCS if j == "fornvannen") == 2022
assert min(int(y) for k, j, y in DOCS if j == "csa") == 2020

# ======================================================================================================================
# 2. Källorna som nämns, kontrollerade mot sökindexet
# ======================================================================================================================
META = {}
for jn in ("fornvannen", "futhark"):
    for line in open(os.path.join(TS, jn, "index.jsonl"), encoding="utf-8"):
        d = json.loads(line)
        META[d["key"]] = d
JLINKS = json.load(open(os.path.join(ROOT, "data", "cache", "literature", "journals.json"), encoding="utf-8"))["articles"]


def link(key):
    if key in JLINKS and JLINKS[key].get("url"):
        return JLINKS[key]["url"]
    d = META[key]
    return d.get("uri") or (f"https://doi.org/{d['doi']}" if d.get("doi") else d["fulltext"])


FUT = {"1": "2010", "4": "2013", "5": "2014", "9-10": "2018–2019"}


def where(key, lang="sv"):
    if key.startswith("futhark_"):
        vol = key.split("_")[1]
        s = f"Futhark {vol.replace('-', '–')} ({FUT[vol]})"
        assert any(s.replace(" ", "") in re.sub(r"\s", "", t) for (t,) in CON.execute("select text from pages where key=?", (key,))), s
        return s
    return f"Fornvännen {META[key]['year']}"


# key: (visningsnamn, antal runstenar texten nämner – kontrolleras mot räkningen)
SRC = {
    "1948_282": ("Sven B. F. Jansson", 22), "1950_330": ("Sven B. F. Jansson", None), "1953_262": ("Sven B. F. Jansson", None),
    "1954_001": ("Sven B. F. Jansson", 19), "1958_241": ("Sven B. F. Jansson", None), "1965_050": ("Sven B. F. Jansson", None),
    "1966_021": ("Sven B. F. Jansson", None), "1969_297": ("Elisabeth Svärdström", None), "1976_096": ("Helmer Gustavson", 39),
    "1975_005": ("Elias Wessén", 13), "1980_187": ("Jan Paul Strid", None), "1986_098": ("Mats G. Larsson", None), "1987_001": ("Volker Weskamp", 19),
    "1998_097": ("Frands Herschend", 37), "1996_143": ("Mats G. Larsson", 14), "1999_196": ("Mats G. Larsson", None),
    "2002_087": ("Mats G. Larsson", None), "2003_195": ("Michael Lerche Nielsen", None), "2008_233": ("Magnus Källström", 32),
    "futhark_5_137_799768": ("Per Stille", 82), "futhark_1_143_381125": ("Magnus Källström", 71),
    "futhark_4_31_682690": ("Klaus Düwel", 41), "futhark_5_115_799772": ("Marco Bianchi", 39),
    "futhark_5_171_799781": ("Maja Bäckvall", 36), "37d3b87e-51fd-4a87-af76-294ffc35901a": ("Annett Krakow", 22),
    "futhark_9-10_193_1385968": ("Patrik Larsson", 21), "futhark_9-10_39_1385978": ("Hanna Åkerström", 18),
}
TITLE, YEAR = {}, {}
for k, (who, n) in SRC.items():
    row = CON.execute("select title, year, authors from docs where key=?", (k,)).fetchone()
    assert row, k
    TITLE[k], YEAR[k] = row[0], int(row[1][:4])
    if who and k != "1975_005":
        assert who.split()[-1] in row[2], (k, who, row[2])
    if n is not None:
        assert PER_TEXT[k] == n, (k, PER_TEXT[k], n)
# den mest nämnande texten före 1998 är Runfynd 1975; ingen text nämner fler än Stille
assert max(n for k, n in PER_TEXT.items() if YEAR.get(k, int(next(x["year"] for x in J if x["text"] == k))) < 1998) == 39
assert max(PER_TEXT.values()) == 82
assert TITLE["1975_005"] == "Rök: ett fornminne och ett ortnamn"
assert any("Av Elias Wessén" in tx for (tx,) in CON.execute("select text from pages where key='1975_005'"))  # författaren står i texten
AUTH = {k: a for k, a in CON.execute("select key, authors from docs")}
J50 = [x for x in J if 1950 <= int(x["year"]) < 1960]
J50_JANSSON = sum(1 for x in J50 if "Jansson" in (AUTH[x["text"]] or ""))
assert (J50_JANSSON, len(J50)) == (75, 82)
SO80 = Counter(x["text"] for x in J if 1980 <= int(x["year"]) < 1990 and x["signum"].startswith("Sö "))
assert sum(SO80.values()) == 35 and SO80["1980_187"] == 8 and SO80["1986_098"] == 5 and SO80.most_common(1)[0][0] == "1980_187"
J10 = Counter(x["source"] for x in J if 2010 <= int(x["year"]) < 2020)
assert J10["futhark"] == 618 and sum(J10.values()) == 783
assert [d for d in DECS if D[d]["ratio"]["Ög"] > 1] == ["1970-talet", "2020-talet"]
assert PER_TEXT["1969_297"] >= 1 and "Runfynd" in TITLE["1969_297"]


def cite(k, lang="sv"):
    return f"[{where(k, lang)}]({link(k)})"


def t(k):
    return TITLE[k].replace(" : ", ": ").strip()


def sources(lang):
    out = []
    for k in sorted(SRC, key=lambda k: (YEAR[k], k)):
        who = SRC[k][0]
        q1, q2 = ("”", "”") if lang == "sv" else ("“", "”")
        out.append(f"- {who}: {q1}{t(k)}{q2}. {where(k, lang)}. [{'Fritt på nätet' if lang == 'sv' else 'Free online'}]({link(k)}).")
    return "\n".join(out)


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons, licens och upphov kontrollerade mot Commons API 2026-11-20)
# ======================================================================================================================
ROK_IMG = ("https://upload.wikimedia.org/wikipedia/commons/b/b1/R%C3%B6kstenen_1.JPG",
           "https://commons.wikimedia.org/wiki/File:R%C3%B6kstenen_1.JPG", "Bengt Olof Åradsson", "CC BY 1.0")
OL17_IMG = ("https://upload.wikimedia.org/wikipedia/commons/9/9d/Bautil_1062_-_%C3%96l_17.png",
            "https://commons.wikimedia.org/wiki/File:Bautil_1062_-_%C3%96l_17.png", "Johan Göransson, Bautil (1750)", "CC0")
OL17 = next(r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "hundra_ar_iii", "stenar.csv"), encoding="utf-8"))
            if r["signum"] == "Öl 17")
assert OL17["forlorad"] == "1" and OL17["n_j"] == "0" and OL17["n_t"] == "0"  # förlorad, aldrig nämnd i tidskrifter eller avhandlingar

# ======================================================================================================================
# 4. Diagrammen (procent; antalen i noten)
# ======================================================================================================================
LAB_EN = {"1906–1949": "1906–1949", **{d: d.replace("-talet", "s") for d in DECS[1:]}}


def chart_decades(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Upplands och Östergötlands andel av omnämnandena, årtionde för årtionde' if sv else 'Uppland and Östergötland: share of the mentions, decade by decade'}"]
    for code, nsv, nen in (("U", "Uppland", "Uppland"), ("Ög", "Östergötland", "Östergötland")):
        share = round(LAND_PC[code])
        rows.append(f"# {nsv} – {share} % av runstenarna" if sv else f"# {nen} – {share}% of the runestones")
        for d in DECS:
            v = SH[d][code]
            rows.append(f"{'+' if v < share else ''}{d if sv else LAB_EN[d]} | {v} | {sv_n(D[d]['pairs']) if sv else en_n(D[d]['pairs'])} {'omnämnanden totalt' if sv else 'mentions in all'}")
    rows.append("Källa: omnämnanden med signum i Fornvännen, Futhark, Namn och bygd och Current Swedish Archaeology; Vitkis räkning. "
                "Markerat: under landskapets andel av runstenarna. Före 1950 hade många stenar ännu inget signum. Diagram: Vitki."
                if sv else "Source: mentions by signum in Fornvännen, Futhark, Namn och bygd and Current Swedish Archaeology; Vitki's count. "
                "Highlighted: below the province's share of the runestones. Before 1950 many stones had no signum yet. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_never(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Andel runstenar som aldrig nämns med signum i tidskrifterna' if sv else 'Share of runestones never mentioned by signum in the journals'}"]
    rows.append("# Textens längd" if sv else "# Length of the text")
    labs = {"Q1": ("högst 22 runor", "up to 22 runes"), "Q2": ("23–42 runor", "23–42 runes"), "Q3": ("43–62 runor", "43–62 runes"),
            "Q4": ("fler än 62 runor", "more than 62 runes")}
    for q in ("Q1", "Q2", "Q3", "Q4"):
        x = L3[q]
        rows.append(f"{'+' if q == 'Q1' else ''}{labs[q][0 if sv else 1]} | {pc(x['never_j'], x['n'])} | {sv_n(x['never_j']) if sv else en_n(x['never_j'])} {'av' if sv else 'of'} {sv_n(x['n']) if sv else en_n(x['n'])}")
    rows.append("# Stenen" if sv else "# The stone")
    for k, lsv, len_ in (("kvar", "finns kvar", "survives"), ("förlorad", "förlorad", "lost")):
        x = F3[k]
        rows.append(f"{'+' if k == 'förlorad' else ''}{lsv if sv else len_} | {pc(x['never_j'], x['n'])} | {sv_n(x['never_j']) if sv else en_n(x['never_j'])} {'av' if sv else 'of'} {sv_n(x['n']) if sv else en_n(x['n'])}")
    rows.append(f"Källa: {sv_n(N)} svenska runstenar i Samnordisk runtextdatabas vars signum går att söka fram; omnämnanden i Fornvännen, Futhark, Namn och bygd och Current Swedish Archaeology. Diagram: Vitki."
                if sv else f"Source: {en_n(N)} Swedish runestones in the Scandinavian Runic-text Database whose signum can be searched for; mentions in Fornvännen, Futhark, Namn och bygd and Current Swedish Archaeology. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_land(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Andel runstenar som nämns minst en gång i tidskrifterna, landskap för landskap' if sv else 'Share of runestones mentioned at least once in the journals, province by province'}"]
    names = {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Vg": "Västergötland", "Sm": "Småland", "Öl": "Öland", "G": "Gotland"}
    for code in ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G"):
        x = LAND3[code]
        v, vt = pc(x["n"] - x["never_j"], x["n"]), pc(x["n"] - x["never_jt"], x["n"])
        rows.append(f"{'+' if code == 'Sm' else ''}{names[code]} | {v} | "
                    + (f"{sv_n(x['n'])} stenar; med avhandlingarna {vt} %" if sv else f"{en_n(x['n'])} stones; with the dissertations {vt}%"))
    rows.append("Källa: tidskrifterna som i diagrammet ovan; i noten även de åtta avhandlingar vi kan söka i. Öland: bara de 53 stenar vars signum går att söka fram. Diagram: Vitki."
                if sv else "Source: the journals as in the chart above; the note also counts the eight dissertations we can search. Öland: only the 53 stones whose signum can be searched for. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
SLUG1, SLUG2 = "hundra-ar-av-runfragor-grundlaggarna", "hundra-ar-av-runfragor-nar-forskarna-borjade-rakna"
SLUG3 = "hundra-ar-av-runfragor-stenarna-som-ingen-skrev-om"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-20-hundra-ar-III.md"
dbl_sv = f"{dec_sv(round(DBL[0], 1))} gånger (mellan {dec_sv(round(DBL[1], 1))} och {dec_sv(round(DBL[2], 1))})"
dbl_en = f"{dec_en(round(DBL[0], 1))} times (between {dec_en(round(DBL[1], 1))} and {dec_en(round(DBL[2], 1))})"
lost_sv = f"{round(100 * (1 - LOST[0]))} procent lägre (mellan {round(100 * (1 - LOST[2]))} och {round(100 * (1 - LOST[1]))} procent)"
lost_en = f"{round(100 * (1 - LOST[0]))} per cent lower (between {round(100 * (1 - LOST[2]))} and {round(100 * (1 - LOST[1]))} per cent)"
assert lost_sv.startswith("41 procent") and "23 och 55" in lost_sv
TOP_LIST_SV = "\n".join(f"- **{s}** {p.split(',')[0]} – {n} texter" for s, n, p in TOP10)
TOP_LIST_EN = "\n".join(f"- **{s}** {p.split(',')[0]} – {n} texts" for s, n, p in TOP10)

title = "Hundra år av runfrågor III: Stenarna som ingen skrev om"
title_en = "A Hundred Years of Runic Questions III: The Stones No One Wrote About"
summary = (f"De två första delarna följde forskarnas frågor från 1906 till i dag. Den tredje vänder på det: vilka runstenar har "
           f"forskarna skrivit om, årtionde för årtionde – och vilka har de aldrig nämnt? Drygt hälften av de svenska runstenarna "
           f"nämns aldrig i tidskrifterna. Det är inte landskapet eller tiden som avgör, utan hur mycket text stenen har och om den "
           f"finns kvar.")
summary_en = ("The first two parts followed scholars' questions from 1906 to the present. The third turns things round: which "
              "runestones have scholars written about, decade by decade – and which have they never mentioned? Just over half of "
              "the Swedish runestones are never mentioned in the journals. It is not the province or the period that decides, but "
              "how much text the stone has and whether it survives.")

body = f"""I [första delen](/artiklar/{SLUG1}) och [andra delen](/artiklar/{SLUG2}) följde vi forskarnas frågor: var stenarna stod, hur gamla de är, vem som ristade dem, vad de var till för. Den här delen vänder på perspektivet. I stället för att fråga vad forskarna frågade, frågar vi vilka stenar de skrev om – och vilka de aldrig nämnde.

Varje svensk runsten har ett signum, ett nummer i utgåvan Sveriges runinskrifter: U 344 i Orkesta, Ög 136 i Rök. När en forskare skriver om en sten står signumet nästan alltid med. Det gör det möjligt att räkna. Vi har letat efter varje svensk runsten i allt vi har hemma, årtionde för årtionde.

## Det vi har hemma

- **Fornvännen** 1906–2022: {sv_n(HOME['fornvannen'])} texter.
- **Futhark**, den internationella tidskriften för runforskning, volym 1–15 (2010–2025): {HOME['futhark']} texter.
- **Namn och bygd** 2010–2025: {HOME['namnochbygd']} årgångar.
- **Current Swedish Archaeology** från 2020: {HOME['csa']} texter.
- **{len(TH)} doktorsavhandlingar** i Vitkis litteraturregister, från Evert Salbergers *Runsvenska namnstudier* 1978 till Tristan Mueller-Vollmers avhandling om personnamnen 2021. {len(IDX)} av dem har vi i fulltext och kan söka i.

Utgåvorna själva, *Sveriges runinskrifter*, räknar vi inte. De tar per definition upp varje sten i sitt landskap, och det är de som har gett stenarna deras nummer. Allt annat i den här artikeln vilar på dem.

Det vi inte har läst är lika viktigt att säga: böckerna, Arkiv för nordisk filologi, Saga och sed, Nytt om runer och mycket annat. Det som följer gäller de texter vi har, inte hela runforskningen.

## Så räknade vi

En text räknas som att den nämner en sten om stenens signum står i texten minst en gång. Samma text räknas bara en gång per sten, hur många gånger signumet än återkommer. För att slippa felträffar – ett museinummer, en tand som heter M 2, en sidhänvisning – måste ordet *run* (runsten, runinskrift, rune) stå i närheten. Vi kontrollerade 100 slumpvis valda omnämnanden för hand, och alla 100 var rätt.

Efteråt hittade vi två slags fel som stickprovet inte hade fångat, och vi rättade dem. Gammal OCR delar ibland upp siffror, så att U 129 blir "U 1 29". Och {UNMEAS} runstenar har ett signum utanför huvudserien, som Öl Köping 12 eller ett nummer i Antikvarisk-topografiska arkivet, som inte går att söka fram i löpande text alls. De stenarna lämnar vi utanför, i stället för att räkna dem som aldrig nämnda. {M['unmeasurable']['Öl']} av dem finns på Öland. Reglerna skrev vi ner och [lade ut innan vi räknade]({PLAN}), och likaså varje ändring.

Kvar blir {sv_n(N)} runstenar. {M['n_journal_texts']} texter i tidskrifterna nämner minst en av dem, sammanlagt {sv_n(len(J))} gånger.

En sak behöver sägas innan vi börjar. Signumet är ett modernt verktyg. Innan ett landskaps band av *Sveriges runinskrifter* kom ut, hade dess stenar inga nummer, och forskarna skrev "stenen vid Rök". Det räknas inte här. Därför är siffrorna före 1950 små och går inte att jämföra med de senare. Även senare kallas de mest kända stenarna ofta vid namn: Rökstenen nämns med sitt signum i bara två texter före 2010.

## Årtionde för årtionde

**Före 1950: Södermanland först.** {DT['1906–1949'][0]} texter nämner {DT['1906–1949'][1]} runstenar med signum. {SH['1906–1949']['Sö']} procent av omnämnandena gäller Södermanland, mest tack vare en enda text: Sven B. F. Janssons ”{t('1948_282')}” ({cite('1948_282')}), som ensam nämner {SRC['1948_282'][1]} stenar.

**1950-talet: Fynden i kyrkmurarna.** {DT['1950-talet'][0]} texter, {DT['1950-talet'][1]} stenar. Uppland har {SH['1950-talet']['U']} procent av omnämnandena, mot {round(LAND_PC['U'])} procent av runstenarna. Det mesta, {J50_JANSSON} av {len(J50)} omnämnanden, kommer från Janssons fyndrapporter: ”{t('1950_330')}” ({cite('1950_330')}), ”{t('1953_262')}” ({cite('1953_262')}), ”{t('1954_001')}” ({cite('1954_001')}) och ”{t('1958_241')}” ({cite('1958_241')}). De stenar forskarna skrev om var för det mesta de som just hade kommit fram, till exempel ur kyrkornas murar.

**1960-talet: Uppland och lite till.** {DT['1960-talet'][0]} texter, {DT['1960-talet'][1]} stenar, och Uppland har {SH['1960-talet']['U']} procent. Jansson skrev om ”{t('1966_021')}” ({cite('1966_021')}) och om ”{t('1965_050')}” ({cite('1965_050')}) – ett av få tillfällen då Östergötland syns alls. Östergötland har ungefär en tiondel av runstenarna, men bara {SH['1960-talet']['Ög']} procent av omnämnandena under årtiondet. Från 1968 skriver Elisabeth Svärdström den årliga rapporten ”Runfynd” ({cite('1969_297')}).

**1970-talet: Runfynd år efter år.** {DT['1970-talet'][0]} texter, {DT['1970-talet'][1]} stenar. Rapporterna ”Runfynd” fortsätter, skrivna av Svärdström, Helmer Gustavson och Thorgunn Snædal. Gustavsons ”{t('1976_096')}” ({cite('1976_096')}) nämner {SRC['1976_096'][1]} runstenar, fler än någon annan text före 1998. Östergötland får för en gång skull sin andel, {SH['1970-talet']['Ög']} procent, bland annat genom Elias Wesséns ”{t('1975_005')}” ({cite('1975_005')}).

**1980-talet: Södermanland.** {DT['1980-talet'][0]} texter, {DT['1980-talet'][1]} stenar. Södermanland har {SH['1980-talet']['Sö']} procent av omnämnandena, mot {round(LAND_PC['Sö'])} procent av stenarna, och de är spridda över flera texter: Jan Paul Strids ”{t('1980_187')}” ({cite('1980_187')}), rapporterna ”Runfynd” och Mats G. Larssons ”{t('1986_098')}” ({cite('1986_098')}). Volker Weskamp skrev ”{t('1987_001')}” ({cite('1987_001')}) och nämner {SRC['1987_001'][1] - 1} andra stenar i samma artikel. Östergötland är tillbaka på {SH['1980-talet']['Ög']} procent.

**1990-talet: Ristarna och statistiken.** {DT['1990-talet'][0]} texter, {DT['1990-talet'][1]} stenar, och Uppland har åter {SH['1990-talet']['U']} procent. Frands Herschends ”{t('1998_097')}” ({cite('1998_097')}) nämner {SRC['1998_097'][1]} stenar i en artikel om ristaren Öpirs signaturer. Mats G. Larsson skrev om Jarlabanke i ”{t('1996_143')}” ({cite('1996_143')}) och om ”{t('1999_196')}” ({cite('1999_196')}). Sju av de {len(TH)} avhandlingarna i vårt register kom under det här årtiondet.

**2000-talet: Enskilda stenar på djupet.** {DT['2000-talet'][0]} texter, {DT['2000-talet'][1]} stenar. Magnus Källström läste Frötunastenen i ”{t('2008_233')}” ({cite('2008_233')}), Michael Lerche Nielsen skrev ”{t('2003_195')}” ({cite('2003_195')}) och Larsson om ”{t('2002_087')}” ({cite('2002_087')}). Ingen text i tidskrifterna nämner en västgötsk runsten med signum under hela årtiondet.

**2010-talet: Futhark och hela landskap.** Nu händer något. {DT['2010-talet'][0]} texter nämner {DT['2010-talet'][1]} olika runstenar, sammanlagt {sv_n(IN2010)} gånger – fler än under alla tidigare årtionden tillsammans ({sv_n(PRE2010)}). Det är Futhark som gör det: {J10['futhark']} av omnämnandena står där. Upplands andel faller till {SH['2010-talet']['U']} procent, för första gången sedan tiden före 1950 under landskapets andel av stenarna. Den text som nämner flest runstenar av alla är Per Stilles ”{t('futhark_5_137_799768')}” ({cite('futhark_5_137_799768')}): {SRC['futhark_5_137_799768'][1]} stenar, {SM['futhark_5_137_799768']} av dem i Småland. Efter den kommer Magnus Källströms artikel om ristaren Öpir ({cite('futhark_1_143_381125')}, {SRC['futhark_1_143_381125'][1]} stenar), Klaus Düwels ”{t('futhark_4_31_682690')}” ({cite('futhark_4_31_682690')}, {SRC['futhark_4_31_682690'][1]}), Marco Bianchis om inskrifter som går i flera riktningar ({cite('futhark_5_115_799772')}, {SRC['futhark_5_115_799772'][1]}) och Maja Bäckvalls ”{t('futhark_5_171_799781')}” ({cite('futhark_5_171_799781')}, {SRC['futhark_5_171_799781'][1]}). Rökstenen nämns med signum i {ROK[2010]} texter.

**2020-talet (till 2025): Östergötland kommer ikapp.** {DT['2020-talet'][0]} texter, {DT['2020-talet'][1]} stenar. Östergötland har {SH['2020-talet']['Ög']} procent av omnämnandena, mer än sin andel av stenarna – det har bara hänt en gång tidigare, på 1970-talet. Annett Krakow skrev om ”{t('37d3b87e-51fd-4a87-af76-294ffc35901a')}” ({cite('37d3b87e-51fd-4a87-af76-294ffc35901a')}), Patrik Larsson om ”{t('futhark_9-10_193_1385968')}” och Hanna Åkerström om ”{t('futhark_9-10_39_1385978')}” (båda i {cite('futhark_9-10_39_1385978')}, som i DiVA är daterad 2020). Rökstenen nämns i {ROK[2020]} texter.

{chart_decades('sv')}

Diagrammet visar två saker. Under ett halvt sekel, från 1950-talet till 2000-talet, gällde ungefär sju av tio omnämnanden en uppländsk sten, trots att Uppland har drygt hälften av runstenarna. Och Östergötland var nästan tyst i samma tid, med undantag för 1970-talet. Båda ändras med Futhark.

## Avhandlingarna

De {len(TH)} avhandlingarna i vårt register fördelar sig ojämnt över tiden: en på 1970-talet (Salberger), {TH_DEC[1990]} på 1990-talet, {TH_DEC[2000]} på 2000-talet, {TH_DEC[2010]} på 2010-talet och {TH_DEC[2020]} hittills på 2020-talet. På 1990-talet kom Henrik Williams om åsrunan, Svante Lagman om de stungna runorna, Mats G. Larsson om utlandsfärderna, Rune Palm om den regionala variationen, Marit Åhlén om Öpir, Torun Zachrisson om gårdarna och gravfälten och Per Stille om Fjädrundaland. På 2000-talet Laila Kitzler Åhfeldt om huggspåren, Linn Lager om korsen, Patrik Larsson om yrrunan, Thorgunn Snædal om Gotland, Kristel Zilmer om resorna österut, Magnus Källström om ristarna och Lisbeth Imer om kronologin. Sedan Marjolein Stern om bilderna, Marco Bianchi och Hanna Åkerström om hur texten läggs på stenen, Jonas Nordby om lönnrunorna, Sofia Pereswetoff-Morath om runblecken och Mueller-Vollmer om namnen.

Flera av dem går igenom nästan varje inskrift för ett enda drag – en runa, ett tecken, en ristares hand. Därför nämns många fler stenar i avhandlingarna än i tidskrifterna, ofta i en förteckning. Bara två handlar om ett enskilt landskap eller en enskild bygd: Snædal om Gotland och Stille om Fjädrundaland.

## Vilka stenar som nämns – och vilka som inte gör det

Av de {sv_n(N)} runstenarna nämns **{sv_n(NEVER)}, {pc(NEVER, N)} procent, aldrig med signum** i de fyra tidskrifterna. {sv_n(M['m2']['named_once'])} nämns en enda gång. Räknar vi in de åtta avhandlingarna vi kan söka i, är det {sv_n(NEVER_T)} stenar, {pc(NEVER_T, N)} procent, som inte nämns någonstans i det vi har hemma utöver utgåvorna.

Uppmärksamheten är ojämnt fördelad. De {M['m2']['top5pct_n']} mest nämnda stenarna, fem procent av alla, står för {round(100 * M['m2']['top5pct_share'])} procent av omnämnandena. De tio mest nämnda:

{TOP_LIST_SV}

![Rökstenen]({ROK_IMG[0]})
Rökstenen (Ög 136) i Östergötland, den runsten som nämns i flest texter – och de flesta av dem efter 2010. Foto: {ROK_IMG[2]}, {ROK_IMG[3]}, via [Wikimedia Commons]({ROK_IMG[1]}).

{chart_land('sv')}

Vad avgör då om en sten blir nämnd? Vi lät en statistisk modell väga samman fem saker på en gång: landskapet, stilgruppen, om stenen finns kvar, om ristaren är känd och hur lång texten är. Modellen tar också hänsyn till att stenar i samma socken ofta nämns i samma text, så att en artikel om en kyrka med tio stenar inte räknas som tio oberoende val. Resultatet anges som odds, chansen att nämnas delad med chansen att inte nämnas. Inom parentes står ett osäkerhetsintervall: det spann som det sanna värdet med stor sannolikhet ligger inom, med tanke på hur många stenar det rör sig om.

- **Textens längd avgör mest.** En sten med dubbelt så lång text har {dbl_sv} så stort odds att nämnas, när allt annat hålls lika. Av den fjärdedel av stenarna som har kortast text, högst 22 runor, nämns {pc(L3['Q1']['never_j'], L3['Q1']['n'])} procent aldrig. Av den fjärdedel som har längst, fler än 62 runor, gäller det {pc(L3['Q4']['never_j'], L3['Q4']['n'])} procent.
- **De förlorade stenarna glöms.** {sv_n(F3['förlorad']['n'])} runstenar är förlorade och kända genom äldre teckningar och anteckningar. {pc(F3['förlorad']['never_j'], F3['förlorad']['n'])} procent av dem nämns aldrig, mot {pc(F3['kvar']['never_j'], F3['kvar']['n'])} procent av dem som finns kvar. Också med textens längd medräknad är oddset {lost_sv}.
- **Ristaren spelar ingen tydlig roll.** Stenar med en känd ristare nämns oftare ({pc(R3['ristare']['n'] - R3['ristare']['never_j'], R3['ristare']['n'])} mot {pc(R3['ingen']['n'] - R3['ingen']['never_j'], R3['ingen']['n'])} procent), men de har också längre texter. När längden räknas in finns ingen tydlig skillnad kvar.
- **Tiden spelar ingen tydlig roll.** Ingen stilgrupp, från de tidigaste stenarna till de sena, nämns tydligt mer eller mindre än någon annan.
- **Inget landskap är tydligt bortglömt.** Inget landskap nämns tydligt mer sällan än Uppland. Östergötlands långa tystnad har hämtats in efter 2010, och räknat över hela tiden är skillnaden inte tydlig. Ett landskap sticker ut åt andra hållet: Småland, med {dec_sv(round(SMO[0], 1))} gånger så stort odds som Uppland (mellan {dec_sv(round(SMO[1], 1))} och {dec_sv(round(SMO[2], 1))}). Men nästan hälften av Smålands omnämnanden, {SM['futhark_5_137_799768']} av {sum(SM.values())}, kommer från en enda artikel – Stilles genomgång av Tiohärad. En forskare som tar sig an en hel bygd kan förändra bilden för ett helt landskap.

Inte heller de gamla gränserna visar några blinda fläckar. Av de {M['m5_all']} härader som har minst tio runstenar finns bara ett där nästan alla stenar saknas i tidskrifterna, Gräsgårds härad på Öland ({M['m5'][0]['never']} av {M['m5'][0]['n']}). Tystnaden ligger inte i vissa bygder. Den går genom alla.

{chart_never('sv')}

## Vad ingen har frågat

Det här är ingen kritik. Tidskrifter är till för det nya och det svåra: ett fynd i en kyrkmur, en inskrift som ingen har kunnat läsa, en ristare som går att följa från sten till sten. Utgåvorna har redan gått igenom varje sten, en efter en. Men när hundra år av texter läggs bredvid varandra syns det som ingen har haft anledning att skriva om.

**Den vanliga stenen.** Tre av fyra stenar med de kortaste texterna nämns aldrig. Och det är de korta stenarna som är de vanliga: någon reste stenen efter någon. Var för sig finns det lite att säga om dem. Tillsammans är de det mesta av materialet. Frågor om den vanliga stenen – vilka som reste de korta stenarna, var de stod, hur de skiljer sig från de långa – går bara att ställa om man ser alla på en gång.

**De förlorade.** Två av tre förlorade runstenar nämns aldrig. Många av dem finns bara som ett träsnitt eller en teckning från 1600- och 1700-talen.

![Öl 17 i Bautil]({OL17_IMG[0]})
Öl 17 vid Seby i Segerstads socken på Öland: ”Torgunn reste denna sten efter Ingjald, sin broder.” Stenen är förlorad, och den nämns varken i tidskrifterna eller i avhandlingarna vi har. Översättning: Runor (Riksantikvarieämbetet). Träsnitt: {OL17_IMG[2]}, {OL17_IMG[3]}, via [Wikimedia Commons]({OL17_IMG[1]}).

**Stenarna utan nummer i huvudserien.** {UNMEAS} runstenar har ett signum som inte går att söka fram i löpande text – på Öland {M['unmeasurable']['Öl']} av {OL_ALL}, de flesta fragment från Köpings kyrka. Vad som än har skrivits om dem, går det inte att hitta genom att söka på deras nummer. Det gäller oss, och det gäller alla andra som söker i databaserna.

**Stenarna utan stilgrupp.** {sv_n(S3['n'])} av de {sv_n(N)} stenarna, drygt hälften, har ingen säker stilgrupp i Samnordisk runtextdatabas. {pc(S3['never_j'], S3['n'])} procent av dem nämns aldrig.

Det som saknas är alltså inte omsorg om de enskilda stenarna. Det är frågor som tar alla stenarna på en gång – också de korta, de förlorade och de som ingen har tittat närmare på.

I Vitki står nu, på varje stens sida under [Inskrifter](/inskrifter), vilka texter i tidskrifterna som nämner den. Den som vill kan själv se om en sten har fått sin artikel – eller om den väntar.

## Våra egna gränser

- Vi räknar signum, inte ortnamn. Före 1950 nämndes stenarna oftast vid namn, och även senare kallas de mest kända så. Rökstenen är underräknad i de äldre årtiondena.
- Vi har bara räknat det vi har hemma. Böcker och flera viktiga tidskrifter saknas, och Namn och bygd och Current Swedish Archaeology finns bara för de senaste åren.
- Ett omnämnande är inte en studie. En sten i en förteckning räknas lika mycket som en sten som en hel artikel handlar om.
- OCR-texten har fel. Stickprovet var rätt i 100 fall av 100, och vi rättade de fel vi hittade efteråt, men enstaka felträffar finns kvar, främst bland stenar med låga nummer.
- Futhark räknas efter utgivningsåret i DiVA, som för några volymer är senare än årtalet på omslaget.

:::box Det viktigaste i korthet
- Drygt hälften av de svenska runstenarna, {pc(NEVER, N)} procent, nämns aldrig med sitt nummer i Fornvännen, Futhark, Namn och bygd eller Current Swedish Archaeology. Fem procent av stenarna står för nära en tredjedel av alla omnämnanden, och Rökstenen toppar.
- Från 1950-talet till 2000-talet gällde ungefär sju av tio omnämnanden en uppländsk sten, och mycket handlade om nya fynd. Östergötland var nästan tyst. Med Futhark från 2010 sprids uppmärksamheten över landet.
- Det är inte landskapet eller tiden som avgör om en sten blir nämnd, utan hur lång texten är och om stenen finns kvar. De korta och de förlorade stenarna är de som ingen skriver om.
- En enda forskare kan förändra bilden: Per Stilles genomgång av Tiohärad står för nästan hälften av alla omnämnanden av småländska stenar.
:::

## Källor

{sources('sv')}

Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Fornvännen finns fritt via Riksantikvarieämbetets plattform [pub.raa.se](https://pub.raa.se) (CC BY 4.0). Futhark finns fritt i [DiVA](https://uu.diva-portal.org) och på [futhark-journal.com](http://www.futhark-journal.com) (volym 1–5 CC BY-NC-ND 3.0, volym 6 CC BY-NC-ND 4.0, från volym 7 CC BY 4.0). Namn och bygd och Current Swedish Archaeology finns fritt på nätet (CC BY 4.0). Reglerna för räkningen och skripten: [analysplanen]({PLAN}) med två tillägg."""

body_en = f"""In [the first part](/en/artiklar/{SLUG1}) and [the second](/en/artiklar/{SLUG2}) we followed scholars' questions: where the stones stood, how old they are, who carved them, what they were for. This part turns the perspective round. Instead of asking what the scholars asked, we ask which stones they wrote about – and which they never mentioned.

Every Swedish runestone has a signum, a number in the edition Sveriges runinskrifter: U 344 at Orkesta, Ög 136 at Rök. When scholars write about a stone, the signum is nearly always there. That makes it possible to count. We have looked for every Swedish runestone in everything we have at home, decade by decade.

## What we have at home

- **Fornvännen** 1906–2022: {en_n(HOME['fornvannen'])} texts.
- **Futhark**, the international journal of runic studies, volumes 1–15 (2010–2025): {HOME['futhark']} texts.
- **Namn och bygd** 2010–2025: {HOME['namnochbygd']} annual volumes.
- **Current Swedish Archaeology** from 2020: {HOME['csa']} texts.
- **{len(TH)} doctoral dissertations** in Vitki's literature register, from Evert Salberger's *Runsvenska namnstudier* in 1978 to Tristan Mueller-Vollmer's dissertation on the personal names in 2021. We have {len(IDX)} of them in full text and can search them.

We do not count the editions themselves, *Sveriges runinskrifter*. By definition they treat every stone in their province, and it is they who gave the stones their numbers. Everything else in this article rests on them.

What we have not read is just as important to state: the books, Arkiv för nordisk filologi, Saga och sed, Nytt om runer and much else. What follows holds for the texts we have, not for all of runic research.

## How we counted

A text counts as mentioning a stone if the stone's signum appears in it at least once. The same text counts only once per stone, however often the signum recurs. To avoid false hits – a museum number, a tooth called M 2, a page reference – the word *run* (runsten, runinskrift, rune) must appear nearby. We checked 100 randomly chosen mentions by hand, and all 100 were right.

Afterwards we found two kinds of error that the sample had not caught, and we corrected them. Old OCR sometimes splits numbers, so that U 129 becomes "U 1 29". And {UNMEAS} runestones have a signum outside the main series, such as Öl Köping 12 or a number in the Antiquarian-Topographical Archive, which cannot be searched for in running text at all. We leave those stones out rather than count them as never mentioned. {M['unmeasurable']['Öl']} of them are on Öland. We wrote the rules down and [published them before we counted]({PLAN}), and likewise every change.

That leaves {en_n(N)} runestones. {M['n_journal_texts']} texts in the journals mention at least one of them, {en_n(len(J))} times in all.

One thing needs saying before we begin. The signum is a modern tool. Before a province's volume of *Sveriges runinskrifter* appeared, its stones had no numbers, and scholars wrote "the stone at Rök". That is not counted here. So the numbers before 1950 are small and cannot be compared with later ones. Even later, the best-known stones are often called by name: the Rök stone is mentioned by its signum in only two texts before 2010.

## Decade by decade

**Before 1950: Södermanland first.** {DT['1906–1949'][0]} texts mention {DT['1906–1949'][1]} runestones by signum. {SH['1906–1949']['Sö']} per cent of the mentions concern Södermanland, mostly thanks to a single text: Sven B. F. Jansson's “{t('1948_282')}” ({cite('1948_282', 'en')}), which on its own mentions {SRC['1948_282'][1]} stones.

**The 1950s: The finds in the church walls.** {DT['1950-talet'][0]} texts, {DT['1950-talet'][1]} stones. Uppland has {SH['1950-talet']['U']} per cent of the mentions, against {round(LAND_PC['U'])} per cent of the runestones. Most of it, {J50_JANSSON} of {len(J50)} mentions, comes from Jansson's find reports: “{t('1950_330')}” ({cite('1950_330', 'en')}), “{t('1953_262')}” ({cite('1953_262', 'en')}), “{t('1954_001')}” ({cite('1954_001', 'en')}) and “{t('1958_241')}” ({cite('1958_241', 'en')}). The stones scholars wrote about were mostly those that had just come to light, for instance out of church walls.

**The 1960s: Uppland and a little more.** {DT['1960-talet'][0]} texts, {DT['1960-talet'][1]} stones, and Uppland has {SH['1960-talet']['U']} per cent. Jansson wrote about “{t('1966_021')}” ({cite('1966_021', 'en')}) and “{t('1965_050')}” ({cite('1965_050', 'en')}) – one of the few times Östergötland appears at all. Östergötland has about a tenth of the runestones but only {SH['1960-talet']['Ög']} per cent of the mentions in the decade. From 1968 Elisabeth Svärdström writes the annual report “Runfynd” ({cite('1969_297', 'en')}).

**The 1970s: Runfynd year after year.** {DT['1970-talet'][0]} texts, {DT['1970-talet'][1]} stones. The “Runfynd” reports continue, written by Svärdström, Helmer Gustavson and Thorgunn Snædal. Gustavson's “{t('1976_096')}” ({cite('1976_096', 'en')}) mentions {SRC['1976_096'][1]} runestones, more than any other text before 1998. For once Östergötland gets its share, {SH['1970-talet']['Ög']} per cent, partly through Elias Wessén's “{t('1975_005')}” ({cite('1975_005', 'en')}).

**The 1980s: Södermanland.** {DT['1980-talet'][0]} texts, {DT['1980-talet'][1]} stones. Södermanland has {SH['1980-talet']['Sö']} per cent of the mentions, against {round(LAND_PC['Sö'])} per cent of the stones, spread over several texts: Jan Paul Strid's “{t('1980_187')}” ({cite('1980_187', 'en')}), the “Runfynd” reports and Mats G. Larsson's “{t('1986_098')}” ({cite('1986_098', 'en')}). Volker Weskamp wrote “{t('1987_001')}” ({cite('1987_001', 'en')}) and mentions {SRC['1987_001'][1] - 1} other stones in the same article. Östergötland is back at {SH['1980-talet']['Ög']} per cent.

**The 1990s: The carvers and the statistics.** {DT['1990-talet'][0]} texts, {DT['1990-talet'][1]} stones, and Uppland again has {SH['1990-talet']['U']} per cent. Frands Herschend's “{t('1998_097')}” ({cite('1998_097', 'en')}) mentions {SRC['1998_097'][1]} stones in an article on the carver Öpir's signatures. Mats G. Larsson wrote about Jarlabanke in “{t('1996_143')}” ({cite('1996_143', 'en')}) and about “{t('1999_196')}” ({cite('1999_196', 'en')}). Seven of the {len(TH)} dissertations in our register came in this decade.

**The 2000s: Single stones in depth.** {DT['2000-talet'][0]} texts, {DT['2000-talet'][1]} stones. Magnus Källström read the Frötuna stone in “{t('2008_233')}” ({cite('2008_233', 'en')}), Michael Lerche Nielsen wrote “{t('2003_195')}” ({cite('2003_195', 'en')}) and Larsson about “{t('2002_087')}” ({cite('2002_087', 'en')}). No text in the journals mentions a runestone from Västergötland by signum in the whole decade.

**The 2010s: Futhark and whole provinces.** Now something happens. {DT['2010-talet'][0]} texts mention {DT['2010-talet'][1]} different runestones, {en_n(IN2010)} times in all – more than in all earlier decades together ({en_n(PRE2010)}). It is Futhark that does it: {J10['futhark']} of the mentions are there. Uppland's share falls to {SH['2010-talet']['U']} per cent, for the first time since before 1950 below the province's share of the stones. The text that mentions most runestones of all is Per Stille's “{t('futhark_5_137_799768')}” ({cite('futhark_5_137_799768', 'en')}): {SRC['futhark_5_137_799768'][1]} stones, {SM['futhark_5_137_799768']} of them in Småland. After it come Magnus Källström's article on the carver Öpir ({cite('futhark_1_143_381125', 'en')}, {SRC['futhark_1_143_381125'][1]} stones), Klaus Düwel's “{t('futhark_4_31_682690')}” ({cite('futhark_4_31_682690', 'en')}, {SRC['futhark_4_31_682690'][1]}), Marco Bianchi's on inscriptions that run in several directions ({cite('futhark_5_115_799772', 'en')}, {SRC['futhark_5_115_799772'][1]}) and Maja Bäckvall's “{t('futhark_5_171_799781')}” ({cite('futhark_5_171_799781', 'en')}, {SRC['futhark_5_171_799781'][1]}). The Rök stone is mentioned by signum in {ROK[2010]} texts.

**The 2020s (to 2025): Östergötland catches up.** {DT['2020-talet'][0]} texts, {DT['2020-talet'][1]} stones. Östergötland has {SH['2020-talet']['Ög']} per cent of the mentions, more than its share of the stones – which has happened only once before, in the 1970s. Annett Krakow wrote “{t('37d3b87e-51fd-4a87-af76-294ffc35901a')}” ({cite('37d3b87e-51fd-4a87-af76-294ffc35901a', 'en')}), Patrik Larsson “{t('futhark_9-10_193_1385968')}” and Hanna Åkerström “{t('futhark_9-10_39_1385978')}” (both in {cite('futhark_9-10_39_1385978', 'en')}, dated 2020 in DiVA). The Rök stone is mentioned in {ROK[2020]} texts.

{chart_decades('en')}

The chart shows two things. For half a century, from the 1950s to the 2000s, about seven in ten mentions concerned a stone from Uppland, though Uppland has just over half the runestones. And Östergötland was almost silent in the same period, except in the 1970s. Both change with Futhark.

## The dissertations

The {len(TH)} dissertations in our register are spread unevenly over time: one in the 1970s (Salberger), {TH_DEC[1990]} in the 1990s, {TH_DEC[2000]} in the 2000s, {TH_DEC[2010]} in the 2010s and {TH_DEC[2020]} so far in the 2020s. In the 1990s came Henrik Williams on the ás-rune, Svante Lagman on the dotted runes, Mats G. Larsson on the journeys abroad, Rune Palm on regional variation, Marit Åhlén on Öpir, Torun Zachrisson on farms and cemeteries and Per Stille on Fjädrundaland. In the 2000s Laila Kitzler Åhfeldt on the carving traces, Linn Lager on the crosses, Patrik Larsson on the yr-rune, Thorgunn Snædal on Gotland, Kristel Zilmer on the journeys east, Magnus Källström on the carvers and Lisbeth Imer on chronology. Then Marjolein Stern on the images, Marco Bianchi and Hanna Åkerström on how the text is laid out on the stone, Jonas Nordby on cipher runes, Sofia Pereswetoff-Morath on the rune-inscribed metal amulets and Mueller-Vollmer on the names.

Several of them go through nearly every inscription for a single feature – a rune, a sign, a carver's hand. That is why many more stones are mentioned in the dissertations than in the journals, often in a list. Only two deal with a single province or district: Snædal with Gotland and Stille with Fjädrundaland.

## Which stones are mentioned – and which are not

Of the {en_n(N)} runestones, **{en_n(NEVER)}, {pc(NEVER, N)} per cent, are never mentioned by signum** in the four journals. {en_n(M['m2']['named_once'])} are mentioned just once. If we include the eight dissertations we can search, {en_n(NEVER_T)} stones, {pc(NEVER_T, N)} per cent, are mentioned nowhere in what we have at home apart from the editions.

Attention is unevenly spread. The {M['m2']['top5pct_n']} most-mentioned stones, five per cent of them all, account for {round(100 * M['m2']['top5pct_share'])} per cent of the mentions. The ten most mentioned:

{TOP_LIST_EN}

![The Rök stone]({ROK_IMG[0]})
The Rök stone (Ög 136) in Östergötland, the runestone mentioned in most texts – most of them after 2010. Photo: {ROK_IMG[2]}, {ROK_IMG[3]}, via [Wikimedia Commons]({ROK_IMG[1]}).

{chart_land('en')}

So what decides whether a stone gets mentioned? We let a statistical model weigh five things at once: the province, the style group, whether the stone survives, whether the carver is known and how long the text is. The model also takes into account that stones in the same parish are often mentioned in the same text, so that an article about a church with ten stones does not count as ten independent choices. The result is given as odds, the chance of being mentioned divided by the chance of not being mentioned. In brackets is an uncertainty interval: the range within which the true value very probably lies, given how many stones there are.

- **The length of the text matters most.** A stone with twice as long a text has {dbl_en} the odds of being mentioned, all else being equal. Of the quarter of the stones with the shortest texts, 22 runes or fewer, {pc(L3['Q1']['never_j'], L3['Q1']['n'])} per cent are never mentioned. Of the quarter with the longest, more than 62 runes, it is {pc(L3['Q4']['never_j'], L3['Q4']['n'])} per cent.
- **The lost stones are forgotten.** {en_n(F3['förlorad']['n'])} runestones are lost and known from older drawings and notes. {pc(F3['förlorad']['never_j'], F3['förlorad']['n'])} per cent of them are never mentioned, against {pc(F3['kvar']['never_j'], F3['kvar']['n'])} per cent of those that survive. Even with the length of the text taken into account, the odds are {lost_en}.
- **The carver plays no clear part.** Stones with a known carver are mentioned more often ({pc(R3['ristare']['n'] - R3['ristare']['never_j'], R3['ristare']['n'])} against {pc(R3['ingen']['n'] - R3['ingen']['never_j'], R3['ingen']['n'])} per cent), but they also have longer texts. Once length is counted in, no clear difference remains.
- **The period plays no clear part.** No style group, from the earliest stones to the late ones, is clearly mentioned more or less often than any other.
- **No province is clearly forgotten.** No province is mentioned clearly less often than Uppland. Östergötland's long silence has been made up since 2010, and over the whole period the difference is not clear. One province stands out the other way: Småland, with {dec_en(round(SMO[0], 1))} times the odds of Uppland (between {dec_en(round(SMO[1], 1))} and {dec_en(round(SMO[2], 1))}). But almost half of Småland's mentions, {SM['futhark_5_137_799768']} of {sum(SM.values())}, come from a single article – Stille's survey of Tiohärad. One scholar who takes on a whole district can change the picture for a whole province.

Nor do the old boundaries show any blind spots. Of the {M['m5_all']} hundreds (härader) with at least ten runestones, there is only one where nearly all the stones are missing from the journals, Gräsgård hundred on Öland ({M['m5'][0]['never']} of {M['m5'][0]['n']}). The silence does not lie in particular districts. It runs through all of them.

{chart_never('en')}

## What no one has asked

This is not a criticism. Journals are there for the new and the difficult: a find in a church wall, an inscription no one has been able to read, a carver who can be followed from stone to stone. The editions have already gone through every stone, one by one. But when a hundred years of texts are laid side by side, what no one has had reason to write about becomes visible.

**The ordinary stone.** Three in four of the stones with the shortest texts are never mentioned. And the short stones are the ordinary ones: someone raised the stone in memory of someone. One by one there is little to say about them. Together they are most of the material. Questions about the ordinary stone – who raised the short stones, where they stood, how they differ from the long ones – can only be asked by looking at all of them at once.

**The lost.** Two in three lost runestones are never mentioned. Many of them survive only as a woodcut or a drawing from the seventeenth and eighteenth centuries.

![Öl 17 in Bautil]({OL17_IMG[0]})
Öl 17 at Seby in Segerstad parish, Öland: “Þorgunnr raised this stone in memory of Ingjaldr, her brother.” The stone is lost, and it is mentioned neither in the journals nor in the dissertations we have. Translation: Scandinavian Runic-text Database. Woodcut: {OL17_IMG[2]}, {OL17_IMG[3]}, via [Wikimedia Commons]({OL17_IMG[1]}).

**The stones without a number in the main series.** {UNMEAS} runestones have a signum that cannot be searched for in running text – on Öland {M['unmeasurable']['Öl']} of {OL_ALL}, most of them fragments from Köping church. Whatever has been written about them cannot be found by searching for their number. That holds for us, and for everyone else who searches the databases.

**The stones without a style group.** {en_n(S3['n'])} of the {en_n(N)} stones, just over half, have no certain style group in the Scandinavian Runic-text Database. {pc(S3['never_j'], S3['n'])} per cent of them are never mentioned.

What is missing, then, is not care for the individual stones. It is questions that take all the stones at once – including the short ones, the lost ones and those no one has looked at closely.

In Vitki, each stone's page under [Inscriptions](/en/inskrifter) now shows which texts in the journals mention it. Anyone who wishes can see for themselves whether a stone has had its article – or whether it is still waiting.

## Our own limits

- We count signa, not place names. Before 1950 stones were mostly named by place, and even later the best-known are called by name. The Rök stone is undercounted in the earlier decades.
- We have counted only what we have at home. Books and several important journals are missing, and Namn och bygd and Current Swedish Archaeology cover only recent years.
- A mention is not a study. A stone in a list counts as much as a stone a whole article is about.
- The OCR text has errors. The sample was right in 100 cases out of 100, and we corrected the errors we found afterwards, but occasional false hits remain, mostly among stones with low numbers.
- Futhark is counted by its year of publication in DiVA, which for some volumes is later than the year on the cover.

:::box The essentials in brief
- Just over half of the Swedish runestones, {pc(NEVER, N)} per cent, are never mentioned by their number in Fornvännen, Futhark, Namn och bygd or Current Swedish Archaeology. Five per cent of the stones account for nearly a third of all mentions, and the Rök stone tops the list.
- From the 1950s to the 2000s about seven in ten mentions concerned a stone from Uppland, and much of it was about new finds. Östergötland was almost silent. With Futhark from 2010, attention spreads across the country.
- It is not the province or the period that decides whether a stone is mentioned, but how long its text is and whether it survives. The short and the lost stones are the ones no one writes about.
- A single scholar can change the picture: Per Stille's survey of Tiohärad accounts for nearly half of all mentions of stones from Småland.
:::

## Sources

{sources('en')}

The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. Fornvännen is freely available through the Swedish National Heritage Board's platform [pub.raa.se](https://pub.raa.se) (CC BY 4.0). Futhark is freely available in [DiVA](https://uu.diva-portal.org) and at [futhark-journal.com](http://www.futhark-journal.com) (volumes 1–5 CC BY-NC-ND 3.0, volume 6 CC BY-NC-ND 4.0, from volume 7 CC BY 4.0). Namn och bygd and Current Swedish Archaeology are freely available online (CC BY 4.0). The rules for the count and the scripts: [the analysis plan]({PLAN}) with two addenda."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|slump(?!vis)|nollmodell|null model|påståendedatabas|claims database|frågelista|question list|"
                      r"relevans|relevance|Rapport 0|Report 0|signifikan|p-värde|p-value", re.I)
labels = ["Forskning", "Geografi", "Datering och stil", "Tolkning", "Ristare"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
SERIES = re.compile(r"^Hundra år av runfrågor")  # web/src/lib/series.ts
assert SERIES.match(title)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M), "inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    assert "Claude" not in b and "språkmodell" not in b and "language model" not in b
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 2 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert all("Wikimedia Commons" in c and re.search(r"CC BY|CC0|public domain", c) for c in caps), caps
    for m in re.finditer(r":::chart[^\n]*\n(.*?)\n:::", b, re.S):
        assert "Diagram: Vitki" in m.group(1) or "Chart: Vitki" in m.group(1)
        for row in m.group(1).splitlines():
            if "|" in row:
                assert 0 <= float(row.split("|")[1].strip()) <= 100, row
    for s in (SLUG1, SLUG2):
        assert s in b
    # forskarna som lyfts fram
    for name in ("Jansson", "Svärdström", "Gustavson", "Wessén", "Strid", "Snædal", "Larsson", "Herschend", "Källström", "Stille", "Düwel",
                 "Bianchi", "Bäckvall", "Krakow", "Åkerström", "Williams", "Lagman", "Palm", "Åhlén", "Zachrisson",
                 "Kitzler Åhfeldt", "Lager", "Zilmer", "Imer", "Stern", "Nordby", "Pereswetoff-Morath", "Mueller-Vollmer",
                 "Salberger", "Weskamp", "Lerche Nielsen"):
        assert name in b, (lang, name)

OUT = {"slug": SLUG3, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
wc = lambda x: len(re.sub(r"\]\([^)]*\)", "]", x).split())  # noqa: E731
path = os.path.join(ROOT, "utdata", "blogg", "hundra_ar_3.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, wc(body), "ord sv,", wc(body_en), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published") and old.get("slug") == SLUG3, "Bara det opublicerade utkastet skrivs över härifrån"
        ref.set({**OUT, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc, SLUG3)
    else:
        assert not [p for p in blog._all() if p.get("slug") == SLUG3], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**OUT, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Forskningshistoria|hundra år av runfrågor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG3)
    blog._forget()
