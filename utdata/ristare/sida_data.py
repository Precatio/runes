"""Data för ristarsidan: alla ristarprofiler (r/carver_profile.R, utdata/ristare/kor_alla.sh) i en fil, med läsbara
etiketter för dragen, likhet mellan varje ristares stenar (ordnad med hierarkisk klustring) och kartunderlag.
    .venv/bin/python utdata/ristare/sida_data.py utdata/ristare/profiler web/public/geo/ristare.json \
        utdata/ristare/modellforslag.csv utdata/attribuering_provad/resultat.json
"""
import glob
import json
import os
import sys

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

WORDS = {
    "faður": "fader", "broður": "bror", "brøðr": "bröder", "sun": "son", "sunn": "son", "moðiR": "moder",
    "dauðr": "död", "dræng": "ung man, dräng", "gærði": "gjorde", "gæra": "göra", "haggva": "hugga",
    "mærki": "minnesmärke", "satti": "satte", "salu": "själ", "stæina": "stenar", "þenna": "denna", "þennsa": "denna",
    "þannsi": "denna", "þennsi": "denna", "þessa": "dessa", "þessi": "denna", "þæiR": "de", "þæiRa": "deras",
    "þau": "de båda", "hans": "hans", "hann": "han", "eR": "som", "en": "men", "a": "på", "i": "i", "með": "med",
    "austr": "österut", "bro": "bro", "vaR": "var", "varð": "blev", "boanda": "make, bonde", "at": "efter, vid",
    "let": "lät", "letu": "läto", "ræisa": "resa", "ræisti": "reste", "ræistu": "reste (flera)", "ræisþi": "reste",
    "and": "ande, själ", "goðan": "god", "hialpi": "hjälpe",
}
LABELS = {
    "msg_gard": "Nämner gård eller bostad", "god": "Lovordet god", "msg_berom": "Berömmer den döde",
    "drengr": "Kallar den döde drengr", "thegn": "Kallar den döde þegn", "rel_barn": "Den döde är resarens barn",
    "rel_foralder": "Den döde är resarens förälder", "rel_make": "Den döde är resarens make eller maka",
    "rel_syskon": "Den döde är resarens syskon", "prep_at": "at (inte æftiR) för ”efter”",
    "pm_stungna": "Stungna runor", "stungen_e": "Stungen e-runa", "stungen_y": "Stungen y-runa",
    "stungen_g": "Stungen g-runa", "o_runa": "o-runan ᚬ används", "r_for_R": "r-runa där ʀ väntas",
    "monoftong": "Monoftong (stin för stæin)", "au_monoftong": "Monoftong i ”och” (uk)", "h_saknas": "h saknas i uddljud",
    "bindrunor": "Bindrunor", "flera_resare": "Flera resare", "kvinna_ensam": "En kvinna reser ensam",
    "kvinna_resare": "En kvinna bland resarna", "pm_kors": "Kors på stenen", "pm_bon": "Bön för den döde",
    "pm_sjal": "Bön för själen", "cat_kristen": "Kristet innehåll", "cat_arv": "Arv eller ägande",
    "cat_bro_vag": "Bro eller väg", "cat_fard": "Färd", "cat_sjalvminne": "Rest åt sig själv",
    "msg_dod_borta": "Dog borta", "msg_dod_uppgift": "Berättar hur eller var han dog", "msg_resa": "Nämner en resa",
    "mat_granit": "Granit", "mat_gnejs": "Gnejs", "mat_sandsten": "Sandsten", "mat_kalksten": "Kalksten",
    "nara_bro": "Nära bro eller vad", "nara_vag": "Nära väg", "nara_vatten": "Nära vatten", "nara_hog": "Nära hög",
    "nara_gravfalt": "Nära gravfält", "nara_gammalt_namn": "Nära gammalt bebyggelsenamn",
    "nara_centralort": "Nära centralortsnamn", "nara_kultnamn": "Nära kultnamn", "i_grupp": "Står i en grupp av stenar",
    "skilj_punkt": "Punkt som skiljetecken", "skilj_kryss": "Kryss som skiljetecken", "skilj_kolon": "Kolon som skiljetecken",
    "skilj_apostrof": "Apostrof som skiljetecken", "skilj_plus": "Plus som skiljetecken",
    "skilj_blandat": "Blandade skiljetecken",
}
STYLES = {"Fp": "fågelperspektiv", "KB": "korsband", "RAK": "rak runslinga", "Pr1": "Pr1", "Pr2": "Pr2",
          "Pr3": "Pr3", "Pr4": "Pr4", "Pr5": "Pr5"}


def label(t):
    if t in LABELS:
        return LABELS[t]
    if t.startswith("ord_"):
        w = t[4:]
        return f"Ordet {w}" + (f" ({WORDS[w]})" if w in WORDS else "")
    if t.startswith("stil_"):
        return "Stilgrupp " + STYLES.get(t[5:], t[5:])
    return t


def family(t):
    if t.startswith("stil_"):
        return "Stil"
    if t.startswith("skilj_"):
        return "Skiljetecken"
    if t.startswith("ord_"):
        return "Ord"
    if t.startswith("mat_"):
        return "Material"
    if t.startswith("nara_") or t == "i_grupp":
        return "Platsen"
    if t in ("pm_stungna", "stungen_e", "stungen_y", "stungen_g", "o_runa", "r_for_R", "monoftong", "au_monoftong",
             "h_saknas", "bindrunor", "prep_at"):
        return "Stavning"
    if t in ("pm_kors", "pm_bon", "pm_sjal", "cat_kristen"):
        return "Kristet"
    if t in ("flera_resare", "kvinna_ensam", "kvinna_resare") or t.startswith("rel_"):
        return "Resarna"
    return "Innehåll"


def r(x, k=3):
    return None if x is None else round(x, k)


def build(path):
    d = json.load(open(path, encoding="utf-8"))
    sig = d["signatur"]
    prof = {x["drag"]: x for x in d["drag"]}
    traits = [{"id": t, "label": label(t), "family": family(t), "lor": r(prof[t]["lor"]),
               "pc": r(prof[t]["k_ristare"] / prof[t]["n_ristare"]), "pn": r(prof[t]["k_grannar"] / prof[t]["n_grannar"]),
               "kc": prof[t]["k_ristare"], "nc": prof[t]["n_ristare"], "kn": prof[t]["k_grannar"], "nn": prof[t]["n_grannar"],
               "dup": [label(x["drag"]) for x in d["drag"] if x.get("dubblett_av") == t]}
              for t in sorted(sig, key=lambda t: -prof[t]["lor"])]
    order = {t: i for i, t in enumerate(sig)}
    stones, nb = [], []
    for s, cells in zip(d["stenar"], d["celler"]):
        if s["set"] == "granne":  # kompakt: id, plats, socken, lat, lon, stil, värde, antal drag, klass
            nb.append([s["signum"], s.get("place"), s.get("parish"), r(s["lat"], 4), r(s["lon"], 4), s.get("style"),
                       r(s["score"]), int(s["n"]), s["klass"]])
            continue
        stones.append({"id": s["signum"], "set": s["set"], "place": s.get("place"), "parish": s.get("parish"),
                       "prov": s["province"], "lat": s["lat"], "lon": s["lon"], "style": s.get("style"),
                       "material": s.get("material"), "score": r(s["score"]), "n": int(s["n"]),
                       "follows": r(s["follows"]), "klass": s["klass"], "modell": r(s.get("modell")),
                       "cells": [cells[order[t["id"]]] for t in traits] if traits else []})
    own = [s for s in stones if s["n"] >= 5 and s["lat"] is not None]
    m = len(own)
    simi = {"ids": [], "m": []}
    if m >= 3 and traits:
        sim = np.full((m, m), np.nan)
        for i in range(m):
            for j in range(m):
                both = [(x, y) for x, y in zip(own[i]["cells"], own[j]["cells"]) if x is not None and y is not None]
                if len(both) >= 5:
                    sim[i, j] = sum(x == y for x, y in both) / len(both)
        fill = np.nanmean(sim) if np.isfinite(sim).any() else 0.5
        dist = 1 - np.nan_to_num(sim, nan=fill)
        np.fill_diagonal(dist, 0)
        lv = leaves_list(linkage(squareform((dist + dist.T) / 2, checks=False), "average"))
        simi = {"ids": [own[i]["id"] for i in lv],
                "m": [[None if np.isnan(sim[i, j]) else round(float(sim[i, j]), 2) for j in lv] for i in lv]}
    pts = [(s["lon"], s["lat"]) for s in stones if s["lat"] is not None]
    lon = [p[0] for p in pts]; lat = [p[1] for p in pts]
    bbox = [min(lon) - 0.35, min(lat) - 0.22, max(lon) + 0.35, max(lat) + 0.22]
    return {"ristare": d["ristare"], "profil": d["profil"], "n_signerade": d["n_signerade"], "km": d["grannar_km"],
            "period": d["period"], "n": d["n"], "granser": d["granser"], "traits": traits, "stones": stones,
            "nb": nb, "sim": simi, "bbox": bbox}


def basemap():
    def rings(geom):
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        return [ring for p in polys for ring in p]
    land = json.load(open("web/public/geo/land.geojson", encoding="utf-8"))
    folk = [{"id": f["properties"]["id"], "ring": [[round(x, 3), round(y, 3)] for x, y in ring]}
            for f in land["features"] for ring in rings(f["geometry"])]
    labels = [{"label": f["properties"]["label"], "lat": f["properties"]["label_lat"], "lon": f["properties"]["label_lon"]}
              for f in land["features"]]
    riken = json.load(open("web/public/geo/riken.geojson", encoding="utf-8"))
    coast = []
    for f in riken["features"]:
        if f["properties"].get("id") == "sverige":
            coast = [[[round(x, 3), round(y, 3)] for x, y in ring[::2]] for ring in rings(f["geometry"]) if len(ring) > 3]
            break
    return {"folk": folk, "labels": labels, "coast": coast}


def suggestions(path):
    """Attribueringsmodellens förslag (r/attribution_candidates.R), per ristare: stenar utan säker ristare där modellen
    sätter ristaren först och spärren ”någon annan” inte slår till; ordnade efter den omkalibrerade sannolikheten."""
    import csv
    by = {}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["someone_else"] == "TRUE":
            by.setdefault(row["top"], {"n_blocked": 0, "rows": []})["n_blocked"] = by.get(row["top"], {"n_blocked": 0})["n_blocked"] + 1
            by.setdefault(row["top"], {"n_blocked": 0, "rows": []})
            continue
        by.setdefault(row["top"], {"n_blocked": 0, "rows": []})["rows"].append(
            {"id": row["signum"], "place": row["place"], "parish": row["parish"], "style": row["style"] or None,
             "p": float(row["p_cal"]), "second": row["second"], "p2": float(row["p2_cal"]),
             "rundata": row["rundata_uncertain"], "near_km": float(row["near_km"]),
             "lat": float(row["lat"]) if row["lat"] not in ("", "NA") else None,
             "lon": float(row["lon"]) if row["lon"] not in ("", "NA") else None})
    for v in by.values():
        v["rows"].sort(key=lambda r: -r["p"])
    return by


SMALL = 20        # ristare med färre säkra stenar får bygdsmodellens andra bedömning
BYGD_MIN_P = 0.5  # bara stenar där bygdsmodellen sätter ristaren först med minst så hög sannolikhet


def bygd_suggestions(path, main_path):
    """Bygdsmodellens förslag (r/attribution_bygd.R) per ristare, med huvudmodellens förstaval bredvid."""
    import csv
    main = {r["signum"]: r for r in csv.DictReader(open(main_path, encoding="utf-8"))}
    by = {}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if float(row["p_cal"]) < BYGD_MIN_P:
            continue
        m = main.get(row["signum"]) or {}
        by.setdefault(row["top"], []).append(
            {"id": row["signum"], "place": row["place"], "parish": row["parish"], "p": float(row["p_cal"]),
             "second": row["second"], "p2": float(row["p2_cal"]), "rundata": row["rundata_uncertain"],
             "lat": float(row["lat"]) if row["lat"] not in ("", "NA") else None,
             "lon": float(row["lon"]) if row["lon"] not in ("", "NA") else None,
             "main_top": m.get("top"), "main_p": float(m["p_cal"]) if m.get("p_cal") else None,
             "main_blocked": m.get("someone_else") == "TRUE"})
    for v in by.values():
        v.sort(key=lambda r: -r["p"])
    return by


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    sugg = suggestions(sys.argv[3]) if len(sys.argv) > 3 else {}
    bygd_path = os.path.join(os.path.dirname(sys.argv[3]), "bygdsforslag.csv") if len(sys.argv) > 3 else ""
    bygd = bygd_suggestions(bygd_path, sys.argv[3]) if bygd_path and os.path.exists(bygd_path) else {}
    names = [ln.strip() for ln in open(os.path.join(src, "ristare.txt"), encoding="utf-8") if ln.strip()]
    carvers = []
    for who in names:
        f = os.path.join(src, who.replace(" ", "_").replace("-", "") + ".json")
        v = {"med": build(f)}
        alt = glob.glob(os.path.join(src, who.replace(" ", "_").replace("-", "") + "__*.json"))
        for a in alt:
            v[os.path.basename(a)[:-5].split("__", 1)[1]] = build(a)
        n_certain = sum(v["med"]["n"].get(k, 0) for k in ("signerad", "attribuerad"))
        carvers.append({"name": who, "variants": v, "forslag": sugg.get(who),
                        "bygd": bygd.get(who, []) if (n_certain < SMALL and who in sugg) else None})
        print(who, len(v["med"]["traits"]), len(v["med"]["stones"]), len(v["med"]["nb"]))
    page = {"carvers": carvers, "karta": basemap()}
    v3 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[3]))), "attribuering_v3", "resultat.json")
    if os.path.exists(v3):  # bygdsmodellens (K3) och huvudmodellens (K0) träff i provningen, för rutan med andra bedömningen
        r3 = json.load(open(v3, encoding="utf-8"))["varianter"]
        k0 = {x["carver"]: x for x in r3["K0"]["per_carver"]}
        page["bygd_test"] = {"half2_macro": [r3["K0"]["half2"]["macro"], r3["K3"]["half2"]["macro"]],
                             "half2_top1": [r3["K0"]["half2"]["top1"], r3["K3"]["half2"]["top1"]],
                             "per_carver": {x["carver"]: {"n": x["n"], "bygd": x["top1"], "main": k0.get(x["carver"], {}).get("top1")}
                                            for x in r3["K3"]["per_carver"]}}
    if len(sys.argv) > 4:  # provningen av modellen (r/attribution_audit.R), som sidan visar per ristare
        page["audit"] = json.load(open(sys.argv[4], encoding="utf-8"))
    json.dump(page, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out, os.path.getsize(out) // 1024, "kB")
