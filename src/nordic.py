"""Danska, norska och svenska runstenar jämförda, och drag som går över gränserna (GET /api/research/nordic;
Kartan → Norden). METHODS.md avsnitt 14f.

Urvalet är Rundatas vikingatida runstenar (period V, föremål runsten) i tre serier: den danska (DR, med Skåne,
Blekinge, Bornholm och Slesvig, som hörde till det danska riket), den norska (N) och de svenska landskapens. Stenarna
grupperas antingen efter serie (land) eller efter riken och trakter omkring 1025, som i kartans gränslager
(web/src/lib/realms.json).

Mönstren läser Rundatas engelska översättning och translitterationen, som är gjorda på samma sätt i alla tre
serierna. Normaliseringen är det inte: den är runsvensk för svenska stenar, runodansk för danska (Guþ hialpi, kumbl
þøsi) och fornvästnordisk för norska (reist rúnar), så mönsterkartans mönster, som söker i normaliseringen, skulle
missa danska och norska former. Kors ingår inte: Rundata anger korsets form för 41 % av de svenska stenarna men för
12 % av de danska och 3 % av de norska, också där korset är välkänt (Kristusbilden på Jellingstenen, DR 42).

Tiden hålls konstant med tre perioder (före 1000, 1000–1050, 1050 och senare). Dateringarna är Rundatas och bygger
på olika system: stilgrupperna (Gräslund) för svenska stenar, den danska indelningen (Helnæs-Gørlev, för-Jelling,
Jelling, efter-Jelling) för danska och årtal eller sekel där sådana finns; de flesta norska stenar är bara daterade
till vikingatid och räknas inte när tiden hålls konstant.

Dansk prägel: en logistisk regression (ridge, klassvikter) lär sig skilja danska från svenska stenar på ordval och
stavning, tränad bara på samtida stenar (970–1050), så att den lär sig skillnaden mellan danskt och svenskt bruk och
inte skillnaden mellan tidiga och sena stenar. Stenar i träningen får en prognos ur en modell som inte sett dem
(femfaldig korsvalidering). Hög dansk prägel betyder att stenen är formulerad och stavad som en dansk sten, inte att
ristaren var dansk.
"""
from __future__ import annotations

import csv
import math
import os
import re
import zlib

from src.inscription_types import CATEGORIES
from src.language_profile import DOTTED
from src.pattern_map import mid_year, pagan
from src.research_gaps import SWEDISH, certain_carvers, province
from src.styles import BY_CODE

# Groupings: by series (country) and by realms and districts about 1025 (the map's layer of realms, epoch 1025)
LANDS = [("danmark", "Danmark", "danmark"), ("sverige", "Sverige", "sverige"), ("norge", "Norge", "norge")]
REALMS_1025 = [
    ("dk_jylland", "Jylland och Slesvig", "danmark"), ("dk_oarna", "Danska öarna", "danmark"),
    ("dk_skane", "Skåne och Blekinge", "danmark"), ("dk_bornholm", "Bornholm", "danmark"),
    ("svitjod", "Svitjod (Uppland, Södermanland, Västmanland, Närke)", "svear"),
    ("svear_norr", "Dalarna och Norrland", "svear"),
    ("gotar", "Götaland (Väster- och Östergötland)", "gotar"),
    ("smaland", "Småland, Öland och Dalsland", "gotar"),
    ("gotland", "Gotland", "gotland"), ("jamtland", "Jämtland och Härjedalen", "jamtland"),
    ("omstritt", "Bohuslän och Värmland (omstridda)", "omstridd"), ("norge", "Norge", "norge"),
]
GROUPINGS = {"land": LANDS, "rike": REALMS_1025}
SWEDISH_REALM = {"U": "svitjod", "Sö": "svitjod", "Vs": "svitjod", "Nä": "svitjod",
                 "D": "svear_norr", "Gs": "svear_norr", "Hs": "svear_norr", "M": "svear_norr", "Ån": "svear_norr",
                 "Lp": "svear_norr", "Ög": "gotar", "Vg": "gotar", "Sm": "smaland", "Öl": "smaland", "Ds": "smaland",
                 "G": "gotland", "J": "jamtland", "Hr": "jamtland", "Bo": "omstritt", "Vr": "omstritt"}
DANISH_REALM = {"Nørrejylland": "dk_jylland", "Sønderjylland": "dk_jylland", "Sydslesvig": "dk_jylland",
                "Fyn": "dk_oarna", "Sjælland": "dk_oarna", "Lolland-Falster": "dk_oarna", "Skåne": "dk_skane",
                "Blekinge": "dk_skane", "Halland": "dk_skane", "Bornholm": "dk_bornholm"}
# Svear and Geats: "Swedish soil" about 1025 (Gotland, Jämtland and the contested provinces are left out)
SWEDISH_SOIL = {"svitjod", "svear_norr", "gotar", "smaland"}

BINS = [("tidig", "före 1000", None, 1000), ("mitt", "1000–1050", 1000, 1050), ("sen", "1050 och senare", 1050, None)]

_I = re.I
TR_CHRISTIAN = re.compile(r"\b(God|God's|Christ|Christian|Christians|holy|Mary|Michael|soul|souls|spirit)\b", _I)
TR_PRAYER = re.compile(r"\b(God|Christ|Michael|Mary)\b[^.;]*\b(help|helps|grant|forgive|ease|receive|have mercy)\b"
                       r"|\bGod's mother|\bMother of God|\bhelp\w*\b[^.;]*\b(soul|spirit)\b", _I)
TR_SOUL_INTENT = re.compile(r"\bfor (his|her|their|the) (soul|spirit)", _I)
TR_SOUL = re.compile(r"\b(soul|souls|spirit)\b", _I)
TR_SIGNATURE = re.compile(r"(?<!be )(?<!was )(?<!were )\b(carved|cut|coloured|colored|painted|hewed|hewn|marked)\b", _I)
# The commissioner, not the carver: "had these runes cut", "had the stone carved" (at most four words between); and a
# nickname, "(the) Coloured"
TR_COMMISSION = re.compile(r"\b(?:had|has|have)\s+(?:[\w'()\[\]/?.,-]+\s+){0,4}$", _I)
TR_NICKNAME = re.compile(r"\(?the\)?\s*$", _I)
TR_TITLE = re.compile(r"\bþegn|\bthegn|\bdrengr|\bdrengs\b|\bvaliant m[ae]n\b", _I)
NORM_TITLE = re.compile(r"\bþ[æe]?i?a?gn|\bdr[æe]ng", _I)
NORM_KUMBL = re.compile(r"\bkumb?l", _I)
TL_STONE_DIPH = re.compile(r"\bst(?:ai|ei|æi|ia)n\w{0,2}\b")
TL_STONE_MONO = re.compile(r"\bst(?:i|e|æ)n\w{0,2}\b")
TL_AFT_SHORT = re.compile(r"\b[aæei]u?ft\b")
TL_AFT_LONG = re.compile(r"\b[aæei]u?ft[iR]\w*")
TR_PLACED = re.compile(r"\bplaced\b", _I)
TR_RAISED = re.compile(r"\braised\b", _I)
TR_HAD = re.compile(r"\bhad\b[^.;]{0,60}\b(raised|made|carved|cut|placed|built)\b", _I)
TR_MADE = re.compile(r"\bmade\b", _I)
TR_PRAISE = re.compile(r"\b(good|best|bravest|foremost|most generous|mildest|very good)\b", _I)
TR_ABROAD = re.compile(CATEGORIES["fard"][3] + r"|Russia|Saxony|Frisia|Wend|Ireland|Rome", _I)
TR_BRIDGE = re.compile(CATEGORIES["bro_vag"][3], _I)
TR_INHERIT = re.compile(CATEGORIES["arv"][3], _I)

# key, label, group, help: the patterns that can be compared between the series
PATTERNS = [
    ("kristen", "Kristen text", "Tro",
     "Gud, Kristus, själen eller en helig nämns i texten. Kors räknas inte, eftersom Rundata bara beskriver korsen på "
     "svenska stenar."),
    ("bon", "Kristen bön", "Tro", "En bön, t.ex. Gud hjälpe hans själ."),
    ("hednisk", "Hedniska eller rituella markörer", "Tro",
     "Torsåkallan, vígi-formler (Tor vige dessa runor), förbannelser eller alu. Få stenar."),
    ("neutral", "Utan religiösa markörer i texten", "Tro",
     "Varken kristen text eller hedniska markörer. En sten utan dem är inte därmed hednisk."),
    ("titel", "Titlarna þegn och drængr", "Innehåll",
     "Den dödes titel: þegn (en man i kungens eller en storman tjänst) eller drængr (ung krigare, god karl)."),
    ("kumbl", "Ordet kumbl", "Innehåll", "Minnesmärket kallas kumbl (”dessa kummel”)."),
    ("bro", "Bro- och vägbygge", "Innehåll", "Nämner en bro eller väg som byggts."),
    ("fard", "Utlandsfärd", "Innehåll", "Nämner resa, död eller strid utomlands."),
    ("arv", "Arv och ägande", "Innehåll", "Uppgifter om arv, ägande eller gård."),
    ("signatur", "Ristarsignatur", "Skrift", "Ristaren nämns: X ristade, högg, målade eller märkte."),
    ("stungna", "Stungna runor", "Skrift", "Stungna runor (e, g, d, y) i inskriften."),
    ("monoftong", "Monoftong i sten", "Skrift",
     "Ordet sten skrivet med en vokal, t.ex. stin, i stället för diftongen ai (stain). Bara stenar där ordet finns."),
]
LIKENESS_PATTERN = ("dansk", "Dansk prägel", "Över gränserna",
                    "Stenen är formulerad och stavad mer som en dansk än som en svensk sten, enligt modellen under ”Över "
                    "gränserna” (danska och svenska stenar med minst två av dragen). Det betyder inte att ristaren var dansk.")
NOT_COMPARABLE = [
    ("Kors", "Rundata anger korsets form för 41 % av de svenska runstenarna, 12 % av de danska och 3 % av de norska, "
     "också där korset är välkänt (Jellingstenen DR 42, Dynnastenen N 68). En skillnad i kors vore en skillnad i "
     "beskrivningen, inte i stenarna."),
    ("Mönsterkartans språkdrag", "Söker i Rundatas normalisering, som är runsvensk, runodansk eller fornvästnordisk "
     "beroende på serie, och missar därför danska och norska former (Guþ hialpi, reist rúnar)."),
]

# The features of Danish likeness: key, label
FEATURES = [
    ("placed", "satte stenen (”placed”)"), ("raised", "reste stenen (”raised”)"),
    ("had", "lät resa eller göra (”had … raised”)"), ("made", "gjorde (”made”)"),
    ("kumbl", "ordet kumbl"), ("titel", "titlarna þegn eller drængr"), ("praise", "berömmande ord (”good”, ”best”)"),
    ("sten_mono", "sten med monoftong (stin)"), ("sten_diph", "sten med diftong (stain)"),
    ("aft_short", "æft utan -iR"), ("aft_long", "æftiR med -iR"),
    ("bon", "kristen bön"), ("soul", "själen nämns"), ("bro", "bro eller väg"), ("signatur", "ristarsignatur"),
    ("stungna", "stungna runor"), ("fard", "utlandsfärd"),
]
TRAIN_YEARS = (970, 1050)

# Rundata's remarks about another country's runes, language or carvers, and texts that name another Nordic land
REMARK = re.compile(r"\b(dansk|svensk|norsk|västnordisk|östnordisk|gutnisk|isländsk)\w*\b(?!\s+Run-urkunder|\s+fornminnes)", _I)
SWEDISH_MADE = re.compile(r"\bsvensk\w*", _I)
# A stone needs at least two of the features for its likeness to say anything: a short or broken text has none, and
# the model then gives it only the base rate
MIN_FEATURES = 2
MENTIONS = {"danmark": re.compile(r"\bDenmark|\bDanes?\b|\bDanish\b", _I),
            "sverige": re.compile(r"\bSweden|\bSwedes?\b|\bSwedish\b|\bUppsala|\bSvíþjóð", _I),
            "norge": re.compile(r"\bNorway|\bNorwegians?\b|\bNorwegian\b", _I)}


# A place for the Danish stones without coordinates in Rundata (scripts/fetch_dk_remains.py): the runestone in Fund og
# Fortidsminder, the parish church or the village
EXTRA_PLACES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dk",
                            "runesten_koordinater.csv")


def extra_places(path: str = EXTRA_PLACES) -> dict[str, tuple[float, float, str]]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return {r["signum"]: (float(r["lat"]), float(r["lon"]), r["precision"]) for r in csv.DictReader(fh) if r["lat"]}


def land_of(rec: dict) -> str | None:
    p = province(rec)
    return "danmark" if p == "DR" else "norge" if p == "N" else "sverige" if p in SWEDISH else None


def realm_of(rec: dict) -> str | None:
    p = province(rec)
    if p == "DR":
        district = (rec.get("district") or "").split(", ")[-1].strip(" ()")
        return DANISH_REALM.get(district)
    return "norge" if p == "N" else SWEDISH_REALM.get(p)


def is_runestone(rec: dict) -> bool:
    return rec.get("period") == "V" and land_of(rec) is not None and "runsten" in (rec.get("object") or "").lower()


def _danish_year(d: str) -> int | None:
    if "jelling el" in d:
        return 1000
    if "kristen efter-jelling" in d:
        return 1025
    if "efter-jelling" in d:
        return 1015
    if "för-jelling" in d:
        return 925
    if "helnæs" in d:
        return 825
    if "jelling" in d:
        return 970
    return None


def _parse_year(d: str) -> int | None:
    m = re.search(r"(\d{3,4})\s*[-–]\s*(\d{3,4})", d)
    if m:
        return (int(m[1]) + int(m[2])) // 2
    m = re.search(r"(\d{3,4})-t", d)
    if m:
        c = int(m[1])
        if re.search(r"första hälften|första delen|\bb\b|början", d):
            return c + 25
        if re.search(r"andra hälften|\bs\b|slutet", d):
            return c + 75
        return c + 50
    m = re.search(r"\b(\d{3,4})\b", d)
    return int(m[1]) if m else None


def year_of(rec: dict) -> int | None:
    """Ungefärligt år: stilgruppens mitt för svenska stenar, den danska periodens mitt, annars Rundatas årtal eller sekel."""
    d = (rec.get("dating") or "").lower()
    if province(rec) in SWEDISH:
        y = mid_year(rec)
        if y is not None:
            return y
    return _danish_year(d) or _parse_year(d)


def bin_of(year: int | None) -> str | None:
    if year is None:
        return None
    return next(k for k, _, lo, hi in BINS if (lo is None or year >= lo) and (hi is None or year < hi))


def _texts(rec: dict) -> tuple[str, str, str]:
    norm = (rec.get("normalization") or "") + " " + (rec.get("normalization_ows") or "")
    return rec.get("translation_en") or "", rec.get("transliteration") or "", norm


def signed(tr: str) -> bool:
    """Ristaren nämns som den som ristade, högg, målade eller märkte – inte beställaren som lät hugga stenen."""
    return any(not TR_COMMISSION.search(tr[max(0, m.start() - 60):m.start()])
               and not TR_NICKNAME.search(tr[max(0, m.start() - 8):m.start()]) for m in TR_SIGNATURE.finditer(tr))


def features(rec: dict) -> dict[str, int] | None:
    """Dragen för dansk prägel (0/1), eller None för en sten utan läsbar text."""
    tr, tl, norm = _texts(rec)
    if not tr.strip():
        return None
    words = re.findall(r"[a-zæøåþðʀR]+", tl)
    soul = bool(TR_SOUL.search(TR_SOUL_INTENT.sub("", tr)))
    return {
        "placed": int(bool(TR_PLACED.search(tr))), "raised": int(bool(TR_RAISED.search(tr))),
        "had": int(bool(TR_HAD.search(tr))), "made": int(bool(TR_MADE.search(tr))),
        "kumbl": int(bool(NORM_KUMBL.search(norm))),
        "titel": int(bool(TR_TITLE.search(tr) or NORM_TITLE.search(norm))),
        "praise": int(bool(TR_PRAISE.search(tr))),
        "sten_mono": int(bool(TL_STONE_MONO.search(tl))), "sten_diph": int(bool(TL_STONE_DIPH.search(tl))),
        "aft_short": int(bool(TL_AFT_SHORT.search(tl))), "aft_long": int(bool(TL_AFT_LONG.search(tl))),
        "bon": int(bool(TR_PRAYER.search(tr))), "soul": int(soul), "bro": int(bool(TR_BRIDGE.search(tr))),
        "signatur": int(signed(tr)), "stungna": int(bool(set("".join(words)) & DOTTED)),
        "fard": int(bool(TR_ABROAD.search(tr))),
    }


def patterns(rec: dict, ft: dict[str, int] | None) -> dict[str, int | None]:
    """De jämförbara mönstren: 1, 0 eller None (oläslig text, eller inget ord sten för monoftongen)."""
    if ft is None:
        # Without a translation only a Thor motif in Rundata's remarks can still be seen (a hammer on a fragment)
        return {k: (1 if k == "hednisk" and pagan(rec) else None) for k, *_ in PATTERNS}
    tr = rec.get("translation_en") or ""
    christian = bool(TR_CHRISTIAN.search(tr)) or bool(ft["bon"])
    heathen = pagan(rec)
    stone = ft["sten_mono"] or ft["sten_diph"]
    return {"kristen": int(christian), "bon": ft["bon"], "hednisk": int(heathen),
            "neutral": int(not christian and not heathen), "titel": ft["titel"], "kumbl": ft["kumbl"],
            "bro": ft["bro"], "fard": ft["fard"], "arv": int(bool(TR_INHERIT.search(tr))), "signatur": ft["signatur"],
            "stungna": ft["stungna"], "monoftong": ft["sten_mono"] if stone else None}


# --- Statistics --------------------------------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mantel_haenszel(strata: list[tuple[int, int, int, int]]) -> tuple[float | None, float | None, int]:
    """Oddskvot och CMH-test (med kontinuitetskorrektion) över tabeller (a, b, c, d); bara tabeller med båda grupperna."""
    from scipy.stats import chi2
    num = den = sa = ea = va = 0.0
    used = 0
    for a, b, c, d in strata:
        n = a + b + c + d
        if a + b == 0 or c + d == 0 or n < 2:
            continue
        used += 1
        num += a * d / n
        den += b * c / n
        m1, m0, r1 = a + b, c + d, a + c
        sa += a
        ea += m1 * r1 / n
        va += m1 * m0 * r1 * (n - r1) / (n * n * (n - 1))
    or_mh = num / den if den > 0 and num > 0 else None
    p = float(chi2.sf((abs(sa - ea) - 0.5) ** 2 / va, 1)) if va > 0 else None
    return or_mh, p, used


def compare(rows: list[dict], key: str, grouping: str) -> dict:
    """Andelen med mönstret per grupp och per period, ett test av skillnaden mellan grupperna och, för länderna,
    parvisa jämförelser med och utan tiden konstant."""
    from scipy.stats import chi2_contingency, fisher_exact
    gk = "land" if grouping == "land" else "rike"
    groups = []
    for g, label, realm in GROUPINGS[grouping]:
        rs = [r for r in rows if r[gk] == g and r["v"][key] is not None]
        k = sum(r["v"][key] for r in rs)
        lo, hi = wilson(k, len(rs))
        by_bin = {}
        for b, *_ in BINS:
            rb = [r for r in rs if r["bin"] == b]
            by_bin[b] = {"n": len(rb), "k": sum(r["v"][key] for r in rb)}
        groups.append({"key": g, "label": label, "realm": realm, "n": len(rs), "k": k,
                       "share": round(k / len(rs), 3) if rs else None, "lo": round(lo, 3), "hi": round(hi, 3),
                       "bins": by_bin, "dated": sum(1 for r in rs if r["bin"])})
    tested = [g for g in groups if g["n"] >= 10]
    test = None
    if len(tested) >= 2 and sum(g["k"] for g in tested) > 0 and sum(g["n"] - g["k"] for g in tested) > 0:
        table = [[g["k"], g["n"] - g["k"]] for g in tested]
        chi, p, dof, expected = chi2_contingency(table)
        test = {"chi2": round(float(chi), 2), "df": int(dof), "p": float(p), "groups": [g["key"] for g in tested],
                "small": bool((expected < 5).any())}
    pairs = []
    if grouping == "land":
        by = {g["key"]: g for g in groups}
        for a_, b_ in (("danmark", "sverige"), ("norge", "sverige"), ("danmark", "norge")):
            A, B = by[a_], by[b_]
            if A["n"] < 5 or B["n"] < 5:
                continue
            a, b, c, d = A["k"], A["n"] - A["k"], B["k"], B["n"] - B["k"]
            crude = (a + 0.5) * (d + 0.5) / ((b + 0.5) * (c + 0.5))
            strata = [(A["bins"][x]["k"], A["bins"][x]["n"] - A["bins"][x]["k"],
                       B["bins"][x]["k"], B["bins"][x]["n"] - B["bins"][x]["k"]) for x, *_ in BINS]
            or_mh, p_mh, used = mantel_haenszel(strata)
            pairs.append({"a": a_, "b": b_, "or": round(crude, 2), "p": float(fisher_exact([[a, b], [c, d]])[1]),
                          "or_mh": None if or_mh is None else round(or_mh, 2), "p_mh": p_mh, "strata": used,
                          "n_dated": A["dated"] + B["dated"]})
    return {"groups": groups, "test": test, "pairs": pairs}


# --- Danish likeness ---------------------------------------------------------------------------------------------

def _fit(X, y, w, lam: float = 1.0):
    """Logistisk regression med ridge (lam) och vikter, med Newtons metod; första kolumnen är interceptet."""
    import numpy as np
    beta = np.zeros(X.shape[1])
    pen = lam * np.eye(X.shape[1])
    pen[0, 0] = 0
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ beta))
        hess = X.T @ (X * (w * p * (1 - p))[:, None]) + pen
        step = np.linalg.solve(hess, X.T @ (w * (y - p)) - pen @ beta)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    return beta


def _auc(scores: list[float], labels: list[int]) -> float | None:
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return None
    from scipy.stats import mannwhitneyu
    return float(mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))


def likeness(rows: list[dict]) -> dict:
    """Dansk prägel för varje dansk och svensk sten med text (0–1), tränad på samtida danska och svenska stenar."""
    import numpy as np
    keys = [k for k, _ in FEATURES]
    cand = [r for r in rows if r["ft"] is not None and r["land"] in ("danmark", "sverige")]
    train = [r for r in cand if r["y"] is not None and TRAIN_YEARS[0] <= r["y"] < TRAIN_YEARS[1]]
    X = lambda rs: np.array([[1.0] + [r["ft"][k] for k in keys] for r in rs])
    y = np.array([1.0 if r["land"] == "danmark" else 0.0 for r in train])
    n1, n0 = y.sum(), len(y) - y.sum()
    if n1 < 20 or n0 < 20:
        return {"available": False, "reason": "För få samtida danska stenar med text."}
    w = np.where(y == 1, len(y) / (2 * n1), len(y) / (2 * n0))
    Xt = X(train)
    beta = _fit(Xt, y, w)
    score = {}
    # Out of fold for the training stones: five folds by the signum, so that the result is the same every time
    fold = np.array([zlib.crc32(r["s"].encode()) % 5 for r in train])
    for f in range(5):
        b = _fit(Xt[fold != f], y[fold != f], w[fold != f])
        for r, s in zip([r for r, ff in zip(train, fold) if ff == f], 1 / (1 + np.exp(-Xt[fold == f] @ b))):
            score[r["s"]] = float(s)
    rest = [r for r in cand if r["s"] not in score]
    if rest:
        for r, s in zip(rest, 1 / (1 + np.exp(-X(rest) @ beta))):
            score[r["s"]] = float(s)
    auc = _auc([score[r["s"]] for r in train], [int(r["land"] == "danmark") for r in train])
    dk = [r for r in train if r["land"] == "danmark"]
    se = [r for r in train if r["land"] == "sverige"]
    feats = [{"key": k, "label": l, "or": round(math.exp(beta[i + 1]), 2),
              "dk": round(sum(r["ft"][k] for r in dk) / len(dk), 3), "se": round(sum(r["ft"][k] for r in se) / len(se), 3)}
             for i, (k, l) in enumerate(FEATURES)]
    return {"available": True, "score": score, "auc": None if auc is None else round(auc, 3),
            "n_train_dk": int(n1), "n_train_se": int(n0), "features": feats, "years": list(TRAIN_YEARS)}


def _row_brief(r: dict, rec: dict, score: float, keys: list[str]) -> dict:
    return {"signum": r["s"], "realm": r["rike"], "province": province(rec), "year": r["y"], "score": round(score, 3),
            "style": rec.get("style") or "", "carvers": certain_carvers(rec),
            "place": rec.get("place") or "", "features": [k for k in keys if r["ft"][k]]}


def crossborder(rows: list[dict], recs: dict[str, dict], like: dict) -> dict:
    """Rundatas anmärkningar om ett annat lands runor eller språk, texter som nämner ett annat nordiskt land och, ur
    den danska prägeln, de svenska stenar, trakter, stilgrupper och ristare som liknar danska stenar mest."""
    remarks, mentions = [], []
    for r in rows:
        rec = recs[r["s"]]
        text = " ".join(x for x in (rec.get("other"), rec.get("carver_raw")) if x)
        if REMARK.search(text):
            remarks.append({"signum": r["s"], "land": r["land"], "year": r["y"], "text": text[:400]})
        tr = rec.get("translation_en") or ""
        for land, rx in MENTIONS.items():
            m = rx.search(tr)
            if land != r["land"] and m:
                mentions.append({"signum": r["s"], "land": r["land"], "names": land, "year": r["y"],
                                 "text": tr[max(0, m.start() - 120):m.end() + 120].strip()})
    out = {"remarks": sorted(remarks, key=lambda x: (x["year"] or 9999, x["signum"])),
           "mentions": sorted(mentions, key=lambda x: (x["year"] or 9999, x["signum"])), "likeness": None}
    if not like.get("available"):
        out["likeness"] = like
        return out
    score, keys = like["score"], [k for k, _ in FEATURES]
    told = [r for r in rows if r["s"] in score and sum(r["ft"].values()) >= MIN_FEATURES]
    se = [r for r in told if r["land"] == "sverige"]
    soil = [r for r in se if r["rike"] in SWEDISH_SOIL]

    def summary(rs: list[dict]) -> dict:
        s = sorted(score[r["s"]] for r in rs)
        return {"n": len(s), "mean": round(sum(s) / len(s), 3) if s else None,
                "danish": sum(1 for x in s if x >= 0.5)}

    by_realm = [{"key": g, "label": l, **summary([r for r in se if r["rike"] == g])}
                for g, l, _ in REALMS_1025 if any(r["rike"] == g for r in se)]
    styles = [s for s in ("RAK", "Fp", "KB", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5") if s in BY_CODE]
    by_style = [{"key": s, "years": f"{BY_CODE[s]['from']}–{BY_CODE[s]['to']}" if BY_CODE[s].get("from") else "",
                 **summary([r for r in soil if recs[r["s"]].get("style") == s and not recs[r["s"]].get("style_uncertain")])}
                for s in styles]
    dk_rows = [r for r in told if r["land"] == "danmark"]
    by_dk = [{"key": g, "label": l, **summary([r for r in dk_rows if r["rike"] == g])}
             for g, l, _ in REALMS_1025 if g.startswith("dk_")]
    carvers: dict[str, list[dict]] = {}
    for r in soil:
        for c in certain_carvers(recs[r["s"]]):
            carvers.setdefault(c, []).append(r)
    carver_rows = []
    for c, rs in carvers.items():
        if len(rs) < 3:
            continue
        ys = sorted(r["y"] for r in rs if r["y"] is not None)
        carver_rows.append({"carver": c, **summary(rs), "first_year": ys[0] if ys else None,
                            "provinces": sorted({province(recs[r["s"]]) for r in rs}),
                            "top": sorted((r["s"] for r in rs), key=lambda s: -score[s])[:3]})
    carver_rows.sort(key=lambda x: -(x["mean"] or 0))
    danish_soil = sorted([r for r in soil if score[r["s"]] >= 0.5], key=lambda r: (r["y"] or 9999, -score[r["s"]]))
    # A check the model never saw: the Danish stones that Rundata's remarks call Swedish-made or Swedish-influenced
    # should look more Swedish than the other Danish stones
    remarked = {x["signum"] for x in remarks if x["land"] == "danmark" and SWEDISH_MADE.search(x["text"])}
    flagged = [r for r in dk_rows if r["s"] in remarked]
    others = [r for r in dk_rows if r["s"] not in remarked]
    check = None
    if len(flagged) >= 3 and others:
        from scipy.stats import mannwhitneyu
        order = sorted(dk_rows, key=lambda r: score[r["s"]])
        check = {"n": len(flagged), "mean": round(sum(score[r["s"]] for r in flagged) / len(flagged), 3),
                 "mean_others": round(sum(score[r["s"]] for r in others) / len(others), 3),
                 "p": float(mannwhitneyu([score[r["s"]] for r in flagged], [score[r["s"]] for r in others],
                                         alternative="less").pvalue),
                 "stones": [{"signum": r["s"], "score": round(score[r["s"]], 3),
                             "rank": order.index(r) + 1} for r in sorted(flagged, key=lambda r: score[r["s"]])],
                 "of": len(dk_rows)}
    out["likeness"] = {
        **{k: like[k] for k in ("available", "auc", "n_train_dk", "n_train_se", "features", "years")},
        "min_features": MIN_FEATURES, "n_told": len(told), "check": check,
        "by_realm": by_realm, "by_style": by_style, "by_danish_realm": by_dk,
        "carvers": carver_rows[:20], "n_carvers": len(carver_rows),
        "most_danish": [_row_brief(r, recs[r["s"]], score[r["s"]], keys)
                        for r in sorted(soil, key=lambda r: -score[r["s"]])[:20]],
        "earliest_danish": [_row_brief(r, recs[r["s"]], score[r["s"]], keys) for r in danish_soil if r["y"]][:15],
        "most_swedish_dk": [_row_brief(r, recs[r["s"]], score[r["s"]], keys)
                            for r in sorted(dk_rows, key=lambda r: score[r["s"]])[:12]],
    }
    return out


def build(inscriptions: list[dict]) -> dict:
    """Stenarna (med plats där den finns), mönstren, jämförelserna per gruppering och dragen över gränserna."""
    rows, recs, extra = [], {}, extra_places()
    for rec in inscriptions:
        if not is_runestone(rec):
            continue
        ft = features(rec)
        y = year_of(rec)
        lat, lon, how = rec.get("lat"), rec.get("lon"), "rundata"
        if lat is None and rec["signum"] in extra:
            lat, lon, how = extra[rec["signum"]]
        rows.append({"s": rec["signum"], "land": land_of(rec), "rike": realm_of(rec), "y": y, "bin": bin_of(y),
                     "ft": ft, "v": patterns(rec, ft), "how": how if lat is not None else None,
                     "lat": None if lat is None else round(lat, 4), "lon": None if lon is None else round(lon, 4)})
        recs[rec["signum"]] = rec
    like = likeness(rows)
    # Danish likeness as a pattern of its own, for the stones with enough of the features (Danish and Swedish)
    score = like.get("score", {})
    for r in rows:
        told = r["s"] in score and sum(r["ft"].values()) >= MIN_FEATURES
        r["v"]["dansk"] = int(score[r["s"]] >= 0.5) if told else None
    patterns_ = PATTERNS + [LIKENESS_PATTERN]
    keys = [k for k, *_ in patterns_]
    return {
        "patterns": [{"key": k, "label": l, "group": g, "help": h} for k, l, g, h in patterns_],
        "not_comparable": [{"label": l, "why": w} for l, w in NOT_COMPARABLE],
        "groupings": {g: [{"key": k, "label": l, "realm": r} for k, l, r in v] for g, v in GROUPINGS.items()},
        "bins": [{"key": k, "label": l} for k, l, *_ in BINS],
        "counts": {land: sum(1 for r in rows if r["land"] == land) for land, *_ in LANDS},
        "with_text": {land: sum(1 for r in rows if r["land"] == land and r["ft"] is not None) for land, *_ in LANDS},
        "with_place": {land: sum(1 for r in rows if r["land"] == land and r["lat"] is not None) for land, *_ in LANDS},
        # Of those, placed by scripts/fetch_dk_remains.py: the registered runestone, the parish church or the village
        "placed": {k: sum(1 for r in rows if r["how"] == k) for k in ("ff", "kyrka", "ort")},
        "dated": {land: sum(1 for r in rows if r["land"] == land and r["bin"]) for land, *_ in LANDS},
        # The stones as arrays in the order of the patterns, as on the pattern map
        "stones": [{"s": r["s"], "lat": r["lat"], "lon": r["lon"], "l": r["land"], "r": r["rike"], "y": r["y"],
                    "v": [r["v"][k] for k in keys]} for r in rows],
        "compare": {g: {k: compare(rows, k, g) for k in keys} for g in GROUPINGS},
        "crossborder": crossborder(rows, recs, like),
    }
