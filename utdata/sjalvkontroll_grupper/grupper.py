"""Tilläggsplanen analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md (låst, SHA-256 c1e3d2ab…, commit 4570096):
självkontrollen med stenar i grupp som en enhet.

Det här skriptet gör grupperna (1 km, `src/spatial_groups.link`), tar fram den närmaste gamla vägens registerobjekt (fid)
för L1 med samma segment och samma klassning som `utdata/riktning/vaglinjer.py`, och räknar proven R (S0, beskrivande
S2 och S3) och L (L1, beskrivande L1b och L0) med en sten per grupp. Gruppnumren för gravfältens 657 stenar skrivs till
`gravfalt_grupper.csv`, som `gravfalt.R` (prov G) läser.

    .venv/bin/python utdata/sjalvkontroll_grupper/grupper.py      → resultat.json, gravfalt_grupper.csv
"""
import csv
import hashlib
import json
import os
import sqlite3
import struct
import sys

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import places, spatial_groups  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-19-sjalvkontroll-tillagg-grupper.md")
SHA = open(PLAN + ".sha256").read().split()[0]
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest() == SHA and SHA.startswith("c1e3d2ab"), "planen är ändrad"
SEED = int(SHA[:8], 16)  # planen: de första 8 tecknen i planens SHA-256, hexadecimalt
NDRAW, NPERM, NPERM_GM = 1000, 999, 9999
LINK_M = 1000.0
RIK = os.path.join(ROOT, "utdata", "riktning")
GPKG = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/raa/lamningar_sverige.gpkg"
KLASSER = os.path.join(RIK, "vaglinjer_l1_klasser.csv")


# ---- grupperna ------------------------------------------------------------------------------------------------------------
def groups_of(lat, lon, shared=None):
    xy = places._xy(np.asarray(lat, float), np.asarray(lon, float))
    return np.array(spatial_groups.link(xy, LINK_M, shared))


# ---- gravfälten: gruppnummer för gravfalt.R -------------------------------------------------------------------------------
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
sk = pd.read_csv(os.path.join(ROOT, "utdata", "familjens_plats", "sjalvkontroll", "stenar_sk.csv"))
gv = sk[sk.grupp.notna()].reset_index(drop=True)
assert len(gv) == 657 and int(gv.grupp.sum()) == 185
gv["sgroup"] = groups_of([RD[s]["lat"] for s in gv.signum], [RD[s]["lon"] for s in gv.signum])
G_INFO = {"stenar": len(gv), "grupper": int(gv.sgroup.nunique()),
          "grupper_med_stenar_i_grupp": int(gv[gv.grupp == 1].sgroup.nunique()),
          "grupper_med_ensamma": int(gv[gv.grupp == 0].sgroup.nunique()),
          "blandade_grupper": int((gv.groupby("sgroup").grupp.nunique() > 1).sum())}
assert (G_INFO["grupper_med_stenar_i_grupp"], G_INFO["grupper_med_ensamma"], G_INFO["blandade_grupper"]) == (73, 472, 0)
gv[["signum", "sgroup"]].to_csv(os.path.join(OUT, "gravfalt_grupper.csv"), index=False)

# ---- riktningen: stenarna och koordinaterna -------------------------------------------------------------------------------
LL = pd.read_csv(os.path.join(RIK, "stenar.csv")).drop_duplicates("signum")[["signum", "lat", "lon"]]
S = pd.read_csv(os.path.join(RIK, "sjalvkontroll_stenar.csv")).merge(LL, on="signum", how="left")
assert len(S) == 214 and S.lat.notna().all()
L = pd.read_csv(os.path.join(RIK, "vaglinjer_stenar.csv")).merge(LL, on="signum", how="left")
assert len(L) == 214 and L.lat.notna().all()


# ---- L1: närmaste gamla vägs registerobjekt, som i vaglinjer.py (gpkg_lines, wkb_lines, segments, nearest) -----------------
def gpkg_lines(blob):
    flags = blob[3]
    env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    return wkb_lines(memoryview(blob)[8 + env:])


def wkb_lines(b):
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


def segments(lines, tags):
    a, b, g = [], [], []
    for ln, tg in zip(lines, tags):
        if len(ln) < 2:
            continue
        a.append(ln[:-1]); b.append(ln[1:]); g.append(np.full(len(ln) - 1, tg))
    return np.vstack(a), np.vstack(b), np.concatenate(g)


def nearest_fid(XY, seg, radius=1000.0):
    """vaglinjer.nearest, med registerobjektet (fid) för det närmaste segmentet tillagt."""
    A, B, G = seg
    lo, hi = np.minimum(A, B), np.maximum(A, B)
    res = np.full((len(XY), 3), np.nan)
    fid = [None] * len(XY)
    for i, (x, y) in enumerate(XY):
        m = (lo[:, 0] <= x + radius) & (hi[:, 0] >= x - radius) & (lo[:, 1] <= y + radius) & (hi[:, 1] >= y - radius)
        if not m.any():
            continue
        a, b, gg = A[m], B[m], G[m]
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
        fid[i] = int(gg[j])
    return res, fid


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
del k_lines
L_XY = places._xy(L.lat.to_numpy(float), L.lon.to_numpy(float))
res, FID = nearest_fid(L_XY, KMR)
# samma avstånd och bäring som vaglinjer.py skrev (kontroll att det är samma beräkning)
ok = L.kmr_dist.notna()
assert np.array_equal(ok.to_numpy(), ~np.isnan(res[:, 0]))
assert np.allclose(res[ok.to_numpy(), 0], L.kmr_dist[ok], atol=1e-6) and np.allclose(res[ok.to_numpy(), 1], L.kmr_brg[ok], atol=1e-6)
L["kmr_fid"] = FID


# ---- proven ---------------------------------------------------------------------------------------------------------------
def perm_index(strata_idx, n, nperm, rng):
    """nperm omblandningar av 0..n-1 inom varje stratum (matris nperm × n)."""
    P = np.tile(np.arange(n), (nperm, 1))
    for g in strata_idx:
        if len(g) > 1:
            P[:, g] = np.asarray(g)[np.argsort(rng.random((nperm, len(g))), axis=1)]
    return P


def one_per_group(f, t, strata, groups, seed):
    """Planens huvudprov: en sten per grupp, provet oförändrat (medel-cos, 999 omblandningar inom stratum, ensidigt),
    1 000 dragningar."""
    rng = np.random.default_rng(seed)
    members = [np.flatnonzero(groups == g) for g in np.unique(groups)]
    obs, exp, p, inom = (np.empty(NDRAW) for _ in range(4))
    for r in range(NDRAW):
        sel = np.array([m[rng.integers(len(m))] for m in members])
        ff, tt, ss = f[sel], t[sel], strata[sel]
        idx = list(pd.Series(np.arange(len(sel))).groupby(ss).indices.values())
        P = perm_index(idx, len(sel), NPERM, rng)
        o = np.cos(np.radians(ff - tt)).mean()
        sims = np.cos(np.radians(ff[P] - tt[None, :])).mean(1)
        obs[r], exp[r] = o, sims.mean()
        p[r] = (1 + (sims >= o).sum()) / (NPERM + 1)
        inom[r] = (np.abs((ff - tt + 180) % 360 - 180) <= 45).mean()
    return {"grupper": len(members), "dragningar": NDRAW, "omblandningar": NPERM,
            "median_medel_cos": float(np.median(obs)), "median_vantat": float(np.median(exp)),
            "median_p": float(np.median(p)), "andel_dragningar_p_under_005": float((p < 0.05).mean()),
            "median_andel_inom_45": float(np.median(inom)), "p_kvartiler": [float(np.quantile(p, .25)), float(np.quantile(p, .75))]}


def group_mean(f, t, strata, groups, seed):
    """Beskrivande: gruppmedel av medel-cos, omblandning sten för sten inom stratum (9 999), som i Känt före låsningen."""
    rng = np.random.default_rng(seed)
    idx = list(pd.Series(np.arange(len(f))).groupby(strata).indices.values())
    P = perm_index(idx, len(f), NPERM_GM, rng)
    gcode = pd.factorize(groups)[0]
    cnt = np.bincount(gcode)

    def stat(c):  # c: (k × n) cos-värden → medel över grupperna av gruppens medel
        s = np.zeros((c.shape[0], len(cnt)))
        np.add.at(s.T, gcode, c.T)
        return (s / cnt).mean(1)
    o = stat(np.cos(np.radians(f - t))[None, :])[0]
    sims = np.concatenate([stat(np.cos(np.radians(f[P[i:i + 1000]] - t[None, :]))) for i in range(0, NPERM_GM, 1000)])
    return {"medel_av_gruppmedel": float(o), "vantat": float(sims.mean()),
            "p": float((1 + (sims >= o).sum()) / (NPERM_GM + 1))}


def run(df, target_col, stratum, shared_col=None, name=""):
    x = df[df[target_col].notna() & df[stratum].notna()].reset_index(drop=True)
    shared = list(x[shared_col]) if shared_col else None
    g1 = groups_of(x.lat, x.lon)
    g = groups_of(x.lat, x.lon, shared) if shared_col else g1
    f, t, s = x.riktning.to_numpy(float), x[target_col].to_numpy(float), x[stratum].to_numpy()
    out = {"stenar": len(x), "grupper": int(len(set(g)))}
    if shared_col:
        out["grupper_bara_1km"] = int(len(set(g1)))
    if out["grupper"] < 5:
        out["status"] = "kan inte prövas (färre än fem grupper)"
        return out, x, g
    out["en_sten_per_grupp"] = one_per_group(f, t, s, g, SEED)
    out["gruppmedel"] = group_mean(f, t, s, g, SEED)
    return out, x, g


R = {}
R["S0"], _, _ = run(S, "vag", "province")
R["S2"], _, _ = run(S, "vag", "lan")
R["S3"], _, _ = run(S[~S.flyttad.astype(bool)], "vag", "province")
s0 = R["S0"]["en_sten_per_grupp"]
R["S0"]["haller"] = bool(s0["median_medel_cos"] > s0["median_vantat"] and s0["median_p"] < 0.05)
assert R["S0"]["stenar"] == 120 and R["S0"]["grupper"] == 101

# L1: gamla vägars linjer inom 2–500 m (vaglinjer.target("kmr", 500))
L["t_kmr"] = L.kmr_brg.where((L.kmr_dist <= 500) & (L.kmr_dist >= 2))
L["t_osm"] = L.osm_brg.where((L.osm_dist <= 500) & (L.osm_dist >= 2))
L["fid_l1"] = [int(v) if pd.notna(d_) and 2 <= d_ <= 500 and v is not None else None for v, d_ in zip(L.kmr_fid, L.kmr_dist)]
Lx = L.copy()
R["L1"], l1x, l1g = run(Lx, "t_kmr", "province", "fid_l1")
R["L1b"], _, _ = run(Lx[~Lx.flyttad.astype(bool)], "t_kmr", "province", "fid_l1")
R["L0"], _, _ = run(Lx, "t_osm", "province")
assert R["L1"]["stenar"] == 34 and R["L1"]["grupper_bara_1km"] == 25 and R["L0"]["stenar"] == 213
l1 = R["L1"]["en_sten_per_grupp"]
R["L1"]["holm_ovre"] = min(1.0, 2 * l1["median_p"])
R["L1"]["haller"] = bool(l1["median_medel_cos"] > l1["median_vantat"] and 2 * l1["median_p"] < 0.05)
R["L1"]["registerobjekt"] = {"stenar_med_objekt": int(l1x.fid_l1.notna().sum()), "olika_objekt": int(l1x.fid_l1.nunique())}

out = {"plan": "analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md", "sha256": SHA, "slumpfro": SEED,
       "lankning_m": LINK_M, "gravfalt_grupper": G_INFO, "prov": R,
       "not": "S0 och L1 avgörs av en sten per grupp; S2, S3, L1b, L0 och gruppmedlen är beskrivande. Varje prov har "
              "sin egen slumpström med samma frö."}
json.dump(out, open(os.path.join(OUT, "resultat.json"), "w"), ensure_ascii=False, indent=1)
for k, v in R.items():
    e = v.get("en_sten_per_grupp", {})
    print(f"{k:4} stenar {v['stenar']:3} grupper {v['grupper']:3} {('(1 km: %d) ' % v['grupper_bara_1km']) if 'grupper_bara_1km' in v else ''}"
          f"median cos {e.get('median_medel_cos', float('nan')):.3f} väntat {e.get('median_vantat', float('nan')):.3f} "
          f"median p {e.get('median_p', float('nan')):.4f} andel p<0,05 {e.get('andel_dragningar_p_under_005', float('nan')):.2f} "
          f"inom45 {e.get('median_andel_inom_45', float('nan')):.2f} | gruppmedel p {v.get('gruppmedel', {}).get('p', float('nan')):.4f}"
          f"{' HÅLLER' if v.get('haller') else (' håller inte' if 'haller' in v else '')}")
print("gravfälten:", G_INFO)
