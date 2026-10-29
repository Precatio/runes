"""Tabell för planen analysplaner/2026-10-29-kyrkan-tog-over.md: en rad per svensk runsten (ej försvunnen) med
gravfält, kyrka och tid. Skriver kyrkan.csv för kyrkan.R.    .venv/bin/python utdata/familjens_plats/kyrkan_data.py"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import places  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")
PLACE = re.compile(r"kyrka\b|kyrkan\b|kyrkogård|kyrkoruin|ödekyrk", re.I)
PLACEMENT = re.compile(r"kyrk|vapenhus|\btorn|bogård|stiglucka|koret|sakristi|gravkor|inmurad", re.I)

c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
c = c[c.lost == 0].reset_index(drop=True)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
plc = [recs[s].get("placement") or "" for s in c.signum]
plname = [recs[s].get("place") or "" for s in c.signum]
c["kyrka_plac"] = [int(bool(PLACEMENT.search(p))) for p in plc]
c["kyrka"] = [int(bool(PLACEMENT.search(p) or PLACE.search(n))) for p, n in zip(plc, plname)]
c["inmurad"] = [int("inmurad" in p.lower()) for p in plc]
c["pa_plats"] = ((c.moved == 0) & c.lat.notna()).astype(int)

has = c.lat.notna().to_numpy()
xy = np.full((len(c), 2), np.nan)
xy[has] = places._xy(c.lat[has].to_numpy(float), c.lon[has].to_numpy(float))
gp = places.places()["gravfalt"]
gd, _ = cKDTree(places._xy([p["lat"] for p in gp], [p["lon"] for p in gp])).query(xy[has])
c["gravfalt"], c["gravfalt250"] = np.nan, np.nan
c.loc[has, "gravfalt"] = (gd <= 500).astype(int)
c.loc[has, "gravfalt250"] = (gd <= 250).astype(int)
all_tree = cKDTree(xy[has])
c["lt"] = np.nan
c.loc[has, "lt"] = np.log1p([len(all_tree.query_ball_point(p, 5000)) - 1 for p in xy[has]])
cols = ["signum", "province", "parish", "style", "style_from", "style_to", "cat_kristen", "moved", "pa_plats", "kyrka",
        "kyrka_plac", "inmurad", "gravfalt", "gravfalt250", "lt"]
c[cols].to_csv(os.path.join(OUT, "kyrkan.csv"), index=False)
print(len(c), c[["pa_plats", "kyrka", "kyrka_plac", "inmurad"]].sum().to_dict(),
      "båda", int(((c.pa_plats == 1) & (c.kyrka == 1)).sum()))
