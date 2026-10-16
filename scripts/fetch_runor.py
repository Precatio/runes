"""Hämtar hela Runor (Riksantikvarieämbetet, utgåva 2020 av Samnordisk runtextdatabas) via dess öppna API.

    python -m scripts.fetch_runor            # hämtar det som saknas i cachen och bygger data/raa/runor_2020.json
    python -m scripts.fetch_runor --build    # bygger bara om sammanställningen ur cachen

Rundata i appen är version 3.1 från 2018. Runor är två år nyare och har uppgifter som Rundata saknar: om stenen finns
kvar (extant), om den står på sin ursprungliga plats, var den först är känd, anteckningar om skador och öden,
nyare läsningar och tolkningar, terminus post/ante quem och id:n i Kulturmiljöregistret. Varje inskrift sparas
oförändrad i data/cache/runor/<id>.json (git-ignorerad); sammanställningen skrivs till data/raa/runor_2020.json
(git-ignorerad). Hämtningen är långsam med flit: två anrop åt gången och en paus mellan dem.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from api.rundata import store
from src.crosscheck import RUNOR, RUNOR_EDITION, UA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache", "runor")
OUT = os.path.join(ROOT, "data", "raa", "runor_2020.json")
WORKERS = 2
PAUSE_S = 0.25


def _get(url: str, params: dict) -> object:
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001 - nätverksfel: försök igen efter en paus
            print(f"  fel ({e}), försöker igen", file=sys.stderr, flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Runor svarar inte: {url} {params}")


def inscription_ids() -> dict[str, str]:
    """id -> signum för alla inskrifter som sökningen ger, ett landskap/land (signumprefix) i taget."""
    prefixes = sorted({r["signum"].split(" ")[0] for r in store().inscriptions})
    out: dict[str, str] = {}
    for p in prefixes:
        hits = _get(f"{RUNOR}/search", {"edition_id": RUNOR_EDITION, "search_field": "SIGNUM", "matching_text": p})
        for h in hits:
            out[h["inscription_id"]] = f"{h['signum1']} {h['signum2']}"
        print(f"{p}: {len(hits)} träffar, {len(out)} unika hittills", flush=True)
        time.sleep(PAUSE_S)
    return out


def fetch(iid: str) -> bool:
    """Hämtar en inskrift till cachen; False om den redan fanns."""
    path = os.path.join(CACHE, f"{iid}.json")
    if os.path.exists(path):
        return False
    d = _get(f"{RUNOR}/inscriptions/{iid}", {"edition_id": RUNOR_EDITION})
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False)
    os.replace(tmp, path)
    time.sleep(PAUSE_S)
    return True


def _interpretation(texts: list, code: str) -> str:
    return " ".join(i["text"] for t in texts for i in t.get("interpretations") or []
                    if (i.get("language") or {}).get("language_code") == code)


def compact(d: dict) -> dict:
    """De fält appen använder, i platt form."""
    pos = d.get("position") or {}
    orig = d.get("original_location") or {}
    texts = d.get("runic_texts") or []
    her = [i for c in d.get("her_identifiers") or [] for i in c.get("identifiers") or []]
    point = lambda p: (p or {}).get("coordinates")  # noqa: E731 - [lon, lat]
    return {
        "signum": f"{d['signum1']} {d['signum2']}", "id": d["inscription_id"],
        "alt_signa": [f"{a.get('signum1', '')} {a.get('signum2', '')}".strip() if isinstance(a, dict) else str(a)
                      for a in d.get("alternative_signa") or []],
        "extant": d.get("extant"), "placement": d.get("placement"),
        "original": orig.get("original"), "original_text": orig.get("text"),
        "current": point(pos.get("current")), "oldest_known": point(pos.get("oldest_known")),
        "place": ((d.get("provenance") or {}).get("place") or {}).get("place"),
        "parish": ((d.get("provenance") or {}).get("parish") or {}).get("parish"),
        "notes": d.get("notes") or [],
        "readings": [{"reading": t.get("reading"), "reference": t.get("reference")} for t in texts],
        "normalization_rsv": _interpretation(texts, "RSV") or _interpretation(texts, "RDA"),
        "normalization_ows": _interpretation(texts, "FVN"),
        "period": (d.get("period") or {}).get("period"), "dating": d.get("dating"),
        "termini": d.get("termini"),
        "material": (d.get("material") or {}).get("material_free_text"),
        "carvers": [{"name": c["name"], "attribution": c.get("attribution"), "certain": c.get("certainty")}
                    for c in d.get("carver") or []],
        "style": [s["style"].replace("\xa0", " ") for s in d.get("profile_style") or []],
        "crosses": d.get("crosses") or [],
        "her_ids": {i["key"]: i["value"] for i in her if i.get("key")},
        "image_links": d.get("image_links") or [],
        "url": (d.get("uri") or "").replace("http://", "https://"),
    }


def build() -> list[dict]:
    rows = []
    for name in sorted(os.listdir(CACHE)):
        if name.endswith(".json"):
            rows.append(compact(json.load(open(os.path.join(CACHE, name), encoding="utf-8"))))
    rows.sort(key=lambda r: r["signum"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"source": "Runor, Riksantikvarieämbetet (Samnordisk runtextdatabas, utgåva 2020). "
                             "https://runor.raa.se", "edition": RUNOR_EDITION,
                   "fetched": time.strftime("%Y-%m-%d"), "inscriptions": rows}, fh, ensure_ascii=False)
    print(f"{len(rows)} inskrifter → {OUT}")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="bygg bara om sammanställningen ur cachen")
    a = ap.parse_args(argv)
    if not a.build:
        os.makedirs(CACHE, exist_ok=True)
        ids = inscription_ids()
        todo = [i for i in ids if not os.path.exists(os.path.join(CACHE, f"{i}.json"))]
        print(f"{len(ids)} inskrifter, {len(todo)} att hämta", flush=True)
        done = 0
        with ThreadPoolExecutor(WORKERS) as ex:
            for got in ex.map(fetch, todo):
                done += got
                if done and done % 250 == 0:
                    print(f"  {done} av {len(todo)}", flush=True)
    build()


if __name__ == "__main__":
    main()
