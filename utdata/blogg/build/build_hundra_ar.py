"""Artikelserien "Hundra år av runfrågor" (sv + en), två delar: I Grundläggarna (1906–1969) och II När forskarna började
räkna (1970–2025). Årtionde för årtionde: vilka som skrev i Fornvännen och Futhark, vilka frågor de ställde, vad som går
igen, och vad som syns först när hundra år läggs bredvid varandra. Viktor 2026-11-11: ödmjukt, det är deras forskning
allt vi gör vilar på; lyft fram dem.

Underlaget är litteraturgenomgången (utdata/litteraturgenomgang: fynd2/ + fynd/, blindflackar.json, kontroll/). Varje
siffra räknas här ur filerna och låses med assert. Varje citat kontrolleras mot originaltextens sida i sökindexet
(/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite); sidnumret räknas fram ur tidskriftens sidspann och
måste stämma med det som står i artikeln. OCR-texten har mellanslag inne i ord och ibland å/ä/ö förväxlade, så
jämförelsen tar bort blanktecken och avstavning och likställer å/ä/a och ö/ø/o. Där OCR:n har blandat två spalter
kontrolleras citatet i delar (frags), som var och en måste stå på sidan och tillsammans täcka citatet.

HOLDBACK (Viktor): inga mått, datarecept eller nollmodeller för hur Vitki ska pröva frågorna; inget om
påståendedatabasen, relevansbedömningarna eller frågelistan. Builder kontrollerar det med en ordlista.
Bilderna är fria (Commons), licens och upphov kontrollerade mot Commons API 2026-11-11.

    ../../../.venv/bin/python build_hundra_ar.py [--write | --update DOC1 DOC2]"""
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

LG = os.path.join(ROOT, "utdata", "litteraturgenomgang")
TS = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
CON = sqlite3.connect(os.path.join(TS, "sok.sqlite"))
sv_n = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731
pc = lambda a, b: round(100 * a / b)  # noqa: E731

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
# Texterna: samma sammanslagning som blindflackar.py (fynd2 vinner över fynd, en rad per nyckel) och samma nivåer.
ARTS, seen = [], set()
for f in sorted(glob.glob(os.path.join(LG, "fynd2", "*.jsonl"))) + sorted(glob.glob(os.path.join(LG, "fynd", "*.jsonl"))):
    b = os.path.basename(f)[:-6]
    for line in open(f, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r["key"] not in seen:
                seen.add(r["key"])
                r["_tier"] = ("run" if r.get("journal") == "futhark" or not b.startswith(("fvg", "fvn"))
                              else ("grann" if b.startswith("fvg") else "nara"))
                r["_y"] = int(str(r["year"])[:4])
                ARTS.append(r)
N = len(ARTS)
TIER = Counter(r["_tier"] for r in ARTS)
JOUR = Counter(r["journal"] for r in ARTS)
assert N == 1577 and TIER == {"run": 486, "grann": 595, "nara": 496} and JOUR == {"fornvannen": 1413, "futhark": 164}
DEC = Counter(r["_y"] // 10 * 10 for r in ARTS)
DECS = list(range(1900, 2030, 10))
assert sorted(DEC) == DECS and sum(DEC.values()) == N
assert min(r["_y"] for r in ARTS) == 1906 and max(r["_y"] for r in ARTS if r["journal"] == "fornvannen") == 2022
P1_TEXTS = sum(DEC[d] for d in DECS if d < 1970)
assert (DEC[1900], DEC[2010], P1_TEXTS) == (21, 282, 633)

# Hur mycket av Fornvännen som inte lästes, och hur mycket av Futhark
DOCS = CON.execute("select key, journal from docs").fetchall()
FV_ALL = sum(1 for _, j in DOCS if j == "fornvannen")
FV_UNREAD = sum(1 for k, j in DOCS if j == "fornvannen" and k not in seen)
FU_UNREAD = [k for k, j in DOCS if j == "futhark" and k not in seen]
assert FV_ALL == 3497 and FV_UNREAD == 2084 and 1950 <= FV_UNREAD <= 2150  # "omkring 2 000"
assert len(FU_UNREAD) == 13 and sum("_x_hel_" in k for k in FU_UNREAD) == 11  # hela volymer, vars artiklar är lästa var för sig

# Forskarnas spann i materialet
def span(*names):
    ys = sorted(r["_y"] for r in ARTS if any(n in str(r["authors"]) for n in names))
    return len(ys), ys[0], ys[-1]


KALL = span("Källström, Magnus", "Magnus Källström")
assert KALL == (33, 1980, 2024)
JANS = span("Jansson, Sven B. F.")
assert JANS[1:] == (1942, 1976)
SVARD = span("Svärdström, Elisabeth")
assert SVARD[1:] == (1939, 1975)

# De 28 återkommande temana (blindflackar.json): i hur många årtionden syns de?
BF = json.load(open(os.path.join(LG, "blindflackar.json"), encoding="utf-8"))
assert BF["texter"] == N and len(BF["kategorier"]) == 28
KAT = {k["kategori"]: k for k in BF["kategorier"]}
ALL13 = sum(1 for k in BF["kategorier"] if len(k["decennier"]) == 13)
assert ALL13 == 23
PER_DEC = {d: sum(1 for k in BF["kategorier"] if k["decennier"].get(str(d), 0) > 0) for d in DECS}
assert PER_DEC[1900] == 24 and min(PER_DEC[d] for d in DECS if d > 1900) == 27 and sum(v == 28 for v in PER_DEC.values()) == 9
# teman i läsbar form (vi skriver dem som frågor, inte som kritik); andel av alla texter där sorteringen noterade temat
THEMES = [("Placeringar prövas inte mot slumpen", "Var stenarna restes, och varför just där", "Where the stones were raised, and why there"),
          ("Dateringen är cirkulär: stilgrupper utan oberoende fasta punkter", "Hur gamla stenarna är", "How old the stones are"),
          ("Bevarande och bortfall styr vilka stenar vi känner", "Vilka stenar som har gått förlorade", "Which stones have been lost"),
          ("Flyttade, inmurade och återresta stenar", "Flyttade och inmurade stenar", "Moved and walled-in stones"),
          ("Gravhällar, medeltida runor och lösföremål används inte", "Gravhällar och lösa föremål med runor", "Grave slabs and loose objects with runes"),
          ("Skattfynd, mynt och silver används inte", "Skatter, mynt och silver", "Hoards, coins and silver"),
          ("Kvinnor och barn", "Kvinnor och barn", "Women and children"),
          ("Stenens bergart och proveniens", "Stenens bergart och ursprung", "The stone's rock type and origin")]
for k, _, _ in THEMES:
    assert len(KAT[k]["decennier"]) == 13, k
TH_PC = [round(KAT[k]["andel"]) for k, _, _ in THEMES]
assert TH_PC == [64, 56, 43, 42, 33, 33, 28, 24]

# Stickprovskontrollen av läsningarna (samma klassning som build_rapport0.py)
def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def klass(b):
    b = b.lower()
    return "ratt" if b.startswith("rätt") else ("egen" if "läsarens egen" in b else ("over" if "överdriv" in b else "fel"))


KC = Counter(klass(c["bedomning"]) for k in jl(os.path.join(LG, "kontroll", "resultat_A.jsonl")) + jl(os.path.join(LG, "kontroll", "resultat_B.jsonl"))
             for c in k["claims"])
assert sum(KC.values()) == 171 and KC["ratt"] == 135 and pc(KC["ratt"], 171) == 79  # "ungefär fyra av fem"

# ======================================================================================================================
# 2. Källorna: sidor, citat, länkar
# ======================================================================================================================
def _n(s):
    s = s.lower().replace("æ", "ae").replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = s.translate(str.maketrans("åäáàøöóéè", "aaaaoooee"))
    return re.sub(r"[\s­\-–—'’‘\"”“»«]+", "", s)


def pagemap(key):
    """Filens sidor → tidskriftens sidnummer. Fornvännen före 2018: sida 1 är metadata med sidspannet (ibland två
    spann); Futhark: filens sida 1 = artikelns första sida (nyckelns tredje led); Fornvännen 2018–: första sidans huvud."""
    ps = CON.execute("select page, text from pages where key=? order by page", (key,)).fetchall()
    assert ps, key
    t1 = ps[0][1]
    if "kulturarvsdata" in t1[:600]:
        line = [x for x in (y.replace("[", "").replace("]", "") for y in t1.split("\n")[:7])
                if re.match(r"\s*Fornvännen\b.*\d+\s*-\s*\d+", x)][0]
        tail = line.split("s.", 1)[1] if re.search(r"Fornvännen \d{4}\(", line) else line.split(",", 1)[-1]
        seq = [n for a, b in re.findall(r"(\d+)\s*-\s*(\d+)", tail) for n in range(int(a), int(b) + 1)]
        return {p: (seq[p - 2] if 0 <= p - 2 < len(seq) else None) for p, _ in ps}, ps
    if key.startswith("futhark_"):
        s = int(key.split("_")[2])
        return {p: s + p - 1 for p, _ in ps}, ps
    s = int(re.findall(r"\b(\d{1,3})\b", t1.split("\n")[0])[-1])
    return {p: s + p - 1 for p, _ in ps}, ps


def pages_with(key, frag):
    m, ps = pagemap(key)
    return [m[p] for p, t in ps if _n(frag) in _n(t)]


def has(key, frag):
    if "_x_hel_" in key:  # hela volymer (förord, redaktion) har ingen sidkarta; texten räcker
        assert any(_n(frag) in _n(t) for (t,) in CON.execute("select text from pages where key=?", (key,))), (key, frag)
        return
    assert pages_with(key, frag), (key, frag)


META = {}
for f in ("fornvannen", "futhark"):
    for line in open(os.path.join(TS, f, "index.jsonl"), encoding="utf-8"):
        d = json.loads(line)
        META[d["key"]] = d
JLINKS = json.load(open(os.path.join(ROOT, "data", "cache", "literature", "journals.json"), encoding="utf-8"))["articles"]


def link(key):
    if key in JLINKS and JLINKS[key].get("url"):
        return JLINKS[key]["url"]
    d = META[key]
    return d.get("uri") or (f"https://doi.org/{d['doi']}" if d.get("doi") else d["fulltext"])


def span_of(key):
    """Sidspannet, med två spann när artikeln är delad (Brate 1907: 20–34, 77–95)."""
    m, _ = pagemap(key)
    v = sorted(x for x in m.values() if x)
    runs, start = [], v[0]
    for a, b in zip(v, v[1:] + [None]):
        if b != a + 1:
            runs.append(f"{start}–{a}")
            start = b
    return ", ".join(runs)


def where(key, lang):
    """'Fornvännen 1950' / 'Futhark 4 (2013)' – Futhark med årgångens tryckta år, som det står i volymen."""
    if key.startswith("futhark_"):
        vol = key.split("_")[1]
        yrs = {"1": "2010", "2": "2011", "4": "2013", "5": "2014", "8": "2017", "9-10": "2018–2019", "12": "2021"}[vol]
        has(key, f"Futhark {vol.replace('-', '–')} ({yrs})")
        return f"Futhark {vol.replace('-', '–')} ({yrs})"
    return f"Fornvännen {META[key]['year']}"


# Citaten. q = som det står i artikeln (OCR-felen rättade); frags = det som står i OCR-texten, om det skiljer sig.
Q = {
    # ---- del I ----
    "baudou": ("2006_075", 76, "Nästan alla svenska arkeologer ser sig som lärjungar till Montelius, trots att han aldrig lett någon regelrätt undervisning.", None),
    "mont1906": ("1906_145", 148, "Att runraden således består af 3 gånger 8 runor", None),
    "brate1907": ("1907_020", 90, "bevisar naturligtvis, att denna skrifttyp är hemma i Sverige", None),
    "friesen1909": ("1909_057", 71, "då man har att konfrontera två källor af så olika art som engelska annalisters och svenska vikingars uppgifter", None),
    "mont1914": ("1914_081", 124, "icke bevarats till våra dagar, utan gått förlorade eller ännu kunna ligga okända i jorden eller i någon kyrkas mur", None),
    "friesen_ingvar": ("1914_081", 111, "Ingen antyder, att hufvudpersonen återvändt", None),
    "lind1914": ("1914_203", 224, "runristade stenar emellanåt fingo tjäna som dokument, stödjande en namngiven parts äganderätt till viss egendom", None),
    "shet1923": ("1923_201", 202, "Tolkningen er jo ellers ikke min sak; jeg har bare forsøkt en eksakt og kritisk fremstilling av det jeg nu kan læse.",
                 ["Tolkningen er jo e", "ers ikke min sak; jeg har bare for", "sökt en eksakt og kritisk fremstilling av det jeg nu kan laese."]),
    "brate1923": ("1923_222", 223, "Mig synes detta icke nog, tydningen måste gå hand i hand med läsningen", None),
    "bergman1926": ("1926_196", 196, "återfinna den av Peringskiöld omtalade runstenen på ytterväggen", None),
    "jungner1927": ("1927_046", 48, "den grupp av rundokument, som haft till syfte att för samtid och eftervärld fastslå ett arvsförhållande", None),
    "lind1928": ("1928_257", 281, "Runstenarna ställdes så, att de lätt kunde bli lästa av förbifarande; de voro självständiga monument vid sidan om, icke topprydnader på högarna.", None),
    "cnat1930": ("1930_116", 117, "att de rests vid eller i närheten av bebyggelse och oftast vid en väg", None),
    "moltke1932": ("1932_321", 324, "kun fotografiet er i stand til at yde et betryggende grundlag.", None),
    "norden1934": ("1934_097", 98, "togs detta snabbt i bruk såsom ett särdeles välkommet besvärjelsemedel just mot gravarnas gengångare", None),
    "gust1941": ("1941_243", 245, "Sedan 1932 hava 311 runstenar lagats eller rests.", None),
    "gust1941b": ("1941_243", 243, "I samband med den runologiska undersökningen har i allmänhet uppmålning med röd, för ändamålet utexperimenterad färg ägt rum.",
                  ["den runologiska undersökningen har i allmänhet uppmålning med röd, för ändamålet utexperimenterad färg ägt rum."]),
    "lind1947": ("1947_050", 50, "Till följd av Otto von Friesens i så många andra frågor välgrundade auktoritet har även den åsikten rotfäst sig, att man framför allt i Uppland vid uppförandet av kyrkor ej sällan gjort sig mödan släpa dit runstenar, som dessförinnan stått på mycket stora avstånd från kyrkplatserna.", None),
    "alsike1": ("1948_168", 168, "Under restaureringsarbeten i Alsike kyrka påträffades en runsten den 5 december 1947.", None),
    "alsike2": ("1948_168", 170, "Runstenen är en typisk Öpirsten.", None),
    "ekholm1": ("1950_137", 145, "Men det förefaller, som skulle den proportionella storleken av denna runstensgrupp blivit i hög grad överskattad.", None),
    "ekholm2": ("1950_137", 145, "För ernående av full klarhet i den här debatterade frågan om runstenarnas ursprungliga placering är dessvärre den nu föreliggande litteraturen icke tillfyllest.", None),
    "wessen1": ("1952_193", 196, "Sammanlagt har Bureus känt till icke mindre än 600 inskrifter, de allra flesta från Uppland.", None),
    "wessen2": ("1952_193", 209, "Men det är ju det märkliga, att i fråga om runstenar betyder Uppland halva Sverige.", None),
    "olsen": ("1953_327", 329, "helst vel i samarbeide med en neurolog", None),
    "holmq": ("1960_135", 138, "Runstenarna är ett grovt material, och ristningsytan är ofta ytterst summariskt tillhuggen.", None),
    "norden1961": ("1961_256", 262, "Vikingatågen var stora gemensamhetsföretag igångsatta av entreprenörer med grundat rykte för segervana.", None),
    "svard1967": ("1967_261", 262, "De runstenar som ha nyupptäckts och granskats 1966 är alla fragment, funna i sekundärt läge.", None),
    # ---- del II ----
    "svard1970": ("1970_247", 249, "Hur härmed än förhåller sig, står där i samtida stenskrift namnet på en nordman i exil.", None),
    "thompson1": ("1972_016", 16, "a tribute to von Friesen's brilliant if speculative treatment of the Upplandic runes", None),
    "thompson2": ("1972_016", 16, "Both carvers have highly distinctive styles, and yet very few traits in common.", None),
    "selinge": ("1978_075", 79, "För representativiteten i jämförande bebyggelsehistoriska beräkningar är alltså fyndfrekvenserna i regel otillräckliga",
                ["För representativiteten i jämförande bebyg", "gelsehistoriska beräkningar är alltså fyndfre", "kvenserna i regel otillräckliga"]),
    "larsson1986": ("1986_098", 98, "The stones show a connection with localities which probably belonged to families with a higher social rank than the average.", None),
    "larsson1996": ("1996_143", 144, "A.-S. Gräslunds stildateringsmetod förefaller alltså av allt att döma ha stora förutsättningar att bli ett utmärkt hjälpmedel vid tolkning av runinskrifterna ur olika aspekter och måste betraktas som ett genombrott inom den runologiska forskningen.",
                    ["Gräslunds stildateringsmetod", "förefaller alltså av allt att döma ha stora förut", "sättningar att bli ett utmärkt hjälpmedel vid",
                     "tolkning av runinskrifterna ur olika aspekter", "och måste betraktas som ett genombrott inom", "den runologiska forskningen."]),
    "orsen1": ("1997_193", 193, "Om man utgår från runstenstexterna måste det i dag, så långt det är möjligt, anses vara bevisat att runstensresande först och främst hör ihop med markering av arv och egendom och endast i andra hand med utlandsfarande.",
               ["Om man utgår från runstenstexterna måste det", "i dag, så långt det är möjligt, anses vara bevisat",
                "att runstensresande först och främst hör ihop", "med markering av arv och egendom och en", "dast i andra hand med utlandsfarande."]),
    "orsen2": ("1997_193", 194, "Jag förnekar inte att statistik kan tillföra arkeologin en ökad förståelse, men den bör inte tillämpas så att man betraktar fornlämningarna ur ett matematiskt perspektiv i högre grad än ur ett socialt och politiskt.",
               ["Jag förnekar inte att statistik kan tillföra arkeo", "login en ökad förståelse, men den bör inte",
                "lämpas så att man betraktar fornlämningarna", "ur ett matematiskt perspektiv i högre grad än", "ur ett socialt och politiskt."]),
    "hersch1999": ("1999_193", 194, "Därför får färderna social slagsida.", None),
    "larsson1999": ("1999_196", 197, "Men hans uppslag att jämföra hemkomna och omkomna utlandsfarare är fyndigt och om jag själv hade tänkt på det så hade jag troligen lagt in någon form av sådan undersökning redan i avhandlingen.",
                    ["Men hans uppslag att jämföra hemkom", "na och omkomna utlandsfarare är fyndigt och", "om jag själv hade tänkt på det så hade jag tro",
                     "ligen lagt in någon form av sådan undersök", "ning redan i avhandlingen."]),
    "hersch2001": ("2001_023", 32, "Det finns två poetiska tekniker i runstensmaterialet.", ["Det finns två poetiska tekniker i runstensmate", "rialet."]),
    "olesen2008": ("2008_litt_d", 311, "Det er derfor glædeligt for forskningen at netop en af nordisk runologi og navneforsknings mest erfarne eksperter, Lena Peterson, påtog sig opgaven",
                   ["Det er derfor glædeligt for forsk", "ningen at netop en af nordisk runologi og nav", "neforsknings mest erfarne eksperter, Lena Pe", "terson, påtog sig opgaven"]),
    "barnes2010": ("futhark_1_7_381131", 23, "Authoritarian pronouncements about the meaning and age of inscriptions should be avoided where no certainty exists.", None),
    "williams2010": ("futhark_1_27_381123", 34, "Their number, their concentration, their location, their nature, their size, and the scope of their inscriptions all indicate that they were meant to be seen and presumably read by more than a few.", None),
    "zilmer2010": ("futhark_1_123_381124", 131, "We have to reckon with the possibility of both regional and carver-related variation here", None),
    "larsson2010": ("futhark_1_249_381135", 250, "Klos börjar sin undersökning med en noggrann och kritisk utsortering av de runstenar som kan antas stå på ursprunglig plats, 730 stenar, vilket givetvis är en utmärkt grund för det fortsatta arbetet.", None),
    "kitzler2011": ("futhark_2_145_512979", 176, "The underlying hypothesis is that carving techniques may reflect the mobility patterns and contacts of the rune carvers.", None),
    "kallstrom2011": ("futhark_2_242_512988", 246, "Av dessa menar han endast ca 10 % kan vara primärt knutna till gränser (utan att samtidigt vara brostenar), medan 45 % hör samman med bylägen eller byägorna.", None),
    "barnes2013a": ("futhark_4_7_682689", 12, "The reading must be done first and must be undertaken by someone with experience in the field.", None),
    "barnes2013b": ("futhark_4_7_682689", 15, "What we suffer from both here and in the case of the Manx crosses is lack of data, not lack of theory.", None),
    "barnes2013c": ("futhark_4_7_682689", 24, "the rush to embrace “magic” in the inter-war years", None),
    "williams2013": ("futhark_4_61_682691", 68, "men veterligen har ännu inget riktigt försök gjorts att relatera observationerna till sociala faktorer.", None),
    "jesch2013": ("futhark_4_77_682692", 88, "Were these people good husbands or good farmers?", None),
    "zilmer2013": ("futhark_4_129_682695", 139, "close to 70 per cent of this material originates from two central Swedish provinces", None),
    "stille2014": ("futhark_5_137_799768", 148, "This is contrary to the commonly held notion that the relation to graves is prototypical.", None),
    "akerstrom2017": ("futhark_8_7_1333693", 55, "Att vi inte kan veta i hur stor utsträckning inskrifter har gått förlorade fram till idag gör det givetvis svårt att avgöra detta.", None),
    "krakow2021": ("37d3b87e-51fd-4a87-af76-294ffc35901a", 102, "Denna isländska sagas datering av Ingvars död har övertagits av många historiker och runologer som utgångspunkt för att datera Ingvarståget",
                   ["Denna isländska sagas da", "tering av Ingvars död har övertagits av många", "historiker och runologer som utgångspunkt för", "att datera Ingvarståget"]),
    "kallstrom2021a": ("futhark_12_7_1722787", 20, "There is currently no annual publication of new Swedish discoveries", None),
    "kallstrom2021b": ("futhark_12_7_1722787", 14, "A thorough discussion of the dating of the inscription is usually lacking for late Viking Age stones", None),
}
for qid, (key, page, q, frags) in Q.items():
    frags = frags or [q]
    nq, pos = _n(q), 0
    for fr in frags:  # delarna står i citatet i ordning och täcker det
        i = nq.find(_n(fr), pos)
        assert i >= 0, (qid, fr)
        pos = i + len(_n(fr))
        assert page in pages_with(key, fr), (qid, fr, pages_with(key, fr))
    assert sum(len(_n(fr)) for fr in frags) >= 0.85 * len(nq), qid
# Shetelig som Brate citerade honom, ordagrant (bekräftar ordet "ellers" som OCR:n läst "eliers")
assert 223 in pages_with("1923_222", "Tolkningen er jo ellers ikke min sak; jeg har bare försökt en eksakt og kritisk fremstilling av det jeg nu kan laese.")

# Sakuppgifter i texten, kontrollerade mot källorna
has("2006_075", "Mitt förslag att sammanslå Må")
has("2006_075", "nadsbladet o Fornminnesföreningens tidskrift")
has("2006_075", "antogs principiellt av Vitterhetsakademiens")
has("1919_112", "Legenda aurea")
has("1931_171", "av ovanstående 25 mer eller mindre säkra fall")
has("1953_327", "9 gånger rister han sitt navn riktig")
has("1963_303", "Euphrosyne")
has("1980_183", "Celsius")
has("1980_183", "1728")
has("1994_233", "Runor och regionalitet")
has("1992_043", "Ramqvist")
has("1986_098", "analys av hypotesen om likformig fördel")  # Larssons χ²-test av spridningen (tabell 4)
has("futhark_12_7_1722787", "In 1967, Elisabeth Svärdström began publishing new finds annually in Fornvännen")
has("futhark_12_7_1722787", "The final, most comprehensive, article entitled “Runfynd” was pub")
has("1942_225", "Då Vallentuna kyrka restaurerades 1937 påträffades en runsten")
has("futhark_4_7_682689", "Lerche Nielsen")
has("1914_203", "Sirid")
assert 205 in pages_with("1914_203", "uppfördes en verklig bro i modern mening och därtill av 75 m:s längd och över ett c:a 3 m. djupt vatten")
has("1923_201", "Venezia")
has("1997_193", "Sawyer, B. 1988. Property and inheritance in Viking")
has("2008_litt_d", "Steenholt Olesen")
has("futhark_9-10_7_1383036", "The Rök Runestone and the End of the World")
has("2008_245", "Places of assembly")
has("1970_247", "Halvdan")
has("1980_183", "Olof Celsius")
has("futhark_2_242_512988", "ca 220 runstenar")
has("futhark_4_61_682691", "Seventh International Symposium on Runes and Runic")
has("futhark_4_61_682691", "Plenary lectures")
has("futhark_5_137_799768", "Antalet kända runstenar är 82")
has("futhark_5_137_799768", "Of the fifty-three monuments with known locations, only fifteen")
has("1997_193", "recenserades av opponenten Per H. Ramqvist")
has("futhark_1_27_381123", "It is not difficult to find established interpretations of runestone texts that")
for k in ("futhark_14-15_207_2024380",):
    assert k in seen

NAMES = {  # visningsnamn och titel per källa
    "2006_075": "Evert Baudou", "1906_145": "Oscar Montelius", "1907_020": "Erik Brate", "1909_057": "Otto von Friesen",
    "1914_081": "Oscar Montelius", "1914_203": "Sune Lindqvist", "1919_112": "Otto von Friesen", "1923_201": "Haakon Shetelig",
    "1923_222": "Erik Brate", "1926_196": "Bengt Bergman", "1927_046": "Hugo Jungner", "1928_257": "Sune Lindqvist",
    "1930_116": "Bengt Cnattingius", "1931_171": "Gustaf Hallström", "1932_321": "Erik Moltke", "1934_097": "Arthur Nordén",
    "1941_243": "Karl Alfred Gustawsson", "1942_225": "Sven B. F. Jansson", "1947_050": "Sune Lindqvist", "1948_168": "Sven B. F. Jansson",
    "1950_137": "Gunnar Ekholm", "1952_193": "Elias Wessén", "1953_327": "Magnus Olsen", "1960_135": "Wilhelm Holmqvist",
    "1961_256": "Arthur Nordén", "1963_303": "Sven B. F. Jansson", "1967_261": "Elisabeth Svärdström",
    "1970_247": "Elisabeth Svärdström", "1972_094": "Elisabeth Svärdström", "1972_016": "Claiborne W. Thompson", "1978_075": "Klas-Göran Selinge",
    "1980_183": "Magnus Källström", "1986_098": "Mats G. Larsson", "1992_043": "Mats G. Larsson", "1994_233": "Jessica Gustafsson",
    "1996_143": "Mats G. Larsson", "1997_193": "Stina Orsenmark", "1999_193": "Frands Herschend", "1999_196": "Mats G. Larsson",
    "2001_023": "Frands Herschend", "2008_245": "Alexandra Sanmark och Sarah Semple", "2008_litt_d": "Rikke Steenholt Olesen (recension)",
    "futhark_1_7_381131": "Michael P. Barnes", "futhark_1_27_381123": "Henrik Williams", "futhark_1_123_381124": "Kristel Zilmer",
    "futhark_1_249_381135": "Mats G. Larsson (recension av Lydia Klos)", "futhark_2_145_512979": "Laila Kitzler Åhfeldt",
    "futhark_2_242_512988": "Magnus Källström (recension av Klas-Göran Selinge)", "futhark_4_7_682689": "Michael P. Barnes",
    "futhark_4_61_682691": "Henrik Williams", "futhark_4_77_682692": "Judith Jesch", "futhark_4_129_682695": "Kristel Zilmer",
    "futhark_5_137_799768": "Per Stille", "futhark_8_7_1333693": "Hanna Åkerström",
    "futhark_9-10_7_1383036": "Per Holmberg, Bo Gräslund, Olof Sundqvist och Henrik Williams",
    "37d3b87e-51fd-4a87-af76-294ffc35901a": "Annett Krakow", "futhark_12_7_1722787": "Magnus Källström",
}
TITLE = {k: CON.execute("select title from docs where key=?", (k,)).fetchone()[0] for k in NAMES}
TITLE["2008_litt_d"] = "Lena Peterson, Nordiskt runnamnslexikon (2007)"
TITLE["1994_233"] = "Aktuella avhandlingar 1992–1993"
TITLE["futhark_1_249_381135"] = "Review of: Lydia Klos, Runensteine in Schweden (2009)"
TITLE["futhark_2_242_512988"] = "Review of: Klas-Göran Selinge, Språket i landskapet"
assert "Selinge" in CON.execute("select title from docs where key='futhark_2_242_512988'").fetchone()[0]
assert "Klos" in CON.execute("select title from docs where key='futhark_1_249_381135'").fetchone()[0]


def cite(qid, lang="sv"):
    """Inline-källa till ett citat: [Fornvännen 1950, s. 145](länk)."""
    key, page, _, _ = Q[qid]
    return f"[{where(key, lang)}, {'s.' if lang == 'sv' else 'p.'} {page}]({link(key)})"


def at(key, page, lang="sv"):
    """Länkad sidhänvisning till en källa utan citat: [Fornvännen 1914, s. 205](länk)."""
    return f"[{where(key, lang)}, {'s.' if lang == 'sv' else ('pp.' if '–' in str(page) else 'p.')} {page}]({link(key)})"


def q(qid):
    return Q[qid][2]


def sources(keys, lang):
    out = []
    for k in sorted(set(keys), key=lambda k: (int(META[k]["year"]) if k in META else 0, NAMES[k])):
        pages = META[k]["pages"] if k.startswith("futhark_") else span_of(k)
        who = NAMES[k] if lang == "sv" else NAMES[k].replace(" och ", " and ").replace("(recension av", "(review of").replace("(recension)", "(review)")
        t = f"”{TITLE[k]}”" if lang == "sv" else f"“{TITLE[k]}”"
        out.append(f"- {who}: {t}. {where(k, lang)}, {'s.' if lang == 'sv' else 'pp.'} {pages}. "
                   f"[{'Fritt på nätet' if lang == 'sv' else 'Free online'}]({link(k)}).")
    return "\n".join(out)


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons, kontrollerade 2026-11-11)
# ======================================================================================================================
IMG = {
    "montelius": ("https://thumb.wikimedia.org/wikipedia/commons/thumb/7/70/Oscar_Montelius._Photograph._Wellcome_V0026871.jpg/960px-Oscar_Montelius._Photograph._Wellcome_V0026871.jpg",
                  "https://commons.wikimedia.org/wiki/File:Oscar_Montelius._Photograph._Wellcome_V0026871.jpg", "Wellcome Collection", "CC BY 4.0"),
    "u344": ("https://upload.wikimedia.org/wikipedia/commons/2/24/U_344%2C_Orkesta.JPG",
             "https://commons.wikimedia.org/wiki/File:U_344,_Orkesta.JPG", "Berig", "CC BY 2.5"),
    "friesen": ("https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d9/Otto_von_Friesen_av_Gunnar_Sundgren_1940_%28cropped%29.jpg/960px-Otto_von_Friesen_av_Gunnar_Sundgren_1940_%28cropped%29.jpg",
                "https://commons.wikimedia.org/wiki/File:Otto_von_Friesen_av_Gunnar_Sundgren_1940_%28cropped%29.jpg", "Gunnar Sundgren (Uppsala universitetsbibliotek)", "public domain"),
    "brate": ("https://upload.wikimedia.org/wikipedia/commons/1/12/Erik_Brate.png",
              "https://commons.wikimedia.org/wiki/File:Erik_Brate.png", "Svenska Dagbladets årsbok 1924", "public domain"),
    "alsike": ("https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7d/Runsten_UFv1948168.JPG/960px-Runsten_UFv1948168.JPG",
               "https://commons.wikimedia.org/wiki/File:Runsten_UFv1948168.JPG", "Fraaxe", "CC BY-SA 3.0"),
    "wessen": ("https://upload.wikimedia.org/wikipedia/commons/f/f2/Elias_Wess%C3%A9n.png",
               "https://commons.wikimedia.org/wiki/File:Elias_Wess%C3%A9n.png", "okänd fotograf (Svenskt porträttarkiv)", "public domain"),
    "hagia": ("https://thumb.wikimedia.org/wikipedia/commons/thumb/3/35/Runic_inscriptions_in_Hagia_Sophia.jpg/960px-Runic_inscriptions_in_Hagia_Sophia.jpg",
              "https://commons.wikimedia.org/wiki/File:Runic_inscriptions_in_Hagia_Sophia.jpg", "Onur capıt", "CC BY-SA 4.0"),
    "janssonmalar": ("https://upload.wikimedia.org/wikipedia/commons/d/d2/RunjanneRA%C3%84.jpg",
                     "https://commons.wikimedia.org/wiki/File:RunjanneRA%C3%84.jpg", "Pål-Nils Nilsson, Riksantikvarieämbetet (Kulturmiljöbild)", "CC BY 2.5 se"),
    "rok": ("https://upload.wikimedia.org/wikipedia/commons/b/b1/R%C3%B6kstenen_1.JPG",
            "https://commons.wikimedia.org/wiki/File:R%C3%B6kstenen_1.JPG", "Bengt Olof Åradsson", "CC BY 1.0"),
}


def pic(k, alt, cap_sv, cap_en, lang):
    url, page, who, lic = IMG[k]
    if lang == "sv":
        return f"![{alt[0]}]({url})\n{cap_sv} {'Foto' if k != 'brate' else 'Bild'}: {who}, {lic}, via [Wikimedia Commons]({page})."
    who_en = who.replace("okänd fotograf (Svenskt porträttarkiv)", "unknown photographer (Svenskt porträttarkiv)").replace("Uppsala universitetsbibliotek", "Uppsala University Library").replace("Svenska Dagbladets årsbok", "Svenska Dagbladet yearbook").replace("Riksantikvarieämbetet", "Swedish National Heritage Board")
    return f"![{alt[1]}]({url})\n{cap_en} {'Photo' if k != 'brate' else 'Image'}: {who_en}, {lic}, via [Wikimedia Commons]({page})."


# ======================================================================================================================
# 4. Diagrammen (procent; antalen i noten)
# ======================================================================================================================
def chart_texts(lang):
    sv = lang == "sv"
    rows = [f":::chart {'De lästa texterna, årtionde för årtionde' if sv else 'The texts we read, decade by decade'}"]
    for d in DECS:
        lab = f"{d}-talet" if sv else f"{d}s"
        if d == 1900:
            lab = "1906–1909"
        v = 100 * DEC[d] / N
        val = f"{v:.1f}".replace(".", ",") if sv else f"{v:.1f}"
        rows.append(f"{'+' if d < 1970 else ''}{lab} | {val} | {sv_n(DEC[d]) if sv else en_n(DEC[d])} {'texter' if sv else 'texts'}")
    rows.append("Källa: Fornvännen 1906–2022 och Futhark 1–15; de 1 577 texter Vitki läste. Andel av alla lästa texter; del I av serien gäller de markerade årtiondena. Diagram: Vitki."
                if sv else "Source: Fornvännen 1906–2022 and Futhark 1–15; the 1,577 texts Vitki read. Share of all texts read; part I of the series covers the highlighted decades. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_themes_per_decade(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Hur många av de 28 återkommande frågorna som syns i varje årtionde' if sv else 'How many of the 28 recurring questions appear in each decade'}"]
    for d in DECS:
        lab = (f"{d}-talet" if sv else f"{d}s") if d > 1900 else "1906–1909"
        v = 100 * PER_DEC[d] / 28
        val = f"{v:.0f}"
        rows.append(f"{'+' if d >= 1970 else ''}{lab} | {val} | {PER_DEC[d]} {'av 28' if sv else 'of 28'}")
    rows.append("Källa: Vitkis genomläsning av Fornvännen och Futhark, 1 577 texter. Ett tema räknas i ett årtionde när minst en text från årtiondet berör det. Temana är vår sortering, inte författarnas egna rubriker. Diagram: Vitki."
                if sv else "Source: Vitki's reading of Fornvännen and Futhark, 1,577 texts. A theme counts in a decade when at least one text from that decade touches on it. The themes are our sorting, not the authors' own headings. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_themes(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Åtta frågor som går igen i alla årtionden' if sv else 'Eight questions that recur in every decade'}"]
    for (k, lsv, len_), p in zip(THEMES, TH_PC):
        rows.append(f"{'+' if p == TH_PC[0] or p == TH_PC[1] else ''}{lsv if sv else len_} | {p} | {sv_n(KAT[k]['texter']) if sv else en_n(KAT[k]['texter'])} {'texter' if sv else 'texts'}")
    rows.append("Källa: Vitkis genomläsning av Fornvännen och Futhark. Andel av de 1 577 texterna där vår sortering noterade frågan; en text kan beröra flera. Alla åtta finns i vart och ett av de tretton årtiondena. Diagram: Vitki."
                if sv else "Source: Vitki's reading of Fornvännen and Futhark. Share of the 1,577 texts in which our sorting noted the question; a text can touch on several. All eight are present in each of the thirteen decades. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


# Metodmeningen (Viktor 2026-11-11: modellen nämns vid namn, kort, i metodstycket; ordet "AI" används inte)
CLAUDE_SV = ("Texterna lästes och sammanfattades med Anthropics språkmodell Claude (Claude Sonnet för läsningen, Claude Opus för "
             "sammanställningen); allt vi citerar och påstår har vi kontrollerat mot originaltexterna.")
CLAUDE_EN = ("The texts were read and summarised with Anthropic's language model Claude (Claude Sonnet for the reading, Claude Opus "
             "for the synthesis); everything we quote or state has been checked by us against the original texts.")
CHECK_SV = ("I en stickprovskontroll var ungefär fyra av fem av sammanfattningarnas påståenden rätt återgivna – därför har vi "
            "kontrollerat varje citat, namn, årtal och sidhänvisning här mot originalen.")
CHECK_EN = ("In a spot check, about four in five of the summaries' statements were rendered correctly – which is why we have checked "
            "every quotation, name, year and page reference here against the originals.")
JOURNALS_SV = ("Fornvännen ges ut av Kungl. Vitterhets Historie och Antikvitets Akademien och finns fritt via Riksantikvarieämbetets "
               "plattform [pub.raa.se](https://pub.raa.se) (CC BY 4.0). Futhark: International Journal of Runic Studies ges ut av "
               "Uppsala universitet och Universitetet i Oslo och finns fritt i [DiVA](https://uu.diva-portal.org) och på "
               "[futhark-journal.com](http://www.futhark-journal.com) (CC BY).")
JOURNALS_EN = ("Fornvännen is published by the Royal Swedish Academy of Letters, History and Antiquities and is freely available "
               "through the Swedish National Heritage Board's platform [pub.raa.se](https://pub.raa.se) (CC BY 4.0). Futhark: "
               "International Journal of Runic Studies is published by Uppsala University and the University of Oslo and is freely "
               "available in [DiVA](https://uu.diva-portal.org) and at [futhark-journal.com](http://www.futhark-journal.com) (CC BY).")
has("futhark_x_hel_2024374", "All articles are available free of charge at http://www.futhark-journal.com")
has("futhark_x_hel_2024374", "University of Oslo")


# ======================================================================================================================
# 5. Del I: Grundläggarna, 1906–1969
# ======================================================================================================================
P1_KEYS = ["2006_075", "1906_145", "1907_020", "1909_057", "1914_081", "1914_203", "1919_112", "1923_201", "1923_222",
           "1926_196", "1927_046", "1928_257", "1930_116", "1931_171", "1932_321", "1934_097", "1941_243", "1942_225",
           "1947_050", "1948_168", "1950_137", "1952_193", "1953_327", "1960_135", "1961_256", "1963_303", "1967_261"]

title1 = "Hundra år av runfrågor I: Grundläggarna som ställde frågorna vi fortfarande ställer"
title1_en = "A Hundred Years of Runic Questions I: The Founders Who Asked What We Still Ask"
summary1 = ("Vi har läst Fornvännen från första årgången 1906 och tidskriften Futhark, sammanlagt 1 577 texter, för att se vilka "
            "frågor forskarna har ställt om runorna och runstenarna. Första delen följer grundläggarna årtionde för årtionde fram "
            "till 1969: Montelius, von Friesen, Brate, Lindqvist, Wessén, Jansson, Svärdström och många fler. Allt Vitki gör vilar "
            "på deras arbete, och deras frågor är förvånansvärt ofta våra.")
summary1_en = ("We have read Fornvännen from its first volume in 1906 and the journal Futhark, 1,577 texts in all, to see which "
               "questions scholars have asked about runes and runestones. The first part follows the founders decade by decade "
               "to 1969: Montelius, von Friesen, Brate, Lindqvist, Wessén, Jansson, Svärdström and many more. Everything Vitki "
               "does rests on their work, and their questions are surprisingly often ours.")

body1 = f"""Den som i dag står framför en runsten vid en kyrka i Uppland läser oftast en skylt: ett signum, en översättning, kanske en datering. Bakom varje rad på skylten står en människa som en gång stod på samma plats, med anteckningsbok, kamera eller magnesiumbloss, och försökte förstå vad hon såg. Den här serien handlar om dem.

Vitki är byggt på deras arbete. Varje läsning vi räknar på, varje signum och nästan varje datering går tillbaka på någon som läste en sten, gav ut den och diskuterade den med sina kolleger – ofta i tidskriften Fornvännen. Vi ville veta vilka frågor de ställde, i vilken ordning, och vilka frågor som kommer tillbaka. Det enklaste sättet att ta reda på det var att läsa.

## Hur vi läste

Vi har läst Fornvännen från första årgången 1906 till 2022 och Futhark, den internationella tidskriften för runforskning, från första volymen 2010. Det blev {sv_n(N)} texter: {TIER['run']} om runor och runstenar, {TIER['grann']} ur närliggande ämnen – arkeologi, ortnamn, historia, konsthistoria och mynt – om vikingatid och tidig medeltid, och {TIER['nara']} andra Fornvännen-texter som berör perioden. {CLAUDE_SV} {CHECK_SV} Båda tidskrifterna finns fritt på nätet, och varje citat nedan har en länk till sin sida.

Den här första delen går fram till 1969. Den andra börjar 1970, ungefär när forskarna började räkna.

{chart_texts('sv')}

De första åren är texterna få, för Fornvännen var en tunn tidskrift och runorna en liten del av den. Från 2010 växer stapeln, eftersom Futhark kommer till. Men redan de tidiga årgångarna ställer nästan alla de frågor som den här serien handlar om.

## 1906–1909: En ny tidskrift och en gammal fråga

Fornvännen föddes 1906 ur två äldre tidskrifter. Arkeologen Oscar Almgren föreslog att de skulle slås samman, och Vitterhetsakademien sade ja i januari samma år. Det var en tid då en enda man fortfarande stod i centrum. Evert Baudou, som hundra år senare skrev tidskriftens födelsehistoria, sammanfattar det så: ”{q('baudou')}” ({cite('baudou')}).

{pic('montelius', ('Oscar Montelius', 'Oscar Montelius'), 'Oscar Montelius (1843–1921), arkeologen som nästan alla svenska arkeologer kring 1900 räknade som sin lärare.', 'Oscar Montelius (1843–1921), the archaeologist whom nearly every Swedish archaeologist around 1900 counted as a teacher.', 'sv')}

Montelius själv skrev i första årgången om en guldbrakteat från Vadstena och en nyfunnen brakteat präglad med samma stämpel. Han räknade runorna i futharken på den och konstaterade ”{q('mont1906')}” ({cite('mont1906')}). Det är en liten iakttagelse, men den är en räkning, och den är rätt.

Året därpå skrev språkforskaren Erik Brate om runinskrifterna på ön Man. Hans fråga var varifrån skriften kom, och hans svar var att Röksteninskrifternas ålderdomligare runor ”{q('brate1907')}” och därifrån spridit sig västerut ({cite('brate1907')}). Frågan om var en skrifttyp hör hemma, och hur den rör sig, kommer tillbaka i varje årtionde efter honom.

Otto von Friesen ställde en annan fråga: kan runstenarna läsas som historia? I sin artikel om Yttergårdsstenarna i Orkesta läste han Ulfs tre gälder i England – från Toste, Torkel och Knut – och ställde dem mot de engelska krönikorna. Han var noga med vad det betydde att göra så: identifieringen var säker så långt det går, skrev han, ”{q('friesen1909')}” ({cite('friesen1909')}).

{pic('u344', ('Runstenen U 344 vid Orkesta kyrka', 'The runestone U 344 at Orkesta church'), 'U 344 vid Orkesta kyrka, en av stenarna där Ulf räknar sina tre gälder i England. Otto von Friesen läste den mot de engelska krönikorna 1909.', 'U 344 at Orkesta church, one of the stones on which Ulf counts his three payments in England. Otto von Friesen read it against the English chronicles in 1909.', 'sv')}

Det decenniet gav oss runstenarna som historiska källor. Allt senare arbete med vikingafärder, med Ingvar och med Knut den stores tid står på den grunden.

## 1910-talet: Färderna, bron och arvet

{pic('friesen', ('Otto von Friesen', 'Otto von Friesen'), 'Otto von Friesen (1870–1942), runolog i Uppsala och den som gav ut Upplands runstenar i början av seklet.', 'Otto von Friesen (1870–1942), runologist at Uppsala, who published the runestones of Uppland at the start of the century.', 'sv')}

År 1914 samlade Montelius alla svenska runstenar han kände till som talar om färder österut. Han citerade von Friesen om Ingvarsstenarna – ”{q('friesen_ingvar')}” ({cite('friesen_ingvar')}) – och han gjorde en iakttagelse som ingen senare generation har kunnat lägga åt sidan. Stenarna kom från en ganska kort tid, och många av dem hade inte överlevt: de hade ”{q('mont1914')}” ({cite('mont1914')}). Frågan om vilka stenar vi inte har, och vad det gör med bilden av dem vi har, står alltså redan här, i en av de första stora sammanställningarna.

Samma år grävde Sune Lindqvist vid brofästena vid Ramsundsberget, där Sigurdsristningen berättar att Sirid gjorde en bro. Han ville veta om bron var en riktig bro, och den var det: ”en verklig bro i modern mening”, över omkring tre meter djupt vatten ({at('1914_203', '205', 'sv')}). Sedan läste han Hillersjöhällens långa arvsberättelse och drog en slutsats som skulle få långt liv: att ”{q('lind1914')}” ({cite('lind1914')}).

Decenniet slutade med en lärd strid. Blyrullen i Alvastra, med en latinsk bön skriven med runor, lästes av von Friesen och kritiserades av Brate, och von Friesen svarade med att datera den genom de stungna runornas utveckling och namnformer ur Legenda aurea ({at('1919_112', '125', 'sv')}). Hur man daterar en runinskrift utan säkra fasta punkter är en fråga som ingen generation efter dem har sluppit.

## 1920-talet: Att läsa eller att tolka

{pic('brate', ('Erik Brate', 'Erik Brate'), 'Erik Brate (1857–1924), språkforskare och utgivare av Östergötlands och Södermanlands runinskrifter.', 'Erik Brate (1857–1924), linguist and editor of the runic inscriptions of Östergötland and Södermanland.', 'sv')}

Pireuslejonet i Venedig bär en vittrad runristning i sina slingor. Den norske arkeologen Haakon Shetelig undersökte originalet i Venedig 1922, och han höll sig medvetet till det han kunde se: ”{q('shet1923')}” ({cite('shet1923')}). Erik Brate, som hade undersökt lejonet 1913, svarade i samma årgång att det inte räckte: ”{q('brate1923')}” ({cite('brate1923')}).

Det är ett av de vackraste meningsutbytena i hela materialet, för båda har rätt om något. Shetelig försvarar det som står på stenen; Brate försvarar att man måste förstå för att kunna se. Samma fråga – vad som kommer först, läsningen eller tolkningen – återkommer nittio år senare i Futhark, som vi ska se i del II.

Samtidigt började man leta efter stenar som hade försvunnit. Bengt Bergman gick på riksantikvariens uppdrag längs Spånga kyrkas putsade väggar 1924, med Peringskiölds anteckningar från 1600-talet i handen, och det lyckades dem att ”{q('bergman1926')}” ({cite('bergman1926')}). De gamla antikvarierna blev en källa till stenar som ingen levande hade sett.

Hugo Jungner läste stenen vid Stora Ek i Västergötland som ett arvsdokument, en sten som tillhör ”{q('jungner1927')}” ({cite('jungner1927')}) – samma tanke som Lindqvist hade prövat på Hillersjö. Och Lindqvist själv, i en lång studie av Jellingemonumenten, gav ett svar på frågan var stenarna stod som fortfarande citeras: ”{q('lind1928')}” ({cite('lind1928')}).

## 1930-talet: Var stod stenen, och syntes runorna?

Bengt Cnattingius frågade 1930 var den mest berömda av dem alla, Rökstenen, ursprungligen hade stått. Han utgick från en allmän regel om runstenarna: ”{q('cnat1930')}” ({cite('cnat1930')}), och sökte med kartor från 1600- och 1700-talen efter den väg och det vattendrag där stenen kunde ha rests.

Det decenniet frågade också hur stenarna hade sett ut. Gustaf Hallström samlade 25 mer eller mindre säkra fall av färg på runstenar och ornerade hällar ({at('1931_171', '271', 'sv')}). Den danske runologen Erik Moltke, som förberedde en ny dansk runutgåva, ville veta hur man dokumenterar en sten utan att idealisera den, och kom fram till att teckningen måste bli ett hjälpmedel: ”{q('moltke1932')}” ({cite('moltke1932')}).

Det var också magins årtionde. Arthur Nordén läste i en serie artiklar flera äldre runristningar som besvärjelser vid gravar. När runskriften kom, skrev han, ”{q('norden1934')}” ({cite('norden1934')}). Läsningarna visar hur nära en tids frågor ligger dess egna strömningar; i del II ser vi hur runologerna själva senare såg tillbaka på mellankrigstidens intresse för magi. Och 1939 skrev en ung Elisabeth Svärdström sin första text i tidskriften, om 1600-talets träsnitt av svenska runstenar. Hennes sista text i vårt material är från {SVARD[2]}.

## 1940-talet: Röd färg, flyttade stenar och fyndet vid Alsike

Den runsten vi ser i dag är ofta en sten som någon har lagat. Karl Alfred Gustawsson redovisade 1941 att Riksantikvarieämbetet arbetat metodiskt sedan 1932: ”{q('gust1941')}” Och: ”{q('gust1941b')}” ({cite('gust1941')}; {cite('gust1941b')}). Den röda färgen på många stenar är alltså inte vikingatidens; den hör till 1930- och 1940-talens runverk, och den är en del av stenarnas historia.

Under samma år kom Sven B. F. Jansson in i tidskriften. Hans första artikel, 1942, redovisade nyfunna stenar, flera av dem framtagna när kyrkor restaurerades – ”{'Då Vallentuna kyrka restaurerades 1937 påträffades en runsten'}” ({at('1942_225', '228', 'sv')}). Han skrev sedan i Fornvännen fram till {JANS[2]}, {JANS[0]} texter i vårt material.

Kyrkorna väckte en tvist som fortfarande pågår i andra former: hur långt hade stenarna flyttats? Lindqvist skrev 1947, med stor respekt för den han motsade: ”{q('lind1947')}” ({cite('lind1947')}). Han trodde i stället att samma familj ofta hade rest två stenar, en hemma och en vid den plats där kyrkan senare byggdes.

Så kom fyndet som visar hur materialet fortfarande växte. ”{q('alsike1')}” Stenen låg under vapenhusmuren med ristningen uppåt och var kilad i fem delar. Sibbe och Ingrid hade rest den efter sina söner, och ristaren hade signerat. Men Jansson behövde knappast signaturen: ”{q('alsike2')}” ({cite('alsike1')}, {cite('alsike2')}).

{pic('alsike', ('Runstenen vid Alsike kyrka', 'The runestone at Alsike church'), 'Runstenen vid Alsike kyrka (U Fv1948;168), funnen under vapenhusmuren den 5 december 1947 och rest igen i maj 1948.', 'The runestone at Alsike church (U Fv1948;168), found under the porch wall on 5 December 1947 and raised again in May 1948.', 'sv')}

## 1950-talet: Var restes runstenarna?

Gunnar Ekholm gav 1950 sin artikel en rubrik som kunde stå över hela den här serien: ”Var restes runstenarna?” Han ifrågasatte von Friesens bild av runstenen som gravvård på gårdens gravfält och pekade i stället på vägar, vadställen, broar och vatten. Om stenarna vid gravfälten skrev han: ”{q('ekholm1')}” Och han var ärlig om underlaget: ”{q('ekholm2')}” ({cite('ekholm1')}).

{pic('wessen', ('Elias Wessén', 'Elias Wessén'), 'Elias Wessén (1889–1981), språkforskare och utgivare av Upplands runinskrifter tillsammans med Sven B. F. Jansson.', 'Elias Wessén (1889–1981), linguist and, with Sven B. F. Jansson, editor of the runic inscriptions of Uppland.', 'sv')}

Två år senare påminde Elias Wessén om att det var 350 år sedan Johannes Bureus påbörjade sina runteckningar. ”{q('wessen1')}” ({cite('wessen1')}) Wessén och Jansson höll på att ge ut Upplands runinskrifter, och Wessén såg vad det betydde för hela fältet: ”{q('wessen2')}” ({cite('wessen2')}). Det är en mening som går att läsa på två sätt. Den beskriver materialets tyngd, och den förklarar varför så mycket av den svenska runforskningen har handlat om Uppland.

Den norske runologen Magnus Olsen ställde 1953 en ovanlig fråga. Åsmund Kåresson skriver sitt namn rätt nio gånger och fel sex gånger. Kunde en del av ristarnas fel förklaras med ordblindhet? Han hoppades att en svensk runforskare skulle ta sig an saken, ”{q('olsen')}” ({cite('olsen')}).

## 1960-talet: Fragment, funtar och Lödöse

Det sista decenniet i den här delen börjar med en varning från arkeologen Wilhelm Holmqvist, i en recension av en avhandling om runstenarnas ornamentik: ”{q('holmq')}” ({cite('holmq')}). Den som vill läsa konstnärliga avsikter i varje asymmetri måste minnas att stenarna höggs i granit, ute, av människor som ibland högg fel.

Arthur Nordén läste 1961 Sparlösastenen och Kälvestenblocket som Sveriges äldsta historiska runinskrifter och såg vikingatågen som affärer: ”{q('norden1961')}” ({cite('norden1961')}). Sven B. F. Jansson visade 1963 hur skaldinnan Euphrosyne 1819 hade byggt en romans på en felläst sten ({at('1963_303', '303', 'sv')}) – ett tidigt exempel på att varje tid läser runstenarna genom sina egna berättelser.

Och Elisabeth Svärdström tog fältet ut ur vikingatiden. Hon läste en dopfunt från Hemsjö och ett måttverktyg från medeltidsstaden Lödöse, och 1967 började hon redovisa de nya fynden varje år under rubriken Runfynd ({at('futhark_12_7_1722787', '20', 'sv')}). Den första redovisningen börjar med en mening som säger mycket om vad materialet är: ”{q('svard1967')}” ({cite('svard1967')}).

## Det som går igen

När vi lägger de sex årtiondena bredvid varandra syns samma frågor om och om igen. Var stod stenarna – vid graven, vid vägen, vid vattnet? Lindqvist 1928, Cnattingius 1930 och Ekholm 1950 svarade var och en utifrån de stenar de kände. Hur gamla är de – och hur daterar man en inskrift utan säkra fasta punkter? Vilka stenar har gått förlorade – Montelius 1914, Bergman 1926, Alsike 1947, Svärdströms fragment i sekundärt läge? Vem ristade – von Friesens och Olsens Åsmund Kåresson, Janssons Öpir? Och vad var en runsten till för – ett minne, en väghållning, ett arvsbrev?

Det är inte en brist som vi pekar på. Det är tvärtom vad som gör en senare generation möjlig. Grundläggarna gav ut stenarna, en efter en, i Sveriges runinskrifter; de lagade och reste dem; de letade upp de förlorade i 1600-talets anteckningar och i kyrkornas murar; och de ställde frågorna så tydligt att de går att pröva. Ekholm skrev själv att litteraturen inte räckte för att avgöra hans fråga. Det var en inbjudan.

I del II följer vi hur nästa generation tog emot den inbjudan: när arkeologerna började räkna, när statistiken fick sin första strid, när Futhark blev en egen tidskrift för runforskningen, och vad som blir synligt först när hundra år läggs bredvid varandra.

:::box Det viktigaste i korthet
- De stora frågorna om runstenarna ställdes tidigt: var de restes, hur gamla de är, vilka som har gått förlorade, vem som ristade dem och vad de var till för. Alla finns i Fornvännen före 1960.
- Grundläggarna gjorde det arbete som allt senare vilar på: utgåvorna, lagningarna, fynden i kyrkmurarna och läsningarna. Den röda färgen på många stenar är deras, inte vikingatidens.
- Deras svar byggde på de stenar de hade framför sig, och de sade det själva. Ekholm 1950: litteraturen räcker inte för att avgöra frågan.
- Redan här finns tvisterna som återkommer: läsning mot tolkning (Shetelig och Brate 1923), gravfältet mot vägen (von Friesen och Ekholm), och hur långt stenarna flyttades (Lindqvist mot von Friesen, Wessén och Jansson).
:::

## Källor

{JOURNALS_SV}

{sources(P1_KEYS, 'sv')}

Siffrorna om de lästa texterna kommer ur Vitkis genomläsning av tidskrifterna (november 2026). Bilderna kommer från Wikimedia Commons, med licens och upphov i bildtexterna."""

body1_en = f"""Whoever stands today before a runestone by a church in Uppland usually reads a sign: a signum, a translation, perhaps a date. Behind every line on that sign stands a person who once stood on the same spot, with a notebook, a camera or a magnesium flare, trying to understand what they saw. This series is about them.

Vitki is built on their work. Every reading we count on, every signum and nearly every date goes back to someone who read a stone, published it and argued about it with colleagues – often in the journal Fornvännen. We wanted to know which questions they asked, in what order, and which questions keep coming back. The simplest way to find out was to read.

## How we read

We have read Fornvännen from its first volume in 1906 to 2022, and Futhark, the international journal of runic studies, from its first volume in 2010. That came to {en_n(N)} texts: {TIER['run']} on runes and runestones, {TIER['grann']} from neighbouring fields – archaeology, place-names, history, art history and coins – on the Viking Age and early Middle Ages, and {TIER['nara']} other Fornvännen texts that touch on the period. {CLAUDE_EN} {CHECK_EN} Both journals are freely available online, and every quotation below links to its page.

This first part runs to 1969. The second begins in 1970, roughly when scholars began to count.

{chart_texts('en')}

In the early years the texts are few, because Fornvännen was a slim journal and runes were a small part of it. From 2010 the bar grows, because Futhark arrives. But even the early volumes ask nearly all the questions this series is about.

## 1906–1909: A new journal and an old question

Fornvännen was born in 1906 out of two older journals. The archaeologist Oscar Almgren proposed merging them, and the Academy of Letters agreed in January that year. It was a time when one man still stood at the centre. Evert Baudou, who wrote the journal's birth story a hundred years later, puts it like this: “{q('baudou')}” (“Nearly all Swedish archaeologists see themselves as disciples of Montelius, although he never gave any regular teaching”; {cite('baudou', 'en')}).

{pic('montelius', ('Oscar Montelius', 'Oscar Montelius'), '', 'Oscar Montelius (1843–1921), the archaeologist whom nearly every Swedish archaeologist around 1900 counted as a teacher.', 'en')}

Montelius himself wrote in the first volume about a gold bracteate from Vadstena and a newly found bracteate struck with the same die. He counted the runes in its futhark and noted “{q('mont1906')}” (“that the rune-row thus consists of 3 times 8 runes”; {cite('mont1906', 'en')}). It is a small observation, but it is a count, and it is right.

The following year the linguist Erik Brate wrote about the runic inscriptions on the Isle of Man. His question was where the script came from, and his answer was that the more archaic runes of the Rök group “{q('brate1907')}” (“prove, of course, that this type of script is at home in Sweden”) and spread west from there ({cite('brate1907', 'en')}). The question of where a script belongs, and how it travels, returns in every decade after him.

Otto von Friesen asked a different question: can runestones be read as history? In his article on the Yttergården stones at Orkesta he read Ulf's three payments in England – from Tosti, Thorkell and Knut – and set them against the English chronicles. He was careful about what that meant: the identification was as certain as it could be, he wrote, “{q('friesen1909')}” (“when one has to confront two sources of such different kinds as the statements of English annalists and of Swedish Vikings”; {cite('friesen1909', 'en')}).

{pic('u344', ('Runestone U 344 at Orkesta church', 'The runestone U 344 at Orkesta church'), '', 'U 344 at Orkesta church, one of the stones on which Ulf counts his three payments in England. Otto von Friesen read it against the English chronicles in 1909.', 'en')}

That decade gave us runestones as historical sources. All later work on Viking voyages, on Ingvar and on the age of Knut the Great stands on that ground.

## The 1910s: The voyages, the bridge and the inheritance

{pic('friesen', ('Otto von Friesen', 'Otto von Friesen'), '', 'Otto von Friesen (1870–1942), runologist at Uppsala, who published the runestones of Uppland at the start of the century.', 'en')}

In 1914 Montelius gathered the Swedish runestones he knew that speak of voyages to the east. He quoted von Friesen on the Ingvar stones – “{q('friesen_ingvar')}” (“None suggests that the main person returned”; {cite('friesen_ingvar', 'en')}) – and he made an observation that no later generation has been able to set aside. The stones came from a rather short period, and many had not survived: they had “{q('mont1914')}” (“not been preserved to our day, but been lost or may still lie unknown in the ground or in some church wall”; {cite('mont1914', 'en')}). The question of which stones we do not have, and what that does to our picture of the ones we have, stands here already, in one of the first great compilations.

That same year Sune Lindqvist dug at the bridge abutments by Ramsundsberget, where the Sigurd carving says that Sigrid made a bridge. He wanted to know whether the bridge was a real bridge, and it was: “a real bridge in the modern sense”, over water about three metres deep ({at('1914_203', '205', 'en')}). Then he read the long inheritance story on the Hillersjö rock and drew a conclusion that would have a long life: that “{q('lind1914')}” (“rune-inscribed stones at times served as documents supporting a named party's ownership of certain property”; {cite('lind1914', 'en')}).

The decade ended with a learned dispute. The lead roll from Alvastra, with a Latin prayer written in runes, was read by von Friesen and criticised by Brate, and von Friesen replied by dating it through the development of the dotted runes and name forms from the Legenda aurea ({at('1919_112', '125', 'en')}). How to date a runic inscription without secure fixed points is a question no generation after them has escaped.

## The 1920s: Reading or interpreting

{pic('brate', ('Erik Brate', 'Erik Brate'), '', 'Erik Brate (1857–1924), linguist and editor of the runic inscriptions of Östergötland and Södermanland.', 'en')}

The Piraeus lion in Venice carries a weathered runic inscription in its loops. The Norwegian archaeologist Haakon Shetelig examined the original in 1922, and he deliberately kept to what he could see: “{q('shet1923')}” (“The interpretation is not my business anyway; I have only tried to give an exact and critical account of what I can now read”; {cite('shet1923', 'en')}). Erik Brate, who had examined the lion in 1913, replied in the same volume that this was not enough: “{q('brate1923')}” (“To me this seems not enough; the interpretation must go hand in hand with the reading”; {cite('brate1923', 'en')}).

It is one of the finest exchanges in the whole material, because both are right about something. Shetelig defends what is on the stone; Brate defends the need to understand in order to see. The same question – which comes first, reading or interpretation – returns ninety years later in Futhark, as we will see in part II.

At the same time people began to look for stones that had vanished. In 1924 Bengt Bergman, commissioned by the National Antiquary, walked the plastered walls of Spånga church with Peringskiöld's seventeenth-century notes in hand, and they managed to “{q('bergman1926')}” (“find again the runestone on the outer wall that Peringskiöld mentions”; {cite('bergman1926', 'en')}). The old antiquaries became a source of stones that no living person had seen.

Hugo Jungner read the stone at Stora Ek in Västergötland as a document of inheritance, a stone belonging to “{q('jungner1927')}” (“the group of runic documents whose purpose was to establish an inheritance for contemporaries and posterity”; {cite('jungner1927', 'en')}) – the same thought Lindqvist had tried at Hillersjö. And Lindqvist himself, in a long study of the Jelling monuments, gave an answer to the question of where stones stood that is still quoted: “{q('lind1928')}” (“The runestones were placed so that they could easily be read by passers-by; they were independent monuments beside the mounds, not ornaments on top of them”; {cite('lind1928', 'en')}).

## The 1930s: Where did the stone stand, and could the runes be seen?

In 1930 Bengt Cnattingius asked where the most famous stone of all, the Rök stone, had originally stood. He started from a general rule about runestones: “{q('cnat1930')}” (“that they were raised at or near settlement and most often by a road”; {cite('cnat1930', 'en')}), and searched maps from the 1600s and 1700s for the road and stream where it might have been raised.

That decade also asked what the stones had looked like. Gustaf Hallström collected 25 more or less certain cases of paint on runestones and decorated slabs ({at('1931_171', '271', 'en')}). The Danish runologist Erik Moltke, preparing a new Danish corpus edition, wanted to know how to document a stone without idealising it, and concluded that drawing must become an aid: “{q('moltke1932')}” (“only the photograph is able to provide a reliable basis”; {cite('moltke1932', 'en')}).

It was also the decade of magic. In a series of articles Arthur Nordén read several older runic inscriptions as spells at graves. When runic writing arrived, he wrote, “{q('norden1934')}” (“it was quickly taken into use as a particularly welcome means of conjuring precisely against the revenants of the graves”; {cite('norden1934', 'en')}). The readings show how close an age's questions lie to its own currents; in part II we see how runologists later looked back on the inter-war interest in magic. And in 1939 a young Elisabeth Svärdström wrote her first text in the journal, on seventeenth-century woodcuts of Swedish runestones. Her last text in our material is from {SVARD[2]}.

## The 1940s: Red paint, moved stones and the find at Alsike

The runestone we see today is often a stone someone has mended. In 1941 Karl Alfred Gustawsson reported that the National Heritage Board had worked methodically since 1932: “{q('gust1941')}” (“Since 1932, 311 runestones have been repaired or raised.”) And: “{q('gust1941b')}” (“In connection with the runological examination, painting with a red colour developed for the purpose has generally taken place”; {cite('gust1941', 'en')}; {cite('gust1941b', 'en')}). The red paint on many stones is thus not the Viking Age's; it belongs to the corpus work of the 1930s and 1940s, and it is part of the stones' history.

In those years Sven B. F. Jansson entered the journal. His first article, in 1942, reported newly found stones, several of them uncovered when churches were restored – “Då Vallentuna kyrka restaurerades 1937 påträffades en runsten” (“When Vallentuna church was restored in 1937 a runestone was found”; {at('1942_225', 228, 'en')}). He went on writing in Fornvännen until {JANS[2]}, {JANS[0]} texts in our material.

The churches raised a dispute that still goes on in other forms: how far had the stones been moved? Lindqvist wrote in 1947, with great respect for the man he contradicted: “{q('lind1947')}” (“Owing to Otto von Friesen's authority, well founded in so many other questions, the view has also taken root that, above all in Uppland, people building churches not seldom took the trouble to drag runestones there that had previously stood very far from the church sites”; {cite('lind1947', 'en')}). He believed instead that the same family had often raised two stones, one at home and one where the church was later built.

Then came the find that shows how the material was still growing. “{q('alsike1')}” (“During restoration work at Alsike church a runestone was found on 5 December 1947.”) It lay under the porch wall with the inscribed face upwards and had been split into five pieces. Sibbe and Ingrid had raised it for their sons, and the carver had signed. But Jansson hardly needed the signature: “{q('alsike2')}” (“The runestone is a typical Öpir stone”; {cite('alsike1', 'en')}, {cite('alsike2', 'en')}).

{pic('alsike', ('Runestone at Alsike church', 'The runestone at Alsike church'), '', 'The runestone at Alsike church (U Fv1948;168), found under the porch wall on 5 December 1947 and raised again in May 1948.', 'en')}

## The 1950s: Where were the runestones raised?

In 1950 Gunnar Ekholm gave his article a title that could stand over this whole series: “Var restes runstenarna?” – Where were the runestones raised? He questioned von Friesen's picture of the runestone as a grave monument on the farm's cemetery and pointed instead to roads, fords, bridges and water. Of the stones at cemeteries he wrote: “{q('ekholm1')}” (“But it seems as if the relative size of this group of runestones has been greatly overestimated.”) And he was honest about the evidence: “{q('ekholm2')}” (“To reach full clarity on the debated question of the runestones' original placing, the literature now available is unfortunately not sufficient”; {cite('ekholm1', 'en')}).

{pic('wessen', ('Elias Wessén', 'Elias Wessén'), '', 'Elias Wessén (1889–1981), linguist and, with Sven B. F. Jansson, editor of the runic inscriptions of Uppland.', 'en')}

Two years later Elias Wessén marked 350 years since Johannes Bureus began his drawings of runic monuments. “{q('wessen1')}” (“In all, Bureus knew no fewer than 600 inscriptions, most of them from Uppland”; {cite('wessen1', 'en')}.) Wessén and Jansson were publishing the runic inscriptions of Uppland, and Wessén saw what that meant for the whole field: “{q('wessen2')}” (“But that is the remarkable thing: where runestones are concerned, Uppland means half of Sweden”; {cite('wessen2', 'en')}). The sentence can be read two ways. It describes the weight of the material, and it explains why so much Swedish runic research has been about Uppland.

In 1953 the Norwegian runologist Magnus Olsen asked an unusual question. Åsmund Kåresson writes his name correctly nine times and wrongly six times. Could some carvers' errors be explained by dyslexia? He hoped a Swedish runologist would take the matter up, “{q('olsen')}” (“preferably, perhaps, in collaboration with a neurologist”; {cite('olsen', 'en')}).

## The 1960s: Fragments, fonts and Lödöse

The last decade of this part opens with a warning from the archaeologist Wilhelm Holmqvist, in a review of a dissertation on the ornament of runestones: “{q('holmq')}” (“Runestones are a coarse material, and the carving surface is often only summarily dressed”; {cite('holmq', 'en')}). Whoever wants to read artistic intent into every asymmetry must remember that the stones were cut in granite, outdoors, by people who sometimes cut wrong.

In 1961 Arthur Nordén read the Sparlösa stone and the Kälvesten block as Sweden's oldest historical runic inscriptions and saw the Viking expeditions as ventures: “{q('norden1961')}” (“The Viking expeditions were large joint enterprises set going by entrepreneurs with a well-founded reputation for victory”; {cite('norden1961', 'en')}). In 1963 Sven B. F. Jansson showed how the poet Euphrosyne had built a romance in 1819 on a misread stone ({at('1963_303', '303', 'en')}) – an early example of how every age reads the runestones through its own stories.

And Elisabeth Svärdström took the field out of the Viking Age. She read a baptismal font from Hemsjö and a measuring tool from the medieval town of Lödöse, and in 1967 she began reporting the new finds every year under the heading Runfynd ({at('futhark_12_7_1722787', '20', 'en')}). The first report opens with a sentence that says much about what the material is: “{q('svard1967')}” (“The runestones newly discovered and examined in 1966 are all fragments, found in secondary positions”; {cite('svard1967', 'en')}).

## What recurs

When we lay the six decades side by side, the same questions appear again and again. Where did the stones stand – by the grave, by the road, by the water? Lindqvist in 1928, Cnattingius in 1930 and Ekholm in 1950 each answered from the stones they knew. How old are they – and how does one date an inscription without secure fixed points? Which stones have been lost – Montelius in 1914, Bergman in 1926, Alsike in 1947, Svärdström's fragments in secondary positions? Who carved them – von Friesen's and Olsen's Åsmund Kåresson, Jansson's Öpir? And what was a runestone for – a memorial, a road work, a deed of inheritance?

This is not a shortcoming we are pointing at. On the contrary, it is what makes a later generation possible. The founders published the stones one by one in Sveriges runinskrifter; they mended and raised them; they tracked down the lost ones in seventeenth-century notes and in church walls; and they asked their questions so clearly that they can be tested. Ekholm himself wrote that the literature was not enough to settle his question. That was an invitation.

In part II we follow how the next generation took up that invitation: when archaeologists began to count, when statistics had its first quarrel, when Futhark became a journal of its own for runic studies, and what becomes visible only when a hundred years are laid side by side.

:::box The essentials in brief
- The great questions about runestones were asked early: where they were raised, how old they are, which have been lost, who carved them and what they were for. All of them are in Fornvännen before 1960.
- The founders did the work everything later rests on: the editions, the repairs, the finds in church walls and the readings. The red paint on many stones is theirs, not the Viking Age's.
- Their answers were built on the stones in front of them, and they said so themselves. Ekholm in 1950: the literature is not enough to settle the question.
- The disputes that recur are already here: reading against interpretation (Shetelig and Brate, 1923), the cemetery against the road (von Friesen and Ekholm), and how far the stones were moved (Lindqvist against von Friesen, Wessén and Jansson).
:::

## Sources

{JOURNALS_EN}

{sources(P1_KEYS, 'en')}

The figures on the texts read come from Vitki's reading of the journals (November 2026). The images come from Wikimedia Commons, with licence and creator in the captions. Translations of quotations are ours."""


# ======================================================================================================================
# 6. Del II: När forskarna började räkna, 1970–2025
# ======================================================================================================================
P2_KEYS = ["1970_247", "1972_016", "1978_075", "1980_183", "1986_098", "1992_043", "1994_233", "1996_143", "1997_193",
           "1999_193", "1999_196", "2001_023", "2008_245", "2008_litt_d", "futhark_1_7_381131", "futhark_1_27_381123",
           "futhark_1_123_381124", "futhark_1_249_381135", "futhark_2_145_512979", "futhark_2_242_512988",
           "futhark_4_7_682689", "futhark_4_61_682691", "futhark_4_77_682692", "futhark_4_129_682695",
           "futhark_5_137_799768", "futhark_8_7_1333693", "futhark_9-10_7_1383036", "37d3b87e-51fd-4a87-af76-294ffc35901a",
           "futhark_12_7_1722787", "1923_222", "1950_137", "1952_193"]

title2 = "Hundra år av runfrågor II: När forskarna började räkna"
title2_en = "A Hundred Years of Runic Questions II: When the Scholars Began to Count"
summary2 = ("Från 1970 till i dag: väringen i Hagia Sofia, ristarnas händer, den första statistiska striden om runstenarna, "
            "Futhark som egen tidskrift och Rökstenen läst på nytt. Andra delen följer Svärdström, Larsson, Gräslund, Palm, "
            "Sawyer, Källström, Williams, Zilmer, Jesch, Klos och många fler – och slutar med det som syns först när hundra år "
            "läggs bredvid varandra, och med våra egna gränser.")
summary2_en = ("From 1970 to today: the Varangian in Hagia Sophia, the carvers' hands, the first statistical quarrel about "
               "runestones, Futhark as a journal of its own and the Rök stone read anew. The second part follows Svärdström, "
               "Larsson, Gräslund, Palm, Sawyer, Källström, Williams, Zilmer, Jesch, Klos and many more – and ends with what "
               "becomes visible only when a hundred years are laid side by side, and with our own limits.")

body2 = f"""I [första delen](/artiklar/hundra-ar-av-runfragor-grundlaggarna) följde vi grundläggarna från 1906 till 1969: de som gav ut stenarna, lagade dem, letade upp de förlorade och ställde frågorna. Den här delen börjar 1970. Mycket är sig likt – nya fynd redovisas varje år, och samma frågor om var stenarna stod och hur gamla de är kommer tillbaka – men något nytt händer också. Forskarna börjar räkna, och de börjar gräla om hur man räknar.

Underlaget är detsamma som i del I: {sv_n(N)} texter ur Fornvännen och Futhark, och hur vi läste dem står i slutet, under Våra egna gränser. Från 1970 till 2025 är det {sv_n(N - P1_TEXTS)} av dem.

## 1970-talet: Väringen i Hagia Sofia och ristarnas händer

Elisabeth Svärdström öppnade decenniet med en ristning långt hemifrån: runor i en marmorbalustrad på södra läktaren i Hagia Sofia i Konstantinopel, där hon läste namnet Halvdan. Hon föreslog att ristningen var medeltida, från slutet av 1000-talet eller senare, och slutade med en mening som gäller hela runforskningen: ”{q('svard1970')}” ({cite('svard1970')}).

{pic('hagia', ('Runristningen i Hagia Sofia', 'The runic inscription in Hagia Sophia'), 'Runristningen på läktaren i Hagia Sofia, Istanbul, som Elisabeth Svärdström läste i Fornvännen 1970.', 'The runic inscription in the gallery of Hagia Sophia, Istanbul, which Elisabeth Svärdström read in Fornvännen in 1970.', 'sv')}

Svärdström läste också medeltidsstadens vardag: runpinnar, karvstickor och redskap från Lödöse, där runorna användes av människor som inte alltid kunde dem. Om en av ristarna skrev hon att han förmodligen ”{'inte har varit runkunnig i vanlig bemärkelse'}” ({at('1972_094', '102', 'sv')}). Runfynd fortsatte att komma ut varje år, med Helmer Gustavson, Thorgunn Snædal, Jan Paul Strid och Marit Åhlén som medförfattare ({cite('kallstrom2021a')}).

Ristarna själva blev en fråga. Runologen Claiborne W. Thompson prövade von Friesens tes att Öpir hade varit Visätes lärjunge. Han kallade den ”{q('thompson1')}” – men konstaterade: ”{q('thompson2')}” ({cite('thompson1')}). Det är ett mönster för hur fältet för samtalet vidare: med respekt för den äldre forskaren, och med stenarna som domare.

Mot slutet av decenniet frågade arkeologen Klas-Göran Selinge hur mycket fornminnesregistret egentligen visar. ”{q('selinge')}”, skrev han om de kända gravfynden ({cite('selinge')}). Frågan om vad som har bevarats och registrerats – och vad det gör med alla jämförelser – är samma fråga som Montelius ställde 1914, nu med ett helt register att ställa den till.

{pic('janssonmalar', ('Sven B. F. Jansson målar runor', 'Sven B. F. Jansson painting runes'), 'Sven B. F. Jansson, ”Run-Janne”, målar i runorna på en häll omkring 1980. Han var riksantikvarie 1966–1972 och skrev i Fornvännen från 1942.', 'Sven B. F. Jansson, “Run-Janne”, painting in the runes on a slab around 1980. He was National Antiquary 1966–1972 and wrote in Fornvännen from 1942.', 'sv')}

## 1980-talet: Den första räkningen

År 1980 publicerade en ung Magnus Källström en artikel om den försvunna runstenen vid Veddesta i Järfälla, känd bara genom Olof Celsius avskrift från 1728 ({at('1980_183', '183–186', 'sv')}). Han jämförde ristarens stavning med andra stenar och visade att en äldre tillskrivning inte höll. Det är början på ett författarskap som går genom hela resten av materialet: {KALL[0]} texter i Fornvännen och Futhark mellan {KALL[1]} och {KALL[2]}.

Arkeologen Mats G. Larsson ställde 1983 frågan vart Ingvar den vittfarne egentligen for, och 1986 gick han igenom Ingvarsstenarnas platser: gravfält, storhögar, tingsplatser och fynd. Han prövade också med ett statistiskt test (χ²) om stenarna var jämnt spridda över Södermanlands härader. Slutsatsen formulerade han försiktigt: ”{q('larsson1986')}” ({cite('larsson1986')}). Det är, i Fornvännen, det tydligaste tidiga exemplet på en ny sorts fråga: inte vad en sten säger, utan hur en grupp stenar fördelar sig.

## 1990-talet: Statistikens första strid

Larsson disputerade 1990 med en avhandling om utlandsfararstenarna och deras gårdar, där han jämförde dem med en lika stor grupp andra runstenar. Opponenten Per H. Ramqvist recenserade den i Fornvännen 1991, och Larsson svarade 1992 ({at('1992_043', '43', 'sv')}). Samma år disputerade Rune Palm i Uppsala med *Runor och regionalitet*, en studie av variationen i hela det nordiska materialet av minnesinskrifter ({at('1994_233', '236', 'sv')}).

Sedan kom striden. År 1997 skrev Stina Orsenmark ett inlägg med rubriken ”Matematisk eller kulturhistorisk analys?”. Hon byggde på Birgit Sawyers arbeten om arv och egendom: ”{q('orsen1')}” ({cite('orsen1')}). Och hon var tydlig med var hon stod: ”{q('orsen2')}” ({cite('orsen2')}).

Två år senare kom två svar i samma årgång. Frands Herschend räknade om Larssons storgårdar och fann att de som kom hem och de som dog skiljer sig åt i vilken sorts jord gårdarna hade: ”{q('hersch1999')}” ({cite('hersch1999')}). Och Larsson svarade båda med en generositet som är ovanlig i en debatt: ”{q('larsson1999')}” ({cite('larsson1999')}).

Det är en av de bästa stunderna i hela materialet. Tre forskare grälar om statistik, och resultatet är att frågan blir bättre. Orsenmarks invändning om hur man väljer sina jämförelser, Herschends nya uppdelning och Larssons öppenhet för den är tillsammans en liten lärobok i hur man räknar på runstenar.

Under samma år blev en annan metod central. Anne-Sofie Gräslund hade delat in runstenarnas ornamentik i stilgrupper, och Larsson använde dem 1996 för att datera Jarlabankes stenar. Han skrev: ”{q('larsson1996')}” ({cite('larsson1996')}). Nästan allt senare arbete med runstenarnas tidsordning, också Vitkis, bygger på Gräslunds stilgrupper.

## 2000-talet: Vers, namn och tingsplatser

Herschend fortsatte att räkna, nu på versen. Med Gräslunds stilgrupper som tidsskala följde han hur de poetiska dragen förändrades i Mälardalens runtexter; ”{q('hersch2001')}”, skrev han ({cite('hersch2001')}). Alexandra Sanmark och Sarah Semple skrev 2008 om tingsplatser i Sverige och England ({at('2008_245', '245–259', 'sv')}), och därmed fick frågan om var stenarna stod ett nytt sammanhang: samlingsplatserna.

Det decenniet fick också ett av de verktyg som hela fältet använder varje dag. Lena Peterson gav 2007 ut den femte, reviderade upplagan av *Nordiskt runnamnslexikon*. Rikke Steenholt Olesen skrev i sin recension: ”{q('olesen2008')}” ({cite('olesen2008')}). Varje gång Vitki räknar personnamn står vi på det lexikonet.

## 2010-talet: Futhark – en egen tidskrift

År 2010 kom första volymen av Futhark: International Journal of Runic Studies. För första gången hade runforskningen en egen internationell tidskrift, och den första volymen läses som ett program.

Michael Barnes skrev om utgåvorna och ställde ett krav: ”{q('barnes2010')}” ({cite('barnes2010')}). Henrik Williams frågade hur ofta runristarna egentligen felristade, och svarade att de vikingatida stenarna inte var slarvigt gjorda: ”{q('williams2010')}” ({cite('williams2010')}). Kristel Zilmer läste uttryck som ”denna sten” och ”här” på färdestenarna och varnade för att dra slutsatser för fort: ”{q('zilmer2010')}” ({cite('zilmer2010')}).

I samma volym recenserade Mats G. Larsson Lydia Klos stora avhandling *Runensteine in Schweden* (2009), som går igenom placeringen för de runstenar i hela Sverige som kan antas stå kvar där de restes. Larsson var kritisk på flera punkter, men han började med det viktigaste: ”{q('larsson2010')}” ({cite('larsson2010')}). I Futhark 2 recenserade Magnus Källström arkeologen Selinges bok om runstenar och gränser, där Selinge hade gått igenom omkring 220 stenar: ”{q('kallstrom2011')}” ({cite('kallstrom2011')}).

År 2013 kom Futhark 4, med plenarföredragen från runsymposiet i Oslo 2010. Barnes frågade vad runologi är, och hans svar knyter an till 1923 års meningsutbyte mellan Shetelig och Brate: ”{q('barnes2013a')}” ({cite('barnes2013a')}). Han såg också tillbaka på grundläggarnas tid och, med en kollegas ord, på ”{q('barnes2013c')}” ({cite('barnes2013c')}). Och han sade något som hela den här serien bekräftar: ”{q('barnes2013b')}” ({cite('barnes2013b')}).

Henrik Williams föreslog i samma volym en social runologi, där man frågar vilka stenar som var påkostade och vilka som var enkla, och konstaterade: ”{q('williams2013')}” ({cite('williams2013')}). Judith Jesch gick igenom orden *bóndi* och *þegn* på över tvåhundra stenar och ställde en fråga som låter enkel men som kräver hela materialet för att besvaras: ”{q('jesch2013')}” ({cite('jesch2013')}). Kristel Zilmer räknade de kristna bönerna och fann att ”{q('zilmer2013')}” ({cite('zilmer2013')}) – Uppland och Södermanland.

Laila Kitzler Åhfeldt hade redan 2011 använt 3D-skanning och huggspårsanalys för att jämföra runstenar och tidigkristna gravmonument i Västergötland: ”{q('kitzler2011')}” ({cite('kitzler2011')}). Vitkis egen huggspårsanalys står i den traditionen. Per Stille gick igenom alla 82 kända runstenar i Tiohärad i Småland och fann att bara femton av dem med känt läge har någon koppling till gravfält: ”{q('stille2014')}” ({cite('stille2014')}). Och Hanna Åkerström, som inventerade det tidigvikingatida runmaterialet, var ärlig om gränsen för varje sådan inventering: ”{q('akerstrom2017')}” ({cite('akerstrom2017')}).

## 2020-talet: Rök på nytt, Ingvar på nytt

Rökstenen, som Cnattingius 1930 ville placera i landskapet, lästes på nytt av fyra forskare från tre ämnen – Per Holmberg, Bo Gräslund, Olof Sundqvist och Henrik Williams – som en text om solen, Oden och världens undergång ({at('futhark_9-10_7_1383036', '7–38', 'sv')}). Att en ny läsning av Sveriges mest kända runsten kom från språkvetenskap, arkeologi och religionshistoria tillsammans säger något om vart fältet har gått.

{pic('rok', ('Rökstenen', 'The Rök stone'), 'Rökstenen (Ög 136) i Östergötland. Cnattingius frågade 1930 var den hade stått; 2020 lästes den på nytt av en språkvetare, en arkeolog, en religionshistoriker och en runolog tillsammans.', 'The Rök stone (Ög 136) in Östergötland. Cnattingius asked in 1930 where it had stood; in 2020 it was read anew by a linguist, an archaeologist, a historian of religion and a runologist together.', 'sv')}

Annett Krakow granskade 2021 den fasta punkt som Ingvarsstenarna har daterats efter, den isländska sagans uppgift om Ingvars död: ”{q('krakow2021')}” ({cite('krakow2021')}). Och Magnus Källström skrev Futharks översikt över de svenska korpusutgåvorna. Han konstaterade att utgåvorna sällan diskuterar dateringen av de sena vikingatida stenarna – ”{q('kallstrom2021b')}” ({cite('kallstrom2021b')}) – och att den årliga redovisningen av nya fynd, som Svärdström började 1967, inte längre finns: ”{q('kallstrom2021a')}” ({cite('kallstrom2021a')}).

## Vad som syns när allt ligger bredvid varandra

När vi hade sorterat de {sv_n(N)} texterna och kontrollerat det vi använder, framträdde 28 frågor som går igen. Det är vår sortering, inte författarnas egna rubriker, och den mäter hur ofta en fråga berörs, inte vem som hade rätt. Men mönstret är tydligt: {ALL13} av de 28 finns i alla tretton årtionden, från 1906 till i dag, och inget årtionde saknar mer än fyra av dem.

{chart_themes_per_decade('sv')}

Diagrammet säger inte att forskningen har stått still. Det säger att de stora frågorna är stora. Var restes stenarna, och varför just där? Hur gamla är de? Vilka har gått förlorade, och vilka står inte där de restes? Vad säger gravhällarna, mynten och silvret, kvinnorna och barnen, stenen själv?

{chart_themes('sv')}

Frågan om var stenarna stod berörs i nästan två texter av tre, och frågan om hur gamla de är i mer än hälften. Det som blir synligt först när allt ligger bredvid varandra är hur dessa två frågor oftast har besvarats: med exempel. Lindqvist 1928, Cnattingius 1930 och Ekholm 1950 utgick från de stenar de kände, och Ekholm sade själv att litteraturen inte räckte. Det är inte en svaghet hos dem. En enskild forskare med en enskild bygd kan inte göra annat, och deras exempel är just det som gör frågorna prövbara.

Det finns viktiga undantag, och de ska nämnas med namn: Larssons utlandsfararstenar 1990, Palms regionala variation 1992, Klos genomgång av placeringen 2009, Stilles Tiohärad och Selinges gränsstenar. De visar att frågorna går att ta till hela material – och samtalet om dem, från Orsenmarks invändning till Larssons svar, visar hur mycket som hänger på hur man gör det. Williams skrev 2013 att ingen ännu på allvar hade prövat om runstenarnas utförande hänger ihop med sociala faktorer, och Barnes att det som fattas är data, inte teori. Det är två av fältets egna röster som säger samma sak som hundra år av frågor säger.

Ingen enskild forskare kunde se det här, för ingen läste alla årgångarna på en gång. Det behövdes inte heller: varje generation svarade på sin tids frågor, med sin tids material. Vi har bara haft förmånen att läsa dem efter varandra.

## De stora sammanställningarna vi står på

Vitki är inte det första försöket att se på hela materialet, och mycket av det vi gör vore omöjligt utan dem som kom före. Några ska nämnas särskilt:

- **Sveriges runinskrifter** (från 1900) och dess utgivare, från Brate, von Friesen, Wessén och Jansson till Svärdström och deras efterföljare: grunden för varje läsning.
- **Samnordisk runtextdatabas** vid Uppsala universitet, som gjorde hela det nordiska materialet sökbart och som Vitki räknar på varje dag.
- **Mats G. Larsson**, *Runstenar och utlandsfärder* (1990): ett av de första försöken att jämföra en grupp runstenar med andra stenar med statistiska metoder.
- **Rune Palm**, *Runor och regionalitet* (1992): variationen i de nordiska minnesinskrifterna, landskap för landskap.
- **Birgit Sawyer**, från *Property and Inheritance in Viking Scandinavia* (1988) till *The Viking-Age Rune-Stones* (2000): runstenarna som vittnesbörd om arv och egendom, räknade över hela Skandinavien.
- **Anne-Sofie Gräslund**s stilgrupper: den tidsskala som nästan alla senare dateringar av runstenar använder.
- **Lena Peterson**s *Nordiskt runnamnslexikon* och *Svenskt runordsregister*: namnen och orden, samlade.
- **Lydia Klos**, *Runensteine in Schweden* (2009): placeringen genomgången för de stenar i hela Sverige som kan antas stå kvar där de restes.
- **Laila Kitzler Åhfeldt**s huggspårsanalys och **Magnus Källström**s arbeten om ristarna och deras signaturer.

## Våra egna gränser

Vi har läst två tidskrifter, inte hela runforskningen. Böcker, avhandlingar och andra tidskrifter – där mycket av det viktigaste står, bland annat flera av verken ovan – har vi inte läst på samma sätt. Av Fornvännen lämnade vi omkring 2 000 texter olästa, de som handlar om stenålder, bronsålder och senare konsthistoria utan koppling till perioden. {CLAUDE_SV} Det var sorteringssteget, och det hittade de återkommande frågorna i {sv_n(N)} texter. {CHECK_SV} De 28 frågorna är vår sortering; en annan läsare hade kanske dragit gränserna annorlunda.

Läsningen gav oss också frågor som vi vill pröva i kommande studier, bland annat om var stenarna restes, hur gamla de är och vilka som har gått förlorade. När vi gör det kommer vi att redovisa hur, och vi kommer att börja i de texter som har citerats här.

:::box Det viktigaste i korthet
- Från 1970 börjar forskarna räkna, och de börjar gräla om hur man räknar. Striden mellan Larsson, Orsenmark och Herschend 1997–1999 är en liten lärobok i hur man gör det väl.
- Futhark gav 2010 runforskningen en egen tidskrift, och dess första volymer ställer samma frågor som grundläggarna – om läsning och tolkning, om stenarnas sociala sida, om vad som fattas.
- {ALL13} av de 28 frågor som går igen finns i alla tretton årtionden. Det betyder inte att forskningen stått still, utan att frågorna om var stenarna restes och hur gamla de är är stora – och att de oftast har besvarats med exempel, bygd för bygd.
- Allt Vitki gör vilar på deras arbete: utgåvorna, databasen, lexikonen, stilgrupperna och de stora sammanställningarna från Larsson, Palm, Sawyer, Gräslund, Peterson, Klos och Källström.
:::

## Källor

{JOURNALS_SV}

{sources(P2_KEYS + ['1972_094'], 'sv')}

Övriga verk som nämns: Rune Palm, *Runor och regionalitet* (Runrön 7, Uppsala 1992); Birgit Sawyer, *Property and Inheritance in Viking Scandinavia* (Alingsås 1988) och *The Viking-Age Rune-Stones* (Oxford 2000); Lydia Klos, *Runensteine in Schweden* (Berlin 2009); Lena Peterson, *Nordiskt runnamnslexikon* (5:e uppl., Uppsala 2007). Siffrorna om de lästa texterna och de återkommande frågorna kommer ur Vitkis genomläsning av tidskrifterna (november 2026). Bilderna kommer från Wikimedia Commons, med licens och upphov i bildtexterna."""

body2_en = f"""In [the first part](/en/artiklar/hundra-ar-av-runfragor-grundlaggarna) we followed the founders from 1906 to 1969: those who published the stones, mended them, tracked down the lost ones and asked the questions. This part begins in 1970. Much stays the same – new finds are reported every year, and the same questions about where the stones stood and how old they are keep returning – but something new happens too. Scholars begin to count, and they begin to argue about how to count.

The material is the same as in part I: {en_n(N)} texts from Fornvännen and Futhark, and how we read them is described at the end, under Our own limits. From 1970 to 2025 there are {en_n(N - P1_TEXTS)} of them.

## The 1970s: The Varangian in Hagia Sophia and the carvers' hands

Elisabeth Svärdström opened the decade with an inscription far from home: runes on a marble balustrade in the south gallery of Hagia Sophia in Constantinople, where she read the name Halvdan. She proposed that the carving was medieval, from the late eleventh century or later, and ended with a sentence that holds for the whole of runic research: “{q('svard1970')}” (“However that may be, there stands in contemporary writing on stone the name of a Northman in exile”; {cite('svard1970', 'en')}).

{pic('hagia', ('Runic inscription in Hagia Sophia', 'The runic inscription in Hagia Sophia'), '', 'The runic inscription in the gallery of Hagia Sophia, Istanbul, which Elisabeth Svärdström read in Fornvännen in 1970.', 'en')}

Svärdström also read the everyday life of a medieval town: rune-sticks, tally sticks and tools from Lödöse, where runes were used by people who did not always master them. Of one carver she wrote that he probably “inte har varit runkunnig i vanlig bemärkelse” (“was not rune-literate in the ordinary sense”; {at('1972_094', 102, 'en')}). Runfynd went on appearing every year, with Helmer Gustavson, Thorgunn Snædal, Jan Paul Strid and Marit Åhlén as co-authors ({cite('kallstrom2021a', 'en')}).

The carvers themselves became a question. The runologist Claiborne W. Thompson tested von Friesen's thesis that Öpir had been Visäte's pupil. He called it “{q('thompson1')}” – but noted: “{q('thompson2')}” ({cite('thompson1', 'en')}). It is a model of how the field carries the conversation on: with respect for the older scholar, and with the stones as judges.

Towards the end of the decade the archaeologist Klas-Göran Selinge asked how much the register of ancient monuments really shows. “{q('selinge')}” (“For representativity in comparative calculations of settlement history, the find frequencies are thus as a rule insufficient”), he wrote of the known grave finds ({cite('selinge', 'en')}). The question of what has been preserved and registered – and what that does to every comparison – is the question Montelius asked in 1914, now put to a whole register.

{pic('janssonmalar', ('Sven B. F. Jansson painting runes', 'Sven B. F. Jansson painting runes'), '', 'Sven B. F. Jansson, “Run-Janne”, painting in the runes on a slab around 1980. He was National Antiquary 1966–1972 and wrote in Fornvännen from 1942.', 'en')}

## The 1980s: The first count

In 1980 a young Magnus Källström published an article on the lost runestone at Veddesta in Järfälla, known only through Olof Celsius's copy of 1728 ({at('1980_183', '183–186', 'en')}). He compared the carver's spelling with other stones and showed that an older attribution did not hold. It was the start of a body of work that runs through the rest of the material: {KALL[0]} texts in Fornvännen and Futhark between {KALL[1]} and {KALL[2]}.

In 1983 the archaeologist Mats G. Larsson asked where Ingvar the Far-Travelled really went, and in 1986 he went through the sites of the Ingvar stones: cemeteries, great mounds, assembly sites and finds. He also used a statistical test (χ²) to ask whether the stones were evenly spread over the hundreds of Södermanland. He phrased the conclusion carefully: “{q('larsson1986')}” ({cite('larsson1986', 'en')}). It is, in Fornvännen, the clearest early example of a new kind of question: not what a stone says, but how a group of stones is distributed.

## The 1990s: Statistics' first quarrel

Larsson defended a dissertation in 1990 on the stones commemorating travellers abroad and their farms, comparing them with an equally large group of other runestones. The faculty opponent, Per H. Ramqvist, reviewed it in Fornvännen in 1991, and Larsson replied in 1992 ({at('1992_043', '43', 'en')}). That same year Rune Palm defended *Runor och regionalitet* at Uppsala, a study of variation in the whole Nordic corpus of memorial inscriptions ({at('1994_233', '236', 'en')}).

Then came the quarrel. In 1997 Stina Orsenmark wrote a contribution titled “Matematisk eller kulturhistorisk analys?” – Mathematical or cultural-historical analysis? She built on Birgit Sawyer's work on inheritance and property: “{q('orsen1')}” (“If one starts from the runestone texts, it must today, as far as possible, be considered proven that raising runestones belongs first and foremost with marking inheritance and property, and only secondarily with travelling abroad”; {cite('orsen1', 'en')}). And she was clear about where she stood: “{q('orsen2')}” (“I do not deny that statistics can add to archaeology's understanding, but it should not be applied so that one views the monuments from a mathematical perspective more than from a social and political one”; {cite('orsen2', 'en')}).

Two years later two replies appeared in the same volume. Frands Herschend recalculated Larsson's great farms and found that those who came home and those who died differ in the kind of land their farms held: “{q('hersch1999')}” (“That is why the voyages acquire a social slant”; {cite('hersch1999', 'en')}). And Larsson answered both with a generosity that is rare in a debate: “{q('larsson1999')}” (“But his suggestion to compare travellers who returned with those who died is ingenious, and had I thought of it myself I would probably have included some such investigation in the dissertation already”; {cite('larsson1999', 'en')}).

It is one of the best moments in the whole material. Three scholars argue about statistics, and the result is that the question gets better. Orsenmark's objection about how comparisons are chosen, Herschend's new division and Larsson's openness to it are together a small textbook in how to count on runestones.

In the same years another method became central. Anne-Sofie Gräslund had divided the ornament of runestones into style groups, and in 1996 Larsson used them to date Jarlabanke's stones. He wrote: “{q('larsson1996')}” (“A.-S. Gräslund's method of stylistic dating thus appears by all accounts to have great potential to become an excellent aid in interpreting runic inscriptions from different aspects, and must be regarded as a breakthrough in runological research”; {cite('larsson1996', 'en')}). Nearly all later work on the chronology of runestones, Vitki's included, builds on Gräslund's style groups.

## The 2000s: Verse, names and assembly sites

Herschend went on counting, now on verse. Using Gräslund's style groups as a time scale, he followed how the poetic features changed in the runic texts of the Mälaren region; “{q('hersch2001')}” (“There are two poetic techniques in the runestone material”), he wrote ({cite('hersch2001', 'en')}). In 2008 Alexandra Sanmark and Sarah Semple wrote about assembly sites in Sweden and England ({at('2008_245', '245–259', 'en')}), giving the question of where stones stood a new context: the places where people gathered.

That decade also brought one of the tools the whole field uses every day. In 2007 Lena Peterson published the fifth, revised edition of *Nordiskt runnamnslexikon*. Rikke Steenholt Olesen wrote in her review: “{q('olesen2008')}” (“It is therefore a joy for scholarship that precisely one of the most experienced experts in Nordic runology and onomastics, Lena Peterson, took on the task”; {cite('olesen2008', 'en')}). Whenever Vitki counts personal names, we stand on that lexicon.

## The 2010s: Futhark – a journal of its own

In 2010 the first volume of Futhark: International Journal of Runic Studies appeared. For the first time runic research had an international journal of its own, and the first volume reads like a programme.

Michael Barnes wrote about corpus editions and set a requirement: “{q('barnes2010')}” ({cite('barnes2010', 'en')}). Henrik Williams asked how often rune carvers actually miscarved, and answered that the Viking Age stones were not carelessly made: “{q('williams2010')}” ({cite('williams2010', 'en')}). Kristel Zilmer read expressions such as “this stone” and “here” on the voyage stones and warned against drawing conclusions too quickly: “{q('zilmer2010')}” ({cite('zilmer2010', 'en')}).

In the same volume Mats G. Larsson reviewed Lydia Klos's large dissertation *Runensteine in Schweden* (2009), which goes through the placing of the runestones in all of Sweden that can be assumed to stand where they were raised. Larsson was critical on several points, but he began with what mattered most: “{q('larsson2010')}” (“Klos begins her study with a careful and critical sorting of the runestones that can be assumed to stand in their original place, 730 stones, which is of course an excellent basis for the further work”; {cite('larsson2010', 'en')}). In Futhark 2 Magnus Källström reviewed the archaeologist Selinge's book on runestones and boundaries, in which Selinge had gone through about 220 stones: “{q('kallstrom2011')}” (“Of these he thinks only about 10 % can be primarily linked to boundaries (without also being bridge stones), while 45 % belong with village sites or village lands”; {cite('kallstrom2011', 'en')}).

In 2013 came Futhark 4, with the plenary lectures from the runic symposium in Oslo in 2010. Barnes asked what runology is, and his answer links back to the 1923 exchange between Shetelig and Brate: “{q('barnes2013a')}” ({cite('barnes2013a', 'en')}). He also looked back on the founders' era and, in a colleague's words, on “{q('barnes2013c')}” ({cite('barnes2013c', 'en')}). And he said something this whole series confirms: “{q('barnes2013b')}” ({cite('barnes2013b', 'en')}).

In the same volume Henrik Williams proposed a social runology, asking which stones were costly and which were simple, and noted: “{q('williams2013')}” (“but as far as is known no real attempt has yet been made to relate the observations to social factors”; {cite('williams2013', 'en')}). Judith Jesch went through the words *bóndi* and *þegn* on more than two hundred stones and asked a question that sounds simple but needs the whole material to answer: “{q('jesch2013')}” ({cite('jesch2013', 'en')}). Kristel Zilmer counted the Christian prayers and found that “{q('zilmer2013')}” ({cite('zilmer2013', 'en')}) – Uppland and Södermanland.

Laila Kitzler Åhfeldt had already in 2011 used 3D scanning and groove analysis to compare runestones and early Christian grave monuments in Västergötland: “{q('kitzler2011')}” ({cite('kitzler2011', 'en')}). Vitki's own groove analysis stands in that tradition. Per Stille went through all 82 known runestones in Tiohärad in Småland and found that only fifteen of those with a known site have any link to a cemetery: “{q('stille2014')}” ({cite('stille2014', 'en')}). And Hanna Åkerström, who inventoried the early Viking Age runic material, was honest about the limit of every such inventory: “{q('akerstrom2017')}” (“That we cannot know to what extent inscriptions have been lost up to today of course makes it difficult to judge this”; {cite('akerstrom2017', 'en')}).

## The 2020s: Rök anew, Ingvar anew

The Rök stone, which Cnattingius in 1930 wanted to place in the landscape, was read anew by four scholars from three fields – Per Holmberg, Bo Gräslund, Olof Sundqvist and Henrik Williams – as a text about the sun, Odin and the end of the world ({at('futhark_9-10_7_1383036', '7–38', 'en')}). That a new reading of Sweden's best-known runestone came from linguistics, archaeology and the history of religion together says something about where the field has gone.

{pic('rok', ('The Rök stone', 'The Rök stone'), '', 'The Rök stone (Ög 136) in Östergötland. Cnattingius asked in 1930 where it had stood; in 2020 it was read anew by a linguist, an archaeologist, a historian of religion and a runologist together.', 'en')}

In 2021 Annett Krakow examined the fixed point by which the Ingvar stones have been dated, the Icelandic saga's date for Ingvar's death: “{q('krakow2021')}” (“This Icelandic saga's dating of Ingvar's death has been taken over by many historians and runologists as the starting point for dating the Ingvar expedition”; {cite('krakow2021', 'en')}). And Magnus Källström wrote Futhark's survey of the Swedish corpus editions. He noted that the editions seldom discuss the dating of the late Viking Age stones – “{q('kallstrom2021b')}” ({cite('kallstrom2021b', 'en')}) – and that the annual report of new finds that Svärdström began in 1967 no longer exists: “{q('kallstrom2021a')}” ({cite('kallstrom2021a', 'en')}).

## What becomes visible when everything lies side by side

Once we had sorted the {en_n(N)} texts and checked what we use, 28 recurring questions emerged. It is our sorting, not the authors' own headings, and it measures how often a question is touched on, not who was right. But the pattern is clear: {ALL13} of the 28 are present in all thirteen decades, from 1906 to today, and no decade lacks more than four of them.

{chart_themes_per_decade('en')}

The chart does not say that research has stood still. It says that the big questions are big. Where were the stones raised, and why there? How old are they? Which have been lost, and which no longer stand where they were raised? What do the grave slabs, the coins and silver, the women and children, the stone itself tell us?

{chart_themes('en')}

The question of where the stones stood is touched on in almost two texts out of three, and the question of how old they are in more than half. What becomes visible only when everything lies side by side is how these two questions have usually been answered: with examples. Lindqvist in 1928, Cnattingius in 1930 and Ekholm in 1950 started from the stones they knew, and Ekholm himself said the literature was not enough. That is no weakness of theirs. A single scholar with a single district can do nothing else, and their examples are precisely what makes the questions testable.

There are important exceptions, and they should be named: Larsson's stones of travellers abroad in 1990, Palm's regional variation in 1992, Klos's survey of placing in 2009, Stille's Tiohärad and Selinge's boundary stones. They show that the questions can be taken to whole bodies of material – and the conversation about them, from Orsenmark's objection to Larsson's reply, shows how much depends on how it is done. Williams wrote in 2013 that no one had yet seriously tested whether the workmanship of runestones is linked to social factors, and Barnes that what is missing is data, not theory. Those are two of the field's own voices saying what a hundred years of questions also say.

No single scholar could see this, because no one read all the volumes at once. Nor was it needed: each generation answered the questions of its time, with the material of its time. We have simply had the privilege of reading them one after another.

## The great compilations we stand on

Vitki is not the first attempt to look at the whole material, and much of what we do would be impossible without those who came before. Some should be named in particular:

- **Sveriges runinskrifter** (from 1900) and its editors, from Brate, von Friesen, Wessén and Jansson to Svärdström and their successors: the basis of every reading.
- The **Scandinavian Runic-text Database** (Samnordisk runtextdatabas) at Uppsala University, which made the whole Nordic corpus searchable and which Vitki counts on every day.
- **Mats G. Larsson**, *Runstenar och utlandsfärder* (1990): one of the first attempts to compare a group of runestones with other stones by statistical methods.
- **Rune Palm**, *Runor och regionalitet* (1992): variation in the Nordic memorial inscriptions, province by province.
- **Birgit Sawyer**, from *Property and Inheritance in Viking Scandinavia* (1988) to *The Viking-Age Rune-Stones* (2000): runestones as evidence of inheritance and property, counted across Scandinavia.
- **Anne-Sofie Gräslund**'s style groups: the time scale nearly all later datings of runestones use.
- **Lena Peterson**'s *Nordiskt runnamnslexikon* and *Svenskt runordsregister*: the names and the words, collected.
- **Lydia Klos**, *Runensteine in Schweden* (2009): placing surveyed for the stones in all of Sweden that can be assumed to stand where they were raised.
- **Laila Kitzler Åhfeldt**'s groove analysis and **Magnus Källström**'s work on the carvers and their signatures.

## Our own limits

We have read two journals, not the whole of runic research. Books, dissertations and other journals – where much of the most important work stands, including several of the works above – we have not read in the same way. Of Fornvännen we left about 2,000 texts unread, those on the Stone Age, the Bronze Age and later art history with no link to the period. {CLAUDE_EN} That was the sorting step, and it found the recurring questions in {en_n(N)} texts. {CHECK_EN} The 28 questions are our sorting; another reader might have drawn the lines differently.

The reading also gave us questions we want to test in coming studies, among them where the stones were raised, how old they are and which have been lost. When we do so, we will report how, and we will start from the texts quoted here.

:::box The essentials in brief
- From 1970 scholars begin to count, and they begin to argue about how to count. The quarrel between Larsson, Orsenmark and Herschend in 1997–1999 is a small textbook in how to do it well.
- In 2010 Futhark gave runic research a journal of its own, and its first volumes ask the same questions as the founders – about reading and interpretation, about the social side of the stones, about what is missing.
- {ALL13} of the 28 recurring questions are present in all thirteen decades. That does not mean research has stood still, but that the questions of where the stones were raised and how old they are are big ones – and that they have usually been answered with examples, district by district.
- Everything Vitki does rests on their work: the editions, the database, the lexicons, the style groups and the great compilations of Larsson, Palm, Sawyer, Gräslund, Peterson, Klos and Källström.
:::

## Sources

{JOURNALS_EN}

{sources(P2_KEYS + ['1972_094'], 'en')}

Other works mentioned: Rune Palm, *Runor och regionalitet* (Runrön 7, Uppsala 1992); Birgit Sawyer, *Property and Inheritance in Viking Scandinavia* (Alingsås 1988) and *The Viking-Age Rune-Stones* (Oxford 2000); Lydia Klos, *Runensteine in Schweden* (Berlin 2009); Lena Peterson, *Nordiskt runnamnslexikon* (5th ed., Uppsala 2007). The figures on the texts read and the recurring questions come from Vitki's reading of the journals (November 2026). The images come from Wikimedia Commons, with licence and creator in the captions. Translations of quotations are ours."""

# ======================================================================================================================
# 7. Kontroller, utdata och Firestore
# ======================================================================================================================
assert 102 in pages_with("1972_094", "ristaren inte har varit runkunnig i vanlig bemärkelse")
assert 228 in pages_with("1942_225", "Då Vallentuna kyrka restaurerades 1937 påträffades en runsten")

def tidy(b):
    """Punkt inne i ett citat som följs av källan flyttas ut: ”…tillhuggen” (källa)."""
    return re.sub(r"\.([”“])(;|,| \()", r"\1\2", b)


body1, body1_en, body2, body2_en = (tidy(x) for x in (body1, body1_en, body2, body2_en))

HOLDBACK = re.compile(r"\bAI\b|AI-läsare|slump|nollmodell|null model|random|påståendedatabas|claims database|frågelista|"
                      r"question list|relevans|relevance|Rapport 0|Report 0|låst analysplan|locked plan|signifikan", re.I)
labels = ["Forskning", "Tolkning", "Datering och stil", "Geografi", "Ristare"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
SLUG1, SLUG2 = "hundra-ar-av-runfragor-grundlaggarna", "hundra-ar-av-runfragor-nar-forskarna-borjade-rakna"
SERIES = re.compile(r"^Hundra år av runfrågor")  # web/src/lib/series.ts
assert SERIES.match(title1) and SERIES.match(title2)

for b, lang in ((body1, "sv"), (body1_en, "en"), (body2, "sv"), (body2_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M), "inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    assert b.count(CLAUDE_SV if lang == "sv" else CLAUDE_EN) == 1 and b.count(CHECK_SV if lang == "sv" else CHECK_EN) == 1
    assert len(re.findall(r"språkmodell|language model", b)) == 1, "modellen nämns bara i metodstycket"
    box = b[b.index(":::box"):]
    box = box[:box.index("\n:::\n")]
    assert "Claude" not in box and "språkmodell" not in box and "language model" not in box
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert imgs and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
    for line in b.splitlines():  # bildtexten efter varje bild nämner licens och Commons
        pass
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert all("Wikimedia Commons" in c and re.search(r"CC BY|public domain", c) for c in caps), caps
    for m in re.finditer(r":::chart[^\n]*\n(.*?)\n:::", b, re.S):  # diagrammen: procent, och Vitki står som upphov
        assert "Diagram: Vitki" in m.group(1) or "Chart: Vitki" in m.group(1)
# varje citat i Q som används i en text står där ordagrant
used = {k for k in Q if any(Q[k][2].rstrip(".") in b for b in (body1, body1_en, body2, body2_en))}
assert used == set(Q), set(Q) - used
# forskarna som ska lyftas fram
for name in ("Montelius", "von Friesen", "Brate", "Lindqvist", "Wessén", "Jansson", "Svärdström", "Ekholm", "Nordén"):
    assert name in body1 and name in body1_en, name
for name in ("Gräslund", "Sawyer", "Palm", "Larsson", "Källström", "Williams", "Zilmer", "Klos", "Jesch", "Peterson", "Barnes",
             "Orsenmark", "Herschend", "Stille", "Åkerström", "Krakow", "Kitzler Åhfeldt", "Selinge", "Thompson"):
    assert name in body2 and name in body2_en, name
assert "/artiklar/" + SLUG1 in body2 and "/en/artiklar/" + SLUG1 in body2_en

OUT = [
    {"slug": SLUG1, "title": title1, "summary": summary1, "body": body1, "title_en": title1_en, "summary_en": summary1_en,
     "body_en": body1_en, "labels": labels},
    {"slug": SLUG2, "title": title2, "summary": summary2, "body": body2, "title_en": title2_en, "summary_en": summary2_en,
     "body_en": body2_en, "labels": labels},
]
wc = lambda t: len(re.sub(r"\]\([^)]*\)", "]", t).split())  # noqa: E731  (länkadresser räknas inte)
for i, o in enumerate(OUT, 1):
    path = os.path.join(ROOT, "utdata", "blogg", f"hundra_ar_{i}.json")
    json.dump(o, open(path, "w"), ensure_ascii=False, indent=1)
    print(path, wc(o["body"]), "ord sv,", wc(o["body_en"]), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        ids = sys.argv[sys.argv.index("--update") + 1: sys.argv.index("--update") + 3]
        assert len(ids) == 2, "--update DOC1 DOC2"
        for doc, o in zip(ids, OUT):
            ref = col.document(doc)
            old = ref.get().to_dict()
            assert old and not old.get("published") and old.get("slug") == o["slug"], "Bara de två opublicerade utkasten skrivs över härifrån"
            ref.set({**o, "updatedAt": now}, merge=True)
            print("uppdaterat utkast:", doc, o["slug"])
    else:
        for o in OUT:
            assert not [p for p in blog._all() if p.get("slug") == o["slug"]], "Adressen används redan; skriv över med --update"
        for o in OUT:
            ref = col.document()
            ref.set({**o, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                     "topic": "Forskningshistoria|hundra år av runfrågor", "createdAt": now, "updatedAt": now})
            print("sparat som opublicerat utkast:", ref.id, o["slug"])
    blog._forget()
