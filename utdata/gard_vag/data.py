"""Tabell per sten för planen analysplaner/2026-10-29-gard-gravfalt-vag.md: i grupp/ensam och kontroller ur
utdata/familjens_plats/stenar.csv, avstånd till bytomter, boplatser och vägar i KMR och inventeringstätheten.
    .venv/bin/python utdata/gard_vag/data.py      Skriver stenar.csv."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import places  # noqa: E402

RAA = os.path.join(ROOT, "data", "raa")
c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e", "corpus.csv"), low_memory=False)
m = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e", "messages.csv"))
fp = pd.read_csv(os.path.join(ROOT, "utdata", "familjens_plats", "stenar.csv"))
st = fp[["signum", "province", "parish", "style", "style_from", "style_to", "grupp", "ensam2km", "lt"]].merge(
    c[["signum", "lat", "lon", "cat_arv", "cat_bro_vag"]], on="signum").merge(m[["signum", "msg_gard"]], on="signum", how="left")
xy = places._xy(st.lat.to_numpy(float), st.lon.to_numpy(float))


def pts(df):
    return places._xy(df.lat.to_numpy(float), df.lon.to_numpy(float))


lam = pd.read_csv(os.path.join(RAA, "lamningar.csv"))
ex = lambda f: pd.read_csv(os.path.join(RAA, "lamningar_extra", f))  # noqa: E731
LAYERS = {
    "bytomt": pts(ex("bytomt_gårdstomt.csv")),
    "boplats": pts(pd.concat([ex("boplats.csv"), ex("husgrund__förhistorisk_medeltida.csv")])),
    "vag": pts(pd.concat([lam[lam.type.isin(["färdväg", "färdvägssystem", "bro"])], ex("vägmärke.csv")])),
}
for k, p in LAYERS.items():
    t = cKDTree(p)
    d, _ = t.query(xy)
    st[f"d_{k}"] = d
    st[f"tat_{k}"] = np.log1p([len(t.query_ball_point(q, 5000)) for q in xy])
st["bytomt500"] = (st.d_bytomt <= 500).astype(int)
st["bytomt250"] = (st.d_bytomt <= 250).astype(int)
st["bytomt1000"] = (st.d_bytomt <= 1000).astype(int)
st["boplats500"] = (st.d_boplats <= 500).astype(int)
st["boplats250"] = (st.d_boplats <= 250).astype(int)
st["boplats1000"] = (st.d_boplats <= 1000).astype(int)
st["vag200"] = (st.d_vag <= 200).astype(int)
st["vag100"] = (st.d_vag <= 100).astype(int)
st["vag400"] = (st.d_vag <= 400).astype(int)
st["arv"] = ((st.cat_arv.fillna(0) > 0) | (st.msg_gard.fillna(0) > 0)).astype(int)
st["bro"] = (st.cat_bro_vag.fillna(0) > 0).astype(int)
st["log_d_bytomt"] = np.log(st.d_bytomt + 1)
st.to_csv(os.path.join(OUT, "stenar.csv"), index=False)
print(len(st), st[["grupp", "arv", "bro", "bytomt500", "boplats500", "vag200"]].sum().to_dict())
