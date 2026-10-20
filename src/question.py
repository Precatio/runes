"""Pröva en egen fråga (Statistik i R; METHODS.md 1y, IMPLEMENTATIONSPLAN.md 3.6).

En forskare väljer ett drag A (tro, skrift, innehåll, ristare) och något att jämföra med: ett annat drag B, ett
landskap, en tidsgräns eller en bergartsfamilj. Svaret är andelen stenar med A där B gäller mot där det inte gäller,
med samma disciplin som kartans Upptäck och R-modulerna – ingen fri text och ingen AI:

  * Bara runstenar, samma rader som korpusanalyserna i R (src/r_bridge.corpus_rows). Stenar där A eller B inte kan
    avgöras (oläslig text, ingen säker stilgrupp för en tidsfråga, okänd bergart) räknas inte.
  * Justerat för det som annars styr de flesta drag: landskap och tid. Mantel–Haenszel över skikt av landskap ×
    tidsskikt (stilgruppens datering i fyra skikt, och odaterade stenar som ett eget skikt); för ett landskap justeras
    bara för tiden, för en tidsgräns bara för landskapet. Oddskvot med 95 %-intervall (Robins–Breslow–Greenland) och
    CMH-test med kontinuitetskorrektion.
  * Halvprovet: socknarna delas i två halvor inom varje landskap, hela socknar växelvis i ordning efter deras
    medeldatering, som i r/change.R och r/hotspots.R. Halvorna bestäms en gång för hela korpusen, oberoende av frågan.
    Ett mönster håller bara om det har samma riktning och p < 0,05 i båda.
  * Ristarprovet: frågan räknas om utan var och en av de fem ristare som har flest stenar i underlaget; den sämsta
    utgången redovisas, så att en flitig ristares vanor inte blir hela mönstret.
  * Många frågor: p-värdena för de frågor som ställts tidigare under besöket skickas med och BH-justeras tillsammans
    med den nya, så att den som prövar tjugo frågor ser vad det kostar.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

from src import geology
from src.nordic import wilson
from src.research_gaps import PROVINCE_NAMES
from src.stone_size import bh

MIN_GROUP = 10   # stenar på var sida om jämförelsen
MIN_TRAIT = 5    # stenar med och utan draget
MIN_PROVINCE = 15
ALPHA = 0.05
N_CARVERS = 5
SPLITS = (1020, 1050, 1075)  # samma tidsgränser som kartan (web/src/lib/patternMap.ts)


def _pm(key):
    return lambda r: None if r.get(f"pm_{key}") in ("", None) else int(r[f"pm_{key}"])


def _trait(key, yes, no):
    def get(r):
        v = r.get(f"trait_{key}") or ""
        return 1 if v in yes else (0 if v in no else None)
    return get


def _cat(key):
    # a category can only be decided where the text is legible (the map's bro pattern is None otherwise)
    return lambda r: None if r.get("pm_bro") in ("", None) else int(r[f"cat_{key}"])


# key, label, group, help, value(row) -> 1, 0 or None
VARIABLES = [
    ("kristen", "Kristna markörer", "Tro", "Kors eller kristen bön eller formel.", _pm("kristen")),
    ("hednisk", "Hedniska eller rituella markörer", "Tro",
     "Torsåkallan, vígi-formler, förbannelser, alu eller Tormotiv. Få stenar.", _pm("hednisk")),
    ("neutral", "Utan religiösa markörer", "Tro", "Varken kristna eller hedniska markörer.", _pm("neutral")),
    ("bon", "Kristen bön", "Tro", "Bön som Guð hjalpi and hans (stenar med läsbar text).", _pm("bon")),
    ("sjal", "Själsbön", "Tro", "Bön som nämner själen.", _pm("sjal")),
    ("kors", "Kors", "Tro", "Kors i ornamentiken enligt Rundata.", _pm("kors")),
    ("stungna", "Stungna runor", "Skrift", "Stungna runor (e, g, d, y) i inskriften.", _pm("stungna")),
    ("monoftong", "Monoftong (stin)", "Skrift", "Monoftong i något ai-ord, t.ex. stin för stain.", _pm("monoftong")),
    ("o_runa", "o-runan för o", "Skrift", "o-ljudet skrivet med o-runan i stället för u-runan.", _pm("o_runa")),
    ("r_for_R", "r för ʀ", "Skrift", "ʀ skrivet med r-runan i ord som æftiʀ.", _pm("r_for_R")),
    ("auk", "auk för 'och'", "Skrift", "Konjunktionen ok skriven auk (diftong) mot uk/ok/ak.",
     _trait("au_och", {"auk"}, {"monoftong"})),
    ("at", "at i minnesformeln", "Skrift", "Minnesformeln med at (före namnet) mot bara æftiR.",
     _trait("preposition", {"at", "båda"}, {"æftiR"})),
    ("h_skrivet", "h skrivet", "Skrift", "h skrivet i början av hans, hialpi m.fl. mot h som saknas.",
     _trait("h_bortfall", {"h skrivet"}, {"h saknas"})),
    ("nasal", "Nasal skriven", "Skrift", "n/m skrivet före homorgan konsonant (bonta) mot utelämnat (buta).",
     _trait("nasal", {"skriven"}, {"utelämnad"})),
    ("bindrunor", "Bindrunor", "Skrift", "Två runor på samma huvudstav.", _trait("bindrunor", {"ja"}, {"nej"})),
    ("signatur", "Ristarsignatur", "Skrift", "Ristarformel i texten, t.ex. risti, hjó.", _pm("signatur")),
    ("bro", "Bro- och vägbygge", "Innehåll", "Nämner en bro eller väg som byggts.", _pm("bro")),
    ("fard", "Utlandsfärd", "Innehåll", "Nämner resa, död eller strid utomlands.", _pm("fard")),
    ("arv", "Arv och ägande", "Innehåll", "Uppgifter om arv, ägande eller gård.", _pm("arv")),
    ("sjalvminne", "Självminne", "Innehåll", "Rest till minne av sig själv eller medan resaren levde.",
     _cat("sjalvminne")),
    ("ristare_kand", "Ristare i Rundata", "Ristare", "Rundata anger en ristare, säker eller osäker.",
     lambda r: int(r["has_carver"])),
    ("signerad", "Signerad", "Ristare", "Ristaren har signerat stenen (säker signatur enligt Rundata).",
     lambda r: int(r["signed"])),
]
VAR = {k: (label, group, help_, fn) for k, label, group, help_, fn in VARIABLES}

# Pairs where one is part of the other's definition: a "finding" would only restate the definition
LINKED = {
    frozenset({"kristen", "bon"}): "Kristna markörer räknar in kristen bön.",
    frozenset({"kristen", "sjal"}): "Kristna markörer räknar in själsbönen.",
    frozenset({"kristen", "kors"}): "Kristna markörer räknar in korset.",
    frozenset({"kristen", "neutral"}): "Utan religiösa markörer betyder utan kristna markörer.",
    frozenset({"hednisk", "neutral"}): "Utan religiösa markörer betyder utan hedniska markörer.",
    frozenset({"bon", "sjal"}): "Själsbönen är en sorts kristen bön.",
    frozenset({"signatur", "signerad"}): "En signerad sten är en sten vars ristarformel nämner ristaren.",
    frozenset({"ristare_kand", "signerad"}): "En signerad sten har alltid en ristare i Rundata.",
}

EPOCHS = ("före 1020", "1020–1050", "1050–1075", "1075 och senare")


def mid_year(r: dict) -> float | None:
    if r.get("style_from") is None or r.get("style_to") is None:
        return None
    return (r["style_from"] + r["style_to"]) / 2


def epoch(r: dict) -> str:
    y = mid_year(r)
    if y is None:
        return "odaterad"
    return EPOCHS[sum(y >= s for s in SPLITS)]


def family(r: dict) -> str | None:
    fams = sorted(geology.families(r.get("material") or ""))
    return fams[0] if fams else None


def halves(rows: list[dict]) -> dict[str, str]:
    """Signum -> halva (A/B): hela socknar växelvis inom varje landskap, i ordning efter socknens medeldatering
    (odaterade socknar sist, större före mindre), som i r/change.R."""
    groups: dict[tuple[str, str], list[float | None]] = defaultdict(list)
    for r in rows:
        pk = r.get("parish") or f"_{r['signum']}"
        y = mid_year(r)
        groups[(r["province"], pk)].append(None if y is None else (y - 1050) / 50)
    order: dict[str, list[tuple]] = defaultdict(list)
    for (prov, pk), ts in groups.items():
        known = [t for t in ts if t is not None]
        mt = sum(known) / len(known) if known else None
        order[prov].append((mt is None, mt if mt is not None else 0.0, -len(ts), pk))
    half: dict[tuple[str, str], str] = {}
    for prov, items in order.items():
        for i, item in enumerate(sorted(items)):
            half[(prov, item[3])] = "A" if i % 2 == 0 else "B"
    return {r["signum"]: half[(r["province"], r.get("parish") or f"_{r['signum']}")] for r in rows}


def prepare(rows: list[dict]) -> dict:
    """Det frågorna behöver ur korpusraderna, räknat en gång: värdena för varje drag, skikt, halvor och ristare."""
    h = halves(rows)
    stones = []
    for r in rows:
        stones.append({"signum": r["signum"], "province": r["province"], "epoch": epoch(r), "year": mid_year(r),
                       "family": family(r), "half": h[r["signum"]], "carver": r.get("carver") or "",
                       "v": {k: fn(r) for k, (_, _, _, fn) in VAR.items()}})
    return {"stones": stones}


def options(prep: dict) -> dict:
    """Det som går att välja: dragen med antal stenar, landskap, tidsgränser och bergartsfamiljer."""
    st = prep["stones"]
    prov = Counter(s["province"] for s in st)
    fam = Counter(s["family"] for s in st if s["family"])
    return {
        "variables": [{"key": k, "label": label, "group": group, "help": help_,
                       "n": sum(s["v"][k] is not None for s in st), "k": sum(s["v"][k] == 1 for s in st)}
                      for k, label, group, help_, _ in VARIABLES],
        "provinces": [{"key": p, "label": PROVINCE_NAMES.get(p, p), "n": n} for p, n in prov.most_common()
                      if n >= MIN_PROVINCE and p in PROVINCE_NAMES and p != "SE"],
        "splits": [{"year": y, "n_before": sum(s["year"] is not None and s["year"] < y for s in st),
                    "n_after": sum(s["year"] is not None and s["year"] >= y for s in st)} for y in SPLITS],
        "families": [{"key": f, "label": geology.FAMILY_LABEL.get(f, f), "n": n} for f, n in fam.most_common()
                     if n >= MIN_GROUP],
        "n_stones": len(st),
    }


def mantel_haenszel(tables: list[tuple[int, int, int, int]]) -> dict:
    """Oddskvot över skikt (a = A och B, b = inte A men B, c = A utan B, d = varken), 95 %-intervall enligt
    Robins–Breslow–Greenland, CMH-test med kontinuitetskorrektion och riktning (observerat mot väntat a)."""
    from scipy.stats import chi2
    sr = ss = spr = sps_qr = sqs = 0.0
    sa = ea = va = 0.0
    used = 0
    for a, b, c, d in tables:
        n = a + b + c + d
        if a + b == 0 or c + d == 0 or a + c == 0 or b + d == 0 or n < 2:
            continue  # a stratum without both groups or without both values says nothing about the association
        used += 1
        r_, s_ = a * d / n, b * c / n
        p_, q_ = (a + d) / n, (b + c) / n
        sr += r_
        ss += s_
        spr += p_ * r_
        sps_qr += p_ * s_ + q_ * r_
        sqs += q_ * s_
        m1, m0, k1 = a + b, c + d, a + c
        sa += a
        ea += m1 * k1 / n
        va += m1 * m0 * k1 * (n - k1) / (n * n * (n - 1))
    if not used or va <= 0:
        return {"or": None, "ci": None, "p": None, "direction": 0, "strata": used}
    p = float(chi2.sf(max(0.0, abs(sa - ea) - 0.5) ** 2 / va, 1))
    direction = 1 if sa > ea else (-1 if sa < ea else 0)
    if sr <= 0 or ss <= 0:  # every stratum one-sided: the odds ratio is 0 or infinite, the test still holds
        return {"or": None, "ci": None, "p": p, "direction": direction, "strata": used}
    or_ = sr / ss
    var = spr / (2 * sr * sr) + sps_qr / (2 * sr * ss) + sqs / (2 * ss * ss)
    se = math.sqrt(var)
    return {"or": or_, "ci": (or_ * math.exp(-1.96 * se), or_ * math.exp(1.96 * se)), "p": p,
            "direction": direction, "strata": used}


def _tables(items: list[tuple[str, int, int]]) -> list[tuple[int, int, int, int]]:
    cells: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for stratum, x, y in items:
        cells[stratum][(1 - x) * 2 + (1 - y)] += 1  # [x=1,y=1], [x=1,y=0], [x=0,y=1], [x=0,y=0]
    return [tuple(c) for c in cells.values()]


def _share(items) -> dict:
    n = len(items)
    k = sum(y for _, _, y in items)
    lo, hi = wilson(k, n)
    return {"n": n, "k": k, "share": k / n if n else None, "ci": [lo, hi]}


def _newcombe(k1: int, n1: int, k0: int, n0: int) -> list[float]:
    """95 %-intervall för skillnaden mellan två andelar (Newcombes hybridmetod med Wilsons intervall)."""
    p1, p0 = k1 / n1, k0 / n0
    l1, u1 = wilson(k1, n1)
    l0, u0 = wilson(k0, n0)
    d = p1 - p0
    return [d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)]


def comparison(kind: str, key) -> dict:
    """Vad A jämförs med: etiketten, värdet (1, 0 eller None) per sten och vad som justeras för."""
    if kind == "drag":
        if key not in VAR:
            raise ValueError(f"Okänt drag: {key}")
        label, _, help_, _ = VAR[key]
        return {"kind": kind, "key": key, "label": label, "help": help_, "yes": f"med {label.lower()}",
                "no": f"utan {label.lower()}", "adjusted": "landskap och tid",
                "x": lambda s: s["v"][key], "stratum": lambda s: f"{s['province']}|{s['epoch']}"}
    if kind == "landskap":
        if key not in PROVINCE_NAMES or key == "SE":
            raise ValueError(f"Okänt landskap: {key}")
        name = PROVINCE_NAMES[key]
        return {"kind": kind, "key": key, "label": name, "help": "", "yes": f"i {name}", "no": "i övriga landskap",
                "adjusted": "tid", "x": lambda s: int(s["province"] == key), "stratum": lambda s: s["epoch"]}
    if kind == "tid":
        year = int(key)
        if year not in SPLITS:
            raise ValueError(f"Tidsgränsen ska vara en av {', '.join(map(str, SPLITS))}")
        return {"kind": kind, "key": year, "label": f"från {year}", "help": "Stilgruppens datering (Gräslund).",
                "yes": f"från {year}", "no": f"före {year}", "adjusted": "landskap",
                "x": lambda s: None if s["year"] is None else int(s["year"] >= year), "stratum": lambda s: s["province"]}
    if kind == "bergart":
        if key not in geology.FAMILIES:
            raise ValueError(f"Okänd bergartsfamilj: {key}")
        name = geology.FAMILY_LABEL.get(key, key)
        return {"kind": kind, "key": key, "label": name, "help": "Bergarten enligt Rundata.", "yes": f"i {name}",
                "no": "i andra bergarter", "adjusted": "landskap och tid",
                "x": lambda s: None if s["family"] is None else int(s["family"] == key),
                "stratum": lambda s: f"{s['province']}|{s['epoch']}"}
    raise ValueError(f"Okänd jämförelse: {kind}")


def ask(prep: dict, a: str, kind: str, key, earlier: list[float] | None = None, carvers: bool = True) -> dict:
    """Svaret på frågan: är A vanligare (eller ovanligare) där B gäller? Se modulens beskrivning."""
    if a not in VAR:
        raise ValueError(f"Okänt drag: {a}")
    b = comparison(kind, key)
    label_a, _, help_a, _ = VAR[a]
    out = {"a": {"key": a, "label": label_a, "help": help_a},
           "b": {k: b[k] for k in ("kind", "key", "label", "help", "yes", "no", "adjusted")}}
    if kind == "drag" and key == a:
        return {**out, "verdict": "samma", "reason": "Samma drag på båda sidor."}
    link = LINKED.get(frozenset({a, key})) if kind == "drag" else None
    if link:
        return {**out, "verdict": "kopplade", "reason": link}

    items, missing = [], 0
    by_signum = {}
    for s in prep["stones"]:
        x, y = b["x"](s), s["v"][a]
        if x is None or y is None:
            missing += 1
            continue
        items.append((b["stratum"](s), x, y))
        by_signum[s["signum"]] = (s, x, y)
    yes = [t for t in items if t[1] == 1]
    no = [t for t in items if t[1] == 0]
    with_a = sum(t[2] for t in items)
    out.update({"n": len(items), "missing": missing, "with_b": _share(yes), "without_b": _share(no)})
    if len(yes) < MIN_GROUP or len(no) < MIN_GROUP or with_a < MIN_TRAIT or len(items) - with_a < MIN_TRAIT:
        return {**out, "verdict": "för få",
                "reason": f"Minst {MIN_GROUP} stenar behövs på var sida om jämförelsen och minst {MIN_TRAIT} med och "
                          f"utan draget."}
    # Expected stones with and without A on the smaller side if A were spread evenly: below 5 the test cannot see a
    # difference even if there is one, so "no difference" would mislead
    small = min(len(yes), len(no))
    if min(small * with_a, small * (len(items) - with_a)) / len(items) < MIN_TRAIT:
        return {**out, "verdict": "för få",
                "reason": f"Draget är för ovanligt (eller för vanligt) för en så liten grupp: färre än {MIN_TRAIT} "
                          f"stenar med eller utan draget vore väntade på den mindre sidan, så provet kan inte se en "
                          f"skillnad även om den finns."}

    w, wo = out["with_b"], out["without_b"]
    out["difference"] = {"value": w["share"] - wo["share"], "ci": _newcombe(w["k"], w["n"], wo["k"], wo["n"])}
    whole = mantel_haenszel(_tables(items))
    out["adjusted"] = whole
    if whole["p"] is None:
        return {**out, "verdict": "för få", "reason": "Inget landskap eller tidsskikt har stenar på båda sidor."}

    halves_out = {}
    for h in ("A", "B"):
        sub = [(b["stratum"](s), x, y) for s, x, y in by_signum.values() if s["half"] == h]
        res = mantel_haenszel(_tables(sub))
        res["n"] = len(sub)
        res["share_with_b"] = _share([t for t in sub if t[1] == 1])["share"]
        res["share_without_b"] = _share([t for t in sub if t[1] == 0])["share"]
        halves_out[h] = res
    replicated = all(r["p"] is not None and r["p"] < ALPHA and r["direction"] == whole["direction"] != 0
                     for r in halves_out.values())
    out["halves"] = {**halves_out, "replicated": replicated}

    if carvers:
        top = Counter(s["carver"] for s, _, _ in by_signum.values() if s["carver"]).most_common(N_CARVERS)
        worst = None
        for name, n_c in top:
            sub = [(b["stratum"](s), x, y) for s, x, y in by_signum.values() if s["carver"] != name]
            res = mantel_haenszel(_tables(sub))
            if res["p"] is None:
                continue
            if worst is None or res["p"] > worst["p"]:
                worst = {"carver": name, "n": n_c, "or": res["or"], "p": res["p"],
                         "holds": res["p"] < ALPHA and res["direction"] == whole["direction"]}
        out["carver_check"] = worst

    ps = [p for p in (earlier or []) if p is not None and 0 <= p <= 1] + [whole["p"]]
    out["q"] = bh(ps)[-1]
    out["n_questions"] = len(ps)
    if whole["p"] >= ALPHA:
        verdict = "ingen skillnad"
    elif not replicated:
        verdict = "bara i hela"
    elif out["q"] >= ALPHA:
        verdict = "håller men inte justerat"
    else:
        verdict = "håller"
    out["verdict"] = verdict
    return out
