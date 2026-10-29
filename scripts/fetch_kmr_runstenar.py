"""Hämtar Kulturmiljöregistrets (RAÄ) poster för de vikingatida runinskrifterna i Runor, via K-samsök.

    python -m scripts.fetch_kmr_runstenar            # hämtar det som saknas i cachen och bygger sammanställningen
    python -m scripts.fetch_kmr_runstenar --build    # bygger bara om sammanställningen ur cachen

Runor (scripts/fetch_runor.py) ger varje inskrifts id i Kulturmiljöregistret (kmrId). Registrets post har det som
Rundata och Runor saknar: terrängen, orienteringen (avstånd till väg, bäck, gård), beskrivningen med mått, material och
åt vilket håll ristningen vetter, skadestatus och tradition. En post kan omfatta flera stenar (numrerade 1), 2) …).
Varje post sparas oförändrad (RDF) i data/cache/kmr/<id>.xml (git-ignorerad); sammanställningen skrivs till
data/raa/kmr_runstenar.json (git-ignorerad). Licens CC0 (Riksantikvarieämbetet). En post i taget, med paus.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time

import requests

from src.crosscheck import UA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNOR = os.path.join(ROOT, "data", "cache", "runor")
CACHE = os.path.join(ROOT, "data", "cache", "kmr")
OUT = os.path.join(ROOT, "data", "raa", "kmr_runstenar.json")
URL = "https://kulturarvsdata.se/raa/lamning/{}"
PAUSE_S = 1.0

FIELD = re.compile(r"<ksam:type xml:lang=\"sv\">([^<]*)</ksam:type>\s*<ksam:(?:desc|spec)[^>]*>(.*?)</ksam:(?:desc|spec)>", re.S)
POINT = re.compile(r"<gml:coordinates[^>]*>([-\d.]+),([-\d.]+)</gml:coordinates>")
LABEL = re.compile(r"<pres:idLabel>(.*?)</pres:idLabel>")
CLASS = re.compile(r"<ksam:itemClassName[^>]*>(.*?)</ksam:itemClassName>")


def kmr_ids() -> dict[str, list[str]]:
    """kmrId -> Runors signa för de vikingatida svenska inskrifterna."""
    out: dict[str, list[str]] = {}
    for name in sorted(os.listdir(RUNOR)):
        if not name.endswith(".json"):
            continue
        d = json.load(open(os.path.join(RUNOR, name), encoding="utf-8"))
        if (d.get("period") or {}).get("period") != "V":
            continue
        country = (((d.get("provenance") or {}).get("country")) or {}).get("country_code")
        if country != "SE":
            continue
        for h in d.get("her_identifiers") or []:
            for i in h.get("identifiers") or []:
                if i.get("key") == "kmrId" and i.get("value"):
                    out.setdefault(i["value"], []).append(f"{d['signum1']} {d['signum2']}")
    return out


def fetch(kid: str) -> bool:
    path = os.path.join(CACHE, f"{kid}.xml")
    if os.path.exists(path):
        return False
    for attempt in range(4):
        try:
            r = requests.get(URL.format(kid), headers=UA, timeout=60)
            if r.status_code == 404:
                open(path, "w").close()  # finns inte längre: tom fil, hämtas inte igen
                return True
            r.raise_for_status()
            tmp = path + ".part"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(r.text)
            os.replace(tmp, path)
            time.sleep(PAUSE_S)
            return True
        except Exception as e:  # noqa: BLE001 - nätverksfel: försök igen efter en paus
            print(f"  fel ({e}), försöker igen", file=sys.stderr, flush=True)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"K-samsök svarar inte: {kid}")


def parse(text: str) -> dict:
    fields: dict[str, list[str]] = {}
    for typ, val in FIELD.findall(text):
        v = html.unescape(re.sub(r"\s+", " ", val)).strip()
        if v:
            fields.setdefault(typ.strip(), []).append(v)
    pt = POINT.search(text)
    lab = LABEL.search(text)
    cls = CLASS.search(text)
    return {"label": lab.group(1) if lab else None, "class": cls.group(1) if cls else None,
            "lon": float(pt.group(1)) if pt else None, "lat": float(pt.group(2)) if pt else None,
            "fields": fields}


def build(ids: dict[str, list[str]]) -> int:
    rows = []
    for kid, signa in sorted(ids.items()):
        path = os.path.join(CACHE, f"{kid}.xml")
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            continue
        rows.append({"kmr_id": kid, "signa": sorted(set(signa)), **parse(open(path, encoding="utf-8").read())})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"source": "Kulturmiljöregistret, Riksantikvarieämbetet, via K-samsök (CC0). "
                             "https://kulturarvsdata.se", "fetched": time.strftime("%Y-%m-%d"), "records": rows},
                  fh, ensure_ascii=False)
    return len(rows)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ids = kmr_ids()
    print(f"{len(ids)} KMR-poster för vikingatida svenska inskrifter", flush=True)
    if "--build" not in argv:
        os.makedirs(CACHE, exist_ok=True)
        n = 0
        for i, kid in enumerate(sorted(ids)):
            n += fetch(kid)
            if (i + 1) % 100 == 0:
                print(f"{i + 1}/{len(ids)} ({n} nya)", flush=True)
    print(f"sammanställning: {build(ids)} poster -> {OUT}")


if __name__ == "__main__":
    main()
