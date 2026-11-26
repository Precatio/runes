"""Vad försvann? (analysplaner/2026-11-26-vad-forsvann.md) – data till vad_forsvann.R.
    .venv/bin/python utdata/vad_forsvann/data.py
Skriver data.csv (huvudprovet: teckning mot teckning) och data_foto.csv (beskrivande: förlorade ur teckning mot
bevarade planschstenar i samma socknar)."""
import hashlib
import json
import os
import sys
from collections import defaultdict

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-26-vad-forsvann.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest() == open(PLAN + ".sha256").read().split()[0], "planen ändrad"
C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
TYP = {"bautil": "Bautil", "rhezelius": "Rhezelius", "peringskiold": "Peringskiöld", "ovrig": "övrig",
       "Bautil": "Bautil", "Rhezelius": "Rhezelius", "Peringskiöld": "Peringskiöld", "SRI-text": "övrig"}
use = json.load(open(os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik", "kallkontroll.json"), encoding="utf-8"))["fält_som_får_läsas"]
TKEY = {"Bautil": "bautil", "Rhezelius": "rhezelius", "Peringskiöld": "peringskiold", "övrig": "ovrig"}
corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"),
                   low_memory=False).drop_duplicates("signum").set_index("signum")


def outcomes(c):
    u1 = None if "djurhuvud" not in c else int(c["djurhuvud"] == "ja")
    u2 = None if "kors" not in c else int(c["kors"] == "ja")
    parts = [c.get("antal_djur") in ("2", "3+") if "antal_djur" in c else None,
             c.get("koppel") == "ja" if "koppel" in c else None,
             c.get("flatverk") in ("attor", "tat") if "flatverk" in c else None]
    known = [p for p in parts if p is not None]
    u3 = None if not known else int(any(known))
    return u1, u2, u3


def row(s, c, forlorad, typ, kalla):
    if s not in corp.index:
        return None
    u1, u2, u3 = outcomes(c)
    par = corp.at[s, "parish"]
    return {"signum": s, "forlorad": forlorad, "typ": typ, "kalla": kalla, "uppland": int(s.startswith("U ")),
            "socken": par if isinstance(par, str) else s, "landskap": s.split()[0], "U1": u1, "U2": u2, "U3": u3}


rows = []
lost = json.load(open(os.path.join(C, "orn_koder_forlorade.json"), encoding="utf-8"))
for s, v in lost.items():
    rows.append(row(s, v["koder"], 1, TYP.get(v["källa"], "övrig"), "teckning"))
kb = json.load(open(os.path.join(C, "kallkontroll_batcher.json"), encoding="utf-8"))
typ = {s["sig"]: s["typ"] for b in kb if b["id"].startswith("t") for s in b["stones"]}
raw = defaultdict(dict)
for r in json.load(open(os.path.join(C, "kodning_kallkontroll.json"), encoding="utf-8")):
    if r["batch"].startswith("t"):
        for x in r["stenar"] or []:
            raw[x["signum"].strip()][r["coder"]] = x
for s, c in consensus(raw).items():
    t = TYP[typ[s]]
    c = {f: v for f, v in c.items() if f in use[TKEY[t]]}  # samma godkända fält som för de förlorade
    rows.append(row(s, c, 0, t, "teckning"))
df = pd.DataFrame([r for r in rows if r])
assert int(corp.loc[df[df.forlorad == 0].signum, "lost"].sum()) == 0
df.to_csv(os.path.join(HERE, "data.csv"), index=False)
# beskrivande: bevarade planschstenar (foto) i samma socknar som de förlorade
plate = json.load(open(os.path.join(C, "orn_koder.json"), encoding="utf-8"))
soc = set(df[df.forlorad == 1].socken)
foto = [row(s, c, 0, "foto", "plansch") for s, c in plate.items()
        if s in corp.index and int(corp.at[s, "lost"]) == 0 and corp.at[s, "parish"] in soc]
pd.concat([df[df.forlorad == 1], pd.DataFrame([r for r in foto if r])]).to_csv(os.path.join(HERE, "data_foto.csv"), index=False)
print(df.groupby("forlorad")[["U1", "U2", "U3"]].count())
