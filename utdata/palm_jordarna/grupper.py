"""Lerkanten med stenarna i grupp som enhet (analysplaner/2026-11-26-lerkanten-grupper.md): grupperna (1 km,
src.spatial_groups.link) för stenarna i kontroller_punkter.csv. grupper.R räknar proven.
    .venv/bin/python utdata/palm_jordarna/grupper.py && Rscript utdata/palm_jordarna/grupper.R
"""
import hashlib
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import places, spatial_groups  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-26-lerkanten-grupper.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest() == open(PLAN + ".sha256").read().split()[0], "planen ändrad"
pts = pd.read_csv(os.path.join(HERE, "kontroller_punkter.csv"))
stones = sorted(pts.stone.unique())
corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
pos = corp.drop_duplicates("signum").set_index("signum")[["lat", "lon"]]
missing = [s for s in stones if s not in pos.index]
assert not missing, missing[:5]
xy = places._xy(pos.loc[stones, "lat"].to_numpy(float), pos.loc[stones, "lon"].to_numpy(float))
g = spatial_groups.link(np.asarray(xy), 1000.0)
pd.DataFrame({"stone": stones, "grupp": g}).to_csv(os.path.join(HERE, "grupper_lerkant.csv"), index=False)
print(len(stones), "stenar i", len(set(g)), "grupper; största gruppen", max(np.bincount(g)))
