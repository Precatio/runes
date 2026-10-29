"""Familjens plats: tabellen per sten och testen inom grupperna (14–15), enligt den låsta planen
analysplaner/2026-10-29-familjens-plats.md. Skriver stenar.csv (för analys.R) och inom_grupper.json.
    .venv/bin/python utdata/familjens_plats/data.py"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import entities, places  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")
NPERM = 9999
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
rng = np.random.default_rng(2026)

c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
msg = pd.read_csv(os.path.join(D, "messages.csv"))
c = c.merge(msg[["signum", "msg_gard"]], on="signum", how="left")
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
dims = json.load(open(os.path.join(ROOT, "data", "stone_dimensions.json")))["stones"]
xy_all = places._xy(c.lat.fillna(0).to_numpy(float), c.lon.fillna(0).to_numpy(float))
has = c.lat.notna().to_numpy()

st = c[(c.moved == 0) & (c.lost == 0) & c.lat.notna()].reset_index(drop=True)
xy = places._xy(st.lat.to_numpy(float), st.lon.to_numpy(float))
tree = cKDTree(xy)
dmat = tree.sparse_distance_matrix(tree, 2000, output_type="coo_matrix")
near_any = np.zeros(len(st), bool)
nn = np.full(len(st), np.inf)
for i, j, d in zip(dmat.row, dmat.col, dmat.data):
    if i == j:
        continue
    nn[i] = min(nn[i], d)
    if 25 < d <= 500:
        near_any[i] = True
d1, _ = tree.query(xy, k=2)
nn = d1[:, 1]
st["grupp"] = np.where(near_any, 1, np.where(nn > 1000, 0, np.nan))
st["ensam2km"] = np.where(near_any, 1, np.where(nn > 2000, 0, np.nan))
# Lokal täthet: alla runstenar med koordinater (också flyttade) inom 5 km
all_tree = cKDTree(xy_all[has])
st["lt"] = np.log1p(np.array([len(all_tree.query_ball_point(p, 5000)) - 1 for p in xy]))


def within(points_xy, radius_m):
    t = cKDTree(points_xy)
    d, _ = t.query(xy)
    return (d <= radius_m).astype(int), d


def kind_xy(kind):
    pts = places.places()[kind]
    return places._xy([p["lat"] for p in pts], [p["lon"] for p in pts])


gr = pd.read_csv(os.path.join(ROOT, "data", "raa", "gransmarken.csv"))
pl = pd.read_csv(os.path.join(ROOT, "data", "ortnamn", "platser.csv"))
pl = pl[pl.place.isin(["village", "hamlet", "farm", "isolated_dwelling", "locality"])]
name = pl.name.str.lower()
OLD = r"(?:sta|stad|by|inge|inga|vin|hem|lösa|tuna)$"
YOUNG = r"(?:torp|torpet|ryd|hult|boda)$"
old_xy = places._xy(pl[name.str.contains(OLD)].lat, pl[name.str.contains(OLD)].lon)
young_xy = places._xy(pl[name.str.contains(YOUNG)].lat, pl[name.str.contains(YOUNG)].lon)
cult_xy = np.vstack([kind_xy("cult_a"), kind_xy("cult_b")])

for scale, suffix in ((1.0, ""), (0.5, "_halv")):
    st["y1_gravfalt" + suffix] = within(kind_xy("gravfalt"), 500 * scale)[0]
    st["y2_hog" + suffix] = within(kind_xy("hog"), 500 * scale)[0]
    st["y3_vag" + suffix] = within(kind_xy("vag"), 500 * scale)[0]
    st["y4_grans" + suffix] = within(places._xy(gr.lat, gr.lon), 500 * scale)[0]
    st["y5_kyrka" + suffix] = within(kind_xy("church"), 2000 * scale)[0]
    st["y6_gammalt_namn" + suffix] = within(old_xy, 1000 * scale)[0]
    st["y7_ungt_namn" + suffix] = within(young_xy, 1000 * scale)[0]
    st["y8_kultnamn" + suffix] = within(cult_xy, 2000 * scale)[0]
    st["y9_centralort" + suffix] = within(kind_xy("central"), 5000 * scale)[0]
st["y10_namnger_plats"] = [int(bool(entities.extract(recs[s])["places"])) for s in st.signum]
st["y11_arv_gard"] = ((st.cat_arv.fillna(0) > 0) | (st.msg_gard.fillna(0) > 0)).astype(int)
h = [dims.get(s, {}) for s in st.signum]
st["y12_hog_sten"] = [(1 if x.get("height_m", 0) >= 1.6 else 0) if x.get("status") == "ok" and not x.get("fragment")
                      and x.get("height_m") else np.nan for x in h]
st["y13_signerad"] = st.pm_signatur
cols = ["signum", "province", "parish", "carver", "style", "style_from", "style_to", "n_words_core", "grupp", "ensam2km",
        "lt", "cat_kristen"] + [k for k in st.columns if k.startswith("y")]
st[cols].to_csv(os.path.join(OUT, "stenar.csv"), index=False)

# ---- Test 14–15 inom grupperna ----------------------------------------------------------------------------------------
pairs = [(i, j) for i, j, d in zip(dmat.row, dmat.col, dmat.data) if i < j and 25 < d <= 500]
n = len(st)
from scipy.sparse import coo_matrix  # noqa: E402
adj = coo_matrix((np.ones(len(pairs)), ([p[0] for p in pairs], [p[1] for p in pairs])), shape=(n, n))
ncomp, lab = connected_components(adj, directed=False)
prov = st.province.to_numpy(dtype=object)
style = st["style"].fillna("").to_numpy(dtype=object)
dated = np.isin(style, STYLES)
groups = [np.where((lab == g) & dated)[0] for g in range(ncomp)]
groups = [g for g in groups if len(g) >= 2]
# Halvorna: socken för socken som i change.R (stenens socken; en grupp/ett par hör till halvan för sin första sten)
t50 = ((st.style_from + st.style_to) / 2 - 1050) / 50
pk = st.parish.fillna("_" + st.signum)
pinfo = pd.DataFrame({"province": st.province, "pk": pk, "t": t50}).groupby(["province", "pk"]).agg(
    mt=("t", "mean"), n=("t", "size")).reset_index()
pinfo = pinfo.sort_values(["province", "mt", "n"], ascending=[True, True, False], na_position="last")
pinfo["half"] = pinfo.groupby("province").cumcount().map(lambda r: "A" if r % 2 == 0 else "B")
half = pd.Series(list(zip(st.province, pk))).map(dict(zip(zip(pinfo.province, pinfo.pk), pinfo.half))).to_numpy()


def perm_within(mask_idx):
    p = np.arange(n)
    for pv in np.unique(prov):
        ix = np.where((prov == pv) & mask_idx)[0]
        p[ix] = rng.permutation(ix)
    return p


def depth(gs, perm):
    return np.mean([len(set(style[perm[g]])) for g in gs]) if gs else np.nan


def test14(gs):
    obs = depth(gs, np.arange(n))
    sims = np.array([depth(gs, perm_within(dated)) for _ in range(NPERM)])
    return {"groups": len(gs), "stones": int(sum(len(g) for g in gs)), "mean_styles": obs,
            "expected": float(sims.mean()), "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}


kr = st.cat_kristen.to_numpy(float)
kk = ~np.isnan(kr)
pp = [(i, j) for i, j in pairs if kk[i] and kk[j]]


def mixed(ps, perm):
    return np.mean([(kr[perm[i]] > 0) != (kr[perm[j]] > 0) for i, j in ps]) if ps else np.nan


def test15(ps):
    obs = mixed(ps, np.arange(n))
    sims = np.array([mixed(ps, perm_within(kk)) for _ in range(NPERM)])
    lo, hi = (1 + (sims <= obs).sum()) / (NPERM + 1), (1 + (sims >= obs).sum()) / (NPERM + 1)
    both_k = np.mean([(kr[i] > 0) and (kr[j] > 0) for i, j in ps]) if ps else np.nan
    return {"pairs": len(ps), "share_mixed": obs, "expected": float(sims.mean()), "share_both_christian": both_k,
            "p": float(min(1.0, 2 * min(lo, hi))), "direction": "fler blandade" if obs > sims.mean() else "färre blandade"}


res = {"plan": "analysplaner/2026-10-29-familjens-plats.md", "n_insitu": n, "n_grupp": int(np.nansum(st.grupp == 1)),
       "n_ensam": int(np.nansum(st.grupp == 0)),
       "t14": test14(groups), "t15": test15(pp)}
for h_ in ("A", "B"):
    res[f"t14_{h_}"] = test14([g for g in groups if half[g[0]] == h_])
    res[f"t15_{h_}"] = test15([(i, j) for i, j in pp if half[i] == h_])
up = np.isin(prov, ["U", "Sö"])
res["t14_U_So"] = test14([g for g in groups if up[g[0]]])
res["t15_U_So"] = test15([(i, j) for i, j in pp if up[i]])
json.dump(res, open(os.path.join(OUT, "inom_grupper.json"), "w"), ensure_ascii=False, indent=1, default=float)
print({k: res[k] for k in ("n_insitu", "n_grupp", "n_ensam")})
for k in ("t14", "t14_A", "t14_B", "t15", "t15_A", "t15_B"):
    print(k, {kk_: (round(v, 3) if isinstance(v, float) else v) for kk_, v in res[k].items()})
