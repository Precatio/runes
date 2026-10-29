"""Tabell per sten för planen analysplaner/2026-10-29-bon-vid-kultplatsen.md: bön, datering, avstånd till teofora
namn, gårdar (KMR bytomt/gårdstomt), tidiga och sena kyrkor och källor med tradition.
    .venv/bin/python utdata/kultplatser/data.py      Skriver stenar.csv."""
import json
import os

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
FP = "3f58e9339191761e"
EARLY = 1200
FARM_EXCLUDE_KM = 0.3

c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "corpus.csv"), low_memory=False)
c = c[c["lat"].notna() & c["lon"].notna() & (c["moved"].fillna(0) == 0)].copy()


_T = Transformer.from_crs(4326, 3006, always_xy=True)  # SWEREF 99 TM, as r/remains.R


def xyz(lat, lon):
    x, y = _T.transform(np.asarray(lon, float), np.asarray(lat, float))
    return np.c_[x, y] / 1000


S = xyz(c["lat"], c["lon"])


def nearest(df):
    t = cKDTree(xyz(df["lat"], df["lon"]))
    d, i = t.query(S)
    return d, i  # km in SWEREF 99 TM


names = pd.read_csv(os.path.join(ROOT, "data", "ortnamn", "kultnamn.csv"))
cult = names[names["tier"] == "A"].reset_index(drop=True)
d, i = nearest(cult)
c["km_cult"] = d
c["cult_name"] = cult["name"].values[i]
c["cult_god"] = cult["god"].values[i]

# Farms: KMR farm sites more than 300 m from every theophoric name (the name's point is itself a village or farm)
farms = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar_extra", "bytomt_gårdstomt.csv"))
farms = farms[farms["lat"].notna() & farms["lon"].notna()]
fd, _ = cKDTree(xyz(cult["lat"], cult["lon"])).query(xyz(farms["lat"], farms["lon"]))
farms = farms[fd > FARM_EXCLUDE_KM]
c["km_farm"], _ = nearest(farms)

ch = pd.read_csv(os.path.join(ROOT, "data", "ortnamn", "kyrkor.csv"))
c["km_church_early"], _ = nearest(ch[ch["year"] <= EARLY])
c["km_church_late"], _ = nearest(ch[ch["year"] > EARLY])

sp = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar_extra", "källa_med_tradition.csv"))
c["km_spring"], _ = nearest(sp[sp["lat"].notna() & sp["lon"].notna()])

off = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar_extra", "offerplats.csv"))
off = off[off["lat"].notna()]
od, _ = cKDTree(xyz(off["lat"], off["lon"])).query(xyz(cult["lat"], cult["lon"]))
cult["km_offerplats"] = od
ce, _ = cKDTree(xyz(ch[ch["year"] <= EARLY]["lat"], ch[ch["year"] <= EARLY]["lon"])).query(xyz(cult["lat"], cult["lon"]))
cult["km_church_early"] = ce

runor = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))["inscriptions"]
moved_runor = {x["signum"] for x in runor if x.get("original") is False}
c["moved_runor"] = c["signum"].isin(moved_runor).astype(int)

c["bon"] = c["cat_kristen"].astype(int)
cols = ["signum", "province", "parish", "carver", "style", "style_from", "style_to", "bon", "lat", "lon", "km_cult",
        "cult_name", "cult_god", "km_farm", "km_church_early", "km_church_late", "km_spring", "moved_runor"]
c[cols].to_csv(os.path.join(OUT, "stenar.csv"), index=False)
cult.to_csv(os.path.join(OUT, "namn.csv"), index=False)
print(len(c), "stenar;", int((c["km_cult"] < 2).sum()), "inom 2 km från ett teofort namn")
