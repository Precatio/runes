"""r för ʀ: klustret i västra Uppland – bygdens tal eller ristarens vana? Skriver utdata/blogg/build/rforR.json.
Omräknad 2026-10-31 på korpus e83202e01a5e6d27 med samma definitioner som forskningsrapporten (build_rapport_r_for_R.py):
flyttade stenar räknas inte någonstans (klustret räknas på stenar som står kvar, och en flyttad sten räknades förut som
'utanför' fast den kan stå mitt i bygden)."""
import os
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[3])  # projektmappen, var den än ligger
import json, math
import numpy as np, pandas as pd
from scipy import stats

D = os.path.join(_PROJ, "data/cache/r/corpus/e83202e01a5e6d27")
d = pd.read_csv(f"{D}/corpus.csv", low_memory=False)
h = json.load(open(f"{D}/hotspots.json"))
pat = next(x for x in h["patterns"] if x["key"] == "r_for_R")
cl = pat["clusters"][0]
inside = set(cl["stones"])
known = d[d.pm_r_for_R.notna() & (d.moved.isna() | (d.moved == 0))].copy()
known["inside"] = known.signum.isin(inside)
# distance to the cluster centre, for every stone
lat0, lon0 = cl["lat"], cl["lon"]
def km(lat, lon):
    p = math.pi / 180
    a = math.sin((lat - lat0) * p / 2) ** 2 + math.cos(lat0 * p) * math.cos(lat * p) * math.sin((lon - lon0) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))
known["km"] = [km(a, b) if pd.notna(a) else np.nan for a, b in zip(known.lat, known.lon)]
out = {"cluster": {k: cl[k] for k in ("center", "radius_km", "n", "cases", "rate_in", "rate_out", "rr", "p", "q_bh")},
       "halves": cl["halves"], "moran": pat["moran"], "n_known": int(len(known)), "share_all": float(known.pm_r_for_R.mean())}

def carver(name):
    c = known[known.carvers_all.fillna("").str.contains(name)]
    i, o = c[c.inside], c[~c.inside]
    t = [[int(i.pm_r_for_R.sum()), int(len(i) - i.pm_r_for_R.sum())], [int(o.pm_r_for_R.sum()), int(len(o) - o.pm_r_for_R.sum())]]
    p = stats.fisher_exact(t)[1] if len(o) and len(i) else None
    return {"n_in": len(i), "k_in": int(i.pm_r_for_R.sum()), "n_out": len(o), "k_out": int(o.pm_r_for_R.sum()), "p": p,
            "styles": c["style"].fillna("–").value_counts().to_dict(),
            "out_places": o.parish.fillna("").value_counts().head(6).to_dict(),
            "out_median_km": float(o.km.median()) if len(o) else None}
out["erik"] = carver("Erik")
out["balle"] = carver("Balle")
print("Erik", out["erik"]); print("Balle", out["balle"])

# the carvers in the cluster who never use it, and their stones elsewhere
ins = known[known.inside]
out["inside_by_carver"] = ins.groupby(ins.carver.fillna("okänd")).pm_r_for_R.agg(["size", "sum"]).sort_values("size", ascending=False).head(8).astype(int).to_dict("index")
print(out["inside_by_carver"])

# time inside the cluster
ins_t = ins[ins["style"].notna()]
out["inside_time"] = ins_t.groupby("style").pm_r_for_R.agg(["size", "sum"]).astype(int).to_dict("index")
print("tid i klustret", out["inside_time"])

# hypercorrection: words ending in r written with the ʀ-rune (r_R / r_n), inside vs outside
def words(df):
    return {"R_n": int(df.R_n.sum()), "R_r": int(df.R_r.sum()), "r_n": int(df.r_n.sum()), "r_R": int(df.r_R.sum()),
            "eftir_n": int(df.R_eftir_n.sum()), "eftir_r": int(df.R_eftir_r.sum())}
w_in, w_out = words(ins), words(known[~known.inside])
out["words_in"], out["words_out"] = w_in, w_out
t = [[w_in["r_R"], w_in["r_n"] - w_in["r_R"]], [w_out["r_R"], w_out["r_n"] - w_out["r_R"]]]
out["hyper_p"] = stats.fisher_exact(t)[1]
out["hyper_or"] = stats.fisher_exact(t)[0]
print("ord inne", w_in, "ute", w_out, "hyper p", out["hyper_p"], "or", out["hyper_or"])
for nm in ("Erik", "Balle"):
    c = known[known.carvers_all.fillna("").str.contains(nm)]
    out[f"words_{nm.lower()}_in"] = words(c[c.inside]); out[f"words_{nm.lower()}_out"] = words(c[~c.inside])
    print(nm, "ord inne", out[f"words_{nm.lower()}_in"], "ute", out[f"words_{nm.lower()}_out"])

# unattributed stones with the spelling in the cluster
u = ins[ins.carver.isna() & (ins.pm_r_for_R == 1)]
out["unsigned"] = u[["signum", "place", "parish", "style"]].fillna("–").to_dict("records")
print("osignerade", out["unsigned"])
# distance gradient for all stones: share by distance band from the centre
bands = [0, 30, 50, 100, 200, 2000]
known["band"] = pd.cut(known.km, bands, right=False)
g = known.groupby("band", observed=True).pm_r_for_R.agg(["size", "mean"])
out["bands"] = [{"from": int(b.left), "to": int(b.right), "n": int(r["size"]), "share": float(r["mean"])} for b, r in g.iterrows()]
print(out["bands"])
# provinces
pv = known.groupby("province").pm_r_for_R.agg(["size", "mean"]).sort_values("size", ascending=False).head(8)
out["provinces"] = {k: {"n": int(v["size"]), "share": float(v["mean"])} for k, v in pv.iterrows()}
print(out["provinces"])
json.dump(out, open(os.path.join(_PROJ, "utdata/blogg/build/rforR.json"), "w"), ensure_ascii=False, indent=1, default=str)
