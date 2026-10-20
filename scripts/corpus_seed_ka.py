"""Fyller den delade mätkorpusen (Firestore `corpus`, databasen vitki) med Kitzler Åhfeldts 36 öppna skanningar av
Södermanlands runstenar, mätta med Vitki-protokollet (groove-5, utdata/Rak/referenser_g5/, METHODS.md 2 och 13).

Posterna får samma form som webbläsaren skriver (web/src/lib/corpus.ts, addEntry) och ett fast id per sten och
metodversion, så att skriptet kan köras om utan dubbletter. Bidragsgivare är grundaren; skannern, institutionen,
DOI och licensen står i skanningens metadata och i noteringen, som regeln i METHODS 17 kräver. Högst 200 snitt per
post (säkerhetsreglernas gräns); fler snitt glesas ut jämnt, och det fulla antalet står i noteringen.
    .venv/bin/python scripts/corpus_seed_ka.py            # visar vad som skulle skrivas
    .venv/bin/python scripts/corpus_seed_ka.py --skriv    # skriver till Firestore
"""
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from dotenv import dotenv_values  # noqa: E402

for f in (".env", "api/.env"):
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        for k, v in dotenv_values(p).items():
            os.environ.setdefault(k, v or "")

from api.config import APP_VERSION  # noqa: E402
from src.stats import METRICS  # noqa: E402

REF = os.path.join(ROOT, "utdata", "Rak", "referenser_g5")
METHOD = "groove-5"
MAX_SLICES = 200
FOUNDER_EMAIL = "viktor.kvant@gmail.com"
SCAN = {"scanned_by": "Laila Kitzler Åhfeldt, Riksantikvarieämbetet",
        "url": "https://doi.org/10.5281/zenodo.11951255", "license": "CC BY 4.0"}


def thin(slices: list[dict]) -> list[dict]:
    if len(slices) <= MAX_SLICES:
        return slices
    step = len(slices) / MAX_SLICES
    return [slices[int(i * step)] for i in range(MAX_SLICES)]


def entry(d: dict, uid: str, name: str, now: str) -> dict:
    sig = d["signum"]
    slices_all = [s for s in d["slices"] if all(s.get(m) is not None for m in METRICS)]
    slices = [{**{m: float(s[m]) for m in METRICS}, "position_mm": float(s.get("position_mm") or 0),
               **({"rune_id": int(s["rune_id"])} if s.get("rune_id") is not None else {})} for s in thin(slices_all)]
    summary = {m: {k: d["summary"][m].get(k) for k in ("n", "mean", "sd", "ci95", "min", "max")} for m in METRICS}
    n_runes = (d.get("rune_summary") or {}).get("n_runes")
    notes = (f"Skanning av Laila Kitzler Åhfeldt (RAÄ), Zenodo {SCAN['url']}, CC BY 4.0. Mätt i Vitki med protokollet "
             f"({METHOD}, bara runor): {len(slices_all)} snitt i {n_runes} igenkända runor"
             + (f"; {MAX_SLICES} av snitten lagrade här, alla i utdata/Rak/referenser_g5" if len(slices_all) > MAX_SLICES else "")
             + ". Seedad av scripts/corpus_seed_ka.py.")
    return {
        "id": f"c_ka_{METHOD}_{re.sub(r'[^\w]+', '_', sig)}",
        "signum": sig, "label": sig, "feature_type": "rune",
        "contributorUid": uid, "contributorName": name, "institution": "Vitki",
        "license": "CC-BY-4.0", "createdAt": now, "method_version": METHOD,
        "means": {m: float(d["means"][m]) for m in METRICS}, "summary": summary, "slices": slices,
        "provenance": {"software": "Vitki", "version": APP_VERSION, "method_version": METHOD, "timestamp": now,
                       "feature_type": "rune", "protocol": d.get("protocol"),
                       "mesh": {"mock": False, "filename": d.get("file"), "sha256": d.get("sha256")},
                       "parameters": d.get("parameters") or {}},
        "scanner": SCAN["scanned_by"], "notes": notes,
        "scan": {**SCAN, "resolution_mm": (d.get("parameters") or {}).get("mesh_point_spacing_mm")},
        "raw_profile_chunks": 0, "rune_forms": 0, "verifications": [],
    }


def main():
    write = "--skriv" in sys.argv
    from api.auth import firebase_app, firestore
    from firebase_admin import auth
    user = auth.get_user_by_email(FOUNDER_EMAIL, app=firebase_app())
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    files = sorted(glob.glob(os.path.join(REF, "*.json")))
    rows = [entry(json.load(open(f, encoding="utf-8")), user.uid, user.display_name or "Viktor Kvant", now) for f in files]
    for e in rows:
        print(f"{'skriver' if write else 'skulle skriva'} {e['id']}: {e['signum']}, {len(e['slices'])} snitt, "
              f"V-vinkel {e['means']['apex_vinkel_deg']:.1f}°")
    if write:
        col = firestore().collection("corpus")
        for e in rows:
            col.document(e["id"]).set(e)
        print(f"{len(rows)} poster skrivna; i korpusen nu:", sum(1 for _ in col.stream()))


if __name__ == "__main__":
    main()
