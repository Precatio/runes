"""Vilka historiska kartor (Lantmäteriets Historiska kartor, historiskakartor.lantmateriet.se) finns runt runstenarna med
känd ristningsriktning? Bara en inventering: per sten listas kartorna inom en ruta om 2 x 2 km (geometriska kartor
1630-1650-talen, storskiften, laga skiften, Häradsekonomiska kartan, Generalstabskartan, Ekonomiska kartan). Läser
bara signum och läge ur utdata/riktning/stenar.csv, inte riktningen. Viktor 2026-11-10: "see if you can download the
oldest maps yourself". Skriver /Volumes/2TB/Antigrvity/Runes/geografi_kallor/historiska_kartor/inventering.json.
    .venv/bin/python scripts/historiska_kartor_inventera.py"""
import csv
import json
import os
import time
import urllib.request

from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/historiska_kartor/inventering.json"
B = "https://historiskakartor.lantmateriet.se/data/search-service/"
HALF = 1000


def post(url, body=None):
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json", "User-Agent": "Vitki research inventory"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception:
            time.sleep(5 * (i + 1))
    return None


def para(doc):
    p = {x["name"]: x["text"] for x in doc["paragraphs"]}
    for g in doc.get("paragraphGroups", []):
        for x in g["paragraphs"]:
            p.setdefault(x["name"], x["text"])
    return p


def main():
    to = Transformer.from_crs(4326, 3006, always_xy=True)
    rows = {r["signum"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "riktning", "stenar.csv"), encoding="utf-8")) if r["lat"]}
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for sig, (lat, lon) in rows.items():
        if sig in out:
            continue
        x, y = to.transform(lon, lat)
        q = f"xmin={round(x - HALF)}&ymin={round(y - HALF)}&xmax={round(x + HALF)}&ymax={round(y + HALF)}"
        g = post(B + "metadata/geosearch?" + q)
        if g is None:
            continue
        rec = {"x": round(x), "y": round(y), "rak": [d | {"serie": grp["name"]} for grp in g.get("documentgroups", []) for d in grp["documents"]], "lms": [], "reg": []}
        body = {"counties": [{"name": c["name"], "parishs": [{"name": p["name"], "settlements": [{"name": s["name"]} for s in p["settlements"]]} for p in c["parishs"]]} for c in g.get("counties", [])]}
        if body["counties"]:
            for arkiv in ("LMS", "REG"):
                d = post(B + arkiv + "/metadata/searchbody?firstMatch=1&pageSize=2000", body) or {"documents": []}
                for doc in d["documents"]:
                    p = para(doc)
                    rec[arkiv.lower()].append({"base": doc.get("base"), "ktun": doc.get("ktun"), "id": p.get("IDHR") or p.get("ALMS"), "seri": p.get("SERI"),
                                               "ar": p.get("VAR") or p.get("ARTA") or p.get("PULD"), "by": p.get("SBY"), "socken": p.get("SOCN"),
                                               "atgard": p.get("ATGBESK") or p.get("ATGFORK"), "anm": p.get("ANM"), "sidor": p.get("ANBI")})
        out[sig] = rec
        json.dump(out, open(OUT + ".tmp", "w"), ensure_ascii=False)
        os.replace(OUT + ".tmp", OUT)
        time.sleep(1.0)
    print(len(out), "stenar inventerade")


if __name__ == "__main__":
    main()
