"""Data för ristarsidan (Balle först): de två profilerna (med och utan Röd-Balles stenar), dragens etiketter, likhet
mellan ristarens stenar (ordnad med hierarkisk klustring), kartunderlag (folkland + kust inom ristarens område).
    .venv/bin/python utdata/ristare/sida_data.py utdata/ristare/balle.json utdata/ristare/balle_utan_rodballe.json OUT.json
"""
import json
import sys

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

LABELS = {
    "msg_gard": "Nämner gård eller bostad", "ord_goðan": "Lovordet góðan (god)", "god": "Lovordet god",
    "msg_berom": "Berömmer den döde", "stil_Pr3": "Stilgrupp Pr3", "stil_Pr4": "Stilgrupp Pr4",
    "rel_barn": "Den döde är resarens barn", "ord_sun": "Ordet sun (son)", "prep_at": "at (inte æftiR) för ”efter”",
    "ord_at": "Ordet at", "ord_boanda": "Ordet bónda (make, bonde)", "skilj_punkt": "Punkt som skiljetecken",
    "pm_stungna": "Stungna runor", "stungen_e": "Stungen e-runa", "stungen_y": "Stungen y-runa",
    "skilj_apostrof": "Apostrof som skiljetecken", "skilj_kryss": "Kryss som skiljetecken",
    "ord_and": "Ordet and (ande, själ)", "ord_let": "Ordet lét (lät)", "ord_ræistu": "Ordet ræistu (reste, plural)",
    "o_runa": "o-runan ᚬ används", "ord_ræisa": "Ordet ræisa (resa)", "ord_hann": "Ordet hann (han)",
    "flera_resare": "Flera resare", "ord_i": "Ordet í (i)", "r_for_R": "r-runa där ʀ väntas",
    "pm_kors": "Kors på stenen", "kvinna_ensam": "En kvinna reser ensam", "monoftong": "Monoftong (stin för stæin)",
}
FAMILY = {"stil": "Stil", "stungna": "Stavning", "monoftong": "Stavning", "o_runa": "Stavning", "r": "Stavning",
          "prep": "Formel", "ord": "Ord", "resare": "Resarna", "familj": "Resarna", "berom": "Beröm",
          "arv": "Innehåll", "kristen": "Kristet", "skilj": "Skiljetecken"}


def family(t, f):
    if t.startswith("skilj_"):
        return "Skiljetecken"
    return FAMILY.get(f, "Övrigt")


def build(path):
    d = json.load(open(path, encoding="utf-8"))
    sig = d["signatur"]
    prof = {r["drag"]: r for r in d["drag"]}
    traits = []
    for t in sorted(sig, key=lambda t: -prof[t]["lor"]):
        r = prof[t]
        traits.append({"id": t, "label": LABELS.get(t, t), "family": family(t, r["familj"]),
                       "lor": round(r["lor"], 3), "pc": round(r["k_ristare"] / r["n_ristare"], 3),
                       "pn": round(r["k_grannar"] / r["n_grannar"], 3), "kc": r["k_ristare"], "nc": r["n_ristare"],
                       "kn": r["k_grannar"], "nn": r["n_grannar"], "p": r["p"],
                       "dup": [x["drag"] for x in d["drag"] if x.get("dubblett_av") == t]})
    order = {t: i for i, t in enumerate(sig)}
    stones = []
    for s, cells in zip(d["stenar"], d["celler"]):
        row = {"id": s["signum"], "set": s["set"], "place": s.get("place"), "parish": s.get("parish"),
               "prov": s["province"], "lat": s["lat"], "lon": s["lon"], "style": s.get("style"),
               "material": s.get("material"), "score": None if s["score"] is None else round(s["score"], 3),
               "n": int(s["n"]), "follows": None if s["follows"] is None else round(s["follows"], 3),
               "klass": s["klass"], "modell": None if s.get("modell") is None else round(s["modell"], 3)}
        if s["set"] != "granne":
            row["cells"] = [cells[order[t["id"]]] for t in traits]
        stones.append(row)
    # Likhet mellan ristarens stenar: andel lika värden på signaturdragen som båda går att avläsa på (minst 5)
    own = [s for s in stones if s["set"] != "granne" and s["n"] >= 5]
    m = len(own)
    sim = np.full((m, m), np.nan)
    for i in range(m):
        for j in range(m):
            a, b = own[i]["cells"], own[j]["cells"]
            both = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
            if len(both) >= 5:
                sim[i, j] = sum(x == y for x, y in both) / len(both)
    dist = 1 - np.nan_to_num(sim, nan=np.nanmean(sim))
    np.fill_diagonal(dist, 0)
    lv = leaves_list(linkage(squareform((dist + dist.T) / 2, checks=False), "average"))
    simi = {"ids": [own[i]["id"] for i in lv],
            "m": [[None if np.isnan(sim[i, j]) else round(float(sim[i, j]), 2) for j in lv] for i in lv]}
    return {"ristare": d["ristare"], "km": d["grannar_km"], "n": d["n"], "granser": d["granser"],
            "traits": traits, "stones": stones, "sim": simi}


def basemap(stones):
    lat = [s["lat"] for s in stones]; lon = [s["lon"] for s in stones]
    bb = (min(lon) - 0.3, min(lat) - 0.2, max(lon) + 0.3, max(lat) + 0.2)
    inside = lambda ring: any(bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] for x, y in ring)  # noqa: E731

    def rings(geom):
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        return [r for p in polys for r in p]
    land = json.load(open("web/public/geo/land.geojson", encoding="utf-8"))
    folk = []
    for f in land["features"]:
        if f["properties"]["id"] in ("tiundaland", "attundaland", "fjadrundaland", "roden"):
            for r in rings(f["geometry"]):
                folk.append({"id": f["properties"]["id"], "label": f["properties"]["label"],
                             "ring": [[round(x, 3), round(y, 3)] for x, y in r]})
    riken = json.load(open("web/public/geo/riken.geojson", encoding="utf-8"))
    coast = []
    for f in riken["features"]:
        if f["properties"].get("id") == "sverige":
            for r in rings(f["geometry"]):
                if len(r) > 3 and inside(r):
                    coast.append([[round(x, 3), round(y, 3)] for x, y in r[::2]])
            break
    labels = [{"label": f["properties"]["label"], "lat": f["properties"]["label_lat"], "lon": f["properties"]["label_lon"]}
              for f in land["features"] if f["properties"]["id"] in ("tiundaland", "attundaland", "fjadrundaland", "roden")]
    return {"bbox": bb, "folk": folk, "coast": coast, "labels": labels}


if __name__ == "__main__":
    a, b, out = sys.argv[1:4]
    A, B = build(a), build(b)
    page = {"med": A, "utan": B, "karta": basemap(A["stones"])}
    json.dump(page, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out, len(json.dumps(page)) // 1024, "kB", len(A["traits"]), len(B["traits"]), len(page["karta"]["coast"]))
