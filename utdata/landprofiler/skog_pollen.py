"""Hur skogrikt var landet omkring år 800–1100? Pollen ur Neotoma Paleoecology Database (CC BY 4.0): för varje pollenlokal
i Götaland och Svealand prover daterade 850–1150 kalibrerade år före 1950 (= ungefär år 800–1100), andelen träd- och
buskpollen (ekologisk grupp TRSH) av träd, buskar och landörter (TRSH + UPHE). Beskrivande underlag för serien De gamla
landen. Skriver skog_pollen.json (per lokal, med gammalt land och härad ur data.py:s socken-logik).
    PYTHONPATH=. .venv/bin/python utdata/landprofiler/skog_pollen.py"""
import json
import os
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/neotoma/"
API = "https://api.neotomadb.org/v2.0/data/"
src = open(os.path.join(HERE, "data.py")).read()
g = {"__name__": "pollen", "__file__": os.path.join(HERE, "data.py")}
exec(compile(src[:src.index("# ---- 1–3 the stones")], "data_head", "exec"), g)
nearest, unit_cols = g["nearest"], g["unit_cols"]

sites = json.load(open(CACHE + "sites.json"))["data"]
out = []
for s in sites:
    geo = json.loads(s["geography"])
    c = geo["coordinates"]
    if geo["type"] == "Polygon":
        ring = c[0]; lon = sum(p[0] for p in ring) / len(ring); lat = sum(p[1] for p in ring) / len(ring)
    else:
        lon, lat = c
    p = nearest((lat, lon), maxkm=20)
    for cu in s["collectionunits"]:
        for ds in cu["datasets"]:
            if ds["datasettype"] != "pollen":
                continue
            f = CACHE + f"ds_{ds['datasetid']}.json"
            if not os.path.exists(f):
                r = requests.get(API + f"downloads/{ds['datasetid']}", timeout=120)
                open(f, "w").write(r.text)
                time.sleep(0.5)
            d = json.load(open(f))
            try:
                samples = d["data"][0]["site"]["collectionunit"]["dataset"]["samples"]
            except (KeyError, IndexError, TypeError):
                continue
            vals = []
            for sm in samples:
                ages = [a.get("age") for a in sm.get("ages", []) if a.get("age") is not None and (a.get("agetype") or "").startswith("Calibrated")]
                if not ages:
                    ages = [a.get("age") for a in sm.get("ages", []) if a.get("age") is not None]
                if not ages or not (850 <= ages[0] <= 1150):
                    continue
                trsh = sum(x.get("value") or 0 for x in sm.get("datum", []) if x.get("ecologicalgroup") == "TRSH" and x.get("elementtype") == "pollen")
                uphe = sum(x.get("value") or 0 for x in sm.get("datum", []) if x.get("ecologicalgroup") == "UPHE" and x.get("elementtype") == "pollen")
                if trsh + uphe >= 100:
                    vals.append({"age": ages[0], "ap": trsh / (trsh + uphe)})
            if vals:
                out.append({"site": s["sitename"], "datasetid": ds["datasetid"], "lat": lat, "lon": lon, "n_samples": len(vals),
                            "ap_mean": sum(v["ap"] for v in vals) / len(vals), "samples": vals,
                            **({k: v for k, v in unit_cols(p).items() if k != "half"} if p else {"province": None})})
json.dump(out, open(os.path.join(HERE, "skog_pollen.json"), "w"), ensure_ascii=False, indent=1)
for o in sorted(out, key=lambda o: (o.get("province") or "", o.get("region") or "")):
    print(f"{o['site'][:28]:28} {o.get('province')} {o.get('region')!s:14} {o.get('harad')!s:22} prover {o['n_samples']:2}  träd/buskar {100 * o['ap_mean']:.0f} %")
