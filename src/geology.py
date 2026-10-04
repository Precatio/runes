"""Berggrunden där en runsten står, ur SGU:s berggrundskarta (WMS GetFeatureInfo).

Rundatas materialuppgift (t.ex. "röd granit", "gråsten", "kalksten") jämförs med berggrunden på platsen
och inom en radie. Jämförelsen görs på bergartsfamiljer, eftersom Rundatas uppgifter är fältbenämningar
och SGU:s är petrografiska enheter.

Källkritik: många runstenar är flyttblock som isen transporterat, eller har fraktats dit av människor
(t.ex. sandsten från Gävletrakten eller kalksten från Öland och Gotland). Att bergarten saknas i
berggrunden runt platsen betyder därför inte att uppgiften är fel – men det är en uppgift om stenens
ursprung som kan vara värd att undersöka. SGU:s karta täcker bara Sverige.
"""
from __future__ import annotations

import json
import math
import os
import re
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import requests

WMS_URL = "https://maps3.sgu.se/geoserver/berg/ows"
LAYER = "SE.GOV.SGU.BERG.GEOLOGISK_ENHET.YTA.50K"
SOURCE = "Sveriges geologiska undersökning (SGU), Berggrund 1:50 000–1:250 000 (visningstjänst)."
CACHE_PATH = os.environ.get("GEOLOGY_CACHE", os.path.join(os.path.dirname(__file__), "..", "data", "cache", "geology.json"))

# Rock families; both Rundata's field names and SGU's rock names are matched by keyword
FAMILIES = {
    "granitoid": ("granit", "granodiorit", "tonalit", "pegmatit", "aplit", "monzonit", "syenit", "kvartsdiorit",
                  "charnockit", "gråsten", "gnejsgranit", "granitgnejs"),
    "gnejs": ("gnejs", "migmatit", "gråsten", "gnejsgranit", "granitgnejs"),
    "sandsten": ("sandsten", "arenit", "arkos", "konglomerat", "siltsten", "gävlesandsten"),
    "kalksten": ("kalksten", "märgel", "dolomit", "marmor"),
    "basisk": ("diabas", "gabbro", "basalt", "amfibolit", "dolerit", "diorit"),
    "vulkanisk": ("ryolit", "dacit", "porfyr", "andesit", "vulkanit", "leptit"),
    "kvartsit": ("kvartsit",),
    "metasediment": ("vacka", "skiffer", "fyllit", "lersten", "metasediment", "glimmerskiffer"),
}
FAMILY_LABEL = {
    "granitoid": "granit och närstående", "gnejs": "gnejs och migmatit", "sandsten": "sandsten",
    "kalksten": "kalksten och marmor", "basisk": "basiska bergarter (diabas, gabbro, amfibolit)",
    "vulkanisk": "vulkaniska bergarter (porfyr, ryolit)", "kvartsit": "kvartsit",
    "metasediment": "metasediment (gråvacka, skiffer)",
}

_lock = threading.Lock()
_cache: dict | None = None


def families(text: str) -> set[str]:
    t = (text or "").lower()
    return {fam for fam, words in FAMILIES.items() if any(w in t for w in words)}


def _load_cache() -> dict:
    global _cache
    if _cache is None:
        try:
            with open(CACHE_PATH, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False)
    except OSError:
        pass


def query_point(lat: float, lon: float, timeout: float = 10.0) -> dict | None:
    """Den geologiska enheten i en punkt (WGS84), eller None om kartan saknar data där."""
    key = f"{lat:.4f},{lon:.4f}"
    with _lock:
        cache = _load_cache()
        if key in cache:
            return cache[key]
    d = 0.001
    params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo", "LAYERS": LAYER, "QUERY_LAYERS": LAYER,
        "CRS": "EPSG:4326", "BBOX": f"{lat - d},{lon - d},{lat + d},{lon + d}", "WIDTH": 101, "HEIGHT": 101,
        "I": 50, "J": 50, "INFO_FORMAT": "application/json", "STYLES": "", "FEATURE_COUNT": 1,
    }
    r = requests.get(WMS_URL, params=params, timeout=timeout)
    r.raise_for_status()
    feats = r.json().get("features") or []
    out = None
    if feats:
        p = feats[0]["properties"]
        out = {"rock": _clean(p.get("bergart_tx")), "unit": _clean(p.get("geo_enh_tx")),
               "minerals": _clean(p.get("min_ss_tx")), "texture": _clean(p.get("str_tx_tx")),
               "colour": _clean(p.get("farg_tx"))}
    with _lock:
        _load_cache()[key] = out
    return out


def _clean(text) -> str:
    """SGU's fields use placeholders like 'Null:okänt' for missing parts; leave them out."""
    cleaned = re.sub(r"\s*[;,]?\s*Null:[^;,]*", "", str(text or ""))
    return cleaned.strip(" ;,")


def _grid(lat: float, lon: float, radius_km: float, step_km: float) -> list[tuple[float, float]]:
    pts = []
    n = int(radius_km // step_km)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            dy, dx = i * step_km, j * step_km
            if dx * dx + dy * dy <= radius_km * radius_km:
                pts.append((lat + dy / 111.0, lon + dx / (111.0 * math.cos(math.radians(lat)))))
    return pts


def enabled() -> bool:
    # Tests and offline use set GEOLOGY_DISABLED=1
    return os.environ.get("GEOLOGY_DISABLED", "") not in ("1", "true")


def bedrock(lat: float, lon: float, material: str = "", radius_km: float = 10.0, step_km: float = 2.5) -> dict:
    """Berggrunden på platsen och inom radien, jämförd med stenens material."""
    at_site = _safe(query_point, lat, lon)
    points = _grid(lat, lon, radius_km, step_km)
    with ThreadPoolExecutor(max_workers=8) as ex:
        units = list(ex.map(lambda p: _safe(query_point, *p), points))
    with _lock:
        _save_cache()
    found = [u for u in units if u]
    rocks = Counter(u["rock"] for u in found)
    fam_share = Counter()
    for u in found:
        for fam in families(u["rock"]) or {"övrigt"}:
            fam_share[fam] += 1
    n = len(found)
    stone_fams = families(material)
    site_fams = families((at_site or {}).get("rock", ""))
    match_site = bool(stone_fams & site_fams)
    near = {fam: round(fam_share[fam] / n, 3) for fam in stone_fams} if n else {}
    match_near = any(v > 0 for v in near.values())
    if not material:
        verdict, text = "okänt", "Rundata anger inget material, så berggrunden kan inte jämföras."
    elif not stone_fams:
        verdict, text = "okänt", f"Materialet \"{material}\" kan inte föras till en bergartsfamilj."
    elif not n and not at_site:
        verdict, text = "okänt", "SGU:s karta saknar data för platsen (t.ex. utanför Sverige eller under vatten)."
    elif match_site:
        verdict, text = "på platsen", f"Berggrunden på platsen är {at_site['rock'].lower()} – samma bergartsfamilj som stenen ({material})."
    elif match_near:
        share = max(near.values())
        verdict = "i närheten"
        text = (f"Berggrunden på platsen är {(at_site or {}).get('rock', 'okänd').lower()}, men "
                f"{', '.join(FAMILY_LABEL[f] for f in stone_fams if near.get(f))} finns inom {radius_km:g} km "
                f"({round(share * 100)} % av provpunkterna).")
    else:
        verdict = "inte i närheten"
        text = (f"Stenens material ({material}) finns inte i berggrunden inom {radius_km:g} km enligt SGU. Stenen kan "
                "vara ett flyttblock eller ha fraktats dit – värt att undersöka.")
    return {
        "material": material, "material_families": sorted(stone_fams),
        "at_site": at_site, "radius_km": radius_km, "sample_points": len(points), "points_with_data": n,
        "rocks_nearby": rocks.most_common(8),
        "families_nearby": {f: round(c / n, 3) for f, c in fam_share.most_common()} if n else {},
        "verdict": verdict, "text": text, "source": SOURCE,
        "caveat": "Runstenar är ofta flyttblock eller transporterade; avvikelse från berggrunden är en ledtråd, inte ett fel.",
    }


def _safe(fn, *args):
    try:
        return fn(*args)
    except (requests.RequestException, ValueError, KeyError):
        return None


def carver_materials(carver: str, inscriptions: list[dict], certain_carvers) -> dict:
    """Bergartsfamiljer på ristarens säkra stenar enligt Rundata."""
    fams, raw = Counter(), Counter()
    n = 0
    for r in inscriptions:
        if carver in certain_carvers(r) and r.get("material"):
            n += 1
            raw[r["material"].lower()] += 1
            for f in families(r["material"]):
                fams[f] += 1
    return {"n": n, "families": {f: round(c / n, 3) for f, c in fams.most_common()} if n else {},
            "materials": raw.most_common(6)}
