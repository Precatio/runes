"""Runinskrifterna på de brittiska öarna (England, Irland, Skottland med Orkney och Shetland, Isle of Man) ur Rundata:
vad de handlar om, vem som minns vem, vilka runor och namn, och de skandinaviska stenar som nämner öarna.
Skriver utdata/brittiska/analys.json. Kodningen av innehållet står i kodning.csv (en rad per vikingatida inskrift).

  .venv/bin/python utdata/brittiska/analys.py
"""
import csv
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scipy.stats import fisher_exact  # noqa: E402

from api.rundata import store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
AREA = {"E": "England", "IR": "Irland", "Sc": "Skottland", "Or": "Orkney", "Sh": "Shetland", "IM": "Isle of Man"}
SWEDEN = {"U", "Sö", "Ög", "Öl", "Vg", "Sm", "G", "Vs", "Gs", "Nä", "Hs", "M", "Ån", "J", "D", "Vr", "Bo", "Hr", "Ds", "Up", "Me", "Lp"}
FEM_REL = r"mother|daughter|wife|sister|housewife|stepmother|mother-in-law|daughter-in-law|foster-mother|foster-daughter|niece|grand-daughter|granddaughter|foster\(-mother"
MAL_REL = r"father|son|brother|husband|husbandman|kinsman|nephew|step-son|stepson|son-in-law|father-in-law|brother-in-law|foster-son|foster-father|grandson|grandfather|uncle|partner|comrade|master|lord|brothers|sons"


def region(signum: str) -> str | None:
    pre = signum.split(" ")[0]
    if pre in AREA:
        return "Brittiska öarna"
    if pre == "DR":
        return "Danmark"
    if pre == "N":
        return "Norge"
    if pre in SWEDEN:
        return "Sverige"
    return None


def commemorated(t: str) -> str | None:
    """Who the monument is in memory of, by the first relationship word after 'in memory of' (as in the women article,
    utdata/blogg/build/kvinnor.py): 'k' a woman, 'm' a man, None when no relationship is stated."""
    t = re.sub(r"§[A-Z]+\s*", "", t or "").replace("(", "").replace(")", "").replace("?", "")
    m = re.search(r"(?:in memory of|for)\b(.{0,90})", t, re.I)
    if not m:
        return None
    rel = re.search(rf"\b(?:his|her|their|\w+'s)\s+(?:[a-z-]+\s+)?({FEM_REL}|{MAL_REL})\b", m.group(1))
    if not rel:
        return None
    return "k" if re.fullmatch(FEM_REL, rel.group(1)) else "m"


def main():
    recs = store().inscriptions
    out = {}
    # 1. The corpus of the British Isles
    bi = [r for r in recs if r["signum"].split(" ")[0] in AREA]
    out["n"] = len(bi)
    out["by_area_period"] = Counter(f"{AREA[r['signum'].split(' ')[0]]}|{r.get('period') or '?'}" for r in bi)
    v = [r for r in bi if r.get("period") == "V"]
    out["viking"] = len(v)
    out["rune_types_viking"] = Counter((r.get("rune_types") or "ej angivet") for r in v)
    out["objects_viking"] = Counter((r.get("object") or "?") for r in v)

    # 2. Who is remembered: women among the monuments that state the relationship, by region (Viking Age)
    mem = {}
    for r in recs:
        if r.get("period") != "V":
            continue
        reg = region(r["signum"])
        if reg is None:
            continue
        if reg != "Brittiska öarna" and "runsten" not in (r.get("object") or "").lower():
            continue  # Scandinavia: runestones (the default object); the islands: every memorial, stated in the text
        g = commemorated(r.get("translation_en"))
        if g:
            key = "Isle of Man" if r["signum"].startswith("IM ") else reg
            mem.setdefault(key, Counter())[g] += 1
            if reg == "Brittiska öarna":
                mem.setdefault("Brittiska öarna utom Man", Counter())[g] += 0 if r["signum"].startswith("IM ") else 1
                mem.setdefault("Brittiska öarna alla", Counter())[g] += 1
    out["women_commemorated"] = {k: {"women": c["k"], "men": c["m"], "share": c["k"] / max(1, c["k"] + c["m"])} for k, c in mem.items()}
    tests = {}
    for other in ("Norge", "Sverige", "Danmark"):
        a, b = mem["Isle of Man"], mem[other]
        odds, p = fisher_exact([[a["k"], a["m"]], [b["k"], b["m"]]])
        tests[f"Isle of Man mot {other}"] = {"odds_ratio": odds, "p": p}
        a = mem["Brittiska öarna alla"]
        odds, p = fisher_exact([[a["k"], a["m"]], [b["k"], b["m"]]])
        tests[f"Brittiska öarna mot {other}"] = {"odds_ratio": odds, "p": p}
    out["women_tests"] = tests

    # 3. The Scandinavian runestones that name the islands (Viking Age), per country and per 1 000 stones
    pats = {"England": r"\bengland", "Irland": r"\bireland\b|\birland", "Skottland": r"\bscotland|\bskotland"}
    stones, named = Counter(), Counter()
    names = []
    for r in recs:
        reg = region(r["signum"])
        if r.get("period") != "V" or reg in (None, "Brittiska öarna") or "runsten" not in (r.get("object") or "").lower():
            continue
        stones[reg] += 1
        t = (r.get("translation_en") or "").lower()
        for place, pat in pats.items():
            if re.search(pat, t):
                named[(reg, place)] += 1
                names.append({"signum": r["signum"], "region": reg, "place": place, "style": r.get("style"),
                              "translation": r.get("translation_en")})
    out["scandinavian_stones"] = dict(stones)
    out["naming_islands"] = {f"{a}|{b}": n for (a, b), n in named.items()}
    out["naming_islands_list"] = names

    # 4. The content coding (kodning.csv): category, names and their origin
    path = os.path.join(HERE, "kodning.csv")
    if os.path.exists(path):
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        out["categories"] = Counter(r["kategori"] for r in rows)
        out["categories_by_area"] = Counter(f"{r['omrade']}|{r['kategori']}" for r in rows)
        nm = Counter()
        for r in rows:
            for part in filter(None, r["namn"].split(";")):
                name, origin = part.split(":")
                nm[origin] += 1
        out["name_origins"] = nm
        out["gaelic_in"] = [r["signum"] for r in rows if ":gaeliskt" in r["namn"]]
        out["mixed"] = [r["signum"] for r in rows if ":gaeliskt" in r["namn"] and ":nordiskt" in r["namn"]]
    json.dump(out, open(os.path.join(HERE, "analys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=dict)
    print(json.dumps({k: out[k] for k in ("n", "viking", "women_commemorated", "women_tests", "scandinavian_stones",
                                         "naming_islands")}, ensure_ascii=False, indent=1, default=dict))


if __name__ == "__main__":
    main()
