"""Runstenarnas mått ur Kulturmiljöregistret (Fornsök), via Runor och K-samsök (se METHODS.md, 9b).

Rundata saknar mått. Runor (RAÄ, utgåva 2020 av Samnordisk runtextdatabas) ger för varje inskrift id:t i
Kulturmiljöregistret, och lämningens beskrivning där anger oftast stenens mått, t.ex. "Runsten, ljus granit, 1,5 m h,
0,5-0,6 m br (Ö-V) och 0,2-0,25m tj. Runhöjd 6-8 cm." Beskrivningen hämtas via K-samsök (kulturarvsdata.se) och
måtten läses ut med reguljära uttryck. Svaren cachas i data/cache/dimensions/.

Tolkningen är försiktig: beskriver lämningen flera föremål ("1) … 2) …") används bara delen som nämner stenens
signum, eller den enda delen som är en runsten; annars räknas måtten som oklara. Fragment markeras. Höjden är
oftast höjden över mark, inte stenens hela längd.
"""
from __future__ import annotations

import json
import os
import re
import time

import requests

from src.crosscheck import RUNOR, RUNOR_EDITION, UA
from src.signum import fold_signum

CACHE = os.environ.get("DIMENSIONS_CACHE", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                        "data", "cache", "dimensions"))
KSAMSOK = "https://kulturarvsdata.se/raa/lamning/xml/{}"
SOURCE = ("Kulturmiljöregistret (Riksantikvarieämbetet) via K-samsök, länkat med Runor (Riksantikvarieämbetet, "
          "utgåva 2020 av Samnordisk runtextdatabas).")

NUM = r"(\d+(?:[,.]\d+)?)"
RANGE = NUM + r"(?:\s*[-–]\s*" + NUM + r")?"
DIM = {
    "height_m": r"(?:h\b|hög|höjd)",
    "width_m": r"(?:br\b|bred|bredd)",
    "thickness_m": r"(?:tj\b|tjock|tjocklek)",
}


def _safe(signum: str) -> str:
    return re.sub(r"[^\w]+", "_", fold_signum(signum)).strip("_")


def _cached_get(kind: str, key: str, fetch):
    path = os.path.join(CACHE, kind, f"{_safe(key)}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    data = fetch()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    time.sleep(0.15)  # be polite to RAÄ's services
    return data


def runor_ids(signum: str) -> dict:
    """Kulturmiljöregistrets id:n (kmrId) och om inskriften finns kvar, ur Runor."""
    def fetch():
        target = fold_signum(signum)
        hits = requests.get(f"{RUNOR}/search", params={"edition_id": RUNOR_EDITION, "search_field": "SIGNUM",
                                                       "matching_text": signum}, headers=UA, timeout=30)
        hits.raise_for_status()
        match = next((h for h in hits.json() if fold_signum(f"{h['signum1']} {h['signum2']}") == target), None)
        if not match:
            return {}
        d = requests.get(f"{RUNOR}/inscriptions/{match['inscription_id']}", params={"edition_id": RUNOR_EDITION},
                         headers=UA, timeout=30)
        d.raise_for_status()
        d = d.json()
        kmr = [i["value"] for h in d.get("her_identifiers") or [] for i in h.get("identifiers") or [] if i.get("key") == "kmrId"]
        return {"kmr": kmr, "extant": d.get("extant"), "artefact": d.get("artefact")}
    return _cached_get("runor", signum, fetch)


def kmr_description(kmr_id: str) -> str:
    def fetch():
        r = requests.get(KSAMSOK.format(kmr_id), headers=UA, timeout=30)
        if r.status_code == 404:
            return {"description": ""}
        r.raise_for_status()
        m = re.search(r"<pres:description>(.*?)</pres:description>", r.text, re.S)
        import html
        return {"description": html.unescape(m.group(1)).strip() if m else ""}
    return _cached_get("kmr", kmr_id, fetch)["description"]


def _value(lo: str, hi: str | None, unit: str) -> tuple[float, float, float]:
    a = float(lo.replace(",", "."))
    b = float(hi.replace(",", ".")) if hi else a
    f = 0.01 if unit == "cm" else 1.0
    return a * f, b * f, (a + b) / 2 * f


def parse(text: str, signum: str) -> dict:
    """Mått ur en beskrivning. Returnerar {height_m, width_m, thickness_m, rune_height_cm, fragment, status}."""
    if not text:
        return {"status": "saknas"}
    # Objects are numbered "1) … 2) …", sometimes without spaces ("nr 2 är2)Runsten")
    parts = [p for p in re.split(r"(?<![\d,.])\d{1,2}\)\s*", text) if p.strip()]
    if len(parts) > 1:
        folded = fold_signum(signum)
        named = [p for p in parts if folded and folded in fold_signum(p)]
        stones = [p for p in parts if re.search(r"(?i)runsten|runristad|runblock|sten med runor", p)]
        if len(named) == 1:
            seg = named[0]
        elif len(stones) == 1:
            seg = stones[0]
        else:
            return {"status": "oklar (flera föremål)"}
    else:
        seg = parts[0] if parts else text
    out: dict = {"status": "ok", "fragment": bool(re.search(r"(?i)fragment|bit av|del av runsten", seg))}
    for key, word in DIM.items():
        m = re.search(RANGE + r"\s*(m|cm)\s*" + word, seg, re.I) or re.search(word + r"\s*" + RANGE + r"\s*(m|cm)", seg, re.I)
        if m:
            lo, hi, unit = m.group(1), m.group(2), m.group(3).lower()
            vmin, vmax, mid = _value(lo, hi, unit)
            if 0.05 <= mid <= 6:  # a runestone is not 6 m or 5 cm: anything else is a parsing error
                out[key] = round(mid, 3)
                if hi:
                    out[key.replace("_m", "_range_m")] = [round(vmin, 3), round(vmax, 3)]
    m = re.search(r"(?i)run(?:höjd|ornas höjd|ornas storlek)\D{0,12}" + RANGE + r"\s*(cm|mm)", seg)
    if m:
        a, b = float(m.group(1).replace(",", ".")), float((m.group(2) or m.group(1)).replace(",", "."))
        f = 0.1 if m.group(3).lower() == "mm" else 1.0
        if 1 <= (a + b) / 2 * f <= 60:
            out["rune_height_cm"] = round((a + b) / 2 * f, 1)
    if not any(k in out for k in DIM):
        out["status"] = "inga mått"
    out["text"] = seg.strip()[:400]
    return out


def dimensions(signum: str) -> dict:
    """Stenens mått med källa, eller status om de saknas."""
    ids = runor_ids(signum)
    if not ids.get("kmr"):
        return {"status": "inget id i Kulturmiljöregistret"}
    best = None
    for k in ids["kmr"]:
        d = parse(kmr_description(k), signum)
        d["kmr_url"] = f"https://kulturarvsdata.se/raa/lamning/{k}"
        if d["status"] == "ok":
            return d
        best = best or d
    return best


DATA = os.environ.get("DIMENSIONS_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                      "data", "stone_dimensions.json"))


def load() -> dict:
    """data/stone_dimensions.json (scripts/build_stone_dimensions.py); tomt om filen saknas."""
    global _loaded
    try:
        mtime = os.path.getmtime(DATA)
    except OSError:
        return {"meta": {}, "stones": {}}
    if _loaded is None or _loaded[0] != mtime:
        _loaded = (mtime, json.load(open(DATA, encoding="utf-8")))
    return _loaded[1]


_loaded = None


def lookup(signum: str) -> dict | None:
    """Stenens mått med källa, eller None om inga säkra mått finns."""
    d = (load().get("stones") or {}).get(signum)
    if not d or d.get("status") != "ok":
        return None
    return {**{k: v for k, v in d.items() if k != "text"}, "description": d.get("text"), "source": SOURCE}


def province_percentile(signum: str, province_of) -> dict | None:
    """Hur hög stenen är jämfört med andra runstenar med kända mått i samma landskap."""
    me = lookup(signum)
    if not me or not me.get("height_m") or me.get("fragment"):
        return None
    stones = load().get("stones") or {}
    prov = province_of(signum)
    heights = [d["height_m"] for s, d in stones.items() if d.get("status") == "ok" and d.get("height_m")
               and not d.get("fragment") and province_of(s) == prov]
    if len(heights) < 10:
        return None
    below = sum(1 for h in heights if h < me["height_m"]) + 0.5 * sum(1 for h in heights if h == me["height_m"])
    return {"province": prov, "n": len(heights), "percentile": round(100 * below / len(heights)),
            "median_m": sorted(heights)[len(heights) // 2]}
