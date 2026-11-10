"""Forskningsrapport 0 (låst mall utdata/rapporter/MALL.md, version 4; formen Datanotis): "Hundra års runforskning" –
litteraturgenomgången av Fornvännen och Futhark i november 2026, läsarkontrollen, de 28 återkommande blinda fläckarna och
frågelistan (301 frågor) som öppen forskningsagenda. Planerad publicering 19 januari 2027 (PUBLICERINGSPLAN.md); Viktor
publicerar.

HÅLLS INNE (Viktors beslut 2026-11-10, följs exakt och kontrolleras nedan): frågorna publiceras bara med titel, tema,
årtionden och en mening om varför de spelar roll; de 22 avgörande märks "Vitki prövar <månad>" ur fältet studie. Hur
varje fråga ska prövas (fälten hur/data/matbart), påståendedatabasen och alla påståendetexter och citat, motiveringarna
(relevans_skal) och relevansnivån för frågor som inte är avgörande publiceras INTE; nivåerna bara som antal totalt.
Påståendedatabasen kommer med huvudrapporten i november 2027.

Läser utdata/litteraturgenomgang/ (fynd2/ + fynd/, blindflackar.json, kontroll/, relevans.jsonl, pastaenden.jsonl,
artikelkandidater/{kandidater_*,sammanslagen_*,fragelista}.jsonl, Forskningsfrågor_Fornvännen_Futhark.xlsx) och den
publicerade texten per fråga i utdata/rapporter/rapport0_fragor_text.json (engelska titlar, varför-meningar, 20 justerade
svenska titlar). Skriver utdata/rapporter/rapport0.json och datasetet rapport0_fragelista.{json,csv}.
    ../../../.venv/bin/python build_rapport0.py [--write | --update DOC]"""
import csv
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

LG = os.path.join(ROOT, "utdata", "litteraturgenomgang")
AK = os.path.join(LG, "artikelkandidater")
RAP = os.path.join(ROOT, "utdata", "rapporter")
jl = lambda p: [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]  # noqa: E731

APP_VERSION = "3.1.0"
SITE = "https://vitkirunor.se"
MALL_SHA = open(os.path.join(RAP, "MALL.md.sha256")).read().split()[0]
assert MALL_SHA.startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-11-10"  # rapportversionens datum, fast i byggaren
SLUG = "hundra-ars-runforskning-fragelistan"
TL_SV = ("tidskrifterna hämtades och läsningen började 2026-11-09; läsningen avslutades, de återkommande blinda fläckarna "
         "räknades och läsarkontrollen gjordes 2026-11-10; frågelistan sammanställdes och bedömdes 2026-11-10")
TL_EN = ("the journals were downloaded and the reading began 2026-11-09; the reading was finished, the recurring blind spots "
         "were counted and the reader check was made 2026-11-10; the question list was compiled and rated 2026-11-10")


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


CODE = git("log", "-1", "--format=%h", "--", "utdata/litteraturgenomgang").stdout.strip() or "okänd"
assert git("merge-base", "--is-ancestor", "774ace9", "HEAD").returncode == 0  # frågelistan
assert git("merge-base", "--is-ancestor", "db91c26", "HEAD").returncode == 0  # läsarkontrollen

# ---- svensk och engelsk talform ---------------------------------------------------------------------------------------
sv_n = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731
pc = lambda k, n: round(100 * k / n)  # noqa: E731

# ---- 1. läsningarna: texter, tidskrifter, nivåer, år (samma logik som blindflackar.py) ----------------------------------
seen, ARTS = set(), []
for f in sorted(glob.glob(os.path.join(LG, "fynd2", "*.jsonl"))) + sorted(glob.glob(os.path.join(LG, "fynd", "*.jsonl"))):
    for r in jl(f):
        if r["key"] not in seen:
            seen.add(r["key"])
            r["_b"] = os.path.basename(f)[:-6]
            ARTS.append(r)
N_TEXTS = len(ARTS)
assert N_TEXTS == 1577
TIER = Counter("run" if r.get("journal") == "futhark" or not r["_b"].startswith(("fvg", "fvn"))
               else ("grann" if r["_b"].startswith("fvg") else "nara") for r in ARTS)
assert TIER == {"run": 486, "grann": 595, "nara": 496}
JOUR = Counter(r.get("journal") for r in ARTS)
assert JOUR == {"fornvannen": 1413, "futhark": 164}
YRS = {j: sorted(int(str(r["year"])[:4]) for r in ARTS if r.get("journal") == j) for j in JOUR}
assert (YRS["fornvannen"][0], YRS["fornvannen"][-1], YRS["futhark"][0], YRS["futhark"][-1]) == (1906, 2022, 2010, 2025)
REL = jl(os.path.join(LG, "relevans.jsonl"))
FV_ALL = [r for r in REL if r["journal"] == "fornvannen"]
FU_ALL = [r for r in REL if r["journal"] == "futhark"]
FV_UNREAD = sum(1 for r in FV_ALL if r["key"] not in seen)
FU_UNREAD = [r for r in FU_ALL if r["key"] not in seen]
assert (len(FV_ALL), FV_UNREAD, len(FU_ALL), len(FU_UNREAD), sum(r["whole_volume"] for r in FU_UNREAD)) == (3497, 2084, 177, 13, 11)

# ---- 2. påståenden, kandidater, sammanslagning ------------------------------------------------------------------------
CLAIMS = jl(os.path.join(LG, "pastaenden.jsonl"))
assert len(CLAIMS) == 4555 and Counter(c["priority"] for c in CLAIMS)[1] == 1244
assert {c["status"] for c in CLAIMS} == {"ej prövat"}
DELAR = sorted(glob.glob(os.path.join(AK, "del_*.jsonl")))
assert len(DELAR) == 16 and sum(len(jl(f)) for f in DELAR) == 4555
KAND = sum(sum(1 for r in jl(f) if "titel" in r) for f in glob.glob(os.path.join(AK, "kandidater_*.jsonl")))
assert KAND == 732 and sum(len(jl(f)) for f in glob.glob(os.path.join(AK, "grupp_g*.jsonl"))) == 732
GRUPPER = sorted(glob.glob(os.path.join(AK, "sammanslagen_g*.jsonl")))
MERGED = sum(len(jl(f)) for f in GRUPPER)
assert len(GRUPPER) == 9 and MERGED == 330
FQ = jl(os.path.join(AK, "fragelista.jsonl"))
N_Q = len(FQ)
assert N_Q == 301 and len({r["titel"] for r in FQ}) == N_Q
LEV = Counter(r["relevans"] for r in FQ)
assert LEV == {1: 22, 2: 65, 3: 193, 4: 21}
# the Excel sheet Viktor reads is the same list (relevance not edited by hand since)
try:
    import openpyxl
    ws = openpyxl.load_workbook(os.path.join(LG, "Forskningsfrågor_Fornvännen_Futhark.xlsx"))["Alla frågor"]
    xl = {r[3]: r[1] for r in ws.iter_rows(min_row=2, values_only=True) if r and r[3]}
    assert len(xl) == N_Q and all(xl[r["titel"]] == r["relevans"] for r in FQ), "Excel och fragelista.jsonl skiljer sig"
except ImportError:
    print("VARNING: openpyxl saknas; Excel-filen jämfördes inte")

TEMAN = [("Människor", "People"), ("Tro och kult", "Faith and cult"), ("Makt och samhälle", "Power and society"),
         ("Landskap och platser", "Landscape and places"), ("Vägar och vatten", "Roads and water"),
         ("Datering och kronologi", "Dating and chronology"), ("Språk och runor", "Language and runes"),
         ("Ristare och verkstäder", "Carvers and workshops"), ("Stenen som föremål", "The stone as an object"),
         ("Bevarande och källkritik", "Survival and source criticism"), ("Kontakter och resor", "Contacts and journeys"),
         ("Ekonomi och silver", "Economy and silver"), ("Gränser och regioner", "Borders and regions"),
         ("Forskningshistoria", "History of research"), ("Metod och nollmodeller", "Method and null models"),
         ("Andra föremål", "Other objects")]
TEMA_EN = dict(TEMAN)
TEMA_ORD = [t for t, _ in TEMAN]
assert {r["tema"] for r in FQ} == set(TEMA_ORD)
TEMA_N = Counter(r["tema"] for r in FQ)

# the studies the decisive questions belong to (PUBLICERINGSPLAN.md; bygg_fragelista.py STUDIER)
STUDIE = {
    "dec 2026 – B. Självkontroller": ("2026-12", "december 2026", "December 2026", "självkontroller av projektets egna resultat", "self-checks of the project's own results"),
    "jan 2027 – A1. Flyttade och försvunna stenar": ("2027-01", "januari 2027", "January 2027", "flyttade och försvunna stenar", "moved and lost stones"),
    "feb 2027 – A2. Registret och nämnaren": ("2027-02", "februari 2027", "February 2027", "fornminnesregistret och nämnaren", "the heritage register and the denominator"),
    "mar 2027 – C. Dateringen": ("2027-03", "mars 2027", "March 2027", "dateringen", "dating"),
    "apr 2027 – D. Platserna mot slumpen": ("2027-04", "april 2027", "April 2027", "platserna mot slumpen", "places tested against chance"),
    "maj 2027 – E. Korset och bönen": ("2027-05", "maj 2027", "May 2027", "korset och bönen", "the cross and the prayer"),
    "jun 2027 – F. Människorna": ("2027-06", "juni 2027", "June 2027", "människorna", "the people"),
    "aug 2027 – R. Ristarna": ("2027-08", "augusti 2027", "August 2027", "ristarna", "the carvers"),
    "sep 2027 – V. Vattnet och landhöjningen": ("2027-09", "september 2027", "September 2027", "vattnet och landhöjningen", "water and land uplift"),
}
DEC = [r for r in FQ if r["relevans"] == 1]
assert all(r["studie"] in STUDIE for r in DEC), [r["studie"] for r in DEC if r["studie"] not in STUDIE]
DEC_STUDIE = Counter(r["studie"] for r in DEC)
assert DEC_STUDIE["dec 2026 – B. Självkontroller"] == 3 and sum(1 for r in DEC if r["studie"].endswith(("2027",)) or " 2027 " in r["studie"]) == 19

# ---- the published text per question (hand-checked; rapport0_fragor_text.json) ---------------------------------------
PT = json.load(open(os.path.join(RAP, "rapport0_fragor_text.json"), encoding="utf-8"))["fragor"]
PTX = {p["kalla_titel"]: p for p in PT}
assert len(PTX) == N_Q and set(PTX) == {r["titel"] for r in FQ}
N_TITLE_EDIT = sum(1 for p in PT if p["titel_sv"] != p["kalla_titel"])
assert N_TITLE_EDIT == 20 and all(("titeljustering" in p) == (p["titel_sv"] != p["kalla_titel"]) for p in PT)


def sort_key(s):
    s = re.sub(r"^[^\wÅÄÖåäö]+", "", s).lower()
    return s.replace("å", "{1").replace("ä", "{2").replace("ö", "{3")


Q = []
for r in FQ:
    p = PTX[r["titel"]]
    Q.append({"tema": r["tema"], "titel_sv": p["titel_sv"], "titel_en": p["titel_en"], "varfor_sv": p["varfor_sv"],
              "varfor_en": p["varfor_en"], "dec": sorted(r["decennier_lista"]),
              "studie": STUDIE.get(r["studie"]) if r["relevans"] == 1 else None})
Q.sort(key=lambda q: (TEMA_ORD.index(q["tema"]), sort_key(q["titel_sv"])))
for i, q in enumerate(Q, 1):
    q["id"] = f"F{i:03d}"
# every published sentence: one sentence, short, no figures, no registers or test words (the holdback)
BANNED = re.compile(r"\d|Rundata|Runor 2020|KMR|SGU|ISOF|SDHK|slump|chance|random|Vitki|nollmodell|null model", re.I)
for q in Q:
    for k in ("varfor_sv", "varfor_en"):
        assert len(q[k].split()) <= 30 and not BANNED.search(q[k]), (q["id"], k, q[k])
    assert q["dec"] and all(d % 10 == 0 and 1900 <= d <= 2020 for d in q["dec"])


def spans(decs, en=False):
    runs, cur = [], [decs[0]]
    for d in decs[1:]:
        if d == cur[-1] + 10:
            cur.append(d)
        else:
            runs.append(cur)
            cur = [d]
    runs.append(cur)
    parts = [f"{a[0]}–{min(a[-1] + 9, 2025)}" for a in runs]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + (" and " if en else " och ") + parts[-1]


def n_dec(n, en=False):
    return (f"{n} decade" + ("" if n == 1 else "s")) if en else (f"{n} årtion" + ("de" if n == 1 else "den"))


# ---- 3. läsarkontrollen ------------------------------------------------------------------------------------------------
STICK = json.load(open(os.path.join(LG, "kontroll", "stickprov.json"), encoding="utf-8"))
assert len(STICK) == 30 and Counter(s["tier"] for s in STICK) == {"run": 12, "grann": 9, "nara": 9}
KA, KB = jl(os.path.join(LG, "kontroll", "resultat_A.jsonl")), jl(os.path.join(LG, "kontroll", "resultat_B.jsonl"))
KALL = KA + KB
assert len(KA) == len(KB) == 15 and {k["key"] for k in KALL} == {s["key"] for s in STICK}
BETYG = Counter(k["betyg"] for k in KALL)
assert BETYG == {"god": 9, "användbar med förbehåll": 21}
SUMM = Counter("rätt" if k["summary"].startswith("rätt") else ("smärre" if k["summary"].startswith("smärre fel") else "annat") for k in KALL)
assert SUMM == {"rätt": 16, "smärre": 14}


def klass(b):
    b = b.lower()
    if b.startswith("rätt"):
        return "ratt"
    if "läsarens egen" in b:
        return "egen"
    if "överdriv" in b:
        return "over"
    assert "fel" in b, b
    return "fel"


CA = Counter(klass(c["bedomning"]) for k in KA for c in k["claims"])
CB = Counter(klass(c["bedomning"]) for k in KB for c in k["claims"])
assert CA == {"ratt": 90, "over": 18, "fel": 6, "egen": 4} and sum(CA.values()) == 118
assert CB == {"ratt": 45, "over": 6, "fel": 2} and sum(CB.values()) == 53
CB_PLAIN = sum(1 for k in KB for c in k["claims"] if c["bedomning"].strip() == "rätt")
assert CB_PLAIN == 38
CT = CA + CB
N_CL = sum(CT.values())
assert N_CL == 171 and CT == {"ratt": 135, "over": 24, "fel": 8, "egen": 4}
assert (pc(CA["ratt"], 118), pc(CT["ratt"], N_CL), pc(CT["over"], N_CL), pc(CT["fel"], N_CL), pc(CT["egen"], N_CL)) == (76, 79, 14, 5, 2)
P1 = Counter(p["bedomning"] for k in KALL for p in k.get("prio1") or [])
assert P1 == {"ja": 19, "delvis": 20}
WRONG_SHARE = pc(CT["over"] + CT["fel"] + CT["egen"], N_CL)
assert WRONG_SHARE == 21  # "ungefär vart femte"

# ---- 4. de blinda fläckarna -------------------------------------------------------------------------------------------
BF = json.load(open(os.path.join(LG, "blindflackar.json"), encoding="utf-8"))
assert BF["texter"] == N_TEXTS and len(BF["kategorier"]) == 28
DECS = [str(d) for d in range(1900, 2030, 10)]
assert len(DECS) == 13
for k in BF["kategorier"]:
    k["ndec"] = sum(1 for d in DECS if k["decennier"].get(d, 0) > 0)
    assert round(100 * k["texter"] / N_TEXTS, 1) == k["andel"]
ALL13 = [k for k in BF["kategorier"] if k["ndec"] == 13]
assert len(ALL13) == 23 and min(k["ndec"] for k in BF["kategorier"]) == 10
TOP = BF["kategorier"]
assert [k["texter"] for k in TOP[:4]] == [1004, 883, 674, 658] and TOP[0]["kategori"] == "Placeringar prövas inte mot slumpen"
BF_EN = {
    "Placeringar prövas inte mot slumpen": "Placements are not tested against chance",
    "Dateringen är cirkulär: stilgrupper utan oberoende fasta punkter": "Dating is circular: style groups without independent fixed points",
    "Bevarande och bortfall styr vilka stenar vi känner": "Survival and loss decide which stones we know",
    "Flyttade, inmurade och återresta stenar": "Moved, walled-in and re-erected stones",
    "Gravhällar, medeltida runor och lösföremål används inte": "Grave slabs, medieval runes and loose objects are not used",
    "Skattfynd, mynt och silver används inte": "Hoards, coins and silver are not used",
    "Kvinnor och barn": "Women and children",
    "Stenens bergart och proveniens": "The stone's rock type and provenance",
    "Korset läses som tro utan prövning; korstypologin oanvänd": "The cross is read as faith without testing; the cross typology is unused",
    "Stenarna läses som befolkning eller rikedom utan nämnare": "The stones are read as population or wealth without a denominator",
    "Ristartillskrivning utan basfrekvens": "Carver attribution without a base rate",
    "Naturvetenskapliga metoder (isotoper, DNA, pollen, fosfat, LiDAR)": "Natural-science methods (isotopes, DNA, pollen, phosphate, LiDAR)",
    "Utgivare, antikvarier och dokumentationshistoria": "Editors, antiquarians and the history of documentation",
    "Sena källor (sagor, lagar, Adam) som facit": "Late sources (sagas, laws, Adam of Bremen) as the answer key",
    "Forskarnas uppmärksamhet är ojämn": "Scholarly attention is uneven",
    "Centralortsnamnen (Husby, Tuna, Hov) är oprövade": "The central-place names (Husby, Tuna, Hov) are untested",
    "Gravfältens ålder och samtidighet med stenen": "The age of the grave fields and whether they were in use when the stone was raised",
    "Norrland, samer och periferin": "Norrland, the Sami and the periphery",
    "Strandlinje, landhöjning och vattennivå": "Shoreline, land uplift and water level",
    "Kyrkornas ålder: träkyrkor syns inte": "The age of the churches: wooden churches are invisible",
    "Fornminnesregistrets täckning är ojämn": "The heritage register's coverage is uneven",
    "Vägarnas ålder och vintervägar": "The age of the roads, and winter roads",
    "Tingsplatserna är oprövade": "The assembly (thing) sites are untested",
    "De ofria, tjänstefolket och hushållet saknas": "The unfree, the servants and the household are missing",
    "Uppland och Mälardalen som norm": "Uppland and the Mälaren valley as the norm",
    "Socken-, härads- och landskapsgränser är yngre än stenarna": "Parish, hundred and provincial borders are younger than the stones",
    "Färg och ommålning": "Paint and repainting",
    "Regional eftersläpning i stil och kristnande": "Regional lag in style and Christianisation",
}
assert set(BF_EN) == {k["kategori"] for k in TOP}
BF_SV = lambda s: s.replace("(sagor, lagar, Adam)", "(sagor, lagar, Adam av Bremen)")  # noqa: E731


def bf_list(en=False):
    out = []
    for i, k in enumerate(TOP, 1):
        name = BF_EN[k["kategori"]] if en else BF_SV(k["kategori"])
        n, a = (en_n(k["texter"]), f"{k['andel']:.0f}") if en else (sv_n(k["texter"]), f"{k['andel']:.0f}")
        d = ("in all 13 decades" if k["ndec"] == 13 else f"in {k['ndec']} of 13 decades") if en else \
            ("i alla 13 årtionden" if k["ndec"] == 13 else f"i {k['ndec']} av 13 årtionden")
        texts = "texts" if en else "texter"
        out.append(f"{i}. **{name}** – {n} {texts} ({a} %), {k['forsta']}–{k['sista']}, {d}.")
    return "\n".join(out)


# ---- 5. frågelistan i texten --------------------------------------------------------------------------------------------
assert min(STUDIE[r["studie"]][0] for r in DEC) == "2026-12" and max(STUDIE[r["studie"]][0] for r in DEC) == "2027-09"
MONTHS = sorted({STUDIE[r["studie"]] for r in DEC}, key=lambda s: s[0])


def decisive(en=False):
    out = []
    for st in MONTHS:
        qs = [q for q in Q if q["studie"] == st]
        head = f"**{st[2]}: {st[4]}**" if en else f"**{st[1][0].upper() + st[1][1:]}: {st[3]}**"
        out.append(head)
        out.append("")
        for q in qs:
            t, w = (q["titel_en"], q["varfor_en"]) if en else (q["titel_sv"], q["varfor_sv"])
            mark = f"Vitki tests it {st[2]}" if en else f"Vitki prövar {st[1]}"
            rec = (f"Recurs {spans(q['dec'], True)} ({n_dec(len(q['dec']), True)})" if en else
                   f"Återkommer {spans(q['dec'])} ({n_dec(len(q['dec']))})")
            out.append(f"- **{t}** – {w} *{rec}. {mark}.*")
        out.append("")
    return "\n".join(out).rstrip()


def others(en=False):
    out = []
    for t in TEMA_ORD:
        qs = [q for q in Q if q["tema"] == t and q["studie"] is None]
        if not qs:
            continue
        assert [sort_key(q["titel_sv"]) for q in qs] == sorted(sort_key(q["titel_sv"]) for q in qs)  # no rank order
        out.append(f"**{TEMA_EN[t] if en else t} ({len(qs)})**")
        out.append("")
        for q in qs:
            out.append(f"- {q['titel_en'] if en else q['titel_sv']} ({n_dec(len(q['dec']), en)})")
        out.append("")
    return "\n".join(out).rstrip()


N_OTHER = sum(1 for q in Q if q["studie"] is None)
assert N_OTHER == N_Q - LEV[1] == 279
TEMA_LIST_SV = "; ".join(f"{t.lower() if i else t} {TEMA_N[t]}" for i, t in enumerate(TEMA_ORD))
TEMA_LIST_EN = "; ".join(f"{TEMA_EN[t] if i == 0 else TEMA_EN[t][0].lower() + TEMA_EN[t][1:]} {TEMA_N[t]}" for i, t in enumerate(TEMA_ORD))
DEC_ALL = Counter(len(r["decennier_lista"]) for r in FQ)
N_MULTI = sum(v for k, v in DEC_ALL.items() if k >= 3)
N_DEC_D5 = sum(1 for r in DEC if len(r["decennier_lista"]) >= 5)
N_ONE = DEC_ALL[1]
assert N_MULTI == 130 and N_DEC_D5 == 13 and N_ONE == 86
MED_TEXTS_DEC = sorted(r["antal_texter"] for r in DEC)[len(DEC) // 2]

# ---- titlar och citering -------------------------------------------------------------------------------------------------
title = ("Hundra års runforskning: samma frågor i varje årtionde, sällan prövade mot slumpen på hela materialet – "
         f"{sv_n(N_TEXTS)} texter och {N_Q} öppna frågor")
title_en = ("A hundred years of runic research: the same questions in every decade, seldom tested against chance on the "
            f"whole material – {en_n(N_TEXTS)} texts and {N_Q} open questions")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (data note), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. {SITE}/en/forskningsrapporter/{SLUG}")
summary = (f"Vi läste {sv_n(N_TEXTS)} texter ur Fornvännen och Futhark med AI-språkmodeller under fasta instruktioner. "
           f"{len(ALL13)} av {len(TOP)} återkommande blinda fläckar finns i varje årtionde från 1900-talets början till i dag; "
           "den största är att placeringar inte prövas mot slumpen. Ur 4 555 mätbara påståenden kom en öppen lista med "
           f"{N_Q} forskningsfrågor; de {LEV[1]} avgörande prövar Vitki från december 2026 till september 2027. En kontroll mot originaltexterna fann "
           f"{pc(CT['ratt'], N_CL)} % av påståendena rätt återgivna.")
summary_en = (f"We read {en_n(N_TEXTS)} texts from Fornvännen and Futhark with AI language models under fixed instructions. "
              f"{len(ALL13)} of {len(TOP)} recurring blind spots appear in every decade from the early twentieth century to "
              "today; the largest is that placements are not tested against chance. From 4,555 measurable claims came an "
              f"open list of {N_Q} research questions; Vitki tests the {LEV[1]} decisive ones from December 2026 to September 2027. A check against "
              f"the original texts found {pc(CT['ratt'], N_CL)} % of the claims correctly rendered.")

FV_CREDIT_SV = ("Fornvännen, utgiven av Kungl. Vitterhets Historie och Antikvitets Akademien, digitaliserad av "
                "Riksantikvarieämbetet (CC BY 4.0)")
FU_CREDIT_SV = "Futhark: International Journal of Runic Studies, Uppsala universitet, via DiVA (CC BY 4.0)"
FV_CREDIT_EN = ("Fornvännen, published by the Royal Swedish Academy of Letters, History and Antiquities (KVHAA), digitised "
                "by the Swedish National Heritage Board (CC BY 4.0)")
FU_CREDIT_EN = "Futhark: International Journal of Runic Studies, Uppsala University, via DiVA (CC BY 4.0)"

c = CT
body = f"""*Viktor Kvant, oberoende forskare. Datanotis. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, runologi, forskningshistoria, litteraturgenomgång, Fornvännen, Futhark, språkmodeller, forskningsagenda. Konkurrerande intressen: rapporten bedömer hur relevant projektets eget bidrag skulle vara; i övrigt inga. Finansiering: ingen.*

## Sammanfattning

Den här datanotisen prövar ingen hypotes. Den beskriver vad hundra års runforskning i två tidskrifter frågar, hur säker vår läsning av den är, och vilka frågor som fortfarande är öppna.

**Bakgrund och syfte.** Runforskningen har i över hundra år frågat var runstenarna restes, när, av vem och varför. Många svar bygger på exempel: en sten vid en väg, vid ett gravfält, vid en bro. Ett exempel visar att något förekommer, men inte att det är vanligare än man skulle vänta sig om stenarna stod var som helst i samma bygd. Vi ville veta vilka frågor som återkommer, om de har prövats på hela materialet, och vilka av dem ett öppet, kvantitativt projekt kan pröva.

**Material.** {sv_n(N_TEXTS)} texter: {sv_n(JOUR['fornvannen'])} ur Fornvännen (lästa texter från {YRS['fornvannen'][0]}–{YRS['fornvannen'][-1]}) och {JOUR['futhark']} ur Futhark (volym 1–15, {YRS['futhark'][0]}–{YRS['futhark'][-1]}). Det är alla texter om runor, texterna i de närliggande disciplinerna om vikingatid och tidig medeltid, och resten av Fornvännen som nämner perioden.

**Metod.** Varje text lästes av en AI-språkmodell under en fast instruktion. Läsaren skrev ned de påståenden som går att mäta, med ordagrant citat, och vad forskningen enligt läsaren har missat. Ur läsningarna kom {sv_n(len(CLAIMS))} mätbara påståenden. Nya läsare grupperade dem i {KAND} artikelkandidater, och efter sammanslagning återstod {N_Q} frågor, bedömda efter hur mycket ett svar skulle betyda för forskningen.

**Resultat.** {len(TOP)} blinda fläckar återkommer. {len(ALL13)} av dem tas upp i alla tretton årtionden från 1900-talets första till 2020-talet, och ingen i färre än tio. Störst är att placeringar inte prövas mot slumpen ({sv_n(TOP[0]['texter'])} texter, {TOP[0]['andel']:.0f} %), att dateringen är cirkulär ({TOP[1]['texter']}, {TOP[1]['andel']:.0f} %) och att bortfallet styr vilka stenar vi känner ({TOP[2]['texter']}, {TOP[2]['andel']:.0f} %). En kontroll av 30 slumpvis valda läsningar mot originaltexterna fann {c['ratt']} av {N_CL} påståenden ({pc(c['ratt'], N_CL)} %) rätt återgivna och ingen läsning opålitlig.

**Slutsats.** Det är inte nya frågor som saknar svar. Det är gamla frågor, ställda i varje generation, som sällan har prövats på hela materialet mot vad slumpen skulle ge. Frågelistan publiceras här som en öppen forskningsagenda. Vad som inte visas: siffrorna mäter hur ofta läsarna tog upp en fråga, inte hur ofta författarna själva såg den som en brist, och läsningen omfattar två tidskrifter, inte monografierna och avhandlingarna.

## 1. Källorna

**Fornvännen** har getts ut av Kungl. Vitterhets Historie och Antikvitets Akademien sedan 1906 och är en av de viktigaste tidskrifterna för svensk arkeologi och runforskning. Riksantikvarieämbetet har digitaliserat årgångarna 1906 till april 2023 under licensen CC BY 4.0. Av de {sv_n(len(FV_ALL))} texterna i den samlingen läste vi {sv_n(JOUR['fornvannen'])}. **Futhark: International Journal of Runic Studies** ges ut vid Uppsala universitet sedan 2010 och finns i DiVA under CC BY 4.0. Vi läste {JOUR['futhark']} av {len(FU_ALL)} poster; de {len(FU_UNREAD)} olästa är nästan bara hela volymer ({sum(r['whole_volume'] for r in FU_UNREAD)}), vars artiklar lästes var för sig.

Texterna valdes i tre nivåer, efter ord som räknades maskinellt i varje text:

- **Runtexterna**, {TIER['run']} texter: alla Futhark-artiklar och de Fornvännen-texter som har flera runsignum, många runord eller runor bland tidskriftens ämnesord.
- **De närliggande disciplinerna**, {TIER['grann']} texter: arkeologi, ortnamn, historia, konsthistoria och numismatik om vikingatid och tidig medeltid, med minst fem ord för perioden och fem för dess ämnen (gravfält, skattfynd, ortnamn, kristnande och liknande).
- **Resten av Fornvännen som berör perioden**, {TIER['nara']} texter, med minst två sådana ord av varje slag.

Kvar oläst är {sv_n(FV_UNREAD)} Fornvännen-texter, mest om stenålder, bronsålder och senare konsthistoria. Monografier, avhandlingar, *Sveriges runinskrifter* och andra tidskrifter ingår inte.

## 2. Läsningen och frågorna

**Läsarna var AI-modeller.** Varje omgång om ungefär tio texter lästes av en språkmodell (Claude, Anthropic) med samma skrivna instruktion. Läsaren skulle läsa hela texten, sammanfatta den, och skriva ned varje påstående som går att pröva mot data om hela runstensmaterialet, med ett ordagrant citat på högst 40 ord, ett förslag på mätning och en prioritet från 1 till 3. Läsaren skulle också säga vad texten och forskningen i stort har missat: perspektiv, oprövade antaganden, snedvridna urval, oanvända metoder och källor. Varje citat kontrollerades maskinellt mot källtexten och finns där ordagrant. Läsningen gav {sv_n(len(CLAIMS))} mätbara påståenden, {sv_n(1244)} med prioritet 1.

**Från påståenden till frågor.** Påståendena delades i tidsordning i {len(DELAR)} delar. Nya läsare, också språkmodeller under en fast instruktion, grupperade varje del till artikelkandidater: en fråga som kan prövas för hela materialet eller en stor del av det. Det gav {KAND} kandidater i {len(TEMAN)} teman. Samma fråga dök upp i många delar och slogs ihop, först inom nio temagrupper ({MERGED} frågor) och sedan mellan grupperna efter en handgranskad lista över dubbletter. Kvar blev {N_Q} frågor.

**Bedömningen.** Varje fråga fick en av fyra nivåer efter hur relevant ett svar från projektet skulle vara för forskningen, inte efter hur ny frågan är: *avgörande* om svaret skulle avgöra en långvarig debatt eller pröva ett antagande som många andra resultat vilar på, *betydande* om det ger starka nya belägg i en aktiv fråga, *användbart* om det kompletterar eller nyanserar, och *begränsat* om få forskningsresultat hänger på svaret eller om data inte räcker. Vid tvekan valdes den lägre nivån, och bedömarna sökte i ett sökindex över tidskrifterna efter om någon redan gjort samma prövning. Utfallet: {LEV[1]} avgörande, {LEV[2]} betydande, {LEV[3]} användbara och {LEV[4]} med lägre relevans. Även bedömningen gjordes av språkmodeller; den är ett omdöme, inte ett mätresultat.

**Vad som publiceras nu och vad som väntar.** Varje fråga publiceras här med titel, tema, de årtionden den återkommer i och en mening om varför svaret spelar roll. Hur varje fråga ska prövas – mått, data och jämförelser – publiceras när studien börjar, i en analysplan som låses och arkiveras med datum innan något räknas. Påståendedatabasen med alla {sv_n(len(CLAIMS))} påståenden och deras citat publiceras som eget dataset med huvudrapporten i november 2027, när påståendena har kontrollerats mot originaltexterna. I {N_TITLE_EDIT} titlar har vi tagit bort siffror, ett citat eller metodval som läsarna fört in och som ännu inte är kontrollerade.

## 3. Läsarkontrollen

Två kontrollanter granskade 30 slumpvis valda läsningar mot originaltexten: {Counter(s['tier'] for s in STICK)['run']} runtexter, {Counter(s['tier'] for s in STICK)['grann']} ur de närliggande disciplinerna och {Counter(s['tier'] for s in STICK)['nara']} ur tredje nivån. Kontrollanterna var också språkmodeller, med instruktionen att läsa hela den relevanta delen av källan och bedöma varje påstående med sidhänvisning. Det är alltså inte en mänsklig kontroll, och det är rapportens största svaghet.

- **Läsningarna som helhet:** {BETYG['god']} goda, {BETYG['användbar med förbehåll']} användbara med förbehåll och ingen opålitlig.
- **Sammanfattningarna:** {SUMM['rätt']} rätt och {SUMM['smärre']} med smärre fel; inga allvarliga fel.
- **Påståendena:** {N_CL} bedömda. {c['ratt']} var rätt återgivna ({pc(c['ratt'], N_CL)} %), {c['over']} överdrivna eller fel tillskrivna ({pc(c['over'], N_CL)} %), {c['fel']} hade sakfel i en detalj ({pc(c['fel'], N_CL)} %), till exempel fel signum eller fel fyndort, och {c['egen']} var läsarens egen slutsats utan att det sades ({pc(c['egen'], N_CL)} %). Den ena kontrollanten använde fasta kategorier ({sum(CA.values())} påståenden, {pc(CA['ratt'], sum(CA.values()))} % rätt); den andra skrev fria bedömningar, och av dess {sum(CB.values())} påståenden var {CB_PLAIN} rätt utan anmärkning och {CB['ratt'] - CB_PLAIN} rätt med en anmärkning.
- **Mätförslagen med prioritet 1:** av {sum(P1.values())} granskade var {P1['ja']} rimliga och {P1['delvis']} delvis rimliga; inget var orimligt. De delvis rimliga överskattade oftast underlaget eller hur oberoende provet skulle bli.

I klartext: ungefär fyra av fem påståenden stämmer med texten, och vart femte är överdrivet eller fel i en detalj. Felen var av fyra slag. Läsarens egen kritik presenterades som textens, ibland med ett citat om något annat som skenbart belägg. Författarnas försiktiga formuleringar föll bort. Enstaka fall gjordes till regel. Och i fritextfälten fanns enstaka verk, namn och tillskrivningar som inte står i texten; citatkontrollen fångar inte sådana.

Därför används inget påstående i en studie eller artikel utan att det har kontrollerats mot originaltexten, och läsarnas omdömen om vad forskningen missat redovisas som läsarnas, inte författarnas.

## 4. De återkommande blinda fläckarna

Efter läsningen samlade vi det läsarna tagit upp under vad forskningen missat i {len(TOP)} återkommande teman och räknade, med ett fast ordmönster per tema, hur många olika texter vars läsning tar upp temat. En text räknas en gång per tema. Siffran mäter alltså hur ofta en läsare fann frågan relevant för texten. Den mäter inte hur ofta författaren själv såg en brist; där det är författarnas egen kritik måste den citeras ur originalet. Andelen är av alla {sv_n(N_TEXTS)} texter, och åren är den första och sista lästa texten som tar upp temat.

{bf_list()}

I klartext: alla de stora frågorna finns i varje årtionde. {len(ALL13)} av de {len(TOP)} temana tas upp i alla tretton årtionden från 1900-talets första till 2020-talet, och de övriga fem i tio till tolv. Det är inte nya frågor som har dykt upp med nya metoder. Det är samma frågor som varje generation ställer om igen, och som i de lästa texterna, enligt läsarna, nästan alltid besvaras med exempel eller för en bygd i taget, inte för hela materialet mot vad slumpen skulle ge.

Det betyder inte att ingen har räknat. Palm (1992) mätte regional variation i hela det nordiska materialet, Sawyer (2000) räknade arv och resare i tusentals inskrifter, Källström (2007) gick igenom de vikingatida ristarna och deras signaturer, och Klos (2009) prövade stenarnas platser i stora delar av Sverige. Men de arbetena står i monografier, och de prövar en fråga i taget. Det som saknas är samma slags prövning, med samma kontroll mot slumpen, för alla frågorna på en gång.

## 5. Frågelistan – en öppen forskningsagenda

De {N_Q} frågorna fördelar sig på {len(TEMAN)} teman: {TEMA_LIST_SV}. {N_MULTI} av dem tas upp i minst tre olika årtionden och {N_ONE} i bara ett; av de {LEV[1]} avgörande tas {N_DEC_D5} upp i minst fem årtionden. Att en enskild fråga syns i få årtionden beror delvis på hur snävt den är formulerad: de breda temana i avsnitt 4 finns i nästan alla.

### 5.1 De {LEV[1]} avgörande frågorna

Svaren på de här frågorna bär många andra resultat: om stenarna står där de restes, hur många som försvunnit, hur gamla de är och om deras platser alls skiljer sig från slumpen. Projektet prövar dem i en låst studie i månaden; tre är kontroller av projektets egna tidigare resultat i december 2026. Under varje fråga står de årtionden den återkommer i bland de lästa texterna.

{decisive()}

### 5.2 Övriga {N_OTHER} frågor, efter tema

Frågorna står i bokstavsordning inom varje tema; ordningen säger inget om hur viktiga de är. Årtiondena och en mening om varför varje fråga spelar roll finns i datasetet (se Data och kod).

{others()}

## 6. Vad det betyder, och råd till den som använder listan

Listan är en karta över det öppna, inte en samling resultat. Ingen fråga besvaras i den här rapporten. Den som vill pröva en fråga är välkommen att göra det, med vilka data och metoder som helst, och vi vill gärna höra om någon redan har gjort det: då ska frågan strykas eller hänvisa dit.

Svagheterna, i ordning efter vikt:

1. **Läsarna och kontrollanterna var AI-modeller.** Vart femte påstående var överdrivet eller fel i en detalj. Inget av dem används utan kontroll mot originaltexten, men listan bär läsarnas urval och betoningar.
2. **Två tidskrifter är inte hela forskningen.** Monografierna, avhandlingarna, *Sveriges runinskrifter*, Runrön och andra tidskrifter är inte lästa. En fråga som ser oprövad ut här kan vara prövad där.
3. **Fläckarna är räknade med ordmönster** i läsarnas anteckningar. De mäter hur ofta ett tema togs upp, inte hur ofta författarna såg det som en brist.
4. **Bedömningen av relevans är ett omdöme**, gjort av språkmodeller, och den gäller hur viktigt projektets eget bidrag skulle vara. Det är en intressekonflikt som läsaren bör väga in.
5. **Luckor i läsningen.** {sv_n(FV_UNREAD)} Fornvännen-texter är olästa, och korta runnotiser som delar sida med en annan artikel kan ha fallit bort.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se]({SITE})). Kodläge i https://github.com/Precatio/runes: commit {CODE} (10 november 2026). Koden och resultatfilerna finns där under GPL-3.0; texterna i tidskrifterna under CC BY 4.0 hos utgivarna.

- **Datasetet** med frågelistan: `utdata/rapporter/rapport0_fragelista.json` och `.csv` ({N_Q} frågor; id, tema, titel på svenska och engelska, årtionden, varför-meningen på båda språken, och för de {LEV[1]} avgörande månaden då Vitki prövar dem). Det publiceras också som eget dataset på Zenodo; DOI läggs till här vid publiceringen. Licens CC BY 4.0.
- Hämtningen: `scripts/hamta_tidskrifter.py` (Fornvännen ur Riksantikvarieämbetets Arkivsök, Futhark ur DiVA), 9 november 2026. Urvalet i tre nivåer: `utdata/litteraturgenomgang/urval.py` (`--niva run`, `grann`, `nara`).
- Läsningen: instruktionerna `UNDERLAG.md`, `LASARE_RUN.md` och `LASARE_GRANN.md`; läsningarna i `fynd2/` och `fynd/`; sammanställningen `sammanstall.py` → `pastaenden.jsonl` (hålls inne till november 2027). Läsarna var Claude Sonnet (Anthropic).
- Läsarkontrollen: `kontroll/KONTROLL.md`, urvalet `kontroll/stickprov.json`, bedömningarna `kontroll/resultat_A.jsonl` och `resultat_B.jsonl`.
- Fläckarna: `blindflackar.py` → `blindflackar.json`; syntesen `SYNTES.md`.
- Frågelistan: `artikelkandidater/INSTRUKTION.md` och `SAMMANSLAGNING.md`, `bygg_fragelista.py` → `fragelista.jsonl` och `Forskningsfrågor_Fornvännen_Futhark.xlsx`. Den publicerade texten per fråga (engelska titlar, varför-meningarna och de {N_TITLE_EDIT} justerade titlarna) står i `utdata/rapporter/rapport0_fragor_text.json`.
- Formen: mallen `utdata/rapporter/MALL.md`, version 4, formen Datanotis. Två avvikelser: rubrikerna är anpassade till en litteraturgenomgång (Läsningen och frågorna, Läsarkontrollen, Fläckarna, Frågelistan i stället för Jämförelsen och Avvikelserna), och frågelistan gör texten längre än mallens 2 000 ord. Rapporten byggs av `utdata/blogg/build/build_rapport0.py`, som läser alla tal ur filerna och stannar om något inte stämmer eller om något som hålls inne kommer med. Ordlista: {SITE}/forskningsrapporter/begrepp.

## Referenser

- Fornvännen. Tidskrift för svensk antikvarisk forskning. Stockholm: Kungl. Vitterhets Historie och Antikvitets Akademien, 1906–. Digitaliserad av Riksantikvarieämbetet, Arkivsök, samlingen Fornvännen (1906–april 2023), https://arkivsok.raa.se, hämtad 2026-11-09. CC BY 4.0.
- Futhark: International Journal of Runic Studies 1–15 (2010–2025). Uppsala: Institutionen för nordiska språk, Uppsala universitet. ISSN 1892-0950. DiVA, https://uu.diva-portal.org, hämtad 2026-11-09. CC BY 4.0.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion.* Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin & New York: de Gruyter.
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden.* Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm.
- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna.* Runrön 7. Uppsala.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones. Custom and Commemoration in Early Medieval Scandinavia.* Oxford: Oxford University Press.

:::box Det viktigaste i korthet
- Runforskningen har ställt samma frågor i hundra år – var stenarna stod, hur gamla de är, vad som gått förlorat – men svaren bygger oftast på exempel, inte på hela materialet ställt mot slumpen.
- Frågelistan är en karta över det som är öppet, inte en samling resultat. De {LEV[1]} frågor som mest annat vilar på prövar Vitki från december 2026 till september 2027, och vem som helst får pröva vilken fråga som helst.
- Läsningen gjordes av AI-modeller. Den är en god karta men ingen källa: ungefär vart femte påstående var överdrivet eller fel i en detalj, och inget används innan det kontrollerats mot originaltexten.
- Hur varje fråga prövas publiceras i en låst plan när studien börjar; påståendena själva kommer med huvudrapporten i november 2027.
:::"""

body_en = f"""*Viktor Kvant, independent researcher. Data note. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. The English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, runology, history of research, literature review, Fornvännen, Futhark, language models, research agenda. Competing interests: the report rates how relevant the project's own contribution would be; otherwise none. Funding: none.*

## Abstract

This data note tests no hypothesis. It describes what a hundred years of runic research in two journals asks, how reliable our reading of it is, and which questions are still open.

**Background and aim.** For more than a hundred years runic research has asked where the runestones were raised, when, by whom and why. Many answers rest on examples: a stone by a road, by a grave field, by a bridge. An example shows that something occurs, but not that it is more common than one would expect if the stones stood anywhere in the same district. We wanted to know which questions recur, whether they have been tested on the whole material, and which of them an open, quantitative project can test.

**Material.** {en_n(N_TEXTS)} texts: {en_n(JOUR['fornvannen'])} from Fornvännen (texts read from {YRS['fornvannen'][0]}–{YRS['fornvannen'][-1]}) and {JOUR['futhark']} from Futhark (volumes 1–15, {YRS['futhark'][0]}–{YRS['futhark'][-1]}). These are all texts on runes, the texts in the neighbouring disciplines on the Viking Age and early Middle Ages, and the rest of Fornvännen that mentions the period.

**Method.** Each text was read by an AI language model under a fixed instruction. The reader wrote down the claims that can be measured, with a verbatim quotation, and what research had missed in the reader's view. The readings gave {en_n(len(CLAIMS))} measurable claims. New readers grouped them into {KAND} article candidates, and after merging {N_Q} questions remained, rated by how much an answer would mean for research.

**Results.** {len(TOP)} blind spots recur. {len(ALL13)} of them are raised in all thirteen decades from the 1900s to the 2020s, and none in fewer than ten. The largest are that placements are not tested against chance ({en_n(TOP[0]['texter'])} texts, {TOP[0]['andel']:.0f} %), that dating is circular ({TOP[1]['texter']}, {TOP[1]['andel']:.0f} %) and that loss decides which stones we know ({TOP[2]['texter']}, {TOP[2]['andel']:.0f} %). A check of 30 randomly chosen readings against the original texts found {c['ratt']} of {N_CL} claims ({pc(c['ratt'], N_CL)} %) correctly rendered and no reading unreliable.

**Conclusion.** These are not new questions that lack answers. They are old questions, asked in every generation, that have seldom been tested on the whole material against what chance would give. The question list is published here as an open research agenda. What is not shown: the figures measure how often the readers raised a question, not how often the authors themselves saw it as a gap, and the reading covers two journals, not the monographs and theses.

## 1. The sources

**Fornvännen** has been published by the Royal Swedish Academy of Letters, History and Antiquities (KVHAA) since 1906 and is one of the main journals for Swedish archaeology and runic research. The Swedish National Heritage Board (Riksantikvarieämbetet) has digitised the volumes from 1906 to April 2023 under the licence CC BY 4.0. Of the {en_n(len(FV_ALL))} texts in that collection we read {en_n(JOUR['fornvannen'])}. **Futhark: International Journal of Runic Studies** has been published at Uppsala University since 2010 and is available in DiVA under CC BY 4.0. We read {JOUR['futhark']} of {len(FU_ALL)} records; the {len(FU_UNREAD)} unread ones are almost all whole volumes ({sum(r['whole_volume'] for r in FU_UNREAD)}), whose articles were read one by one.

The texts were selected in three tiers, by words counted automatically in each text:

- **The runic texts**, {TIER['run']} texts: all Futhark articles and the Fornvännen texts with several runic signa, many runic words or runes among the journal's subject words.
- **The neighbouring disciplines**, {TIER['grann']} texts: archaeology, place names, history, art history and numismatics on the Viking Age and early Middle Ages, with at least five words for the period and five for its subjects (grave fields, hoards, place names, Christianisation and the like).
- **The rest of Fornvännen that touches the period**, {TIER['nara']} texts, with at least two such words of each kind.

Left unread are {en_n(FV_UNREAD)} Fornvännen texts, mostly on the Stone Age, the Bronze Age and later art history. Monographs, theses, *Sveriges runinskrifter* and other journals are not included.

## 2. The reading and the questions

**The readers were AI models.** Each batch of about ten texts was read by a language model (Claude, Anthropic) with the same written instruction. The reader was to read the whole text, summarise it, and write down every claim that can be tested against data on the whole runestone material, with a verbatim quotation of at most 40 words, a suggested measurement and a priority from 1 to 3. The reader was also to say what the text and the field at large had missed: perspectives, untested assumptions, skewed samples, unused methods and sources. Every quotation was checked automatically against the source text and occurs there verbatim. The reading gave {en_n(len(CLAIMS))} measurable claims, {en_n(1244)} of them with priority 1.

**From claims to questions.** The claims were divided in time order into {len(DELAR)} parts. New readers, also language models under a fixed instruction, grouped each part into article candidates: a question that can be tested for the whole material or a large part of it. This gave {KAND} candidates in {len(TEMAN)} themes. The same question appeared in many parts and was merged, first within nine theme groups ({MERGED} questions) and then across the groups from a hand-checked list of duplicates. {N_Q} questions remained.

**The rating.** Each question was given one of four levels by how relevant an answer from the project would be for research, not by how new the question is: *decisive* if the answer would settle a long debate or test an assumption many other results rest on, *significant* if it gives strong new evidence in an active question, *useful* if it complements or nuances, and *limited* if few research results depend on the answer or the data do not suffice. When in doubt the lower level was chosen, and the raters searched an index of the journals for whether anyone had already made the same test. The outcome: {LEV[1]} decisive, {LEV[2]} significant, {LEV[3]} useful and {LEV[4]} of lower relevance. The rating, too, was made by language models; it is a judgement, not a measurement.

**What is published now and what waits.** Each question is published here with its title, theme, the decades it recurs in and one sentence on why the answer matters. How each question is to be tested – measures, data and comparisons – is published when the study begins, in an analysis plan that is locked and archived with a date before anything is counted. The claims database with all {en_n(len(CLAIMS))} claims and their quotations will be published as a dataset of its own with the main report in November 2027, once the claims have been checked against the original texts. In {N_TITLE_EDIT} titles we have removed figures, a quotation or choices of method that the readers had brought in and that are not yet checked.

## 3. The reader check

Two checkers examined 30 randomly chosen readings against the original text: {Counter(s['tier'] for s in STICK)['run']} runic texts, {Counter(s['tier'] for s in STICK)['grann']} from the neighbouring disciplines and {Counter(s['tier'] for s in STICK)['nara']} from the third tier. The checkers were language models too, instructed to read the whole relevant part of the source and judge each claim with a page reference. It is therefore not a human check, and that is the report's greatest weakness.

- **The readings as a whole:** {BETYG['god']} good, {BETYG['användbar med förbehåll']} usable with reservations and none unreliable.
- **The summaries:** {SUMM['rätt']} correct and {SUMM['smärre']} with minor errors; no serious errors.
- **The claims:** {N_CL} judged. {c['ratt']} were correctly rendered ({pc(c['ratt'], N_CL)} %), {c['over']} overstated or wrongly attributed ({pc(c['over'], N_CL)} %), {c['fel']} had a factual error in a detail ({pc(c['fel'], N_CL)} %), such as a wrong signum or find-place, and {c['egen']} were the reader's own conclusion without saying so ({pc(c['egen'], N_CL)} %). One checker used fixed categories ({sum(CA.values())} claims, {pc(CA['ratt'], sum(CA.values()))} % correct); the other wrote free judgements, and of its {sum(CB.values())} claims {CB_PLAIN} were correct without remark and {CB['ratt'] - CB_PLAIN} correct with a remark.
- **The priority-1 measurement suggestions:** of {sum(P1.values())} examined, {P1['ja']} were reasonable and {P1['delvis']} partly reasonable; none was unreasonable. The partly reasonable ones mostly overrated the evidence or how independent the test would be.

In plain words: about four in five claims agree with the text, and one in five is overstated or wrong in a detail. The errors were of four kinds. The reader's own criticism was presented as the text's, sometimes with a quotation about something else as apparent evidence. The authors' cautious wording dropped out. Single cases were made into rules. And the free-text fields held occasional works, names and attributions that are not in the text; the quotation check does not catch those.

Therefore no claim is used in a study or an article until it has been checked against the original text, and the readers' views of what research has missed are reported as the readers', not the authors'.

## 4. The recurring blind spots

After the reading we gathered what the readers had raised about what research has missed into {len(TOP)} recurring themes and counted, with a fixed word pattern per theme, how many different texts have a reading that raises the theme. A text is counted once per theme. The figure thus measures how often a reader found the question relevant to the text. It does not measure how often the author saw a gap; where it is the authors' own criticism, it must be quoted from the original. The share is of all {en_n(N_TEXTS)} texts, and the years are the first and last text read that raises the theme.

{bf_list(True)}

In plain words: all the large questions are present in every decade. {len(ALL13)} of the {len(TOP)} themes are raised in all thirteen decades from the 1900s to the 2020s, and the remaining five in ten to twelve. These are not new questions that arrived with new methods. They are the same questions that each generation asks again, and in the texts read, according to the readers, they are almost always answered with examples or for one district at a time, not for the whole material against what chance would give.

This does not mean that nobody has counted. Palm (1992) measured regional variation across the whole Nordic material, Sawyer (2000) counted inheritance and sponsors in thousands of inscriptions, Källström (2007) examined the Viking-Age carvers and their signatures, and Klos (2009) tested the stones' sites across large parts of Sweden. But that work is in monographs, and it tests one question at a time. What is missing is the same kind of test, with the same check against chance, for all the questions at once.

## 5. The question list – an open research agenda

The {N_Q} questions fall into {len(TEMAN)} themes: {TEMA_LIST_EN}. {N_MULTI} of them are raised in at least three different decades and {N_ONE} in only one; of the {LEV[1]} decisive ones, {N_DEC_D5} are raised in at least five decades. That a single question appears in few decades partly reflects how narrowly it is phrased: the broad themes in section 4 are present in almost all.

### 5.1 The {LEV[1]} decisive questions

The answers to these questions carry many other results: whether the stones stand where they were raised, how many have been lost, how old they are and whether their sites differ from chance at all. The project tests them in one locked study a month; three are checks of the project's own earlier results in December 2026. Under each question are the decades it recurs in among the texts read.

{decisive(True)}

### 5.2 The other {N_OTHER} questions, by theme

The questions are in alphabetical order (of the Swedish titles) within each theme; the order says nothing about their importance. The decades and a sentence on why each question matters are in the dataset (see Data and code).

{others(True)}

## 6. What it means, and advice for users of the list

The list is a map of what is open, not a collection of results. No question is answered in this report. Anyone who wants to test a question is welcome to, with any data and methods, and we would like to hear if someone already has: the question should then be struck or point there.

The weaknesses, in order of importance:

1. **The readers and the checkers were AI models.** One claim in five was overstated or wrong in a detail. None is used without a check against the original text, but the list carries the readers' choices and emphases.
2. **Two journals are not the whole field.** The monographs, theses, *Sveriges runinskrifter*, Runrön and other journals are not read. A question that looks untested here may be tested there.
3. **The blind spots are counted with word patterns** in the readers' notes. They measure how often a theme was raised, not how often the authors saw it as a gap.
4. **The relevance rating is a judgement**, made by language models, and it concerns how important the project's own contribution would be. That is a conflict of interest the reader should weigh.
5. **Gaps in the reading.** {en_n(FV_UNREAD)} Fornvännen texts are unread, and short runic notices sharing a page with another article may have been missed.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se]({SITE})). Code state in https://github.com/Precatio/runes: commit {CODE} (10 November 2026). The code and the result files are there under GPL-3.0; the journal texts are under CC BY 4.0 with their publishers.

- **The dataset** with the question list: `utdata/rapporter/rapport0_fragelista.json` and `.csv` ({N_Q} questions; id, theme, title in Swedish and English, decades, the why sentence in both languages, and for the {LEV[1]} decisive ones the month Vitki tests them). It is also published as a dataset of its own on Zenodo; the DOI will be added here on publication. Licence CC BY 4.0.
- Download: `scripts/hamta_tidskrifter.py` (Fornvännen from the Heritage Board's Arkivsök, Futhark from DiVA), 9 November 2026. Selection in three tiers: `utdata/litteraturgenomgang/urval.py` (`--niva run`, `grann`, `nara`).
- Reading: the instructions `UNDERLAG.md`, `LASARE_RUN.md` and `LASARE_GRANN.md`; the readings in `fynd2/` and `fynd/`; the compilation `sammanstall.py` → `pastaenden.jsonl` (held back until November 2027). The readers were Claude Sonnet (Anthropic).
- Reader check: `kontroll/KONTROLL.md`, the sample `kontroll/stickprov.json`, the judgements `kontroll/resultat_A.jsonl` and `resultat_B.jsonl`.
- Blind spots: `blindflackar.py` → `blindflackar.json`; the synthesis `SYNTES.md`.
- Question list: `artikelkandidater/INSTRUKTION.md` and `SAMMANSLAGNING.md`, `bygg_fragelista.py` → `fragelista.jsonl` and `Forskningsfrågor_Fornvännen_Futhark.xlsx`. The published text per question (English titles, the why sentences and the {N_TITLE_EDIT} adjusted titles) is in `utdata/rapporter/rapport0_fragor_text.json`.
- Form: the template `utdata/rapporter/MALL.md`, version 4, the form Data note. Two deviations: the headings are adapted to a literature review (The reading and the questions, The reader check, The blind spots, The question list instead of The comparison and The deviations), and the question list makes the text longer than the template's 2,000 words. The report is built by `utdata/blogg/build/build_rapport0.py`, which reads every figure from the files and stops if anything does not match or if anything held back is included. Glossary: {SITE}/en/forskningsrapporter/begrepp.

## References

- Fornvännen. Journal of Swedish Antiquarian Research. Stockholm: Royal Swedish Academy of Letters, History and Antiquities (KVHAA), 1906–. Digitised by the Swedish National Heritage Board, Arkivsök, collection Fornvännen (1906–April 2023), https://arkivsok.raa.se, retrieved 2026-11-09. CC BY 4.0.
- Futhark: International Journal of Runic Studies 1–15 (2010–2025). Uppsala: Department of Scandinavian Languages, Uppsala University. ISSN 1892-0950. DiVA, https://uu.diva-portal.org, retrieved 2026-11-09. CC BY 4.0.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion.* Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin & New York: de Gruyter.
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden.* Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm.
- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna.* Runrön 7. Uppsala.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones. Custom and Commemoration in Early Medieval Scandinavia.* Oxford: Oxford University Press.

:::box The essentials in brief
- Runic research has asked the same questions for a hundred years – where the stones stood, how old they are, what has been lost – but the answers mostly rest on examples, not on the whole material set against chance.
- The question list is a map of what is open, not a collection of results. Vitki tests the {LEV[1]} questions that most else rests on from December 2026 to September 2027, and anyone may test any question.
- The reading was done by AI models. It is a good map but not a source: about one claim in five was overstated or wrong in a detail, and none is used before it has been checked against the original text.
- How each question is tested is published in a locked plan when the study begins; the claims themselves come with the main report in November 2027.
:::"""

# ---- checks: form ---------------------------------------------------------------------------------------------------------
assert "I klartext" in body and "In plain words" in body_en
assert WRONG_SHARE == 21 and pc(c["ratt"], N_CL) == 79  # "fyra av fem" / "vart femte"
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS|STATUS\.md"
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    for q in Q:  # the question titles are the readers' words and may use ordinary words like "fingeravtryck"
        head = head.replace(q["titel_sv"], "").replace(q["titel_en"], "")
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert not re.search(r"\]\(/", b), "absoluta länkar"
    assert "/forskningsrapporter/begrepp" in b
    assert b.count("CC BY 4.0") >= 4  # the journals credited
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Datanotis. Rapportversion 1, 2026-11-10. Tidslinje:")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Data note. Report version 1, 2026-11-10. Timeline:")
_h = body_en.splitlines()[0].strip("* ")
assert re.search(r"Report version (\d+), (\d{4}-\d{2}-\d{2})", _h) and re.search(r"(?:made|done) in Vitki (\d+(?:\.\d+)*)", _h)
assert re.search(r"Keywords: ([^.]+)\.", _h) and "CC BY 4.0" in _h and "*" not in TL_SV + TL_EN
_tl = re.search(r"(?:Timeline):\s*(.+?)\.\s+(?:The analysis was made)", _h).group(1).split("; ")
assert len(_tl) == 3 and all(re.search(r"\d{4}-\d{2}-\d{2}$", x) for x in _tl)
for b in (body, body_en):
    assert len(re.findall(r"(?:Vitki prövar|Vitki tests it) \w+ 202\d\.\*", b)) == LEV[1]
    for q in Q:
        assert (q["titel_sv"] if b is body else q["titel_en"]) in b, q["id"]

# ---- checks: the holdback (Viktor 2026-11-10) -------------------------------------------------------------------------------
PUB_TEXT = body + body_en


def frags(s, n=45):
    """Pieces of a held-back text long enough that finding one in the published text means a leak."""
    s = re.sub(r"\s+", " ", s or "")
    return [p.strip() for p in re.split(r"[.;|]\s", s) if len(p.strip()) >= n]


def leaks(text):
    bad = []
    for r in FQ:
        for k in ("relevans_skal", "fraga", "data", "varfor"):
            bad += [(k, f) for f in frags(r.get(k)) if f in text]
    for cl in CLAIMS:
        for k in ("quote", "claim", "how"):
            v = re.sub(r"\s+", " ", cl.get(k) or "").strip()
            if len(v) >= 30 and v in text:
                bad.append((k, v))
    return bad


assert not leaks(PUB_TEXT), leaks(PUB_TEXT)[:5]
# relevance levels: named only once each, in the aggregate paragraph of section 2
_bsv = re.sub(r"användbar\w* med förbehåll", "", body)
for word, n in (("betydande", 2), ("användbar", 2), ("begränsa", 1)):
    assert len(re.findall(word, _bsv, re.I)) == n, (word, len(re.findall(word, _bsv, re.I)))
for word, n in (("significant", 2), ("useful", 2), ("limited", 1)):
    assert len(re.findall(r"\b" + word + r"\b", body_en, re.I)) == n, word  # definition + outcome sentence
for q in Q:  # no level next to a non-decisive question
    for t in (q["titel_sv"], q["titel_en"]):
        line = [ln for ln in PUB_TEXT.split("\n") if t in ln]
        assert all(not re.search(r"betydande|användbar|begränsa|significant|useful|limited", ln, re.I) for ln in line), q["id"]

# ---- the dataset (published fields only) ------------------------------------------------------------------------------------
FIELDS = ["id", "tema_sv", "tema_en", "titel_sv", "titel_en", "artionden", "antal_artionden", "varfor_sv", "varfor_en",
          "vitki_provar_manad", "vitki_provar_sv", "vitki_provar_en"]
ROWS = []
for q in Q:
    st = q["studie"]
    ROWS.append({"id": q["id"], "tema_sv": q["tema"], "tema_en": TEMA_EN[q["tema"]], "titel_sv": q["titel_sv"],
                 "titel_en": q["titel_en"], "artionden": ";".join(str(d) for d in q["dec"]), "antal_artionden": len(q["dec"]),
                 "varfor_sv": q["varfor_sv"], "varfor_en": q["varfor_en"], "vitki_provar_manad": st[0] if st else "",
                 "vitki_provar_sv": f"Vitki prövar {st[1]} ({st[3]})" if st else "",
                 "vitki_provar_en": f"Vitki tests it {st[2]} ({st[4]})" if st else ""})
assert [list(r) for r in ROWS] == [FIELDS] * N_Q and sum(1 for r in ROWS if r["vitki_provar_manad"]) == LEV[1]
DS = {
    "titel": "Forskningsfrågor ur hundra års runforskning (Fornvännen 1906–2023, Futhark 1–15)",
    "title_en": "Research questions from a hundred years of runic research (Fornvännen 1906–2023, Futhark 1–15)",
    "version": 1, "datum": TODAY, "licens": "CC BY 4.0", "upphov": "Viktor Kvant, Vitki (vitkirunor.se)",
    "rapport": f"{SITE}/forskningsrapporter/{SLUG}", "report_en": f"{SITE}/en/forskningsrapporter/{SLUG}",
    "underlag": (f"{sv_n(N_TEXTS)} texter ur Fornvännen ({FV_CREDIT_SV}) och Futhark ({FU_CREDIT_SV}), lästa av "
                 f"AI-språkmodeller i november 2026; {sv_n(len(CLAIMS))} mätbara påståenden → {KAND} kandidater → {N_Q} frågor."),
    "basis_en": (f"{en_n(N_TEXTS)} texts from Fornvännen ({FV_CREDIT_EN}) and Futhark ({FU_CREDIT_EN}), read by AI "
                 f"language models in November 2026; {en_n(len(CLAIMS))} measurable claims → {KAND} candidates → {N_Q} questions."),
    "relevans_totalt": {"avgörande": LEV[1], "betydande": LEV[2], "användbart": LEV[3], "begränsat": LEV[4]},
    "om_urvalet": ("Publicerat: titel, tema, årtionden och en mening om varför frågan spelar roll; de avgörande frågorna "
                   "märkta med månaden då Vitki prövar dem. Inte publicerat: hur frågorna ska prövas, påståendedatabasen "
                   "(kommer med huvudrapporten i november 2027), motiveringarna och relevansnivån för enskilda frågor som "
                   "inte är avgörande. Ordningen är tema och sedan bokstavsordning."),
    "falt": {"id": "frågans nummer i den här versionen", "artionden": "årtionden (1900 = 1900–1909) då frågan tas upp i de lästa texterna",
             "varfor_sv/varfor_en": "en mening om varför svaret spelar roll för läsare och forskning",
             "vitki_provar_*": "bara för de avgörande frågorna: månaden och studien då Vitki prövar frågan"},
    "fragor": ROWS,
}
assert not leaks(json.dumps(DS, ensure_ascii=False))
assert not re.search(r'"relevans"|relevans_skal|"hur"|"data"|matbart|pastaenden|"kallor"', json.dumps(DS, ensure_ascii=False))
json.dump(DS, open(os.path.join(RAP, "rapport0_fragelista.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(RAP, "rapport0_fragelista.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(ROWS)

# ---- out ----------------------------------------------------------------------------------------------------------------------
WORDS_SV = len(body.split("## Data")[0].split())
WORDS_EN = len(body_en.split("## Data")[0].split())
PROSE_SV = len((body.split("### 5.1")[0] + body.split("## 6.")[1].split("## Data")[0]).split())
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Datering och stil", "Geografi", "Tro och magi", "Kvinnor och barn"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(RAP, "rapport0.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", WORDS_SV, "före Data och kod (löptext utan frågelistan", PROSE_SV, ");",
      len(body_en.split()), "words,", WORDS_EN, "before Data and code; dataset", N_Q, "rader")

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
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|litteraturgenomgang", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
