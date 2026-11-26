"""Lokala ornamenttraditioner (analysplaner/2026-11-26-lokala-ornamenttraditioner.md) – data till traditioner.R.
Språkdragen för jämförelsen: de sex trait_-kolumner som flest av stenarna har ett värde i; binärt = det vanligaste värdet.
    .venv/bin/python utdata/lokala_traditioner/data.py"""
import hashlib
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-26-lokala-ornamenttraditioner.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest() == open(PLAN + ".sha256").read().split()[0], "planen ändrad"
STY = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
cons = json.load(open(os.path.join(ROOT, "data", "cache", "hander", "ornamentik", "orn_koder.json"), encoding="utf-8"))
c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"),
                low_memory=False).drop_duplicates("signum").set_index("signum")
c["st"] = c["style"].astype(str).str.replace("\xa0", " ").str.replace(" ", "")


def b(cond, ok):
    return None if not ok else int(cond)


rows = []
for s, k in cons.items():
    if s not in c.index or int(c.at[s, "lost"]) == 1 or c.at[s, "st"] not in STY or not isinstance(c.at[s, "district"], str):
        continue
    r = {"signum": s, "stil": c.at[s, "st"], "landskap": s.split()[0], "harad": c.at[s, "district"],
         "socken": c.at[s, "parish"] if isinstance(c.at[s, "parish"], str) else s}
    r["D1"] = b(k.get("koppel") == "ja", "koppel" in k)
    r["D2"] = b(k.get("huvud_vy") == "uppifran", k.get("huvud_vy") in ("uppifran", "profil"))
    r["D3"] = b(k.get("oga") == "mandel", k.get("oga") in ("mandel", "rund"))
    r["D4"] = b(k.get("flatverk") != "inget", "flatverk" in k)
    r["D5"] = b(k.get("orm_extra") == "ja", "orm_extra" in k)
    r["D6"] = b(k.get("kors") == "ja", "kors" in k)
    r["D7"] = b(k.get("antal_djur") in ("2", "3+"), k.get("antal_djur") in ("1", "2", "3+"))
    r["D8"] = b(k.get("svans") == "spiral", "svans" in k and k.get("svans") != "ingen_svans")
    rows.append(r)
df = pd.DataFrame(rows)
tc = [x for x in c.columns if x.startswith("trait_")]
cov = sorted(tc, key=lambda t: -c.loc[df.signum, t].notna().sum())[:6]
for t in cov:
    v = c.loc[df.signum, t]
    mode = v.dropna().mode().iloc[0]
    df["S_" + t[len("trait_"):]] = [None if pd.isna(x) else int(x == mode) for x in v]
df.to_csv(os.path.join(HERE, "data.csv"), index=False)
print(len(df), "stenar,", df.harad.nunique(), "härader; språkdrag:", cov)
print(df[[x for x in df.columns if x.startswith(("D", "S_"))]].count().to_dict())
