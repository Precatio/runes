"""Landprofiler (låst plan analysplaner/2026-11-02-landprofiler.md, sha eb59f631): bygger tre tabeller med härad, gammalt
land, landskap, socken och halva per enhet – stenar.csv (runstenarnas drag), gravar.csv (fornlämningsregistrets gravar
och gravfält med form ur beskrivningen) och namn.csv (ortnamnens ändelser).
    PYTHONPATH=. .venv/bin/python utdata/landprofiler/data.py
Indata: /Volumes/2TB/tmp/landprofil/grav_pt.csv och grav_pg.csv (ogr2ogr-uttag ur geografi_kallor/raa/lamningar_sverige.gpkg,
se resultat.md), ISOF:s socknar och härader, data/ortnamn/platser.csv och kultnamn.csv."""
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402
from src import regions  # noqa: E402

csv.field_size_limit(10 ** 9)
ISOF = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
RAA = "/Volumes/2TB/tmp/landprofil/"
SVEALAND_GOTALAND = {"Uppland": "U", "Södermanland": "Sö", "Västmanland": "Vs", "Närke": "Nä", "Dalarna": "D",
                     "Värmland": "Vr", "Östergötland": "Ög", "Västergötland": "Vg", "Småland": "Sm", "Öland": "Öl",
                     "Gotland": "G", "Bohuslän": "Bo", "Dalsland": "Ds", "Halland": "Hl", "Blekinge": "Bl", "Skåne": "Sk",
                     "Gästrikland": "Gs"}
SPLIT = {"U", "Sm", "G"}


def km(a, b):
    return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians(a[0])))


# ---- ISOF parishes with härad and province ---------------------------------------------------------------------------
dist = {d["id"]: d["name"] for d in json.load(open(ISOF + "districts.json"))}
prov = {p["id"]: p["name"] for p in json.load(open(ISOF + "provinces.json"))}
PAR = [p for p in json.load(open(ISOF + "parishes.json"))
       if p.get("latitude") and p.get("district_id") in dist and prov.get(p.get("province_id")) in SVEALAND_GOTALAND]
for p in PAR:
    p["pt"] = (p["latitude"], p["longitude"])
    p["harad"] = dist[p["district_id"]]
    p["prov"] = SVEALAND_GOTALAND[prov[p["province_id"]]]
BYNAME = defaultdict(list)
for p in PAR:
    BYNAME[p["name"].replace(" sn", "").strip().lower()].append(p)
GRID = defaultdict(list)
for p in PAR:
    GRID[(round(p["pt"][0] * 4), round(p["pt"][1] * 2))].append(p)


def nearest(pt, maxkm=15):
    cands = [p for dy in (-1, 0, 1) for dx in (-1, 0, 1) for p in GRID.get((round(pt[0] * 4) + dy, round(pt[1] * 2) + dx), [])]
    if not cands:
        return None
    p = min(cands, key=lambda p: km(p["pt"], pt))
    return p if km(p["pt"], pt) <= maxkm else None


def parish_of(names, pt):
    for n in names:
        c = [p for p in BYNAME.get(n.strip().lower(), []) if km(p["pt"], pt) <= 30]
        if c:
            return min(c, key=lambda p: km(p["pt"], pt))
    return nearest(pt)


# ---- härad → old land (for subdivided provinces), from the stones and the land definitions ---------------------------
hl = json.load(open(os.path.join(ROOT, "web", "src", "lib", "historiska_land.json")))
H2L = {}
for land in hl["epoch"]["regions"]:
    for h in land.get("harad", []):
        H2L[h] = land["id"]
norm = lambda h: h.replace("N. ", "Norra ").replace("S. ", "Södra ").replace(" hd", " härad").replace(" sg", " skeppslag").replace(" tg", " tingslag")  # noqa: E731
st = L.stones(json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"])
votes = defaultdict(Counter)
stone_par = {}
for sg, x in st.items():
    if x["lat"] is None:
        continue
    p = parish_of([(x["parish"] or "").replace(" sn", "")], (x["lat"], x["lon"]))
    if p is None:
        continue
    stone_par[sg] = p
    reg = regions.old_region(sg, x["province"])
    if x["province"] in SPLIT and reg != x["province"]:
        votes[p["harad"]][reg] += 1


def old_land(p):
    if p["prov"] not in SPLIT:
        return p["prov"]
    if votes.get(p["harad"]):
        return votes[p["harad"]].most_common(1)[0][0]
    return H2L.get(norm(p["harad"]), p["prov"])


# halves: parishes alternately within the province, ordered by latitude then name (no dating for graves and names)
order = defaultdict(list)
for p in PAR:
    order[p["prov"]].append(p)
HALF = {}
for pv, ps in order.items():
    for i, p in enumerate(sorted(ps, key=lambda p: (-p["pt"][0], p["name"]))):
        HALF[id(p)] = i % 2


def unit_cols(p):
    return {"province": p["prov"], "region": old_land(p), "harad": p["harad"], "parish": p["name"], "half": HALF[id(p)],
            "county": p.get("county_id")}


# ---- 1–3 the stones ---------------------------------------------------------------------------------------------------
LANG = ["monoftong", "au_monoftong", "o_runa", "r_for_R", "nasal_utelamnad", "h_saknas", "stungen_e", "stungen_y",
        "stungen_g", "bindrunor", "short_twig", "skilj_punkt", "skilj_kryss", "skilj_kolon", "skilj_apostrof", "skilj_plus",
        "skilj_blandat", "prep_at"]
SED = ["cat_sjalvminne", "cat_bro_vag", "cat_kristen", "cat_fard", "cat_arv", "cat_ting", "cat_magisk", "pm_hednisk",
       "pm_kors", "pm_bon", "pm_sjal", "pm_stungna", "pm_signatur", "has_carver", "msg_dod_uppgift", "msg_dod_borta",
       "msg_resa", "msg_gald", "msg_gard", "msg_berom", "kvinna_resare", "kvinna_ensam", "flera_resare", "kvinna_dod",
       "rel_barn", "rel_foralder", "rel_syskon", "rel_make", "rel_slakt", "rel_ej_slakt", "drengr", "thegn", "god",
       "hog_sten", "i_grupp"]
PLATS = ["nara_gravfalt", "nara_hog", "nara_vag", "nara_bro", "nara_fornborg", "nara_church", "nara_vatten",
         "nara_gammalt_namn", "nara_ungt_namn", "nara_kultnamn", "nara_centralort", "pa_plats", "lokal"]
NATUR = ["mat_granit", "mat_sandsten", "mat_kalksten", "mat_gnejs"]
drag = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv"))))
ORD = [c for c in drag[0] if c.startswith("ord_")]
rows = []
for f in drag:
    sg = f["signum"]
    if sg not in stone_par:
        continue
    yr = (float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None
    per = "odaterad" if yr is None else "–1010" if yr < 1010 else "1010–1040" if yr < 1040 else "1040–1070" if yr < 1070 else "1070–"
    rows.append({"signum": sg, **unit_cols(stone_par[sg]), "period": per, "carver": f.get("carver") or "",
                 **{k: f.get(k, "") for k in LANG + ORD + SED + PLATS + NATUR}})
# stone halves as before: parishes alternately within the province, ordered by mean dating (graves and names have no
# dating, so their parishes are ordered by latitude)
pm = defaultdict(list)
for r, f in zip(rows, [f for f in drag if f["signum"] in stone_par]):
    pm[(r["province"], r["parish"])].append((float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None)
for pv in {k[0] for k in pm}:
    keys = sorted((k for k in pm if k[0] == pv), key=lambda k: (all(y is None for y in pm[k]), np.mean([y for y in pm[k] if y] or [0]), -len(pm[k]), k[1]))
    hh = {k: i % 2 for i, k in enumerate(keys)}
    for r in rows:
        if r["province"] == pv:
            r["half"] = hh[(r["province"], r["parish"])]
with open(os.path.join(HERE, "stenar.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("stenar", len(rows))

# ---- 4 the graves -----------------------------------------------------------------------------------------------------
FORMS = {"kvadratisk": r"kvadratisk", "rektangular": r"rektangul", "treudd": r"treudd", "skeppsformig": r"skepps",
         "oval": r"\boval", "rund": r"\brund"}
GF = {"hogar": r"\bhögar\b|\b(?:1|en|ett)\s+hög\b",  # not "1 m hög" (height)
      "kvadratisk": r"kvadratisk", "rektangular": r"rektangul", "treudd": r"treudd",
      "skeppsformig": r"skepps", "oval": r"\boval", "stenkrets": r"domarring|stenkrets", "rest_sten": r"rest(?:a)? sten",
      "mittsten": r"mittsten|sten i mitten", "kantkedja": r"kantkedja"}
seen, graves = set(), []
for f in ("grav_pt.csv", "grav_pg.csv"):
    for r in csv.DictReader(open(RAA + f)):
        if r["uuid"] in seen or not r.get("X"):
            continue
        seen.add(r["uuid"])
        pt = (float(r["Y"]), float(r["X"]))
        p = parish_of(re.split(r"[,/]", r["socken"] or ""), pt)
        if p is None:
            continue
        d = (r["beskrivning"] or "").lower()
        t = r["lamningstyp"]
        g = {"uuid": r["uuid"], **unit_cols(p), "typ": t}
        if t == "Gravfält":
            for k, rx in GF.items():
                g["gf_" + k] = int(bool(re.search(rx, d)))
            m_h = re.search(r"(\d+)\s+(?:st\s+)?högar", d); m_s = re.search(r"(\d+)\s+(?:[a-zåäö]+\s+){0,3}stensättningar", d)
            g["gf_fler_hogar"] = (int(int(m_h.group(1)) > int(m_s.group(1))) if (m_h and m_s) else "")
        else:
            for k in ("Hög", "Stensättning", "Röse", "Grav markerad av sten/block", "Stenkrets/stenrad", "Flatmarksgrav"):
                g["typ_" + re.sub(r"\W+", "_", k.lower())] = int(t == k)
            if t == "Stensättning":
                for k, rx in FORMS.items():
                    g["form_" + k] = int(bool(re.search(rx, d[:200])))
        graves.append(g)
cols = sorted({k for g in graves for k in g}, key=lambda k: (not k in ("uuid", "province", "region", "harad", "parish", "half", "typ"), k))
with open(os.path.join(HERE, "gravar.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(graves)
print("gravar", len(graves), Counter(g["typ"] for g in graves).most_common())

# ---- 5 the place names --------------------------------------------------------------------------------------------------
END = {"sta": r"sta$", "by": r"by$", "inge": r"(?:inge|inga|unge)$", "tuna": r"tuna$", "hem": r"(?:hem|um)$", "vin": r"vin$",
       "losa": r"lösa$", "aker": r"åker$", "berga": r"berga$", "torp": r"torp$", "ryd": r"(?:ryd|red)$", "hult": r"hult$",
       "boda": r"(?:boda|bo)$", "sater": r"(?:säter|sätra)$", "stad": r"stad$", "lunda": r"(?:lunda|lund)$",
       "hammar": r"hammar$", "vik": r"vik$", "nas": r"näs$", "holm": r"holm$", "husby": r"^husby"}
kult = {r["name"].strip().lower() for r in csv.DictReader(open(os.path.join(ROOT, "data", "ortnamn", "kultnamn.csv")))
        if r.get("name")}
names = []
for r in csv.DictReader(open(os.path.join(ROOT, "data", "ortnamn", "platser.csv"))):
    if r["place"] not in ("hamlet", "village", "isolated_dwelling", "farm", "locality"):
        continue
    pt = (float(r["lat"]), float(r["lon"]))
    p = nearest(pt)
    if p is None:
        continue
    n = r["name"].strip().lower()
    if not n or " " in n:
        continue
    names.append({"name": r["name"], **unit_cols(p), **{"n_" + k: int(bool(re.search(rx, n))) for k, rx in END.items()},
                  "n_kult": int(n in kult)})
with open(os.path.join(HERE, "namn.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(names[0])); w.writeheader(); w.writerows(names)
print("namn", len(names), Counter(n["province"] for n in names).most_common(8))
json.dump({"LANG": LANG, "ORD": ORD, "SED": SED, "PLATS": PLATS, "NATUR": NATUR,
           "GRAV": [c for c in cols if c.startswith(("gf_", "typ_", "form_"))],
           "NAMN": ["n_" + k for k in END] + ["n_kult"]}, open(os.path.join(HERE, "drag.json"), "w"), ensure_ascii=False, indent=1)
