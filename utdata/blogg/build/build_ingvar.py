"""Artikeln "Var det bara Ingvar?" (sv + en): berättelsen om självkontrollen av östandelen i "Vikingarnas värld – vilka
platser nämner de?" (slug vikingarnas-varld). Planerad publicering 8 december 2026 (PUBLICERINGSPLAN.md); Viktor
publicerar själv.

Alla siffror läses ur den låsta självkontrollens resultat (analysplaner/2026-11-10-sjalvkontroll-osterled.md, 4d00080;
utdata/varlden/sjalvkontroll/resultat.json) och ur Rundata, och låses med assert. Runtexterna står ordagrant som i
Rundatas normalisering. Litteraturcitaten är kontrollerade mot Fornvännens fria fulltext (OCR i
downloads/tidskrifter/fornvannen/text; Sindbæks stycke dessutom mot sidbilden, s. 180, 2026-11-10, eftersom OCR:en
läser æ fel) och länkas till pub.raa.se.
    ../../../.venv/bin/python build_ingvar.py [--write | --update DOC]"""
import csv
import datetime as dt
import io
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, commons  # noqa: E402

V = os.path.join(ROOT, "utdata", "varlden")
SKDIR = os.path.join(V, "sjalvkontroll")
SK = json.load(open(os.path.join(SKDIR, "resultat.json"), encoding="utf-8"))
recs = json.load(open(os.path.join(ROOT, "data", "rundata.json")))
recs = recs if isinstance(recs, list) else recs.get("inscriptions", list(recs.values()))
BY = {r["signum"]: r for r in recs}
REGION = {p["plats"]: p["region"] for p in csv.DictReader(open(os.path.join(V, "platser.csv"), encoding="utf-8"))}
ROWS = {r["text"]: r for r in csv.DictReader(open(os.path.join(V, "platser_per_text.csv"), encoding="utf-8"))
        if r["korpus"] == "runstenar_sverige"}

pc = lambda x: round(100 * x)  # noqa: E731


def ci(d, key="ci"):
    return pc(d[key][0]), pc(d[key][1])


# ---- P1: östandelen med och utan Ingvarsstenarna (den låsta planen) ----------------------------------------------------
P1 = SK["p1"]
assert SK["plan"] == "analysplaner/2026-11-10-sjalvkontroll-osterled.md"
assert P1["dom"] == "försvagat (obestämt)"
ING = P1["ingvarsstenar"]
N_ING = P1["antal_ingvarsstenar"]
assert N_ING == len(ING) == P1["antal_ingvar_med_plats"] == 25
ALL, UI, B = P1["alla"], P1["utan_ingvar"], P1["beskrivande"]
assert UI["ci"][0] < 0.5 < UI["ostandel"], "försvagat: punktskattningen över hälften, intervallet omfattar hälften"
ALL_P, (ALL_LO, ALL_HI) = pc(ALL["ostandel"]), ci(ALL)
UI_P, (UI_LO, UI_HI) = pc(UI["ostandel"]), ci(UI)
assert (ALL_P, ALL_LO, ALL_HI, UI_P, UI_LO, UI_HI) == (66, 58, 74, 58, 49, 67)
SURPLUS, DROP = pc(ALL["ostandel"] - 0.5), pc(ALL["ostandel"] - UI["ostandel"])
assert (SURPLUS, DROP) == (16, 8) and 0.4 < (ALL["ostandel"] - UI["ostandel"]) / (ALL["ostandel"] - 0.5) < 0.6, "ungefär hälften"
assert round(P1["skillnad_pe"]) == -DROP
GRP = P1["ingvar_gruppens_platser"]
GRP_O, GRP_V = int(GRP["O"]), int(GRP["V"])
OST_ALL, OST_ING = P1["oststenar"]["alla"], P1["oststenar"]["varav_ingvar"]
assert OST_ING == N_ING and OST_ING / OST_ALL > 0.25, "mer än var fjärde sten som nämner öster"
UI_N = UI["stenar"]
ONE, NARROW, KNUT, BOTH = (B[k] for k in ("ingvar_som_en_text", "smal_definition", "utan_knut", "utan_ingvar_och_knut"))
N_KNUT, N_NARROW = len(B["knutsstenar"]), NARROW["antal"]
assert {pc(ONE["ostandel"]), pc(NARROW["ostandel"]), pc(BOTH["ostandel"])} == {59} and pc(KNUT["ostandel"]) == 67
SAG = B["sagor_publicerade"]
FA, HK, IS = SAG["fornaldarsagor"], SAG["heimskringla"], SAG["islanningasagor"]
assert UI["ci"][0] > HK["ci"][1] and UI["ci"][0] > IS["ci"][1], "utan Ingvar: ingen överlappning med Heimskringla och islänningasagorna"
assert pc(UI["ostandel"]) == pc(FA["ostandel"]) == 58, "texten: i nivå med fornaldarsagorna"
assert pc(ALL["ostandel"]) > pc(FA["ostandel"])
IS_P, (IS_LO, IS_HI), HK_P, FA_P = pc(IS["ostandel"]), ci(IS), pc(HK["ostandel"]), pc(FA["ostandel"])

# ---- P2 och tidskurvan ---------------------------------------------------------------------------------------------------
P2 = SK["p2"]["huvud_med_ingvar"]
assert P2["dom"] == "för få träffar" and not P2["enough"]
LATE_N, MIN_N = int(P2["platser"]["sen"]), 20
assert LATE_N < MIN_N
assert SK["p2"]["huvud_utan_ingvar"]["dom"] == "för få träffar"
assert SK["p2"]["rob_trend_mittar"]["or"] > 1 and SK["p2"]["rob_trend_mittar_utan_ingvar"]["or"] > 1, "lutningen pekar mot öster, inte väster"
K = SK["kurva"]
KM = {g["stil"]: g for g in K["med_ingvar"]}
KU = {g["stil"]: g for g in K["utan_ingvar"]}
EARLY_P, LATE_P = pc(K["med_ingvar_tidig"]["ostandel"]), pc(K["med_ingvar_sen"]["ostandel"])
EARLY_UI = pc(K["utan_ingvar_tidig"]["ostandel"])
assert (EARLY_P, LATE_P, EARLY_UI) == (65, 67, 53)
RAK_P, RAK_N, RAK_UI = pc(KM["RAK"]["ostandel"]), KM["RAK"]["stenar"], pc(KU["RAK"]["ostandel"])
assert RAK_P == min(pc(g["ostandel"]) for g in K["med_ingvar"]), "RAK ser mest mot väster"
FP_P, FP_N, FP_UI = pc(KM["Fp"]["ostandel"]), KM["Fp"]["stenar"], pc(KU["Fp"]["ostandel"])
FP_ING = KM["Fp"]["stenar"] - KU["Fp"]["stenar"]
assert FP_P == max(pc(g["ostandel"]) for g in K["med_ingvar"] if g["ci"]), "Fp: toppen bland grupper med intervall"
assert FP_ING == sum(1 for s in ING if BY[s]["style"] == "Fp" and not BY[s]["style_uncertain"]) == 15
assert 2 * FP_ING > FP_N, "mer än hälften av Fp-gruppens stenar"


def stil(r):
    return (r.get("style") or "").replace(" [Gräslund muntligt]", "").strip()


# RAK-stenarna: vilket land nämns oftast?
RAK = [s for s, r in ROWS.items() if stil(BY[s]) == "RAK" and not BY[s]["style_uncertain"]
       and any(int(r[p]) for p, g in REGION.items() if g in ("öster", "väster"))]
assert len(RAK) == RAK_N
RAK_CT = {p: sum(1 for s in RAK if int(ROWS[s][p])) for p, g in REGION.items() if g in ("öster", "väster")}
LANDS = {p: n for p, n in RAK_CT.items() if "allmänt" not in p}
RAK_ENG = LANDS["England"]
assert RAK_ENG == max(LANDS.values()) == 9 and sorted(LANDS.values())[-2] < RAK_ENG
RAK_WGEN = RAK_CT["Västerled (allmänt)"]
assert RAK_WGEN == RAK_ENG, "lika många säger bara 'i väster'"
assert stil(BY["Sö 131"]) == "RAK" and not BY["Sö 131"]["style_uncertain"] and "Sö 131" in ING
assert KM["RAK"]["stenar"] - KU["RAK"]["stenar"] == 1

# ---- de tjugofem stenarna: människorna -----------------------------------------------------------------------------------
PROV = {k: sum(1 for s in ING if s.split()[0] == k) for k in ("Sö", "U", "Ög", "Vs", "M")}
assert sum(PROV.values()) == N_ING and PROV["Sö"] == 13 and PROV["U"] == 8 and "M 4" in ING
REL = {"far": ["Sö 107", "Sö 108", "Sö 254", "U 1143", "U 439", "U 644", "U 654", "U 661"],
       "son": ["Sö 105", "Sö 179", "Sö 9", "U 778", "Ög 155", "Ög 30"],
       "bror": ["Sö 131", "Sö 287", "Sö 320", "Sö 335", "U Fv1992;157"],
       "styvson": ["Vs 19"],
       "oklar": ["M 4", "Sö 173", "Sö 277", "Sö 281", "U 837"]}  # skadad text, eller (Sö 173) två män
RX = {"far": r"\b(their|his|her) father\b", "son": r"\b(their|his|her|her/his) sons?\b", "bror": r"\b(their|his) brother\b",
      "styvson": r"\bstepson\b"}
assert sorted(sum(REL.values(), [])) == sorted(ING)
for k, rx in RX.items():
    for s in REL[k]:
        assert re.search(rx, BY[s]["translation_en"]), (k, s)
assert "brother" in BY["Sö 173"]["translation_en"] and "father" in BY["Sö 173"]["translation_en"]
N_FAR, N_SON, N_BROR, N_OKLAR = (len(REL[k]) for k in ("far", "son", "bror", "oklar"))
assert (N_FAR, N_SON, N_BROR, N_OKLAR) == (8, 6, 5, 5)
SERK = sorted(s for s in ING if int(ROWS[s]["Serkland"]))
assert SERK == ["Sö 131", "Sö 179", "Sö 281", "U 439"] and "Serkland(?)" in BY["U 439"]["translation_en"]
ASKIL = sorted(s for s in ING if any(c["name"] == "Äskil 2" and not c["uncertain"] for c in BY[s]["carvers"]))
ASKIL_Q = sorted(s for s in ING if any(c["name"] == "Äskil 2" and c["uncertain"] for c in BY[s]["carvers"]))
assert ASKIL == ["Sö 179", "U 439", "U 644", "U 661", "U 778", "U 837"] and ASKIL_Q == ["U 654"]
assert any(c["name"] == "Äskil 2" and c["kind"] == "S" for c in BY["U 778"]["carvers"])


def norm(s):
    return BY[s]["normalization"].replace('"', "").strip()


SO173 = "Hann hafði vestarla um vaRit længi, dou austarla með Ingvari."
U778 = "Es atti æinn seR skip ok austr styrði i Ingvars lið."
U778_SIGN = "Æskell ræist."
U654 = "Es kunni val knærri styra."
SO9 = "Hann ændaðis með Ingvari."
SO320 = "dræng sniallan, sun LiføyaR"
for s, q in (("Sö 173", SO173), ("U 778", U778), ("U 778", U778_SIGN), ("U 654", U654), ("Sö 9", SO9), ("Sö 320", SO320)):
    assert q in norm(s), (s, q)
assert norm("Sö 173").startswith("§A Myskia ok Manni/Mani letu ræisa kumbl þausi at broður sinn HroðgæiR ok faður sinn Holmstæin.")
assert norm("U 778").startswith("Þialfi ok Holmlaug letu ræisa stæina þessa alla at Banka/Bagga, sun sinn.")
assert norm("Sö 9").startswith("Bergviðr/Barkviðr ok þau Hælga ræistu stæin þannsi at Ulf, sun sinn.")
assert norm("Sö 179").startswith("Tola let ræisa stæin þennsa at sun sinn Harald, broður Ingvars.")
assert "ræistu stæin þenna æftiR Gunnlæif, faður sinn. Es vas austr með Ingvari drepinn." in norm("U 654")
assert "U 540" not in ING and "Greece" in BY["U 540"]["translation_en"]
assert "Ög 30" in ING and "in memory of Ingvarr, his son. He died in the east" in BY["Ög 30"]["translation_en"]
assert "Ög 30" not in ING or N_NARROW < N_ING
assert "skipari Holmstæins" in norm("Sö 335") and "brukar" not in SO320
assert "Gunnleifr, their father" in BY["U 654"]["translation_en"] and "Andvéttr and Kárr and <kiti> and Blesi and Djarfr" in BY["U 654"]["translation_en"]
assert all("Ingvar" in BY[s]["translation_en"] for s in ASKIL), "Äskils sex stenar nämner alla Ingvar"
assert "son of Lífey" in BY["Sö 320"]["translation_en"] and "their brother" in BY["Sö 320"]["translation_en"]

# Två Serklandsstenar utan Ingvars namn står kvar enligt planens definition. Räkneexempel UTANFÖR planen (bara
# punktskattning): samma mått, utan också dem.


def share(excl):
    o = v = 0
    for s, r in ROWS.items():
        if s in excl:
            continue
        o += sum(1 for p, g in REGION.items() if g == "öster" and int(r[p]))
        v += sum(1 for p, g in REGION.items() if g == "väster" and int(r[p]))
    return o, v, o / (o + v)


assert share(set()) [:2] == (ALL["O"], ALL["V"]) and share(set(ING))[:2] == (UI["O"], UI["V"]), "samma mått som analysen"
SERK_UTAN = sorted(s for s, r in ROWS.items() if int(r["Serkland"]) and s not in ING)
assert SERK_UTAN == ["Sö 279", "U 785"]
assert "Serkland" in BY["Sö 279"]["translation_en"] and "Eimundr's son" in BY["Sö 279"]["translation_en"]
EXTRA_P = pc(share(set(ING) | set(SERK_UTAN))[2])
assert EXTRA_P == 57

# ---- litteraturen: citaten kontrollerade mot fulltexten -------------------------------------------------------------------
FV = os.path.join(ROOT, "..", "downloads", "tidskrifter", "fornvannen")
IDX = {}
for line in open(os.path.join(FV, "index.jsonl"), encoding="utf-8"):
    d = json.loads(line)
    IDX.setdefault(d["key"], d)


def flat(x):
    return re.sub(r"\s+", "", x).replace("-", "")


def check(key, *frags):
    t = flat(open(os.path.join(FV, "text", key + ".txt"), encoding="utf-8").read())
    for f in frags:
        assert flat(f) in t, (key, f)
    assert IDX[key]["licence"] == "https://creativecommons.org/licenses/by/4.0/"
    return IDX[key]["uri"]


SINDBAEK = ("Endelig kendes ikke mindre end 96 svenske runesten som nævner personer som var rejst *austr i Garðr*, eller "
            "helt til *Griklandi* eller *Serkland* … Runestenene taler selv på dette tidspunkt ofte om særlige "
            "heltebedrifter som Ingvar Vidfarnes togt til Det kaspiske Hav, der alene tegner sig for mere end 25 sten.")
# OCR:en läser æ som ae/a och 'taler' som 'tåler'; texten ovan är jämförd med sidbilden (s. 180).
URL_SINDBAEK = check("2003_179", "kendes ikke mindre end 96 svenske runesten", "Vidfarnes", "Det kaspiske Hav",
                     "tegner sig for mere end 25 sten", "Alle disse kilder er imid", "fra 1 1. årk. eller senere")
WESTIN = ("De svenska vikingatågen voro huvudsakligen riktade mot öster. Mot slutet av vikingatiden inträder emellertid "
          "en förskjutning. Den östra vägen genom Ryssland till Orienten blir av flera orsaker mindre betydande för nordborna.")
URL_WESTIN = check("1941_085", WESTIN, "också genom runstenarnas vittnesbörd, att många svear drogo i västerled",
                   "arabiska mynten som dominera i de skandinaviska skattefynden, senare dominera de västerländska mynten")
THULIN = ("Sagan säger att Ingvar dog år 1041, en uppgift som trots sin otillförlitlighet blivit den fastaste punkten i "
          "de uppländska runstenarnas kronologi.")
URL_THULIN = check("1985_190", "Sagan säger att Ingvar", "dog år 1041, en uppgift som trots sin otillför",
                   "litlighet blivit den fastaste punkten i de upp", "ländska runstenarnas kronologi",
                   "dateras till 1030-1031")
URL_KRAKOW = check("37d3b87e-51fd-4a87-af76-294ffc35901a",
                   "used by a large number of runologists as a chronological pillar for the dating of the Upplandic runestones in general",
                   "does not seem to support a dating to c.1040, but to c.1020", "Adam’s dating of the death of King Óláfr Eiríksson to 1039")
URL_LARSSON = check("a82dcf86-2d49-4dd9-9f40-bf1b071ce2c5", "1040 (1036–1041 enligt sagans kronologi)",
                    "strider mot petjenegerna år 1036", "stenarna att de i många fall är resta över män",
                    "som återvänt välbehållna och fått en runsten rest", "Fornvännen 116:101–113")
URL_KRAKOW2 = check("825a2fdb-65e8-4e8f-9467-5abe459f1be2", "brukar klassificeras som syftande till Ingvarstå",
                    "Toponymet Serkland finns också i några andra")
assert IDX["2003_179"]["authors"] == ["Sindbæk, Søren M."] and IDX["1941_085"]["authors"] == ["Westin, Gunnar"]
assert IDX["1985_190"]["authors"] == ["Thulin, Alf"]

GH = "https://github.com/Precatio/runes/blob/main"
PLAN = f"{GH}/analysplaner/2026-11-10-sjalvkontroll-osterled.md"
RES = f"{GH}/utdata/varlden/sjalvkontroll/resultat.md"

# ---- fotografier (Wikimedia Commons) ----------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["Sö 173", "U 778"])
INFO = commons.commons_info(list(FILES.values()))
IMG = {s: INFO[f] for s, f in FILES.items()}
for s in ("Sö 173", "U 778"):
    assert IMG[s]["licence"] == "CC BY 2.5" and IMG[s]["author"] == "Berig", (s, IMG[s])


def credit(s, lang):
    i = IMG[s]
    return f"{'Foto' if lang == 'sv' else 'Photo'}: Berig, [{i['licence']}]({i['licence_url']}), via [Wikimedia Commons]({i['page']})."


# ---- tidskurvan (samma figur som sjalvkontroll/kurva.py, på svenska och engelska) ------------------------------------------
def draw(lang):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sv = lang == "sv"
    ink, muted, grid, surf = "#222222", "#6b6b6b", "#e6e6e3", "#fcfcfb"
    series = [("med_ingvar", "Alla stenar" if sv else "All stones", "#b7410e", -0.12, "o"),
              ("utan_ingvar", "Utan Ingvarsstenarna" if sv else "Without the Ingvarr stones", "#1f74a8", 0.12, "s")]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    fig.patch.set_facecolor(surf)
    ax.set_facecolor(surf)
    for key, label, col, dx, mk in series:
        for i, g in enumerate(K[key]):
            x = i + dx
            if g["ci"]:
                ax.plot([x, x], [100 * g["ci"][0], 100 * g["ci"][1]], color=col, lw=2, solid_capstyle="round", alpha=0.55)
            ax.plot(x, 100 * g["ostandel"], mk, color=col, ms=8, mec=surf, mew=2, label=label if i == 0 else None)
    ax.axhline(50, color=muted, lw=1, ls=(0, (3, 3)))
    ax.text(len(K["med_ingvar"]) - 0.5, 51, "hälften" if sv else "half", color=muted, fontsize=8, ha="right", va="bottom")
    unit = "st." if sv else "stones"
    ax.set_xticks(range(len(K["med_ingvar"])),
                  [f"{g['stil']}\n{g['ar'][0]}–{g['ar'][1]}\n{g['stenar']} {unit}" for g in K["med_ingvar"]], fontsize=8, color=ink)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Östandel av platserna (%)" if sv else "Share of places in the east (%)", color=ink, fontsize=9)
    ax.grid(axis="y", color=grid, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(grid)
    ax.tick_params(colors=muted, labelsize=8)
    ax.legend(frameon=False, fontsize=8, loc="lower right", labelcolor=ink)
    ax.set_title("Östandel per stilgrupp (svenska runstenar, säker stilgrupp)" if sv else
                 "Share of places in the east by style group (Swedish runestones, certain style group)", color=ink, fontsize=10, loc="left")
    fig.text(0.01, 0.01, "Linje = 95 %-intervall (bara grupper med minst 10 platser). Antal stenar avser alla stenar. "
             "Diagram: Vitki, efter Rundata och Gräslunds stildatering." if sv else
             "Line = 95 % interval (only groups with at least 10 places). Number of stones refers to all stones. "
             "Chart: Vitki, after Rundata and Gräslund's style dating.", fontsize=7, color=muted)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=surf)
    plt.close(fig)
    out = os.path.join(ROOT, "utdata", "blogg", "ingvar")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, f"tidskurva_{lang}.png"), "wb").write(buf.getvalue())
    return blog_figures.freeze(buf.getvalue())


FIG = {lang: draw(lang) for lang in ("sv", "en")}


# ---- diagrammet över räknesätten -----------------------------------------------------------------------------------------
def chart(lang):
    sv = lang == "sv"
    rows = [(ALL, "Alla stenar (den publicerade siffran)" if sv else "All stones (the published figure)", True),
            (UI, f"Utan de {N_ING} Ingvarsstenarna" if sv else f"Without the {N_ING} Ingvarr stones", True),
            (ONE, "Ingvarståget räknat som en enda text" if sv else "The Ingvarr expedition counted as a single text", False),
            (NARROW, "Bara stenar med Ingvar som ledare borträknade" if sv else "Only stones naming Ingvarr as leader removed", False),
            (BOTH, "Utan både Ingvar och Knuts gäld" if sv else "Without both Ingvarr and Knútr's payment", False),
            (KNUT, "Utan Knuts gäld (väster), Ingvar kvar" if sv else "Without Knútr's payment (west), Ingvarr kept", False)]
    out = [":::chart Hur stor del av platserna som ligger i öster, räknat på olika sätt" if sv else
           ":::chart Share of the places that lie in the east, counted in different ways"]
    for d, label, hi in rows:
        lo, up = ci(d)
        note = f"troligen mellan {lo} och {up} %" if sv else f"probably between {lo} and {up} %"
        out.append(f"{'+' if hi else ''}{label} | {pc(d['ostandel'])} | {note}")
    out.append("Källa: Vitkis räkning i Samnordisk runtextdatabas; varje plats räknas en gång per sten. Diagram: Vitki." if sv else
               "Source: Vitki's count in the Scandinavian Runic-text Data Base; each place counted once per stone. Chart: Vitki.")
    return "\n".join(out) + "\n:::"


# ---- texten -------------------------------------------------------------------------------------------------------------------
title = "Vikingarnas österled – eller bara Ingvars?"
summary = (f"Runstenarna ser mot öster, skrev vi i en tidigare artikel. Men {N_ING} av stenarna minns samma färd: Ingvars "
           "tåg mot Serkland. Vi räknade bort dem efter en plan som låstes i förväg. Ungefär halva österns övervikt "
           "försvann – och det visade sig att samma tåg också är ett av ankarna för när runstenarna restes.")

body = f"""*{SO173}*

Han hade länge varit i väster. Han dog i öster, med Ingvar.

Raden står på en sten vid Tystberga i Södermanland (Sö 173). Myskja och Manni lät resa den efter sin bror Hróðgeirr och sin far Holmsteinn. Vem av dem som hade varit länge i väster säger stenen inte. Men den säger något som få runstenar säger: att en och samma man kunde ha båda väderstrecken i sitt liv. Först väster, sedan öster, i ett följe som inte kom tillbaka.

![Runstenen Sö 173]({IMG['Sö 173']['thumb']})
Sö 173 vid Tystberga: ”Han hade länge varit i väster, dog i öster med Ingvar.” {credit('Sö 173', 'sv')}

I artikeln [Vikingarnas värld – vilka platser nämner de?](/artiklar/vikingarnas-varld) räknade vi alla platser utanför Norden som nämns på de svenska runstenarna. Två av tre låg i öster, {ALL_P} %. Den här artikeln handlar om vad som hände när vi vände oss mot vår egen siffra och frågade om den håller.

## En invändning i en bisats

Tänk dig att du läser alla dödsannonser i en kustort under femtio år och märker att påfallande många handlar om havet. Sedan ser du att en stor del av dem kom samma höst, efter ett enda förlis. Havet var farligt, det står fast. Men din siffra säger mindre om hur ofta folk for till sjöss än om en enda natt.

Den invändningen mot vår siffra fanns redan i litteraturen, i en bisats. Den danske arkeologen Søren Sindbæk skrev 2003 i Fornvännen om något helt annat, om när vikingarnas vägar genom Ryssland öppnades, och nämnde i förbigående runstenarna:

> {SINDBAEK}

Slutligen känner vi inte mindre än 96 svenska runstenar som nämner personer som rest österut till Garðar, eller ända till Grekland eller Serkland … Runstenarna talar vid den här tiden ofta om särskilda hjältedåd, som Ingvar den vittfarnes tåg till Kaspiska havet, som ensamt står för mer än 25 stenar (Sindbæk 2003, s. 180).

Om det stämmer kan vår östandel vara Ingvars förlis snarare än en hel generations väg. Det gick inte att veta utan att räkna. Så innan vi räknade skrev vi ner reglerna: vilka stenar som räknas som Ingvarsstenar, och vad som skulle få oss att säga att resultatet håller, är försvagat eller faller. [Planen]({PLAN}) låstes den 10 november 2026, och först därefter räknades något.

## Ingvars män

Vår definition var medvetet vid. En sten räknas om den nämner Ingvar som ledare för en färd, eller om den nämner namnet Ingvar och dessutom en plats i öster. Hellre en sten för mycket än en för lite, för det gör det svårare för vår egen siffra att klara sig. Tjugosex stenar fångades. En av dem, U 540, tog vi bort när vi läste texten: där är Ingvar en av dem som reste stenen, och den döde dog i Grekland, utan något som knyter honom till tåget. Kvar blev {N_ING}, lika många som Sindbæk räknade.

De står från Medelpad i norr till Östergötland i söder, men de flesta i Södermanland ({PROV['Sö']}) och Uppland ({PROV['U']}). Läser man dem i följd är de en ovanligt tät samling människor.

Åtta av de döda var fäder, och det var deras barn som reste stenen. Sex var söner, fem var bröder och en var styvson. På de övriga fem är texten för skadad för att säga vem som minns vem, eller så minns stenen två män. I Svinnegarn i Uppland reste Þjalfi och Holmlaug stenar efter sin son Banki: *{U778}* – som ensam ägde ett skepp och styrde österut i Ingvars följe (U 778). Vid Varpsund reste fem söner en sten efter sin far Gunnleifr, som dräptes i öster med Ingvar, och lade till en rad om vad han kunde: *{U654}* – han kunde styra ett lastskepp väl (U 654). Vid Lifsinge i Södermanland reste Bergviðr och Helga en sten efter sin son Ulfr: *{SO9}* – han fick sitt slut med Ingvar (Sö 9). Vid Stäringe minns tre bröder en fjärde, Bjórsteinn, och nämner hans mor vid namn: *{SO320}*, en duktig och tapper man, Lífeys son (Sö 320). Och vid Gripsholm står Tolas sten efter sonen Harald, Ingvars bror, som vi läste i den förra artikeln (Sö 179).

Serkland, landet där de dog, nämns på fyra av stenarna, på en av dem med frågetecken (U 439). Skeppen nämns på fler: den som styrde, den som ägde, den som var med i en annans skeppslag. Och flera av stenarna har samma hand. Rundata knyter sex av dem till ristaren Äskil, och en sjunde med frågetecken. På en av dem har han själv skrivit sitt namn: *{U778_SIGN}* – Äskil ristade (U 778).

Det är det första skälet att ta Sindbæks bisats på allvar. De {N_ING} stenarna är inte {N_ING} oberoende vittnen om vart svearna for. De är ett vittnesmål, upprepat av de familjer som drabbades, ofta av samma ristare. Av de {OST_ALL} stenar i vårt urval som nämner en plats i öster är {OST_ING} Ingvarsstenar, mer än var fjärde.

![Runstenen U 778]({IMG['U 778']['thumb']})
U 778 i Svinnegarns kyrka: Banki ”ägde ensam ett skepp och styrde österut i Ingvars följe”. {credit('U 778', 'sv')}

## Vad som blir kvar

Ingvarsstenarna nämner {GRP_O} platser i öster och {GRP_V} i väster. Räknar man bort dem sjunker östandelen från {ALL_P} till {UI_P} %.

Det är en stor rörelse för en enda färd. Av de {SURPLUS} procentenheter som runstenarna låg över hälften står Ingvarsstenarna för {DROP}. Ungefär halva österns övervikt är alltså ett tåg.

Det som blir kvar är dessutom osäkrare än vi skulle vilja. Med {UI_N} stenar kvar ligger östandelen troligen mellan {UI_LO} och {UI_HI} %. Eftersom hälften ligger inom det spannet kan vi inte utesluta att stenarna, utan Ingvar, nämnde öster och väster ungefär lika ofta. (Spannet räknade vi genom att dra stenarna på nytt tiotusen gånger, så att en sten som nämner många platser inte väger som många stenar.) Planens dom blir därför: försvagat. Den bästa skattningen ligger fortfarande över hälften, men vi kan inte längre säga att stenarna tydligt ser mot öster.

Vi räknade också på andra sätt, och alla pekar åt samma håll:

{chart('sv')}

Räknas tåget som en enda text, i stället för att strykas helt, landar andelen på {pc(ONE['ostandel'])} %. Stryks bara de {N_NARROW} stenar som uttryckligen nämner Ingvar som ledare blir det också {pc(NARROW['ostandel'])} %. Väster har ingen motsvarighet. Stenarna om Knuts gäld i England är bara {N_KNUT}, och tar man bort dem ändras nästan ingenting ({pc(KNUT['ostandel'])} %). Ingen händelse i väster väger på stenarna som Ingvars i öster.

## Det som håller

Det låter som en förlust, och till en del är det en. Men det viktigaste i den förra artikeln var inte att stenarna ser mot öster i sig. Det var jämförelsen: att runstenarna och islänningarnas sagor om sina egna förfäder ser åt olika håll, och att sagorna om forntiden liknar stenarna.

Den jämförelsen står kvar. Islänningasagorna har {IS_P} % öster, troligen mellan {IS_LO} och {IS_HI} %, och kungasagorna i Heimskringla {HK_P} %. Runstenarna utan Ingvar, {UI_P} %, överlappar ingen av dem. Med Ingvar låg stenarna högre än alla sagor. Utan honom hamnar de i nivå med fornaldarsagorna, sagorna om tiden före Islands bebyggelse, som också har {FA_P} %. Det är en lustig symmetri, eftersom sagan om Ingvar själv räknas till fornaldarsagorna, och mer än så ska vi inte göra av den. Men hypotesen från förra gången, att österleden på Island hade blivit forntid, vilar inte på Ingvar.

## Westin och tiden

Den andra invändningen är äldre. Gunnar Westin skrev 1941, i en artikel om en ryttargrav i Västmanland:

> {WESTIN}

(Westin 1941, s. 93.) Han stödde sig mest på skattfynden – arabiska mynt dominerar fram till 900-talets mitt eller senare del, sedan västerländska – men han nämnde också runstenarna, där många svear drog i västerled och fick del av de gälder som den engelske kungen tvingades betala.

Om Westin har rätt borde de yngre runstenarna se mer mot väster än de äldre. Runstenarna har inga årtal, men de kan ordnas efter ornamentiken, i de stilgrupper som Rundata anger efter Anne-Sofie Gräslund, med ungefärliga år: RAK omkring 980–1015, Fp 1010–1050 och så vidare till Pr5, 1100–1130.

Svaret är att vi inte kan avgöra det. Stenarna i de sena stilgrupperna, efter omkring 1050, nämner bara {LATE_N} platser, och planen krävde minst {MIN_N} för en dom. Det vi kan göra är att visa kurvan.

![Östandel per stilgrupp, med och utan Ingvarsstenarna]({FIG['sv']})
Hur stor del av platserna som ligger i öster, stilgrupp för stilgrupp, med och utan Ingvarsstenarna. Prickarna är andelen, strecken visar var den troligen ligger (bara för grupper med minst tio platser). Stilgrupperna har Gräslunds ungefärliga år, inte årtal ur texterna. Diagram: Vitki, efter Rundata och Gräslunds stildatering.

Kurvan visar ingen förskjutning mot väster. Stenarna före omkring 1050 har {EARLY_P} % öster, de senare {LATE_P} %. Om något lutar kurvan åt andra hållet, men den vilar på för få sena stenar för att vi ska bygga något på det.

Två saker syns ändå tydligt. Den första är att de äldsta stenarna, RAK-gruppen omkring år 1000, är de som ser mest mot väster: {RAK_P} % öster. England är det land de nämner oftast, på {RAK_ENG} av {RAK_N} stenar, och lika många säger bara ”i väster”. Väst kom alltså inte sist på stenarna, utan först. Mats G. Larsson påpekar dessutom att Englandsstenarna i många fall restes över män som kommit hem välbehållna och fick sin sten först när de dött hemma (Larsson 2021). Resan kan alltså vara äldre än stenen.

Den andra är toppen i Fp-gruppen, 1010–1050: {FP_P} % öster. Av gruppens {FP_N} stenar är {FP_ING} Ingvarsstenar. Utan dem sjunker toppen till {FP_UI} %. Den östliga höjdpunkten mitt i 1000-talet är, i vårt material, till stor del ett och samma tåg.

Westins förskjutning kan mycket väl ha skett. Men i så fall hör den till skattfyndens 900-tal, som runstenarna inte når.

## Den fastaste punkten

Här kommer det som gör kontrollen viktigare än en rättelse. Alf Thulin skrev 1985:

> {THULIN}

(Thulin 1985, s. 201.) Runstenarna har få säkra årtal. Ett av de viktigaste kommer inte från stenarna själva, utan från en isländsk saga skriven långt senare. Och året är omstritt. Thulin hade själv föreslagit 1030–1031. Annett Krakow föreslog 2021 i Fornvännen att tåget i stället hör till omkring 1020: sagans tidsram bygger enligt henne på Adam av Bremens sena år för Olof Skötkonungs död, och Ingvarsstenarnas enkla ornamentik passar bättre med 1020. Hon skriver också att tågets datering har använts av många runologer som en kronologisk stöttepelare för de uppländska runstenarna i allmänhet. Mats G. Larsson svarade i samma årgång och höll fast vid omkring 1040, bland annat med furst Jaroslavs strider mot petjenegerna år 1036. Krakow svarade i sin tur. Frågan är öppen.

En detalj i vår egen tabell passar in här. Skarðis sten vid Lundby (Sö 131), en av de mest kända Ingvarsstenarna, står i Rundata i RAK, den grupp som brukar dateras till 980–1015. Antingen är stenen äldre än 1041 tillåter, eller så överlappar stilgrupperna mer än deras årtal. Vi kan inte avgöra vilket.

Så här hänger det ihop. Ingvars tåg är både en stor del av svaret på frågan *var*, mer än var fjärde sten som nämner öster, och ett av ankarna för frågan *när*. Den som ritar en kurva över runstenarnas omvärld genom 1000-talet, som vi gjorde ovan, ritar en kurva där samma färd bestämmer hur hög toppen blir och, genom dateringen, ungefär var på tidsaxeln den hamnar. Det är inget fel i kurvan. Men det är något man måste veta när man läser den.

## Det vi inte vet

- **Definitionen är vid.** Ög 30 minns en son som hette Ingvar och dog i öster. Han kan ha varit en helt annan Ingvar. Med den smala definitionen, där bara stenar som nämner Ingvar som ledare räknas bort, blir resultatet ändå detsamma.
- **Två Serklandsstenar står kvar.** Sö 279 och U 785 nämner Serkland men inte Ingvar, så planens definition tog inte med dem, fast forskningen ofta räknar Sö 279 till tåget (Krakow 2021b). Tar vi bort också dem blir andelen {EXTRA_P} %. Det talet räknade vi efter planen och bara som en punktskattning.
- **Stilgrupper är inte årtal.** Kurvan bygger på ornamentiken, och dess år är ungefärliga och delvis förankrade i just Ingvarståget.
- **Stenarna minns främst dem som dog borta.** Den som kom hem fick sällan en sten. Att en plats nämns betyder inte heller att någon reste dit.
- **De sena stenarna är för få.** Med de sena stenar som finns i dag kan Westins fråga inte prövas på runstenarna.

## Vad vi tror att det betyder

En runsten restes när någon inte kom hem. En lyckad handelsresa ger inga stenar, en katastrof ger många på en gång. Ingvars tåg var en katastrof, och därför väger det så tungt.

Vår tolkning, och den har vi inte visat, är att runstenarna mäter förlust snarare än trafik. Österns övervikt på stenarna är till ungefär hälften en enda stor sorg, buren av mödrar som Tola och Lífey, av söner som reste sten efter sina fäder och av en ristare som fick hugga samma namn gång på gång. Det gör inte österleden mindre verklig. Det betyder att siffran ska läsas som ett mått på vad familjerna förlorade och ville att andra skulle minnas, inte som en räkning av skeppen.

Nästa gång du läser att ”runstenarna visar” något, också hos oss, fråga hur många av stenarna som handlar om samma dag. Och står du framför en Ingvarsten, vid Tystberga, Svinnegarn eller Gripsholm, läs vem som reste den. Det är nästan alltid någon som blev kvar.

:::box Det viktigaste i korthet
- Ungefär halva österns övervikt på de svenska runstenarna är minnet av ett enda tåg. Utan Ingvar ser stenarna fortfarande något oftare österut, men inte så tydligt att vi kan utesluta att det var lika ofta.
- Det som skiljer runstenarna från islänningarnas sagor om sina förfäder står kvar. Hypotesen att österleden på Island blev forntid bärs inte av Ingvar.
- Runstenar är minnen av förluster. En katastrof ger många stenar på en gång, och den som räknar dem måste fråga hur många som handlar om samma händelse.
- Samma tåg är också ett av ankarna för när runstenarna restes, och dess år är omstritt. Någon förskjutning mot väster under 1000-talet syns inte, men de sena stenarna är för få för en dom.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Runtexterna står ordagrant i Rundatas normalisering; översättningarna är våra, efter Rundatas engelska.
- Sindbæk, Søren M. 2003. Varægiske vinterruter: slædetransport i Rusland og spørgsmålet om den tidlige vikingetids orientalske import i Nordeuropa. *Fornvännen* 98, s. 179–193 (citatet s. 180). [Fri fulltext hos Riksantikvarieämbetet]({URL_SINDBAEK}).
- Westin, Gunnar 1941. En västmanländsk ryttargrav. *Fornvännen* 36, s. 85–101 (citatet s. 93). [Fri fulltext]({URL_WESTIN}).
- Thulin, Alf 1985. Var vikingatidens ryssar (fry. rus') franker? Några reflektioner i anledning av Omeljan Pritsaks The Origin of Rus'. *Fornvännen* 80, s. 190–202 (citatet s. 201). [Fri fulltext]({URL_THULIN}).
- Gräslund, Anne-Sofie 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139. Stilgrupperna (RAK, Fp, Pr1–Pr5) och deras dateringar.
- Krakow, Annett 2021a. Olof Erikssons dödsår och dateringen av Ingvarståget. *Fornvännen* 116, s. 101–113. [Fri fulltext]({URL_KRAKOW}).
- Larsson, Mats G. 2021. Ingvarstågets datering. *Fornvännen* 116, s. 243–244. [Fri fulltext]({URL_LARSSON}).
- Krakow, Annett 2021b. Ingvarstågets datering: svar till Mats G. Larsson. *Fornvännen* 116, s. 338–339. [Fri fulltext]({URL_KRAKOW2}).
- Vitkis självkontroll: [den låsta analysplanen]({PLAN}) och [resultaten]({RES}) (10 november 2026). Den tidigare artikeln, [Vikingarnas värld – vilka platser nämner de?](/artiklar/vikingarnas-varld), har fått ett tillägg med de nya siffrorna.
- Foto: Wikimedia Commons, med fotograf och licens i bildtexterna. Diagrammen: Vitki."""

title_en = "The Vikings' road east – or just Ingvarr's?"
summary_en = (f"The runestones look east, we wrote in an earlier article. But {N_ING} of the stones remember the same "
              "journey: Ingvarr's expedition to Serkland. We took them out, following a plan locked in advance. About half "
              "of the east's lead disappeared – and the same expedition turned out to be one of the anchors for when the "
              "runestones were raised.")

body_en = f"""*{SO173}*

He had long been in the west. He died in the east, with Ingvarr.

The line stands on a stone at Tystberga in Södermanland (Sö 173). Myskja and Manni had it raised for their brother Hróðgeirr and their father Holmsteinn. Which of them had long been in the west the stone does not say. But it says something few runestones say: that one and the same man could have both directions in his life. First the west, then the east, in a company that did not come back.

![The runestone Sö 173]({IMG['Sö 173']['thumb']})
Sö 173 at Tystberga: "He had long been in the west; died in the east with Ingvarr." {credit('Sö 173', 'en')}

In the article [The Vikings' world – which places do they name?](/en/artiklar/vikingarnas-varld) we counted every place outside Scandinavia named on the Swedish runestones. Two in three lay in the east, {ALL_P} %. This article is about what happened when we turned to our own figure and asked whether it holds.

## An objection in a subordinate clause

Imagine reading every death notice in a coastal town over fifty years and noticing that a striking number are about the sea. Then you see that many of them came in the same autumn, after a single shipwreck. The sea was dangerous; that stands. But your figure says less about how often people went to sea than about one night.

That objection to our figure was already in the literature, in a subordinate clause. The Danish archaeologist Søren Sindbæk wrote in Fornvännen in 2003 about something else entirely, about when the Viking routes through Russia opened, and mentioned the runestones in passing:

> {SINDBAEK}

Finally, no fewer than 96 Swedish runestones are known that name people who had travelled east to Garðar, or all the way to Greece or Serkland … At this time the runestones themselves often speak of special heroic deeds, such as Ingvarr the Far-Travelled's expedition to the Caspian Sea, which alone accounts for more than 25 stones (Sindbæk 2003, p. 180).

If so, our east share might be Ingvarr's shipwreck rather than a whole generation's road. There was no way to know without counting. So before we counted, we wrote down the rules: which stones count as Ingvarr stones, and what would make us say the result holds, is weakened or falls. [The plan]({PLAN}) was locked on 10 November 2026, and only then was anything counted.

## Ingvarr's men

Our definition was deliberately wide. A stone counts if it names Ingvarr as the leader of a journey, or if it names Ingvarr and also a place in the east. Better one stone too many than one too few, because that makes it harder for our own figure to survive. Twenty-six stones were caught. One of them, U 540, we removed on reading the text: there Ingvarr is one of those who raised the stone, and the dead man died in Greece, with nothing to tie him to the expedition. That left {N_ING}, as many as Sindbæk counted.

They stand from Medelpad in the north to Östergötland in the south, but most of them in Södermanland ({PROV['Sö']}) and Uppland ({PROV['U']}). Read one after another, they are an unusually close gathering of people.

Eight of the dead were fathers, and it was their children who raised the stone. Six were sons, five were brothers and one was a stepson. On the other five the text is too damaged to say who remembers whom, or the stone remembers two men. At Svinnegarn in Uppland, Þjalfi and Holmlaug raised stones for their son Banki: *{U778}* – who alone owned a ship and steered to the east in Ingvarr's retinue (U 778). At Varpsund five sons raised a stone for their father Gunnleifr, who was killed in the east with Ingvarr, and added a line about what he could do: *{U654}* – he could steer a cargo ship well (U 654). At Lifsinge in Södermanland, Bergviðr and Helga raised a stone for their son Ulfr: *{SO9}* – he met his end with Ingvarr (Sö 9). At Stäringe three brothers remember a fourth, Bjórsteinn, and name his mother: *{SO320}*, an able, valiant man, Lífey's son (Sö 320). And at Gripsholm stands Tóla's stone for her son Haraldr, Ingvarr's brother, which we read in the earlier article (Sö 179).

Serkland, the land where they died, is named on four of the stones, on one of them with a question mark (U 439). Ships are named on more: the one who steered, the one who owned, the one who was another man's seaman. And several of the stones share a hand. Rundata ties six of them to the carver Áskell (Äskil), and a seventh with a question mark. On one of them he wrote his own name: *{U778_SIGN}* – Áskell carved (U 778).

That is the first reason to take Sindbæk's clause seriously. The {N_ING} stones are not {N_ING} independent witnesses to where the Svear travelled. They are one testimony, repeated by the families who were struck, often by the same carver. Of the {OST_ALL} stones in our selection that name a place in the east, {OST_ING} are Ingvarr stones: more than one in four.

![The runestone U 778]({IMG['U 778']['thumb']})
U 778 in Svinnegarn church: Banki "alone owned a ship and steered to the east in Ingvarr's retinue". {credit('U 778', 'en')}

## What is left

The Ingvarr stones name {GRP_O} places in the east and {GRP_V} in the west. Take them out, and the east share falls from {ALL_P} to {UI_P} %.

That is a large movement for a single journey. Of the {SURPLUS} percentage points by which the runestones lay above half, the Ingvarr stones account for {DROP}. About half of the east's lead, in other words, is one expedition.

What is left is also less certain than we would like. With {UI_N} stones left, the east share probably lies between {UI_LO} and {UI_HI} %. Since half lies inside that range, we cannot rule out that the stones, without Ingvarr, named east and west about equally often. (We computed the range by drawing the stones anew ten thousand times, so that a stone naming many places does not weigh like many stones.) The plan's verdict is therefore: weakened. The best estimate is still above half, but we can no longer say that the stones clearly look east.

We also counted in other ways, and they all point the same way:

{chart('en')}

Counting the expedition as a single text, instead of removing it altogether, puts the share at {pc(ONE['ostandel'])} %. Removing only the {N_NARROW} stones that explicitly name Ingvarr as leader also gives {pc(NARROW['ostandel'])} %. The west has no counterpart. The stones about Knútr's payment in England number only {N_KNUT}, and removing them changes almost nothing ({pc(KNUT['ostandel'])} %). No event in the west weighs on the stones like Ingvarr's in the east.

## What holds

That sounds like a loss, and in part it is one. But the most important thing in the earlier article was not that the stones look east as such. It was the comparison: that the runestones and the Icelanders' sagas about their own ancestors look in different directions, and that the sagas about the ancient past resemble the stones.

That comparison stands. The sagas of Icelanders have {IS_P} % east, probably between {IS_LO} and {IS_HI} %, and the kings' sagas in Heimskringla {HK_P} %. The runestones without Ingvarr, at {UI_P} %, overlap with neither. With Ingvarr the stones lay higher than any of the sagas. Without him they are level with the legendary sagas, the sagas about the time before Iceland was settled, which also have {FA_P} %. It is a curious symmetry, since the saga of Ingvarr itself is counted among the legendary sagas, and we will make no more of it than that. But the hypothesis from last time, that in Iceland the eastern route had become the ancient past, does not rest on Ingvarr.

## Westin and time

The second objection is older. Gunnar Westin wrote in 1941, in an article about a horseman's grave in Västmanland:

> {WESTIN}

The Swedish Viking expeditions were mainly directed to the east. Towards the end of the Viking Age, however, a shift occurs. The eastern route through Russia to the Orient becomes, for several reasons, less important to the Northmen (Westin 1941, p. 93). He relied mostly on the hoards – Arabic coins dominate until the middle or later part of the tenth century, western coins afterwards – but he also mentioned the runestones, on which many Svear went west and shared in the great payments the English king was forced to make.

If Westin is right, the younger runestones should look west more than the older ones. Runestones have no years, but they can be ordered by their ornament, in the style groups Rundata gives after Anne-Sofie Gräslund, with approximate years: RAK about 980–1015, Fp 1010–1050 and so on to Pr5, 1100–1130.

The answer is that we cannot tell. The stones in the late style groups, after about 1050, name only {LATE_N} places, and the plan required at least {MIN_N} for a verdict. What we can do is show the curve.

![Share of places in the east by style group, with and without the Ingvarr stones]({FIG['en']})
The share of places that lie in the east, style group by style group, with and without the Ingvarr stones. The dots are the share; the lines show where it probably lies (only for groups with at least ten places). The style groups carry Gräslund's approximate years, not years from the texts. Chart: Vitki, after Rundata and Gräslund's style dating.

The curve shows no shift to the west. The stones from before about 1050 have {EARLY_P} % east, the later ones {LATE_P} %. If anything the curve tilts the other way, but it rests on too few late stones for us to build anything on that.

Two things do show clearly. The first is that the oldest stones, the RAK group around the year 1000, are the ones that look most to the west: {RAK_P} % east. England is the land they name most often, on {RAK_ENG} of {RAK_N} stones, and as many simply say "in the west". The west, in other words, did not come last on the stones but first. Mats G. Larsson also points out that the England stones were in many cases raised for men who came home safe and got their stone only when they had died at home (Larsson 2021). The journey may be older than the stone.

The second is the peak in the Fp group, 1010–1050: {FP_P} % east. Of the group's {FP_N} stones, {FP_ING} are Ingvarr stones. Without them the peak drops to {FP_UI} %. The eastern high point in the middle of the eleventh century is, in our material, largely one and the same expedition.

Westin's shift may well have happened. But if so, it belongs to the tenth century of the hoards, which the runestones do not reach.

## The firmest point

Here is what makes the check more important than a correction. Alf Thulin wrote in 1985:

> {THULIN}

The saga says that Ingvarr died in 1041, a statement which despite its unreliability has become the firmest point in the chronology of the Uppland runestones (Thulin 1985, p. 201). The runestones have few certain years. One of the most important comes not from the stones themselves but from an Icelandic saga written much later. And the year is disputed. Thulin himself had proposed 1030–1031. In 2021 Annett Krakow proposed in Fornvännen that the expedition belongs to around 1020 instead: the saga's time frame, she argues, rests on Adam of Bremen's late year for the death of Olof Skötkonung, and the plain ornament of the Ingvarr stones fits 1020 better. She also writes that the expedition's date has been used by a large number of runologists as a chronological pillar for the Uppland runestones in general. Mats G. Larsson replied in the same volume and held to around 1040, citing among other things Prince Yaroslav's battles against the Pechenegs in 1036. Krakow replied in turn. The question is open.

A detail in our own table fits here. Skarði's stone at Lundby (Sö 131), one of the best-known Ingvarr stones, stands in Rundata in RAK, the group usually dated 980–1015. Either the stone is older than 1041 allows, or the style groups overlap more than their years do. We cannot tell which.

This is how it fits together. Ingvarr's expedition is both a large part of the answer to the question *where* – more than one in four stones that name the east – and one of the anchors for the question *when*. Whoever draws a curve of the runestones' world through the eleventh century, as we did above, draws a curve in which the same journey sets how high the peak goes and, through the dating, roughly where on the time axis it lands. There is nothing wrong with the curve. But it is something one must know when reading it.

## What we do not know

- **The definition is wide.** Ög 30 remembers a son called Ingvarr who died in the east. He may have been a quite different Ingvarr. With the narrow definition, where only stones naming Ingvarr as leader are removed, the result is the same.
- **Two Serkland stones remain.** Sö 279 and U 785 name Serkland but not Ingvarr, so the plan's definition did not include them, although scholars often count Sö 279 with the expedition (Krakow 2021b). Removing them too gives {EXTRA_P} %. We computed that figure after the plan, and only as a point estimate.
- **Style groups are not years.** The curve rests on ornament, and its years are approximate and partly anchored in the Ingvarr expedition itself.
- **The stones remember above all those who died abroad.** Those who came home seldom got a stone. Nor does naming a place mean anyone travelled there.
- **The late stones are too few.** With the late stones we have today, Westin's question cannot be tested on the runestones.

## What we think it means

A runestone was raised when someone did not come home. A successful trading voyage leaves no stones; a disaster leaves many at once. Ingvarr's expedition was a disaster, and that is why it weighs so heavily.

Our interpretation, and we have not shown it, is that the runestones measure loss rather than traffic. About half of the east's lead on the stones is one great grief, carried by mothers like Tóla and Lífey, by sons who raised stones for their fathers and by a carver who had to cut the same name again and again. That does not make the eastern route less real. It means the figure should be read as a measure of what families lost and wanted others to remember, not as a count of the ships.

The next time you read that "the runestones show" something, ours included, ask how many of the stones are about the same day. And if you stand before an Ingvarr stone, at Tystberga, Svinnegarn or Gripsholm, read who raised it. It is almost always someone who stayed behind.

:::box The essentials in brief
- About half of the east's lead on the Swedish runestones is the memory of a single expedition. Without Ingvarr the stones still look east somewhat more often, but not clearly enough to rule out that it was equally often.
- What sets the runestones apart from the Icelanders' sagas about their ancestors still stands. The hypothesis that in Iceland the eastern route became the ancient past is not carried by Ingvarr.
- Runestones are memorials of losses. A disaster yields many stones at once, and whoever counts them must ask how many are about the same event.
- The same expedition is also one of the anchors for when the runestones were raised, and its year is disputed. No shift to the west during the eleventh century can be seen, but the late stones are too few for a verdict.
:::

## Sources

- The Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. The runic texts are quoted verbatim from Rundata's normalisation; the translations are ours, after Rundata's English.
- Sindbæk, Søren M. 2003. Varægiske vinterruter: slædetransport i Rusland og spørgsmålet om den tidlige vikingetids orientalske import i Nordeuropa. *Fornvännen* 98, pp. 179–193 (quotation p. 180). [Free full text from the Swedish National Heritage Board]({URL_SINDBAEK}).
- Westin, Gunnar 1941. En västmanländsk ryttargrav. *Fornvännen* 36, pp. 85–101 (quotation p. 93). [Free full text]({URL_WESTIN}).
- Thulin, Alf 1985. Var vikingatidens ryssar (fry. rus') franker? Några reflektioner i anledning av Omeljan Pritsaks The Origin of Rus'. *Fornvännen* 80, pp. 190–202 (quotation p. 201). [Free full text]({URL_THULIN}).
- Gräslund, Anne-Sofie 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139. The style groups (RAK, Fp, Pr1–Pr5) and their dates.
- Krakow, Annett 2021a. Olof Erikssons dödsår och dateringen av Ingvarståget. *Fornvännen* 116, pp. 101–113. [Free full text]({URL_KRAKOW}).
- Larsson, Mats G. 2021. Ingvarstågets datering. *Fornvännen* 116, pp. 243–244. [Free full text]({URL_LARSSON}).
- Krakow, Annett 2021b. Ingvarstågets datering: svar till Mats G. Larsson. *Fornvännen* 116, pp. 338–339. [Free full text]({URL_KRAKOW2}).
- Vitki's self-check: [the locked analysis plan]({PLAN}) and [the results]({RES}) (10 November 2026, in Swedish). The earlier article, [The Vikings' world – which places do they name?](/en/artiklar/vikingarnas-varld), has been given an addition with the new figures.
- Photos: Wikimedia Commons, with photographer and licence in the captions. Charts: Vitki."""

# ---- kontroller -----------------------------------------------------------------------------------------------------------------
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "/artiklar/vikingarnas-varld" in b and URL_THULIN in b and URL_SINDBAEK in b and URL_WESTIN in b
    for img in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b):
        assert img.startswith("/api/blog/figures/") or re.match(r"https://(upload|thumb)\.wikimedia\.org/", img), img
    assert b.count("Vitki") >= 3
    # aldrig siffra först i en mening (brödtexten före källorna; bild- och diagramrader och sidhänvisningar räknas inte)
    prose = re.split(r"^## (Källor|Sources)$", b, flags=re.M)[0]
    txt = " ".join(line for line in re.sub(r"!\[[^\]]*\]\([^)]*\)", "", prose).splitlines() if "|" not in line and not line.startswith(":::"))
    bad = [txt[max(0, m.start() - 30):m.end() + 20] for m in re.finditer(r"(?<!\b[sp])[.!?]\s+\(?\d", txt)]
    assert not bad, bad
    assert "Det viktigaste i korthet" in b or "The essentials in brief" in b
assert body.index(":::box Det viktigaste i korthet") < body.index("## Källor")
assert body_en.index(":::box The essentials in brief") < body_en.index("## Sources")
assert not re.search(r"\bjag\b", body.replace(THULIN, "").replace(WESTIN, ""), re.I), "vi-form"

labels = ["Forskning", "Geografi", "Datering och stil"]
out = {"slug": "osterled-eller-bara-ingvars", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": labels}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "blogg", "ingvar.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord sv,", len(body_en.split()), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Forskning|omvarld", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
