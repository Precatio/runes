"""Ristningens riktning mot vägens linje enligt den låsta planen analysplaner/2026-11-10-riktning-vaglinjer.md
(L0 dagens vägar ur OpenStreetMap, K kalibreringen, L1 registrets gamla vägar som linjer; L2 räknas senare).

    .venv/bin/python utdata/riktning/vaglinjer.py --klassa    Skriver bara vaglinjer_l1_klasser.csv (först).
    .venv/bin/python utdata/riktning/vaglinjer.py --osm       Tar ut OSM-vägarna inom 1,5 km (ogr2ogr; ingen bäring).
    .venv/bin/python utdata/riktning/vaglinjer.py             Räknar K, L0 och L1; skriver vaglinjer.json och vaglinjer_stenar.csv.

OSM: © OpenStreetMaps bidragsgivare, ODbL (Geofabriks Sverigeutdrag). KMR: Riksantikvarieämbetet, CC0."""
import json
import os
import re
import sqlite3
import struct
import subprocess
import sys

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import places  # noqa: E402

GEO = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor"
GPKG = os.path.join(GEO, "raa", "lamningar_sverige.gpkg")
OSM_ZIP = os.path.join(GEO, "osm", "sweden-latest-free.shp.zip")
OSM_UT = os.path.join(GEO, "osm", "vagar_kring_stenar.gpkg")
BUF = os.path.join(GEO, "osm", "stenar_buffert_1500m.geojson")
KLASSER = os.path.join(OUT, "vaglinjer_l1_klasser.csv")
NPERM = 9999
SEED = 2026
GAMMAL = re.compile(r"hålväg|vägbank|vadställe|kavelbro|förhistori|järnålder|vikingatid|bronsålder|medeltid")
UNG = re.compile(r"banvall|järnväg|fäbod|militärväg|valv")
HALV_BANK = re.compile(r"hålväg|vägbank")
RUNSTEN = re.compile(r"runsten|runristning")
OSM_UTOM = ("motorway", "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
            "steps", "bridleway", "cycleway", "footway")


def stenar() -> pd.DataFrame:
    d0 = pd.read_csv(os.path.join(OUT, "stenar.csv"))
    d = d0.sort_values("vag_text", na_position="last").drop_duplicates("signum").sort_index().reset_index(drop=True)
    assert len(d) == 214
    fl = pd.read_csv(os.path.join(OUT, "sjalvkontroll_stenar.csv"))[["signum", "flyttad"]]
    d = d.merge(fl, on="signum", how="left")
    assert d.flyttad.notna().all() and int(d.flyttad.sum()) == 91
    xy = places._xy(d.lat.to_numpy(float), d.lon.to_numpy(float))
    d["x"], d["y"] = xy[:, 0], xy[:, 1]
    return d


# --- GeoPackage-geometri (linjer) ---
def gpkg_lines(blob: bytes) -> list[np.ndarray]:
    flags = blob[3]
    env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    return wkb_lines(memoryview(blob)[8 + env:])


def wkb_lines(b) -> list[np.ndarray]:
    bo = "<" if b[0] == 1 else ">"
    t = struct.unpack(bo + "I", b[1:5])[0]
    dims = 2
    if t & 0x80000000:
        dims += 1
    if t & 0x40000000:
        dims += 1
    t &= 0x0FFFFFFF
    if t >= 3000:
        dims, t = 4, t - 3000
    elif t >= 2000:
        dims, t = 3, t - 2000
    elif t >= 1000:
        dims, t = 3, t - 1000
    if t == 2:
        n = struct.unpack(bo + "I", b[5:9])[0]
        a = np.frombuffer(bytes(b[9:9 + n * dims * 8]), dtype=bo + "f8").reshape(n, dims)[:, :2]
        return [a.copy()]
    if t == 5:
        n = struct.unpack(bo + "I", b[5:9])[0]
        out, off = [], 9
        for _ in range(n):
            bb = b[off:]
            bo2 = "<" if bb[0] == 1 else ">"
            m = struct.unpack(bo2 + "I", bb[5:9])[0]
            out += wkb_lines(bb)
            off += 9 + m * dims * 8
        return out
    raise ValueError(f"geometrityp {t}")


def klassa() -> None:
    con = sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True)
    q = ("SELECT fid, uuid, lamningsnummer, lamningstyp, antikvariskbedomning, lan, beskrivning "
         "FROM 'lämningar_sverige_linestring' WHERE lamningstyp IN ('Färdväg','Färdvägssystem','Bro')")
    k = pd.read_sql_query(q, con)
    con.close()
    b = k.beskrivning.fillna("").str.lower()
    k["gammal"] = (b.str.contains(GAMMAL) & ~b.str.contains(UNG)).astype(int)
    k["halvag_vagbank"] = (k.gammal.astype(bool) & b.str.contains(HALV_BANK)).astype(int)
    k["fornlamning"] = (k.antikvariskbedomning == "Fornlämning").astype(int)
    k["nämner_runsten"] = b.str.contains(RUNSTEN).astype(int)
    k.drop(columns=["beskrivning"]).to_csv(KLASSER, index=False)
    print("linjer", len(k), k.lamningstyp.value_counts().to_dict(), "gamla", int(k.gammal.sum()),
          k[k.gammal == 1].lamningstyp.value_counts().to_dict(), "hålväg/vägbank", int(k.halvag_vagbank.sum()),
          "gamla fornlämning", int((k.gammal & k.fornlamning).sum()), "gamla som nämner runsten", int((k.gammal & k["nämner_runsten"]).sum()))


def osm_extract() -> None:
    d = stenar()
    feats = []
    for x, y in zip(d.x, d.y):
        a = np.linspace(0, 2 * np.pi, 49)
        ring = [[float(x + 1500 * np.cos(t)), float(y + 1500 * np.sin(t))] for t in a]
        feats.append({"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [ring]}})
    json.dump({"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3006"}},
               "features": feats}, open(BUF, "w"))
    where = "fclass NOT IN (" + ",".join(f"'{c}'" for c in OSM_UTOM) + ")"
    if os.path.exists(OSM_UT):
        os.remove(OSM_UT)
    cmd = ["ogr2ogr", "-f", "GPKG", OSM_UT, f"/vsizip/{OSM_ZIP}/gis_osm_roads_free_1.shp", "-t_srs", "EPSG:3006",
           "-where", where, "-clipdst", BUF, "-nln", "vagar", "-nlt", "MULTILINESTRING", "-explodecollections"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


if "--klassa" in sys.argv:
    klassa()
    sys.exit(0)
if "--osm" in sys.argv:
    osm_extract()
    sys.exit(0)

assert os.path.exists(KLASSER) and os.path.exists(OSM_UT)
d = stenar()
XY = d[["x", "y"]].to_numpy()


def segments(lines: list[np.ndarray], tags: np.ndarray):
    a, b, g = [], [], []
    for ln, tg in zip(lines, tags):
        if len(ln) < 2:
            continue
        a.append(ln[:-1]); b.append(ln[1:]); g.append(np.full(len(ln) - 1, tg))
    return np.vstack(a), np.vstack(b), np.concatenate(g)


def nearest(seg, mask_tag=None, radius=1000.0):
    """Per sten: avstånd, bäring till närmaste punkt och linjens riktning (axial) där, inom radien."""
    A, B, G = seg
    if mask_tag is not None:
        keep = mask_tag(G)
        A, B = A[keep], B[keep]
    lo, hi = np.minimum(A, B), np.maximum(A, B)
    res = np.full((len(XY), 3), np.nan)
    for i, (x, y) in enumerate(XY):
        m = (lo[:, 0] <= x + radius) & (hi[:, 0] >= x - radius) & (lo[:, 1] <= y + radius) & (hi[:, 1] >= y - radius)
        if not m.any():
            continue
        a, b = A[m], B[m]
        ab = b - a
        L2 = (ab ** 2).sum(1)
        t = np.clip(((np.array([x, y]) - a) * ab).sum(1) / np.where(L2 > 0, L2, 1), 0, 1)
        p = a + ab * t[:, None]
        dist = np.hypot(p[:, 0] - x, p[:, 1] - y)
        j = int(np.argmin(dist))
        if dist[j] > radius:
            continue
        brg = (np.degrees(np.arctan2(p[j, 0] - x, p[j, 1] - y)) + 360) % 360
        ldir = (np.degrees(np.arctan2(ab[j, 0], ab[j, 1])) + 360) % 180
        res[i] = (dist[j], brg, ldir)
    return res


# --- OSM-linjer ---
con = sqlite3.connect(f"file:{OSM_UT}?mode=ro", uri=True)
geomcol = con.execute("SELECT column_name FROM gpkg_geometry_columns WHERE table_name='vagar'").fetchone()[0]
rows = con.execute(f"SELECT fclass, {geomcol} FROM vagar").fetchall()
con.close()
o_lines, o_tags = [], []
for fc, blob in rows:
    for ln in gpkg_lines(blob):
        o_lines.append(ln); o_tags.append(fc)
OSM = segments(o_lines, np.array(o_tags, dtype=object))
n_osm = len(rows)
del rows

# --- KMR-linjer ---
kl = pd.read_csv(KLASSER).set_index("fid")
con = sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True)
k_lines, k_fid = [], []
for fid, blob in con.execute("SELECT fid, geometri FROM 'lämningar_sverige_linestring' "
                             "WHERE lamningstyp IN ('Färdväg','Färdvägssystem','Bro')"):
    if fid in kl.index and kl.at[fid, "gammal"] == 1:
        for ln in gpkg_lines(blob):
            k_lines.append(ln); k_fid.append(fid)
con.close()
KMR = segments(k_lines, np.array(k_fid))
old_hb = set(kl.index[kl.halvag_vagbank == 1])
old_forn = set(kl.index[(kl.gammal == 1) & (kl.fornlamning == 1)])
old_utan_rs = set(kl.index[(kl.gammal == 1) & (kl["nämner_runsten"] == 0)])

R = {}
R["osm"] = nearest(OSM)
R["osm_tpu"] = nearest(OSM, lambda g: np.isin(g, ["track", "track_grade1", "track_grade2", "track_grade3", "track_grade4",
                                                  "track_grade5", "path", "unclassified"]))
R["kmr"] = nearest(KMR)
R["kmr_hb"] = nearest(KMR, lambda g: np.isin(g, list(old_hb)))
R["kmr_forn"] = nearest(KMR, lambda g: np.isin(g, list(old_forn)))
R["kmr_utan_rs"] = nearest(KMR, lambda g: np.isin(g, list(old_utan_rs)))
for k, r in R.items():
    d[f"{k}_dist"], d[f"{k}_brg"], d[f"{k}_ldir"] = r[:, 0], r[:, 1], r[:, 2]

# gon-rättelser (beskrivande ristningar; K använder rättade vägar)
gon = json.load(open(os.path.join(OUT, "gon_kontroll.json"), encoding="utf-8"))
rv = {(g["signum"], float(g["last"])): float(g["ratt"]) for g in gon["rattade_vagar"]}
rr = {(g["signum"], float(g["last"])): float(g["ratt"]) for g in gon["rattade_ristningar"]}
d["vag_text_gon"] = [rv.get((s, float(v)), v) if pd.notna(v) else np.nan for s, v in zip(d.signum, d.vag_text)]
d["riktning_gon"] = [rr.get((s, float(v)), v) for s, v in zip(d.signum, d.riktning)]
n_gon_v = int((d.vag_text.notna() & (d.vag_text_gon != d.vag_text)).sum())
n_gon_r = int((d.riktning_gon != d.riktning).sum())


def target(src: str, radius: float) -> pd.Series:
    """Bäringen till vägen i källan inom radien; NaN utan väg eller närmare än 2 m."""
    ok = (d[f"{src}_dist"] <= radius) & (d[f"{src}_dist"] >= 2)
    return d[f"{src}_brg"].where(ok)


def test(mask: pd.Series, tgt: pd.Series, facing: str = "riktning") -> dict:
    x = d[mask & tgt.notna()].copy()
    x["t"] = tgt[x.index]
    x = x.reset_index(drop=True)
    if len(x) < 5:
        return {"n": len(x)}
    f, t = x[facing].to_numpy(float), x.t.to_numpy(float)
    groups = list(x.groupby("province").indices.values())
    rng = np.random.default_rng(SEED)
    stat = lambda ff: np.cos(np.radians(ff - t)).mean()
    obs = stat(f)
    sims = np.empty(NPERM)
    for i in range(NPERM):
        idx = np.arange(len(x))
        for g in groups:
            idx[g] = rng.permutation(g)
        sims[i] = stat(f[idx])
    return {"n": len(x), "medel_cos": float(obs), "vantat": float(sims.mean()),
            "andel_inom_45": float((np.abs((f - t + 180) % 360 - 180) <= 45).mean()),
            "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}


def tvars(mask: pd.Series, src: str, radius: float, facing: str = "riktning") -> dict:
    ok = mask & (d[f"{src}_dist"] <= radius) & (d[f"{src}_dist"] >= 2)
    x = d[ok]
    ang = np.abs(((x[facing] - x[f"{src}_ldir"]) + 90) % 180 - 90)  # 0 = längs linjen, 90 = vinkelrätt
    return {"n": int(len(x)), "andel_tvars": float((ang >= 45).mean()) if len(x) else None,
            "andel_langs": float((ang < 45).mean()) if len(x) else None}


ALLA = pd.Series(True, index=d.index)
OFL = ~d.flyttad.astype(bool)


def prov(src: str, radius: float = 500, facing: str = "riktning") -> dict:
    t = target(src, radius)
    return {"a": test(ALLA, t, facing), "b": test(OFL, t, facing),
            "tvars_a": tvars(ALLA, src, radius, facing), "for_nara_2m": int(((d[f"{src}_dist"] < 2)).sum())}


def held(r: dict) -> bool:
    return bool("medel_cos" in r and r["medel_cos"] > r["vantat"] and r["p"] < 0.05)


def b_ok(r: dict) -> bool:
    if "medel_cos" not in r:
        return False
    return r["medel_cos"] > r["vantat"] and (r["n"] < 30 or r["p"] < 0.05)


# --- K ---
def kalib(radius: float) -> dict:
    ok = d.vag_text_gon.notna() & (d.osm_dist <= radius) & (d.osm_dist >= 2)
    x = d[ok]
    diff = np.abs((x.osm_brg - x.vag_text_gon + 180) % 360 - 180)
    return {"n_textvag": int(d.vag_text_gon.notna().sum()), "n": int(len(x)),
            "andel_inom_45": float((diff <= 45).mean()) if len(x) else None,
            "median_skillnad": float(np.median(diff)) if len(x) else None}


K = kalib(500)
K["godkand"] = bool(K["andel_inom_45"] is not None and K["andel_inom_45"] >= 0.70)

L0 = prov("osm")
L0a, L0b = L0["a"], L0["b"]
gate = bool(L0a.get("n", 0) >= 30 and held(L0a) and L0a["andel_inom_45"] >= 0.40 and "medel_cos" in L0b and L0b["medel_cos"] > L0b["vantat"])
L0["grind_haller"] = gate
L0["b_pkrav_uppfyllt"] = b_ok(L0b)

L1 = prov("kmr")
L1a, L1b = L1["a"], L1["b"]
if L1a.get("n", 0) < 30:
    L1["status"] = "kan inte prövas"
else:
    p1 = L1a["p"]
    # Holm över L1 och L2. L2 är inte räknad än: 2·p är den största Holm-p L1 kan få, p den minsta.
    L1["holm_p_ovre"] = min(1.0, 2 * p1)
    L1["holm_p_nedre"] = p1
    raw_ok = L1a["medel_cos"] > L1a["vantat"]
    if not gate:
        L1["status"] = "beskrivande (grinden håller inte)"
    elif raw_ok and 2 * p1 < 0.05 and b_ok(L1b):
        L1["status"] = "håller (oavsett L2)"
    elif not raw_ok or p1 >= 0.05 or not b_ok(L1b):
        L1["status"] = "håller inte (oavsett L2)"
    else:
        L1["status"] = "avgörs av L2 (Holm)"

besk = {"K_300": kalib(300), "K_1000": kalib(1000),
        "L0_300": prov("osm", 300), "L0_1000": prov("osm", 1000), "L1_300": prov("kmr", 300), "L1_1000": prov("kmr", 1000),
        "L1_halvag_vagbank": prov("kmr_hb"), "L1_fornlamning": prov("kmr_forn"), "L1_utan_runstenslinjer": prov("kmr_utan_rs"),
        "L0_track_path_unclassified": prov("osm_tpu"),
        "L0_gon": prov("osm", facing="riktning_gon"), "L1_gon": prov("kmr", facing="riktning_gon"),
        "tvars_L0_b": tvars(OFL, "osm", 500), "tvars_L1_b": tvars(OFL, "kmr", 500)}

info = {"stenar": len(d), "flyttade": int(d.flyttad.sum()), "osm_vagar_utdrag": n_osm, "osm_segment": int(len(OSM[0])),
        "kmr_gamla_linjer": int((kl.gammal == 1).sum()), "kmr_gamla_lamningar": int(kl[kl.gammal == 1].uuid.nunique()),
        "kmr_segment": int(len(KMR[0])), "gon_rattade_textvagar": n_gon_v, "gon_rattade_ristningar": n_gon_r}
keep = ["signum", "province", "half", "riktning", "riktning_gon", "vag_text", "vag_text_gon", "flyttad"] + \
       [c for c in d.columns if c.split("_")[0] in ("osm", "kmr")]
d[keep].to_csv(os.path.join(OUT, "vaglinjer_stenar.csv"), index=False)
out = {"plan": "analysplaner/2026-11-10-riktning-vaglinjer.md", "info": info, "K": K, "L0": L0, "L1": L1,
       "L2": "inte räknad (väntar på avritningen)", "beskrivande": besk}
json.dump(out, open(os.path.join(OUT, "vaglinjer.json"), "w"), ensure_ascii=False, indent=1)


def fmt(r):
    if "medel_cos" not in r:
        return f"n {r.get('n')} (för få)"
    return f"n {r['n']:3d}  cos {r['medel_cos']:.3f} mot {r['vantat']:.3f}  inom 45° {r['andel_inom_45']:.2f}  p {r['p']:.4f}"


print(json.dumps(info, ensure_ascii=False))
print("K", K)
print("L0 a", fmt(L0a), "| b", fmt(L0b), "| grind", gate, "| tvärs", L0["tvars_a"], "| <2 m", L0["for_nara_2m"])
print("L1 a", fmt(L1a), "| b", fmt(L1b), "|", L1.get("status"), "| Holm-p", L1.get("holm_p_nedre"), "–", L1.get("holm_p_ovre"),
      "| tvärs", L1["tvars_a"], "| <2 m", L1["for_nara_2m"])
for k, r in besk.items():
    if k.startswith("K_") or k.startswith("tvars"):
        print(" ", k, r)
    else:
        print(" ", k, "a", fmt(r["a"]), "| b", fmt(r["b"]), "| tvärs", r["tvars_a"])
