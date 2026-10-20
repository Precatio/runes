"""Tabellen för den multipla imputationen (analysplan_mi.md): en rad per runsten ur samma korpusrader som R-analyserna
och Pröva en egen fråga, med tidsskiktet (tomt för stenar utan säker stilgrupp), de 22 dragen som ja/nej/okänd,
bergartsfamilj, antal ord, socken, stilgruppens mittår och språkdateringens två skillnader (utdata/mi/aux_dating.json).
Skriver utdata/mi/korpus_mi.csv.
    PYTHONPATH=. .venv/bin/python utdata/mi/export.py"""
import csv
import json
import math
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from api.routers.orthography import model  # noqa: E402
from src import question as q, r_bridge as rb  # noqa: E402

rows = rb.corpus_rows(store().inscriptions, model().names)
prep = q.prepare(rows)
by = {r["signum"]: r for r in rows}
aux = json.load(open(os.path.join(ROOT, "utdata", "mi", "aux_dating.json")))
n_prov = Counter(s["province"] for s in prep["stones"])
traits = [k for k, *_ in q.VARIABLES]
out = os.path.join(ROOT, "utdata", "mi", "korpus_mi.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["signum", "province", "province_imp", "parish", "year", "E", *traits, "family", "logwords", "aux1", "aux2"])
    for s in prep["stones"]:
        r = by[s["signum"]]
        a = aux.get(s["signum"])
        ll = a["ll"] if a else None
        w.writerow([s["signum"], s["province"], s["province"] if n_prov[s["province"]] >= q.MIN_PROVINCE else "övrigt",
                    r.get("parish") or "", "" if s["year"] is None else s["year"],
                    "" if s["epoch"] == "odaterad" else s["epoch"],
                    *[{1: "ja", 0: "nej", None: "okänd"}[s["v"][t]] for t in traits],
                    s["family"] or "okänd", round(math.log1p(r.get("n_words") or 0), 4),
                    "" if not ll else round(ll["1100"] - ll["1000"], 4), "" if not ll else round(ll["900"] - ll["1000"], 4)])
dated = sum(s["epoch"] != "odaterad" for s in prep["stones"])
with_aux = sum(1 for s in prep["stones"] if s["signum"] in aux)
print(f"{len(prep['stones'])} runstenar, {dated} daterade, {with_aux} med språkdatering → {out}")
print("skikt:", Counter(s["epoch"] for s in prep["stones"]))
