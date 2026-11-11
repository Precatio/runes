"""Artikeln "Döda i vita kläder – sju runstenar över dem som dog nydöpta" (sv + en): de sju uppländska runstenar som
säger att den döde dog *i hvitavaðum*, 'i vita kläder', det vill säga i dopdräkten. Beskrivande artikel (spår P,
PUBLICERINGSPLAN.md), planerad fredag 4 december 2026; ingen hypotesprövning mot slumpen. Viktor publicerar själv.

Alla siffror läses ur Rundata (data/rundata.json) och låses med assert; stenarna söks i både translitterering och
normalisering, och listan jämförs med litteraturens (sju stenar). Runtexterna står ordagrant som i Rundatas
normalisering. Litteraturcitaten är kontrollerade mot de fria fulltexterna i downloads/tidskrifter (OCR:en, med
blanksteg bortrensade) och mot sidbilderna: Svärdström & Gustavson 1973 s. 194 (OCR:en läser 'våder' som 'vader'),
Jansson 1972 s. 178, Ahlstedt Yrlid 1969 s. 273 och Bender Jørgensen 2008 s. 314–315, 2026-11-11.
    ../../../.venv/bin/python build_vita_klader.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, commons, people, regions  # noqa: E402
from src import research_gaps as rg  # noqa: E402
from src.blog_examples import STYLE_YEARS  # noqa: E402

INS = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
BY = {r["signum"]: r for r in INS}
pc = lambda x: round(100 * x)  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731


def norm(s):
    return BY[s]["normalization"].replace('"', "").strip()


# ---- 1. Stenarna: alla stavningar, i translitterering och normalisering ----------------------------------------------
# Normaliseringen skriver alltid ...tavaðum; translittereringen visar ristarnas egna stavningar (hoitauaþum, fita+faþum,
# huita'huaþum ...). Vi söker i hela Rundata, alla föremål, alla länder och perioder.
NORM_RX = re.compile(r"tava[ðd]um|tavá[ðd]um", re.I)
TRANS_RX = re.compile(r"(uaþum|faþum|uaþ\[um\]|huaþum|uaþom|uatum)")


def hit(r):
    t = re.sub(r"[^a-zþæøåöäR\[\]]", "", (r.get("transliteration") or ""))
    return bool(NORM_RX.search((r.get("normalization") or "") + " " + (r.get("normalization_ows") or ""))
                or TRANS_RX.search(t))


HITS = sorted(r["signum"] for r in INS if hit(r))
SEVEN = ["U 243", "U 364", "U 613", "U 699", "U 896", "U 1036", "U Fv1973;194"]
# Den vida sökningen i translittereringen fångar också N 324, en träpinne med ordet lofuðum ('vi lovade'), som inte
# hör hit; alla andra träffar har formeln i normaliseringen.
assert BY["N 324"]["normalization"].strip() == "lofuðum" and not NORM_RX.search(BY["N 324"]["normalization"])
assert sorted(set(HITS) - {"N 324"}) == sorted(SEVEN), HITS
assert all(NORM_RX.search(BY[s]["normalization"]) for s in SEVEN)
assert all(rg.is_runestone(BY[s]) for s in SEVEN), "alla sju är svenska vikingatida runstenar"
assert {rg.province(BY[s]) for s in SEVEN} == {"U"}
# Inga andra föremål och inga andra länder: träffarna ovan gäller hela Rundata
SE_STONES = [r for r in INS if rg.is_runestone(r)]
U_STONES = [r for r in SE_STONES if rg.province(r) == "U"]
N_SE, N_U = len(SE_STONES), len(U_STONES)
assert (N_SE, N_U) == (2321, 1178)
ONE_IN = round(N_U / len(SEVEN))
assert ONE_IN == 168  # "ungefär en av 170"

SPELL = {"U 243": "hoitauaþum", "U 364": "huitauaþ[um]", "U 613": "hoita+uaþum", "U 699": "huita·uaþum",
         "U 896": "fita+faþum", "U 1036": "huita'huaþum", "U Fv1973;194": "...tauaþum"}
for s, f in SPELL.items():
    assert f in BY[s]["transliteration"], (s, f)
PLACE = {s: BY[s]["place"] for s in SEVEN}
PARISH = {s: BY[s]["parish"] for s in SEVEN}
assert PLACE == {"U 243": "Molnby", "U 364": "Gådersta", "U 613": "Torsätra", "U 699": "Amnö", "U 896": "Håga",
                 "U 1036": "Tensta kyrka", "U Fv1973;194": "Uppsala domkyrka"}
assert PARISH == {"U 243": "Vallentuna sn", "U 364": "Skepptuna sn", "U 613": "Västra Ryds sn", "U 699": "Veckholms sn",
                  "U 896": "Bondkyrka sn (nu Uppsala)", "U 1036": "Tensta sn", "U Fv1973;194": "Uppsala"}
assert BY["U 243"]["flags"]["lost"] and not any(BY[s]["flags"]["lost"] for s in SEVEN if s != "U 243")
assert "[hvi]tavaðum" in norm("U Fv1973;194"), "domkyrkostenens ord är delvis kompletterat"
assert "Danma[rku](?)" in norm("U 896") and "a Danmarku i hvitavaðum" in norm("U 699")

# ---- 2. De döda och resarna (handgenomgång, kontrollerad mot Rundatas engelska) -------------------------------------
T = {s: BY[s]["translation_en"] for s in SEVEN}
assert "in memory of Fasti and Sigfastr, their sons. They died in (their) christening robes." in T["U 243"]
assert "He died in christening robes." in T["U 364"] and "Karsi and Kar-..." in T["U 364"]
assert "in memory of her son Eysteinn who died in christening robes" in T["U 613"]
assert "in memory of Brúni, her husbandman. He died in christening robes in Denmark." in T["U 699"]
assert "for the spirit of Eyndr(?), their son, (who) died in christening robes in Denmark(?)" in T["U 896"]
assert "in memory of Andvéttr, her son, who died in christening robes" in T["U 1036"]
assert T["U Fv1973;194"].startswith("... had this stone erected ... christening robes")
DEAD_REL = {"son": ["U 243", "U 613", "U 896", "U 1036"], "make": ["U 699"], "okänd": ["U 364", "U Fv1973;194"]}
assert sorted(sum(DEAD_REL.values(), [])) == sorted(SEVEN)
MEN = 2 + 1 + 1 + 1 + 1 + 1  # U 243 två söner; U 364 "Hann"; U 613, U 699, U 896, U 1036 en man var
MEN_STONES = 6
assert (MEN, MEN_STONES) == (7, 6)  # "sju män på sex stenar"
RAISERS = {"U 243": [("Holmlaugr", "m"), ("Holmfríðr", "k")], "U 364": [("Karsi", "m"), ("Kar-...", "?")],
           "U 613": [("Una/Unna", "k")], "U 699": [("Ingileif", "k")], "U 1036": [("Helga", "k")]}
for s, ps in RAISERS.items():
    for name, _ in ps:
        assert name in T[s], (s, name)
assert T["U 1036"].startswith("Sigfastr and Brandr and Véketill. Helga had the stone erected")
LEGIBLE = len(RAISERS)
WOMAN = sorted(s for s, ps in RAISERS.items() if any(g == "k" for _, g in ps))
assert (LEGIBLE, len(WOMAN)) == (5, 4) and WOMAN == ["U 1036", "U 243", "U 613", "U 699"]
# jämförelsen: Vitkis automatiska läsning (src/people.py) av Upplands runstenar
PROWS = {x["signum"]: x for x in people.rows(INS)}
assert all(PROWS[s]["resare_k"] > 0 for s in WOMAN), "den automatiska läsningen ser samma kvinnor"
UPR = [PROWS[r["signum"]] for r in U_STONES if r["signum"] in PROWS]
GEND = [x for x in UPR if x["resare_k"] + x["resare_m"] > 0]
CHILD = [x for x in GEND if x["rel_barn"]]
W_ALL = pc(sum(1 for x in GEND if x["resare_k"]) / len(GEND))
W_CHILD = pc(sum(1 for x in CHILD if x["resare_k"]) / len(CHILD))
assert (len(GEND), W_ALL, len(CHILD), W_CHILD) == (737, 35, 140, 61)

# ---- 3. Var: folkland och socknar ------------------------------------------------------------------------------------
FOLK = {s: regions.old_region(s, "U") for s in SEVEN}
assert FOLK == {"U 243": "attundaland", "U 364": "attundaland", "U 613": "attundaland", "U 699": "fjadrundaland",
                "U 896": "tiundaland", "U 1036": "tiundaland", "U Fv1973;194": "tiundaland"}
UFOLK = {}
for r in U_STONES:
    k = regions.old_region(r["signum"], "U")
    UFOLK[k] = UFOLK.get(k, 0) + 1
UF = {k: pc(v / N_U) for k, v in UFOLK.items()}
assert (UF["attundaland"], UF["tiundaland"], UF["fjadrundaland"]) == (45, 33, 14)

# ---- 4. När: Gräslunds stilgrupper -------------------------------------------------------------------------------------
STYLE = {s: (BY[s]["style"], BY[s]["style_uncertain"]) for s in SEVEN}
assert STYLE == {"U 243": ("Pr3", False), "U 364": ("Pr4", True), "U 613": ("Pr3 - Pr4", True), "U 699": ("Pr3", False),
                 "U 896": ("Pr1", True), "U 1036": ("Pr4", False), "U Fv1973;194": ("Pr4", False)}
SURE = sorted(s for s in SEVEN if rg.has_style(BY[s]))
assert SURE == ["U 1036", "U 243", "U 699", "U Fv1973;194"]
UST = {}
for r in U_STONES:
    if rg.has_style(r):
        UST[r["style"]] = UST.get(r["style"], 0) + 1
N_UST = sum(UST.values())
assert N_UST == 567 and UST["KB"] == 7
LATE = pc((UST["Pr3"] + UST["Pr4"]) / N_UST)
assert LATE == 58
ORDER = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
KB = pc(UST["KB"] / N_UST)
assert KB == 1
Y = STYLE_YEARS
assert (Y["Pr3"], Y["Pr4"]) == ((1045, 1075), (1070, 1100))

# ---- 5. Vad mer: kors, böner, ristare ----------------------------------------------------------------------------------
CROSS = sorted(s for s in SEVEN if BY[s]["cross_form"].strip())
assert CROSS == ["U 1036", "U 243", "U 613", "U 896"]
U_CROSS = pc(sum(1 for r in U_STONES if r["cross_form"].strip()) / N_U)
assert U_CROSS == 47
PRAY_RX = re.compile(r"\b(hialp|hjalp)", re.I)  # hialpi, hialp, hialpin, hjalpi
PRAY = sorted(s for s in SEVEN if PRAY_RX.search(norm(s)))
assert PRAY == ["U 1036", "U 613"]
U_PRAY_N = sum(1 for r in U_STONES if PRAY_RX.search(r["normalization"]))
U_PRAY = pc(U_PRAY_N / N_U)
assert (U_PRAY_N, U_PRAY) == (141, 12)
FYR_AND = sorted(r["signum"] for r in U_STONES if "fyr and" in r["normalization"])
assert "U 896" in FYR_AND and len(FYR_AND) == 6
CARV = {s: BY[s]["carver_raw"] for s in SEVEN}
assert CARV == {"U 243": "Visäte (A)", "U 364": "Torfast (A); Åsmund (L); Torsten (A) [Källström 2007a:269]",
                "U 613": "Visäte (A)", "U 699": "Balle (S)", "U 896": "Öpir 1 (S), verkar inte vara huggen av Öpir.",
                "U 1036": "Öpir 1 (A) [ej Öpir, Åhlén 1997]", "U Fv1973;194": ""}
BALLE_S = sorted(r["signum"] for r in SE_STONES if any(c["name"] == "Balle" and c["kind"] == "S" and not c["uncertain"] for c in r["carvers"]))
BALLE_A = sorted(r["signum"] for r in SE_STONES if any(c["name"] == "Balle" and c["kind"] == "A" for c in r["carvers"]))
assert (len(BALLE_S), len(BALLE_A)) == (21, 55) and "U 699" in BALLE_S
import math  # noqa: E402
DIST_M = 1000 * math.hypot((BY["U 896"]["lat"] - BY["U Fv1973;194"]["lat"]) * 111.2,
                           (BY["U 896"]["lon"] - BY["U Fv1973;194"]["lon"]) * 111.2 * math.cos(math.radians(59.86)))
assert round(DIST_M, -1) == 150
assert "ryttare" in BY["U Fv1973;194"]["other"] and "golvbrunn" in BY["U Fv1973;194"]["other"]

# Texterna som citeras ordagrant (Rundatas normalisering)
Q243 = "ÞæiR dou i hvitavaðum."
Q699 = "Ingilæif let ræisa st[æin] at Bruna, boanda sinn. Hann varð dauðr a Danmarku i hvitavaðum. Balli rist[i]."
Q613 = "Una/Unna let ræisa þennsa stæin æftiR sun sinn Øystæin/Æistæin, sum do i hvitavaðum. Guð hialpi salu hans."
Q1036 = ("Hælga let retta stæin æftiR Andvett, sun sinn, sum [vaR] dauðr [i] hvitavaðum. "
         "Kristr hialpi sial AndvettaR.")
Q896 = "letu ræisa stæin fyr and Øy[nda]R(?), sun sinn, dauðr [i] hvitavaðum i Danma[rku](?)"
Q614 = "Hann vas siukR uti, þa þæiR giald toku a Gutlandi."
for s, q in (("U 243", Q243), ("U 699", Q699), ("U 613", Q613), ("U 1036", Q1036), ("U 896", Q896), ("U 614", Q614)):
    assert q in norm(s), (s, q)
assert norm("U 1036").startswith("Sigfastr ok Brandr ok Vikætill. Hælga")
assert "sick abroad when they took payment on Gotland" in BY["U 614"]["translation_en"]
assert "Skúli and Folki" in BY["U 614"]["translation_en"] and CARV["U 613"] == BY["U 614"]["carver_raw"]
PLACEMENT = {s: BY[s]["placement"] for s in ("U 613", "U 699", "U 896", "U 1036", "U Fv1973;194")}
assert PLACEMENT == {"U 613": "SHM", "U 699": "I Ekholmens park.", "U 896": "I Universitetsparken, Uppsala.",
                     "U 1036": "Omedelbart utanför bogårdsmuren.",
                     "U Fv1973;194": "Under pelaren mellan Sture- och Finstakoren."}

# ---- 6. Litteraturen: citaten kontrollerade mot fulltexten -------------------------------------------------------------
TID = os.path.join(ROOT, "..", "downloads", "tidskrifter")
FV = os.path.join(TID, "fornvannen")
IDX = {}
for line in open(os.path.join(FV, "index.jsonl"), encoding="utf-8"):
    d = json.loads(line)
    IDX.setdefault(d["key"], d)
JOURNALS = json.load(open(os.path.join(ROOT, "data", "cache", "literature", "journals.json"), encoding="utf-8"))["articles"]
JURL = {(a["journal"], a["url"].rsplit(":", 1)[-1].split("/")[0]): a for a in (JOURNALS.values() if isinstance(JOURNALS, dict) else JOURNALS) if a.get("url")}


def flat(x):
    return re.sub(r"\s+", "", x).replace("-", "").replace("­", "")


def streams(raw):
    """Fornvännens OCR lägger två spalter på samma rad; vi jämför mot hela texten och mot vänster- och högerspalten var
    för sig (ett avbrott på minst tre blanksteg skiljer spalterna, en ensam rad långt in hör till högerspalten)."""
    left, right = [], []
    for line in raw.splitlines():
        if not line.strip():
            continue
        ind = len(line) - len(line.lstrip())
        segs = re.split(r"\s{3,}", line.strip())
        if len(segs) == 1:
            (right if ind > 30 else left).append(segs[0])
        else:
            left.append(segs[0])
            right.append(" ".join(segs[1:]))
    return [flat(raw), flat(" ".join(left)), flat(" ".join(right))]


def check_fv(key, *frags):
    t = streams(open(os.path.join(FV, "text", key + ".txt"), encoding="utf-8").read())
    for f in frags:
        assert any(flat(f) in x for x in t), (key, f)
    assert IDX[key]["licence"] == "https://creativecommons.org/licenses/by/4.0/"
    return IDX[key]["uri"]


def check_fu(key, diva, *frags):
    t = flat(open(os.path.join(TID, "futhark", "text", key + ".txt"), encoding="utf-8").read())
    for f in frags:
        assert flat(f) in t, (key, f)
    return JURL[("Futhark", diva)]["url"]


# Svärdström & Gustavson 1973, s. 194. 'våder' kontrollerat mot sidbilden; OCR:en har 'vader', så fragmenten undviker ordet.
SVG_VADER = "Inskriftens 'vita våder' betecknar de kläder som den döpte bar under dopet och en tid därefter."
SVG_SEX = ("I Uppland finns ytterligare sex runstenar resta över män som dött i vita våder. I nästan samtliga fall rör det "
           "sig om unga män som sannolikt dött utomlands; i minst ett fall nämns Danmark.")
SVG_DOD = ("Av de tillgängliga delarna av inskriften kan man anta, att stenen har rests av fränderna till någon eller några "
           "som på dödslägret låtit döpa sig.")
URL_SVG = check_fv("1973_185", "betecknar de kläder som den döpte bar under dopet och en tid därefter",
                   "I Uppland finns ytterligare sex runstenar resta över män som dött i vita",
                   "I nästan samtliga fall rör det sig om unga män som sannolikt dött utomlands; i minst ett fall nämns Danmark",
                   SVG_DOD, "ett språkligt karakteristikon för mis", "en framställning av en ryttare till häst",
                   "rester av två korsarmar", "Partiet i Sturekoret har dock fått ligga kvar synligt i en golvbrunn")
assert IDX["1973_185"]["authors"] == ["Svärdström, Elisabeth", "Gustavson, Helmer"]
# Jansson 1972, s. 178 (OCR: 'dubbclmonumentet')
URL_JANSSON = check_fv("1972_170", "Visäte har t. ex. undvikit upprepning", "vid Torsätra (U 613 och 614)",
                       "Också där avviker den ornamentala stilen i påfallande grad på de båda runstenarna")
assert IDX["1972_170"]["authors"] == ["Jansson, Sven B. F."]
# Ahlstedt Yrlid 1969, s. 272–273
KAGA = ("Kornukas far Kol blev den förste som begrovs på Kaga kyrkas kyrkogård. Han begrovs »in albis», dvs. han döptes "
        "först på dödsbädden och dog medan han ännu var iförd sin dopklädnad.")
URL_KAGA = check_fv("1969_272", KAGA, "en visserligen endast i två sena avskrifter bevarad tradition")
assert IDX["1969_272"]["authors"] == ["Yrlid Ahlstedt, Inger"]
# Bender Jørgensen 2008 (recension av Annika Larsson, Klädd krigare, 2007), s. 314–315
LARSSON = ("Larsson ser runestenene som juridiske dokumenter der skulle sikre arven for slægten, og understreger "
           "realiteterne bag dåbsklæderne: nye, hvide klæder der markerede en ny, kristen identitet.")
# citatet går över sidbrytningen s. 314/315 och kontrolleras i två delar
LARSSON_A, LARSSON_B = LARSSON.split(" realiteterne")
URL_BJ = check_fv("2008_litt_d", LARSSON_A, "realiteterne" + LARSSON_B, "Et sidste problemkompleks handler om runesten, rejst over mænd der »dog i dopkläder»",
                  "Annika Larsson, Klädd krigare. Skifte i skandina", "Lise Bender Jørgensen",
                  "sin personlige erfaring som arkæolog og tekstilingeniør")  # "arkeologen Annika Larsson"
# Fridell 2013 (recension av Zilmer & Jesch 2012), Futhark 4, s. 208
FRIDELL = ("Henrik Williams föreslår en nytolkning av frasen dauðr i hwitawaðum, som återfinns på sju uppländska runstenar. "
           "Man har hittills menat att uttrycket syftar på vita dopkläder, som nyligen kristnade och nydöpta burit på sin "
           "dödsbädd. Williams vill i stället tänka sig att det refererar till vita kläder burna efter den exklusivare "
           "ceremoni som kallas konfirmation, bl.a. med hänvisning till ett ställe i Víga-Glúms saga, där huvudpersonens död "
           "skildras. Förklaringen verkar fullt möjlig, men framläggs med vederbörlig försiktighet.")
for _q in ("återfinns på sju uppländska runstenar", "menat att uttrycket syftar på vita dopkläder, som nyligen kristnade och nydöpta burit på sin dödsbädd",
           "Williams vill i stället tänka sig att det refererar till vita kläder burna efter den exklusivare ceremoni som kallas konfirmation, bl.a. med hänvisning till ett ställe i Víga-Glúms saga, där huvudpersonens död skildras. Förklaringen verkar fullt möjlig, men framläggs med vederbörlig försiktighet."):
    assert _q in FRIDELL, _q
URL_FRIDELL = check_fu("futhark_4_207_682703", "682703", FRIDELL, "Reviewed by Staffan Fridell")
# Källström 2010, Futhark 1, s. 144 och 157
KALL = ("The possibility that Øpir may have made some of these carvings at an early stage of his career should not be "
        "ruled out. The issue needs further investigation.")
URL_KALL = check_fu("futhark_1_143_381125", "381125", KALL, "U 1032, U 1036 and U 1056",
                    "huita ' huaþum hvītavāðum, U 1036", "died in baptismal robes in Denmark(?)")

# ---- 7. Bilder (Wikimedia Commons) --------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["U 243", "U 613", "U 699", "U 1036"])
INFO = commons.commons_info(list(FILES.values()))
IMG = {s: INFO[f] for s, f in FILES.items()}
assert (IMG["U 243"]["author"], IMG["U 243"]["licence"]) == ("Johan Göransson", "CC0") and FILES["U 243"] == "Bautil 68 - U 243.png"
assert (IMG["U 613"]["author"], IMG["U 613"]["licence"]) == ("Wilson44691", "CC BY-SA 3.0")
assert (IMG["U 699"]["author"], IMG["U 699"]["licence"]) == ("The Swedish National Heritage Board", "CC0")
assert (IMG["U 1036"]["author"], IMG["U 1036"]["licence"]) == ("Ulkl", "Public domain")


def lic(s):
    i = IMG[s]
    return f"[{i['licence']}]({i['licence_url']})" if i.get("licence_url") else i["licence"]


def credit(s, lang):
    sv = lang == "sv"
    via = f"via [Wikimedia Commons]({IMG[s]['page']})"
    if s == "U 243":
        return (f"Träsnitt nummer 68 i Johan Göranssons *Bautil* (1750), {lic(s)}, {via}." if sv else
                f"Woodcut number 68 in Johan Göransson's *Bautil* (1750), {lic(s)}, {via}.")
    if s == "U 699":
        return (f"Äldre teckning, Riksantikvarieämbetet, {lic(s)}, {via}." if sv else
                f"Older drawing, Swedish National Heritage Board, {lic(s)}, {via}.")
    pd = "public domain" if IMG[s]["licence"] == "Public domain" else lic(s)
    return f"{'Foto' if sv else 'Photo'}: {IMG[s]['author']}, {pd}, {via}."


# ---- 8. Kartan: Upplands runstenar och de sju (Natural Earth, egen läsare av shapefiler) ------------------------------
NE = os.path.join(ROOT, "data", "cache", "r", "naturalearth")
VIEW = (16.75, 59.15, 19.25, 60.62)  # lon/lat


def polygons(path, box):
    """Polygonerna i en shapefil (typ 5) vars ram skär box, som listor av (lon, lat)-ringar."""
    data = open(path, "rb").read()
    pos, out = 100, []
    while pos < len(data):
        _, length = struct.unpack(">ii", data[pos:pos + 8])
        rec = data[pos + 8:pos + 8 + 2 * length]
        pos += 8 + 2 * length
        if struct.unpack("<i", rec[:4])[0] != 5:
            continue
        x0, y0, x1, y1 = struct.unpack("<4d", rec[4:36])
        if x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3]:
            continue
        nparts, npts = struct.unpack("<2i", rec[36:44])
        parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])) + [npts]
        pts = struct.unpack(f"<{2 * npts}d", rec[44 + 4 * nparts:44 + 4 * nparts + 16 * npts])
        for a, b in zip(parts, parts[1:]):
            out.append([(pts[2 * i], pts[2 * i + 1]) for i in range(a, b)])
    return out


def draw_map(lang):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    sv = lang == "sv"
    ink, muted, accent, landc = "#222222", "#6b6b6b", "#b7410e", "#f4f4f2"
    pad = 0.4
    box = (VIEW[0] - pad, VIEW[1] - pad, VIEW[2] + pad, VIEW[3] + pad)
    land = polygons(os.path.join(NE, "land", "ne_10m_land.shp"), box)
    lakes = (polygons(os.path.join(NE, "lakes", "ne_10m_lakes.shp"), box)
             + polygons(os.path.join(NE, "lakes_europe", "ne_10m_lakes_europe.shp"), box))
    assert land and lakes
    fig, ax = plt.subplots(figsize=(7.2, 7.4), dpi=170)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#e9eef2")
    for ring in land:
        ax.add_patch(Polygon(ring, closed=True, facecolor=landc, edgecolor="#94a3b8", lw=0.4))
    for ring in lakes:
        ax.add_patch(Polygon(ring, closed=True, facecolor="#e9eef2", edgecolor="#cbd5e1", lw=0.3))
    bg = [(r["lon"], r["lat"]) for r in U_STONES if r["lat"] is not None and r["signum"] not in SEVEN]
    ax.scatter([p[0] for p in bg], [p[1] for p in bg], s=5, color="#9aa5b1", alpha=0.6, lw=0, zorder=3,
               label="Upplands övriga runstenar" if sv else "Uppland's other runestones")
    pts = {s: (BY[s]["lon"], BY[s]["lat"]) for s in SEVEN}
    ax.scatter([p[0] for p in pts.values()], [p[1] for p in pts.values()], s=70, color=accent, edgecolor="white", lw=1.2,
               zorder=5, label="De sju stenarna i vita kläder" if sv else "The seven stones in white clothes")
    upps = "Uppsala (U 896, U Fv1973;194)"
    labels = {"U 243": ("U 243 Molnby", (8, -4)), "U 364": ("U 364 Gådersta", (8, 2)),
              "U 613": ("U 613 Torsätra", (8, 2)), "U 699": ("U 699 Amnö", (8, -10)),
              "U 896": (upps, (8, 2)), "U 1036": ("U 1036 Tensta", (8, 2))}
    for s, (txt, off) in labels.items():
        ha = "right" if off[0] < 0 else "left"
        ax.annotate(txt, pts[s], xytext=off, textcoords="offset points", fontsize=8.5, color=ink, ha=ha, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    ax.set_xlim(VIEW[0], VIEW[2])
    ax.set_ylim(VIEW[1], VIEW[3])
    ax.set_aspect(1 / 0.503)  # cos(59.8°)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(loc="lower left", fontsize=8, frameon=True, facecolor="white", edgecolor="none", labelcolor=ink)
    ax.set_title("De sju runstenarna som säger ”i vita kläder”" if sv else "The seven runestones that say “in white clothes”",
                 color=ink, fontsize=11, loc="left")
    fig.text(0.01, 0.01, ("Karta: Vitki, efter Samnordisk runtextdatabas (ODbL). Kustlinjer och sjöar: Natural Earth.") if sv else
             ("Map: Vitki, after the Scandinavian Runic-text Data Base (ODbL). Coastlines and lakes: Natural Earth."),
             fontsize=7, color=muted)
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    out = os.path.join(ROOT, "utdata", "blogg", "vita_klader")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, f"karta_{lang}.png"), "wb").write(buf.getvalue())
    return blog_figures.freeze(buf.getvalue())


MAP = {lang: draw_map(lang) for lang in ("sv", "en")}


# ---- 9. Diagrammet: stilgrupperna --------------------------------------------------------------------------------------
def chart(lang):
    sv = lang == "sv"
    around = "omkring" if sv else "about"
    out = [":::chart När restes stenarna? Andel i varje stilgrupp" if sv else
           ":::chart When were the stones raised? Share in each style group",
           f"# Upplands {sp(N_UST)} runstenar med säker stilgrupp" if sv else
           f"# Uppland's {N_UST:,} runestones with a certain style group"]
    for g in ORDER:
        hi = "+" if g in ("Pr3", "Pr4") else ""
        out.append(f"{hi}{g} | {pc(UST[g] / N_UST)} | {around} {Y[g][0]}–{Y[g][1]}")
    out.append("# De fyra stenarna i vita kläder med säker stilgrupp" if sv else
               "# The four stones in white clothes with a certain style group")
    n3 = sum(1 for s in SURE if BY[s]["style"] == "Pr3")
    n4 = sum(1 for s in SURE if BY[s]["style"] == "Pr4")
    assert (n3, n4) == (2, 2)
    out.append(f"+Pr3 | {pc(n3 / len(SURE))} | U 243, U 699")
    out.append(f"+Pr4 | {pc(n4 / len(SURE))} | U 1036, U Fv1973;194")
    out.append(f"Källa: Samnordisk runtextdatabas, stilgrupper efter Anne-Sofie Gräslund med hennes ungefärliga år. "
               f"Gruppen KB ({KB} %) är utelämnad. Diagram: Vitki." if sv else
               f"Source: the Scandinavian Runic-text Data Base, style groups after Anne-Sofie Gräslund with her approximate "
               f"years. The KB group ({KB} %) is left out. Chart: Vitki.")
    return "\n".join(out) + "\n:::"


# ---- 10. Texten ------------------------------------------------------------------------------------------------------------
title = "Döda i vita kläder – sju runstenar över dem som dog nydöpta"
title_en = "Died in white clothes – seven runestones for those who died newly baptised"
summary = ("På sju runstenar, alla i Uppland, står att den döde dog ”i vita kläder”, i dopdräkten. Vi läste alla sju: "
           "vilka som dog och vilka som reste stenarna, var och när de restes, vad mer som står på dem och vad "
           "forskarna har trott att orden betyder.")
summary_en = ("Seven runestones, all in Uppland, say that the dead man died “in white clothes”, in his baptismal robes; we "
              "read all seven to see who died, who raised the stones, where and when, and what scholars think the words meant.")

body = f"""*{Q243}*

De dog i vita kläder.

Raden stod på en sten vid Molnby i Vallentuna socken (U 243). Holmlaugr och Holmfríðr lät resa den efter Fasti och Sigfastr, sina söner. Stenen är borta sedan länge, och vi känner den från ett träsnitt i *Bautil*, 1700-talets stora bok om runstenarna. Två söner hade dött, och om hur de dog ville föräldrarna att stenen skulle säga en enda sak: att de dog i vita kläder.

![Runstenen U 243 i Bautil]({IMG['U 243']['thumb']})
U 243 vid Molnby, Vallentuna. Stenen är försvunnen. {credit('U 243', 'sv')}

Den som har varit på ett dop i dag har sett det vita: ett litet barn i en lång klänning som kanske har gått i arv i familjen. På runstenarna är det söner och en make som bär det vita, och de dog i det.

Den här artikeln räknar och beskriver. Vi prövar ingen hypotes mot slumpen; stenarna är för få för det. Vi har letat upp alla stenar som säger detta och frågat dem det man kan fråga en sten: vem dog, vem reste den, var står den, när restes den och vad mer står på den?

## Vad orden betyder

På stenarna står *i hvitavaðum*, ordagrant ’i vita kläder’. När en ny sten med orden hittades under en pelare i Uppsala domkyrka 1972 skrev Elisabeth Svärdström och Helmer Gustavson i Fornvännen:

> {SVG_VADER}

Den som döptes fick en vit dräkt och bar den en tid efteråt. Den som dog under den tiden dog alltså i vita kläder. Svärdström och Gustavson kallade uttrycket ”ett språkligt karakteristikon för missionstiden”, ett språkligt kännetecken för tiden när kristendomen kom.

## Sju stenar, alla i Uppland

Vi sökte i Samnordisk runtextdatabas, Rundata, både i translittereringen, alltså runorna skrivna med våra bokstäver så som de står på stenen, och i normaliseringen, där forskarna har skrivit orden i en enhetlig fornspråklig form. Ristarna stavade olika, och därför letade vi efter alla stavningar. Vi hittade sju stenar:

- **U 243**, Molnby i Vallentuna socken: *{SPELL['U 243']}*
- **U 364**, Gådersta i Skepptuna socken: *{SPELL['U 364']}*
- **U 613**, Torsätra i Västra Ryds socken: *{SPELL['U 613']}*
- **U 699**, Amnö i Veckholms socken: *{SPELL['U 699']}*
- **U 896**, Håga i Bondkyrka socken (Uppsala): *{SPELL['U 896']}*
- **U 1036**, Tensta kyrka: *{SPELL['U 1036']}*
- **U Fv1973;194**, Uppsala domkyrka: *{SPELL['U Fv1973;194']}*

Hakparenteserna markerar runor som i dag är borta men som är kända från äldre avbildningar eller kan fyllas i. Ristaren av U 896 skrev *f* där andra skrev *u*, och ristaren av U 1036 satte in ett *h* som inte hör dit, precis som i namnet Andvéttr på samma sten (*anhuit*), vilket Magnus Källström har noterat (Källström 2010).

Det är sju av Upplands {sp(N_U)} vikingatida runstenar, ungefär en sten av 170. Bland Sveriges övriga runstenar finns inte en enda till, och Rundata har inga i Danmark eller Norge och inga på andra föremål än runstenar. Talet stämmer med litteraturen: Svärdström och Gustavson räknade med sex stenar utöver den nya, och Staffan Fridell skriver i Futhark 2013 att frasen ”återfinns på sju uppländska runstenar”.

![Karta över de sju stenarna i Uppland]({MAP['sv']})
De sju stenarna (rostrött) bland Upplands övriga runstenar (grått). Hågastenen är utsatt där den står i dag, i Uppsala, omkring {round(DIST_M, -1):.0f} meter från domkyrkostenen. Karta: Vitki, efter Samnordisk runtextdatabas (ODbL). Kustlinjer och sjöar: Natural Earth.

Tre stenar ligger i Attundaland, tre i Tiundaland och en i Fjädrundaland. Det är ungefär så Upplands runstenar fördelar sig över huvud taget ({UF['attundaland']} procent i Attundaland, {UF['tiundaland']} i Tiundaland, {UF['fjadrundaland']} i Fjädrundaland). De vita kläderna hörde alltså inte till en enda bygd. De står där Upplands runstenar står.

## De döda var män

Alla döda vars kön går att läsa är män: sju män på sex stenar, eftersom Molnbystenen gäller två bröder. På den sjunde, stenen i domkyrkan, är både namnet och släktskapen borta. Ingen av stenarna är, så långt den går att läsa, rest efter en kvinna.

Fyra stenar är resta efter söner och en efter en make. På två går släktskapen inte att läsa. Två säger var mannen dog: i Danmark på U 699, och troligen på U 896, där ordet är skadat.

Svärdström och Gustavson skrev 1973 att det ”i nästan samtliga fall” rör sig om ”unga män som sannolikt dött utomlands”. Stenarna själva säger mindre än så. Att de döda var unga står inte på någon av dem, men att de var söner står på fyra. Att de dog utomlands står på en, kanske två. Resten är en tolkning, och kanske en rimlig sådan, för en son som dör före sina föräldrar är ofta ung. Men det står inte på stenarna.

## Kvinnorna reste stenarna

På fem av stenarna går det att läsa vem som reste dem, och på fyra av dem står en kvinna:

- **Una** reste U 613 ensam efter sin son Eysteinn.
- **Ingileif** reste U 699 ensam efter Brúni, sin make.
- **Helga** reste U 1036 efter sin son Andvéttr. Före hennes namn står tre mansnamn utan verb: Sigfastr, Brandr och Véketill.
- **Holmfríðr** reste U 243 tillsammans med Holmlaugr, efter sina två söner.

Den femte, U 364, restes av Karsi och någon vars namn bara börjar på *kar-*.

Fyra av fem är många jämfört med Upplands runstenar i allmänhet, där en kvinna står bland resarna på ungefär var tredje sten ({W_ALL} procent). Men stenar efter barn är annorlunda: på dem står en kvinna bland resarna på ungefär sex av tio ({W_CHILD} procent). De två siffrorna kommer ur Vitkis automatiska läsning av vem som reste stenarna och efter vem, och den läsningen gör enstaka fel. Med fem läsbara stenar kan vi inte säga mer än att stenarna i vita kläder följer ett mönster vi har sett förut: när en son dog stod hans mor ofta med på stenen.

## När restes de?

Runstenar har inga årtal. De kan ordnas efter ornamentiken i de stilgrupper som Anne-Sofie Gräslund har ställt upp, och Rundata anger gruppen för de flesta uppländska stenar. Av de sju har fyra en säker stilgrupp: två Pr3, omkring {Y['Pr3'][0]}–{Y['Pr3'][1]}, och två Pr4, omkring {Y['Pr4'][0]}–{Y['Pr4'][1]}. Två av de osäkra hamnar också där, i Pr3–Pr4 och Pr4. Bara Hågastenen (U 896) förs med frågetecken till en tidigare grupp, Pr1.

{chart('sv')}

De vita kläderna hör alltså till andra halvan av 1000-talet. Men det är också då de flesta uppländska runstenar restes: {LATE} procent av stenarna med säker stilgrupp hör till Pr3 eller Pr4. Formeln hör hemma i den tid då Uppland reste flest stenar, och diagrammet visar inte att den skulle ha haft någon egen tid.

## Vad mer står på stenarna?

**Kors.** Rundata anger ett kors på fyra av de sju (U 243, U 613, U 896 och U 1036), och på domkyrkostenen såg Svärdström och Gustavson ”rester av två korsarmar”. Fem av sju stenar har alltså kors. Av Upplands runstenar i allmänhet har ungefär hälften ett kors enligt Rundata ({U_CROSS} procent), så här finns inget märkligt.

**Böner.** Två stenar har en bön: *Guð hialpi salu hans*, ’Gud hjälpe hans själ’, på Unas sten och *Kristr hialpi sial AndvettaR*, ’Kristus hjälpe Andvétts själ’, på Helgas. Bland Upplands runstenar har ungefär en av åtta en sådan bön ({U_PRAY} procent). Hågastenen säger dessutom att den är rest *fyr and*, ’för anden’, den dödes själ, och de orden finns på bara sex uppländska stenar. Två eller tre av sju är fler än vanligt, men med sju stenar är det en iakttagelse och inget mer.

**Bilder.** Domkyrkostenen har, enligt Svärdström och Gustavson, ”en framställning av en ryttare till häst” ovanför runslingan.

**Ristarna.** Ingen enskild ristare står bakom orden. Rundata för Molnbystenen och Unas sten till Visäte, utan signatur men med hans stil. Ingileifs sten är signerad av Balle. Hågastenen bär signaturen *Reð runaR ØpiR*, ’Öpir ordnade runorna’, och Helgas sten är tillskriven Öpir, men Rundata noterar för båda att de inte verkar vara den kände Öpirs verk (för Helgas sten med hänvisning till Åhlén 1997). Magnus Källström har prövat frågan på nytt och skriver om en grupp stenar kring Uppsala, bland dem Helgas:

> {KALL}

Det betyder: att Öpir kan ha gjort några av dessa ristningar tidigt i sin bana ska inte uteslutas; frågan behöver undersökas vidare. Gåderstastenen är tillskriven Torfast och Torsten och har drag som liknar Åsmunds. Stenarna knyts alltså till minst fyra olika ristare i tre folkland. Det var ett sätt att tala om de döda och inte en enskild ristares vana.

## Ingileif, Una och Helga

*{Q699}*

Ingileif lät resa stenen efter Brúni, sin make. Han dog i Danmark i vita kläder. Balle ristade.

![Runstenen U 699]({IMG['U 699']['thumb']})
U 699 från Amnö i Veckholm, i dag i Ekholmens park. {credit('U 699', 'sv')}

Balle var en flitig ristare: Rundata räknar {len(BALLE_S)} runstenar som han signerade och {len(BALLE_A)} som tillskrivs honom. Här skrev han in en enda omständighet om Brúnis död: var och i vad. Stenen säger inte om han döptes i Danmark eller redan hemma, och inte heller hur han dog. Den säger att hans hustru ville att det skulle stå.

*{Q613}*

Una lät resa denna sten efter sin son Eysteinn, som dog i vita kläder. Gud hjälpe hans själ.

![Runstenen U 613]({IMG['U 613']['thumb']})
U 613 från Torsätra, i dag på Historiska museet i Stockholm. {credit('U 613', 'sv')}

Unas sten stod vid Torsätra tillsammans med en annan sten av samma ristare, U 614. Sven B. F. Jansson kallade dem ”dubbelmonumentet vid Torsätra” och noterade att Visäte gav dem helt olika ornamentik (Jansson 1972). Den andra stenen restes av Skúli och Folki efter deras bror och säger: *{Q614}* ’Han var sjuk ute när de tog gäld på Gotland.’ Två män, två ovanliga dödsfall, på samma plats. Om familjerna hörde ihop vet vi inte.

*{Q1036}*

Helga lät resa stenen efter Andvéttr, sin son, som dog i vita kläder. Kristus hjälpe Andvétts själ.

![Runstenen U 1036]({IMG['U 1036']['thumb']})
U 1036 vid Tensta kyrka. {credit('U 1036', 'sv')}

Helgas sten står vid Tensta kyrka, alldeles utanför kyrkogårdsmuren. Den är en av de stenar där bönen nämner den döde vid namn.

## Vad betydde de vita kläderna?

Stenarna säger att männen dog i vita kläder. De säger inte varför de bar dem. Forskarna har läst orden på åtminstone fyra sätt, och vi räknar dem hellre än att döma mellan dem.

**Dopet på dödsbädden.** Svärdström och Gustavson skrev om domkyrkostenen: ”{SVG_DOD}” Staffan Fridell sammanfattar 2013 den gängse läsningen så: man har ”menat att uttrycket syftar på vita dopkläder, som nyligen kristnade och nydöpta burit på sin dödsbädd”.

**En senare parallell.** Om Kaga kyrka i Östergötland finns en tradition, bevarad bara i två sena avskrifter, om den förste som begravdes på kyrkogården. Inger Ahlstedt Yrlid återger den:

> {KAGA}

**Konfirmationen.** Henrik Williams har föreslagit att de vita kläderna i stället hör till konfirmationen. Vi har inte läst hans text själva utan återger den efter Fridells recension:

> Williams vill i stället tänka sig att det refererar till vita kläder burna efter den exklusivare ceremoni som kallas konfirmation, bl.a. med hänvisning till ett ställe i Víga-Glúms saga, där huvudpersonens död skildras. Förklaringen verkar fullt möjlig, men framläggs med vederbörlig försiktighet.

**Arvet.** Arkeologen Annika Larsson har läst stenarna som dokument om arv, enligt Lise Bender Jørgensens recension av hennes avhandling (vi har inte läst avhandlingen):

> {LARSSON}

Det vill säga: Larsson ser runstenarna som juridiska handlingar som skulle säkra arvet för släkten, och betonar det konkreta bakom dopkläderna: nya, vita kläder som markerade en ny, kristen identitet.

Ingen av läsningarna kan avgöras av stenarna. Ingen sten nämner sjukdom, sår eller dödsbädd, och den enda omständighet som står är ett land, Danmark.

Här tillåter vi oss en tolkning som inte är stenarnas egen. Vilken läsning som än stämmer valde familjerna att skriva det på en sten som andra skulle läsa. Det som skrevs var en upplysning till de levande om var den döde hörde hemma: han dog som kristen.

## Vad vi inte vet

- **Sju stenar är för få för statistik.** Procenttalen ovan beskriver de sju och prövar ingenting.
- **Tre stenar är skadade.** På domkyrkostenen är början av ordet ifylld ([hvi]tavaðum), och Danmark på Hågastenen är osäkert.
- **”Christening robes” är en tolkning.** Rundatas engelska översätter med dopkläder; runorna säger vita kläder.
- **Stilgrupperna är inte årtal.** Åren är ungefärliga.
- **Könen läses ur namn och släktord.** Jämförelsetalen för hela Uppland kommer ur en automatisk läsning.
- **En sten är borta.** Molnbystenen känner vi bara från äldre avbildningar.

Den vita dopklänning som går i arv i många familjer i dag har släktingar på sju uppländska stenar. Gå och se en av dem. Läs vem som reste den. Fyra gånger av fem är det en kvinna.

:::box Det viktigaste i korthet
- Sju runstenar, alla i Uppland, säger att den döde dog i vita kläder, i dopdräkten. Det är ungefär en av 170 uppländska stenar, och orden finns inte på någon annan sten i Rundata.
- De döda är män, oftast söner, och stenarna restes oftast av kvinnor: mödrar och en hustru. Det passar med att mödrar ofta står på stenar efter barn.
- Stenarna hör till andra halvan av 1000-talet, då Uppland reste flest stenar, och huggdes av flera olika ristare. Orden var ett sätt att tala om de döda, inte en ristares egenhet.
- Vad de vita kläderna betydde, dop på dödsbädden, konfirmation eller ett arv som skulle säkras, säger stenarna inte. De säger bara att familjen ville att det skulle stå där.
:::

## Se själv

- **U 613**, Unas sten, finns på Historiska museet i Stockholm.
- **U 1036**, Helgas sten, står vid Tensta kyrka norr om Uppsala, omedelbart utanför kyrkogårdsmuren.
- **U 896**, Hågastenen, står i Universitetsparken i Uppsala.
- **U Fv1973;194** ligger under en pelare i Uppsala domkyrka, mellan Sture- och Finstakoren, och en del syns i en golvbrunn.
- **U 699**, Ingileifs sten, står i Ekholmens park i Veckholm.

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Runtexterna citeras ordagrant efter Rundatas normalisering; översättningarna är våra, efter Rundatas engelska.
- Svärdström, Elisabeth & Gustavson, Helmer 1973. Runfynd 1972. *Fornvännen* 68, s. 185–203 (citaten s. 194). [Fri fulltext från Riksantikvarieämbetet]({URL_SVG}).
- Jansson, Sven B. F. 1972. Den nyfunna runstenen vid Lilla Vilunda i Upplands Väsby. *Fornvännen* 67, s. 170–179 (s. 178). [Fri fulltext]({URL_JANSSON}).
- Ahlstedt Yrlid, Inger 1969. De romanska målningarna på Kaga kyrkas triumfbågsvägg. *Fornvännen* 64, s. 272–286 (citatet s. 273). [Fri fulltext]({URL_KAGA}).
- Bender Jørgensen, Lise 2008. Recension av Annika Larsson, *Klädd krigare. Skifte i skandinaviskt dräktskick kring år 1000* (OPIA 39, Uppsala 2007). *Fornvännen* 103, s. 313–315 (citatet s. 314–315). [Fri fulltext]({URL_BJ}).
- Fridell, Staffan 2013. Recension av K. Zilmer & J. Jesch (red.), *Epigraphic Literacy and Christian Identity* (Turnhout: Brepols 2012). *Futhark* 4, s. 207–208 (citaten s. 208). [Fri fulltext]({URL_FRIDELL}).
- Källström, Magnus 2010. Some Thoughts on the Rune-Carver ØpiR: A Revaluation of the Storvreta Stone (U 1022) and Some Related Carvings. *Futhark* 1, s. 143–160 (s. 144 och 157). [Fri fulltext]({URL_KALL}).
- Williams, Henrik 2012. Bidrag om frasen *dauðr i hwitawaðum* i K. Zilmer & J. Jesch (red.), *Epigraphic Literacy and Christian Identity*. Utrecht Studies in Medieval Literacy 4. Turnhout: Brepols. Inte läst av oss; återgivet efter Fridell 2013.
- Larsson, Annika 2007. *Klädd krigare. Skifte i skandinaviskt dräktskick kring år 1000*. OPIA 39. Uppsala. Inte läst av oss; återgivet efter Bender Jørgensen 2008.
- Gräslund, Anne-Sofie 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139. Stilgrupperna och deras år.
- Bilder: Wikimedia Commons, med upphov och licens i bildtexterna. Karta och diagram: Vitki."""

body_en = f"""*{Q243}*

They died in white clothes.

The line stood on a stone at Molnby in Vallentuna parish (U 243). Holmlaugr and Holmfríðr had it raised in memory of Fasti and Sigfastr, their sons. The stone has long been lost, and we know it from a woodcut in *Bautil*, the great eighteenth-century book of runestones. Two sons had died, and about how they died the parents wanted the stone to say one thing only: that they died in white clothes.

![The runestone U 243 in Bautil]({IMG['U 243']['thumb']})
U 243 at Molnby, Vallentuna. The stone is lost. {credit('U 243', 'en')}

Anyone who has been to a christening today has seen the white: a small child in a long gown that may have been handed down in the family. On the runestones it is sons and a husband who wear the white, and they died in it.

This article counts and describes. We test no hypothesis against chance; there are too few stones for that. We have found every stone that says this and asked them what one can ask a stone: who died, who raised it, where does it stand, when was it raised, and what else is on it?

## What the words mean

The stones say *i hvitavaðum*, literally ‘in white clothes’. When a new stone with the words was found under a pillar in Uppsala Cathedral in 1972, Elisabeth Svärdström and Helmer Gustavson wrote in Fornvännen:

> {SVG_VADER}

That is: the ‘white clothes’ of the inscription are the clothes the baptised person wore during baptism and for a time afterwards. Whoever died in that time died in white clothes. Svärdström and Gustavson called the expression “ett språkligt karakteristikon för missionstiden”, a linguistic hallmark of the time when Christianity arrived.

## Seven stones, all in Uppland

We searched the Scandinavian Runic-text Data Base, Rundata, both in the transliteration, the runes written in our letters as they stand on the stone, and in the normalisation, where scholars have written the words in a uniform Old Norse form. The carvers spelled differently, so we searched for every spelling. We found seven stones:

- **U 243**, Molnby in Vallentuna parish: *{SPELL['U 243']}*
- **U 364**, Gådersta in Skepptuna parish: *{SPELL['U 364']}*
- **U 613**, Torsätra in Västra Ryd parish: *{SPELL['U 613']}*
- **U 699**, Amnö in Veckholm parish: *{SPELL['U 699']}*
- **U 896**, Håga in Bondkyrka parish (Uppsala): *{SPELL['U 896']}*
- **U 1036**, Tensta church: *{SPELL['U 1036']}*
- **U Fv1973;194**, Uppsala Cathedral: *{SPELL['U Fv1973;194']}*

Square brackets mark runes that are gone today but are known from older drawings or can be supplied. The carver of U 896 wrote *f* where others wrote *u*, and the carver of U 1036 added an *h* that does not belong, just as in the name Andvéttr on the same stone (*anhuit*), as Magnus Källström has noted (Källström 2010).

That is seven of Uppland's {N_U:,} Viking-age runestones, about one stone in 170. Among the rest of Sweden's runestones there is not a single other one, and Rundata has none in Denmark or Norway and none on objects other than runestones. The number agrees with the literature: Svärdström and Gustavson counted six stones besides the new one, and Staffan Fridell writes in Futhark in 2013 that the phrase “återfinns på sju uppländska runstenar”, is found on seven Uppland runestones.

![Map of the seven stones in Uppland]({MAP['en']})
The seven stones (rust red) among Uppland's other runestones (grey). The Håga stone is shown where it stands today, in Uppsala, about {round(DIST_M, -1):.0f} metres from the cathedral stone. Map: Vitki, after the Scandinavian Runic-text Data Base (ODbL). Coastlines and lakes: Natural Earth.

Three stones lie in Attundaland, three in Tiundaland and one in Fjädrundaland, the old folk-lands of Uppland. That is roughly how Uppland's runestones are spread overall ({UF['attundaland']} per cent in Attundaland, {UF['tiundaland']} in Tiundaland, {UF['fjadrundaland']} in Fjädrundaland). The white clothes did not belong to one district. They stand where Uppland's runestones stand.

## The dead were men

All the dead whose sex can be read are men: seven men on six stones, since the Molnby stone is for two brothers. On the seventh, the stone in the cathedral, both the name and the relationship are gone. None of the stones, as far as it can be read, was raised for a woman.

Four stones were raised for sons and one for a husband. On two the relationship cannot be read. Two say where the man died: in Denmark on U 699, and probably on U 896, where the word is damaged.

Svärdström and Gustavson wrote in 1973 that “in nearly all cases” these are “young men who probably died abroad”. The stones themselves say less than that. That the dead were young is on none of them, but that they were sons is on four. That they died abroad is on one, perhaps two. The rest is an interpretation, and perhaps a reasonable one, for a son who dies before his parents is often young. But it is not on the stones.

## The women raised the stones

On five of the stones it is possible to read who raised them, and on four of them a woman stands:

- **Una** raised U 613 alone in memory of her son Eysteinn.
- **Ingileif** raised U 699 alone in memory of Brúni, her husband.
- **Helga** raised U 1036 in memory of her son Andvéttr. Before her name stand three men's names without a verb: Sigfastr, Brandr and Véketill.
- **Holmfríðr** raised U 243 together with Holmlaugr, in memory of their two sons.

The fifth, U 364, was raised by Karsi and someone whose name only begins with *kar-*.

Four of five is a lot compared with Uppland's runestones in general, where a woman is among the raisers on about one stone in three ({W_ALL} per cent). But stones for children are different: on them a woman is among the raisers on about six in ten ({W_CHILD} per cent). Those two figures come from Vitki's automatic reading of who raised the stones and for whom, and that reading makes the occasional mistake. With five legible stones we cannot say more than that the stones in white clothes follow a pattern we have seen before: when a son died, his mother often stood on the stone.

## When were they raised?

Runestones carry no years. They can be ordered by their ornament, in the style groups Anne-Sofie Gräslund has set out, and Rundata gives the group for most Uppland stones. Of the seven, four have a certain style group: two Pr3, about {Y['Pr3'][0]}–{Y['Pr3'][1]}, and two Pr4, about {Y['Pr4'][0]}–{Y['Pr4'][1]}. Two of the uncertain ones also land there, in Pr3–Pr4 and Pr4. Only the Håga stone (U 896) is placed, with a question mark, in an earlier group, Pr1.

{chart('en')}

The white clothes thus belong to the second half of the eleventh century. But that is also when most Uppland runestones were raised: {LATE} per cent of the stones with a certain style group belong to Pr3 or Pr4. The formula belongs to the time when Uppland raised the most stones, and the chart does not show that it had a time of its own.

## What else is on the stones?

**Crosses.** Rundata records a cross on four of the seven (U 243, U 613, U 896 and U 1036), and on the cathedral stone Svärdström and Gustavson saw “rester av två korsarmar”, remains of two cross arms. Five of seven stones thus have a cross. About half of Uppland's runestones in general have a cross according to Rundata ({U_CROSS} per cent), so there is nothing unusual here.

**Prayers.** Two stones have a prayer: *Guð hialpi salu hans*, ‘God help his soul’, on Una's stone and *Kristr hialpi sial AndvettaR*, ‘Christ help Andvéttr's soul’, on Helga's. Among Uppland's runestones about one in eight has such a prayer ({U_PRAY} per cent). The Håga stone also says it was raised *fyr and*, ‘for the spirit’, the dead man's soul, and those words occur on only six Uppland stones. Two or three of seven is more than usual, but with seven stones it is an observation and nothing more.

**Pictures.** The cathedral stone has, according to Svärdström and Gustavson, “en framställning av en ryttare till häst”, a rider on horseback, above the rune band.

**The carvers.** No single carver stands behind the words. Rundata attributes the Molnby stone and Una's stone to Visäte, unsigned but in his style. Ingileif's stone is signed by Balli. The Håga stone bears the signature *Reð runaR ØpiR*, ‘Øpir arranged the runes’, and Helga's stone is attributed to Øpir, but Rundata notes for both that they do not seem to be the work of the well-known Øpir (for Helga's stone citing Åhlén 1997). Magnus Källström has taken up the question again and writes of a group of stones around Uppsala, Helga's among them:

> {KALL}

The Gådersta stone is attributed to Torfast and Torsten and has features resembling Åsmundr's. The stones are thus linked to at least four different carvers in three folk-lands. It was a way of speaking about the dead, not one carver's habit.

## Ingileif, Una and Helga

*{Q699}*

Ingileif had the stone raised in memory of Brúni, her husband. He died in Denmark in white clothes. Balli carved.

![The runestone U 699]({IMG['U 699']['thumb']})
U 699 from Amnö in Veckholm, today in Ekholmen park. {credit('U 699', 'en')}

Balli was a busy carver: Rundata counts {len(BALLE_S)} runestones he signed and {len(BALLE_A)} attributed to him. Here he wrote down a single circumstance of Brúni's death: where, and in what. The stone does not say whether he was baptised in Denmark or already at home, nor how he died. It says that his wife wanted it written.

*{Q613}*

Una had this stone raised in memory of her son Eysteinn, who died in white clothes. God help his soul.

![The runestone U 613]({IMG['U 613']['thumb']})
U 613 from Torsätra, today in the Swedish History Museum in Stockholm. {credit('U 613', 'en')}

Una's stone stood at Torsätra together with another stone by the same carver, U 614. Sven B. F. Jansson called them “dubbelmonumentet vid Torsätra”, the double monument at Torsätra, and noted that Visäte gave them quite different ornament (Jansson 1972). The other stone was raised by Skúli and Folki in memory of their brother and says: *{Q614}* ‘He was sick abroad when they took payment on Gotland.’ Two men, two unusual deaths, at the same place. Whether the families were connected we do not know.

*{Q1036}*

Helga had the stone raised in memory of Andvéttr, her son, who died in white clothes. Christ help Andvéttr's soul.

![The runestone U 1036]({IMG['U 1036']['thumb']})
U 1036 at Tensta church. {credit('U 1036', 'en')}

Helga's stone stands at Tensta church, just outside the churchyard wall. It is one of the stones where the prayer names the dead man.

## What did the white clothes mean?

The stones say that the men died in white clothes. They do not say why they wore them. Scholars have read the words in at least four ways, and we would rather count them than judge between them.

**Baptism on the deathbed.** Svärdström and Gustavson wrote of the cathedral stone: “{SVG_DOD}” That is, the stone was probably raised by the kin of one or more people who had themselves baptised on their deathbed. Staffan Fridell in 2013 sums up the usual reading: it has been held “att uttrycket syftar på vita dopkläder, som nyligen kristnade och nydöpta burit på sin dödsbädd”, that the expression refers to white baptismal clothes worn on their deathbed by the newly converted and newly baptised.

**A later parallel.** About Kaga church in Östergötland there is a tradition, preserved only in two late copies, about the first man buried in its churchyard. Inger Ahlstedt Yrlid gives it:

> {KAGA}

That is: Kol, Kornuka's father, was the first to be buried in Kaga churchyard. He was buried *in albis*, that is, he was baptised only on his deathbed and died while still wearing his baptismal robe.

**Confirmation.** Henrik Williams has suggested that the white clothes instead belong to confirmation. We have not read his text ourselves and give it after Fridell's review:

> Williams vill i stället tänka sig att det refererar till vita kläder burna efter den exklusivare ceremoni som kallas konfirmation, bl.a. med hänvisning till ett ställe i Víga-Glúms saga, där huvudpersonens död skildras. Förklaringen verkar fullt möjlig, men framläggs med vederbörlig försiktighet.

That is: Williams would rather think the phrase refers to white clothes worn after the more exclusive ceremony called confirmation, citing among other things a passage in *Víga-Glúms saga* describing the hero's death; Fridell finds the explanation quite possible, but put forward with due caution.

**The inheritance.** The archaeologist Annika Larsson has read the stones as documents about inheritance, according to Lise Bender Jørgensen's review of her thesis (we have not read the thesis):

> {LARSSON}

That is: Larsson sees the runestones as legal documents meant to secure the inheritance for the family, and stresses the reality behind the baptismal clothes: new, white clothes that marked a new, Christian identity.

None of these readings can be settled by the stones. No stone mentions illness, wounds or a deathbed, and the only circumstance stated is a country, Denmark.

Here we allow ourselves an interpretation that is not the stones' own. Whichever reading is right, the families chose to write it on a stone that others would read. What was written was word to the living about where the dead man belonged: he died a Christian.

## What we do not know

- **Seven stones are too few for statistics.** The percentages above describe the seven and test nothing.
- **Three stones are damaged.** On the cathedral stone the start of the word is supplied ([hvi]tavaðum), and Denmark on the Håga stone is uncertain.
- **“Christening robes” is an interpretation.** Rundata's English translates with baptismal clothes; the runes say white clothes.
- **Style groups are not years.** The years are approximate.
- **Sex is read from names and kinship words.** The comparison figures for all of Uppland come from an automatic reading.
- **One stone is lost.** We know the Molnby stone only from older drawings.

The white christening gown that is handed down in many families today has relatives on seven Uppland stones. Go and see one of them. Read who raised it. Four times out of five it is a woman.

:::box The essentials in brief
- Seven runestones, all in Uppland, say that the dead man died in white clothes, in his baptismal robes. That is about one in 170 Uppland stones, and the words are on no other stone in Rundata.
- The dead are men, mostly sons, and the stones were mostly raised by women: mothers and a wife. That fits with mothers often standing on stones for children.
- The stones belong to the second half of the eleventh century, when Uppland raised the most stones, and were cut by several different carvers. The words were a way of speaking about the dead, not one carver's quirk.
- What the white clothes meant, baptism on the deathbed, confirmation or an inheritance to be secured, the stones do not say. They say only that the family wanted it written there.
:::

## See for yourself

- **U 613**, Una's stone, is in the Swedish History Museum in Stockholm.
- **U 1036**, Helga's stone, stands at Tensta church north of Uppsala, just outside the churchyard wall.
- **U 896**, the Håga stone, stands in the University Park in Uppsala.
- **U Fv1973;194** lies under a pillar in Uppsala Cathedral, between the Sture and Finsta chapels, and part of it can be seen in a well in the floor.
- **U 699**, Ingileif's stone, stands in Ekholmen park in Veckholm.

## Sources

- The Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. The runic texts are quoted verbatim from Rundata's normalisation; the translations are ours, after Rundata's English.
- Svärdström, Elisabeth & Gustavson, Helmer 1973. Runfynd 1972. *Fornvännen* 68, pp. 185–203 (quotations p. 194). [Free full text from the Swedish National Heritage Board]({URL_SVG}).
- Jansson, Sven B. F. 1972. Den nyfunna runstenen vid Lilla Vilunda i Upplands Väsby. *Fornvännen* 67, pp. 170–179 (p. 178). [Free full text]({URL_JANSSON}).
- Ahlstedt Yrlid, Inger 1969. De romanska målningarna på Kaga kyrkas triumfbågsvägg. *Fornvännen* 64, pp. 272–286 (quotation p. 273). [Free full text]({URL_KAGA}).
- Bender Jørgensen, Lise 2008. Review of Annika Larsson, *Klädd krigare. Skifte i skandinaviskt dräktskick kring år 1000* (OPIA 39, Uppsala 2007). *Fornvännen* 103, pp. 313–315 (quotation pp. 314–315). [Free full text]({URL_BJ}).
- Fridell, Staffan 2013. Review of K. Zilmer & J. Jesch (eds), *Epigraphic Literacy and Christian Identity* (Turnhout: Brepols 2012). *Futhark* 4, pp. 207–208 (quotations p. 208). [Free full text]({URL_FRIDELL}).
- Källström, Magnus 2010. Some Thoughts on the Rune-Carver ØpiR: A Revaluation of the Storvreta Stone (U 1022) and Some Related Carvings. *Futhark* 1, pp. 143–160 (pp. 144 and 157). [Free full text]({URL_KALL}).
- Williams, Henrik 2012. Contribution on the phrase *dauðr i hwitawaðum* in K. Zilmer & J. Jesch (eds), *Epigraphic Literacy and Christian Identity*. Utrecht Studies in Medieval Literacy 4. Turnhout: Brepols. Not read by us; given after Fridell 2013.
- Larsson, Annika 2007. *Klädd krigare. Skifte i skandinaviskt dräktskick kring år 1000*. OPIA 39. Uppsala. Not read by us; given after Bender Jørgensen 2008.
- Gräslund, Anne-Sofie 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139. The style groups and their years.
- Images: Wikimedia Commons, with creator and licence in the captions. Map and chart: Vitki."""

# ---- 11. Kontroller --------------------------------------------------------------------------------------------------------
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    blocks = [ln.strip() for ln in b.split("\n") if ln.strip().startswith(":::")]
    assert all(o != ":::" and c == ":::" for o, c in zip(blocks[::2], blocks[1::2])) and len(blocks) % 2 == 0, blocks
    for img in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b):
        assert img.startswith("/api/blog/figures/") or re.match(r"https://(upload|thumb)\.wikimedia\.org/", img), img
    assert b.count("![") == 5
    for u in (URL_SVG, URL_JANSSON, URL_KAGA, URL_BJ, URL_FRIDELL, URL_KALL):
        assert u in b
    assert "Vitki" in b and ("Karta: Vitki" in b or "Map: Vitki" in b)
    assert not re.search(r"\bAI\b", b)
    # aldrig siffra först i en mening (brödtexten före källorna; bild-, diagram- och listrader räknas inte)
    prose = re.split(r"^## (Källor|Sources)$", b, flags=re.M)[0]
    txt = " ".join(line for line in re.sub(r"!\[[^\]]*\]\([^)]*\)", "", prose).splitlines()
                   if "|" not in line and not line.startswith(":::"))
    bad = [txt[max(0, m.start() - 30):m.end() + 20] for m in re.finditer(r"(?<!\b[sp])[.!?]\s+\(?\d", txt)]
    assert not bad, bad
    # varje chart-värde är en procentsiffra
    for blk in re.findall(r":::chart.*?\n:::", b, re.S):
        for ln in blk.splitlines()[1:]:
            if "|" in ln:
                assert re.fullmatch(r"\d{1,3}", ln.split("|")[1].strip()), ln
assert body.index(":::box Det viktigaste i korthet") < body.index("## Se själv") < body.index("## Källor")
assert body_en.index(":::box The essentials in brief") < body_en.index("## See for yourself") < body_en.index("## Sources")
assert not re.search(r"\bjag\b", body, re.I), "vi-form"
assert len(summary_en.split(".")) == 2, "en mening"

labels = ["Forskning", "Tro och magi", "Kvinnor och barn", "Ristare", "Datering och stil"]
out = {"slug": "doda-i-vita-klader", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": labels}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "blogg", "vita_klader.json")
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
                 "topic": "Forskning|vita kläder", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
