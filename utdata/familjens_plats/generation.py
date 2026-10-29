"""Restes stengrupperna under en generation? Enligt den låsta planen analysplaner/2026-10-29-en-generation.md.
    .venv/bin/python utdata/familjens_plats/generation.py      Skriver generation.json."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import places  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")
NSIM = 9999
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
rng = np.random.default_rng(2026)

c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
c["year"] = (c.style_from + c.style_to) / 2
# Bygdens stenar: stildaterade, med koordinater, ej försvunna (också flyttade)
P = c[(c.lost == 0) & c.lat.notna() & c["style"].isin(STYLES)].reset_index(drop=True)
pxy = places._xy(P.lat.to_numpy(float), P.lon.to_numpy(float))
ptree = cKDTree(pxy)
p_style = P["style"].to_numpy(dtype=object)
p_year = P.year.to_numpy(float)
p_insitu = (P.moved == 0).to_numpy()

# Grupperna som i data.py
st = c[(c.moved == 0) & (c.lost == 0) & c.lat.notna()].reset_index(drop=True)
xy = places._xy(st.lat.to_numpy(float), st.lon.to_numpy(float))
tree = cKDTree(xy)
dm = tree.sparse_distance_matrix(tree, 500, output_type="coo_matrix")
keep = (dm.row < dm.col) & (dm.data > 25)
n = len(st)
adj = coo_matrix((np.ones(keep.sum()), (dm.row[keep], dm.col[keep])), shape=(n, n))
_, lab = connected_components(adj, directed=False)
style = st["style"].fillna("").to_numpy(dtype=object)
dated = np.isin(style, STYLES)
groups = [np.where((lab == g) & dated)[0] for g in np.unique(lab)]
groups = [g for g in groups if len(g) >= 2]

t50 = ((st.style_from + st.style_to) / 2 - 1050) / 50
pk = st.parish.fillna("_" + st.signum)
pinfo = pd.DataFrame({"province": st.province, "pk": pk, "t": t50}).groupby(["province", "pk"]).agg(
    mt=("t", "mean"), n=("t", "size")).reset_index()
pinfo = pinfo.sort_values(["province", "mt", "n"], ascending=[True, True, False], na_position="last")
pinfo["half"] = pinfo.groupby("province").cumcount().map(lambda r: "A" if r % 2 == 0 else "B")
half = pd.Series(list(zip(st.province, pk))).map(dict(zip(zip(pinfo.province, pinfo.pk), pinfo.half))).to_numpy()
prov = st.province.to_numpy(dtype=object)
carver = st.carver.fillna("").to_numpy(dtype=object)
year = ((st.style_from + st.style_to) / 2).to_numpy(float)


def pool(g, radius, insitu_only=False):
    near = set().union(*[ptree.query_ball_point(xy[i], radius) for i in g])
    excl = set().union(*[ptree.query_ball_point(xy[i], 500) for i in g])
    ix = np.array(sorted(near - excl), dtype=int)
    return ix[p_insitu[ix]] if insitu_only and len(ix) else ix


def draws(ix, k):
    """NSIM dragningar av k stenar ur poolen utan återläggning: (antal stilgrupper, alla samma, spännvidd)."""
    order = np.argsort(rng.random((NSIM, len(ix))), axis=1)[:, :k]
    sty, yr = p_style[ix][order], p_year[ix][order]
    nst = np.array([len(set(r)) for r in sty])
    return nst, (nst == 1).astype(float), yr.max(1) - yr.min(1)


def run(gs, radius=10000, insitu_only=False):
    rows = []
    for g in gs:
        ix = pool(g, radius, insitu_only)
        if len(ix) < 10:
            continue
        rows.append((g, draws(ix, len(g))))
    if not rows:
        return {"groups": 0}
    obs_n = np.mean([len(set(style[g])) for g, _ in rows])
    obs_same = np.mean([len(set(style[g])) == 1 for g, _ in rows])
    obs_span = np.mean([year[g].max() - year[g].min() for g, _ in rows])
    sim_n = np.mean([d[0] for _, d in rows], axis=0)
    sim_same = np.mean([d[1] for _, d in rows], axis=0)
    sim_span = np.mean([d[2] for _, d in rows], axis=0)
    return {"groups": len(rows), "stones": int(sum(len(g) for g, _ in rows)),
            "mean_styles": obs_n, "expected": float(sim_n.mean()),
            "p": float((1 + (sim_n <= obs_n).sum()) / (NSIM + 1)),
            "share_all_same": obs_same, "share_all_same_expected": float(sim_same.mean()),
            "p_all_same": float((1 + (sim_same >= obs_same).sum()) / (NSIM + 1)),
            "span_years": obs_span, "span_expected": float(sim_span.mean()),
            "provinces": pd.Series([prov[g[0]] for g, _ in rows]).value_counts().to_dict()}


main = run(groups)
A, B = run([g for g in groups if half[g[0]] == "A"]), run([g for g in groups if half[g[0]] == "B"])
status = ("håller" if main["p"] < 0.05 and A["p"] < 0.05 and B["p"] < 0.05 else
          "antydan" if main["p"] < 0.05 else "ingen skillnad påvisad")
one_carver = [g for g in groups if not (all(carver[g] != "") and len(set(carver[g])) == 1)]
rob = {"bygd_5km": run(groups, 5000), "bygd_20km": run(groups, 20000), "pool_pa_plats": run(groups, insitu_only=True),
       "utan_en_ristare": run(one_carver), "U_So": run([g for g in groups if prov[g[0]] in ("U", "Sö")])}
res = {"plan": "analysplaner/2026-10-29-en-generation.md", "main": main, "halves": {"A": A, "B": B},
       "status": status, "robustness": rob}
json.dump(res, open(os.path.join(OUT, "generation.json"), "w"), ensure_ascii=False, indent=1, default=float)


def line(name, r):
    if not r.get("groups"):
        return f"{name}: inga grupper"
    return (f"{name:16s} grupper {r['groups']:3d} stenar {r['stones']:3d}  stilgrupper {r['mean_styles']:.2f} väntat "
            f"{r['expected']:.2f} p {r['p']:.4f} | alla samma {r['share_all_same']:.2f} väntat "
            f"{r['share_all_same_expected']:.2f} p {r['p_all_same']:.4f} | spann {r['span_years']:.0f} år väntat "
            f"{r['span_expected']:.0f}")


print(line("alla", main), "\n" + line("halva A", A), "\n" + line("halva B", B), "\nutslag:", status)
for k, r in rob.items():
    print(line(k, r))
print(main["provinces"])
