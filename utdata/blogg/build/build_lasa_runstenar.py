"""Artikeln "Läs om du kan – kunde vikingatidens folk läsa runstenarna?" (sv + en): vad runstenarna själva säger om att
läsas. Beskrivande räkning utan test mot slumpen (spår P, planerad tisdag 15 december 2026, PUBLICERINGSPLAN.md);
Viktor publicerar själv.

Allt räknas här ur Rundata (data/rundata.json, Sveriges vikingatida runstenar enligt research_gaps.is_runestone, också
fragment och försvunna stenar) och ur Kulturmiljöregistrets beskrivningar (data/raa/kmr_runstenar.json, CC0), och låses
med assert. Formlerna är kodade för hand ur en ordsökning i Rundatas normalisering till fornvästnordiska; varje träff är
läst och listan står nedan (LASA, RATT, HAR, MEDAN). Andra föremål (stenkista, block, berghäll, revben, spänne,
medeltida gravhällar) redovisas för sig och räknas aldrig in i runstenarnas andelar (object-types-separate).

Litteraturcitaten är kontrollerade mot de nedladdade fulltexterna (downloads/tidskrifter, OCR) och kontrolleras igen
här när filerna finns: varje citat måste stå på angiven sida. Länkarna kommer ur data/cache/literature/journals.json.
    ../../../.venv/bin/python build_lasa_runstenar.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import statistics as st
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, commons  # noqa: E402
from src.research_gaps import SWEDISH, is_runestone, province  # noqa: E402

ALL = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
BY = {r["signum"]: r for r in ALL}
RS = [r for r in ALL if is_runestone(r)]
RSIG = {r["signum"] for r in RS}
N = len(RS)
assert N == 2321


def ows(s):
    """Rundatas normalisering till fornvästnordiska, utan citattecknen före namn och utan hakparenteserna runt
    kompletterade runor (texten står annars ordagrant)."""
    return re.sub(r'[\[\]"]', "", BY[s]["normalization_ows"] or "").strip()


pc = lambda x: round(100 * x)  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en = lambda n: f"{n:,}"  # noqa: E731
dsv = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")  # noqa: E731
den = lambda x, d=1: f"{x:.{d}f}"  # noqa: E731

# ---- 1. formlerna, kodade för hand ------------------------------------------------------------------------------------
# Uppmaning att tyda (ráða 'tyda'): sökt på ráð-/ráði/ráða i normaliseringen och i translitterationen (raþ-), varje
# träff läst. U 825 'lét ráða(?)' betyder 'lät ordna' och räknas inte. Hs 10 och G 227 är skadade.
LASA = ["Sö 213", "U 729", "U 887", "U 328", "U 847", "U 1167", "Öl 28", "Vg 119", "Hs 10", "G 227"]
LASA_SKADAD = ["Hs 10", "G 227"]
# Ristaren lovar 'rätta runor' / 'rätt ristat'
RATT = ["U 203", "U 346", "U 847", "Gs 11", "Gs 12", "Öl 28"]
# Texten pekar ut sin plats: 'här' (hér) eller att stenen/runorna 'står' (standa, stendr)
HAR = ["Sö 18", "Sö 66", "Sö 138", "Sö 204", "Sö 206", "U 327", "U 512", "U 541", "U 559", "U 707", "U 729", "U 838",
       "U Fv1983;228", "Ög 136", "Sö 61", "Sö 122", "Sö 137", "Sö 340", "Vs 15"]
# 'så länge stenen lever': minnet knyts till stenens varaktighet (meðan)
MEDAN = ["Sm 16", "U 323", "U Fv1973;194"]
# Färg: fáði 'färgade', steinda 'måla', rjóða 'röda' (Bo Boije4 fáðu översätts 'ristade' och räknas inte)
FARG = ["Ög 8", "Ög 136", "Sö 204", "Sö 205", "Sö 206", "Sö 213", "Sö 347", "Sm 144", "Vg 119", "Hs 10", "Hs 14", "Hs 21"]
for group in (LASA, RATT, HAR, MEDAN, FARG):
    assert len(group) == len(set(group)) and set(group) <= RSIG, group

# kontrollerna som låser kodningen mot texten
for s in ("Sö 213", "U 887"):
    assert "Ráði sá kunni." in ows(s), s
assert "Ráði drengr/tœkr sá rýnn sé rúnum þeim, sem Balli risti." in ows("U 729")
assert ows("U 328").endswith("Ráð þessi!")
assert "Ásmundr hjó rúnar réttar þeim ráða skal." in ows("U 847")
assert "þeim ráða kann." in ows("U 1167")
assert "Brandr rétt í hjó, því ráða kann." in ows("Öl 28")
assert "Ok ráð rúnar þar reginkunnu" in ows("Vg 119")
assert "ráða(?)" in ows("Hs 10") and "ráða kann" in ows("G 227")
assert "lét ráða(?)" in ows("U 825") and "U 825" not in LASA
assert ows("U 203").endswith("Rétt er ristit.")
assert "Ásmundr markaði rúnar réttar." in ows("U 346")
assert "Ásmundr Kára sonr markaði rúnar réttar" in ows("Gs 11") and "Rúnar réttar" in ows("Gs 12")
for s in HAR:
    assert re.search(r"\bH[ée]r\b|\bhé\b|stendr|standa", ows(s)), s
for s in MEDAN:
    assert "meðan" in ows(s) or "með aldr lifir" in ows(s), s
for s in FARG:
    assert re.search(r"\bfáð|steind|roðn|roðin", ows(s)), s
assert "fáðu" in ows("Bo Boije4") and "carved" in BY["Bo Boije4"]["translation_en"] and "Bo Boije4" not in FARG

N_LASA, N_RATT, N_HAR, N_MEDAN, N_FARG = len(LASA), len(RATT), len(HAR), len(MEDAN), len(FARG)
assert (N_LASA, N_RATT, N_HAR, N_MEDAN, N_FARG) == (10, 6, 19, 3, 12)
LASA_RATT = sorted(set(LASA) | set(RATT))
assert len(LASA_RATT) == 14  # Öl 28 och U 847 har båda
PER_LASA = int(round(N / N_LASA, -1))
assert PER_LASA == 230

# ristarna bakom "rätta runor": fyra av sex signerade av en Ásmundr
ASM = [s for s in RATT if any(c["name"] == "Åsmund" and c["kind"] == "S" for c in BY[s]["carvers"])]
assert ASM == ["U 346", "U 847", "Gs 11", "Gs 12"]
# Auðríkr (Rundata: Örik) har ingen annan sten i Rundata
assert [s for s, r in BY.items() if any(c["name"] == "Örik" for c in r["carvers"])] == ["U 887"]
ORD = {4: "fyra", 5: "fem", 12: "tolv"}
WORD = {4: "four", 5: "five", 12: "twelve"}

# var och när uppmaningarna står: hälften i Uppland, hälften i de sena stilgrupperna – och Upplands andel av alla stenar
LASA_U = [s for s in LASA if province(BY[s]) == "U"]
assert len(LASA_U) == 5
LATE = [s for s in LASA if (BY[s]["style"] or "").startswith(("Pr3", "Pr4"))]
assert sorted(LATE) == sorted(["Sö 213", "U 729", "U 887", "U 847", "U 1167"])
U_SHARE = sum(1 for r in RS if province(r) == "U") / N
assert 0.45 < U_SHARE < 0.55, U_SHARE
LASA_PROV = sorted({province(BY[s]) for s in LASA})
assert LASA_PROV == sorted(["Sö", "U", "Öl", "Vg", "Hs", "G"])

# kvinnor bland dem som reser stenarna med uppmaningen: Sö 213 (Gylla, Guðfríðr), U 328 (Gyríðr, Guðlaug)
assert "reisti Gylla at Geirbjôrn, bónda sinn, ok Guðfríðr at fôður sinn" in ows("Sö 213")
assert ows("U 328").startswith("Gyríðr ok Guðlaug þær létu reisa stein þenna")

# ---- 2. det vardagliga tilltalet: 'denna', ristarens namn, bönen --------------------------------------------------------
DENNA = [r for r in RS if re.search(r"\bþenna\b|\bþessi\b|\bþessa\b|\bþessar\b|\bþessum\b|\bþetta\b|\bþessir\b",
                                    ows(r["signum"]))]
N_DENNA = len(DENNA)
assert N_DENNA == 800
SIGNED = [r for r in RS if any(c["kind"] == "S" for c in r["carvers"])]
N_SIGNED = len(SIGNED)
assert N_SIGNED == 248
# bön: ett bönens verb (hjälpe, bärge, lätte, förlåte, nåde) och Gud, Kristus, Mikael eller Herren – eller verbet direkt
# före ande/själ, när gudsnamnet har vittrat bort (U 129 "hjalpi sál")
PRAY_V = re.compile(r"\b(?:hjalp\w*|bjargi|létti\w*|fyrirgefi|náði)\b", re.I)
PRAY_G = re.compile(r"\bGuðs?\b|\bKrist\w*|\bMikj\w*|\bdróttin\w*", re.I)
PRAY_S = re.compile(r"\bhjalp\w*\s+(?:ônd|sál)", re.I)


def is_prayer(s):
    t = ows(s)
    return bool(PRAY_V.search(t) and (PRAY_G.search(t) or PRAY_S.search(t)))


PRAYER = [r for r in RS if is_prayer(r["signum"])]
N_PRAYER = len(PRAYER)
assert N_PRAYER == 301, N_PRAYER
assert all(is_prayer(s) for s in ("U 129", "U 867", "Ög 152", "Sö 139", "Sö 135")) and not is_prayer("Sm 144")
assert pc(N_DENNA / N) == 34 and pc(N_SIGNED / N) == 11 and pc(N_PRAYER / N) == 13 and round(N / N_PRAYER) == 8
PER_SIGNED = round(N / N_SIGNED)
assert PER_SIGNED == 9
# den äldre artikeln räknade bara stenar med läsbar text: 182 av 1 292
SIG_OLD = json.load(open(os.path.join(ROOT, "utdata", "blogg", "2026-10-ristaren-tog-sista-ordet.json"), encoding="utf-8"))
SIG_OLD_B = re.sub(r"\s", " ", SIG_OLD["body"])
assert "1 292 runstenar" in SIG_OLD_B and "På 182 av dem" in SIG_OLD_B
# ristaren i första person och kvinnan som färgade
assert "Alríkr(?) reist-ek rúnar. Er kunni vel knerri stýra." in ows("U 654")
assert "Gunnborga fáði stein þenna, hin góða." in ows("Hs 21")
assert any(c["name"] == "Gunnborga" and c["kind"] == "S" for c in BY["Hs 21"]["carvers"])
# bönen som kanske ber läsaren: Öl 44 (osäker, Zilmer 2013)
assert "Guð hjalpi sálu hans! Les ... ave(?)!" in ows("Öl 44") and "Öl 44" in RSIG
assert "Guð hjalpi ônd hans" in ows("U 96")  # den vanliga formen

# ---- 3. runornas och stenarnas storlek ur Kulturmiljöregistret -----------------------------------------------------------
KMR = json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))
RUNH = re.compile(r"Runhöjd(?:en)?(?:\s+(?:är|ca|cirka|omkring))*\s*(\d+(?:[,.]\d+)?)(?:\s*[-–]\s*(\d+(?:[,.]\d+)?))?\s*(cm|m)\b",
                  re.I)
STENH = re.compile(r"(\d+(?:[,.]\d+)?)\s*m\s+h(?:ög|\b)", re.I)
rune_h, stone_h = {}, {}
for rec in KMR["records"]:
    sig = rec["signa"]
    if len(sig) != 1 or sig[0] not in RSIG:  # bara poster om en enda runsten
        continue
    txt = " ".join(rec["fields"].get("Beskrivning", []))
    if (m := RUNH.search(txt)):
        a = float(m.group(1).replace(",", "."))
        b = float(m.group(2).replace(",", ".")) if m.group(2) else a
        v = (a + b) / 2 * (100 if m.group(3).lower() == "m" else 1)
        if 2 <= v <= 40:  # "6–10 m" och liknande skrivfel faller bort
            rune_h.setdefault(sig[0], v)
    if (m := STENH.search(txt)):
        v = float(m.group(1).replace(",", "."))
        if 0.3 <= v <= 6:
            stone_h.setdefault(sig[0], v)
RH = sorted(rune_h.values())
SH = sorted(stone_h.values())
RH_N, RH_MED, (RH_Q1, _, RH_Q3) = len(RH), st.median(RH), st.quantiles(RH, n=4)
SH_N, SH_MED, (SH_Q1, _, SH_Q3) = len(SH), st.median(SH), st.quantiles(SH, n=4)
assert (RH_N, RH_MED, RH_Q1, RH_Q3) == (935, 8.0, 7.0, 10.5), (RH_N, RH_MED, RH_Q1, RH_Q3)
assert (SH_N, SH_MED, round(SH_Q1, 2), round(SH_Q3, 2)) == (1296, 1.6, 1.22, 1.95), (SH_N, SH_MED, SH_Q1, SH_Q3)
SH_Q1, SH_Q3 = 1.2, 2.0  # avrundat uppåt från hälften, som i texten: "mellan 1,2 och 2,0 meter"

# ---- 4. andra föremål, för sig ----------------------------------------------------------------------------------------
SE = lambda r: province(r) in SWEDISH  # noqa: E731
ANDRA = [r["signum"] for r in ALL if SE(r) and r["period"] == "V" and not is_runestone(r)
         and re.search(r"interpret", r["translation_en"] or "", re.I)]
assert sorted(ANDRA) == sorted(["U 11", "U 29", "U Fv1959;196", "G 310", "U NOR1997;29A", "U NOR2000;32B",
                                "U NOR2000;34A", "G 10", "G 393"]), ANDRA
ANDRA_STEN = ["U 11", "U 29", "U Fv1959;196", "G 310"]  # block, berghäll, stenkista, bildsten (G 310 osäker)
ANDRA_LOSA = ["U NOR1997;29A", "U NOR2000;32B", "U NOR2000;34A", "G 393", "G 10"]  # fyra revben, ett ringspänne
assert sorted(ANDRA_STEN + ANDRA_LOSA) == sorted(ANDRA)
assert [BY[s]["object"] for s in ANDRA_STEN] == ["jordfast stenblock", "berghäll", "massiv stenkista", "bildsten med runinskrift"]
assert all(BY[s]["object"] == "runben, revben" for s in ANDRA_LOSA[:4]) and BY["G 10"]["object"] == "ringspänne"
SIGTUNA = [s for s in ANDRA_LOSA if BY[s]["parish"] == "Sigtuna"]
assert len(SIGTUNA) == 3
assert "Hverr sem rúnum ráðr hafi bœnir fyrir Ála/Alla sál." in ows("U Fv1959;196")
assert BY["U Fv1959;196"]["place"] == "Hammarby kyrka"
assert ows("U 11").startswith("Ráð þú rúnar.") and ows("U 29").startswith("Ráð þú!")
assert "Ráð þú!" in ows("U NOR2000;34A")
assert "menn rýnasta á Miðgarði" in ows("Sö 56") and BY["Sö 56"]["object"] == "jordfast block"
# medeltida gravhällar med runor i Sverige som ber läsaren om förbön
GH = [r for r in ALL if SE(r) and r["period"] == "M" and "gravhäll" in (r["object"] or "").lower()]
GHP = [r for r in GH if re.search(r"\bpray", r["translation_en"] or "", re.I)]
GHP_G = [r for r in GHP if province(r) == "G"]
assert (len(GH), len(GHP), len(GHP_G)) == (226, 45, 40)
assert "Biðið góðs fyrir" in ows("G 295")

# ---- 5. litteraturen: varje citat står på angiven sida i den nedladdade fulltexten ----------------------------------------
TXT = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
LIT = json.load(open(os.path.join(ROOT, "data", "cache", "literature", "journals.json"), encoding="utf-8"))["articles"]
flat = lambda s: re.sub(r"[\W_]+", "", s.replace("\xad", "")).lower()  # noqa: E731
CITAT = [  # (nyckel, fil, sidhuvud som inleder sidan, sidhuvud för nästa sida, citat)
    ("futhark_4_201_682701", "futhark/text/futhark_4_201_682701.txt", "206 • Reviews", None,
     "implies a tolerably widespread ability to read what was written"),
    ("futhark_4_201_682701", "futhark/text/futhark_4_201_682701.txt", "206 • Reviews", None,
     "faktum är att vi inte riktigt vet hur det förhåller sig med förmågan att läsa under vikingatiden"),
    ("futhark_4_201_682701", "futhark/text/futhark_4_201_682701.txt", "206 • Reviews", None,
     "förmedlats muntligt av ett litet fåtal läskunniga"),
    ("futhark_1_27_381123", "futhark/text/futhark_1_27_381123.txt", "34 • Henrik Williams", "Read What’s There • 35",
     "they were meant to be seen and presumably read by more than a few"),
    ("futhark_1_27_381123", "futhark/text/futhark_1_27_381123.txt", "Read What’s There • 31", "Read What’s There • 33",
     "They trick us into misjudging the competence of runographers and their readers"),
    ("futhark_1_27_381123", "futhark/text/futhark_1_27_381123.txt", "Read What’s There • 33", "34 • Henrik Williams",
     "Balli’s readers will be members of a select group of those qualified to appreciate his text"),
    ("futhark_1_27_381123", "futhark/text/futhark_1_27_381123.txt", "Read What’s There • 33", "34 • Henrik Williams",
     "He proposes (pp. 681–86) the attractive interpretation tǿkR ‘alert, adept’"),
    ("futhark_1_27_381123", "futhark/text/futhark_1_27_381123.txt", "Read What’s There • 33", "34 • Henrik Williams",
     "interpretation presented by Jansson originated with Otto von Friesen"),
    ("futhark_1_123_381124", "futhark/text/futhark_1_123_381124.txt", "138 • Kristel Zilmer", "Deictic References • 139",
     "there emerges a kind of encounter between the original commissioners of the memorial and the potential audience"),
    ("futhark_1_123_381124", "futhark/text/futhark_1_123_381124.txt", "138 • Kristel Zilmer", "Deictic References • 139",
     "a kind of materialised and visualised speech"),
    ("futhark_4_129_682695", "futhark/text/futhark_4_129_682695.txt", "136 • Kristel Zilmer", "Prayers and Invocations • 137",
     "There is a further uncertain case on a fragmentary eleventh-century stone inscription from Öland (Öl 44)"),
    ("futhark_4_129_682695", "futhark/text/futhark_4_129_682695.txt", "136 • Kristel Zilmer", "Prayers and Invocations • 137",
     "which has been interpreted Les Ave ‘read Hail (Mary)’"),
    ("1984_250", "fornvannen/text/1984_250.txt", "258    H. Gustavson och Th. Snadal Brink", None,
     ("Runstenarnas inskrifter måste ha", "fortsatt att fascinera förbipasserande länge efter",
      "det att runstenstiden tog slut")),
    ("1984_250", "fornvannen/text/1984_250.txt", "258    H. Gustavson och Th. Snadal Brink", None,
     ("Runkunnigheten", "levde ju också vidare och många har säkert kun-", "nat läsa inskrifterna långt in i medeltiden")),
]
if os.path.isdir(TXT):
    for key, fil, start, stop, quote in CITAT:
        text = open(os.path.join(TXT, fil), encoding="utf-8").read()
        i = text.index(start)
        j = text.index(stop, i) if stop else i + 6000
        page = text[i:j]
        if isinstance(quote, tuple):  # tvåspaltig OCR: citatets rader står i ordning men med grannspalten emellan
            k = 0
            for part in quote:
                k = page.index(part, k) + len(part)
        else:
            assert flat(quote) in flat(page), (key, quote)
    assert "Th. S. B." in open(os.path.join(TXT, "fornvannen/text/1984_250.txt"), encoding="utf-8").read()
URL = {k: LIT[k]["url"] for k in ("futhark_4_201_682701", "futhark_1_27_381123", "futhark_1_123_381124",
                                  "futhark_4_129_682695", "1984_250")}
assert URL["futhark_4_201_682701"].endswith("diva2:682701/FULLTEXT01.pdf") and URL["1984_250"].startswith("https://pub.raa.se/")
assert (LIT["futhark_4_201_682701"]["pages"], LIT["futhark_1_27_381123"]["pages"], LIT["futhark_1_123_381124"]["pages"],
        LIT["futhark_4_129_682695"]["pages"]) == ("201–207", "27–39", "123–141", "129–171")

# ---- 6. fotografier (Wikimedia Commons) --------------------------------------------------------------------------------
F_SO213 = "Sö213 Nybble gård - kmb.16000300019518.jpg"
F_U887 = "U887 Skillsta - KMB - 16001000039664.jpg"
F_U729 = "Oscar Juel - 090 Runsten U 729 Ågersta, Löts socken, Uppland - Otto von Friesen - Alvin-record 144234.jpg"
INFO = commons.commons_info([F_SO213, F_U887, F_U729])
assert INFO[F_SO213]["author"] == INFO[F_U887]["author"] == "Bengt A. Lundberg"
assert INFO[F_SO213]["licence"].startswith("CC BY 2.5") and INFO[F_U887]["licence"] == "CC BY 2.5"
assert INFO[F_U729]["licence"] == "Public domain" and INFO[F_U729]["author"] == "Hans Oscar Juel"
assert "Otto von Friesen" in INFO[F_U729]["description"]


def pic(f, alt, text, lang):
    i = INFO[f]
    if i["licence"] == "Public domain":
        lic = "fri från upphovsrätt" if lang == "sv" else "public domain"
    else:
        lic = f"[{i['licence']}]({i['licence_url']})"
    who = "Foto" if lang == "sv" else "Photo"
    return f"![{alt}]({i['thumb']})\n{text} {who}: {i['author']}, {lic}, via [Wikimedia Commons]({i['page']})."


SIG_ART = "/artiklar/2026-10-ristarsignatur-breder-ut-sig"
VAG_RAPP = "/forskningsrapporter/ristningen-vand-mot-vagen"
GH_REPO = "https://github.com/Precatio/runes/blob/main/utdata/blogg/build/build_lasa_runstenar.py"

# ---- svenska ------------------------------------------------------------------------------------------------------------
title = "Läs om du kan – kunde vikingatidens folk läsa runstenarna?"
summary = (f"Ingen vet hur många som kunde läsa runor på 1000-talet. Men stenarna själva säger vem de räknade med. Vi gick "
           f"igenom Sveriges {sp(N)} vikingatida runstenar: var tredje pekar på sig själv med ordet ”denna”, var nionde bär "
           f"ristarens namn – och bara tio ber uttryckligen om en läsare: tyde den som kan.")

chart_sv = f""":::chart Hur ofta talar runstenen om sig själv och sin läsare?
Ordet ”denna” eller ”dessa” – om stenen, runorna eller bron | {dsv(100 * N_DENNA / N)} | {N_DENNA} stenar
En bön till Gud för den döde | {dsv(100 * N_PRAYER / N)} | {N_PRAYER} stenar
Ristarens namn | {dsv(100 * N_SIGNED / N)} | {N_SIGNED} stenar
”Här” eller ”står” – texten pekar ut sin plats | {dsv(100 * N_HAR / N)} | {N_HAR} stenar
+En uppmaning att tyda runorna | {dsv(100 * N_LASA / N)} | {N_LASA} stenar
Ett löfte om ”rätta runor” | {dsv(100 * N_RATT / N)} | {N_RATT} stenar
Källa: Vitkis räkning bland Sveriges {sp(N)} vikingatida runstenar i Samnordisk runtextdatabas. Fragment räknas med, så andelarna är lägsta tal.
:::"""

body = f"""Den som står framför en runsten i dag behöver nästan alltid skylten bredvid för att förstå den. Runorna går att lära sig på en eftermiddag, men språket är tusen år gammalt och stavningen följer regler vi får gissa oss till. Så var det inte för den som gick förbi på 1000-talet. Språket var hans eget. Men kunde han läsa det som stod?

Ingen frågade vikingarna, och de skrev inga böcker om saken. Stenarna själva säger ändå mer än man tror. Ibland talar de om att de står *här*. Ibland går ristaren i god för att runorna är *rätta*. Och på några få stenar vänder sig texten direkt till den som läser: *Ráði sá kunni* – tyde den som kan.

Vi räknade hur ofta det händer. Det är en enkel räkning, utan test mot slumpen. Vi gick igenom Sveriges {sp(N)} vikingatida runstenar i Samnordisk runtextdatabas, också fragment och försvunna stenar, och sökte i texterna efter de ord där stenen talar om sig själv, sin plats eller sin läsare. Varje träff lästes för hand. Det tar ett kort avsnitt. Resten handlar om människorna – de som ristade, de som lät rista och de som skulle läsa.

{chart_sv}

Så ser det ut i stort. En sten på tre pekar på sig själv: *stein þenna*, denna sten, som om någon stod framför den. Ungefär var nionde bär ristarens namn och var åttonde en bön. Men bara en sten på omkring {PER_LASA} ber uttryckligen någon att läsa.

## Tyde den som kan

Tio runstenar i Sverige uppmanar den som ser dem att tyda runorna. Verbet är *ráða*, samma ord som vårt *råda*; här betyder det att tyda, att lista ut vad som står. *Ráði sá kunni*, tyde den som kan, står det på två av dem. På Lundby i Markim (U 328) är uppmaningen kortast. Två kvinnor, Gyríðr och Guðlaug, reser stenen efter sin far och sin make och slutar med en befallning: *Ráð þessi!* – Tyd dessa! På två andra (U 847 och U 1167) säger texten att runorna är huggna *þeim ráða skal* eller *þeim ráða kann*: åt den som ska tyda, åt den som kan tyda. På två är stenen så skadad att bara ordet för att tyda står kvar.

Hälften av de tio står i Uppland, och hälften är ristade under 1000-talets andra hälft, i stilgrupperna Pr3 och Pr4. Mer än så ska man inte läsa in. Uppland har {pc(U_SHARE)} procent av alla runstenarna, så hälften är ungefär vad man väntar sig, och tio stenar är för få för att visa ett mönster. Det vi kan säga är det enkla. Uppmaningen fanns i hela landet, från Öland till Hälsingland, men den var sällsynt.

## Gylla och Guðfríðr på Selaön

Den kanske vackraste av dem står vid Nybble på Selaön i Mälaren (Sö 213). Där har ristaren skrivit sitt namn först, inte sist:

> *{ows('Sö 213')}*

Stenen högg Ásbjôrn, målad som ett märke, och band den med runor. Gylla reste den efter Geirbjôrn, sin make, och Guðfríðr efter sin far. Han var den bäste bonden i Kíll. Tyde den som kan.

{pic(F_SO213, 'Runstenen Sö 213 vid Nybble på Selaön', 'Sö 213 vid Nybble på Selaön: ”Stenen högg Ásbjôrn, målad som ett märke … Tyde den som kan.”', 'sv')}

Det är en hustru och en dotter som har låtit göra stenen, och tre saker i texten handlar om att synas och läsas. Stenen var *steindan*, målad. Runorna *band* den, som ett band runt något dyrbart. Och sist kommer en utmaning till den som stannar. Ásbjôrn visste att det inte räckte att hugga runorna. Någon skulle också kunna dem.

Rundata tillskriver, med hänvisning till Magnus Källström, en ristare med samma namn också en sten vid Överselö kyrka drygt tre kilometer bort (Sö 206). Även den är rest av kvinnor, en mor efter sina söner och en syster efter sina bröder, och även den talar om hur den ser ut: *Hér skal standa steinar þessir, rúnum roðnir* – här ska dessa stenar stå, rödfärgade med runor.

## Sonen som högg själv

Vid Skillsta i Skogs-Tibble socken i Uppland (U 887) står en sten som tre bröder lät resa efter sin far:

> *{ows('U 887')}*

Jógeirr och Fastgeirr och Auðríkr lät resa stenen efter Borggeirr, sin ryktbare far. Själv högg Auðríkr efter sin far dessa runor. Tyde den som kan. (Namnet kan också läsas Eyríkr, Erik.)

{pic(F_U887, 'Runstenen U 887 vid Skillsta', 'U 887 vid Skillsta i Skogs-Tibble: ”Själv högg Auðríkr efter sin far dessa runor. Tyde den som kan.”', 'sv')}

Det är ingen känd ristare som talar här. Rundata har inte hans namn på någon annan sten. Det är en son som har lärt sig runorna så väl att han kunde hugga sin fars sten själv, och som ville att det skulle synas. Och han slutar som Ásbjôrn: med en utmaning. Den som kan läsa ska läsa. Den som inte kan ser i alla fall att här finns något att kunna.

## Rätta runor

Sex stenar säger något om själva ristningen: att den är rätt. *Rétt er ristit*, det är rätt ristat, står det vid Angarns kyrka (U 203). *Ásmundr markaði rúnar réttar*, Ásmundr märkte ut rätta runor, står det vid Frösunda kyrka (U 346). Vid Västeråkers kyrka (U 847) sätts de två sakerna ihop: *Ásmundr hjó rúnar réttar þeim ráða skal* – Ásmundr högg rätta runor åt den som ska tyda. Och på Öland skriver Brandr att han högg rätt, *því ráða kann*: därför kan man tyda (Öl 28).

Fyra av de sex stenarna är signerade av en Ásmundr; på en sten i Gästrikland (Gs 11) kallar han sig Kåres son. Ett löfte om rätta runor har bara mening om någon kan se om det stämmer. Ristaren talar här till en läsare som väntas kunna skilja rätt från fel – eller åtminstone till en beställare som ville kunna säga att texten var rätt gjord.

## Här ska stenen stå

En annan sorts tilltal pekar. *Hér mun standa steinn nær brautu*, här ska stenen stå nära vägen, står det på två stenar i Uppland som Rundata räknar till ristaren Balle (U 707 och U 838). *Hér skal standa steinn viðr bryggju*, här ska stenen stå vid bron, står det vid Tjäran i Fasterna (U 512). Sammanlagt {N_HAR} stenar pekar ut sin egen plats med ett *här* eller säger att stenen eller runorna *står*. På tre till knyts minnet till stenens varaktighet, som vid Nöbbele i Småland (Sm 16): *Því mun góðs manns um getit verða, meðan steinn lifir ok stafir rúna* – så ska den gode mannen bli ihågkommen, så länge stenen lever och runornas stavar.

Ordet *här* har bara mening för den som står på platsen. Kristel Zilmer, som har studerat sådana pekande ord på runstenarna, skriver att de skapar ”a kind of encounter between the original commissioners of the memorial and the potential audience” – ett slags möte mellan dem som lät resa stenen och den publik som kunde komma (*Futhark* 1, 2010, s. 138). Hon kallar runstenens text ”a kind of materialised and visualised speech”, ett slags tal som har blivit sten och bild.

Det stämmer med något vi har mätt. I en [forskningsrapport]({VAG_RAPP}) fann vi att hälften av de stenar som står kvar på sin plats vänder ristningen inom 45 grader från vägen, mot en fjärdedel om riktningen vore slumpvis. Texten vändes mot den som gick förbi. En reservation hör till: vägen vi mätte mot är för det mesta vägen som den går i dag. Om vikingatidens väg gick på samma ställe prövar vi nu mot gamla kartor, och det arbetet är inte klart.

## Ristaren som skrev sitt namn

Det mest personliga tilltalet är ett namn. På {N_SIGNED} av stenarna, ungefär var nionde, har ristaren skrivit sitt eget namn, med ett verb som *risti* eller *hjó*, ristade eller högg. Hur namnet med tiden tog textens sista ord har vi skrivit om i [Ristaren tog sista ordet]({SIG_ART}). Här räknas bara en sak: en signatur är skriven för att läsas. Den som sätter sitt namn på en sten räknar med att någon ska se det.

En ristare talar till och med i första person. Vid Varpsund i Övergrans socken (U 654), där fem söner reste en sten efter en far som dog österut med Ingvar, står det: *Alríkr(?) reist-ek rúnar. Er kunni vel knerri stýra.* Jag, Alríkr, ristade runorna. Han kunde väl styra en knarr. Och i Hälsingland är det en kvinna som har gjort det sista arbetet på stenen: *Gunnborga fáði stein þenna, hin góða* – Gunnborga den goda färgade denna sten (Hs 21).

## Bönen gick till Gud, inte till dig

Man kunde tro att en kristen runsten skulle be den som går förbi om en bön. Det gör den nästan aldrig. På {N_PRAYER} av stenarna står en bön, men den riktar sig till Gud: *Guð hjalpi ônd hans*, Gud hjälpe hans ande. Läsaren är vittne, inte den som ber. I vår genomgång finns bara en runsten som kan ha bett läsaren direkt, ett fragment från Bo på Öland (Öl 44), där bönen följs av runorna *lis : iki*. De har tolkats som *Les Ave*, ”läs Ave Maria”, och Kristel Zilmer räknar det som ett osäkert fall (*Futhark* 4, 2013, s. 136).

Utanför runstenarna ser det annorlunda ut, och det ska räknas för sig. På en stenkista vid Hammarby kyrka i Uppland (U Fv1959;196), också den från vikingatiden, står det: *Hverr sem rúnum ráðr hafi bœnir fyrir Ála sál* – var och en som tyder runorna må ha böner för Ales själ. Där möts de två sakerna, läsaren och bönen. Och på medeltidens gravhällar blir det vanligt. Av {len(GH)} medeltida gravhällar med runor i Sverige ber {len(GHP)} läsaren om förbön, {len(GHP_G)} av dem på Gotland: *Biðið góðs fyrir …*, be gott för … Att vända sig till den som läser och be om något kom alltså med kyrkogården, efter runstenarnas tid.

## Runor en handflata höga

Hur stora var runorna? Kulturmiljöregistrets beskrivningar anger runornas höjd för {RH_N} av stenarna. Medianen – värdet i mitten när alla stenarna ställs på rad efter runornas höjd – är {dsv(RH_MED, 0)} centimeter, och hälften av stenarna har runor mellan {dsv(RH_Q1, 0)} och {dsv(RH_Q3)} centimeter höga – ungefär en handflata. Stenarna själva är enligt registret i mitten {dsv(SH_MED)} meter höga, hälften mellan {dsv(SH_Q1)} och {dsv(SH_Q3)} meter.

Det är text som syns på några stegs håll, inte på långt avstånd. Och den var färgad. På {ORD[N_FARG]} stenar står det att runorna eller stenen målades: *fáði*, färgade, *steindi*, målade, eller *roðnir*, rödfärgade. Färgen har nästan alltid regnat bort, men när stenen var ny var den det första man såg.

Runornas storlek säger att stenen skulle synas. Om den också lästes säger storleken ingenting om.

## Vad forskningen säger

Kunde folk läsa? Forskarna är inte överens, och det ärliga svaret är att ingen vet.

Michael Barnes menar i sin handbok om runor att så många monument på allmänna platser ”implies a tolerably widespread ability to read what was written”, alltså att förmågan att läsa var ganska spridd. Vi har läst det i Patrik Larssons recension av boken, där han citerar meningen. Larsson kallar det en fullt rimlig slutsats men skriver att ”faktum är att vi inte riktigt vet hur det förhåller sig med förmågan att läsa under vikingatiden”. Budskapet kan, skriver han, ha ”förmedlats muntligt av ett litet fåtal läskunniga”, och skriften kan ha varit bara en del av helheten (*Futhark* 4, 2013, s. 206).

Henrik Williams lutar åt andra hållet. Runstenarnas antal, täthet, placering, storlek och texternas omfång visar enligt honom att ”they were meant to be seen and presumably read by more than a few” – de var gjorda för att ses och antagligen läsas av fler än några få (*Futhark* 1, 2010, s. 34). Han varnar för tolkningar som förklarar svåra ord som felristningar: ”They trick us into misjudging the competence of runographers and their readers” – de lurar oss att underskatta både ristarna och deras läsare (s. 32).

Hans exempel är Ågerstastenen (U 729), där Balle ristade *Ráði drengr/tœkr sá rýnn sé rúnum þeim*. Runorna säger *tekr*. Sedan Otto von Friesen har ordet lästs som en felristning för *drængR*, dräng, och Judith Jesch byggde på det en läsning, som Williams citerar, där ”Balli’s readers will be members of a select group of those qualified to appreciate his text” – Balles läsare skulle vara en utvald krets. Williams föredrar Evert Salbergers förslag, *tǿkR*, ’vaken, skicklig’: inget felhugget ord utan ett ovanligt (s. 33). Rundata anger båda. Med Salbergers läsning säger stenen: tyde den skicklige som är kunnig i runor, de runor som Balle ristade.

{pic(F_U729, 'Otto von Friesen vid runstenen U 729 i Ågersta', 'Runologen Otto von Friesen vid U 729 i Ågersta, stenen där han läste ordet *tekr* som en felristning.', 'sv')}

Och läsandet tog inte slut med runstenarna. Thorgunn Snædal Brink skrev 1984 att ”runstenarnas inskrifter måste ha fortsatt att fascinera förbipasserande länge efter det att runstenstiden tog slut” och att ”många har säkert kunnat läsa inskrifterna långt in i medeltiden” (*Fornvännen* 79, s. 258).

Lösa föremål hör inte till räkningen här, men de ska nämnas för sig. Från vikingatidens Sverige finns samma uppmaning på {ORD[len(ANDRA_LOSA)]} lösa föremål – fyra revben, tre av dem från Sigtuna, och ett ringspänne från Gotland – och på {ORD[len(ANDRA_STEN)]} andra stenar än runstenar: ett block på Adelsö (U 11, *Ráð þú rúnar*), berghällen vid Hillersjö (U 29, *Ráð þú!*), stenkistan vid Hammarby och, osäkert, en bildsten på Gotland. Ett revben med orden *Ráð þú!* är ingen minnessten. Kanske var det en övning eller en lek, en gåta till någon som satt bredvid. Det vet vi inte. Men uppmaningen att tyda hörde uppenbarligen hemma också i vardagen.

## Vad stenarna svarar

Så vad svarar stenarna? De svarar inte på hur många som kunde läsa. Men de visar vem de räknade med. En sten på tre pekar på sig själv – *denna sten* – som om någon stod framför den. Var nionde bär ristarens namn, skrivet för att läsas. Ett tjugotal pekar ut platsen med ett *här*. Och bara tio ber uttryckligen om en läsare, och de gör det på ett sätt som säger något: *tyde den som kan*. Det låter inte som en uppmaning till alla. Det låter som en utmaning till några.

Här tillåter vi oss en tolkning som inte är stenarnas egen. Kanske var det så det fungerade. Texten var skriven för den som kunde, och den som inte kunde fick höra den, av en granne, av ristaren eller av den som lät resa stenen. En runsten var något man både såg och hörde. Rökstenen, den längsta av dem alla, säger själv *sôgum*, jag säger eller vi säger. Den räknar med åhörare.

## Pröva själv

Nästa gång du står vid en runsten, leta efter ordet för sten – *stain*, *stin* eller *sten* – och läs ordet efter. Står det *þansi*, *þinsi* eller *þina* är det ordet *denna*. Då pekar stenen på sig själv och på platsen där du står. Den räknade med dig.

:::box Så räknade vi
- **Materialet:** Sveriges {sp(N)} vikingatida runstenar i Samnordisk runtextdatabas, också fragment och försvunna stenar. Andra stenar och lösa föremål räknas för sig och aldrig in i runstenarnas andelar.
- **Sökningen:** vi sökte i Rundatas normaliserade texter efter orden för att tyda (*ráða*), för ”rätt” om runorna, för ”här” och ”står”, för färg och för ”denna”, och läste varje träff för hand. Ristarnas namn är Rundatas egna uppgifter om signerade stenar. Här räknas alla stenar, också fragment, och därför blir talet högre än i artikeln Ristaren tog sista ordet, som räknade bara de 1 292 stenarna med läsbar text och fann namnet på 182.
- **Svagheten:** normaliseringen är redan en tolkning, och på skadade stenar kan formlerna ha försvunnit. Talen är därför lägsta tal. Runhöjderna kommer ur fältbeskrivningar av olika ålder och noggrannhet.
- **Det vi inte gör:** vi prövar inget mot slumpen. Det här är en beskrivning av vad som står, inte ett test.
:::

:::box Det viktigaste i korthet
- Runstenarna räknar med en läsare hela tiden – en sten på tre pekar på sig själv med ordet ”denna” – men bara tio av {sp(N)} ber uttryckligen någon att läsa.
- De som ber gör det som en utmaning, *tyde den som kan*, och ristare lovade ibland ”rätta runor”. Att kunna läsa var något att vara stolt över, inte något alla väntades kunna.
- Bönen på runstenarna riktades till Gud. Att be den som läser om förbön blev vanligt först på medeltidens gravhällar.
- Hur många som kunde läsa vet ingen. Stenarna svarar på en annan fråga: de var gjorda för att ses av alla och läsas av några.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Kulturmiljöregistret, Riksantikvarieämbetet, via K-samsök (CC0): runornas och stenarnas höjd.
- Larsson, Patrik 2013. Recension av Michael P. Barnes, *Runes: A Handbook* (2012). *Futhark* 4, s. 201–207; citaten s. 206. [Fri fulltext]({URL['futhark_4_201_682701']})
- Williams, Henrik 2010. ”Read What’s There: Interpreting Runestone Inscriptions.” *Futhark* 1, s. 27–39; citaten s. 32–34, där Judith Jesch (1998) citeras på s. 33. [Fri fulltext]({URL['futhark_1_27_381123']})
- Zilmer, Kristel 2010. ”Deictic References in Runic Inscriptions on Voyage Runestones.” *Futhark* 1, s. 123–141; citaten s. 138. [Fri fulltext]({URL['futhark_1_123_381124']})
- Zilmer, Kristel 2013. ”Christian Prayers and Invocations in Scandinavian Runic Inscriptions from the Viking Age and Middle Ages.” *Futhark* 4, s. 129–171; om Öl 44 s. 136. [Fri fulltext]({URL['futhark_4_129_682695']})
- Gustavson, Helmer & Snædal Brink, Thorgunn 1984. ”Runfynd 1983.” *Fornvännen* 79; stycket av Thorgunn Snædal Brink, s. 258. [Fri fulltext]({URL['1984_250']})
- Vitkis räkning, med listan över varje kodad sten, är öppen på [GitHub]({GH_REPO}).
- Bilder: Wikimedia Commons, med fotografen i bildtexterna."""

# ---- engelska -----------------------------------------------------------------------------------------------------------
title_en = "Read it if you can – could Viking-age people read the runestones?"
summary_en = (f"Of Sweden's {en(N)} Viking-age runestones, one in three points at itself with the word ‘this’ and one in nine "
              f"carries the carver's name, but only ten explicitly ask for a reader: interpret, he who can.")

chart_en = f""":::chart How often does a runestone speak of itself and its reader?
The word ‘this’ or ‘these’ – of the stone, the runes or the bridge | {den(100 * N_DENNA / N)} | {N_DENNA} stones
A prayer to God for the dead | {den(100 * N_PRAYER / N)} | {N_PRAYER} stones
The carver's name | {den(100 * N_SIGNED / N)} | {N_SIGNED} stones
‘Here’ or ‘stands’ – the text points out its place | {den(100 * N_HAR / N)} | {N_HAR} stones
+A call to interpret the runes | {den(100 * N_LASA / N)} | {N_LASA} stones
A promise of ‘right runes’ | {den(100 * N_RATT / N)} | {N_RATT} stones
Source: Vitki's count among Sweden's {en(N)} Viking-age runestones in the Scandinavian Runic-text Data Base. Fragments are included, so the shares are minimum figures.
:::"""

body_en = f"""Anyone standing in front of a runestone today nearly always needs the sign beside it to understand it. The runes can be learnt in an afternoon, but the language is a thousand years old and the spelling follows rules we have to guess at. It was not like that for someone walking past in the eleventh century. The language was their own. But could they read what was written?

Nobody asked the Vikings, and they wrote no books on the matter. Yet the stones themselves say more than one might think. Sometimes they say that they stand *here*. Sometimes the carver vouches that the runes are *right*. And on a few stones the text turns straight to the one who reads: *Ráði sá kunni* – interpret, he who can.

We counted how often that happens. It is a simple count, with no test against chance. We went through Sweden's {en(N)} Viking-age runestones in the Scandinavian Runic-text Data Base, including fragments and lost stones, and searched the texts for the words in which a stone speaks of itself, its place or its reader. Every hit was read by hand. That takes one short section. The rest is about the people – those who carved, those who had the stones carved and those who were meant to read.

{chart_en}

That is the broad picture. One stone in three points at itself: *stein þenna*, this stone, as if someone stood in front of it. About one in nine carries the carver's name and one in eight a prayer. But only about one stone in {PER_LASA} explicitly asks anyone to read.

## Interpret, he who can

Ten runestones in Sweden call on whoever sees them to interpret the runes. The verb is *ráða*, the same word as English *read* and the old *rede*; here it means to interpret, to work out what is written. *Ráði sá kunni*, interpret, he who can, stands on two of them. At Lundby in Markim (U 328) the call is at its shortest. Two women, Gyríðr and Guðlaug, raise the stone for their father and their husband and end with a command: *Ráð þessi!* – Interpret these! On two others (U 847 and U 1167) the text says that the runes were cut *þeim ráða skal* or *þeim ráða kann*: for the one who shall interpret, for the one who can. On two the stone is so damaged that only the word for interpreting remains.

Half of the ten stand in Uppland, and half were carved in the second half of the eleventh century, in the style groups Pr3 and Pr4. One should not read more into it than that. Uppland has {pc(U_SHARE)} per cent of all runestones, so half is roughly what one would expect, and ten stones are too few to show a pattern. What we can say is the simple thing. The call was known across the country, from Öland to Hälsingland, but it was rare.

## Gylla and Guðfríðr on Selaön

Perhaps the most beautiful of them stands at Nybble on the island of Selaön in Lake Mälaren (Sö 213). Here the carver put his name first, not last:

> *{ows('Sö 213')}*

Ásbjôrn cut the stone, painted as a marker, and bound it with runes. Gylla raised it in memory of Geirbjôrn, her husband, and Guðfríðr in memory of her father. He was the best farmer in Kíll. Interpret, he who can.

{pic(F_SO213, 'The runestone Sö 213 at Nybble on Selaön', 'Sö 213 at Nybble on Selaön: ‘Ásbjôrn cut the stone, painted as a marker … Interpret, he who can.’', 'en')}

It is a wife and a daughter who had the stone made, and three things in the text are about being seen and read. The stone was *steindan*, painted. The runes *bound* it, like a band around something precious. And last comes a challenge to whoever stops. Ásbjôrn knew that cutting the runes was not enough. Someone also had to know them.

Rundata, following Magnus Källström, attributes to a carver of the same name a stone at Överselö church just over three kilometres away (Sö 206). It too was raised by women, a mother for her sons and a sister for her brothers, and it too speaks of how it looks: *Hér skal standa steinar þessir, rúnum roðnir* – here shall these stones stand, reddened with runes.

## The son who carved it himself

At Skillsta in Skogs-Tibble parish in Uppland (U 887) stands a stone that three brothers had raised for their father:

> *{ows('U 887')}*

Jógeirr and Fastgeirr and Auðríkr had the stone raised in memory of Borggeirr, their renowned father. Auðríkr himself cut these runes in memory of his father. Interpret, he who can. (The name can also be read Eyríkr, Eric.)

{pic(F_U887, 'The runestone U 887 at Skillsta', 'U 887 at Skillsta in Skogs-Tibble: ‘Auðríkr himself cut these runes in memory of his father. Interpret, he who can.’', 'en')}

This is not a known carver speaking. Rundata has his name on no other stone. It is a son who had learnt the runes well enough to cut his father's stone himself, and who wanted that to show. And he ends as Ásbjôrn did: with a challenge. Whoever can read shall read. Whoever cannot will at least see that there is something here to know.

## Right runes

Six stones say something about the carving itself: that it is right. *Rétt er ristit*, it is rightly carved, stands at Angarn church (U 203). *Ásmundr markaði rúnar réttar*, Ásmundr marked out the right runes, stands at Frösunda church (U 346). At Västeråker church (U 847) the two things are joined: *Ásmundr hjó rúnar réttar þeim ráða skal* – Ásmundr cut the right runes for the one who shall interpret. And on Öland, Brandr writes that he cut rightly, *því ráða kann*: so one can interpret (Öl 28).

Four of the six stones are signed by an Ásmundr; on a stone in Gästrikland (Gs 11) he calls himself Kári's son. A promise of right runes only means something if someone can see whether it holds. The carver is speaking to a reader expected to tell right from wrong – or at least to a patron who wanted to be able to say that the text was properly made.

## Here shall the stone stand

Another kind of address points. *Hér mun standa steinn nær brautu*, here shall the stone stand near the road, is written on two stones in Uppland that Rundata assigns to the carver Balli (U 707 and U 838). *Hér skal standa steinn viðr bryggju*, here shall the stone stand by the bridge, is written at Tjäran in Fasterna (U 512). Altogether {N_HAR} stones point out their own place with a *here*, or say that the stone or the runes *stand*. On three more, the memory is tied to how long the stone lasts, as at Nöbbele in Småland (Sm 16): *Því mun góðs manns um getit verða, meðan steinn lifir ok stafir rúna* – so the good man shall be remembered, as long as the stone lives and the staves of the runes.

The word *here* only means something to someone standing at the spot. Kristel Zilmer, who has studied such pointing words on the runestones, writes that they create ‘a kind of encounter between the original commissioners of the memorial and the potential audience’ (*Futhark* 1, 2010, p. 138). She calls the runestone's text ‘a kind of materialised and visualised speech’.

That fits something we have measured. In a [research report](/en{VAG_RAPP}) we found that half of the stones still in their place turn the inscription within 45 degrees of the road, against a quarter if the direction were random. The text was turned towards the passer-by. One reservation belongs here: the road we measured against is mostly the road as it runs today. Whether the Viking-age road ran in the same place we are now testing against old maps, and that work is not finished.

## The carver who wrote his name

The most personal form of address is a name. On {N_SIGNED} of the stones, about one in nine, the carver wrote his own name, with a verb such as *risti* or *hjó*, carved or cut. How the name in time took the last word of the text we have written about in [The carver had the last word](/en{SIG_ART}). Here only one thing counts: a signature is written to be read. Whoever puts their name on a stone expects someone to see it.

One carver even speaks in the first person. At Varpsund in Övergran parish (U 654), where five sons raised a stone for a father who died in the east with Ingvarr, it says: *Alríkr(?) reist-ek rúnar. Er kunni vel knerri stýra.* I, Alríkr, carved the runes. He could steer a cargo ship well. And in Hälsingland it is a woman who did the last work on the stone: *Gunnborga fáði stein þenna, hin góða* – Gunnborga the good coloured this stone (Hs 21).

## The prayer went to God, not to you

One might think that a Christian runestone would ask the passer-by for a prayer. It almost never does. On {N_PRAYER} of the stones there is a prayer, but it is addressed to God: *Guð hjalpi ônd hans*, God help his spirit. The reader is a witness, not the one who prays. In our survey only one runestone may have asked the reader directly, a fragment from Bo on Öland (Öl 44), where the prayer is followed by the runes *lis : iki*. They have been interpreted as *Les Ave*, ‘read the Hail Mary’, and Kristel Zilmer counts it as an uncertain case (*Futhark* 4, 2013, p. 136).

Beyond the runestones things look different, and that must be counted separately. On a stone coffin at Hammarby church in Uppland (U Fv1959;196), also from the Viking Age, it says: *Hverr sem rúnum ráðr hafi bœnir fyrir Ála sál* – whoever interprets the runes, may he have prayers for Áli's soul. Here the two things meet, the reader and the prayer. And on the grave slabs of the Middle Ages it becomes common. Of {len(GH)} medieval grave slabs with runes in Sweden, {len(GHP)} ask the reader to pray, {len(GHP_G)} of them on Gotland: *Biðið góðs fyrir …*, pray good for … Turning to the reader and asking for something came, then, with the churchyard, after the time of the runestones.

## Runes a palm high

How large were the runes? The descriptions in the Swedish heritage register (Kulturmiljöregistret) give the height of the runes for {RH_N} of the stones. The median – the middle value when all the stones are lined up by the height of their runes – is {den(RH_MED, 0)} centimetres, and half of the stones have runes between {den(RH_Q1, 0)} and {den(RH_Q3)} centimetres high – about the width of a palm. According to the register the stones themselves are {den(SH_MED)} metres high in the middle, half of them between {den(SH_Q1)} and {den(SH_Q3)} metres.

That is text you can see from a few paces, not from far off. And it was coloured. On {WORD[N_FARG]} stones the text says that the runes or the stone were painted: *fáði*, coloured, *steindi*, painted, or *roðnir*, reddened. The paint has almost always washed away, but when the stone was new it was the first thing one saw.

The size of the runes says that the stone was meant to be seen. Whether it was also read, the size does not say.

## What research says

Could people read? Scholars do not agree, and the honest answer is that nobody knows.

Michael Barnes argues in his handbook on runes that so many monuments in public places ‘implies a tolerably widespread ability to read what was written’. We have read the sentence in Patrik Larsson's review of the book, where he quotes it. Larsson calls this a perfectly reasonable conclusion, but writes that in fact we do not really know how things stood with the ability to read in the Viking Age. The message, he writes, may have been passed on orally by a small number of people who could read, and the writing may have been only one part of the whole (*Futhark* 4, 2013, p. 206, in Swedish).

Henrik Williams leans the other way. The runestones' number, concentration, location, size and the scope of their texts show, in his view, that ‘they were meant to be seen and presumably read by more than a few’ (*Futhark* 1, 2010, p. 34). He warns against interpretations that explain difficult words away as miscarvings: ‘They trick us into misjudging the competence of runographers and their readers’ (p. 32).

His example is the Ågersta stone (U 729), where Balli carved *Ráði drengr/tœkr sá rýnn sé rúnum þeim*. The runes say *tekr*. Since Otto von Friesen the word has been read as a miscarving of *drængR*, ‘valiant man’, and Judith Jesch built on it a reading, quoted by Williams, in which ‘Balli’s readers will be members of a select group of those qualified to appreciate his text’. Williams prefers Evert Salberger's proposal, *tǿkR*, ‘alert, adept’: not a miscut word but a rare one (p. 33). Rundata gives both. With Salberger's reading the stone says: let the adept who is skilled in runes interpret the runes that Balli carved.

{pic(F_U729, 'Otto von Friesen at the runestone U 729 at Ågersta', 'The runologist Otto von Friesen at U 729, Ågersta, the stone where he read the word *tekr* as a miscarving.', 'en')}

And reading did not end with the runestones. Thorgunn Snædal Brink wrote in 1984 that the runestones' inscriptions must have gone on fascinating passers-by long after the runestone period ended, and that many could surely read them far into the Middle Ages (*Fornvännen* 79, p. 258, in Swedish).

Loose objects are not part of the count here, but they should be mentioned separately. From Viking-age Sweden the same call is found on {WORD[len(ANDRA_LOSA)]} loose objects – four ribs, three of them from Sigtuna, and a ring brooch from Gotland – and on {WORD[len(ANDRA_STEN)]} stones that are not runestones: a boulder on Adelsö (U 11, *Ráð þú rúnar*), the rock face at Hillersjö (U 29, *Ráð þú!*), the stone coffin at Hammarby and, uncertainly, a picture stone on Gotland. A rib with the words *Ráð þú!* is no memorial. Perhaps it was an exercise or a game, a riddle for someone sitting nearby. We do not know. But the call to interpret evidently belonged in everyday life too.

## What the stones answer

So what do the stones answer? They do not tell us how many people could read. But they show whom they counted on. One stone in three points at itself – *this stone* – as if someone were standing in front of it. One in nine carries the carver's name, written to be read. Some twenty point out the place with a *here*. And only ten explicitly ask for a reader, and they do it in a way that says something: *interpret, he who can*. That does not sound like a call to everyone. It sounds like a challenge to some.

Here we allow ourselves an interpretation that is not the stones' own. Perhaps that is how it worked. The text was written for those who could read it, and those who could not heard it, from a neighbour, from the carver or from whoever had the stone raised. A runestone was something one both saw and heard. The Rök stone, the longest of them all, itself says *sôgum*, I say or we say. It counts on listeners.

## Try it yourself

Next time you stand by a runestone, look for the word for stone – *stain*, *stin* or *sten* – and read the word after it. If it says *þansi*, *þinsi* or *þina*, that is the word *this*. Then the stone is pointing at itself, and at the spot where you stand. It counted on you.

:::box How we counted
- **The material:** Sweden's {en(N)} Viking-age runestones in the Scandinavian Runic-text Data Base, including fragments and lost stones. Other stones and loose objects are counted separately and never added to the runestones' shares.
- **The search:** we searched Rundata's normalised texts for the words for interpreting (*ráða*), for ‘right’ of the runes, for ‘here’ and ‘stands’, for colour and for ‘this’, and read every hit by hand. The carvers' names are Rundata's own record of signed stones. Here all stones are counted, fragments too, which is why the figure is higher than in the article The carver had the last word, which counted only the 1,292 stones with a legible text and found the name on 182.
- **The weakness:** the normalisation is already an interpretation, and on damaged stones the formulas may have been lost. The figures are therefore minimum figures. The rune heights come from field descriptions of varying age and precision.
- **What we do not do:** we test nothing against chance. This is a description of what is written, not a test.
:::

:::box The essentials in brief
- The runestones count on a reader all the time – one stone in three points at itself with the word ‘this’ – but only ten of {en(N)} explicitly ask anyone to read.
- Those that ask do it as a challenge, *interpret, he who can*, and carvers sometimes promised ‘right runes’. Being able to read was something to be proud of, not something everyone was expected to manage.
- The prayer on the runestones was addressed to God. Asking the reader to pray became common only on the grave slabs of the Middle Ages.
- How many could read, nobody knows. The stones answer a different question: they were made to be seen by all and read by some.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Kulturmiljöregistret, Swedish National Heritage Board, via K-samsök (CC0): the height of the runes and stones.
- Larsson, Patrik 2013. Review of Michael P. Barnes, *Runes: A Handbook* (2012). *Futhark* 4, pp. 201–207; the quotations p. 206. [Free full text]({URL['futhark_4_201_682701']})
- Williams, Henrik 2010. ‘Read What’s There: Interpreting Runestone Inscriptions.’ *Futhark* 1, pp. 27–39; the quotations pp. 32–34, where Judith Jesch (1998) is quoted on p. 33. [Free full text]({URL['futhark_1_27_381123']})
- Zilmer, Kristel 2010. ‘Deictic References in Runic Inscriptions on Voyage Runestones.’ *Futhark* 1, pp. 123–141; the quotations p. 138. [Free full text]({URL['futhark_1_123_381124']})
- Zilmer, Kristel 2013. ‘Christian Prayers and Invocations in Scandinavian Runic Inscriptions from the Viking Age and Middle Ages.’ *Futhark* 4, pp. 129–171; on Öl 44 p. 136. [Free full text]({URL['futhark_4_129_682695']})
- Gustavson, Helmer & Snædal Brink, Thorgunn 1984. ‘Runfynd 1983.’ *Fornvännen* 79; the passage by Thorgunn Snædal Brink, p. 258. [Free full text]({URL['1984_250']})
- Vitki's count, with the list of every coded stone, is open on [GitHub]({GH_REPO}).
- Images: Wikimedia Commons, with the photographer in the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "AI" not in re.sub(r"[A-Za-zÅÄÖåäö]AI|AI[A-Za-zÅÄÖåäö]", "", b)
assert body.count("![") == body_en.count("![") == 3

out = {"slug": "las-om-du-kan-kunde-folk-lasa-runstenarna", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Formler och syfte", "Ristare", "Tolkning"]}
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "lasa_runstenar.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body_en.split()), "words")

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
                 "topic": "Forskning|formler", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
