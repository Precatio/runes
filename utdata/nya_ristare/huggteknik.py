"""Huggtekniken inom modellens grupper (analysplaner/2026-11-24-nya-ristare-3d.md, sha ffb9b051).

    .venv/bin/python utdata/nya_ristare/huggteknik.py
"""
import glob
import hashlib
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-24-nya-ristare-3d.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("ffb9b051"), "planen är ändrad efter låsningen"
CORE4 = ["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "bottenradie_mm"]
SAND = {"Sö 128", "Sö 134", "Sö 160", "Sö 161", "Sö 162", "Sö 163", "Sö 207", "Sö 370", "Sö Fv1948;282", "Sö Fv1954;19"}
B = 9999

vals = {}
for f in glob.glob(os.path.join(ROOT, "utdata", "Rak", "referenser_g7", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    if "signum" not in d:
        continue
    s = d["signum"].replace("Sö 137A", "Sö 137").replace("Sö 137B", "Sö 137")
    vals.setdefault(s, []).append([d["means"][k] for k in CORE4])
sig = sorted(vals)
X = np.array([np.mean(vals[s], axis=0) for s in sig])
X = (X - X.mean(0)) / X.std(0)
D = np.hypot.reduce if False else np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
ix = {s: i for i, s in enumerate(sig)}
sand = np.array([s in SAND for s in sig])

G = json.load(open(os.path.join(HERE, "grupper.json"), encoding="utf-8"))
groups = [(g["id"], g["typ"], [ix[s] for s in g["stenar"] if s in ix]) for g in G]
groups = [(gid, typ, m) for gid, typ, m in groups if len(m) >= 2]
assert [g[0] for g in groups] == ["G039", "G052", "G055", "G084", "G097", "G105"], [g[0] for g in groups]


def gmean(m, Dm=D):
    return float(np.mean([Dm[a, b] for k, a in enumerate(m) for b in m[k + 1:]]))


obs_each = [gmean(m) for _, _, m in groups]
obs = float(np.mean(obs_each))
rng = np.random.default_rng(20261124)
null, null_each = [], []
for _ in range(B):
    perm = np.arange(len(sig))
    for mat in (True, False):
        idx = np.where(sand == mat)[0]
        perm[idx] = rng.permutation(idx)
    # gruppernas stenar ersätts med de stenar som fått deras plats; storlek och bergart behålls
    each = [gmean([perm[a] for a in m]) for _, _, m in groups]
    null.append(np.mean(each))
    null_each.append(each)
null = np.array(null)
null_each = np.array(null_each)
p = float((np.sum(null <= obs) + 1) / (B + 1))
per = [{"grupp": gid, "typ": typ, "stenar": [sig[i] for i in m], "avstånd": round(o, 3),
        "omblandat_medel": round(float(null_each[:, k].mean()), 3), "p": round(float((np.sum(null_each[:, k] <= o) + 1) / (B + 1)), 4)}
       for k, ((gid, typ, m), o) in enumerate(zip(groups, obs_each))]
unk = [k for k, g in enumerate(groups) if g[1] == "okänd hand"]
obs_u = float(np.mean([obs_each[k] for k in unk]))
p_u = float((np.sum(null_each[:, unk].mean(1) <= obs_u) + 1) / (B + 1))
allpairs = float(np.mean(D[np.triu_indices(len(sig), 1)]))
out = {"plan_sha": "ffb9b051", "stenar": len(sig), "medel_alla_par": round(allpairs, 3), "H3D": {"observerat": round(obs, 3),
       "omblandat_medel": round(float(null.mean()), 3), "p": round(p, 4), "håller": p < 0.05},
       "okänd_hand": {"observerat": round(obs_u, 3), "p": round(p_u, 4)}, "grupper": per}
json.dump(out, open(os.path.join(HERE, "huggteknik.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
