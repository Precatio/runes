"""Självkontrollen (analysplaner/2026-11-10-sjalvkontroll-gravfalt.md), steg 2: lägger gravfältsklasserna (klasser.py)
och länen mot exakt samma stenar som originalet (utdata/familjens_plats/stenar.csv). Skriver stenar_sk.csv för analys.R.
    .venv/bin/python utdata/familjens_plats/sjalvkontroll/data.py"""
from __future__ import annotations

import collections
import csv
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src import places  # noqa: E402
import klasser  # noqa: E402

FP = os.path.dirname(HERE)
D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")

st = pd.read_csv(os.path.join(FP, "stenar.csv"), low_memory=False)
c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
ins = c[(c.moved == 0) & (c.lost == 0) & c.lat.notna()].reset_index(drop=True)
assert list(ins.signum) == list(st.signum), "stenarna är inte desamma som i originalet"
xy = places._xy(ins.lat.to_numpy(float), ins.lon.to_numpy(float))

g = klasser.load()
gxy = places._xy([x["lat"] for x in g], [x["lon"] for x in g])


def within(mask, r_m):
    t = cKDTree(gxy[np.asarray(mask, bool)])
    d, _ = t.query(xy)
    return (d <= r_m).astype(int)


allm = np.ones(len(g), bool)
V = np.array([x["V"] for x in g])
Vnb = np.array([x["V_utan_block"] for x in g])
Y = np.array([x["Y"] for x in g])
st["y_alla"] = within(allm, 500)
assert (st.y_alla == st.y1_gravfalt).all(), "alla gravfält inom 500 m ska vara originalets utfall"
st["y_V"] = within(V, 500)
st["y_Y"] = within(Y, 500)
st["y_V250"] = within(V, 250)
st["y_V_utan_block"] = within(Vnb, 500)
# Registrets täthet: antal registrerade gravfält (alla) 1–5 km från stenen
t_all = cKDTree(gxy)
n5 = np.array([len(t_all.query_ball_point(p, 5000)) for p in xy])
n1 = np.array([len(t_all.query_ball_point(p, 1000)) for p in xy])
st["gfdens"] = np.log1p(n5 - n1)

# Stenarnas län: stenens egen KMR-post; annars närmaste gravfält med län i samma landskap
kmr = json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]
lan_by_id = {r["id"]: (r["lan"], r["landskap"]) for r in
             csv.DictReader(open(os.path.join(ROOT, "data", "raa", "runristning_lan.csv"), encoding="utf-8"))}
sig2 = {}
for r in kmr:
    if r["kmr_id"] in lan_by_id and lan_by_id[r["kmr_id"]][0]:
        for s in r["signa"]:
            sig2.setdefault(s, lan_by_id[r["kmr_id"]])
lan, how = [], []
# landskapets namn i registret för varje landskapskod, ur de stenar som har en KMR-post
pmap = collections.defaultdict(collections.Counter)
for s, p in zip(st.signum, st.province):
    if s in sig2:
        pmap[p][sig2[s][1]] += 1
pname = {p: cnt.most_common(1)[0][0] for p, cnt in pmap.items()}
gprov = np.array([x["province"] for x in g])
glan = np.array([x["lan"] for x in g])
for i, (s, p) in enumerate(zip(st.signum, st.province)):
    if s in sig2:
        lan.append(sig2[s][0])
        how.append("egen KMR-post")
        continue
    m = (glan != "") & (gprov == pname.get(p, "")) if p in pname else (glan != "")
    if not m.any():
        m = glan != ""
    j = np.argmin(((gxy[m] - xy[i]) ** 2).sum(1))
    lan.append(glan[m][j])
    how.append("närmaste gravfält i landskapet" if p in pname else "närmaste gravfält")
st["lan"] = lan
st["lan_hur"] = how
cols = ["signum", "province", "parish", "style_from", "style_to", "grupp", "lt", "y1_gravfalt", "y_alla", "y_V", "y_Y",
        "y_V250", "y_V_utan_block", "gfdens", "lan", "lan_hur"]
st[cols].to_csv(os.path.join(HERE, "stenar_sk.csv"), index=False)
sel = st[st.grupp.notna()]
print(len(st), "stenar,", len(sel), "i grupp eller ensamma")
print(sel.lan_hur.value_counts().to_dict())
print(sel.lan.value_counts().to_dict())
